# Fichiers météo et catalogue
Les fichiers enregistrés sont rangés par zone climatique dans donnees/meteo/ et décrits dans config/catalogue_fichiers.csv.

Les fichiers RE2020 sont des années types en heure UTC ; les observations Météo-France (1er mai – 30 septembre 2026) sont aussi en heure UTC.

Un relevé de moins d'un an permet le DH basic, pas le DH RE2020 (la moyenne glissante a besoin de l'année).

Le menu de gauche montre le fichier en cours et ses fichiers récents. Le bouton « Changer de fichier » ouvre la fenêtre de choix : une recherche dans toutes les familles ; les familles en onglets (RE2020, Observations, TRACC à venir, Importés). Pour chaque famille, une mini carte de France montre les zones climatiques, teintées du vert au corail selon le DH du fichier « Th-D canicule » de la zone (réglage RE2020), avec le nombre de fichiers de chaque zone et un point par station ; à côté, les fichiers sont listés par zone avec leur DH (barre et chiffre) et leurs nuits ≥ 20 °C. Un clic sur une zone ne garde qu'elle dans la liste ; un nouveau clic, ou « Toutes les zones », revient à toutes. Un clic sur un fichier le choisit. L'import d'un fichier se fait dans la même fenêtre (« + Importer »). La même fenêtre choisit le second fichier de l'onglet Comparer.

La famille de chaque fichier est la colonne « famille » de config/catalogue_fichiers.csv.

Trois colonnes facultatives placent la station sur la carte : « latitude » et « longitude » (degrés décimaux), sinon « departement » (numéro du département : le point est mis en son centre), sinon le centre de la zone.
