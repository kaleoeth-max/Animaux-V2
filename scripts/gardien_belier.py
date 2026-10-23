"""Gardien de la Prairie n°1 : le Bélier Colosse (version monstre / boss).

Bête blindée à quatre pattes : corps bas couleur sable rayé de rouille, épines sombres le
long du dos, énormes cornes noires en spirale, gueule à crocs, griffes et queue à épines.
Rôle : le gardien « tank », lent, massif et terrifiant.

Lancer :  python3 scripts/gardien_belier.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import lowpoly as lp  # noqa: E402

NAME = "Gardien_Prairie_Belier"


def epine(m, nom, base, hauteur, rayon, penche=(0, 0, 0), couleur="brun_noir"):
    """Épine à 4 faces posée sur `base`, inclinée de `penche` (degrés)."""
    rx, ry, rz = penche
    rot = lp.Euler(tuple(math.radians(a) for a in penche), "XYZ").to_matrix()
    centre = lp.Vector(base) + rot @ lp.Vector((0, 0, hauteur / 2))
    return m.cone(nom, couleur, tuple(centre), rayon, 0.0, hauteur, rot=(rx, ry, rz), sides=4)


def build():
    lp.reset_scene()
    m = lp.Model(NAME)

    # ---------------------------------------------------------------- corps blindé
    corps = [
        m.ico("poitrail", "sable", (0, -3.2, 6.2), (3.3, 3.0, 2.9), jitter=0.22),
        m.ico("dos", "sable", (0, 0.6, 6.4), (3.1, 3.4, 2.8), jitter=0.22, seed=1),
        m.ico("hanches", "sable", (0, 4.2, 6.0), (2.8, 2.7, 2.5), jitter=0.2, seed=2),
        m.ico("ventre", "rouille", (0, 0.4, 4.4), (2.3, 5.6, 1.3), jitter=0.12),
    ]
    # plaques d'armure sur l'échine
    for i, y in enumerate((-4.2, -2.4, -0.6, 1.2, 3.0, 4.8)):
        corps.append(m.box(f"plaque{i}", "sable_fonce" if i % 2 else "sable", (0, y, 8.9 - 0.12 * abs(y)),
                           (1.6, 0.85, 0.45), rot=(-12, 0, 0), bevel=0.3))
    # rayures rouille sur les flancs (en chevrons)
    for i, y in enumerate((-4.4, -2.6, -0.8, 1.0, 2.8, 4.5)):
        for s in (1, -1):
            corps.append(m.box(f"rayure{i}{s}", "rouille", ((2.75 - 0.08 * abs(y)) * s, y, 6.6),
                               (0.35, 0.36, 1.15 + 0.25 * (i % 2)), rot=(22, 10 * s, 0), bevel=0.25))
    # crinière de piquants sable autour du cou (le reste de sa laine)
    for i in range(9):
        a = math.radians(-100 + i * 25)
        corps.append(epine(m, f"criniere{i}", (2.6 * math.sin(a), -5.0, 6.9 + 2.4 * math.cos(a)),
                           2.0, 0.75, penche=(-55, 40 * math.sin(a), 0), couleur="sable_fonce"))
    # grandes épines du dos + petites rangées sur les épaules
    for i, (y, h) in enumerate(((-4.6, 2.2), (-3.0, 2.8), (-1.3, 3.1), (0.4, 3.0), (2.1, 2.6), (3.8, 2.1), (5.3, 1.6))):
        corps.append(epine(m, f"epine{i}", (0, y, 8.6 - 0.1 * abs(y)), h, 0.6, penche=(-28, 0, 0)))
        for s in (1, -1):
            corps.append(epine(m, f"epine_cote{i}{s}", (1.7 * s, y + 0.3, 8.0 - 0.15 * abs(y)), h * 0.55, 0.38,
                               penche=(-30, 32 * s, 0)))
    m.join("Corps", corps)

    # ---------------------------------------------------------------- pattes griffues
    for nom, x, y, avant in (("AvG", 2.9, -3.4, True), ("AvD", -2.9, -3.4, True),
                             ("ArG", 2.7, 4.2, False), ("ArD", -2.7, 4.2, False)):
        s = 1 if x > 0 else -1
        epaule = (x, y, 5.6)
        coude = (x + 0.5 * s, y + (0.4 if avant else 0.9), 3.0)
        pied = (x + 0.6 * s, y - 0.6, 0.55)
        patte = [
            m.ico("epaule", "sable", epaule, (1.5, 1.7, 2.0), jitter=0.15, seed=int(y)),
            m.beam("haut", "sable_fonce", epaule, coude, 1.0, 1.1, bevel=0.2),
            m.beam("bas", "sable", coude, pied, 0.85, 0.9, bevel=0.2),
            m.box("bande", "rouille", (coude[0], coude[1] - 0.1, 2.2), (1.0, 1.0, 0.3), bevel=0.3),
            m.ico("pied", "sable_fonce", (pied[0], pied[1] - 0.3, 0.5), (1.2, 1.5, 0.55)),
            epine(m, "ergot", (coude[0], coude[1] + 0.8, coude[2]), 1.3, 0.35, penche=(-70, 0, 0)),
        ]
        for k, dx in enumerate((-0.65, 0.0, 0.65)):  # trois griffes vers l'avant
            patte.append(epine(m, f"griffe{k}", (pied[0] + dx, pied[1] - 1.5, 0.35), 1.0, 0.25,
                               penche=(100, 0, 0)))
        m.join(f"Patte_{nom}", patte)

    # ---------------------------------------------------------------- queue à épines
    pts = [(0, 6.2, 6.0), (0, 8.8, 5.2), (0, 11.4, 4.2), (0, 13.8, 3.6), (0, 16.0, 3.4)]
    queue = [m.tube("queue", "sable", pts, [1.5, 1.15, 0.8, 0.45, 0.0], sides=6, ring_scale=(1.0, 0.8))]
    for i, (y, z, h) in enumerate(((8.6, 6.3, 1.6), (10.6, 5.2, 1.3), (12.5, 4.4, 1.0), (14.3, 3.9, 0.8))):
        queue.append(epine(m, f"q{i}", (0, y, z), h, 0.4, penche=(-40, 0, 0)))
        for s in (1, -1):
            queue.append(epine(m, f"q{i}{s}", (0.9 * s * (1 - i * 0.2), y + 0.3, z - 0.6), h * 0.9, 0.3,
                               penche=(-60, 70 * s, 0), couleur="rouille"))
    m.join("Queue", queue)

    # ---------------------------------------------------------------- tête
    tete = [
        m.ico("crane", "sable", (0, -7.6, 6.9), (2.0, 2.3, 1.8), rot=(-8, 0, 0), jitter=0.12),
        m.ico("museau", "sable", (0, -9.9, 6.2), (1.45, 1.7, 1.05), jitter=0.08),
        m.box("arcade", "brun_noir", (0, -8.9, 7.75), (1.75, 0.45, 0.3), rot=(-15, 0, 0), bevel=0.3),
        m.box("narines", "brun_noir", (0, -11.45, 6.45), (0.6, 0.15, 0.3), bevel=0.3),
    ]
    for s in (1, -1):
        for k, y in enumerate((-9.2, -10.0, -10.8)):  # crocs du haut
            tete.append(epine(m, f"croc{k}{s}", ((1.05 - 0.1 * k) * s, y, 5.5), 0.55 + 0.15 * (k == 0), 0.16,
                              penche=(180, 0, 0), couleur="dent"))
        tete.append(corne(m, s))
    tete = [m.join("Tete", tete)]

    machoire = [m.ico("machoire", "rouille", (0, -9.3, 4.95), (1.25, 2.0, 0.55), rot=(8, 0, 0))]
    for s in (1, -1):  # défenses du bas
        machoire.append(epine(m, f"defense{s}", (0.95 * s, -10.6, 5.1), 0.8, 0.2, penche=(-10, 10 * s, 0),
                              couleur="dent"))
    m.join("Machoire", machoire)

    # yeux séparés : Material = Neon dans Roblox
    for nom, s in (("Oeil_G", 1), ("Oeil_D", -1)):
        m.ico(nom, "oeil_glace", (1.35 * s, -9.0, 7.15), (0.22, 0.3, 0.2), subdiv=1)
    return m


def corne(m, s):
    """Énorme corne en spirale : part du crâne, tourne en arrière, en bas, puis pointe vers l'avant."""
    pts, radii = [], []
    n, tours = 30, 0.95
    for i in range(n):
        u = i / (n - 1)
        theta = (u * tours - 0.12) * 2 * math.pi
        rayon = 2.3 * (1 - 0.35 * u)
        x = (1.3 + 3.0 * u ** 0.6) * s  # s'écarte vite de la tête, puis s'enroule
        y = -6.6 + rayon * math.sin(theta) - 0.8 * u
        z = 6.7 + rayon * math.cos(theta)
        pts.append((x, y, z))
        radii.append(0.8 * (1 - u) + 0.12 * u)
    radii[-1] = 0.0
    return m.tube(f"corne{s}", "brun_noir", pts, radii, sides=6, up=(1, 0, 0))


if __name__ == "__main__":
    model = build()
    print("stats", model.stats())
    model.export()
    if "--no-render" not in sys.argv:
        for p in lp.render_previews(model):
            print("preview", p)
