# Fichiers météo et catalogue
Les fichiers enregistrés sont rangés par zone climatique dans donnees/meteo/ et décrits dans config/catalogue_fichiers.csv.

Les fichiers RE2020 sont des années types en heure UTC ; les relevés sont en heure légale.

Un relevé de moins d'un an permet le DH basic, pas le DH RE2020 (la moyenne glissante a besoin de l'année).

Le menu de gauche montre le fichier en cours et ses fichiers récents. Le bouton « Changer de fichier » ouvre la fenêtre de choix : une recherche dans toutes les familles ; les familles en onglets (RE2020, Relevés, TRACC à venir, Importés) ; pour RE2020, les 8 zones placées comme sur la carte de France, avec une barre qui donne la sévérité du climat (DH du fichier « Th-D canicule », réglage RE2020) ; puis les fichiers de la zone, chacun avec son usage et trois chiffres clés (DH, nuits ≥ 20 °C, T max). L'import d'un fichier se fait dans la même fenêtre (« + Importer »). La même fenêtre choisit le second fichier de l'onglet Comparer.

La famille de chaque fichier est la colonne « famille » de config/catalogue_fichiers.csv.
