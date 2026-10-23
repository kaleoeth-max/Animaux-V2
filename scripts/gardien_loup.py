"""Gardien de la Forêt : le Loup des Ronces (loup mutant, même direction artistique que les autres gardiens).

Loup élancé à longues pattes, fourrure gris-bleu nuit (dos plus foncé, ventre clair), grosse crinière autour
du cou, crête d'épines blanches sur l'échine, ronces violet sombre enroulées en spirale autour du corps, du cou,
des pattes et de la queue (épines, feuilles, mûres), long museau à gueule pleine de crocs et grands crocs,
grandes oreilles pointues, yeux violets lumineux, pattes à quatre doigts griffus, longue queue touffue.
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

# volumes du corps : poitrail profond, taille fine, croupe musclée
COU = Ellipsoid((0, -5.6, 8.1), (1.8, 2.0, 2.0))
POITRAIL = Ellipsoid((0, -3.1, 7.2), (2.3, 2.6, 2.7))
DOS = Ellipsoid((0, 0.6, 7.5), (2.0, 3.2, 2.0))
HANCHES = Ellipsoid((0, 3.8, 7.3), (2.1, 2.3, 2.1))
VENTRE = Ellipsoid((0, -1.0, 5.7), (1.6, 3.4, 1.1))
CRINIERE = Ellipsoid((0, -5.0, 7.9), (2.4, 1.8, 2.5))
TORSE = (COU, POITRAIL, DOS, HANCHES)

# réglages du squelette et des animations (voir lib/animation.py)
ANIM = dict(
    torse=((0, 3.8, 7.3), (0, -4.8, 7.6)), tete=((0, -6.6, 8.6), (0, -12.4, 8.4)), machoire_bout=(0, -11.9, 6.9),
    pieces_torse=("Corps", "Ronces"),
    pas_marche=1.7, leve_marche=0.9, pas_course=2.0, leve_course=1.2,
    couche=-3.6, tete_couche=14, avant_couche=(-1.2, 0.0),
)


def couleur_corps(t, a, rng):
    """Dos gris-bleu foncé, flancs gris-bleu, ventre clair (comme un vrai loup)."""
    lat = math.sin(math.radians(a))
    if lat < -0.45:
        return "gris_bleu_clair"
    if lat > 0.55:
        return "gris_bleu_fonce"
    return "gris_bleu_fonce" if rng.random() < 0.25 else "gris_bleu"


def couleur_patte(t, a, rng):
    return "gris_bleu_clair" if rng.random() < 0.35 else ("gris_bleu", "gris_bleu_fonce")[rng.randrange(2)]


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


# ---------------------------------------------------------------------------- ronces

def spirale(ell, t0, t1, a0, a1, n=40, lift=0.12):
    """Points d'une spirale posée sur un Ellipsoid (pour enrouler une ronce)."""
    return [ell.point(t0 + (t1 - t0) * i / n, a0 + (a1 - a0) * i / n, lift) for i in range(n + 1)]


def ronce(m, prefixe, pts, seed, rayon=0.13):
    """Tige de ronce le long de pts, avec épines blanches, quelques feuilles et des mûres."""
    rng = random.Random(f"ronce:{prefixe}:{seed}")
    pts = [Vector(p) for p in pts]
    pieces = [m.tube(prefixe, "ronce", pts, rayon, sides=5)]
    for i in range(1, len(pts) - 1):
        tg = (pts[i + 1] - pts[i - 1]).normalized()
        dehors = tg.cross(Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))).normalized()
        if i % 2 == 0:
            pieces.append(m.spike(f"{prefixe}_ep{i}", "os", pts[i], dehors, tg, 0.4, 0.08, bend=0.25, sides=3,
                                  steps=2))
        if i % 6 == 3:
            pieces.append(m.kite(f"{prefixe}_f{i}", "feuille_fonce", pts[i] + dehors * 0.1, dehors, tg, 0.4, 0.6,
                                 0.06, tilt=10))
        if i % 9 == 5:
            for j in range(3):
                pieces.append(m.ico(f"{prefixe}_m{i}{j}", "mure", pts[i] + dehors * 0.18 + tg * (0.12 * (j - 1)),
                                    0.12, subdiv=1))
    return pieces


def ronces_du_corps(m):
    pieces = []
    # posées par-dessus la fourrure (lift) et assez épaisses pour bien se voir
    pieces += ronce(m, "r_poitrail", spirale(POITRAIL, -0.55, 0.6, 20, 700, n=48, lift=0.25), 1, rayon=0.2)
    pieces += ronce(m, "r_hanches", spirale(HANCHES, -0.5, 0.75, 200, 830, n=44, lift=0.25), 2, rayon=0.2)
    pieces += ronce(m, "r_cou", spirale(COU, -0.4, 0.5, 60, 520, n=34, lift=0.55), 3, rayon=0.2)
    m.join("Ronces", pieces)


# ---------------------------------------------------------------------------- corps

def corps(m):
    pieces = [m.ellipsoid(f"vol{i}", "gris_bleu_fonce", e, jitter=0.06, seed=i) for i, e in enumerate(TORSE)]
    pieces.append(m.ellipsoid("ventre", "gris_bleu_clair", VENTRE))
    pieces.append(m.ellipsoid("criniere", "gris_bleu_fonce", CRINIERE))
    zones = ((COU, 7, (-0.85, 0.6), 0.65, 1.7), (POITRAIL, 9, (-0.9, 0.6), 0.7, 1.7),
             (DOS, 9, (-0.75, 0.8), 0.7, 1.7), (HANCHES, 8, (-0.45, 0.95), 0.7, 1.6))
    for i, (e, rangs, plage, pas, longueur) in enumerate(zones):
        pieces += m.fur(f"po{i}_", e, rangs, plage, (-90, 270), couleur_corps, ARRIERE, pas, souleve=0.1,
                        longueur=longueur, seed=i)
    pieces += m.fur("pv_", VENTRE, 7, (-0.8, 0.8), (225, 315), lambda t, a, r: "gris_bleu_clair", ARRIERE, 0.55,
                    souleve=0.08)
    # crinière : longues mèches qui retombent vers l'arrière et vers le bas
    pieces += m.fur("pcr", CRINIERE, 8, (-0.9, 0.7), (-90, 270),
                    lambda t, a, r: ("gris_bleu", "gris_bleu_fonce", "gris_bleu_clair")[r.randrange(3)],
                    Vector((0, 1, -0.6)), 0.6, souleve=0.22, longueur=2.4, seed=7)

    # crête d'épines blanches sur l'échine (poils hérissés devenus épines)
    rng = random.Random("crete")
    n = 12
    for i in range(n):
        y = -6.2 + i * (11.6 / (n - 1)) + rng.uniform(-0.2, 0.2)
        L = (0.8 + 1.4 * math.exp(-((y + 3.5) / 3.0) ** 2)) * rng.uniform(0.8, 1.1)
        z = dessus(0, y)
        if z is None:
            continue
        pieces.append(m.spike(f"epine{i}", "os", (0, y, z - 0.2), (0, 0.2, 1), ARRIERE, L, 0.3 + 0.08 * L, bend=0.6))
        if i % 2 == 0:
            for s in (1, -1):
                zc = dessus(0.9, y + 0.3)
                if zc is not None:
                    pieces.append(m.spike(f"epine{i}_{s}", "os", (0.9 * s, y + 0.3, zc - 0.15), (0.6 * s, 0.2, 1),
                                          ARRIERE, L * 0.5, 0.22, bend=0.5))
    m.join("Corps", pieces)


# ---------------------------------------------------------------------------- pattes

PATTES = (("AvG", 1.7, -3.3, True), ("AvD", -1.7, -3.3, True),
          ("ArG", 1.7, 4.0, False), ("ArD", -1.7, 4.0, False))


def articulations(x, y, avant):
    """Points d'articulation d'une patte (longues pattes de loup), du haut vers le pied."""
    s = 1 if x > 0 else -1
    if avant:  # épaule, coude (en arrière), poignet
        # coude bien replié en arrière : la patte garde de la réserve quand le corps se cabre au galop
        return [Vector((x, y, 7.0)), Vector((x + 0.3 * s, y + 1.4, 4.3)), Vector((x + 0.35 * s, y + 0.1, 1.0))]
    # hanche, genou (vers l'avant), jarret haut (replié en arrière), cheville
    return [Vector((x, y, 7.1)), Vector((x + 0.3 * s, y - 1.4, 4.9)), Vector((x + 0.45 * s, y + 1.3, 2.5)),
            Vector((x + 0.5 * s, y + 0.5, 0.95))]


def patte(m, nom, x, y, avant):
    s = 1 if x > 0 else -1
    if avant:
        haut_, milieu, poignet = articulations(x, y, avant)
        epaule = Ellipsoid((x + 0.1 * s, y, 6.6), (1.3, 1.7, 1.9))
        bras = Ellipsoid.between(haut_, milieu, 0.95, 1.05, extra=1.08, up=(0, 1, 0))
        pieces = [m.ellipsoid("epaule", "gris_bleu_fonce", epaule), m.ellipsoid("bras", "gris_bleu_fonce", bras)]
        pieces += m.fur("pe", epaule, 7, (-0.85, 0.85), (-90, 270), couleur_corps, BAS, 0.55, souleve=0.1)
        pieces += m.fur("pb", bras, 6, (-0.8, 0.85), (0, 360), couleur_corps, None, 0.5, souleve=0.1, seed=1)
        segments = [(milieu, poignet, [0.7, 0.6, 0.52])]
    else:
        haut_, milieu, jarret, poignet = articulations(x, y, avant)
        cuisse = Ellipsoid((x + 0.15 * s, y - 0.3, 6.2), (1.5, 2.2, 2.3))
        pieces = [m.ellipsoid("cuisse", "gris_bleu_fonce", cuisse)]
        pieces += m.fur("pc", cuisse, 9, (-0.85, 0.9), (-90, 270), couleur_corps, Vector((0, 0.6, -1)), 0.6,
                        souleve=0.1, longueur=1.6)
        segments = [(milieu, jarret, [0.75, 0.65, 0.5]), (jarret, poignet, [0.5, 0.48, 0.48])]
    pieces.append(m.ico("articulation", "gris_bleu_fonce", milieu, 0.7, jitter=0.05, seed=4))
    for i, (p1, p2, rayons) in enumerate(segments):
        d = (p2 - p1).normalized()
        seg = Ellipsoid.between(p1, p2, rayons[0], extra=1.15, up=(0, 1, 0))
        bas = Ellipsoid.between(p1.lerp(p2, 0.5), p2 + d * 0.3, rayons[-1] * 1.1, extra=1.15, up=(0, 1, 0))
        pieces.append(m.ellipsoid(f"seg{i}", "gris_bleu_fonce", seg))
        pieces.append(m.ellipsoid(f"bas{i}", "gris_bleu_fonce", bas))
        pieces += m.fur(f"ps{i}", seg, 6, (-0.85, 0.7), (0, 360), couleur_patte, None, 0.42, souleve=0.08,
                        seed=10 + i)
        pieces += m.fur(f"pp{i}", bas, 4, (-0.2, 0.8), (0, 360), couleur_patte, None, 0.4, souleve=0.06,
                        seed=20 + i)
    # ronce enroulée autour de la patte (le bas de patte, celui qui bouge le plus)
    p1, p2, rayons = segments[-1]
    lien = Ellipsoid.between(p1, p2, rayons[0] * 1.05, extra=1.0, up=(0, 1, 0))
    pieces += ronce(m, "r_patte", spirale(lien, -0.8, 0.7, 0, 760, n=30, lift=0.08), 10 + int(x * 10), rayon=0.1)
    pieces.append(m.spike("ergot", "os", milieu + Vector((0, 0.6, 0.0)), (0.3 * s, 1, 0.3), BAS, 0.8, 0.2, bend=0.3))

    # patte de loup : coussinet, 4 doigts, griffes sombres + ergot arrière
    pied = Vector((poignet.x, poignet.y - 0.45, 0.45))
    vol = Ellipsoid(pied, (0.75, 0.95, 0.45))
    pieces.append(m.ellipsoid("pied", "gris_bleu_fonce", vol))
    pieces += m.fur("pf", vol, 3, (-0.6, 0.6), (30, 150), couleur_patte, Vector((0, -1, 0)), 0.35, souleve=0.05,
                    longueur=1.1)
    for k, ang in enumerate((-32, -11, 11, 32)):
        r = math.radians(ang)
        d = Vector((math.sin(r), -math.cos(r), 0))
        doigt = pied + d * 0.72 + Vector((0, 0, -0.07))
        pieces.append(m.ellipsoid(f"doigt{k}", "gris_bleu_fonce", Ellipsoid(doigt, (0.25, 0.33, 0.3), axis=d)))
        pieces.append(m.spike(f"griffe{k}", "brun_noir", doigt + d * 0.28, d + Vector((0, 0, -0.1)), BAS, 0.45, 0.12,
                              bend=0.5, steps=4))
    pieces.append(m.spike("griffe_arr", "brun_noir", pied + Vector((0.3 * s, 0.6, 0.3)), (0.2 * s, 1, 0), BAS, 0.35,
                          0.1, bend=0.5))
    m.join(f"Patte_{nom}", pieces)


# ---------------------------------------------------------------------------- queue

QUEUE = [Vector(p) for p in ((0, 5.8, 7.7), (0, 8.0, 7.1), (0, 10.2, 6.0), (0.3, 12.2, 4.8),
                             (0.6, 14.0, 3.9), (0.7, 15.6, 3.4))]
RAYONS_QUEUE = [0.85, 1.0, 1.05, 0.95, 0.7]  # rayon du volume de poils de chaque tronçon


def queue(m):
    """Longue queue touffue : tronçons de poils le long du chemin, bout plus clair, une ronce enroulée."""
    pieces = []
    for i, r in enumerate(RAYONS_QUEUE):
        tr = Ellipsoid.between(QUEUE[i], QUEUE[i + 1], r, extra=1.3)
        pieces.append(m.ellipsoid(f"troncon{i}", "gris_bleu_fonce", tr))
        bout = i == len(RAYONS_QUEUE) - 1
        pieces += m.fur(f"pq{i}", tr, 6, (-0.85, 0.9), (0, 360),
                        (lambda t, a, rr: "gris_bleu_clair") if bout else couleur_corps, None, 0.5,
                        souleve=0.15, longueur=2.0, seed=30 + i)
    lien = Ellipsoid.between(QUEUE[1], QUEUE[3], 0.95, extra=1.0)
    pieces += ronce(m, "r_queue", spirale(lien, -0.8, 0.8, 0, 600, n=26, lift=0.12), 40, rayon=0.1)
    m.join("Queue", pieces)


# ---------------------------------------------------------------------------- tête

CRANE = Ellipsoid((0, -7.4, 9.0), (1.6, 1.9, 1.5))
MUSEAU = Ellipsoid((0, -10.2, 8.3), (0.85, 2.2, 0.75))        # long museau de loup
NEZ = Ellipsoid((0, -9.2, 8.75), (0.95, 2.3, 0.65))           # pont du nez
GENCIVE_HAUT = Ellipsoid((0, -9.9, 7.87), (0.8, 2.5, 0.14))
MACHOIRE = Ellipsoid((0, -9.8, 7.1), (0.85, 2.4, 0.55), axis=(0, 1, 0.08))
CHARNIERE = (0, -7.7, 7.55)
OUVERTURE = 12  # babines retroussées, gueule entrouverte
LEVRE_HAUT = 7.8
LEVRE = 7.95
LEVRE_BAS = 7.45
OEIL_Y, OEIL_Z = -8.6, 9.3
PAUPIERE_SORTIE = 0.42


def bord_haut(y, z, k=0.82):
    return max(bord(MUSEAU, y, z, k), bord(CRANE, y, z, k))


def tete(m):
    rng = random.Random("tete")
    peau = lambda t, a, r: "gris_bleu_fonce" if r.random() < 0.35 else "gris_bleu"  # noqa: E731
    pieces = [m.ellipsoid("crane", "gris_bleu_fonce", CRANE, jitter=0.03),
              m.ellipsoid("museau", "gris_bleu", MUSEAU, jitter=0.02),
              m.ellipsoid("nez", "gris_bleu", NEZ, jitter=0.02),
              m.ellipsoid("gencive", "gueule", GENCIVE_HAUT),
              m.ellipsoid("truffe", "brun_noir", Ellipsoid((0, -12.15, 8.55), (0.45, 0.42, 0.32)))]
    pieces += m.fur("pc", CRANE, 9, (-0.85, 0.8), (20, 160), peau, ARRIERE, 0.38, souleve=0.08, longueur=1.6)
    pieces += m.fur("pn", NEZ, 8, (-0.85, 0.6), (35, 145), peau, ARRIERE, 0.32, souleve=0.04, longueur=1.4, seed=1)
    pieces += m.fur("pm", MUSEAU, 6, (-0.75, 0.4), (15, 165), peau, ARRIERE, 0.3, souleve=0.03, longueur=1.3,
                    size=0.85, seed=2)
    for s in (1, -1):
        pieces.append(m.box(f"narine{s}", "gueule", (0.17 * s, -12.53, 8.55), (0.09, 0.06, 0.06), bevel=0.3))
        pieces += oeil(m, s)
        pieces.append(m.tube(f"arcade{s}", "gris_bleu_fonce",
                             [(0.35 * s, -9.3, 9.75), (0.9 * s, -9.0, 9.95), (1.3 * s, -8.5, 9.95),
                              (1.45 * s, -7.9, 9.7)], [0.18, 0.24, 0.22, 0.08], sides=6))
        # grande oreille pointue, enracinée dans le crâne
        racine = Vector((0.8 * s, -7.0, 10.1))
        assert CRANE.inside(racine), "l'oreille doit être enracinée dans le crâne"
        ext = [racine, Vector((1.05 * s, -6.7, 11.4)), Vector((1.25 * s, -6.5, 12.6))]
        pieces.append(m.tube(f"oreille{s}", "gris_bleu_fonce", ext, [0.85, 0.6, 0.0], sides=6, ring_scale=(1.0, 0.32),
                             up=(0, 1, 0)))
        pieces.append(m.tube(f"oreille_int{s}", "gris_bleu_clair", [p + Vector((0, -0.17, 0.05)) for p in ext],
                             [0.58, 0.4, 0.0], sides=6, ring_scale=(1.0, 0.22), up=(0, 1, 0)))
        # joues : muscle + collerette de longues mèches vers l'arrière
        joue = Ellipsoid((1.05 * s, -7.9, 8.2), (0.55, 0.95, 0.7))
        pieces.append(m.ellipsoid(f"masseter{s}", "gris_bleu", joue, jitter=0.03, seed=3))
        pieces += m.fur(f"pj{s}", joue, 4, (-0.6, 0.8), (-80, 80) if s > 0 else (100, 260), peau,
                        Vector((s * 0.4, 1, -0.2)), 0.35, souleve=0.25, longueur=2.4, seed=4)
        # crocs du haut, plantés dans la gencive ; le 10e est le grand croc
        for k in range(12):
            y = -8.3 - 0.3 * k
            xx = min(bord_haut(y, LEVRE_HAUT), bord(GENCIVE_HAUT, y, LEVRE_HAUT + 0.08, 0.9))
            base = (s * xx, y, LEVRE_HAUT + 0.08)
            assert GENCIVE_HAUT.inside(base, 0.05), "chaque croc doit partir de la gencive"
            grand = k % 2 == 0
            long_ = 0.95 if k == 9 else (0.42 if grand else 0.28) + rng.uniform(0, 0.06)
            pieces.append(m.spike(f"croc{k}{s}", "dent", base, (0.1 * s, -0.05, -1), (0, -1, 0), long_,
                                  0.17 if k == 9 else (0.12 if grand else 0.09), bend=0.2, sides=4, steps=2))
        pieces.append(m.tube(f"levre{s}", "brun_noir",
                             [(s * bord_haut(y, LEVRE, 0.97), y, LEVRE) for y in [-8.0 - 0.36 * k for k in range(11)]]
                             + [(0.2 * s, -12.1, LEVRE + 0.03)], 0.05, sides=5))
    pieces.append(m.ellipsoid("gueule", "gueule", Ellipsoid((0, -9.8, 7.6), (0.7, 2.3, 0.3))))
    m.join("Tete", pieces)

    mach = [m.ellipsoid("machoire", "gris_bleu", MACHOIRE, jitter=0.03),
            m.ellipsoid("menton", "gris_bleu_clair", Ellipsoid((0, -11.4, 6.85), (0.6, 0.55, 0.42)), jitter=0.03),
            m.ellipsoid("gencive_bas", "gueule", Ellipsoid((0, -9.9, 7.55), (0.72, 2.2, 0.1))),
            m.ellipsoid("langue", "truffe", Ellipsoid((0, -10.1, 7.6), (0.45, 1.7, 0.1)))]
    for s in (1, -1):
        mach.append(m.ellipsoid(f"angle{s}", "gris_bleu_fonce", Ellipsoid((0.75 * s, -8.0, 7.15), (0.45, 0.85, 0.5)),
                                jitter=0.03, seed=6))
        cote = (-60, 20) if s > 0 else (160, 240)
        mach += m.fur(f"pmj{s}", MACHOIRE, 6, (-0.8, 0.7), cote, lambda t, a, r: ("gris_bleu", "gris_bleu_clair")[
            r.randrange(2)], ARRIERE, 0.4, souleve=0.06, longueur=1.4, seed=7 + s)
        for k in range(8):  # frange de poils sous la mâchoire, de plus en plus longue vers la gorge
            y = -11.0 + 0.4 * k
            t = (y - MACHOIRE.c.y) / MACHOIRE.r.y
            a = 300 if s > 0 else 240
            mach.append(m.meche(f"frange{k}{s}", "gris_bleu_clair" if k % 2 else "gris_bleu", MACHOIRE.point(t, a),
                                MACHOIRE.normal(t, a), Vector((0, 1, -0.8)), 0.8 + 0.1 * k, 0.16, souleve=0.3))
        for k in range(10):  # dents du bas ; la 9e est le grand croc du bas
            y = -8.45 - 0.3 * k
            base = (s * bord(MACHOIRE, y, LEVRE_BAS, 0.86), y, LEVRE_BAS - 0.08)
            assert MACHOIRE.inside(base), "chaque dent du bas doit partir de la mâchoire"
            mach.append(m.spike(f"dent{k}{s}", "dent", base, (0.15 * s, -0.05, 1), (0, -1, 0),
                                0.75 if k == 8 else (0.4 if k % 2 else 0.26), 0.14 if k == 8 else 0.1, bend=0.15,
                                sides=4, steps=2))
        z = LEVRE_BAS + 0.1
        avant = MACHOIRE.c.y - MACHOIRE.r.y * math.sqrt(max(0.0, 1 - ((z - MACHOIRE.c.z) / MACHOIRE.r.z) ** 2))
        mach.append(m.tube(f"levre_bas{s}", "brun_noir",
                           [(s * bord(MACHOIRE, y, z, 0.98), y, z) for y in [-8.0 - 0.3 * k for k in range(13)]
                            if y > avant + 0.15] + [(0.18 * s, avant + 0.05, z)], 0.05, sides=5))
    machoire = m.join("Machoire", mach)
    m.rotate_about([machoire], OUVERTURE, "X", CHARNIERE)

    for nom, s in (("Oeil_G", 1), ("Oeil_D", -1)):  # iris violet : Material = Neon dans Roblox
        c, n, _, _, rh, rv = repere_oeil(s)
        m.ellipsoid(nom, "oeil_violet", Ellipsoid(c + n * 0.03, (rh, 0.16, rv), axis=n), subdiv=2)
        m.ellipsoid(f"Paupiere_{nom[-1]}", "gris_bleu_fonce", Ellipsoid(c - n * PAUPIERE_SORTIE * 0.75,
                                                                       (rh * 1.12, 0.13, rv * 1.2), axis=n), subdiv=2)


def repere_oeil(s):
    x = bord(CRANE, OEIL_Y, OEIL_Z, 1.0)
    c = Vector((x * s, OEIL_Y, OEIL_Z))
    n = Vector((0.75 * s, -0.65, 0.12)).normalized()  # yeux de prédateur, plus tournés vers l'avant
    hx = n.cross(Vector((0, 0, 1))).normalized()
    return c, n, hx, hx.cross(n), 0.38, 0.22


def oeil(m, s):
    c, n, hx, hz, rh, rv = repere_oeil(s)
    avant = 1 if hx.y < 0 else -1
    pieces = [m.ellipsoid(f"orbite{s}", "brun_noir", Ellipsoid(c - n * 0.05, (rh * 1.25, 0.17, rv * 1.4), axis=n))]
    pieces.append(m.beam(f"pupille{s}", "brun_noir", c + n * 0.19 - hz * rv * 0.85, c + n * 0.19 + hz * rv * 0.85,
                         0.06, 0.03))
    pieces.append(m.ico(f"reflet{s}", "blanc_doux", c + n * 0.19 + hz * rv * 0.4 + hx * avant * rh * 0.35, 0.04,
                        subdiv=0))
    haut, bas = [], []
    for i in range(9):
        phi = math.pi * i / 8
        cx = math.cos(phi)
        haut.append(c + n * 0.15 + hx * rh * 1.1 * cx + hz * (rv * 0.6 * math.sin(phi) + 0.04 - 0.18 * avant * cx))
        bas.append(c + n * 0.08 + hx * rh * 1.05 * cx - hz * rv * 1.05 * math.sin(phi))
    pieces.append(m.tube(f"paupiere_h{s}", "gris_bleu_fonce", haut,
                         [0.06, 0.1, 0.13, 0.14, 0.14, 0.14, 0.13, 0.1, 0.06], sides=6, ring_scale=(1.0, 0.75)))
    pieces.append(m.tube(f"paupiere_b{s}", "gris_bleu", bas, [0.03, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.03],
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
        tete_c = (0, -10.0, 8.0)
        vues = ((35, "avant"), (215, "arriere"), (28, "tete", 2.4, (0, -9.0, 9.0)),
                (0, "tete_face", 3.0, tete_c, 0.4), (90, "tete_profil", 2.8, tete_c, 0.6),
                (125, "tete_arriere", 2.6, (0, -8.8, 8.8), 2.2))
        for p in lp.render_previews(model, views=vues):
            print("preview", p)
