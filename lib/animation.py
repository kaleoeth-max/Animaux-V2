"""Squelette et animations d'un gardien à quatre pattes, export Roblox (commun à tous les modèles).

Un module de modèle (ex. scripts/gardien_belier.py) fournit : NAME, build(), PATTES, articulations(),
QUEUE (6 points), CHARNIERE, OUVERTURE, repere_oeil(), PAUPIERE_SORTIE et un dictionnaire ANIM :
  torse          (tête, queue) de l'os Torse — sa tête est le pivot du corps
  tete           (tête, queue) de l'os Tete — sa tête est le pivot du cou
  machoire_bout  bout de l'os Machoire (sa tête est CHARNIERE)
  pieces_torse   pièces liées rigidement au torse (ex. ("Corps",))
  pas_marche, leve_marche, pas_course, leve_course   foulées (studs)
  couche, tete_couche, avant_couche                  pose de sommeil (descente du corps, tête, pieds avant)
  croc_tete, croc_ouverture, croc_pique              facultatifs : amplitude du coup de croc (défaut 16, 22, 6)
  sommeil="boule" + boule_avant, boule_arriere (pieds), boule_tete, boule_queue, boule_roulis, boule_lacet
                                                     facultatifs : sommeil roulé en boule au lieu du sphinx
  sommeil="cote" + cote_roulis, cote_epaisseur, cote_tete, cote_queue, cote_pattes_avant, cote_pattes_arriere
                                                     facultatifs : sommeil couché sur le flanc
Un module d'animations (ex. scripts/animations_belier.py) appelle configurer(modele) puis main().

Animations (30 images/s, sur place) :
  Marche        1,3 s en boucle : pas en diagonale, corps qui tangue, queue qui balance
  Course        0,7 s en boucle : galop, grandes foulées
  Sommeil       3,0 s en boucle : couché en sphinx (ou roulé en boule), yeux fermés, respiration lente
  CoupDeCroc    1,2 s           : recul, gueule grande ouverte, attaque vers l'avant, claquement

Sorties dans exports/<NAME>/ : <NAME>_rig.fbx (modèle + os), <NAME>_<Anim>.fbx (une animation par fichier),
<NAME>_anime.glb (tout en un) ; un GIF par animation dans previews/.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly as lp  # noqa: E402
from lowpoly import Euler, Matrix, Vector  # noqa: E402

import bpy  # noqa: E402

FPS = 30
g = None      # module du modèle, fixé par configurer()
NAME = None
ANIM = {}
TORSE_TETE = None  # tête de l'os Torse (pivot du corps)


def configurer(modele):
    global g, NAME, ANIM, TORSE_TETE
    g, NAME, ANIM = modele, modele.NAME, modele.ANIM
    TORSE_TETE = Vector(ANIM["torse"][0])


# ---------------------------------------------------------------------------- squelette

def os_pattes():
    """{nom de patte: [(nom d'os, début, fin), ...]} du haut vers le pied."""
    out = {}
    for nom, x, y, avant in g.PATTES:
        j = g.articulations(x, y, avant)
        cheville = j[-1]
        bout = Vector((cheville.x, cheville.y - 1.7, 0.4))
        segs = [(f"{nom}_{i + 1}", j[i], j[i + 1]) for i in range(len(j) - 1)]
        segs.append((f"{nom}_Pied", cheville, bout))
        out[nom] = segs
    return out


def os_queue():
    q = g.QUEUE
    return [("Queue1", q[0], q[1]), ("Queue2", q[1], q[2]), ("Queue3", q[2], q[3]), ("Queue4", q[3], q[5])]


def creer_squelette(model):
    data = bpy.data.armatures.new(f"{NAME}_Squelette")
    rig = bpy.data.objects.new(f"{NAME}_Rig", data)
    model.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    eb = data.edit_bones

    def os_(nom, tete, queue, parent=None):
        b = eb.new(nom)
        b.head, b.tail = Vector(tete), Vector(queue)
        b.roll = 0.0
        if parent:
            b.parent = eb[parent]
        return b

    os_("Racine", (0, 0, 0), (0, -2, 0))
    os_("Torse", *ANIM["torse"], "Racine")
    os_("Tete", *ANIM["tete"], "Torse")
    os_("Machoire", g.CHARNIERE, ANIM["machoire_bout"], "Tete")
    for cote, sg in (("G", 1), ("D", -1)):
        c, n = g.repere_oeil(sg)[:2]
        centre = c - n * g.PAUPIERE_SORTIE * 0.75
        os_(f"Paupiere_{cote}", centre, centre + n * 0.6, "Tete")
    parent = "Torse"
    for nom, a, b in os_queue():
        os_(nom, a, b, parent)
        parent = nom
    for segs in os_pattes().values():
        parent = "Torse"
        for nom, a, b in segs:
            os_(nom, a, b, parent)
            parent = nom
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig


# ---------------------------------------------------------------------------- liaison pièces -> os

def _dist_segment(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (a + ab * t - p).length


def lier(rig, obj, segments=None, os_unique=None, fondu=0.6):
    """Lie une pièce au squelette : à un seul os (rigide) ou à une chaîne d'os (pondération par distance,
    avec un fondu entre deux os voisins pour que la pièce se plie en douceur)."""
    mod = obj.modifiers.new("Squelette", "ARMATURE")
    mod.object = rig
    obj.parent = rig
    if os_unique:
        vg = obj.vertex_groups.new(name=os_unique)
        vg.add(range(len(obj.data.vertices)), 1.0, "REPLACE")
        return
    groupes = {nom: obj.vertex_groups.new(name=nom) for nom, _, _ in segments}
    for v in obj.data.vertices:
        d = sorted((_dist_segment(v.co, a, b), nom) for nom, a, b in segments)
        (d1, n1), (d2, n2) = d[0], d[1]
        ecart = d2 - d1
        w1 = 1.0 if ecart >= fondu else 0.5 + 0.5 * ecart / fondu
        groupes[n1].add([v.index], w1, "REPLACE")
        if w1 < 1.0:
            groupes[n2].add([v.index], 1.0 - w1, "REPLACE")


def lier_tout(model, rig):
    pattes = os_pattes()
    for obj in model.parts:
        n = obj.name
        if n in ANIM["pieces_torse"]:
            lier(rig, obj, os_unique="Torse")
        elif n in ("Tete", "Oeil_G", "Oeil_D"):
            lier(rig, obj, os_unique="Tete")
        elif n == "Machoire":
            lier(rig, obj, os_unique="Machoire")
        elif n.startswith("Paupiere_"):
            lier(rig, obj, os_unique=n)
        elif n == "Queue":
            lier(rig, obj, os_queue(), fondu=1.2)
        elif n.startswith("Patte_"):
            lier(rig, obj, pattes[n[len("Patte_"):]], fondu=0.5)
        else:
            raise ValueError(f"pièce sans os : {n}")


# ---------------------------------------------------------------------------- pieds posés au sol (IK)


def _angle(v):
    """Angle d'un vecteur dans le plan vertical avant/arrière (Y, Z)."""
    return math.atan2(v.z, v.y)


def _plan(v):
    return math.hypot(v.y, v.z)


def _tour(a):
    return (a + math.pi) % TAU - math.pi


def ik_pattes(pose, cibles=None, pointe=None):
    """Calcule les angles des pattes pour que chaque cheville atteigne sa cible (par défaut : sa position
    de repos, pieds bien posés au sol) même quand le corps bouge. Le pied reste à plat.
    cibles : {patte: décalage (dy, dz) de la cheville} ; pointe : {patte: inclinaison des orteils en degrés}."""
    cibles, pointe = cibles or {}, pointe or {}
    pose["_cibles"] = {}
    rot, dep = pose.get("Torse", ((0, 0, 0), (0, 0, 0)))
    r = Euler(tuple(math.radians(a) for a in rot), "XYZ").to_matrix().to_4x4()
    torse = Matrix.Translation(TORSE_TETE + Vector(dep)) @ r @ Matrix.Translation(-TORSE_TETE)
    tangage = math.radians(rot[0])
    for nom, x, y, avant in g.PATTES:
        j = g.articulations(x, y, avant)
        dy, dz = cibles.get(nom, (0.0, 0.0))
        cheville = j[-1] + Vector((0, dy, dz))
        pose["_cibles"][nom] = cheville
        # patte arrière : le dernier segment (jarret -> cheville) garde son orientation, on vise le jarret
        cible = cheville if avant else cheville + (j[2] - j[3])
        a0, a1, a2 = j[0], j[1], j[2]
        l1, l2 = _plan(a1 - a0), _plan(a2 - a1)  # longueurs dans le plan avant/arrière
        epaule = torse @ a0
        v = cible - epaule
        d = max(abs(l1 - l2) + 1e-3, min(l1 + l2 - 1e-3, math.hypot(v.y, v.z)))
        base = math.atan2(v.z, v.y)
        alpha = math.acos(max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
        # sens de pliage (coude en arrière / genou en avant) : celui de la pose de repos
        v0 = a2 - a0
        base0 = math.atan2(v0.z, v0.y)
        al0 = alpha_repos(l1, l2, v0)
        sens = 1 if abs(_tour(base0 + al0 - _angle(a1 - a0))) < abs(_tour(base0 - al0 - _angle(a1 - a0))) else -1
        b1 = base + sens * alpha
        coude = Vector((0, epaule.y + l1 * math.cos(b1), epaule.z + l1 * math.sin(b1)))
        b2 = math.atan2(cible.z - coude.z, cible.y - coude.y)
        c1 = _tour(b1 - _angle(a1 - a0))  # changement d'angle absolu de chaque segment
        c2 = _tour(b2 - _angle(a2 - a1))
        rx1, rx2 = c1 - tangage, c2 - c1
        pose[f"{nom}_1"] = ((math.degrees(rx1), 0, 0), (0, 0, 0))
        pose[f"{nom}_2"] = ((math.degrees(rx2), 0, 0), (0, 0, 0))
        if not avant:
            pose[f"{nom}_3"] = ((math.degrees(-c2), 0, 0), (0, 0, 0))
            c2 = 0.0
        pose[f"{nom}_Pied"] = ((math.degrees(-c2) + pointe.get(nom, 0.0), 0, 0), (0, 0, 0))
    return pose


def alpha_repos(l1, l2, v0):
    d = math.hypot(v0.y, v0.z)
    return math.acos(max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))


# ---------------------------------------------------------------------------- animations
# Chaque animation renvoie, pour un instant u dans [0, 1], {os: (rotation en degrés (x, y, z), déplacement)}.
# Les rotations sont exprimées dans les axes du monde au repos (X = côté gauche de la bête, Y = arrière,
# Z = haut), autour de la tête de l'os, et s'ajoutent à celles de l'os parent.
#   rx > 0 : une tête / mâchoire pointée vers l'avant descend ; une patte (pointée vers le bas) part en arrière ;
#            la queue (pointée vers l'arrière) monte.
#   rz > 0 : la queue part vers la droite de la bête (-X) ; la tête tourne vers sa gauche.

TAU = 2 * math.pi


def lisse(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def cles(u, points):
    """Interpole des valeurs-clés [(u, valeur), ...] avec un lissage (début et fin en douceur)."""
    if u <= points[0][0]:
        return points[0][1]
    for (u0, v0), (u1, v1) in zip(points, points[1:]):
        if u <= u1:
            w = lisse((u - u0) / (u1 - u0))
            return v0 + (v1 - v0) * w
    return points[-1][1]


def queue_ondule(pose, u, ampl, decal=0.7, montee=0.0):
    for i in range(4):
        pose[f"Queue{i + 1}"] = ((montee, 0, ampl * (1 + 0.3 * i) * math.sin(TAU * u - decal * i)), (0, 0, 0))


def anim_marche(u):
    pose = {
        "Torse": ((0, 2.5 * math.sin(TAU * u), 0), (0, 0, 0.14 * math.cos(2 * TAU * u))),
        "Tete": ((3 * math.sin(2 * TAU * u), 0, -3 * math.sin(TAU * u)), (0, 0, 0)),
        "Machoire": ((-6 + 3 * math.sin(2 * TAU * u), 0, 0), (0, 0, 0)),
    }
    queue_ondule(pose, u, 9, montee=4)
    # pas en diagonale : pendant l'appui le pied glisse vers l'arrière au sol, puis revient levé
    phases = {"AvG": 0.0, "ArD": 0.0, "AvD": 0.5, "ArG": 0.5}
    cibles, pointe = {}, {}
    for nom, _, _, avant in g.PATTES:
        a = TAU * (u + phases[nom])
        leve = max(0.0, math.cos(a))
        cibles[nom] = (-ANIM["pas_marche"] * math.sin(a), ANIM["leve_marche"] * leve ** 1.5)
        pointe[nom] = 14 * leve ** 2  # les orteils pointent seulement une fois le pied bien levé
    return ik_pattes(pose, cibles, pointe)


def anim_coup_de_croc(u):
    bas, ouvre, plonge = ANIM.get("croc_tete", 16), ANIM.get("croc_ouverture", 22), ANIM.get("croc_pique", 6)
    tete = cles(u, [(0, 0), (0.3, -20), (0.45, bas), (0.55, bas - 2), (1, 0)])
    mach = cles(u, [(0, 0), (0.3, ouvre - 4), (0.42, ouvre), (0.5, -g.OUVERTURE), (0.62, -g.OUVERTURE), (1, 0)])
    avance = cles(u, [(0, 0), (0.3, 0.5), (0.45, -1.0), (0.6, -1.0), (1, 0)])
    pique = cles(u, [(0, 0), (0.3, -4), (0.45, plonge), (0.6, plonge), (1, 0)])
    pose = {
        "Torse": ((pique, 0, 0), (0, avance, -abs(avance) * 0.25)),
        "Tete": ((tete, 0, 0), (0, 0, 0)),
        "Machoire": ((mach, 0, 0), (0, 0, 0)),
    }
    queue_ondule(pose, u, 6, montee=cles(u, [(0, 0), (0.45, 6), (1, 0)]))
    return ik_pattes(pose)


def anim_course(u):
    """Galop : grandes foulées, pattes avant puis arrière presque ensemble, le corps tangue d'avant en arrière."""
    pose = {
        "Torse": ((5 * math.sin(TAU * u), 0, 0), (0, 0, -0.2 + 0.3 * math.cos(2 * TAU * u))),
        "Tete": ((5 - 5 * math.sin(TAU * u + 0.6), 0, 0), (0, 0, 0)),
        "Machoire": ((4 + 4 * math.sin(2 * TAU * u), 0, 0), (0, 0, 0)),  # halète, gueule ouverte
    }
    queue_ondule(pose, u, 4, montee=5)
    phases = {"AvG": 0.0, "AvD": 0.12, "ArG": 0.5, "ArD": 0.62}
    cibles, pointe = {}, {}
    for nom in phases:
        a = TAU * (u + phases[nom])
        leve = max(0.0, math.cos(a))
        cibles[nom] = (-ANIM["pas_course"] * math.sin(a), ANIM["leve_course"] * leve ** 1.5)
        pointe[nom] = 20 * leve ** 2
    return ik_pattes(pose, cibles, pointe)


def anim_sommeil(u):
    """Sommeil : en sphinx (par défaut), roulé en boule (ANIM["sommeil"] == "boule") ou couché sur le côté
    (ANIM["sommeil"] == "cote")."""
    if ANIM.get("sommeil") == "boule":
        return anim_sommeil_boule(u)
    if ANIM.get("sommeil") == "cote":
        return anim_sommeil_cote(u)
    return anim_sommeil_sphinx(u)


def anim_sommeil_cote(u):
    """Couché sur le flanc : tout le corps bascule d'environ 90° autour de l'os Racine et repose au sol, pattes
    allongées sur le côté et un peu pliées, tête posée, queue qui retombe, yeux fermés, respiration lente."""
    souffle = math.sin(TAU * u)
    angle = ANIM.get("cote_roulis", 88)
    h = Vector(ANIM["torse"][0]).z               # hauteur du corps au repos
    epaisseur = ANIM.get("cote_epaisseur", 2.3)  # demi-épaisseur du corps (fourrure comprise) posé sur le flanc
    a = math.radians(angle)
    pose = {
        "Racine": ((0, angle, 0), (-h * math.sin(a), 0, epaisseur - h * math.cos(a))),
        "Torse": ((0, 0, 0), (0, 0, 0.06 * souffle)),  # respiration : le flanc se soulève
        "Tete": (ANIM.get("cote_tete", (8, 0, 0)), (0, 0, 0)),
        "Machoire": ((-g.OUVERTURE, 0, 0), (0, 0, 0)),
    }
    for cote, sg in (("G", 1), ("D", -1)):
        n = g.repere_oeil(sg)[1]
        pose[f"Paupiere_{cote}"] = ((0, 0, 0), tuple(n * g.PAUPIERE_SORTIE))
    for i, rz in enumerate(ANIM.get("cote_queue", (-12, -10, -8, -6))):
        pose[f"Queue{i + 1}"] = ((ANIM.get("cote_queue_rx", 0) if i == 0 else 0, 0, rz), (0, 0, 0))
    # pattes détendues : les avant vers l'avant, les arrière vers l'arrière, un peu pliées
    for nom, _, _, avant in g.PATTES:
        angles = ANIM.get("cote_pattes_avant", (-25, 35)) if avant else ANIM.get("cote_pattes_arriere", (20, -25, 15))
        for k, rx in enumerate(angles):
            pose[f"{nom}_{k + 1}"] = ((rx, 0, 0), (0, 0, 0))
    return pose


def anim_sommeil_boule(u):
    """Roulé en boule au sol : corps posé et un peu basculé sur le côté, pattes repliées dessous, tête tournée
    vers le flanc museau au sol, queue enroulée vers l'avant jusqu'au museau, yeux fermés, respiration lente."""
    souffle = math.sin(TAU * u)
    pose = {
        "Torse": ((1.0 * souffle, ANIM.get("boule_roulis", 12), ANIM.get("boule_lacet", 8)),
                  (0, 0, ANIM["couche"] + 0.08 * souffle)),
        "Tete": ((ANIM["tete_couche"] + 0.8 * souffle, 0, -ANIM.get("boule_tete", 70)), (0, 0, 0)),
        "Machoire": ((-g.OUVERTURE, 0, 0), (0, 0, 0)),
    }
    for cote, sg in (("G", 1), ("D", -1)):
        n = g.repere_oeil(sg)[1]
        pose[f"Paupiere_{cote}"] = ((0, 0, 0), tuple(n * g.PAUPIERE_SORTIE))
    courbe = ANIM.get("boule_queue", 38)
    courbes = courbe if isinstance(courbe, (tuple, list)) else (courbe,) * 4  # un angle par os, de la base au bout
    for i in range(4):
        pose[f"Queue{i + 1}"] = ((ANIM.get("boule_queue_monte", 8) if i == 0 else 0, 0,
                                  courbes[i] + 2 * souffle * (i == 3)), (0, 0, 0))
    cibles = {}
    for nom, _, _, avant in g.PATTES:
        cibles[nom] = ANIM["boule_avant"] if avant else ANIM["boule_arriere"]
    return ik_pattes(pose, cibles)


def anim_sommeil_sphinx(u):
    """Couché en sphinx, menton posé, yeux fermés, queue enroulée sur le côté, respiration lente."""
    souffle = math.sin(TAU * u)
    pose = {
        "Torse": ((2 + 1.2 * souffle, 0, 0), (0, 0.2, ANIM["couche"] + 0.1 * souffle)),
        "Tete": ((ANIM["tete_couche"] + 1.0 * souffle, 0, -12), (0, 0, 0)),
        "Machoire": ((-g.OUVERTURE + 1.5 * max(0.0, souffle), 0, 0), (0, 0, 0)),  # gueule fermée, petit ronflement
    }
    for cote, sg in (("G", 1), ("D", -1)):
        n = g.repere_oeil(sg)[1]
        pose[f"Paupiere_{cote}"] = ((0, 0, 0), tuple(n * g.PAUPIERE_SORTIE))
    for i, courbe in enumerate((16, 22, 28, 34)):
        pose[f"Queue{i + 1}"] = ((10 if i == 0 else 0, 0, courbe + 2 * souffle * (i == 3)), (0, 0, 0))
    # pose de sphinx : coudes posés au sol derrière les épaules, avant-bras à plat vers l'avant ;
    # pattes arrière repliées sous le corps
    return ik_pattes(pose, {"AvG": ANIM["avant_couche"], "AvD": ANIM["avant_couche"]})


ANIMATIONS = [  # (nom, durée en images, fonction, boucle)
    ("Marche", 40, anim_marche, True),
    ("Course", 22, anim_course, True),
    ("Sommeil", 90, anim_sommeil, True),
    ("CoupDeCroc", 36, anim_coup_de_croc, False),
]


def creer_action(rig, nom, duree, fonction, boucle):
    action = bpy.data.actions.new(f"{NAME}_{nom}")
    action.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = action
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
    os_repos = {b.name: b.matrix_local.copy() for b in rig.data.bones}
    for f in range(duree + 1):
        u = (f / duree) % 1.0 if boucle else f / duree
        pose = fonction(u)
        for pb in rig.pose.bones:
            rot, dep = pose.get(pb.name, ((0, 0, 0), (0, 0, 0)))
            repos = os_repos[pb.name]
            h = repos.to_translation()
            r = Euler(tuple(math.radians(a) for a in rot), "XYZ").to_matrix().to_4x4()
            delta = Matrix.Translation(h + Vector(dep)) @ r @ Matrix.Translation(-h)
            pb.matrix_basis = repos.inverted() @ delta @ repos
            pb.keyframe_insert("location", frame=f + 1)
            pb.keyframe_insert("rotation_quaternion", frame=f + 1)
    return action


# ---------------------------------------------------------------------------- export + aperçus

def exporter(model, rig, actions):
    out = os.path.join(lp.EXPORTS, NAME)
    objets = [rig] + model.parts
    bpy.ops.object.select_all(action="DESELECT")
    for o in objets:
        o.select_set(True)
    bpy.context.view_layer.objects.active = rig
    commun = dict(use_selection=True, object_types={"ARMATURE", "MESH"}, add_leaf_bones=False,
                  apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS", mesh_smooth_type="FACE",
                  path_mode="COPY", embed_textures=True, axis_forward="-Z", axis_up="Y",
                  primary_bone_axis="Y", secondary_bone_axis="X")
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix()
    bpy.ops.export_scene.fbx(filepath=os.path.join(out, f"{NAME}_rig.fbx"), bake_anim=False, **commun)
    for (nom, duree, _, _), action in zip(ANIMATIONS, actions):
        rig.animation_data.action = action
        bpy.context.scene.frame_start, bpy.context.scene.frame_end = 1, duree + 1
        bpy.ops.export_scene.fbx(filepath=os.path.join(out, f"{NAME}_{nom}.fbx"), bake_anim=True,
                                 bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                                 bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0, **commun)
    rig.animation_data.action = actions[0]
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, f"{NAME}_anime.glb"), export_format="GLB",
                              use_selection=True, export_animations=True, export_animation_mode="ACTIONS")


def gifs(model, rig, actions, taille=420, pas=2):
    from PIL import Image

    scene = bpy.context.scene
    scene.render.fps = FPS
    # met en place lumière, sol et caméra (un seul rendu de test, écrasé ensuite)
    lp.render_previews(model, views=((35, "_anim_tmp"),), size=taille, samples=10)
    os.remove(os.path.join(lp.PREVIEWS, f"{model.name}__anim_tmp.png"))
    tmp = os.path.join(lp.PREVIEWS, "_frames")
    os.makedirs(tmp, exist_ok=True)
    chemins = []
    for (nom, duree, _, _), action in zip(ANIMATIONS, actions):
        rig.animation_data.action = action
        images = []
        for f in range(1, duree + 1, pas):
            scene.frame_set(f)
            scene.render.filepath = os.path.join(tmp, f"{nom}_{f:03d}.png")
            bpy.ops.render.render(write_still=True)
            images.append(Image.open(scene.render.filepath).convert("RGB"))
        chemin = os.path.join(lp.PREVIEWS, f"{NAME}_anim_{nom}.gif")
        images[0].save(chemin, save_all=True, append_images=images[1:], duration=int(1000 * pas / FPS), loop=0)
        chemins.append(chemin)
        print("gif", chemin)
    for fichier in os.listdir(tmp):
        os.remove(os.path.join(tmp, fichier))
    os.rmdir(tmp)
    return chemins


def main():
    model = g.build()
    rig = creer_squelette(model)
    lier_tout(model, rig)
    actions = [creer_action(rig, *a) for a in ANIMATIONS]
    print("os :", len(rig.data.bones), "| animations :", ", ".join(a[0] for a in ANIMATIONS))
    exporter(model, rig, actions)
    if "--no-render" not in sys.argv:
        gifs(model, rig, actions)

