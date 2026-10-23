"""Gardien de la Prairie n°2 : le Grand Lièvre Sentinelle (style « blocs » chibi).

Style inspiré d'un chiot low poly : formes en blocs biseautés, grosse tête, deux tons
(caramel + blanc), pattes brun foncé, yeux noirs brillants et petit sourire.
Il garde son écharpe de feuilles et son bâton fleuri de gardien de la prairie.

Lancer :  python3 scripts/gardien_lievre.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import lowpoly as lp  # noqa: E402

NAME = "Gardien_Prairie_Lievre"
B = 0.28  # biseau des blocs (proportion de la demi-taille)


def build():
    lp.reset_scene()
    m = lp.Model(NAME)

    # ---------------------------------------------------------------- corps
    corps = [
        m.box("tronc", "caramel", (0, 0.3, 3.9), (1.9, 1.7, 2.3), bevel=B),
        m.box("ventre", "blanc_doux", (0, -1.2, 3.6), (1.3, 0.4, 1.8), bevel=B),
        m.box("queue", "blanc_doux", (0, 2.15, 1.9), 0.7, rot=(10, 0, 0), bevel=0.25),
    ]
    for s in (1, -1):
        corps += [
            m.box(f"cuisse{s}", "caramel", (1.6 * s, 0.6, 1.8), (0.8, 1.35, 1.25), bevel=B),
            m.box(f"pied{s}", "brun_patte", (1.3 * s, -0.9, 0.42), (0.7, 1.5, 0.42), bevel=B),
        ]
    m.join("Corps", corps)

    # ---------------------------------------------------------------- tête (grosse : style chibi)
    tete = [
        m.box("crane", "caramel", (0, -0.4, 8.25), (2.3, 2.0, 1.95), bevel=B),
        m.box("museau", "blanc_doux", (0, -2.2, 7.35), (1.15, 0.55, 0.75), bevel=0.25),
        m.box("liste", "blanc_doux", (0, -2.3, 9.0), (0.42, 0.18, 1.0), bevel=0.2),
        m.box("truffe", "noir_brillant", (0, -2.82, 7.78), (0.36, 0.13, 0.22), bevel=0.25),
        m.box("sourire_milieu", "noir_brillant", (0, -2.77, 7.42), (0.04, 0.05, 0.17)),
        m.box("dents", "dent", (0, -2.72, 6.88), (0.24, 0.07, 0.2), bevel=0.15),
    ]
    for s in (1, -1):
        tete += [
            m.box(f"sourire{s}", "noir_brillant", (0.22 * s, -2.77, 7.21), (0.22, 0.05, 0.045),
                  rot=(0, -28 * s, 0)),
            m.box(f"joue{s}", "joue_rose", (1.6 * s, -2.42, 7.6), (0.38, 0.05, 0.2), bevel=0.2),
        ]
    tete = [m.join("Tete", tete)]
    for nom, s in (("Oeil_G", 1), ("Oeil_D", -1)):
        oeil = [
            m.box("oeil", "noir_brillant", (0.98 * s, -2.42, 8.3), (0.33, 0.1, 0.42), bevel=0.3),
            m.box("reflet", "blanc_doux", (0.9 * s + 0.08, -2.53, 8.52), (0.1, 0.03, 0.11)),
        ]
        tete.append(m.join(nom, oeil))

    # ---------------------------------------------------------------- oreilles (séparées : animables)
    # oreille gauche bien droite
    tete.append(m.join("Oreille_G", [
        m.box("ext", "caramel", (1.15, -0.3, 12.0), (0.6, 0.28, 2.0), rot=(0, 10, 0), bevel=B),
        m.box("int", "joue_rose", (1.17, -0.6, 11.9), (0.33, 0.06, 1.55), rot=(0, 10, 0), bevel=0.2),
    ]))
    # oreille droite cassée vers l'avant : le petit air de caractère du lièvre
    pli = (-1.2, -0.3, 12.25)
    sens = (0, -math.sin(math.radians(60)), math.cos(math.radians(60)))
    haut = tuple(p + 1.0 * d for p, d in zip(pli, sens))
    tete.append(m.join("Oreille_D", [
        m.box("ext", "caramel", (-1.15, -0.3, 11.2), (0.6, 0.28, 1.15), rot=(0, -10, 0), bevel=B),
        m.box("int", "joue_rose", (-1.17, -0.6, 11.15), (0.33, 0.06, 0.85), rot=(0, -10, 0), bevel=0.2),
        m.box("pointe", "caramel_fonce", haut, (0.56, 0.27, 1.05), rot=(60, 0, 0), bevel=B),
    ]))

    # ---------------------------------------------------------------- bras
    epaule, main = {}, {}
    for cote, s in (("G", 1), ("D", -1)):
        epaule[cote] = (1.85 * s, -0.4, 6.0)
        # bras gauche posé sur le ventre, bras droit tendu vers le bâton
        main[cote] = (1.5, -1.85, 4.7) if s > 0 else (-2.75, -1.75, 5.0)
        m.join(f"Bras_{cote}", [
            m.beam("bras", "caramel", epaule[cote], main[cote], 0.5, bevel=0.12),
            m.box("patte", "brun_patte", main[cote], (0.5, 0.5, 0.38), bevel=B),
        ])

    # ---------------------------------------------------------------- bâton fleuri
    bx, by = -2.95, -1.75
    baton = [
        m.beam("manche", "bois", (bx, by, 0.15), (bx, by, 11.0), 0.2, bevel=0.05),
        m.box("bague", "bois_clair", (bx, by, 7.4), (0.3, 0.3, 0.22), bevel=0.2),
        m.box("coeur", "fleur_jaune", (bx, by - 0.05, 11.75), (0.45, 0.22, 0.45), rot=(0, 45, 0), bevel=0.25),
    ]
    for i in range(6):
        a = math.radians(i * 60)
        baton.append(m.box(f"petale{i}", "fleur_blanche",
                           (bx + 0.95 * math.cos(a), by + 0.1, 11.75 + 0.95 * math.sin(a)),
                           (0.5, 0.14, 0.3), rot=(0, -i * 60, 0), bevel=0.25))
    for i, s in enumerate((1, -1)):
        baton.append(m.box(f"feuille{i}", "feuille", (bx + 0.6 * s, by, 10.3 - 0.4 * i), (0.55, 0.1, 0.22),
                           rot=(0, -30 * s, 0), bevel=0.25))
    m.join("Baton", baton)

    # ---------------------------------------------------------------- écharpe de feuilles
    echarpe = []
    n = 10
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = 2.05 * math.sin(a), 0.3 - 1.85 * math.cos(a)
        echarpe.append(m.box(f"f{i}", "feuille" if i % 2 else "feuille_fonce", (x, y, 6.3),
                             (0.68, 0.32, 0.3), rot=(0, 0, -math.degrees(a)), bevel=0.25))
    # noeud et pan qui pendent sur le côté
    echarpe.append(m.box("noeud", "feuille_fonce", (1.2, -1.95, 6.0), 0.35, rot=(0, 0, 20), bevel=0.25))
    echarpe.append(m.box("pan", "feuille", (1.45, -2.0, 5.1), (0.3, 0.12, 0.7), rot=(0, -15, 20), bevel=0.25))
    m.join("Echarpe", echarpe)

    # taille de gardien : ~16 studs de haut
    m.scale_about(m.parts, 1.15, pivot=(0, 0, 0))
    return m


if __name__ == "__main__":
    model = build()
    print("stats", model.stats())
    model.export()
    if "--no-render" not in sys.argv:
        for p in lp.render_previews(model, fond="studio"):
            print("preview", p)
