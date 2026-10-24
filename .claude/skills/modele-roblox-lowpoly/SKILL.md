---
name: modele-roblox-lowpoly
description: Crée ou modifie un modèle 3D low poly pour les jeux Roblox de ce dépôt (Animaux V2, Steal an Egg) avec Blender en headless (module Python bpy) — gardiens de zone, animaux, monstres — puis l'exporte en FBX/GLB, rend des aperçus, et peut ajouter un squelette et des animations (marche, course, sommeil, attaque) importables dans Roblox. À utiliser dès que l'utilisateur demande un nouveau modèle, un gardien, une amélioration de modèle (tête, bouche, pattes, yeux, écailles…), une animation, ou montre une image d'inspiration pour un modèle.
---

# Modèle 3D low poly pour Roblox (Blender headless)

Méthode mise au point sur le **Bélier Colosse** (gardien de la zone Prairie, validé par l'utilisateur,
commit `59db35f`), puis réutilisée pour le **Rat Ravageur** (zone Champ, validé, commit `d37058e`). Références : `scripts/gardien_belier.py`
et `scripts/gardien_rat.py` (modèles), `lib/animation.py` (squelette + animations, commun à tous) et les petits
modules `scripts/animations_<modele>.py`. Pour un nouveau quadrupède, copier `gardien_rat.py` (le plus récent)
et l'adapter.

**Direction artistique commune** (« mutants » de Steal an Egg) : écailles qui se chevauchent avec zigzags rouille
sur les flancs, crête d'épines noires courbes, gueule à crocs (mâchoire massive à plaques et frange), yeux de
reptile lumineux, pattes écaillées à ergots. Chaque zone ajoute sa touche (Prairie : cornes de bélier ;
Champ : épis de blé mutants sur le dos).
**Chaque gardien a sa propre palette** (l'utilisateur a refusé un rat aux couleurs du Bélier) : mêmes formes,
couleurs différentes. Bélier : sable + zigzags rouille, épines noires, yeux ambre. Rat : anthracite + zigzags vert
toxique, épines couleur os, yeux rouges. Loup (Forêt) : gris-bleu nuit (dos foncé, ventre clair),
ronces violettes, épines blanches, yeux violets. Pour un nouveau gardien, choisir une palette nettement différente des
précédents et l'annoncer à l'utilisateur.

## Mise en route

```bash
pip install -r requirements.txt        # bpy (Blender 5.2 en module Python)
python3 scripts/gardien_belier.py       # exemple : export + aperçus
```

- Pas de GPU / OpenGL dans le conteneur : EEVEE et Workbench ne marchent pas. Les rendus se font avec
  **Cycles CPU** (`lp.render_previews`, déjà configuré). Un rendu 900 px ≈ 20 s.
- `import bpy` doit précéder `import bmesh` (déjà fait dans `lib/lowpoly.py`).
- Scripts longs (rendus d'animation, plusieurs minutes) : les lancer en arrière-plan.

## Conventions (ne pas changer sans raison)

- **Échelle** : 1 unité Blender = 1 stud. Un joueur fait ~5 studs ; un gardien boss ≈ 10 à 35 studs.
- **Orientation** : le modèle regarde vers **-Y**, repose sur **z = 0** (rien sous le sol au repos).
- **Couleurs** : une seule texture « palette » (`lp.PALETTE`, une case par couleur). Ajouter une couleur
  **à la fin** du dictionnaire uniquement (l'ordre fixe les UV). Les valeurs sont en sRGB 0-255, écrites telles
  quelles dans l'image (ne pas les convertir en linéaire : bug déjà corrigé une fois).
- **Pièces** : chaque partie animable ou spéciale est une pièce nommée (`Tete`, `Machoire`, `Queue`,
  `Patte_AvG`, `Oeil_G`…) obtenue avec `m.join(nom, [morceaux])`. Les pièces à passer en `Neon` dans Roblox
  (iris) sont séparées. Garder **< 10 000 triangles par pièce** (`m.stats()` alerte au-delà).
- Code, commentaires, noms : **en français**, comme le reste du dépôt.

## Boîte à outils (`lib/lowpoly.py`)

| Outil | Usage |
|---|---|
| `lp.reset_scene()`, `m = lp.Model(nom)` | nouvelle scène, nouveau modèle (crée la palette) |
| `m.ico / m.box / m.cone / m.beam / m.tube` | formes de base (`beam` = bloc entre 2 points, `tube` = suit des points avec un rayon par point, 0 = pointe) |
| `lp.Ellipsoid(centre, (rx, ry, rz), axis, up)` | volume orienté + surface paramétrée : `point(t, a)`, `normal(t, a)`, `inside(p, marge)`, `Ellipsoid.between(p1, p2, r)` |
| `m.ellipsoid(nom, couleur, ell)` | volume de base à partir d'un Ellipsoid |
| `m.scales(prefixe, ell, rangs, plage_t, plage_a, couleur_fn, flow, pas, h, tilt, size)` | écailles qui se chevauchent sur un Ellipsoid |
| `m.kite(...)` | une écaille / plaque ; `m.spike(...)` : épine, dent, griffe courbe |
| `m.fur(...)` / `m.meche(...)` | **poils** au lieu d'écailles : mèches plates couchées vers l'arrière (mêmes paramètres de répartition que `scales`, plus `souleve` et `longueur`) |
| `lp.zigzag(x)` | motif en zigzag pour `couleur_fn` (ex. rayures rouille sur les flancs) |
| `m.rotate_about / m.scale_about` | ajuster une pièce (ex. ouvrir la mâchoire autour de la charnière) |
| `m.export()` | FBX (texture intégrée) + GLB dans `exports/<nom>/` |
| `lp.render_previews(m, views, fond)` | aperçus PNG ; vue = `(angle, nom)` ou `(angle, nom, zoom, cible, hauteur)` ; angle 0 = de face, 90 = côté gauche ; `fond="prairie"` ou `"studio"` |

Paramètres de surface d'un Ellipsoid : `t` ∈ [-1, 1] le long de l'axe, `a` en degrés autour
(90 = dessus, 270 = dessous). Pour un membre créé avec `up=(0, 1, 0)` : a=0 → +X, 90 → arrière, 270 → avant.

## Déroulé d'un nouveau modèle

1. **Proposer** 2 idées différentes (silhouettes contrastées) si l'utilisateur ne précise pas. S'il envoie une
   image d'inspiration, en décrire les traits clés (forme, couleurs, détails) avant de coder.
2. **Construire** dans `scripts/<nom_du_modele>.py` : volumes de base → détails → pièces jointes par partie.
   Exposer en constantes de module tout ce dont l'animation aura besoin (volumes de la tête, `PATTES`,
   `articulations()`, chemin de la queue, charnière de la mâchoire, repère des yeux…).
3. **Rendre** les aperçus et **les regarder** (outil Read sur les PNG) : vue d'ensemble avant/arrière, puis
   gros plans (tête de face, de profil, trois-quarts arrière, pattes) — rendre les gros plans de travail dans le
   dossier scratchpad (`lp.PREVIEWS = ...`) pour ne pas polluer `previews/`.
4. **Corriger**, re-rendre, jusqu'à ce que ce soit propre. **Vérifier par le calcul**, pas seulement à l'œil (voir
   ci-dessous).
5. **Envoyer** les images à l'utilisateur (SendUserFile, `display: "render"`), expliquer en français ce qui a changé.
6. **Mettre à jour** `README.md` (tableau des modèles : taille mesurée, pièces, triangles), **commiter**, et
   **pousser** (le hook du dépôt exige que tout soit poussé en fin de tour).

## Règles de qualité (apprises des retours de l'utilisateur)

- **Tout ce qui sort de la tête doit y être ancré** : dents, défenses, cornes, narines, paupières. Le vérifier
  avec `Ellipsoid.inside()` et un `assert` (ex. base de chaque dent dans la gencive / la mâchoire, racine des cornes
  dans le crâne, narines sur la surface du museau). Ces asserts ont déjà attrapé plusieurs erreurs.
- **Rien ne doit traverser le corps** : vérifier qu'une corne ne rentre pas dans le cou/torse/épaules
  (`verifie_cornes` dans `gardien_belier.py`), en ignorant la racine volontairement enfouie.
- **Rien sous le sol** au repos (point le plus bas ≈ 0) : griffes courbées jusqu'au sol, pas à travers.
- **Poils (rat)** : mèches couchées, `souleve` ≈ 0,05–0,12 (au-delà de ~0,25 ça fait hérisson), plus courtes et
  plus rases sur la tête et le museau ; couleur d'accent en **fines traînées** seulement (sinon on dirait de l'herbe).
  La fourrure coûte plus cher en triangles que les écailles (~7 500 pour le corps du rat) : surveiller `m.stats()`.
- **Ne pas faire « pareil que les autres »** : l'utilisateur a refusé un loup trop proche du Bélier et du Rat
  (même fourrure partout, même crête d'épines, même gueule en zigzag). Chaque gardien doit avoir son **style de
  surface** (Bélier : écailles ; Rat : fourrure ; Loup : volumes lisses à facettes + marques + touffes `touffe()` en
  dents de scie aux endroits typiques), sa propre **dentition** (loup : incisives, grands crocs, petites dents
  triangulaires) et son propre **motif sur le dos** (loup : tiges de ronces en arc au lieu d'une crête).
- **Ronces réalistes** (loup, `gardien_loup.py`) : `ronce()` = tige effilée (bois `ronce_fonce` puis pousse
  `tige_ronce`), épines crochues vers la base tous les ~0,3 stud, `feuille_trifoliee()`, `mure()` (grappe de
  drupéoles noires ou rouges), `fleur()`. Tiges du dos avec `tige_en_arc()` : elles doivent retomber **dans le vide
  sur le côté** (sinon on dirait des arceaux de croquet) ; enroulements avec `enroulement()` (pas et écart
  irréguliers, jamais une spirale parfaite), `lift` ≈ 0,1–0,25 au-dessus de la surface.
- **Longues pattes** (loup) : au repos, garder le coude bien replié ; une patte presque tendue n'a plus de réserve
  quand le corps se cabre au galop (le vérificateur le signale : écart cheville/cible > 0,15).
- **Pattes de rat** : mains à paume rose, 4 doigts à jointures + petit pouce ; pieds arrière longs posés à plat
  jusqu'au talon, 5 doigts ; griffes sombres (pas couleur os, sinon on les confond avec les épines).
- **Écailles plaquées**, sinon l'animal paraît « poilu » : `h` ≈ 0,08–0,17 et `tilt` ≤ 8 sur le corps,
  plus fins sur la tête (`h` ≈ 0,06–0,1, `size` 0,5–0,8).
- **Pas de « cou » fin** entre deux volumes (ex. jambe → pied) : ajouter un volume de raccord.
- **Bouche** façon monstre : longue ligne de gueule, rangée serrée de crocs en zigzag jusqu'au fond, dents du bas
  emboîtées, lèvres sombres, mâchoire du bas massive avec plaques sur les côtés et frange d'écailles pointues
  dessous, menton qui ne dépasse pas du museau, gueule entrouverte au repos.
- **Yeux** : posés sur la surface du crâne, orbite sombre, iris séparé (Neon), pupille fendue, paupière du haut
  épaisse et inclinée vers le museau pour un regard méchant.
- Mesurer la taille réelle en **réimportant le FBX** avant de l'écrire dans le README.

## Animations

Voir [animations.md](animations.md) : squelette, liaison des pièces, poses en axes du monde, cinématique inverse
des pattes, export Roblox, GIF, vérification (`python3 scripts/verifier_animations.py <module>`).
Le code est générique (`lib/animation.py`) : un nouveau modèle fournit ses constantes (`PATTES`,
`articulations()`, `QUEUE`, `CHARNIERE`, `OUVERTURE`, `repere_oeil()`, `PAUPIERE_SORTIE`) et un dictionnaire
`ANIM` de réglages, puis un module `scripts/animations_<modele>.py` de quelques lignes.
Jeu d'animations retenu par l'utilisateur pour un gardien : **Marche, Course, Sommeil, CoupDeCroc**.

## Import dans Roblox (à rappeler à l'utilisateur)

1. Importer `<nom>_rig.fbx` (modèle + os) avec l'importeur 3D de Studio.
2. Animation Editor → `…` → Import → *From FBX Animation* → un fichier `<nom>_<Animation>.fbx` à la fois ;
   cocher la boucle pour les animations en boucle ; publier pour obtenir les ID.
3. Mettre `roblox/Gardien_Animations.server.lua` (commun à tous les gardiens) dans le modèle, coller les ID et
   régler les vitesses nominales du modèle en haut du script. Iris : `Material = Neon`.
Ce circuit n'a pas encore été testé de bout en bout dans Studio : le dire, et demander une capture en cas de souci.
