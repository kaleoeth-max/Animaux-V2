"""Gardien de la Prairie n°1 : le Bélier Colosse (version monstre / boss, détaillée).

Bête blindée à quatre pattes couverte d'écailles qui se chevauchent : sable sur le dessus,
zigzags orange rouille sur les flancs et le ventre. Rangées d'épines noires courbes sur le
dos, énormes cornes annelées en spirale, gueule pleine de crocs, collerette d'épines sur les
joues, doigts griffus et longue queue à nageoires d'épines.
Rôle : le gardien « tank », lent, massif et terrifiant.

Lancer :  python3 scripts/gardien_belier.py
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import lowpoly as lp  # noqa: E402
from lowpoly import Ellipsoid, Vector, zigzag  # noqa: E402

NAME = "Gardien_Prairie_Belier"
ARRIERE = Vector((0, 1, 0))  # les écailles et épines du corps pointent vers l'arrière
BAS = Vector((0, 0, -1))

# volumes du corps (alignés sur Y : face vers -Y)
COU = Ellipsoid((0, -6.3, 7.0), (1.95, 2.2, 1.95))
POITRAIL = Ellipsoid((0, -3.4, 6.5), (3.2, 3.0, 2.9))
DOS = Ellipsoid((0, 0.6, 6.7), (3.0, 3.6, 2.8))
HANCHES = Ellipsoid((0, 4.6, 6.2), (2.7, 2.9, 2.5))
VENTRE = Ellipsoid((0, 0.6, 4.6), (2.4, 5.8, 1.4))
TORSE = (COU, POITRAIL, DOS, HANCHES)


def couleur_corps(t, a, rng):
    """Dessus sable (avec des écailles plus foncées), flancs et ventre en zigzags rouille."""
    lat = math.sin(math.radians(a))
    decale = 0.0 if math.cos(math.radians(a)) >= 0 else 0.37
    if lat < -0.1 + 0.45 * zigzag(t * 2.2 + decale):
        return "rouille"
    return "sable_fonce" if rng.random() < 0.28 else "sable"


def dessus(x, y):
    """Hauteur du dos en (x, y) : le point le plus haut des volumes du torse."""
    z = None
    for e in TORSE:
        k = 1 - (x / e.r.x) ** 2 - ((y - e.c.y) / e.r.y) ** 2
        if k > 0:
            zz = e.c.z + e.r.z * math.sqrt(k)
            z = zz if z is None else max(z, zz)
    return z


def build():
    lp.reset_scene()
    m = lp.Model(NAME)
    corps(m)
    for nom, x, y, avant in (("AvG", 2.9, -3.4, True), ("AvD", -2.9, -3.4, True),
                             ("ArG", 2.7, 4.4, False), ("ArD", -2.7, 4.4, False)):
        patte(m, nom, x, y, avant)
    queue(m)
    tete(m)
    return m


# ---------------------------------------------------------------------------- corps

def corps(m):
    pieces = [m.ellipsoid(f"vol{i}", "sable_fonce", e, jitter=0.08, seed=i) for i, e in enumerate(TORSE)]
    pieces.append(m.ellipsoid("ventre", "rouille", VENTRE))

    # écailles qui se chevauchent sur tout le torse
    zones = ((COU, 5, (-0.85, 0.6), 0.95), (POITRAIL, 6, (-0.9, 0.55), 1.1),
             (DOS, 7, (-0.75, 0.8), 1.15), (HANCHES, 6, (-0.45, 0.95), 1.1))
    for i, (e, rangs, plage, pas) in enumerate(zones):
        pieces += m.scales(f"ec{i}_", e, rangs, plage, (-90, 270), couleur_corps, ARRIERE, pas, h=0.17,
                           tilt=9, seed=i)
    pieces += m.scales("ev_", VENTRE, 7, (-0.8, 0.8), (225, 315), lambda t, a, r: "rouille", ARRIERE, 0.75,
                       h=0.2, tilt=10)

    # rangée centrale de grandes épines courbes + deux rangées sur les côtés + une rangée sur les flancs
    rng = random.Random("crete")
    n = 11
    for i in range(n):
        y = -7.2 + i * (14.0 / (n - 1)) + rng.uniform(-0.3, 0.3)
        L = (1.2 + 2.6 * math.sin(math.pi * (i + 0.5) / n)) * rng.uniform(0.75, 1.1)
        z = dessus(0, y)
        if z is None:
            continue
        pieces.append(m.spike(f"epine{i}", "brun_noir", (0, y, z - 0.2), (0, -0.15, 1), ARRIERE, L,
                              0.5 + 0.12 * L / 3, bend=0.55))
        for s in (1, -1):
            for (dx, k, penche) in ((1.35, 0.55, 0.55), (2.35, 0.32, 1.4)):
                if i % 2 and dx > 2:  # rangée des flancs : une épine sur deux
                    continue
                zc = dessus(dx, y + 0.3)
                if zc is None:
                    continue
                pieces.append(m.spike(f"epine{i}_{dx}{s}", "brun_noir", (dx * s, y + 0.3, zc - 0.15),
                                      (penche * s, 0, 1), ARRIERE, L * k * rng.uniform(0.8, 1.2), 0.34,
                                      bend=0.5))
    m.join("Corps", pieces)


# ---------------------------------------------------------------------------- pattes

def couleur_patte(t, a, rng):
    """Bas des pattes : zigzags rouille sur fond sable."""
    if t > -0.3 + 0.45 * zigzag(a / 120):
        return "rouille"
    return "sable_fonce" if rng.random() < 0.3 else "sable"


def patte(m, nom, x, y, avant):
    """Patte de bête : avant = épaule / coude replié en arrière / poignet,
    arrière = grosse cuisse / genou vers l'avant / jarret replié en arrière."""
    s = 1 if x > 0 else -1
    if avant:
        haut_ = Vector((x, y, 6.3))
        milieu = Vector((x + 0.6 * s, y + 0.9, 3.6))     # coude
        poignet = Vector((x + 0.75 * s, y - 0.2, 1.25))
        epaule = Ellipsoid((x + 0.1 * s, y, 6.0), (1.6, 1.9, 2.1))
        biceps = Ellipsoid.between(haut_, milieu, 1.3, 1.4, extra=1.05, up=(0, 1, 0))
        pieces = [m.ellipsoid("epaule", "sable_fonce", epaule), m.ellipsoid("biceps", "sable_fonce", biceps)]
        pieces += m.scales("ee", epaule, 5, (-0.85, 0.85), (-90, 270), couleur_corps, BAS, 0.8, h=0.16, tilt=8)
        pieces += m.scales("eb", biceps, 4, (-0.8, 0.8), (0, 360), couleur_corps, None, 0.75, h=0.15, tilt=8,
                           seed=1)
        segments = [(milieu, poignet, [1.05, 0.95, 0.72], "rouille")]
    else:
        haut_ = Vector((x, y, 6.1))
        milieu = Vector((x + 0.5 * s, y - 1.1, 3.9))     # genou
        jarret = Vector((x + 0.7 * s, y + 0.9, 1.9))
        poignet = Vector((x + 0.75 * s, y, 1.0))
        cuisse = Ellipsoid((x + 0.2 * s, y - 0.2, 5.2), (1.75, 2.3, 2.3))
        pieces = [m.ellipsoid("cuisse", "sable_fonce", cuisse)]
        pieces += m.scales("ec", cuisse, 6, (-0.85, 0.85), (-90, 270), couleur_corps, Vector((0, 0.5, -1)), 0.85,
                           h=0.16, tilt=8)
        segments = [(milieu, jarret, [1.0, 0.9, 0.75], "sable_fonce"),
                    (jarret, poignet, [0.75, 0.7, 0.68], "rouille")]
        # épine du jarret
        pieces.append(m.spike("ergot_jarret", "brun_noir", jarret + Vector((0, 0.5, 0.1)), (0.2 * s, 1, 0.2),
                              Vector((0, 0.3, 1)), 1.2, 0.3, bend=0.3))
    # articulation bosselée (coude / genou)
    pieces.append(m.ico("articulation", "sable_fonce", milieu, 1.05, jitter=0.08, seed=4))

    for i, (p1, p2, rayons, couleur) in enumerate(segments):
        # avant-bras / jambe : volume effilé couvert d'écailles (zigzags rouille vers le bas)
        seg = Ellipsoid.between(p1, p2, rayons[0], extra=1.12, up=(0, 1, 0))  # a=0 : +X, 90 : arrière, 270 : avant
        pieces.append(m.ellipsoid(f"seg{i}", "sable_fonce", seg))
        pieces.append(m.ico(f"poignet{i}", "sable_fonce", p2, rayons[-1] * 1.05, jitter=0.05, seed=7 + i))
        d = (p2 - p1).normalized()
        pieces += m.scales(f"es{i}", seg, 5, (-0.85, 0.85), (0, 360), couleur_patte, None, 0.6, h=0.14, tilt=8,
                           seed=10 + i)
        # épines à l'arrière du segment
        for k, t in enumerate((-0.35, 0.3)):
            pieces.append(m.spike(f"epine{i}{k}", "brun_noir", seg.point(t, 90), seg.normal(t, 90) + Vector((0, 0, 0.3)),
                                  d, 1.0 - 0.25 * k, 0.26, bend=0.35))
    # ergots derrière le coude / genou
    for k in range(2):
        pieces.append(m.spike(f"ergot{k}", "brun_noir", milieu + Vector((0, 0.8, 0.4 - 0.8 * k)),
                              (0.3 * s, 1, 0.3), BAS, 1.3 - 0.4 * k, 0.3, bend=0.3))
    cheville = poignet

    # pied + quatre doigts griffus + une griffe arrière
    pied = Vector((cheville.x, cheville.y - 0.4, 0.55))
    pied_vol = Ellipsoid(pied, (1.2, 1.5, 0.6))
    pieces.append(m.ellipsoid("pied", "sable_fonce", pied_vol))
    pieces += m.scales("ep", pied_vol, 3, (-0.7, 0.7), (25, 155), couleur_patte, Vector((0, -1, 0)), 0.6, h=0.12,
                       tilt=6)
    for k, ang in enumerate((-42, -14, 14, 42)):
        r = math.radians(ang)
        d = Vector((math.sin(r), -math.cos(r), 0))
        bout = pied + d * 1.75 + Vector((0, 0, -0.15))
        pieces.append(m.tube(f"doigt{k}", "sable", [pied + d * 0.6, pied + d * 1.2 + Vector((0, 0, 0.05)), bout],
                             [0.42, 0.36, 0.3], sides=5))
        pieces.append(m.kite(f"ecdoigt{k}", "rouille" if k % 2 else "sable_fonce",
                             pied + d * 1.15 + Vector((0, 0, 0.3)), (0, 0, 1), d, 0.5, 0.75, 0.15, tilt=6))
        pieces.append(m.spike(f"griffe{k}", "brun_noir", bout, d, BAS, 0.95, 0.26, bend=0.7))
    pieces.append(m.spike("griffe_arr", "brun_noir", pied + Vector((0, 1.2, 0.2)), (0, 1, 0.2), BAS, 0.7, 0.22,
                          bend=0.6))
    m.join(f"Patte_{nom}", pieces)


# ---------------------------------------------------------------------------- queue

def queue(m):
    chemin = [Vector(p) for p in ((0, 6.6, 6.0), (0, 9.4, 5.2), (0.4, 12.2, 4.3), (0.9, 14.8, 3.6),
                                  (0.7, 17.3, 3.1), (0.2, 19.6, 2.8))]
    rayons = [1.75, 1.4, 1.05, 0.75, 0.42, 0.0]
    pieces = [m.tube("queue", "sable_fonce", chemin, rayons, sides=7, ring_scale=(1.0, 0.85))]
    rng = random.Random("queue")

    def echantillon(u):
        f = u * (len(chemin) - 1)
        i = min(int(f), len(chemin) - 2)
        w = f - i
        p = chemin[i].lerp(chemin[i + 1], w)
        r = rayons[i] + (rayons[i + 1] - rayons[i]) * w
        tg = (chemin[i + 1] - chemin[i]).normalized()
        cote = tg.cross(Vector((0, 0, 1))).normalized()
        return p, r, tg, cote, cote.cross(tg)

    # écailles en anneaux
    rangs = 16
    for i in range(rangs):
        u = 0.03 + 0.85 * i / (rangs - 1)
        p, r, tg, cote, haut = echantillon(u)
        nb = max(4, round(2 * math.pi * r / 0.7))
        for k in range(nb):
            a = 2 * math.pi * (k + 0.5 * (i % 2)) / nb
            nrm = cote * math.cos(a) + haut * math.sin(a)
            if math.sin(a) < -0.1 + 0.45 * zigzag(u * 6):
                couleur = "rouille"
            else:
                couleur = "sable_fonce" if rng.random() < 0.3 else "sable"
            pos = p + (cote * math.cos(a) + haut * 0.85 * math.sin(a)) * r
            pieces.append(m.kite(f"eq{i}_{k}", couleur, pos, nrm, tg,
                                 max(2 * math.pi * r / nb * 1.35, 0.25), 1.05 - 0.4 * u, 0.15, tilt=9))

    # nageoires d'épines sur les côtés + épines noires sur le dessus
    for i in range(11):
        u = 0.08 + 0.84 * i / 10
        p, r, tg, cote, haut = echantillon(u)
        L = 2.0 * (1 - 0.55 * u)
        for s in (1, -1):
            pieces.append(m.spike(f"nag{i}{s}", "rouille" if i % 2 else "sable", p + cote * s * r * 0.9,
                                  cote * s + tg * 0.25, tg, L, 0.28 * (1 - 0.4 * u), bend=0.5))
        pieces.append(m.spike(f"dq{i}", "brun_noir", p + haut * r * 0.8, haut, tg, L * 0.75,
                              0.3 * (1 - 0.4 * u), bend=0.45))
    # bouquet d'épines au bout
    p, r, tg, cote, haut = echantillon(0.97)
    for k, ang in enumerate((-50, -25, 0, 25, 50)):
        d = tg * math.cos(math.radians(ang)) + cote * math.sin(math.radians(ang))
        pieces.append(m.spike(f"bout{k}", "brun_noir", p, d + haut * 0.15, haut, 1.6 - 0.25 * abs(ang) / 25,
                              0.26, bend=0.2))
    m.join("Queue", pieces)


# ---------------------------------------------------------------------------- tête

CRANE = Ellipsoid((0, -8.7, 7.0), (1.9, 2.4, 1.7))
MUSEAU = Ellipsoid((0, -10.9, 6.35), (1.35, 1.65, 0.95))
MACHOIRE = Ellipsoid((0, -10.2, 5.05), (1.25, 2.1, 0.55), axis=(0, 1, 0.08))
CHARNIERE = (0, -8.3, 5.5)
LEVRE_HAUT = 5.75  # hauteur où les crocs du haut sortent du museau
LEVRE_BAS = 5.45   # hauteur où les dents du bas sortent de la mâchoire


def bord(e, y, z, k=0.82):
    """Demi-largeur de l'ellipsoïde e à (y, z), réduite de k pour planter une dent juste à l'intérieur."""
    q = (y - e.c.y) / e.r.y
    h = (z - e.c.z) / e.r.z
    return e.r.x * math.sqrt(max(0.08, 1 - q * q - h * h)) * k


NEZ = Ellipsoid((0, -10.1, 6.85), (1.1, 2.1, 0.75))           # pont du nez entre crâne et museau
GENCIVE_HAUT = Ellipsoid((0, -10.4, 5.82), (1.12, 1.95, 0.17))
JOUE = 1.45  # écart des muscles de la mâchoire


def tete(m):
    rng = random.Random("tete")
    peau = lambda t, a, r: "sable_fonce" if r.random() < 0.3 else "sable"  # noqa: E731
    pieces = [m.ellipsoid("crane", "sable_fonce", CRANE, jitter=0.04),
              m.ellipsoid("museau", "sable", MUSEAU, jitter=0.03),
              m.ellipsoid("nez", "sable", NEZ, jitter=0.03),
              m.ellipsoid("gencive", "gueule", GENCIVE_HAUT)]
    # écailles fines qui coulent vers l'arrière
    pieces += m.scales("ec", CRANE, 7, (-0.85, 0.75), (28, 152), peau, ARRIERE, 0.5, h=0.08, tilt=3,
                       size=0.8)
    pieces += m.scales("en", NEZ, 6, (-0.85, 0.6), (40, 140), peau, ARRIERE, 0.42, h=0.07, tilt=3, size=0.8,
                       seed=1)
    pieces += m.scales("em", MUSEAU, 5, (-0.75, 0.4), (20, 160), peau, ARRIERE, 0.42, h=0.06, tilt=2, size=0.8,
                       seed=2)
    # crête de petites bosses sombres sur l'arête du nez
    for k in range(5):
        y = -11.8 + 0.6 * k
        z = NEZ.c.z + NEZ.r.z * math.sqrt(max(0.0, 1 - ((y - NEZ.c.y) / NEZ.r.y) ** 2))
        if MUSEAU.inside((0, y, z)):
            q = (y - MUSEAU.c.y) / MUSEAU.r.y
            z = max(z, MUSEAU.c.z + MUSEAU.r.z * math.sqrt(max(0.0, 1 - q * q)))
        pieces.append(m.kite(f"arete{k}", "sable_fonce", (0, y, z - 0.02), (0, -0.3, 1), ARRIERE,
                             0.4 + 0.05 * k, 0.6, 0.2, tilt=14))
    pieces.append(narine(m, 1))
    pieces.append(narine(m, -1))
    for s in (1, -1):
        # naseau en relief autour de la narine
        pieces.append(m.ico(f"naseau{s}", "sable", (0.45 * s, -12.15, 6.8), (0.32, 0.3, 0.24), subdiv=1))
        # orbite creusée + arcade sourcilière lourde et froncée (plus basse côté nez = air méchant)
        pieces.append(m.box(f"orbite{s}", "brun_noir", (1.62 * s, -9.55, 7.3), (0.3, 0.6, 0.32),
                            rot=(0, 0, -12 * s), bevel=0.3))
        pieces.append(m.tube(f"arcade{s}", "sable_fonce",
                             [(0.45 * s, -10.25, 7.5), (1.2 * s, -9.95, 7.78), (1.85 * s, -9.4, 7.88),
                              (2.05 * s, -8.75, 7.65)], [0.26, 0.34, 0.32, 0.12], sides=6))
        for k in range(3):  # petites épines au-dessus de l'arcade
            pieces.append(m.spike(f"arcade_ep{k}{s}", "brun_noir", (s * (1.1 + 0.4 * k), -9.9 + 0.35 * k, 7.95),
                                  (0.35 * s, 0.4, 1), ARRIERE, 0.5 + 0.12 * k, 0.17, bend=0.6, sides=4))
        # muscle de la mâchoire (joue) + deux écailles
        joue = Ellipsoid((JOUE * s, -8.7, 6.05), (0.65, 1.1, 0.85))
        pieces.append(m.ellipsoid(f"masseter{s}", "sable", joue, jitter=0.04, seed=3))
        pieces += m.scales(f"ej{s}", joue, 2, (-0.5, 0.5), (-60, 60) if s > 0 else (120, 240), peau, ARRIERE,
                           0.5, h=0.1, tilt=6, seed=4)
        # collerette d'épines sur les joues
        for k in range(4):
            pieces.append(m.spike(f"joue{k}{s}", "sable" if k % 2 else "sable_fonce",
                                  (s * 1.75, -8.0 + 0.15 * k, 6.4 - 0.4 * k), (s, 0.7, 0.1 - 0.15 * k),
                                  ARRIERE, 1.4 - 0.15 * k, 0.32, bend=0.35))
        # crocs du haut : plantés dans la gencive, sous le bord du museau
        for k in range(8):
            y = -9.2 - 0.4 * k
            base = (s * bord(MUSEAU, y, LEVRE_HAUT), y, LEVRE_HAUT + 0.08)
            pieces.append(m.spike(f"croc{k}{s}", "dent", base, (0, -0.1, -1), (0, -1, 0),
                                  0.5 + rng.uniform(0, 0.2) + 0.25 * (k == 2), 0.15 + 0.04 * (k == 2),
                                  bend=0.15, sides=4, steps=1))
        obj, pts, radii = corne(m, s)
        pieces.append(obj)
        dedans = verifie_cornes(pts[1:], radii[1:])  # le 1er point est la racine, enfouie dans le crâne
        if dedans:
            print(f"ATTENTION : la corne {'G' if s > 0 else 'D'} touche le corps ({len(dedans)} points)")
    # couronne d'épines à l'arrière du crâne
    for k, dx in enumerate((-0.8, 0.0, 0.8)):
        pieces.append(m.spike(f"couronne{k}", "brun_noir", (dx, -7.0, 8.2), (dx * 0.4, 1, 0.7), BAS,
                              1.5 - 0.3 * abs(dx), 0.32, bend=0.25))
    # intérieur de la gueule (visible quand la mâchoire est ouverte)
    pieces.append(m.ellipsoid("gueule", "gueule", Ellipsoid((0, -10.2, 5.55), (1.0, 1.9, 0.4))))
    m.join("Tete", pieces)

    mach = [m.ellipsoid("machoire", "rouille", MACHOIRE),
            m.ellipsoid("gencive_bas", "gueule", Ellipsoid((0, -10.3, 5.47), (1.0, 1.85, 0.14)))]
    # écailles sous le menton et sur les côtés de la mâchoire
    mach += m.scales("em", MACHOIRE, 7, (-0.8, 0.75), (190, 350),
                     lambda t, a, r: "rouille" if r.random() < 0.6 else "sable_fonce", ARRIERE, 0.45, h=0.05,
                     tilt=2, size=0.5, seed=5)
    for s in (1, -1):
        for k in range(6):
            y = -9.3 - 0.45 * k
            mach.append(m.spike(f"dent{k}{s}", "dent", (s * bord(MACHOIRE, y, LEVRE_BAS), y, LEVRE_BAS - 0.08),
                                (0, -0.1, 1), (0, -1, 0), 0.32 + 0.08 * (k % 2), 0.12, bend=0.1,
                                sides=4, steps=1))
        # défenses : sortent du bord de la mâchoire et remontent le long du museau, côté extérieur
        base = (s * bord(MACHOIRE, -11.0, 5.2, 0.7), -11.0, 5.2)  # plantée DANS la mâchoire
        assert MACHOIRE.inside(base), "la défense doit partir de la mâchoire"
        mach.append(m.spike(f"defense{s}", "dent", base, (0.18 * s, -0.15, 1), (s, 0, 0), 1.25, 0.22,
                            bend=0.3))
    machoire = m.join("Machoire", mach)
    # gueule entrouverte : la mâchoire pivote autour de la charnière
    m.rotate_about([machoire], 14, "X", CHARNIERE)

    # yeux (Material = Neon dans Roblox) avec pupille fendue de reptile
    for nom, s in (("Oeil_G", 1), ("Oeil_D", -1)):
        m.join(nom, [
            m.ico("globe", "oeil_glace", (1.86 * s, -9.7, 7.32), (0.2, 0.36, 0.22), rot=(0, 0, -12 * s)),
            m.box("pupille", "brun_noir", (2.02 * s, -9.75, 7.32), (0.05, 0.07, 0.18), rot=(0, 0, -12 * s)),
        ])


def narine(m, s):
    """Narine posée sur le bout du museau (à moitié enfoncée dans la surface, pas devant)."""
    x, z = 0.42 * s, 6.75
    k = 1 - (x / MUSEAU.r.x) ** 2 - ((z - MUSEAU.c.z) / MUSEAU.r.z) ** 2
    y = MUSEAU.c.y - MUSEAU.r.y * math.sqrt(k) + 0.06  # surface avant du museau, légèrement dedans
    assert MUSEAU.inside((x, y, z)), "la narine doit être sur le museau"
    return m.box(f"narine{s}", "brun_noir", (x, y, z), (0.17, 0.1, 0.11), rot=(0, 0, 25 * s), bevel=0.3)


def corne(m, s):
    """Corne annelée de bélier : part du haut du crâne, passe derrière l'oeil, descend et revient
    vers l'avant le long de la joue. Elle reste autour de la tête, sans toucher le cou ni le corps."""
    # racine plantée dans le crâne, puis la spirale
    pts, radii = [(0.45 * s, -8.9, 7.7)], [0.9]
    assert CRANE.inside(pts[0]), "la corne doit partir du crâne"
    n, tours = 56, 0.92
    for i in range(n):
        u = i / (n - 1)
        theta = (u * tours - 0.08) * 2 * math.pi
        retrecit = 1 - 0.35 * u
        x = (0.9 + 3.3 * u ** 0.45) * s  # s'écarte vite du crâne
        y = -8.3 + 1.7 * retrecit * math.sin(theta)
        z = 7.1 + 2.0 * retrecit * math.cos(theta)
        pts.append((x, y, z))
        anneau = 1.0 + (0.11 if i % 2 == 0 else 0.0)  # anneaux de croissance
        radii.append((0.95 * (1 - u) + 0.1 * u) * anneau)
    radii[-1] = 0.0
    return m.tube(f"corne{s}", "brun_noir", pts, radii, sides=7, ring_scale=(1.0, 0.7), up=(1, 0, 0)), pts, radii


def verifie_cornes(pts, radii):
    """Liste les points de la corne qui rentrent dans le cou, le torse ou les épaules."""
    volumes = list(TORSE) + [Ellipsoid((x, y, 6.0), (1.5, 1.8, 2.0)) for x, y in ((2.9, -3.4), (-2.9, -3.4))]
    return [i for i, (p, r) in enumerate(zip(pts, radii)) if any(e.inside(p, r) for e in volumes)]


if __name__ == "__main__":
    model = build()
    st = model.stats()
    print("stats", st["pieces"], "pièces,", st["triangles"], "triangles")
    for nom, t in sorted(st["par_piece"].items()):
        print("   ", nom, t)
    model.export()
    if "--no-render" not in sys.argv:
        tete_c = (0, -10.0, 6.3)
        vues = ((35, "avant"), (215, "arriere"), (28, "tete", 2.4, (0, -9.5, 6.8)),
                (0, "tete_face", 3.0, tete_c, 0.4),         # bien en face, à hauteur de la gueule
                (90, "tete_profil", 2.8, tete_c, 0.6),      # de côté
                (125, "tete_arriere", 2.6, (0, -9.3, 6.6), 2.2))  # de trois-quarts arrière
        for p in lp.render_previews(model, views=vues):
            print("preview", p)
