"""Animations du Bélier Colosse : squelette, liaison des pièces aux os, 5 animations, export Roblox.

Animations (30 images/s, sur place) :
  Repos         2,0 s en boucle : respiration, tête qui scrute, queue qui ondule
  Marche        1,3 s en boucle : pas en diagonale, corps qui tangue, queue qui balance
  Morsure       1,2 s           : recul, gueule grande ouverte, attaque vers l'avant, claquement
  Rugissement   2,5 s           : tête levée, gueule ouverte au maximum, tête qui tremble
  CoupDeQueue   1,4 s           : le corps pivote et la queue balaie de côté
  Course        0,7 s en boucle : galop, grandes foulées (~11,5 studs/s)
  Sommeil       3,0 s en boucle : couché en sphinx, yeux fermés, queue enroulée, respiration lente

Sorties dans exports/Gardien_Prairie_Belier/ :
  Gardien_Prairie_Belier_rig.fbx        modèle + squelette (à importer dans Roblox)
  Gardien_Prairie_Belier_<Anim>.fbx     une animation par fichier (Animation Editor > Import > From FBX Animation)
  Gardien_Prairie_Belier_anime.glb      tout en un (pour visualiser dans n'importe quel viewer glTF)
et un GIF par animation dans previews/.

Lancer :  python3 scripts/animations_belier.py            (export + GIF)
          python3 scripts/animations_belier.py --no-render (export seulement)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import gardien_belier as g  # noqa: E402
import lowpoly as lp  # noqa: E402
from lowpoly import Euler, Matrix, Vector  # noqa: E402

import bpy  # noqa: E402

FPS = 30
NAME = g.NAME


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
    os_("Torse", (0, 3.5, 6.4), (0, -4.5, 6.6), "Racine")
    os_("Tete", (0, -6.9, 7.0), (0, -11.5, 6.6), "Torse")
    os_("Machoire", g.CHARNIERE, (0, -11.8, 4.7), "Tete")
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
        if n == "Corps":
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

TORSE_TETE = Vector((0, 3.5, 6.4))  # tête de l'os Torse (pivot du corps)


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


def anim_repos(u):
    pose = {
        "Torse": ((1.2 * math.sin(TAU * u), 0, 0), (0, 0, 0.08 * math.sin(TAU * u))),
        "Tete": ((2 * math.sin(2 * TAU * u) - 1.2 * math.sin(TAU * u), 0, 9 * math.sin(TAU * u)), (0, 0, 0)),
        "Machoire": ((-7 + 4 * math.sin(TAU * u + 1), 0, 0), (0, 0, 0)),
    }
    queue_ondule(pose, u, 5)
    return ik_pattes(pose)


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
        cibles[nom] = (-1.5 * math.sin(a), 0.9 * leve ** 1.5)
        pointe[nom] = 14 * leve ** 2  # les orteils pointent seulement une fois le pied bien levé
    return ik_pattes(pose, cibles, pointe)


def anim_morsure(u):
    tete = cles(u, [(0, 0), (0.3, -20), (0.45, 16), (0.55, 14), (1, 0)])
    mach = cles(u, [(0, 0), (0.3, 18), (0.42, 22), (0.5, -14), (0.62, -14), (1, 0)])
    avance = cles(u, [(0, 0), (0.3, 0.5), (0.45, -1.0), (0.6, -1.0), (1, 0)])
    pique = cles(u, [(0, 0), (0.3, -4), (0.45, 6), (0.6, 6), (1, 0)])
    pose = {
        "Torse": ((pique, 0, 0), (0, avance, -abs(avance) * 0.25)),
        "Tete": ((tete, 0, 0), (0, 0, 0)),
        "Machoire": ((mach, 0, 0), (0, 0, 0)),
    }
    queue_ondule(pose, u, 6, montee=cles(u, [(0, 0), (0.45, 6), (1, 0)]))
    return ik_pattes(pose)


def anim_rugissement(u):
    leve = cles(u, [(0, 0), (0.25, 1), (0.8, 1), (1, 0)])
    tremble = math.sin(TAU * u * 9) * cles(u, [(0, 0), (0.3, 1), (0.75, 1), (0.85, 0), (1, 0)])
    pose = {
        "Torse": ((-4 * leve, 0, 0), (0, 0.3 * leve, 0)),
        "Tete": ((-28 * leve + 2 * tremble, 0, 5 * tremble), (0, 0, 0)),
        "Machoire": ((30 * leve, 0, 0), (0, 0, 0)),
    }
    queue_ondule(pose, u, 4, montee=8 * leve)
    return ik_pattes(pose)


def anim_coup_de_queue(u):
    balai = cles(u, [(0, 0), (0.3, -1), (0.55, 1.2), (0.75, 1.0), (1, 0)])
    pose = {
        "Torse": ((0, 0, 4 * balai), (0, 0, 0)),
        "Tete": ((0, 0, -18 * balai), (0, 0, 0)),
        "Machoire": ((cles(u, [(0, 0), (0.45, 10), (1, 0)]), 0, 0), (0, 0, 0)),
    }
    for i in range(4):
        retard = cles(u - 0.04 * i, [(0, 0), (0.3, -1), (0.55, 1.2), (0.75, 1.0), (1, 0)])
        pose[f"Queue{i + 1}"] = ((6 * abs(retard), 0, 22 * retard * (1 + 0.25 * i)), (0, 0, 0))
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
        cibles[nom] = (-2.1 * math.sin(a), 1.4 * leve ** 1.5)
        pointe[nom] = 20 * leve ** 2
    return ik_pattes(pose, cibles, pointe)


def anim_sommeil(u):
    """Couché en sphinx, menton posé, yeux fermés, queue enroulée sur le côté, respiration lente."""
    souffle = math.sin(TAU * u)
    pose = {
        "Torse": ((2 + 1.2 * souffle, 0, 0), (0, 0.2, -2.3 + 0.1 * souffle)),
        "Tete": ((10 + 1.0 * souffle, 0, -12), (0, 0, 0)),
        "Machoire": ((-14 + 1.5 * max(0.0, souffle), 0, 0), (0, 0, 0)),  # gueule fermée, petit ronflement
    }
    for cote, sg in (("G", 1), ("D", -1)):
        n = g.repere_oeil(sg)[1]
        pose[f"Paupiere_{cote}"] = ((0, 0, 0), tuple(n * g.PAUPIERE_SORTIE))
    for i, courbe in enumerate((16, 22, 28, 34)):
        pose[f"Queue{i + 1}"] = ((10 if i == 0 else 0, 0, courbe + 2 * souffle * (i == 3)), (0, 0, 0))
    # pose de sphinx : coudes posés au sol derrière les épaules, avant-bras à plat vers l'avant ;
    # pattes arrière repliées sous le corps
    return ik_pattes(pose, {"AvG": (-0.9, 0.0), "AvD": (-0.9, 0.0)})


ANIMATIONS = [  # (nom, durée en images, fonction, boucle)
    ("Repos", 60, anim_repos, True),
    ("Marche", 40, anim_marche, True),
    ("Morsure", 36, anim_morsure, False),
    ("Rugissement", 75, anim_rugissement, False),
    ("CoupDeQueue", 42, anim_coup_de_queue, False),
    ("Course", 22, anim_course, True),
    ("Sommeil", 90, anim_sommeil, True),
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


if __name__ == "__main__":
    main()
