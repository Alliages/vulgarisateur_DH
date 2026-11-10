# Bienvenue sur « Météo et Chaleur »

Chaque étude thermique d'un bâtiment repose sur un fichier météo. C'est souvent **l'hypothèse qui pèse le plus sur les résultats**, et pourtant on la regarde rarement.

Cet outil sert à **ouvrir ces fichiers, les comprendre et les comparer**. Il s'adresse aux professionnels du bâtiment, sans besoin d'être thermicien.

## À quoi sert l'outil

- Voir si un fichier météo est chaud ou non, avec des indicateurs simples (**degrés-heures**, **nuits chaudes**, journées et semaines les plus chaudes).
- Comparer deux fichiers, par exemple le fichier réglementaire RE2020 et l'été 2026 réellement mesuré.

## Trois notions pour bien lire les résultats

> **Un fichier météo, c'est 8760 heures.** Une année compte 8760 heures. Un fichier météo est donc un tableau de 8760 lignes, avec la température, l'ensoleillement, l'humidité, le vent…

> **Météo ou climat ?** La météo, c'est le temps qu'il a fait une année donnée, à un endroit précis. Le climat, c'est la tendance sur une longue période. Un fichier météo peut être une vraie année mesurée, une moyenne de plusieurs années ou une année reconstruite. En RE2020, un fichier représente une année moyenne (mesures Météo-France de 2000 à 2018) pour les consommations. Pour le confort d'été, on y insère une séquence caniculaire.

> **Les degrés-heures (DH).** Chaque heure, on mesure de combien la température dépasse un seuil, puis on additionne sur l'année. Dans la RE2020, le seuil varie entre **26 et 28 °C** et le calcul porte sur la température intérieure du bâtiment. Ici, on applique ce calcul aux températures horaires du fichier choisi. Avec un fichier météo, le résultat décrit donc la chaleur de la météo. On peut aussi importer ses propres températures, par exemple celles d'un bâtiment simulé.

Pour aller plus loin, l'onglet **Méthode & sources** détaille les calculs, les hypothèses et leurs sources.

<!-- bouton_methode -->

## Les données

L'outil propose des fichiers météo classés par **zone climatique RE2020**. L'onglet **Observations** contient des relevés Météo-France de 20 stations, du 1er mai au 30 septembre 2026. Le bouton « Importer » de la fenêtre de choix charge votre propre fichier, et de nouveaux fichiers peuvent être déposés sur le dépôt GitHub.

<h2 class="alerte">Limites</h2>

- **L'outil n'est pas une étude thermique.** Il aide à comprendre les données qui en sont le point de départ.
- Les fichiers proposés par l'outil sont uniquement des fichiers météo.

<h2 class="liens">Liens utiles</h2>

- [Carte des zones climatiques RE2020](https://alliages.github.io/zones-climatiques-re2020/)
- [Les 6 seuils de la RE2020](https://seuils-re2020.streamlit.app/)
- [Wiki des données météo](https://github.com/Alliages/meteo/wiki/WIKI-Donn%C3%A9es-M%C3%A9t%C3%A9o)
- [Fichiers météo officiels de la RE2020](https://rt-re-batiment.developpement-durable.gouv.fr/documents-complementaires-a706.html)
- [Code de l'outil](https://github.com/Alliages/vulgarisateur_DH)
