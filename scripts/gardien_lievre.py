"""Gardien de la Prairie n°2 : le Grand Lièvre Sentinelle.

Lièvre géant dressé sur ses pattes arrière, avec une écharpe de feuilles et un bâton fleuri.
Rôle : le gardien « vigie », rapide, qui repère les voleurs d'oeufs de loin.

Lancer :  python3 scripts/gardien_lievre.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import lowpoly as lp  # noqa: E402

NAME = "Gardien_Prairie_Lievre"


def build():
    lp.reset_scene()
    m = lp.Model(NAME)

    # ---------------------------------------------------------------- corps
    corps = [
        m.ico("ventre", "lievre", (0, 0.3, 4.6), (2.4, 2.1, 3.2), jitter=0.1),
        m.ico("plastron", "lievre_creme", (0, -1.25, 4.6), (1.75, 1.0, 2.6), jitter=0.06),
        m.ico("poitrine", "lievre", (0, 0.0, 7.3), (2.0, 1.8, 1.9), jitter=0.08),
        m.ico("queue", "lievre_creme", (0, 2.5, 2.4), 0.95, jitter=0.12),
    ]
    for s in (1, -1):
        corps += [
            m.ico(f"cuisse{s}", "lievre", (1.8 * s, 0.5, 2.3), (1.3, 1.9, 1.8), jitter=0.1, seed=s),
            m.ico(f"pied{s}", "lievre_fonce", (1.45 * s, -1.4, 0.45), (0.85, 2.1, 0.5), seed=s),
            m.ico(f"orteils{s}", "lievre_creme", (1.45 * s, -3.2, 0.4), (0.6, 0.45, 0.35), subdiv=0),
        ]
    m.join("Corps", corps)

    # ---------------------------------------------------------------- tête
    tete = [
        m.ico("crane", "lievre", (0, -0.6, 9.7), (1.75, 1.85, 1.6), jitter=0.06),
        m.ico("nez", "truffe", (0, -2.6, 9.55), (0.3, 0.22, 0.22), subdiv=0),
        m.box("dents", "dent", (0, -2.4, 8.7), (0.22, 0.08, 0.25), bevel=0.04),
    ]
    for s in (1, -1):
        tete += [
            m.ico(f"joue{s}", "lievre_creme", (0.6 * s, -2.05, 9.05), (0.7, 0.6, 0.55), subdiv=1),
            m.box(f"sourcil{s}", "lievre_fonce", (0.85 * s, -2.05, 10.6), (0.5, 0.14, 0.12),
                  rot=(0, 20 * s, -25 * s), bevel=0.04),
        ]
    tete = [m.join("Tete", tete)]
    for nom, s in (("Oeil_G", 1), ("Oeil_D", -1)):  # Material = Neon dans Roblox
        tete.append(m.ico(nom, "oeil_vert", (0.95 * s, -1.85, 10.05), (0.32, 0.3, 0.36)))

    # ---------------------------------------------------------------- oreilles (séparées : animables)
    oreilles = {
        "G": [(0.6, -0.1, 10.9), (0.85, 0.0, 12.4), (1.05, 0.2, 14.0), (1.15, 0.35, 15.6), (1.2, 0.4, 16.3)],
        # l'oreille droite est cassée vers l'avant : plus de caractère
        "D": [(-0.6, -0.1, 10.9), (-0.85, 0.0, 12.4), (-1.1, 0.1, 13.8), (-1.6, -0.6, 14.6), (-2.1, -1.5, 14.9)],
    }
    for cote, pts in oreilles.items():
        ext = m.tube("ext", "lievre", pts, [0.5, 0.7, 0.68, 0.45, 0.0], ring_scale=(1.0, 0.42), up=(0, 1, 0))
        interieur = [(x, y - 0.22, z) for x, y, z in pts[:-1]]
        inn = m.tube("int", "rose_oreille", interieur, [0.3, 0.48, 0.45, 0.0],
                     ring_scale=(1.0, 0.3), up=(0, 1, 0))
        tete.append(m.join(f"Oreille_{cote}", [ext, inn]))
    m.scale_about(tete, 1.2, pivot=(0, -0.4, 8.6))

    # ---------------------------------------------------------------- bras
    for cote, s in (("G", 1), ("D", -1)):
        bras = [
            m.tube("bras", "lievre", [(1.7 * s, -0.2, 7.8), (2.4 * s, -0.9, 6.4), (1.75 * s, -2.2, 6.2)],
                   [0.62, 0.5, 0.42]),
            m.ico("patte", "lievre_creme", (1.7 * s, -2.4, 6.2), 0.55),
        ]
        m.join(f"Bras_{cote}", bras)

    # ---------------------------------------------------------------- bâton fleuri (main droite)
    bx, by = -1.7, -2.45
    baton = [m.tube("manche", "bois", [(bx, by, 0.2), (bx + 0.1, by, 4.0), (bx - 0.05, by, 8.5), (bx, by, 12.0)],
                    [0.26, 0.24, 0.24, 0.22])]
    baton.append(m.cone("bague", "bois_clair", (bx, by, 6.9), 0.36, 0.36, 0.5, sides=6))
    baton.append(m.ico("coeur_fleur", "fleur_jaune", (bx, by - 0.1, 12.6), 0.6, subdiv=1))
    for i in range(6):
        a = 2 * math.pi * i / 6
        baton.append(m.ico(f"petale{i}", "fleur_blanche",
                           (bx + 1.0 * math.cos(a), by + 0.15, 12.6 + 1.0 * math.sin(a)),
                           (0.6, 0.22, 0.6), subdiv=0, jitter=0.03, seed=i))
    for i, (dx, dz, rz) in enumerate(((0.75, 11.4, -35), (-0.75, 11.1, 35))):
        baton.append(m.ico(f"feuille{i}", "feuille", (bx + dx, by, dz), (0.7, 0.18, 0.3),
                           rot=(0, rz, 0), subdiv=0))
    m.join("Baton", baton)

    # ---------------------------------------------------------------- écharpe de feuilles
    echarpe = []
    for i in range(10):
        a = 2 * math.pi * i / 10
        x, y = 1.75 * math.sin(a), 0.0 - 1.6 * math.cos(a)
        echarpe.append(m.ico(f"f{i}", "feuille" if i % 2 else "feuille_fonce", (x, y, 8.45),
                             (0.75, 0.75, 0.38), rot=(0, 0, -math.degrees(a)), subdiv=0, seed=i))
    # deux pans qui pendent dans le dos
    for i, (dx, dz) in enumerate(((0.5, 7.4), (-0.3, 6.5))):
        echarpe.append(m.ico(f"pan{i}", "feuille_fonce" if i else "feuille", (dx, 1.95, dz),
                             (0.55, 0.25, 0.85), rot=(10, 0, 15 * (1 - 2 * i)), subdiv=0))
    m.join("Echarpe", echarpe)
    return m


if __name__ == "__main__":
    model = build()
    print("stats", model.stats())
    model.export()
    if "--no-render" not in sys.argv:
        for p in lp.render_previews(model):
            print("preview", p)
