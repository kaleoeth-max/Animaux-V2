"""Gardien de la Forêt : le Loup des Ronces (loup mutant, style propre à lui).

Différent des autres gardiens (pas d'écailles, pas de fourrure uniforme, pas de crête d'épines) :
- corps en volumes lisses à facettes avec de vraies marques de loup (selle sombre, masque, gorge et ventre
  clairs), et le poil concentré en grandes touffes en dents de scie (crinière, plastron, joues, coudes,
  culotte, queue en panache) ;
- silhouette fine et haute, long cou, museau étroit, dentition de loup (incisives, grands crocs, petites
  dents triangulaires), babines retroussées et plis de grognement, yeux violets à pupille ronde ;
- ronces réalistes : tiges effilées (bois violet-brun puis pousse rougeâtre), épines crochues vers l'arrière,
  feuilles à trois folioles (quelques-unes rougies), mûres en grappes (noires et rouges), fleurs ; des tiges
  jaillissent du dos en arc, d'autres s'enroulent irrégulièrement au cou, aux pattes et à la queue.
Rôle : le chasseur rapide de la forêt.

Lancer :  python3 scripts/gardien_loup.py            (export + aperçus)
          python3 scripts/gardien_loup.py --no-render
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import lowpoly as lp  # noqa: E402
from lowpoly import Ellipsoid, Vector  # noqa: E402

NAME = "Gardien_Foret_Loup"
ARRIERE = Vector((0, 1, 0))
BAS = Vector((0, 0, -1))
HAUT = Vector((0, 0, 1))

# volumes du corps : fin et haut, poitrail profond, taille marquée, long cou qui monte vers la tête
COU = Ellipsoid((0, -5.9, 8.5), (1.45, 2.1, 1.65), axis=(0, 1, -0.5))
POITRAIL = Ellipsoid((0, -3.3, 7.3), (1.85, 2.4, 2.45))
DOS = Ellipsoid((0, 0.5, 7.7), (1.55, 3.2, 1.65))
HANCHES = Ellipsoid((0, 3.8, 7.5), (1.7, 2.2, 1.8))
VENTRE = Ellipsoid((0, -1.6, 6.1), (1.25, 2.6, 0.9))
SELLE = Ellipsoid((0, 0.8, 8.15), (1.45, 3.9, 1.3))        # marque sombre sur le dos
PLASTRON = Ellipsoid((0, -4.6, 6.9), (1.35, 1.3, 1.9))      # poitrail clair
TORSE = (POITRAIL, DOS, HANCHES)

# réglages du squelette et des animations (voir lib/animation.py)
ANIM = dict(
    torse=((0, 3.8, 7.5), (0, -4.8, 7.6)), tete=((0, -6.8, 8.9), (0, -12.5, 8.6)), machoire_bout=(0, -12.1, 7.3),
    pieces_torse=("Corps", "Ronces"),
    pas_marche=1.7, leve_marche=0.9, pas_course=2.0, leve_course=1.2,
    couche=-3.85, tete_couche=34, avant_couche=(-1.2, 0.0),
    # sommeil couché sur le flanc (choix de l'utilisateur, à la place de la boule)
    sommeil="cote", cote_roulis=88, cote_epaisseur=3.4, cote_tete=(8, 0, 28), cote_queue=(12, 10, 8, 6),
)


def dessus(x, y):
    z = None
    for e in TORSE:
        k = 1 - (x / e.r.x) ** 2 - ((y - e.c.y) / e.r.y) ** 2
        if k > 0:
            zz = e.c.z + e.r.z * math.sqrt(k)
            z = zz if z is None else max(z, zz)
    return z


def bord(e, y, z, k=0.82):
    """Demi-largeur de l'ellipsoïde e (aligné sur les axes) à (y, z), réduite de k."""
    q = (y - e.c.y) / e.r.y
    h = (z - e.c.z) / e.r.z
    return e.r.x * math.sqrt(max(0.08, 1 - q * q - h * h)) * k


# ---------------------------------------------------------------------------- poils en touffes

def touffe(m, nom, centre, normale, sens, nb, longueur, largeur, couleurs, ecart, seed, souleve=0.4):
    """Touffe en dents de scie : quelques longues mèches qui partent du même endroit en éventail."""
    rng = random.Random(f"touffe:{nom}:{seed}")
    n = Vector(normale).normalized()
    s0 = Vector(sens) - n * Vector(sens).dot(n)
    s0 = s0.normalized() if s0.length > 1e-4 else n.orthogonal().normalized()
    cote = n.cross(s0)
    pieces = []
    for i in range(nb):
        racine = Vector(centre) + cote * rng.uniform(-1, 1) * ecart + s0 * rng.uniform(-0.3, 0.3) * ecart
        d = s0 + cote * rng.uniform(-0.35, 0.35)
        pieces.append(m.meche(f"{nom}{i}", couleurs[rng.randrange(len(couleurs))], racine, n, d,
                              longueur * rng.uniform(0.75, 1.15), largeur * rng.uniform(0.8, 1.2),
                              souleve * rng.uniform(0.8, 1.2)))
    return pieces


def touffes_sur(m, nom, ell, positions, sens, nb, longueur, largeur, couleurs_fn, ecart, souleve=0.4):
    """Touffes posées sur un Ellipsoid aux paramètres (t, a) donnés ; couleurs_fn(t, a) -> liste de couleurs."""
    pieces = []
    for i, (t, a) in enumerate(positions):
        n = ell.normal(t, a)
        sv = sens(n) if callable(sens) else sens
        pieces += touffe(m, f"{nom}{i}_", ell.point(t, a, -0.05), n, sv, nb, longueur, largeur, couleurs_fn(t, a),
                         ecart, i, souleve)
    return pieces


def grille(t0, t1, nt, a0, a1, na):
    """Positions (t, a) réparties sur une zone d'Ellipsoid, rangées décalées en quinconce."""
    pos = []
    for i in range(nt):
        t = t0 + (t1 - t0) * i / max(nt - 1, 1)
        for k in range(na):
            pos.append((t, a0 + (a1 - a0) * (k + 0.5 * (i % 2)) / na))
    return pos


def arriere_et_bas(n):
    """Sens du poil : vers l'arrière, un peu vers le bas, en s'écartant légèrement du corps."""
    return Vector((0, 1, -0.35)) + n * 0.2


def pelage(t, a):
    """Couleur des touffes selon la position : dessus sombre, flancs gris-bleu, dessous clair."""
    lat = math.sin(math.radians(a))
    if lat > 0.4:
        return ("gris_bleu_fonce", "gris_bleu")
    if lat < -0.35:
        return ("gris_bleu_clair", "gris_bleu_clair", "gris_bleu")
    return ("gris_bleu", "gris_bleu", "gris_bleu_fonce")


# ---------------------------------------------------------------------------- ronces réalistes

def feuille_trifoliee(m, nom, p, d, rng):
    """Feuille de ronce : pétiole + trois folioles dentelées (couleurs variées, quelques-unes rougies)."""
    d = Vector(d).normalized()
    plan = d.cross(HAUT if abs(d.z) < 0.9 else ARRIERE).normalized()
    normale = plan.cross(d).normalized()
    couleur = ("feuille_fonce", "feuille_fonce", "feuille", "feuille_rouge")[rng.randrange(4)]
    bout = p + d * 0.35
    pieces = [m.tube(f"{nom}_pet", "tige_ronce", [p, bout], [0.035, 0.03], sides=3)]
    for j, ang in enumerate((0, 50, -50)):
        r = math.radians(ang)
        dd = d * math.cos(r) + plan * math.sin(r)
        taille = 1.0 if j == 0 else 0.8
        pieces.append(m.kite(f"{nom}_fol{j}", couleur, bout + dd * 0.3 * taille, normale, dd,
                             0.34 * taille, 0.62 * taille, 0.05, tilt=8))
    return pieces


def mure(m, nom, p, rng):
    """Mûre : petite grappe de drupéoles (noire si mûre, rouge sinon) au bout d'un pédoncule."""
    couleur = "mure" if rng.random() < 0.72 else "mure_rouge"
    pieces = []
    for j in range(6):
        a = 2 * math.pi * j / 5
        off = Vector((math.cos(a) * 0.08, math.sin(a) * 0.08, 0.05 * (j % 2))) if j < 5 else Vector((0, 0, 0.1))
        pieces.append(m.ico(f"{nom}_d{j}", couleur, p + off, 0.075, subdiv=0))
    return pieces


def fleur(m, nom, p, normale):
    n = Vector(normale).normalized()
    u = n.orthogonal().normalized()
    v = n.cross(u)
    pieces = [m.ico(f"{nom}_coeur", "fleur_jaune", p + n * 0.05, 0.07, subdiv=0)]
    for j in range(5):
        a = 2 * math.pi * j / 5
        d = u * math.cos(a) + v * math.sin(a)
        pieces.append(m.kite(f"{nom}_pet{j}", "fleur_blanche", p + d * 0.14, n, d, 0.2, 0.26, 0.03, tilt=12))
    return pieces


def ronce(m, prefixe, pts, seed, rayon=0.14, feuilles=1.3, fruits=2.0, fleurs=True):
    """Tige de ronce le long de pts : bois violet-brun qui s'affine en pousse rougeâtre, épines crochues
    (penchées vers la base de la tige) tous les ~0,3 stud, feuilles trifoliées, mûres et fleurs."""
    rng = random.Random(f"ronce:{prefixe}:{seed}")
    pts = [Vector(p) for p in pts]
    milieu = len(pts) // 2
    n = len(pts)
    rayons = [rayon * (1 - 0.65 * i / (n - 1)) for i in range(n)]
    pieces = [m.tube(f"{prefixe}_bois", "ronce_fonce", pts[:milieu + 1], rayons[:milieu + 1], sides=5),
              m.tube(f"{prefixe}_pousse", "tige_ronce", pts[milieu:], rayons[milieu:], sides=5)]
    longueur = 0.0
    prochaine_epine, prochaine_feuille, prochain_fruit = 0.2, feuilles * 0.5, fruits * 0.7
    tour = 0
    for i in range(1, n):
        seg = pts[i] - pts[i - 1]
        longueur += seg.length
        tg = seg.normalized()
        ref = tg.orthogonal().normalized()
        if longueur >= prochaine_epine:
            prochaine_epine += rng.uniform(0.26, 0.38) + rayon * 0.8  # plus la tige est grosse, plus elles s'espacent
            tour += 1
            a = 2.1 * tour + rng.uniform(-0.3, 0.3)  # épines réparties tout autour de la tige
            dehors = ref * math.cos(a) + tg.cross(ref) * math.sin(a)
            pieces.append(m.spike(f"{prefixe}_ep{i}_{tour}", "sable", pts[i], dehors, -tg, 0.22 + rayons[i] * 0.8,
                                  rayons[i] * 0.55, bend=0.7, sides=3, steps=3))
        if feuilles and longueur >= prochaine_feuille:
            prochaine_feuille += feuilles * rng.uniform(0.8, 1.2)
            a = rng.uniform(0, 2 * math.pi)
            dehors = ref * math.cos(a) + tg.cross(ref) * math.sin(a)
            pieces += feuille_trifoliee(m, f"{prefixe}_f{i}", pts[i], dehors + tg * 0.6, rng)
        if fruits and longueur >= prochain_fruit and i > n * 0.35:
            prochain_fruit += fruits * rng.uniform(0.8, 1.2)
            a = rng.uniform(0, 2 * math.pi)
            dehors = ref * math.cos(a) + tg.cross(ref) * math.sin(a)
            tige = pts[i] + dehors * 0.25 + BAS * 0.12
            pieces.append(m.tube(f"{prefixe}_ped{i}", "tige_ronce", [pts[i], tige], [0.03, 0.025], sides=3))
            if fleurs and rng.random() < 0.25:
                pieces += fleur(m, f"{prefixe}_fl{i}", tige, dehors)
            else:
                pieces += mure(m, f"{prefixe}_m{i}", tige + BAS * 0.08, rng)
    return pieces


def tige_en_arc(depart, sens, longueur, hauteur, seed, n=26):
    """Tige qui jaillit du dos, monte, s'arque puis retombe, avec une légère ondulation naturelle."""
    rng = random.Random(f"arc:{seed}")
    depart, sens = Vector(depart), Vector(sens).normalized()
    cote = sens.cross(HAUT).normalized()
    ph1, ph2 = rng.uniform(0, 6), rng.uniform(0, 6)
    pts = []
    for i in range(n + 1):
        u = i / n
        ondule = cote * 0.18 * math.sin(7 * u + ph1) + HAUT * 0.1 * math.sin(9 * u + ph2)
        # monte, s'arque, puis retombe dans le vide sur le côté (le bout ne rentre pas dans le corps)
        pts.append(depart + sens * longueur * u + HAUT * (hauteur * math.sin(math.pi * u * 0.7) - 0.9 * u ** 3)
                   + ondule * u)
    return pts


def enroulement(ell, t0, t1, a0, a1, seed, n=40, lift=0.12):
    """Enroulement irrégulier autour d'un Ellipsoid (pas une spirale parfaite : pas et écart qui varient)."""
    rng = random.Random(f"enroule:{seed}")
    ph = rng.uniform(0, 6)
    pts = []
    for i in range(n + 1):
        u = i / n
        t = t0 + (t1 - t0) * (u + 0.06 * math.sin(11 * u + ph))
        a = a0 + (a1 - a0) * u + 18 * math.sin(5 * u + ph)
        pts.append(ell.point(max(-0.95, min(0.95, t)), a, lift + 0.08 * math.sin(13 * u + ph) ** 2))
    return pts


def ronces_du_corps(m):
    pieces = []
    # grosses tiges qui s'enroulent autour du torse, collées au corps (posées dans la fourrure)
    for i, (ell, t0, t1, a0, a1) in enumerate(((POITRAIL, -0.6, 0.5, 30, 500), (DOS, -0.75, 0.7, 150, 640),
                                               (HANCHES, -0.45, 0.85, 300, 790))):
        pieces += ronce(m, f"r_torse{i}", enroulement(ell, t0, t1, a0, a1, 50 + i, n=40, lift=0.4), 50 + i, rayon=0.24,
                        feuilles=1.5, fruits=2.6)
    # deux pousses courtes qui dépassent des épaules
    for i, (x, y, sx, sy) in enumerate(((0.6, -2.6, 1.0, 0.4), (-0.6, -2.2, -1.0, 0.5))):
        depart = Vector((x, y, dessus(x, y) - 0.35))
        pieces.append(m.ico(f"noeud{i}", "ronce_fonce", depart + HAUT * 0.25, (0.36, 0.36, 0.42), jitter=0.04, seed=i))
        pieces += ronce(m, f"r_pousse{i}", tige_en_arc(depart, (sx, sy, 0), 1.8, 1.0, i, n=14), 10 + i, rayon=0.17,
                        feuilles=0.8, fruits=1.0)
    # collier de ronces au cou
    pieces += ronce(m, "r_cou", enroulement(COU, -0.5, 0.55, 40, 690, 3, n=44, lift=0.4), 3, rayon=0.24,
                    feuilles=1.6, fruits=2.6)
    m.join("Ronces", pieces)


# ---------------------------------------------------------------------------- corps

def corps(m):
    pieces = [m.ellipsoid("cou", "gris_bleu", COU, jitter=0.05, seed=1),
              m.ellipsoid("poitrail", "gris_bleu", POITRAIL, jitter=0.06, seed=2),
              m.ellipsoid("dos", "gris_bleu", DOS, jitter=0.06, seed=3),
              m.ellipsoid("hanches", "gris_bleu", HANCHES, jitter=0.06, seed=4),
              m.ellipsoid("ventre", "gris_bleu_clair", VENTRE, jitter=0.05, seed=5),
              m.ellipsoid("selle", "gris_bleu_fonce", SELLE, jitter=0.05, seed=6),
              m.ellipsoid("plastron", "gris_bleu_clair", PLASTRON, jitter=0.05, seed=7)]
    # fourrure en grandes touffes (comme la queue) sur tout le corps : sombre dessus, claire dessous
    pieces += touffes_sur(m, "pc", COU, grille(-0.85, 0.75, 5, -90, 270, 9), arriere_et_bas, 3, 1.9, 0.3, pelage,
                          0.4, souleve=0.35)
    pieces += touffes_sur(m, "pp", POITRAIL, grille(-0.9, 0.7, 6, -90, 270, 11), arriere_et_bas, 3, 1.7, 0.3, pelage,
                          0.4, souleve=0.32)
    pieces += touffes_sur(m, "pd", DOS, grille(-0.8, 0.8, 6, -90, 270, 10), arriere_et_bas, 3, 1.7, 0.28, pelage,
                          0.4, souleve=0.32)
    pieces += touffes_sur(m, "ph", HANCHES, grille(-0.5, 0.95, 5, -90, 270, 10), arriere_et_bas, 3, 1.7, 0.28, pelage,
                          0.4, souleve=0.32)
    # crinière plus longue autour du cou, plastron clair et frange sous le ventre
    pieces += touffes_sur(m, "crin", COU, [(t, a) for t in (0.15, 0.55) for a in range(-80, 280, 30)],
                          lambda n: Vector((0, 1, -0.35)) + n * 0.25, 3, 2.3, 0.32, pelage, 0.45, souleve=0.45)
    pieces += touffes_sur(m, "plas", PLASTRON, [(t, a) for t in (-0.5, 0.0, 0.45) for a in (245, 270, 295)],
                          Vector((0, 0.15, -1)), 3, 1.9, 0.28, lambda t, a: ("gris_bleu_clair",), 0.35, souleve=0.4)
    pieces += touffes_sur(m, "vent", VENTRE, [(t, 270) for t in (-0.6, -0.2, 0.2, 0.6)], Vector((0, 0.6, -1)), 3, 1.3,
                          0.22, lambda t, a: ("gris_bleu_clair",), 0.4, souleve=0.3)
    m.join("Corps", pieces)


# ---------------------------------------------------------------------------- pattes

PATTES = (("AvG", 1.35, -3.4, True), ("AvD", -1.35, -3.4, True),
          ("ArG", 1.4, 4.0, False), ("ArD", -1.4, 4.0, False))
PATTES_AVEC_RONCE = ("AvG", "ArD")  # en diagonale, comme si la bête s'était prise dans un roncier


def articulations(x, y, avant):
    """Points d'articulation d'une patte (longues pattes de loup), du haut vers le pied."""
    s = 1 if x > 0 else -1
    if avant:  # épaule, coude bien replié en arrière (réserve pour le galop), poignet
        return [Vector((x, y, 7.0)), Vector((x + 0.25 * s, y + 1.4, 4.3)), Vector((x + 0.3 * s, y + 0.1, 1.0))]
    # hanche, genou (vers l'avant), jarret haut (replié en arrière), cheville
    return [Vector((x, y, 7.2)), Vector((x + 0.25 * s, y - 1.4, 5.0)), Vector((x + 0.4 * s, y + 1.4, 2.5)),
            Vector((x + 0.45 * s, y + 0.5, 0.95))]


def patte(m, nom, x, y, avant):
    s = 1 if x > 0 else -1
    if avant:
        haut_, milieu, poignet = articulations(x, y, avant)
        epaule = Ellipsoid((x + 0.1 * s, y, 6.6), (1.15, 1.6, 1.8))
        bras = Ellipsoid.between(haut_, milieu, 1.0, 1.1, extra=1.08, up=(0, 1, 0))
        pieces = [m.ellipsoid("epaule", "gris_bleu", epaule, jitter=0.05, seed=1),
                  m.ellipsoid("bras", "gris_bleu", bras, jitter=0.04, seed=2)]
        pieces += touffes_sur(m, "te", epaule, grille(-0.8, 0.8, 4, -90, 270, 7), lambda n: Vector((0, 0.5, -1)) + n * 0.2,
                              3, 1.4, 0.24, pelage, 0.3, souleve=0.3)
        pieces += touffes_sur(m, "tb", bras, grille(-0.7, 0.6, 3, 0, 360, 6), lambda n: Vector((0, 0.4, -1)) + n * 0.2,
                              2, 1.1, 0.2, pelage, 0.2, souleve=0.3)
        segments = [(milieu, poignet, [0.68, 0.6, 0.52])]
        # touffe derrière le coude
        pieces += touffe(m, "coude", milieu + Vector((0.1 * s, 0.55, 0.2)), (0.3 * s, 1, 0), (0, 0.6, -1), 4, 1.2, 0.2,
                         ("gris_bleu", "gris_bleu_fonce"), 0.3, 1, souleve=0.45)
    else:
        haut_, milieu, jarret, poignet = articulations(x, y, avant)
        cuisse = Ellipsoid((x + 0.15 * s, y - 0.3, 6.3), (1.35, 2.1, 2.2))
        pieces = [m.ellipsoid("cuisse", "gris_bleu", cuisse, jitter=0.05, seed=1)]
        segments = [(milieu, jarret, [0.72, 0.6, 0.48]), (jarret, poignet, [0.5, 0.46, 0.46])]
        pieces += touffes_sur(m, "tcu", cuisse, grille(-0.85, 0.85, 5, -90, 270, 8),
                              lambda n: Vector((0, 0.6, -1)) + n * 0.2, 3, 1.5, 0.26, pelage, 0.35, souleve=0.3)
        # culotte : longues touffes à l'arrière de la cuisse
        pieces += touffes_sur(m, "culotte", cuisse, [(0.55, a) for a in ((10, 200) if s < 0 else (-20, 170))[:1]]
                              + [(0.7, 120 if s > 0 else 60), (0.85, 90)],
                              Vector((0, 0.5, -1)), 4, 1.6, 0.25, pelage, 0.4, souleve=0.45)
        pieces += touffe(m, "jarret", jarret + Vector((0, 0.35, 0.1)), (0, 1, 0.2), (0, 0.3, -1), 3, 0.8, 0.16,
                         ("gris_bleu",), 0.2, 2, souleve=0.4)
    pieces.append(m.ico("articulation", "gris_bleu", milieu, 0.75, jitter=0.05, seed=4))
    for i, (p1, p2, rayons) in enumerate(segments):
        d = (p2 - p1).normalized()
        seg = Ellipsoid.between(p1, p2, rayons[0], extra=1.15, up=(0, 1, 0))
        bas = Ellipsoid.between(p1.lerp(p2, 0.5), p2 + d * 0.3, rayons[-1] * 1.1, extra=1.15, up=(0, 1, 0))
        pieces.append(m.ellipsoid(f"seg{i}", "gris_bleu" if i == 0 and not avant else "gris_bleu_clair", seg,
                                  jitter=0.03, seed=5 + i))
        pieces.append(m.ellipsoid(f"bas{i}", "gris_bleu_clair", bas, jitter=0.03, seed=7 + i))
    if nom in PATTES_AVEC_RONCE:  # ronce enroulée irrégulièrement autour du bas de la patte
        p1, p2, rayons = segments[-1]
        lien = Ellipsoid.between(p1, p2, rayons[0] * 1.05, extra=1.0, up=(0, 1, 0))
        pieces += ronce(m, "r_patte", enroulement(lien, -0.85, 0.75, 0, 640, 20 + int(x * 10), n=28, lift=0.12),
                        20 + int(x * 10), rayon=0.17, feuilles=1.5, fruits=0)

    # patte de loup : coussinet, 4 doigts, griffes sombres + ergot arrière
    pied = Vector((poignet.x, poignet.y - 0.45, 0.45))
    pieces.append(m.ellipsoid("pied", "gris_bleu_clair", Ellipsoid(pied, (0.72, 0.92, 0.45)), jitter=0.03))
    for k, ang in enumerate((-32, -11, 11, 32)):
        r = math.radians(ang)
        d = Vector((math.sin(r), -math.cos(r), 0))
        doigt = pied + d * 0.7 + Vector((0, 0, -0.07))
        pieces.append(m.ellipsoid(f"doigt{k}", "gris_bleu_clair", Ellipsoid(doigt, (0.24, 0.32, 0.29), axis=d)))
        pieces.append(m.spike(f"griffe{k}", "brun_noir", doigt + d * 0.27, d + Vector((0, 0, -0.1)), BAS, 0.42, 0.11,
                              bend=0.5, steps=4))
    pieces.append(m.spike("griffe_arr", "brun_noir", pied + Vector((0.3 * s, 0.6, 0.3)), (0.2 * s, 1, 0), BAS, 0.32,
                          0.09, bend=0.5))
    m.join(f"Patte_{nom}", pieces)


# ---------------------------------------------------------------------------- queue

QUEUE = [Vector(p) for p in ((0, 5.8, 7.9), (0, 7.8, 7.4), (0, 9.8, 6.4), (0.3, 11.6, 5.2),
                             (0.6, 13.2, 4.3), (0.7, 14.6, 3.8))]
RAYONS_QUEUE = [0.55, 0.7, 0.75, 0.7, 0.5]


def queue(m):
    """Queue en panache : tronçons couverts de grandes touffes qui s'écartent, bout sombre comme un vrai loup."""
    pieces = []
    for i, r in enumerate(RAYONS_QUEUE):
        tr = Ellipsoid.between(QUEUE[i], QUEUE[i + 1], r, extra=1.25)
        bout = i == len(RAYONS_QUEUE) - 1
        pieces.append(m.ellipsoid(f"troncon{i}", "gris_bleu_fonce" if bout else "gris_bleu", tr, jitter=0.03))
        d = (QUEUE[i + 1] - QUEUE[i]).normalized()
        pieces += touffes_sur(m, f"pq{i}_", tr, [(t, a) for t in (-0.5, 0.2) for a in range(0, 360, 60)],
                              lambda n, d=d: d + n * 0.35, 3, 1.8 + 0.3 * (i in (1, 2, 3)), 0.28,
                              (lambda t, a: ("gris_bleu_fonce",)) if bout else pelage, 0.35, souleve=0.35)
    lien = Ellipsoid.between(QUEUE[0], QUEUE[2], 0.62, extra=1.0)
    pieces += ronce(m, "r_queue", enroulement(lien, -0.8, 0.8, 0, 560, 40, n=26, lift=0.35), 40, rayon=0.18,
                    feuilles=1.4, fruits=2.2)
    m.join("Queue", pieces)


# ---------------------------------------------------------------------------- tête

CRANE = Ellipsoid((0, -7.6, 9.4), (1.5, 1.85, 1.4))
NEZ = Ellipsoid((0, -9.6, 9.1), (0.8, 2.2, 0.55))            # chanfrein (marque sombre)
MUSEAU = Ellipsoid((0, -10.4, 8.6), (0.72, 2.15, 0.6))       # museau long et étroit, clair
GENCIVE_HAUT = Ellipsoid((0, -10.1, 8.2), (0.66, 2.5, 0.12))
MACHOIRE = Ellipsoid((0, -10.0, 7.5), (0.7, 2.35, 0.45), axis=(0, 1, 0.08))
CHARNIERE = (0, -8.0, 7.95)
OUVERTURE = 14  # il grogne : gueule entrouverte, crocs bien visibles
LEVRE_HAUT = 8.15
LEVRE = 8.3
LEVRE_BAS = 7.8
OEIL_Y, OEIL_Z = -8.75, 9.65
PAUPIERE_SORTIE = 0.4


def bord_haut(y, z, k=0.82):
    return max(bord(MUSEAU, y, z, k), bord(CRANE, y, z, k))


def dent(m, nom, base, vers, longueur, rayon, recourbe=0.2):
    return m.spike(nom, "dent", base, vers, ARRIERE, longueur, rayon, bend=recourbe, sides=3, steps=2)


def tete(m):
    pieces = [m.ellipsoid("crane", "gris_bleu", CRANE, jitter=0.03, seed=1),
              m.ellipsoid("chanfrein", "gris_bleu_fonce", NEZ, jitter=0.02, seed=2),
              m.ellipsoid("museau", "gris_bleu_clair", MUSEAU, jitter=0.02, seed=3),
              m.ellipsoid("gencive", "gueule", GENCIVE_HAUT),
              m.ellipsoid("truffe", "brun_noir", Ellipsoid((0, -12.4, 8.85), (0.4, 0.36, 0.3)))]
    # plis de grognement discrets sur les côtés du museau (le loup retrousse les babines)
    for s in (1, -1):
        for k, y in enumerate((-11.0, -10.55)):
            x = bord(MUSEAU, y, 8.85, 0.97)
            pieces.append(m.tube(f"pli{k}{s}", "gris_bleu", [(x * s * 0.6, y + 0.15, 9.05), (x * s, y, 8.8),
                                                             (x * s * 1.02, y - 0.1, 8.5)], 0.035, sides=4))
    pieces += touffes_sur(m, "tc", CRANE, grille(-0.3, 0.85, 4, 20, 160, 6), arriere_et_bas, 2, 1.0, 0.2, pelage,
                          0.25, souleve=0.3)
    for s in (1, -1):
        pieces.append(m.box(f"narine{s}", "gueule", (0.16 * s, -12.72, 8.85), (0.08, 0.06, 0.06), bevel=0.3))
        pieces += oeil(m, s)
        # sourcil sombre + tache claire au-dessus de l'oeil (marque typique du loup)
        pieces.append(m.tube(f"arcade{s}", "gris_bleu_fonce",
                             [(0.3 * s, -9.4, 10.0), (0.85 * s, -9.15, 10.15), (1.25 * s, -8.6, 10.1),
                              (1.35 * s, -8.0, 9.85)], [0.15, 0.2, 0.18, 0.06], sides=6))
        pieces.append(m.ellipsoid(f"tache{s}", "gris_bleu_clair", Ellipsoid((0.75 * s, -9.0, 10.0), (0.28, 0.24, 0.14))))
        # grande oreille triangulaire, enracinée dans le crâne, avec une touffe claire à l'intérieur
        racine = Vector((0.68 * s, -7.3, 10.15))
        assert CRANE.inside(racine), "l'oreille doit être enracinée dans le crâne"
        ext = [racine, Vector((0.95 * s, -6.95, 11.7)), Vector((1.15 * s, -6.7, 13.0))]
        pieces.append(m.tube(f"oreille{s}", "gris_bleu_fonce", ext, [0.7, 0.55, 0.0], sides=6, ring_scale=(1.0, 0.32),
                             up=(0, 1, 0)))
        # base de l'oreille : bourrelet de peau + touffes qui la soudent au crâne (plus de coin dans le vide)
        base_oreille = Ellipsoid((0.75 * s, -7.2, 10.45), (0.7, 0.42, 0.55))
        assert CRANE.inside(base_oreille.c), "la base de l'oreille doit être dans le crâne"
        pieces.append(m.ellipsoid(f"base_oreille{s}", "gris_bleu_fonce", base_oreille, jitter=0.03))
        pieces += touffes_sur(m, f"bo{s}", base_oreille, [(t, a) for t in (-0.3, 0.4) for a in range(0, 360, 60)],
                              lambda n: n + Vector((0, 0.6, 0.3)), 2, 0.8, 0.18, pelage, 0.15, souleve=0.4)
        pieces.append(m.tube(f"oreille_int{s}", "gris_bleu_clair", [p + Vector((0, -0.16, 0.05)) for p in ext],
                             [0.45, 0.36, 0.0], sides=6, ring_scale=(1.0, 0.2), up=(0, 1, 0)))
        pieces += touffe(m, f"oreille_touffe{s}", Vector((0.95 * s, -7.1, 11.2)), (0.2 * s, -1, 0), HAUT, 3, 0.8, 0.12,
                         ("gris_bleu_clair",), 0.15, 5, souleve=0.4)
        # joues : grosse collerette de touffes claires vers l'arrière et l'extérieur
        joue = Ellipsoid((1.05 * s, -7.9, 8.6), (0.55, 0.95, 0.7))
        pieces.append(m.ellipsoid(f"joue{s}", "gris_bleu_clair", joue, jitter=0.03, seed=3))
        pieces += touffes_sur(m, f"jt{s}", joue, [(t, a) for t in (-0.2, 0.4) for a in ((-40, 0, 40) if s > 0 else
                                                                                       (140, 180, 220))],
                              Vector((s * 0.5, 1, -0.3)), 3, 1.7, 0.24, lambda t, a: ("gris_bleu_clair", "gris_bleu"),
                              0.3, souleve=0.4)
        # dentition de loup : incisives, grand croc, petites dents triangulaires derrière
        for k, x in enumerate((0.12, 0.3)):
            pieces.append(dent(m, f"incisive{k}{s}", (x * s, -12.0 + 0.12 * k, LEVRE_HAUT + 0.08), (0, -0.1, -1),
                               0.24, 0.07, 0.1))
        base_croc = (s * bord(GENCIVE_HAUT, -11.45, LEVRE_HAUT + 0.08, 0.85), -11.45, LEVRE_HAUT + 0.08)
        assert GENCIVE_HAUT.inside(base_croc, 0.05), "le croc doit partir de la gencive"
        pieces.append(dent(m, f"croc{s}", base_croc, (0.05 * s, -0.1, -1), 1.05, 0.17, 0.3))
        for k in range(6):
            y = -10.85 + 0.42 * k
            base = (s * min(bord_haut(y, LEVRE_HAUT), bord(GENCIVE_HAUT, y, LEVRE_HAUT + 0.08, 0.9)), y,
                    LEVRE_HAUT + 0.08)
            assert GENCIVE_HAUT.inside(base, 0.05), "chaque dent doit partir de la gencive"
            pieces.append(dent(m, f"molaire{k}{s}", base, (0.1 * s, 0, -1), 0.32 - 0.02 * k, 0.15, 0.05))
        # babine du haut, retroussée au-dessus du croc (grognement)
        pieces.append(m.tube(f"levre{s}", "brun_noir",
                             [(s * bord_haut(y, LEVRE, 0.97), y, LEVRE + 0.22 * math.exp(-((y + 11.4) / 0.5) ** 2))
                              for y in [-8.3 - 0.33 * k for k in range(12)]] + [(0.2 * s, -12.3, LEVRE + 0.05)],
                             0.06, sides=5))
    pieces.append(m.ellipsoid("gueule", "gueule", Ellipsoid((0, -10.0, 7.95), (0.6, 2.3, 0.28))))
    m.join("Tete", pieces)

    mach = [m.ellipsoid("machoire", "gris_bleu_clair", MACHOIRE, jitter=0.02),
            m.ellipsoid("menton", "gris_bleu_clair", Ellipsoid((0, -11.7, 7.25), (0.5, 0.5, 0.36)), jitter=0.02),
            m.ellipsoid("gencive_bas", "gueule", Ellipsoid((0, -10.1, 7.88), (0.6, 2.2, 0.09))),
            m.ellipsoid("langue", "truffe", Ellipsoid((0, -10.3, 7.93), (0.4, 1.7, 0.09)))]
    # gorge : touffes claires qui pendent sous la mâchoire, vers l'arrière
    mach += touffes_sur(m, "gorge", MACHOIRE, [(t, 270) for t in (-0.1, 0.3, 0.7)], Vector((0, 1, -0.7)), 3, 1.3,
                        0.2, lambda t, a: ("gris_bleu_clair",), 0.3, souleve=0.35)
    for s in (1, -1):
        mach.append(m.ellipsoid(f"angle{s}", "gris_bleu", Ellipsoid((0.7 * s, -8.2, 7.6), (0.42, 0.8, 0.45)),
                                jitter=0.03, seed=6))
        for k, x in enumerate((0.1, 0.26)):
            mach.append(dent(m, f"incisive_bas{k}{s}", (x * s, -11.75 + 0.12 * k, LEVRE_BAS - 0.06), (0, -0.1, 1),
                             0.2, 0.06, 0.1))
        base = (s * bord(MACHOIRE, -11.1, LEVRE_BAS, 0.86), -11.1, LEVRE_BAS - 0.08)
        assert MACHOIRE.inside(base), "le croc du bas doit partir de la mâchoire"
        mach.append(dent(m, f"croc_bas{s}", base, (0.1 * s, -0.1, 1), 0.8, 0.15, 0.25))
        for k in range(5):
            y = -10.55 + 0.45 * k
            base = (s * bord(MACHOIRE, y, LEVRE_BAS, 0.86), y, LEVRE_BAS - 0.08)
            assert MACHOIRE.inside(base), "chaque dent du bas doit partir de la mâchoire"
            mach.append(dent(m, f"molaire_bas{k}{s}", base, (0.1 * s, 0, 1), 0.28, 0.13, 0.05))
        z = LEVRE_BAS + 0.1
        avant = MACHOIRE.c.y - MACHOIRE.r.y * math.sqrt(max(0.0, 1 - ((z - MACHOIRE.c.z) / MACHOIRE.r.z) ** 2))
        mach.append(m.tube(f"levre_bas{s}", "brun_noir",
                           [(s * bord(MACHOIRE, y, z, 0.98), y, z) for y in [-8.3 - 0.3 * k for k in range(13)]
                            if y > avant + 0.15] + [(0.16 * s, avant + 0.05, z)], 0.05, sides=5))
    machoire = m.join("Machoire", mach)
    m.rotate_about([machoire], OUVERTURE, "X", CHARNIERE)

    for nom, s in (("Oeil_G", 1), ("Oeil_D", -1)):  # iris violet : Material = Neon dans Roblox
        c, n, _, _, rh, rv = repere_oeil(s)
        m.ellipsoid(nom, "oeil_violet", Ellipsoid(c + n * 0.03, (rh, 0.16, rv), axis=n), subdiv=2)
        m.ellipsoid(f"Paupiere_{nom[-1]}", "gris_bleu", Ellipsoid(c - n * PAUPIERE_SORTIE * 0.75,
                                                                 (rh * 1.12, 0.13, rv * 1.2), axis=n), subdiv=2)


def repere_oeil(s):
    x = bord(CRANE, OEIL_Y, OEIL_Z, 1.0)
    c = Vector((x * s, OEIL_Y, OEIL_Z))
    n = Vector((0.72 * s, -0.68, 0.12)).normalized()  # yeux de prédateur, tournés vers l'avant
    hx = n.cross(HAUT).normalized()
    return c, n, hx, hx.cross(n), 0.36, 0.2


def oeil(m, s):
    """Oeil de loup en amande : contour sombre, pupille ronde (pas de fente de reptile), regard en biais."""
    c, n, hx, hz, rh, rv = repere_oeil(s)
    avant = 1 if hx.y < 0 else -1
    pieces = [m.ellipsoid(f"orbite{s}", "brun_noir", Ellipsoid(c - n * 0.05, (rh * 1.3, 0.16, rv * 1.45), axis=n))]
    pieces.append(m.ico(f"pupille{s}", "brun_noir", c + n * 0.19, (0.09, 0.09, 0.09), subdiv=1))
    pieces.append(m.ico(f"reflet{s}", "blanc_doux", c + n * 0.2 + hz * rv * 0.35 + hx * avant * rh * 0.3, 0.035,
                        subdiv=0))
    haut, bas = [], []
    for i in range(9):
        phi = math.pi * i / 8
        cx = math.cos(phi)
        haut.append(c + n * 0.15 + hx * rh * 1.12 * cx + hz * (rv * 0.55 * math.sin(phi) + 0.03 - 0.16 * avant * cx))
        bas.append(c + n * 0.08 + hx * rh * 1.05 * cx - hz * rv * 1.05 * math.sin(phi))
    pieces.append(m.tube(f"paupiere_h{s}", "gris_bleu_fonce", haut,
                         [0.05, 0.09, 0.11, 0.12, 0.12, 0.12, 0.11, 0.09, 0.05], sides=6, ring_scale=(1.0, 0.75)))
    pieces.append(m.tube(f"paupiere_b{s}", "brun_noir", bas, [0.03, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.03],
                         sides=5))
    return pieces


def build():
    lp.reset_scene()
    m = lp.Model(NAME)
    corps(m)
    ronces_du_corps(m)
    for nom, x, y, avant in PATTES:
        patte(m, nom, x, y, avant)
    queue(m)
    tete(m)
    return m


if __name__ == "__main__":
    model = build()
    st = model.stats()
    print("stats", st["pieces"], "pièces,", st["triangles"], "triangles")
    for nom, t in sorted(st["par_piece"].items()):
        print("   ", nom, t)
    print("point le plus bas :", round(min(v.co.z for o in model.parts for v in o.data.vertices), 2))
    model.export()
    if "--no-render" not in sys.argv:
        tete_c = (0, -10.2, 8.4)
        vues = ((35, "avant"), (215, "arriere"), (28, "tete", 2.4, (0, -9.2, 9.2)),
                (0, "tete_face", 3.0, tete_c, 0.4), (90, "tete_profil", 2.8, tete_c, 0.6),
                (125, "tete_arriere", 2.6, (0, -8.8, 9.0), 2.2))
        for p in lp.render_previews(model, views=vues):
            print("preview", p)
