# Journal des versions — Météo et Chaleur

Règle : `0.8.x` tant que l'outil ne fonctionnait pas bien, `0.9.x` depuis qu'il approche d'une version finale.
Dernier chiffre **pair** = gros changement, **impair** = correction.

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
