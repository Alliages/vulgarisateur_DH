# Journal des versions — Météo et Chaleur

Règle : `0.8.x` tant que l'outil ne fonctionnait pas bien, `0.9.x` depuis qu'il approche d'une version finale.
Dernier chiffre **pair** = gros changement, **impair** = correction.

## 0.9.12 — version de test (04/11/2026), fichiers TRACC

- **48 fichiers TRACC** au catalogue : 8 zones × +2, +2,7 et +4 °C, avec ou sans vague de chaleur
  (`donnees/meteo/TRACC/<zone>/tracc_plus2_0.csv` … `tracc_plus4_0_vdc.csv`), format `heure;T` en UTC, température à 2 m.
- `outils/convertir_tracc.py` les produit depuis le dossier `TRACC/` (non publié, ajouté au `.gitignore`).
- Valeurs de la source non corrigées : maxima au-dessus de 46 °C signalés dans la description de 4 fichiers.
  Coordonnées reprises des lignes RE2020 (longitude de Carpentras fausse dans la source).

## 0.9.11 — correction (04/11/2026), onglet Accueil et favicon

- Nouvel onglet **Accueil**, ouvert au démarrage : à quoi sert l'outil, trois notions (8760 heures, météo ou
  climat, degrés-heures), les données, les limites et les liens utiles (carte des zones climatiques, wiki des
  données météo, fichiers RE2020 officiels, code). Bouton vers l'onglet Méthode & sources.
- Texte dans `docs/accueil.md` (modifiable sans toucher au code) ; affichage `interface/onglet_accueil.py` ;
  titres sur fond coloré et notions en encadrés caramel (`interface/style.css`). Pas de nom de fichier dans le
  haut de page de l'Accueil, aucun calcul lancé.
- **Favicon** : le logo de l'en-tête (onde blanche sur rond indigo) remplace le soleil ☀
  (`interface/favicon.png`, source `interface/favicon.svg`).
- Test de l'interface : le DH de référence est vérifié dans l'onglet Analyser (l'app s'ouvre sur l'Accueil).

## 0.9.10 — version de test (03/11/2026), fenêtre de choix en carte

**Fenêtre « Changer de fichier »**, pour toutes les familles du catalogue (RE2020, Observations, puis TRACC) :
- mini carte de France des zones climatiques, teintées du vert au corail selon le DH du fichier « Th-D canicule »
  de la zone (réglage RE2020) ; étiquette « zone · nombre de fichiers » ; un point par station ;
- clic sur une zone (étiquette ou département) : la liste ne garde que cette zone ; nouveau clic ou
  « ✕ Toutes les zones » : tout revoir ;
- fichiers listés par zone : nom, barre et chiffre du DH, nuits ≥ 20 °C ; clic = fichier choisi ;
- barres de DH sur une échelle commune (0 à 3 300 °C.h, `DH_ECHELLE_CHOIX`), dégradé vert → caramel → corail
  (nouvelle couleur `VERT` dans la charte) ; légende discrète.
- Pastilles « zone · n » légèrement transparentes, placées automatiquement dans leur zone sans recouvrir un point
  ni une autre pastille (au plus près de leur place habituelle).
- Remplace la grille schématique des zones RE2020 et les cartes de fichiers (gardées pour la recherche et les
  fichiers importés). Composant `interface/carte_zones.py` (`st.components.v2`).

**Catalogue** : colonnes facultatives `departement`, `latitude`, `longitude` (position du point ; à défaut,
centre du département puis de la zone). Coordonnées renseignées pour les 8 stations de la carte
zones-climatiques-re2020 ; département renseigné pour tous les fichiers.

**Observations** (20 stations) :
- 5 stations ajoutées : Strasbourg-Botanique (centre-ville, H1b), Clermont-Ferrand (aéroport, H1c),
  Toulouse-Blagnac (aéroport, H2c), Montpellier et Perpignan (aéroport, H3).
- Noms clairs « Station (emplacement) » : ville, centre-ville, périphérie, aéroport ou aérodrome ; nouvelle colonne
  `emplacement` ; fichiers et identifiants renommés en conséquence (ex. `lille_lesquin_aeroport_2026.csv`).
- Coordonnées, altitude, emplacement et distance au centre-ville de toutes les stations repris de la synthèse
  Météo-France du 03/11/2026 (description du fichier).

## 0.9.9 — correction (03/11/2026), fichiers météo

- Famille « Relevés » renommée **« Observations »** ; dossier `donnees/meteo/Observations/`.
- 15 observations ajoutées, 1er mai – 30 septembre 2026, horaires, Météo-France, heure UTC, au moins une par
  zone : **Trappes**, **Paris-Montsouris**, Roubaix, Lille-Lesquin (H1a), Nancy-Essey (H1b), Lyon Tête d'Or,
  Mâcon (H1c), Rennes (H2a), Tours, Angers, Nantes (H2b), Agen, Bordeaux-Paulin (H2c), Carpentras (H2d),
  Marignane (H3). Trappes : température reconstituée du 6/07 7h au 17/07 8h UTC (trou de mesure).
- Onglet Comparer : le haut de page affiche les deux fichiers, chacun dans sa couleur (fichier 1 à gauche,
  second fichier à droite).
- Relevés Trappes et Paris-Montsouris de mai 2026 **retirés du catalogue** : 16 fichiers RE2020 restent.
  Le relevé Trappes reste dans `tests/donnees/` comme jeu de test d'un relevé partiel (tests inchangés).

## 0.9.8 — version de test (01/11/2026), audit du code

Résultats inchangés : les 10 indicateurs des 18 fichiers du catalogue, sous 4 réglages, et les 8 graphiques ont
été comparés avant / après (valeurs, textes, mini-graphiques et graphiques identiques ; non-régression
839,145 °C.h). Seul ajout visible : la bulle « i » des cartes de nuit signale que les heures de nuit (22h-6h)
sont une hypothèse de l'outil.

**Indicateurs « en plugin »**
- Un fichier par indicateur dans `calcul/indicateurs/` (`dh.py`, `nuits_20.py`…), découvert automatiquement ;
  la teinte, l'icône et la carte principale sont déclarées dans le fichier. Modèle commenté : `_modele.py`.
  Marche à suivre dans le README (« Ajouter un indicateur »).
- Le contexte de calcul commun (DH horaire, jours, nuits, journée et semaine les plus chaudes, plus longue suite
  de nuits) est dans `calcul/analyse.py` ; le calcul qui était dans l'interface y a été déplacé.

**Import de fichiers plus sûr**
- Dates `01/06/2026` lues au format français (1er juin), avec un avertissement : elles étaient lues comme le
  6 janvier, sans message.
- Messages clairs en français pour un fichier vide, d'une seule colonne, de longueur inattendue, avec une
  température ou une date illisible (un fichier d'une colonne faisait planter la page).
- Taille limitée à 5 Mo, 5 imports par visite ; nom du fichier nettoyé ; deux imports du même nom ne
  s'écrasent plus.

**Rapidité**
- `pythermalcomfort` n'est plus installé avec l'outil : son chargement retardait d'environ 11 s chaque
  démarrage en ligne. La formule (identique) est dans `calcul/confort_ptc.py` ; la librairie reste la
  référence des tests (`requirements-dev.txt`, `tests/test_confort_ptc.py`).
- Graphiques gardés en mémoire (cache) : un graphique déjà construit se réaffiche en ≈ 15 ms au lieu de
  ≈ 200 ms (annuel, cumul des DH…).
- Les caches se renouvellent quand un CSV de `config/` est régénéré, sans redémarrer l'outil.

**Sécurité, robustesse**
- En ligne, une erreur n'affiche plus la trace Python (chemins du serveur) mais une courte référence ;
  `METEO_DEBUG=1` remet la trace complète en local.
- `.gitignore` complété (`.venv/`, `.env`, `.streamlit/secrets.toml`, paquets Git…).
- Versions de pandas, numpy et openpyxl bornées ; `requirements-dev.txt` pour les tests et la documentation.
- Séries du catalogue partagées entre visiteurs en lecture seule.

**Lisibilité**
- `config/charte.py` : couleurs, police et dimensions (retirées de `config/reglages.py`) ;
  `interface/style.css` : la feuille de style, sortie du code Python.
- `graphiques.py` découpé en `graphiques_communs.py`, `graphiques_analyse.py` et `graphiques_comparaison.py` ;
  cartes d'indicateurs dans `interface/cartes.py` ; menu des réglages dans `interface/menu_reglages.py`.
- Valeurs écrites en dur passées dans `hypotheses.xlsx` : repères 350 / 1 250 °C.h du cumul des DH (statut
  « à préciser » : article de l'arrêté à citer), heures de nuit et période d'été des textes des cartes,
  durée de la semaine de l'onglet Créer.
- Un seul scénario d'occupation (celui de `calcul/dh_re2020.py`) au lieu de deux copies.
- README : lien vers l'outil en ligne, formats d'import, « Ajouter un indicateur », « pythermalcomfort ».

**Tests**
- 57 tests (33 avant) : registre des indicateurs, import de fichiers mal formés, plus longue suite de nuits,
  ouverture de chaque onglet (Streamlit AppTest), référence pythermalcomfort.
- GitHub Actions (`.github/workflows/tests.yml`) : documentation à jour, tests et pip-audit à chaque envoi.

## 0.9.7 — version de test (01/11/2026), corrections

- Graphique de l'année (Analyser) simplifié : plus de bandes ni de points violets, ni d'étiquette « nuit la plus
  chaude » ; les nuits ≥ 20 °C sont des barres bleu clair dans une bande sous les DH (bleu nuit foncé, plus
  hautes, si ≥ 24 °C), étiquetées à gauche. Titre « Températures fichier · <fichier> », sous-titre = les trois
  indicateurs. Axe des DH du jour jusqu'à 300 °C.h (plus si un jour dépasse), graduations de 50.
- Axe des DH de la couleur des barres (caramel) sur tous les graphiques.
- « Température(s) extérieure(s) » devient « température(s) fichier » dans le code et la documentation
  (sauf `calcul/dh_re2020.py`, où le paramètre `t_exterieure` est bien la température extérieure de la
  formule RE2020). L'outil est fait, en base, pour des températures extérieures, mais accepte tout fichier
  horaire, y compris des températures intérieures simulées (README, page « Ce que mesure l'outil »).

## 0.9.5 — version de test (01/11/2026), corrections

- Fenêtre de choix : les tuiles de zone et de fichier sont cliquables sur toute leur surface (le bouton
  transparent n'avait que la largeur de son texte : seule la partie gauche réagissait).
- Menu : retour à la carte du fichier en cours de la 0.9.2 (seul le bouton « Changer de fichier » l'ouvre),
  sans pastille rouge.
- Graphique de l'année (Analyser) : nuits ≥ 20 °C en bandes violettes claires, avec un point au minimum de
  chaque nuit (plus foncé pour les nuits ≥ 24 °C).
- Console Windows : le message sans conséquence « ConnectionResetError [WinError 10054] » (connexion fermée
  par le navigateur) n'est plus affiché.
- **Réglage d'occupation** : à la première ouverture après le démarrage, l'outil pouvait passer en « 24h/24 »
  (DH 1 133 au lieu de 839 pour H1a Th-D) : la mémoire du navigateur relançait la page pendant le premier calcul
  et Streamlit perdait l'état du bouton replié. Le réglage est maintenant gardé à part des boutons (8 premières
  ouvertures sur 8 correctes) ; « Revenir au réglage RE2020 » remet aussi l'affichage des boutons.

## 0.9.4 — version de test (01/11/2026)

- Bouton de repli du menu toujours visible, flèche blanche ; survol de « Réglages » : indigo éclairci.
- Sources retirées sous les graphiques (elles restent dans l'export et l'onglet Méthode & sources).
- Toute la carte du fichier en cours (menu de gauche) ouvre la fenêtre de choix, pas seulement son bouton.
- Pastilles rouges retirées devant le nom du fichier (menu et en-tête).
- Nouveau pied de page : « Indicateurs calculés sur la base de fichiers climatiques - Météo & Chaleur
  version … - Guillaume Meunier - Code Source » (lien vers le dépôt GitHub).
- README réécrit (partie utilisateurs / partie développeurs, schéma, installation sans activation sous
  Windows) avec une capture `docs/capture-accueil.png`.

## 0.9.2 — version de test (01/11/2026)

Retours du 31/10 et du 01/11, avec le style de l'image envoyée (logo en onde, titres de menu en pastilles indigo,
onglets cerclés).

- **Onglet ④ Exporter** (`interface/onglet_exporter.py`, `export/export.py`) : 1 ou 2 fichiers (le 2ᵉ = second
  fichier de Comparer), avec ou sans indicateurs, avec ou sans données horaires ; copier-coller en tableau (Excel,
  Word) ou en texte (mail) ; CSV « Excel français » (indicateurs en tête, 8 760 heures, valeurs au millième) ou
  Excel .xlsx. Réglage, version et sources inscrits. L'export du menu de gauche est retiré.
- **Haut de page fixe** jusqu'au nom du fichier (en-tête, barre des onglets, nom du fichier).
- **Plus rapide** : seul l'onglet ouvert est calculé ; la navigation dans Méthode & sources ne recalcule que la page
  de documentation (fragment).
- Menu : réglages dans une partie repliée par défaut ; titres « Fichier météo » / « Réglages » en pastilles indigo.
- Ordre par défaut des cartes : DH, heures > 28 °C, DH nuit, nuits tropicales, nuits tropicales consécutives,
  nuits ≥ 24 °C, température moyenne, température moyenne nocturne (hypotheses.xlsx).
- Semaine la plus chaude : sans légende (couleurs expliquées dans le sous-titre) ; semaine et journée : axe des DH
  plus bas, barres plus hautes.
- Comparer : **graphique des nuits chaudes, nuit par nuit**, avec la plus longue suite de nuits tropicales encadrée.
- Mémoire du navigateur (`streamlit-extras` local_storage_manager) : dernier fichier, récents, lignes, ordre des cartes.
- Erreurs lisibles : message en français + détail copiable (try/except natif ; l'extra « exception_handler »
  ne fonctionne plus avec Streamlit 1.66).
- Tests : `tests/test_export.py`.
- requirements.txt : Plotly 7.1.0 (Plotly 5.22.0 bloquait l'installation de streamlit-extras, qui exige 5.23 ou plus).

## 0.9.0 — version de test (29/10/2026)

On approche d'une version finale. Validé : fond teinté des cartes, DH par jour sur l'année, heure légale des maximums.

- **Choix du fichier météo dans une fenêtre dédiée** (`interface/choix_fichier.py`) :
  - menu de gauche allégé : carte du fichier en cours, bouton « Changer de fichier », fichiers récents ;
  - recherche dans toutes les familles ; familles en onglets (RE2020, Relevés, TRACC à venir, Importés, + Importer) ;
  - zones RE2020 sur une carte schématique, barre = DH du fichier « Th-D canicule » (réglage RE2020) ;
  - fichiers en cartes cliquables avec usage et 3 chiffres clés (DH, nuits ≥ 20 °C, T max) ;
  - « Analyser ce fichier » / « Comparer avec le fichier en cours » ; la même fenêtre choisit le second fichier de Comparer.
- Créer : « + Comparer comme fichier C » ouvre directement l'onglet Comparer avec le fichier créé.
- Tests : `tests/test_choix_fichier.py` (carte des zones, second fichier par défaut, recherche).

## 0.8.4 — version non fonctionnelle (29/10/2026)

Retours des 24 (soir), 26 et 28 octobre ; style inspiré d'un tableau de bord épuré (cartes blanches arrondies
sur fond gris chaud, carte principale en couleur pleine, mini-graphiques et jauge dans les cartes, pastilles d'écart).

- Graphiques : titre des axes (« °C », « °C.h ») à l'horizontale au-dessus de la graduation la plus haute ;
  dates en français au format long sur tous les axes ; DH de chaque jour en barres jaunes sur l'année.
- Nom du fichier en gros sous la barre des onglets ; « Méthode DH » devient « Seuils d'inconfort pour le DH ».
- Cartes : ordre au choix (menu « Indicateurs affichés »), fond teinté de la couleur de la carte, DH en rouge,
  nuit en foncé, températures moyennes à 1 décimale, mini-graphique par mois, jauge « part des DH la nuit ».
- Comparer : fichier de l'onglet Analyser en corail, second fichier en bleu canard (cartouches, tableau, courbes) ;
  écarts en pastilles ; nuits les plus chaudes annotées ; journée **et** semaine les plus chaudes superposées avec
  traits 20 / 28 °C, fond orangé au-dessus de 28 °C, bleu en dessous de 20 °C.
- Fichiers météo classés par famille (RE2020, TRACC à venir, Relevés, Importés) : famille → zone → fichier.
- Windows : pyarrow figé dans requirements.txt ; l'outil fonctionne sans pyarrow (formulaire simple dans Créer).

## 0.8.0 — version non fonctionnelle (23/10/2026)

- Remplacement de l'ancienne app Dash par l'interface Streamlit « Météo et Chaleur ».
- Onglets Analyser, Comparer, Créer jour / semaine, Méthode & sources.
- 18 fichiers météo : 8 zones × Th-BC et Th-D (RE2020) + relevés Trappes et Paris-Montsouris mai 2026.
- Indicateurs : DH (RE2020 ou basic 26/28, avec ou sans occupation), DH nuit, nuits ≥ 20 °C et ≥ 24 °C,
  journée la plus chaude (T moyenne / T max), semaine la plus chaude (T moyenne / moyenne des T max / pointe T max).
- Droite de confort adaptatif via pythermalcomfort 4.6.2 ; non-régression H1a Th-D = 839,145 °C.h.
- Documentation éditable : `docs/sources/documentation.docx` et `hypotheses.xlsx`, convertis par `outils/convertir_docs.py`.
- Export CSV (série horaire) et Excel (indicateurs, horaire, journalier, hypothèses, réglage).
- Retours du 24/10 intégrés (toujours 0.8.0, à la demande) :
  - menu de gauche à nouveau rappelable une fois replié ; lien « Méthode & sources » actif ;
  - année : moyenne journalière + bande min-max rouge clair + horaire fin, Tmax et nuit la plus chaude annotées ;
  - semaine / journée : date complète et DH de la période dans le titre, jours de la semaine, heures d'absence
    grisées (scénario provisoire), axe DH jaune foncé, pas de lignes horizontales ajoutées ;
  - « θrm » renommé « température extérieure lissée » ;
  - nouveaux indicateurs : heures > 28 °C, nuits tropicales consécutives (max), température moyenne et
    température moyenne nocturne (été 1/06-30/09) ; DH semaine / jour retirés des cartes ;
  - Comparer : noms des fichiers à la place de A / B, colonne « Écart … par rapport à … », colonne barres
    supprimée, été superposé plus haut avec maximums annotés, journées les plus chaudes superposées ;
  - style inspiré du graphique de référence H1a Trappes (titre + sous-titre, source en pied, mois en gras).
- Pas encore fait : boîte aux lettres GitHub et Actions, import multi-séries, version anglaise.
