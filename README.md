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
python3 scripts/animations_belier.py           # squelette + animations du Bélier (+ GIF d'aperçu)
python3 scripts/verifier_animations.py         # vérifie pieds / sol de chaque animation
```

La méthode complète (outils, règles de qualité, animations, import Roblox) est rangée dans le skill
`.claude/skills/modele-roblox-lowpoly/` : Claude Code le charge automatiquement pour les prochains modèles.

Sorties :
- `exports/<Nom>/<Nom>.fbx` et `.glb` : à importer dans Roblox Studio (*Avatar > 3D Importer* ou *Import 3D*).
- `exports/<Nom>/<Nom>_palette.png` : la texture des couleurs (déjà intégrée au FBX/GLB).
- `previews/<Nom>_avant.png` / `_arriere.png` : aperçus rendus.

## Steal an Egg — Zone Prairie : les gardiens

| Gardien | Rôle | Taille (studs) | Pièces | Triangles |
|---|---|---|---|---|
| **Bélier Colosse** (`Gardien_Prairie_Belier`) ✅ validé (tag `belier-colosse-v1`) | tank / boss — bête couverte d'écailles, pattes à frange d'écailles et grands pieds griffus, longue gueule à crocs et mâchoire massive à plaques, cornes annelées | ≈ 11 × 33 × 14 (haut) | 12 | ~21 200 (max ~4 100 par pièce) |
| **Grand Lièvre Sentinelle** (`Gardien_Prairie_Lievre`) | vigie, rapide — style « blocs » chibi | ≈ 7 × 6 × 16 (haut) | 10 | ~2200 |

![Bélier](previews/Gardien_Prairie_Belier_avant.png)
![Bélier, tête](previews/Gardien_Prairie_Belier_tete.png)
![Bélier, tête de face](previews/Gardien_Prairie_Belier_tete_face.png)
![Bélier, tête de profil](previews/Gardien_Prairie_Belier_tete_profil.png)
![Bélier, tête de trois-quarts arrière](previews/Gardien_Prairie_Belier_tete_arriere.png)
![Lièvre](previews/Gardien_Prairie_Lievre_avant.png)

## Conseils d'import dans Roblox

- **Échelle** : 1 unité Blender = 1 stud (un joueur fait ~5 studs). Si la taille ne colle pas, ajuste l'échelle dans l'importeur.
- **Yeux** : les pièces `Oeil_G` / `Oeil_D` sont séparées. Bélier : iris ambre, mets `Material = Neon` pour qu'il brille. Lièvre : yeux noirs brillants (garder `SmoothPlastic`).
- **Animation (Lièvre)** : les pièces sont nommées et séparées (Tete, Oreille_D, Bras_G, Baton…) pour être reliées par des `Motor6D`.
- **Orientation** : les modèles regardent vers l'avant (-Y dans Blender) ; tourne le modèle dans Studio si besoin.

## Animations du Bélier Colosse

Squelette de 24 os (Racine, Torse, Tete, Machoire, Paupiere_G/D, Queue1-4, 3 à 4 os par patte + pied). Les pièces sont liées
aux os ; la queue et les pattes se plient en douceur. Les pieds restent posés au sol (cinématique inverse).

| Animation | Durée | Boucle | Aperçu |
|---|---|---|---|
| `Marche` | 1,3 s | oui | pas en diagonale sur place (~4,5 studs/s) |
| `Course` | 0,7 s | oui | galop, grandes foulées (~11,5 studs/s) |
| `Sommeil` | 3,0 s | oui | couché en sphinx, yeux fermés, queue enroulée, respiration lente |
| `CoupDeCroc` | 1,2 s | non | recul, gueule grande ouverte, attaque, claquement |

![Marche](previews/Gardien_Prairie_Belier_anim_Marche.gif)
![Course](previews/Gardien_Prairie_Belier_anim_Course.gif)
![Sommeil](previews/Gardien_Prairie_Belier_anim_Sommeil.gif)
![Coup de croc](previews/Gardien_Prairie_Belier_anim_CoupDeCroc.gif)

Fichiers (dans `exports/Gardien_Prairie_Belier/`) :
- `Gardien_Prairie_Belier_rig.fbx` : modèle + squelette.
- `Gardien_Prairie_Belier_<Animation>.fbx` : une animation par fichier.
- `Gardien_Prairie_Belier_anime.glb` : tout en un, pour regarder les animations dans un viewer glTF.

Dans Roblox Studio (pas encore testé de bout en bout) :
1. Importer `Gardien_Prairie_Belier_rig.fbx` avec l'importeur 3D (le modèle arrive avec ses os).
2. Ouvrir l'**Animation Editor** sur le modèle, puis `…` > *Import* > *From FBX Animation* et choisir
   `Gardien_Prairie_Belier_Marche.fbx` (recommencer pour chaque animation). Cocher la boucle pour `Marche`, `Course` et `Sommeil`,
   puis publier chaque animation pour obtenir son ID.
3. Mettre `roblox/GardienBelier_Animations.server.lua` dans le modèle et coller les ID en haut du script.
   Le script joue `Marche` quand le gardien bouge puis `Course` au-delà de 8 studs/s (à l'arrêt il garde sa pose),
   lance le coup de croc avec `gardien:SetAttribute("Action", "CoupDeCroc")` et le fait dormir avec
   `gardien:SetAttribute("Dort", true)` (`false` pour le réveiller).

Les pièces `Paupiere_G` / `Paupiere_D` sont cachées dans la tête : seule l'animation `Sommeil` les fait sortir.

## Structure

```
.claude/skills/   skill « modele-roblox-lowpoly » (la méthode, pour les prochains modèles)
lib/lowpoly.py   outils communs (formes low poly, palette de couleurs, export, rendu)
scripts/         un script par modèle (+ animations_belier.py)
roblox/          scripts Luau à mettre dans Roblox Studio
exports/         fichiers prêts pour Roblox
previews/        images d'aperçu
```
