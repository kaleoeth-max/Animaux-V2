# Animations d'un modèle (squelette + clips pour Roblox)

Code commun : `lib/animation.py`. Un modèle s'y branche avec un module de quelques lignes
(`scripts/animations_rat.py` : `animation.configurer(gardien_rat)` puis `animation.main()`), en fournissant dans son
script de modèle les constantes listées en tête de `lib/animation.py` et un dictionnaire `ANIM` :
os Torse / Tete / bout de mâchoire, pièces liées au torse (ex. `("Corps", "Ble")`), foulées de marche / course,
pose de sommeil, amplitude du coup de croc. Régler ces valeurs jusqu'à ce que le vérificateur dise `ok` partout
(ex. pour le rat, tête basse : `croc_tete=2`, `croc_pique=1.5` sinon la mâchoire plonge dans le sol ;
pattes courtes : `pas_course=1.55` sinon les chevilles n'atteignent plus leur cible).

## 1. Squelette

- Os créés en mode édition à partir des **points du modèle** (exposés par le script du modèle) :
  `Racine` → `Torse` → `Tete` → `Machoire` / `Paupiere_G/D` ; `Queue1..4` ; pour chaque patte une chaîne
  d'os entre ses articulations + un os `<Patte>_Pied`.
- `roll = 0`, pas de `use_connect` : les rotations sont toujours exprimées en axes du monde (voir 3), donc
  l'orientation locale des os n'a pas d'importance.

## 2. Liaison des pièces aux os

- Pièce rigide → un seul os (`lier(rig, obj, os_unique=...)`) : Corps→Torse, Tete/Oeil→Tete, Machoire→Machoire.
- Pièce qui doit se plier (queue, pattes) → pondération par distance aux segments d'os, avec un fondu entre
  deux os voisins (`lier(rig, obj, segments, fondu=...)`).
- Toute nouvelle pièce doit être prise en charge dans `lier_tout` ou listée dans `ANIM["pieces_torse"]`
  (sinon erreur volontaire).
- **Astuce paupières** : une pièce « paupière fermée » cachée dans la tête au repos (vérifier qu'aucun sommet ne
  dépasse), qu'un os fait glisser devant l'œil pendant `Sommeil` (Roblox n'anime pas l'échelle des os).

## 3. Poses

Chaque animation est une fonction `anim_x(u)` (u ∈ [0, 1]) qui renvoie `{os: ((rx, ry, rz) degrés, (dx, dy, dz))}`.
Les rotations sont en **axes du monde au repos**, autour de la tête de l'os, et s'ajoutent à celles du parent :
- `rx > 0` : tête / mâchoire (pointées vers l'avant) descendent ; patte (vers le bas) part en arrière ; queue monte.
- `rz > 0` : la queue part vers la droite de la bête (-X) ; la tête tourne vers sa gauche.

`creer_action` convertit : `matrix_basis = repos⁻¹ · T(tête + d) · R · T(-tête) · repos`, puis pose des clés
`location` + `rotation_quaternion` à chaque image (30 images/s). Outils : `cles(u, [(u, valeur), ...])` pour des
clés lissées, `queue_ondule(...)`, `math.sin(TAU * u)` pour les boucles (début = fin).

## 4. Pieds au sol : cinématique inverse (`ik_pattes`)

- Toujours finir une pose par `return ik_pattes(pose, cibles, pointe)`.
- Par défaut chaque cheville reste à sa position de repos (pieds posés) même si le torse bouge ;
  `cibles={patte: (dy, dz)}` déplace la cheville (pas de marche/course : glisse en arrière pendant l'appui, revient
  levée) ; `pointe={patte: degrés}` incline les orteils (seulement une fois le pied levé : `k * leve**2`).
- IK plane (plan avant/arrière) à 2 segments ; patte arrière à 3 segments : le dernier garde son orientation.
  Le sens de pliage (coude en arrière, genou en avant) est repris de la pose de repos.
- Au repos l'IK doit redonner **0°** partout (test rapide : `ik_pattes({})`).

## 5. Export et aperçus

- `<nom>_rig.fbx` (modèle + os, sans animation), un `<nom>_<Animation>.fbx` par clip (`bake_anim=True`,
  une seule action), `<nom>_anime.glb` (toutes les actions), un GIF par clip dans `previews/` (Cycles, 420 px,
  une image sur deux). Compter ~1 min de rendu par seconde d'animation.
- Supprimer les FBX/GIF des animations retirées (`git rm`).

## 6. Vérification (obligatoire avant de livrer)

```bash
python3 scripts/verifier_animations.py animations_<modele>
```
Chaque ligne doit être `ok` : écart cheville/cible < 0,15, point le plus bas > -0,5 (les pointes d'ergots qui
s'enfoncent un peu en position couchée sont tolérées). Puis regarder des **planches** de 5 images par GIF et
au moins un gros plan rendu sur une image clé (pattes pliées, gueule ouverte) pour repérer une déformation.

## 7. Script Roblox

`roblox/Gardien_Animations.server.lua` (commun) : charge les clips par ID, choisit Marche/Course selon
la vitesse réelle (`AdjustSpeed` = vitesse / vitesse nominale du clip), attaque via
`SetAttribute("Action", "CoupDeCroc")`, sommeil via `SetAttribute("Dort", true/false)`.
Vitesse nominale d'un clip en place = longueur glissée par le pied pendant l'appui / durée de l'appui.
