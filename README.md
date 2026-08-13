# OnePieceDle

Jeu de devinette quotidien inspiré des jeux « -dle » : trouver le personnage de One Piece
mystère à partir d'indices colorés. Implémentation maison, 100 % statique
(HTML/CSS/JS, aucune dépendance, aucun build).

## Lancer

```bash
cd ~/onepiecedle
python3 -m http.server 8080
# puis http://localhost:8080
```

Ou simplement ouvrir `index.html` dans le navigateur.

## Contenu

- **470 personnages** : liste définitive triée à la main, une ligne par nom dans
  `tools/selection.txt`. C'est le seul filtre du dataset — ajouter ou retirer un nom
  dans ce fichier puis relancer `tools/rebuild.py` suffit à faire évoluer le roster.
- **3 modes** : Classique, Emoji (le personnage résumé en emojis) et Prime (retrouver
  le porteur d'une prime).
- **Portraits** pour les 470 personnages, dans l'autocomplétion et la colonne « Personnage ».
- **Défi du jour**, avec rejeu des **6 jours précédents** : un personnage par mode et
  par jour, le même pour tout le monde, tiré d'un hash de la date. Chaque jour garde sa
  propre progression ; seules les parties du jour même comptent dans les statistiques.
- **Progression sauvegardée** : les essais du jour sont conservés par mode en
  `localStorage`. Un rechargement restaure le plateau tel quel (et l'écran de résultat
  si tu as déjà trouvé) ; tout repart à zéro au changement de date.
- Autocomplétion avec alias/surnoms (`luffy`, `akainu`, `barbe noire`, `mr 2`…),
  navigation clavier, indices progressifs, statistiques et série en `localStorage`,
  partage du résultat en grille d'emojis.

## Colonnes comparées

Vert = exact, jaune = partiel, rouge = faux.

Le jaune (« pas loin ») ne s'applique qu'à la prime, la taille, le Haki et la saga :
sur l'affiliation, deux équipages de pirates sans rapport ressortaient en jaune,
ce qui induisait en erreur.

| Colonne | Vert | Jaune |
|---|---|---|
| Genre | identique | — |
| Affiliation | même équipage | *(pas de correspondance partielle)* |
| Fruit du Démon | même type | même famille Zoan, ou deux fruits différents |
| Haki (💪 noirci = Armement, 👁️ Observation, 👑 Rois) | mêmes types | au moins un type en commun |
| Prime | identique | écart ≤ 20 % |
| Taille | identique | écart ≤ 15 cm |
| 1re apparition | même saga | saga adjacente |

Les flèches ⬆ / ⬇ indiquent si la valeur cherchée est plus grande ou plus petite.

## Source des données

Les primes, tailles, types de Fruit du Démon et origines ont été extraits des infobox
(`Char box`) de **One Piece Encyclopédie** via son API MediaWiki, puis comparés fiche
par fiche à la base :

- 35 primes corrigées ou complétées, 170 tailles, 15 types de fruit, 102 origines ;
- les Marines et agents notés en étoiles/couronnes sur le wiki sont convertis selon la
  règle **1 étoile = 100 M, 1 couronne = 1 Md** (8 personnages). La conversion recoupe
  la valeur chiffrée du wiki pour 7 d'entre eux ; seul Sakazuki diverge (4 couronnes
  = 4 Md par la règle, alors que sa fiche indique 5 Md entre parenthèses) ;
- les primes barrées (révoquées) sont ignorées au profit de la prime courante ;
- seule exception assumée au wiki : **Luffy** est classé « Zoan Mythique » (canon depuis
  le chapitre 1044) alors que l'infobox fr indique encore « Paramecia ».
- `js/wikilinks.js` associe chaque personnage au titre de sa fiche ; les 238 titres ont
  été vérifiés via l'API (aucun lien mort, redirections résolues). L'écran de fin
  affiche un lien vers la fiche.

Les orthographes du wiki sont acceptées en saisie : `Kaidou`, `Ener`, `Nefertari Vivi`,
`Edward Newgate`, `Don Quichotte Doflamingo`, `Aramaki`…

Le texte du wiki est sous licence CC BY-SA ; le crédit figure en pied de page.

## Images

Les portraits vivent dans `img/`, nommés d'après le slug du personnage
(`monkey-d-luffy.png`), et sont listés dans `img/manifest.json`. Le jeu les charge en
`lazy` : seuls les personnages proposés déclenchent un téléchargement.

Pour réimporter un lot d'images depuis un dossier dont les fichiers portent le nom des
personnages :

```bash
python3 tools/import-images.py "Images One Piece"
```

Le script fait la correspondance via les noms, les alias du jeu et les titres du wiki
(`Imu.webp` → Im, `inazuma.jpg` → Inazuma), renomme en slug, régénère le manifeste et
signale les personnages sans image comme les fichiers non rattachés.

`tools/build-manifest.sh` régénère seulement le manifeste, si tu déposes des fichiers
déjà nommés en slug dans `img/`.

Sans aucune image, le jeu reste jouable : les personnages s'affichent avec un aplat
coloré portant leur initiale.

**Droits** : les portraits fournis dans ce dépôt proviennent de l'œuvre de
Eiichiro Oda / Shueisha / Toei. Ils sont utilisés ici dans un projet de fan strictement
personnel et non diffusé. Leur redistribution ou une mise en ligne publique n'est pas
couverte par la licence CC BY-SA du wiki, qui ne porte que sur le texte.

## Deux pools distincts

Le wiki recense ~1900 personnages canon, mais la grande majorité sont des figurants
sans aucune donnée publiée : ni prime, ni taille, ni Haki, ni fruit. Les tirer comme
personnage du jour donnerait une grille de « ? » impossible à résoudre.

D'où la séparation :

- **proposables** : les 1893, tous saisissables et présents dans l'autocomplétion ;
- **cibles possibles** : ceux qui ont un indice emoji ou au moins 2 champs renseignés,
  soit 340 en Classique, 236 en Emoji, 118 en Prime.

Le seuil est la propriété `estCible`, en haut de `js/game.js` — un chiffre à changer
si tu veux élargir ou resserrer.

## Régénérer la base depuis le wiki

```bash
python3 tools/list_cats.py   # énumère les catégories de personnages
python3 tools/harvest.py     # récupère les infobox (~1900 pages, en cache)
python3 tools/rebuild.py     # reconstruit js/characters.js
python3 tools/build-list.py  # régénère PERSONNAGES.txt
```

`js/characters.js` est entièrement généré. Les indices emoji, écrits à la main, vivent
dans `js/emoji.js` : une régénération ne les touche pas.

## Éditer les personnages

Tout est dans `js/characters.js`, une ligne par personnage :

```js
[ nom, genre, equipage, camp, fruit, haki, prime, taille, origine, saga, emoji ]
```

- `genre` : `M` / `F` / `?`
- `camp` : Pirate, Marine, Gouvernement, Revolutionnaire, Samourai, Civil, Geant, Autre
- `fruit` : Aucun, Paramecia, Logia, Zoan, Zoan Ancestral, Zoan Mythique
- `haki` : combinaison de `A` (Armement), `O` (Observation), `R` (Rois) — `""` si aucun
- `prime` : en berries, `0` = aucune, `-1` = inconnue
- `taille` : en cm, `-1` = inconnue
- `saga` : une valeur du tableau `SAGAS`

`origine` : East Blue, West Blue, North Blue, South Blue, Grand Line, Wano,
Ile des Hommes-Poissons, Ciel, Elbaf, Calm Belt, Terre Sainte de Mary Joa, Inconnue —
la taxonomie du wiki, qui ne distingue pas le Nouveau Monde de Grand Line.

Les primes et tailles non révélées dans l'œuvre restent à `-1` (affichées « ? ») :
99 personnages ont une prime connue, 217 une taille connue.

## Note

Projet de fan non officiel, sans aucun asset issu du site original ni de l'œuvre :
uniquement du code maison et des données factuelles (noms, affiliations, primes),
créditées à One Piece Encyclopédie.
One Piece est une œuvre d'Eiichiro Oda / Shueisha.
