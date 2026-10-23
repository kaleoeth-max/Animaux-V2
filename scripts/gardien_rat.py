"""Gardien du Champ : le Rat Ravageur (rat mutant, même direction artistique que le Bélier Colosse).

Rat géant au dos voûté couvert d'écailles anthracite (zigzags vert toxique sur les flancs), crête d'épines
couleur os, épis de blé mutants qui lui poussent sur le dos, long museau pointu à truffe rose et moustaches,
énormes incisives jaunes, gueule à crocs avec mâchoire à plaques, grandes oreilles rondes, yeux rouges,
mains griffues à l'avant, longs pieds à cinq doigts à l'arrière, longue queue nue annelée et épineuse.
Rôle : le gardien rapide et vicieux du champ.

Lancer :  python3 scripts/gardien_rat.py            (export + aperçus)
          python3 scripts/gardien_rat.py --no-render
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import lowpoly as lp  # noqa: E402
from lowpoly import Ellipsoid, Vector, zigzag  # noqa: E402

NAME = "Gardien_Champ_Rat"
ARRIERE = Vector((0, 1, 0))
BAS = Vector((0, 0, -1))

# volumes du corps : dos voûté, grosse croupe, avant plus fin
COU = Ellipsoid((0, -5.3, 5.7), (1.85, 1.9, 1.9))
POITRAIL = Ellipsoid((0, -2.8, 5.9), (2.6, 2.6, 2.6))
DOS = Ellipsoid((0, 0.8, 6.6), (3.1, 3.4, 3.2))
HANCHES = Ellipsoid((0, 4.0, 6.0), (3.0, 2.8, 2.9))
VENTRE = Ellipsoid((0, 0.5, 4.3), (2.3, 4.8, 1.3))
TORSE = (COU, POITRAIL, DOS, HANCHES)

# réglages du squelette et des animations (voir lib/animation.py)
ANIM = dict(
    torse=((0, 4.0, 6.3), (0, -4.5, 5.9)), tete=((0, -5.9, 6.0), (0, -12.3, 5.4)), machoire_bout=(0, -11.3, 3.9),
    pieces_torse=("Corps", "Ble"),
    pas_marche=1.3, leve_marche=0.8, pas_course=1.55, leve_course=1.05,
    couche=-1.7, tete_couche=6, avant_couche=(-0.7, 0.0),
    croc_tete=2, croc_ouverture=20, croc_pique=1.5,  # tête basse : il mord sans piquer du nez dans le sol
)


def couleur_corps(t, a, rng):
    """Poil anthracite, avec une fine traînée vert toxique en zigzag sur les flancs (sa palette à lui)."""
    lat = math.sin(math.radians(a))
    decale = 0.0 if math.cos(math.radians(a)) >= 0 else 0.37
    if abs(lat + 0.2 - 0.35 * zigzag(t * 2.2 + decale)) < 0.1:  # fine traînée toxique en zigzag
        return "vert_toxique"
    return "anthracite_fonce" if rng.random() < 0.3 else "anthracite"


def couleur_patte(t, a, rng):
    if t > -0.3 + 0.45 * zigzag(a / 120):
        return "vert_toxique"
    return "anthracite_fonce" if rng.random() < 0.3 else "anthracite"


def dessus(x, y):
    """Hauteur du dos en (x, y)."""
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


def build():
    lp.reset_scene()
    m = lp.Model(NAME)
    corps(m)
    ble(m)
    for nom, x, y, avant in PATTES:
        patte(m, nom, x, y, avant)
    queue(m)
    tete(m)
    return m


# ---------------------------------------------------------------------------- corps

def corps(m):
    pieces = [m.ellipsoid(f"vol{i}", "anthracite_fonce", e, jitter=0.08, seed=i) for i, e in enumerate(TORSE)]
    pieces.append(m.ellipsoid("ventre", "gris_clair", VENTRE))
    # fourrure : mèches de poil qui partent vers l'arrière (plus longues sur le dos voûté)
    zones = ((COU, 7, (-0.85, 0.6), 0.7, 1.6), (POITRAIL, 8, (-0.9, 0.55), 0.75, 1.6),
             (DOS, 10, (-0.75, 0.8), 0.8, 1.9), (HANCHES, 8, (-0.45, 0.95), 0.8, 1.7))
    for i, (e, rangs, plage, pas, longueur) in enumerate(zones):
        pieces += m.fur(f"po{i}_", e, rangs, plage, (-90, 270), couleur_corps, ARRIERE, pas, souleve=0.12,
                        longueur=longueur, seed=i)
    pieces += m.fur("pv_", VENTRE, 8, (-0.8, 0.8), (225, 315),
                    lambda t, a, r: "gris_clair" if r.random() < 0.75 else "anthracite", ARRIERE, 0.6, souleve=0.08)

    # crête d'épines (vertèbres mutantes), plus hautes sur le dos voûté
    rng = random.Random("crete")
    n = 12
    for i in range(n):
        y = -6.4 + i * (12.2 / (n - 1)) + rng.uniform(-0.25, 0.25)
        L = (0.9 + 2.6 * math.exp(-((y - 0.6) / 3.6) ** 2)) * rng.uniform(0.8, 1.1)
        z = dessus(0, y)
        if z is None:
            continue
        pieces.append(m.spike(f"epine{i}", "os", (0, y, z - 0.2), (0, -0.1, 1), ARRIERE, L,
                              0.42 + 0.1 * L / 3, bend=0.55))
        for s in (1, -1):
            if i % 2:
                continue
            zc = dessus(1.3, y + 0.3)
            if zc is not None:
                pieces.append(m.spike(f"epine{i}_{s}", "os", (1.3 * s, y + 0.3, zc - 0.15),
                                      (0.6 * s, 0, 1), ARRIERE, L * 0.5 * rng.uniform(0.8, 1.2), 0.3, bend=0.5))
    m.join("Corps", pieces)


# épis de blé : (x, y) de chaque touffe sur le dos
TOUFFES_BLE = ((1.9, -1.4), (-1.9, -0.2), (2.1, 2.0), (-2.0, 3.0), (1.6, 4.6), (-1.5, -2.6), (2.3, 0.6))


def ble(m):
    """Épis de blé mutants qui poussent sur le dos, entre les épines (pièce « Ble », liée au torse)."""
    rng = random.Random("ble")
    pieces = []
    for i, (x, y) in enumerate(TOUFFES_BLE):
        s = 1 if x > 0 else -1
        z = dessus(x, y)
        base0 = Vector((x, y, z - 0.25))
        for k in range(3):
            d = Vector((s * rng.uniform(0.3, 0.8), rng.uniform(-0.1, 0.5), 1)).normalized()
            L = rng.uniform(2.2, 3.0)
            base = base0 + Vector((rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), 0))
            tige = [base + d * L * u + ARRIERE * 0.35 * L * u * u for u in (0, 0.35, 0.7, 1.0)]
            pieces.append(m.tube(f"tige{i}{k}", "ble_fonce", tige, [0.08, 0.07, 0.06, 0.05], sides=4))
            # épi : grains de part et d'autre de la tige + barbes au sommet
            haut = (tige[-1] - tige[-2]).normalized()
            cote = haut.cross(Vector((1, 0, 0)) if abs(haut.x) < 0.9 else Vector((0, 1, 0))).normalized()
            for j in range(4):
                u = 0.66 + 0.1 * j
                p = base + d * L * u + ARRIERE * 0.35 * L * u * u
                for sg in (1, -1):
                    pieces.append(m.ellipsoid(f"grain{i}{k}{j}{sg}", "ble", Ellipsoid(p + cote * sg * 0.11,
                                                                                       (0.12, 0.2, 0.12), axis=haut)))
            for j in range(3):
                pieces.append(m.spike(f"barbe{i}{k}{j}", "ble", tige[-1], haut + cote * (j - 1) * 0.3, ARRIERE, 0.6,
                                      0.03, bend=0.2, sides=3, steps=2))
    m.join("Ble", pieces)


# ---------------------------------------------------------------------------- pattes

PATTES = (("AvG", 2.2, -3.0, True), ("AvD", -2.2, -3.0, True),
          ("ArG", 2.7, 4.2, False), ("ArD", -2.7, 4.2, False))


def articulations(x, y, avant):
    """Points d'articulation d'une patte, du haut vers le pied."""
    s = 1 if x > 0 else -1
    if avant:  # épaule, coude (replié en arrière), poignet
        return [Vector((x, y, 5.4)), Vector((x + 0.4 * s, y + 0.7, 3.0)), Vector((x + 0.5 * s, y - 0.2, 1.0))]
    # hanche, genou (vers l'avant), jarret (replié en arrière), cheville
    return [Vector((x, y, 5.6)), Vector((x + 0.4 * s, y - 1.2, 3.6)), Vector((x + 0.6 * s, y + 1.0, 1.7)),
            Vector((x + 0.65 * s, y + 0.2, 0.9))]


def patte(m, nom, x, y, avant):
    """Patte de rat : avant = épaule, bras, coude touffu, avant-bras, main à 4 doigts + pouce ;
    arrière = grosse cuisse, jambe, long pied posé à plat jusqu'au talon, 5 longs doigts."""
    s = 1 if x > 0 else -1
    poil_bas = lambda t, a, r: "vert_toxique" if r.random() < 0.08 else ("anthracite_fonce", "anthracite")[r.randrange(2)]  # noqa: E731,E501
    if avant:
        haut_, milieu, poignet = articulations(x, y, avant)
        epaule = Ellipsoid((x + 0.1 * s, y, 5.3), (1.5, 1.8, 1.9))
        bras = Ellipsoid.between(haut_, milieu, 1.15, 1.2, extra=1.08, up=(0, 1, 0))
        pieces = [m.ellipsoid("epaule", "anthracite_fonce", epaule), m.ellipsoid("bras", "anthracite_fonce", bras)]
        pieces += m.fur("pe", epaule, 7, (-0.85, 0.85), (-90, 270), couleur_corps, BAS, 0.6, souleve=0.12)
        pieces += m.fur("pb", bras, 6, (-0.8, 0.85), (0, 360), couleur_corps, None, 0.55, souleve=0.12, seed=1)
        segments = [(milieu, poignet, [1.0, 0.88, 0.78])]
    else:
        haut_, milieu, jarret, poignet = articulations(x, y, avant)
        cuisse = Ellipsoid((x + 0.2 * s, y - 0.2, 5.0), (1.95, 2.6, 2.5))
        pieces = [m.ellipsoid("cuisse", "anthracite_fonce", cuisse)]
        pieces += m.fur("pc", cuisse, 9, (-0.85, 0.9), (-90, 270), couleur_corps, Vector((0, 0.6, -1)), 0.7,
                        souleve=0.12, longueur=1.7)
        segments = [(milieu, jarret, [0.95, 0.85, 0.7]), (jarret, poignet, [0.72, 0.68, 0.66])]
    pieces.append(m.ico("articulation", "anthracite_fonce", milieu, 0.9, jitter=0.06, seed=4))

    for i, (p1, p2, rayons) in enumerate(segments):
        d = (p2 - p1).normalized()
        seg = Ellipsoid.between(p1, p2, rayons[0], extra=1.15, up=(0, 1, 0))  # a=0 : +X, 90 : arrière, 270 : avant
        bas = Ellipsoid.between(p1.lerp(p2, 0.5), p2 + d * 0.35, rayons[-1] * 1.1, extra=1.15, up=(0, 1, 0))
        pieces.append(m.ellipsoid(f"seg{i}", "anthracite_fonce", seg))
        pieces.append(m.ellipsoid(f"bas{i}", "anthracite_fonce", bas))
        pieces += m.fur(f"ps{i}", seg, 6, (-0.85, 0.7), (0, 360), poil_bas, None, 0.5, souleve=0.1, seed=10 + i)
        pieces += m.fur(f"pp{i}", bas, 4, (-0.2, 0.8), (0, 360), poil_bas, None, 0.45, souleve=0.08, seed=20 + i)
    # touffe de poils et épine couleur os derrière le coude / genou
    for k in range(5):
        a = math.radians(-40 + 20 * k)
        pieces.append(m.meche(f"touffe{k}", "anthracite_fonce" if k % 2 else "anthracite",
                              milieu + Vector((0.4 * math.sin(a), 0.6, 0.3 * math.cos(a))),
                              (0.4 * math.sin(a), 1, 0.2), BAS, 1.1, 0.2, souleve=0.2))
    pieces.append(m.spike("ergot", "os", milieu + Vector((0, 0.75, 0.0)), (0.3 * s, 1, 0.3), BAS, 1.0, 0.24,
                          bend=0.3))

    griffe = lambda nom_, bout, d, longueur: m.spike(nom_, "brun_noir", bout, d + Vector((0, 0, 0.12)), BAS,  # noqa: E731
                                                     longueur, 0.17, bend=0.5, steps=5)
    if avant:
        # main : paume rose, 4 doigts à jointures, petit pouce sur le côté intérieur
        main = Vector((poignet.x, poignet.y - 0.45, 0.42))
        pieces.append(m.ellipsoid("paume", "rose_queue", Ellipsoid(main, (0.85, 0.85, 0.42)), jitter=0.03))
        pieces.append(m.ellipsoid("dos_main", "anthracite_fonce", Ellipsoid(main + Vector((0, 0.15, 0.18)),
                                                                           (0.8, 0.8, 0.36))))
        pieces += m.fur("pm", Ellipsoid(main + Vector((0, 0.15, 0.18)), (0.8, 0.8, 0.36)), 3, (-0.5, 0.6), (40, 140),
                        poil_bas, Vector((0, -1, 0)), 0.35, souleve=0.06, longueur=1.2)
        doigts = [(ang, 1.2 if abs(ang) < 20 else 1.0) for ang in (-33, -11, 11, 33)]
        pouce = (-75 * s, 0.6)
        depart = main + Vector((0, -0.5, 0))
    else:
        # long pied de rat posé à plat : talon au sol, 5 longs doigts
        talon = Vector((poignet.x, poignet.y + 0.2, 0.4))
        pied = Vector((poignet.x, poignet.y - 1.1, 0.4))
        vol = Ellipsoid.between(talon, pied + Vector((0, -0.9, 0)), 0.85, 0.4, extra=1.05)
        pieces.append(m.ellipsoid("pied", "anthracite_fonce", vol))
        pieces.append(m.ellipsoid("plante", "rose_queue", Ellipsoid(pied + Vector((0, 0.2, -0.12)), (0.75, 1.6, 0.25))))
        pieces += m.fur("pf", vol, 4, (-0.8, 0.6), (35, 145), poil_bas, Vector((0, -1, 0)), 0.4, souleve=0.06,
                        longueur=1.2)
        doigts = [(ang, 1.15 if abs(ang) < 25 else 0.95) for ang in (-36, -18, 0, 18, 36)]
        pouce = None
        depart = pied + Vector((0, -0.85, 0))
    for k, (ang, long_) in enumerate(doigts + ([pouce] if pouce else [])):
        r = math.radians(ang)
        d = Vector((math.sin(r), -math.cos(r), 0))
        base = depart + d * 0.15
        jointure = depart + d * (0.55 * long_) + Vector((0, 0, 0.12))
        bout = depart + d * long_ + Vector((0, 0, -0.12))
        epais = 0.24 if k < len(doigts) else 0.2
        pieces.append(m.tube(f"doigt{k}", "rose_queue", [base, jointure, bout], [epais, epais * 0.85, epais * 0.7],
                             sides=6))
        pieces.append(m.ico(f"jointure{k}", "rose_queue", jointure, (epais * 0.85,) * 3, subdiv=1))
        pieces.append(griffe(f"griffe{k}", bout, d, 0.7 * long_))
    m.join(f"Patte_{nom}", pieces)


# ---------------------------------------------------------------------------- queue

QUEUE = [Vector(p) for p in ((0, 6.6, 6.2), (0, 9.6, 4.8), (0.6, 12.8, 3.2), (1.4, 15.8, 2.0),
                             (1.6, 18.6, 1.4), (1.2, 21.2, 1.1))]
RAYONS_QUEUE = [1.05, 0.8, 0.6, 0.42, 0.26, 0.0]


def echantillon_queue(u):
    f = u * (len(QUEUE) - 1)
    i = min(int(f), len(QUEUE) - 2)
    w = f - i
    p = QUEUE[i].lerp(QUEUE[i + 1], w)
    r = RAYONS_QUEUE[i] + (RAYONS_QUEUE[i + 1] - RAYONS_QUEUE[i]) * w
    tg = (QUEUE[i + 1] - QUEUE[i]).normalized()
    cote = tg.cross(Vector((0, 0, 1))).normalized()
    return p, r, tg, cote, cote.cross(tg)


def queue(m):
    """Longue queue nue de rat, annelée (anneaux en relief), avec des épines noires sur le dessus."""
    pts, rayons = [], []
    n = 60
    for i in range(n + 1):
        p, r, *_ = echantillon_queue(i / n)
        pts.append(p)
        rayons.append(r * (1.1 if i % 2 == 0 else 1.0))  # anneaux
    rayons[-1] = 0.0
    pieces = [m.tube("queue", "rose_queue", pts, rayons, sides=7)]
    for i in range(9):
        u = 0.06 + 0.8 * i / 8
        p, r, tg, cote, haut = echantillon_queue(u)
        pieces.append(m.spike(f"dq{i}", "os", p + haut * r * 0.8, haut, tg, 1.1 * (1 - 0.6 * u),
                              0.24 * (1 - 0.5 * u), bend=0.45))
    m.join("Queue", pieces)


# ---------------------------------------------------------------------------- tête

CRANE = Ellipsoid((0, -7.3, 6.3), (1.85, 2.2, 1.7))
MUSEAU = Ellipsoid((0, -10.1, 5.45), (1.1, 2.2, 0.85))       # long museau pointu
NEZ = Ellipsoid((0, -9.3, 5.95), (1.15, 2.3, 0.8))            # pont du nez
GENCIVE_HAUT = Ellipsoid((0, -9.6, 4.97), (0.95, 2.4, 0.15))
MACHOIRE = Ellipsoid((0, -9.4, 4.2), (1.05, 2.25, 0.68), axis=(0, 1, 0.08))
CHARNIERE = (0, -7.5, 4.65)
OUVERTURE = 10
LEVRE_HAUT = 4.9
LEVRE = 5.05
LEVRE_BAS = 4.6
OEIL_Y, OEIL_Z = -8.9, 6.95
PAUPIERE_SORTIE = 0.45


def bord_haut(y, z, k=0.82):
    return max(bord(MUSEAU, y, z, k), bord(CRANE, y, z, k))


def tete(m):
    rng = random.Random("tete")
    peau = lambda t, a, r: "anthracite_fonce" if r.random() < 0.3 else "anthracite"  # noqa: E731
    pieces = [m.ellipsoid("crane", "anthracite_fonce", CRANE, jitter=0.04),
              m.ellipsoid("museau", "anthracite", MUSEAU, jitter=0.03),
              m.ellipsoid("nez", "anthracite", NEZ, jitter=0.03),
              m.ellipsoid("gencive", "gueule", GENCIVE_HAUT),
              m.ico("truffe", "rose_queue", (0, -12.2, 5.62), (0.42, 0.34, 0.34), subdiv=1)]
    # poil court sur la tête, plus ras vers le bout du museau
    pieces += m.fur("pc", CRANE, 9, (-0.85, 0.8), (25, 155), peau, ARRIERE, 0.42, souleve=0.08, longueur=1.6)
    pieces += m.fur("pn", NEZ, 8, (-0.85, 0.6), (35, 145), peau, ARRIERE, 0.36, souleve=0.05, longueur=1.4, seed=1)
    pieces += m.fur("pm", MUSEAU, 6, (-0.75, 0.4), (15, 165), peau, ARRIERE, 0.34, souleve=0.03, longueur=1.3,
                    size=0.85, seed=2)
    for s in (1, -1):
        # narine sur la truffe
        narine = (0.2 * s, -12.5, 5.66)
        pieces.append(m.box(f"narine{s}", "brun_noir", narine, (0.1, 0.08, 0.07), rot=(0, 0, 25 * s), bevel=0.3))
        pieces += oeil(m, s)
        pieces.append(m.tube(f"arcade{s}", "anthracite_fonce",
                             [(0.4 * s, -9.45, 7.05), (1.05 * s, -9.2, 7.32), (1.6 * s, -8.7, 7.42),
                              (1.8 * s, -8.1, 7.22)], [0.22, 0.3, 0.28, 0.1], sides=6))
        for k in range(3):
            pieces.append(m.spike(f"arcade_ep{k}{s}", "os", (s * (0.95 + 0.33 * k), -9.15 + 0.3 * k, 7.5),
                                  (0.35 * s, 0.4, 1), ARRIERE, 0.45 + 0.1 * k, 0.15, bend=0.6, sides=4))
        # grande oreille ronde de rat, enracinée dans le crâne
        axe = Vector((0.6 * s, -0.8, 0.1)).normalized()
        centre = Vector((1.55 * s, -6.3, 7.75))
        pieces.append(m.ellipsoid(f"oreille{s}", "anthracite_fonce", Ellipsoid(centre, (1.0, 0.16, 1.15), axis=axe),
                                  subdiv=2))
        pieces.append(m.ellipsoid(f"oreille_int{s}", "rose_queue",
                                  Ellipsoid(centre + axe * 0.08, (0.72, 0.1, 0.88), axis=axe), subdiv=2))
        assert CRANE.inside(centre - Vector((0, 0, 1.0))), "l'oreille doit être enracinée dans le crâne"
        # moustaches
        for k in range(3):
            y, z = -11.1 - 0.25 * k, 5.35 + 0.15 * k
            racine = Vector((s * bord(MUSEAU, y, z, 0.9), y, z))
            assert MUSEAU.inside(racine), "chaque moustache doit partir du museau"
            dz = 0.25 * (k - 1)
            pieces.append(m.tube(f"moustache{k}{s}", "brun_noir",
                                 [racine, racine + Vector((1.2 * s, 0.45, dz)), racine + Vector((2.5 * s, 1.3, dz * 1.8))],
                                 [0.045, 0.035, 0.0], sides=4))
        # muscle de la mâchoire + collerette d'épines sur les joues
        joue = Ellipsoid((1.3 * s, -7.9, 5.4), (0.6, 1.0, 0.8))
        pieces.append(m.ellipsoid(f"masseter{s}", "anthracite", joue, jitter=0.04, seed=3))
        for k in range(4):
            pieces.append(m.spike(f"joue{k}{s}", "anthracite" if k % 2 else "anthracite_fonce",
                                  (s * 1.6, -7.4 + 0.15 * k, 5.8 - 0.35 * k), (s, 0.7, 0.1 - 0.15 * k),
                                  ARRIERE, 1.2 - 0.12 * k, 0.28, bend=0.35))
        # crocs du haut, plantés dans la gencive
        for k in range(11):
            y = -8.0 - 0.3 * k
            x = min(bord_haut(y, LEVRE_HAUT), bord(GENCIVE_HAUT, y, LEVRE_HAUT + 0.08, 0.9))
            base = (s * x, y, LEVRE_HAUT + 0.08)
            assert GENCIVE_HAUT.inside(base, 0.05), "chaque croc doit partir de la gencive"
            grand = k % 2 == 0
            pieces.append(m.spike(f"croc{k}{s}", "dent", base, (0.12 * s, -0.05, -1), (0, -1, 0),
                                  (0.45 if grand else 0.3) + rng.uniform(0, 0.08), 0.13 if grand else 0.1,
                                  bend=0.15, sides=4, steps=1))
        # lèvre du haut
        pieces.append(m.tube(f"levre{s}", "brun_noir",
                             [(s * bord_haut(y, LEVRE, 0.97), y, LEVRE) for y in [-7.7 - 0.35 * k for k in range(11)]]
                             + [(0.25 * s, -11.8, LEVRE + 0.03)], 0.06, sides=5))
        # grande incisive jaune de rat (signature), plantée dans le bout du museau
        base = Vector((0.2 * s, -11.75, 5.05))
        assert MUSEAU.inside(base), "l'incisive doit partir du museau"
        pieces.append(m.spike(f"incisive{s}", "ble", base, (0, -0.25, -1), ARRIERE, 1.35, 0.17, bend=0.25, sides=4))
    # couronne d'épines derrière le crâne
    for k, dx in enumerate((-0.7, 0.0, 0.7)):
        pieces.append(m.spike(f"couronne{k}", "os", (dx, -6.5, 7.6), (dx * 0.4, 1, 0.7), BAS,
                              1.3 - 0.3 * abs(dx), 0.28, bend=0.25))
    pieces.append(m.ellipsoid("gueule", "gueule", Ellipsoid((0, -9.4, 4.68), (0.85, 2.2, 0.35))))
    m.join("Tete", pieces)

    mach = [m.ellipsoid("machoire", "vert_toxique_fonce", MACHOIRE, jitter=0.04),
            m.ellipsoid("menton", "vert_toxique_fonce", Ellipsoid((0, -11.0, 3.95), (0.75, 0.55, 0.5)), jitter=0.05),
            m.ellipsoid("gencive_bas", "gueule", Ellipsoid((0, -9.5, 4.82), (0.88, 2.1, 0.11))),
            m.ellipsoid("langue", "rose_queue", Ellipsoid((0, -9.8, 4.88), (0.55, 1.5, 0.12)))]
    plaque = lambda t, a, r: ("anthracite", "anthracite_fonce", "vert_toxique")[r.randrange(3)]  # noqa: E731
    for s in (1, -1):
        mach.append(m.ellipsoid(f"angle{s}", "anthracite_fonce", Ellipsoid((0.85 * s, -7.9, 4.25), (0.5, 0.9, 0.6)),
                                jitter=0.04, seed=6))
        cote = (-40, 25) if s > 0 else (155, 220)
        mach += m.fur(f"pj{s}", MACHOIRE, 6, (-0.8, 0.7), cote, plaque, ARRIERE, 0.45, souleve=0.06, longueur=1.4,
                      seed=7 + s)
        for k in range(8):  # frange d'écailles pointues sous la mâchoire
            y = -10.7 + 0.38 * k
            t = (y - MACHOIRE.c.y) / MACHOIRE.r.y
            a = 300 if s > 0 else 240
            mach.append(m.spike(f"frange{k}{s}", ("anthracite_fonce", "vert_toxique", "anthracite")[k % 3],
                                MACHOIRE.point(t, a), MACHOIRE.normal(t, a) + Vector((0, 0.9, -0.3)), ARRIERE,
                                0.45 + 0.06 * k, 0.17, bend=0.3, sides=4))
        for k in range(9):  # dents du bas, emboîtées entre celles du haut
            y = -8.15 - 0.3 * k
            base = (s * bord(MACHOIRE, y, LEVRE_BAS, 0.86), y, LEVRE_BAS - 0.08)
            assert MACHOIRE.inside(base), "chaque dent du bas doit partir de la mâchoire"
            mach.append(m.spike(f"dent{k}{s}", "dent", base, (0.25 * s, -0.05, 1), (0, -1, 0),
                                0.5 if k % 2 else 0.34, 0.13 if k % 2 else 0.1, bend=0.12, sides=4, steps=1))
        z = LEVRE_BAS + 0.1
        avant = MACHOIRE.c.y - MACHOIRE.r.y * math.sqrt(max(0.0, 1 - ((z - MACHOIRE.c.z) / MACHOIRE.r.z) ** 2))
        mach.append(m.tube(f"levre_bas{s}", "brun_noir",
                           [(s * bord(MACHOIRE, y, z, 0.98), y, z) for y in [-7.8 - 0.3 * k for k in range(11)]
                            if y > avant + 0.15] + [(0.22 * s, avant + 0.05, z)], 0.06, sides=5))
        # incisive du bas
        base = Vector((0.16 * s, -11.0, 4.5))
        assert MACHOIRE.inside(base), "l'incisive du bas doit partir de la mâchoire"
        mach.append(m.spike(f"incisive_bas{s}", "ble", base, (0, -0.35, 1), ARRIERE, 0.9, 0.14, bend=0.2, sides=4))
    machoire = m.join("Machoire", mach)
    m.rotate_about([machoire], OUVERTURE, "X", CHARNIERE)

    for nom, s in (("Oeil_G", 1), ("Oeil_D", -1)):  # iris rouge : Material = Neon dans Roblox
        c, n, _, _, rh, rv = repere_oeil(s)
        m.ellipsoid(nom, "oeil_rouge", Ellipsoid(c + n * 0.03, (rh, 0.17, rv), axis=n), subdiv=2)
        m.ellipsoid(f"Paupiere_{nom[-1]}", "anthracite_fonce", Ellipsoid(c - n * PAUPIERE_SORTIE * 0.75,
                                                                       (rh * 1.12, 0.14, rv * 1.2), axis=n), subdiv=2)


def repere_oeil(s):
    x = bord(CRANE, OEIL_Y, OEIL_Z, 1.0)
    c = Vector((x * s, OEIL_Y, OEIL_Z))
    n = Vector((0.88 * s, -0.42, 0.15)).normalized()
    hx = n.cross(Vector((0, 0, 1))).normalized()
    return c, n, hx, hx.cross(n), 0.4, 0.3


def oeil(m, s):
    c, n, hx, hz, rh, rv = repere_oeil(s)
    avant = 1 if hx.y < 0 else -1
    pieces = [m.ellipsoid(f"orbite{s}", "brun_noir", Ellipsoid(c - n * 0.05, (rh * 1.25, 0.18, rv * 1.35), axis=n))]
    pieces.append(m.beam(f"pupille{s}", "brun_noir", c + n * 0.2 - hz * rv * 0.85, c + n * 0.2 + hz * rv * 0.85,
                         0.07, 0.03))
    pieces.append(m.ico(f"reflet{s}", "blanc_doux", c + n * 0.2 + hz * rv * 0.4 + hx * avant * rh * 0.35, 0.045,
                        subdiv=0))
    haut, bas = [], []
    for i in range(9):
        phi = math.pi * i / 8
        cx = math.cos(phi)
        haut.append(c + n * 0.16 + hx * rh * 1.08 * cx + hz * (rv * 0.62 * math.sin(phi) + 0.05 - 0.18 * avant * cx))
        bas.append(c + n * 0.08 + hx * rh * 1.05 * cx - hz * rv * 1.05 * math.sin(phi))
    pieces.append(m.tube(f"paupiere_h{s}", "anthracite_fonce", haut,
                         [0.07, 0.12, 0.15, 0.16, 0.16, 0.16, 0.15, 0.12, 0.07], sides=6, ring_scale=(1.0, 0.75)))
    pieces.append(m.tube(f"paupiere_b{s}", "anthracite", bas, [0.04, 0.05, 0.06, 0.06, 0.06, 0.06, 0.06, 0.05, 0.04],
                         sides=5))
    return pieces


if __name__ == "__main__":
    model = build()
    st = model.stats()
    print("stats", st["pieces"], "pièces,", st["triangles"], "triangles")
    for nom, t in sorted(st["par_piece"].items()):
        print("   ", nom, t)
    print("point le plus bas :", round(min(v.co.z for o in model.parts for v in o.data.vertices), 2))
    model.export()
    if "--no-render" not in sys.argv:
        tete_c = (0, -9.6, 5.6)
        vues = ((35, "avant"), (215, "arriere"), (28, "tete", 2.4, (0, -8.8, 6.2)),
                (0, "tete_face", 3.0, tete_c, 0.4), (90, "tete_profil", 2.8, tete_c, 0.6),
                (125, "tete_arriere", 2.6, (0, -8.6, 6.0), 2.2))
        for p in lp.render_previews(model, views=vues):
            print("preview", p)
