"""Gardien de la Prairie n°1 : le Bélier des Prés.

Gros bélier laineux aux cornes en spirale, avec une guirlande de fleurs et une cloche dorée.
Rôle : le gardien « tank », lent et massif.

Lancer :  python3 scripts/gardien_belier.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import lowpoly as lp  # noqa: E402

NAME = "Gardien_Prairie_Belier"


def build():
    lp.reset_scene()
    m = lp.Model(NAME)

    # ---------------------------------------------------------------- corps laineux
    corps = [m.ico("corps", "laine", (0, 0.4, 6.4), (3.2, 5.0, 3.0), jitter=0.15)]
    touffes = [  # (x, y, z, rayon) côté droit, dupliquées en miroir
        (1.5, -2.2, 8.5, 1.6), (1.6, 0.6, 8.8, 1.7), (1.4, 3.2, 8.4, 1.6),
        (2.9, -1.6, 6.6, 1.5), (3.0, 1.4, 6.4, 1.6), (2.4, 4.2, 6.0, 1.3),
        (2.6, -0.2, 4.6, 1.3),
    ]
    for i, (x, y, z, r) in enumerate(touffes):
        for s in (1, -1):
            couleur = "laine" if (i + (s > 0)) % 2 else "laine_ombre"
            corps.append(m.ico(f"touffe{i}{s}", couleur, (x * s, y, z), r, jitter=0.12, seed=s))
    corps.append(m.ico("dos", "laine", (0, 1.8, 9.3), (1.6, 2.4, 1.0), jitter=0.12))
    corps.append(m.ico("collerette", "laine", (0, -4.4, 6.9), (2.7, 1.8, 2.6), jitter=0.15))
    corps.append(m.ico("queue", "laine_ombre", (0, 5.5, 7.6), 0.8, subdiv=0))
    m.join("Corps", corps)

    # ---------------------------------------------------------------- pattes
    for nom, x, y in (("AvG", 1.8, -2.8), ("AvD", -1.8, -2.8), ("ArG", 1.8, 3.2), ("ArD", -1.8, 3.2)):
        patte = [
            m.ico("cuisse", "laine_ombre", (x, y, 4.2), 1.35, jitter=0.1),
            m.tube("jambe", "visage_belier", [(x, y, 3.6), (x, y - 0.1, 2.0), (x, y, 0.7)],
                   [0.6, 0.5, 0.5]),
            m.cone("sabot", "sabot", (x, y - 0.1, 0.35), 0.75, 0.55, 0.7),
        ]
        m.join(f"Patte_{nom}", patte)

    # ---------------------------------------------------------------- tête
    tete = [
        m.ico("crane", "visage_belier", (0, -6.4, 8.7), (1.5, 1.9, 1.5), rot=(-20, 0, 0)),
        m.ico("museau", "visage_belier", (0, -7.9, 7.7), (1.05, 1.1, 0.95)),
        m.ico("toupet", "laine", (0, -6.0, 10.0), (1.5, 1.3, 0.9), jitter=0.1),
        m.box("narine", "sabot", (0, -8.85, 7.95), (0.45, 0.12, 0.2), bevel=0.05),
    ]
    for s in (1, -1):
        # sourcils froncés : il garde ses oeufs !
        tete.append(m.box(f"sourcil{s}", "sabot", (0.95 * s, -7.25, 9.35), (0.55, 0.15, 0.13),
                          rot=(0, 22 * s, -15 * s), bevel=0.04))
        tete.append(m.tube(f"oreille{s}", "visage_belier",
                           [(1.2 * s, -5.6, 8.4), (2.1 * s, -5.3, 8.0), (2.7 * s, -5.1, 7.7)],
                           [0.35, 0.4, 0.0], ring_scale=(1.0, 0.45)))
        tete.append(corne(m, s))
    tete = [m.join("Tete", tete)]

    # yeux séparés : dans Roblox, mettre Material = Neon pour qu'ils brillent
    for nom, s in (("Oeil_G", 1), ("Oeil_D", -1)):
        tete.append(m.ico(nom, "oeil_ambre", (1.0 * s, -7.15, 8.95), (0.3, 0.3, 0.26), subdiv=1))
    # tête plus grosse et plus haute : silhouette de gardien
    m.scale_about(tete, 1.3, pivot=(0, -5.2, 8.4), offset=(0, -0.3, 0.6))

    # ---------------------------------------------------------------- guirlande + cloche
    guirlande = []
    arc = []
    for i in range(13):
        phi = math.radians(-80 + i * (160 / 12))
        arc.append((2.25 * math.sin(phi), -5.75 + 0.6 * (1 - math.cos(phi)), 6.3 - 1.2 * math.cos(phi) + 1.2))
    guirlande.append(m.tube("liane", "feuille_fonce", arc, 0.14, sides=5))
    couleurs = ("fleur_rose", "fleur_blanche", "fleur_jaune")
    for i, p in enumerate(arc[::2]):
        x, y, z = p
        guirlande.append(m.ico(f"petales{i}", couleurs[i % 3], (x, y - 0.15, z), (0.5, 0.3, 0.5),
                               subdiv=0, seed=i, jitter=0.03))
        coeur = "fleur_jaune" if couleurs[i % 3] != "fleur_jaune" else "corne_fonce"
        guirlande.append(m.ico(f"coeur{i}", coeur, (x, y - 0.42, z), 0.2, subdiv=0))
    for i, p in enumerate(arc[1::2]):
        x, y, z = p
        guirlande.append(m.ico(f"feuille{i}", "feuille", (x, y - 0.1, z), (0.42, 0.2, 0.28),
                               rot=(0, 30 * (1 if i % 2 else -1), 0), subdiv=0))
    bas = arc[6]
    guirlande.append(m.cone("cloche", "cloche_or", (bas[0], bas[1] - 0.2, bas[2] - 0.75), 0.6, 0.3, 0.8,
                            sides=8))
    guirlande.append(m.ico("battant", "corne_fonce", (bas[0], bas[1] - 0.2, bas[2] - 1.2), 0.18, subdiv=0))
    m.scale_about([m.join("Guirlande", guirlande)], 1.2, pivot=(0, -5.2, 6.8))
    return m


def corne(m, s):
    """Corne en spirale : part du haut du crâne, tourne vers l'arrière, le bas puis l'avant."""
    pts, radii = [], []
    n, tours = 26, 1.25
    for i in range(n):
        u = i / (n - 1)
        theta = u * tours * 2 * math.pi
        rayon = 1.75 * (1 - 0.62 * u)
        x = (1.0 + 1.5 * u) * s
        y = -5.6 + rayon * math.sin(theta)
        z = 8.75 + rayon * math.cos(theta)
        pts.append((x, y, z))
        radii.append(0.62 * (1 - u) + 0.1 * u)
    radii[-1] = 0.0
    return m.tube(f"corne{s}", "corne", pts, radii, sides=6, up=(1, 0, 0))


if __name__ == "__main__":
    model = build()
    print("stats", model.stats())
    model.export()
    if "--no-render" not in sys.argv:
        for p in lp.render_previews(model):
            print("preview", p)
