# Journal des versions — Météo et Chaleur

Règle : `0.8.x` tant que l'outil ne fonctionnait pas bien, `0.9.x` depuis qu'il approche d'une version finale.
Dernier chiffre **pair** = gros changement, **impair** = correction.

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
