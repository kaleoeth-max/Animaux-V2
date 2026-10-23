"""Vérifie les animations d'un modèle : les pieds suivent-ils leur cible, et rien ne passe-t-il sous le sol ?

Pour chaque animation, mesure sur toutes les images (une sur deux) :
  - l'écart entre chaque cheville réelle et sa cible (doit rester < ~0,15 stud) ;
  - le glissement latéral des chevilles (doit rester petit) ;
  - le point le plus bas du modèle, et la pièce qui le porte (doit rester proche de 0).

Lancer :  python3 scripts/verifier_animations.py                  (Bélier)
          python3 scripts/verifier_animations.py animations_xxx    (autre module d'animations)

Le module d'animations doit fournir : g (module du modèle, avec g.build et g.PATTES), creer_squelette,
lier_tout, creer_action, ANIMATIONS, et des fonctions d'animation qui passent par ik_pattes
(elles renvoient alors les cibles des chevilles dans pose["_cibles"]).
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

nom_module = next((a for a in sys.argv[1:] if not a.startswith("-")), "animations_belier")
sys.argv = [sys.argv[0], "--no-render"]
A = importlib.import_module(nom_module)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402


def main():
    g = A.g
    model = g.build()
    rig = A.creer_squelette(model)
    A.lier_tout(model, rig)
    actions = [A.creer_action(rig, *a) for a in A.ANIMATIONS]
    ok = True
    for (nom, duree, fonction, boucle), action in zip(A.ANIMATIONS, actions):
        rig.animation_data.action = action
        ecart, glisse, plus_bas, piece_basse = 0.0, 0.0, 99.0, ""
        for f in range(1, duree + 2, 2):
            bpy.context.scene.frame_set(f)
            u = ((f - 1) / duree) % 1.0 if boucle else (f - 1) / duree
            for patte, cible in fonction(u).get("_cibles", {}).items():
                reel = rig.pose.bones[f"{patte}_Pied"].head
                ecart = max(ecart, (Vector((0, reel.y, reel.z)) - Vector((0, cible.y, cible.z))).length)
                glisse = max(glisse, abs(reel.x - cible.x))
            dg = bpy.context.evaluated_depsgraph_get()
            for o in model.parts:
                ev = o.evaluated_get(dg)
                me = ev.to_mesh()
                z = min((ev.matrix_world @ v.co).z for v in me.vertices)
                ev.to_mesh_clear()
                if z < plus_bas:
                    plus_bas, piece_basse = z, o.name
        alerte = ecart > 0.15 or plus_bas < -0.5
        ok &= not alerte
        print(f"{'ATTENTION' if alerte else 'ok':9s} {nom:12s} cheville/cible max {ecart:.3f} | "
              f"glissement latéral max {glisse:.3f} | point le plus bas {plus_bas:.2f} ({piece_basse})")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
