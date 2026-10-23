# Animaux V2 — modèles 3D low poly pour Roblox

Modèles générés par scripts Python avec Blender en headless (module `bpy`, sans interface).

## Installation

```bash
pip install -r requirements.txt   # installe bpy (Blender 5.2 en module Python)
```

## Générer un modèle

```bash
python3 scripts/gardien_belier.py              # export + images d'aperçu
python3 scripts/gardien_lievre.py --no-render  # export seulement (plus rapide)
```

Sorties :
- `exports/<Nom>/<Nom>.fbx` et `.glb` : à importer dans Roblox Studio (*Avatar > 3D Importer* ou *Import 3D*).
- `exports/<Nom>/<Nom>_palette.png` : la texture des couleurs (déjà intégrée au FBX/GLB).
- `previews/<Nom>_avant.png` / `_arriere.png` : aperçus rendus.

## Steal an Egg — Zone Prairie : les gardiens

| Gardien | Rôle | Taille (studs) | Pièces | Triangles |
|---|---|---|---|---|
| **Bélier Colosse** (`Gardien_Prairie_Belier`) | tank / boss — bête à écailles (pattes lisses), épines, cornes annelées, griffes | ≈ 11 × 33 × 14 (haut) | 10 | ~10 700 (max ~5 700 par pièce) |
| **Grand Lièvre Sentinelle** (`Gardien_Prairie_Lievre`) | vigie, rapide — style « blocs » chibi | ≈ 7 × 6 × 16 (haut) | 10 | ~2200 |

![Bélier](previews/Gardien_Prairie_Belier_avant.png)
![Bélier, tête](previews/Gardien_Prairie_Belier_tete.png)
![Lièvre](previews/Gardien_Prairie_Lievre_avant.png)

## Conseils d'import dans Roblox

- **Échelle** : 1 unité Blender = 1 stud (un joueur fait ~5 studs). Si la taille ne colle pas, ajuste l'échelle dans l'importeur.
- **Yeux** : les pièces `Oeil_G` / `Oeil_D` sont séparées. Bélier : mets `Material = Neon` pour des yeux lumineux. Lièvre : yeux noirs brillants (garder `SmoothPlastic`).
- **Animation** : les pièces sont nommées et séparées (Tete, Machoire, Queue, Patte_AvG, Oreille_D, Bras_G, Baton…) pour être reliées par des `Motor6D` et animées (oreilles qui bougent, pattes qui marchent).
- **Orientation** : les modèles regardent vers l'avant (-Y dans Blender) ; tourne le modèle dans Studio si besoin.

## Structure

```
lib/lowpoly.py   outils communs (formes low poly, palette de couleurs, export, rendu)
scripts/         un script par modèle
exports/         fichiers prêts pour Roblox
previews/        images d'aperçu
```
