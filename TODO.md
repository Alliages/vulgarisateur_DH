# « Météo et Chaleur » — liste des choses à faire

Base : version 0.8.0 (locale, non publiée). **Rien n'est lancé tant que Guigui ne dit pas « lance » / « go ».**
Numéro de la prochaine version : à demander à Guigui avant de lancer.

## Retours du 24/10/2026 — FAITS (restés en 0.8.0, à la demande de Guigui)

### Onglet ANALYSER
| # | Demande | État |
|---|---|---|
| A1 | Menu de gauche replié impossible à rappeler | ✅ seul la barre d'outils Streamlit est masquée, le bouton de rappel reste |
| A2 | Moyenne journalière + variation min-max en rouge clair | ✅ |
| A3 | Tmax et nuit la plus chaude, point + valeur | ✅ (heure affichée en heure légale) |
| A4 | Pas de lignes horizontales sur semaine / journée | ✅ |
| A5 | Date complète dans le titre | ✅ |
| A6 | Axe DH jaune foncé | ✅ |
| A7 | Jours de la semaine + heures d'absence RE2020 | ✅ bandes grises (scénario provisoire) |
| A8 | DH de la période dans le titre | ✅ |
| A9 | Remplacer « θrm » | ✅ « température extérieure lissée » |
| A10 | Heures > 28 °C | ✅ seuil dans hypotheses.xlsx |
| A11 | Nuits tropicales consécutives (max) | ✅ |
| A12 | Température moyenne | ✅ hypothèse prise : été 1/06-30/09 (toute la série si pas d'été) — à valider |
| A13 | Température moyenne nocturne | ✅ idem, nuits 22h-6h — à valider |
| A14 | Retirer DH semaine / jour des cartes | ✅ actif = 0 |
| A15 | Lien « Méthode & sources » inactif | ✅ bouton qui ouvre l'onglet |

### Onglet COMPARER
| # | Demande | État |
|---|---|---|
| C1 | Été superposé plus haut | ✅ |
| C2 | Noms des fichiers à la place de A / B | ✅ |
| C3 | « B − A » pas clair | ✅ « Écart — H3 … par rapport à H1a … » |
| C4 | Supprimer la colonne barres | ✅ |
| C5 | Maximums dans l'été superposé | ✅ |

### Style (image de référence H1a Trappes) : ✅ titre + sous-titre, légende claire, annotations, aire d'écart,
mois en gras, source en pied, axes noirs fléchés.

## Fichiers météo — Observations (03/11/2026)
- [x] 15 stations Météo-France 2026 (01/05–30/09, UTC), dont Trappes et Paris-Montsouris, intégrées en 0.9.9.

## Fenêtre de choix en carte (0.9.10)
- [ ] **TRACC** : même carte + liste ; rien à coder, il suffit d'inscrire les fichiers au catalogue (famille TRACC,
  zone, département, et si possible latitude / longitude).
- [ ] Coordonnées à compléter (colonnes `latitude`, `longitude`) : Paris-Montsouris, Roubaix, Lille-Lesquin,
  Lyon Tête d'Or, Angers ville, Nantes ville, Bordeaux-Paulin (placées pour l'instant au centre du département).

## Points ouverts
- Heure des maximums : affichée en heure légale (16 h) ; l'image de référence est en UTC (14 h). À trancher.
- Bandeau des hypothèses : passe sur deux lignes sur écran moyen.
- Tableau de l'onglet Créer : décimales avec un point (limite du tableau éditable Streamlit).

## Rappels permanents
- Occupation logement : hypothèse CEREMA provisoire, à vérifier par Guigui.
- Source du seuil de nuit à 24 °C : à trouver.
- Liste des fichiers par zone : plus tard.
- Pas encore fait depuis 0.8.0 : boîte aux lettres GitHub + Actions, import multi-séries / zip, version anglaise.
