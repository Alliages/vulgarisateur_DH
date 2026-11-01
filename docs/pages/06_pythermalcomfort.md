# pythermalcomfort
Depuis la version 0.9.8, l'outil n'a plus besoin de la librairie libre pythermalcomfort (licence MIT) pour fonctionner : la droite de confort adaptatif (0,33 × température fichier lissée + 18,8 + 2 °C) tient en une ligne, écrite dans l'outil, et charger la librairie retardait d'environ 11 secondes le démarrage de l'outil en ligne. pythermalcomfort reste la référence : un test automatique vérifie que la formule de l'outil donne les mêmes valeurs que la librairie.

Les spécificités RE2020 (moyenne glissante récursive, période température fichier lissée ≥ 16 °C, plafonds, occupation) restent dans le code de l'outil.
