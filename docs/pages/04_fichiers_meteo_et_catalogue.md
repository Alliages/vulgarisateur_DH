# Fichiers météo et catalogue
Les fichiers enregistrés sont rangés par zone climatique dans donnees/meteo/ et décrits dans config/catalogue_fichiers.csv.

Les fichiers RE2020 sont des années types en heure UTC ; les relevés sont en heure légale.

Un relevé de moins d'un an permet le DH basic, pas le DH RE2020 (la moyenne glissante a besoin de l'année).

Dans le menu de gauche, les fichiers sont classés par famille : RE2020 (années types réglementaires), TRACC (trajectoire de réchauffement de référence, à venir), Relevés (mesures datées), puis Importés (fichiers chargés pendant la session). On choisit la famille, puis la zone, puis le fichier ; la case de recherche cherche dans toutes les familles.

La famille de chaque fichier est la colonne « famille » de config/catalogue_fichiers.csv.
