"""Animations du Bélier Colosse : Marche, Course, Sommeil, CoupDeCroc (voir lib/animation.py).

Lancer :  python3 scripts/animations_belier.py            (export + GIF)
          python3 scripts/animations_belier.py --no-render (export seulement)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import animation  # noqa: E402
import gardien_belier as g  # noqa: E402
from animation import ANIMATIONS, creer_action, creer_squelette, ik_pattes, lier_tout  # noqa: E402,F401

animation.configurer(g)

if __name__ == "__main__":
    animation.main()
