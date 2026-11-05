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
- [x] **TRACC** : 48 fichiers au catalogue (0.9.12), produits par `outils/convertir_tracc.py`.
- [ ] TRACC : vérifier à la source les maxima au-dessus de 46 °C (Rennes 54,8 et 49,2 ; Tours 53,7 ; Nancy 46,9) et
  la longitude de Carpentras (5,216 dans les fichiers, celle de Marignane).
- [x] Coordonnées des 20 observations (synthèse Météo-France du 03/11/2026).
- [ ] Emplacement à confirmer (déduit dans la synthèse) : Agen, Carpentras, Nancy-Essey, Tours, Trappes.
- [ ] Clermont-Ferrand, Montpellier, Perpignan, Toulouse : pas de poste de centre-ville ; l'aéroport sous-estime
  la chaleur urbaine (surtout la nuit). À signaler dans l'outil ?

## Indicateur « sévérité cumulée des vagues de chaleur » (04/11/2026, sans changement de version)
Méthode Météo-France (Soubeyroux et al. 2016) à la station : Tm = (TN+TX)/2, toute l'année ;
Spic / Sdeb / Sint = centiles 99,5 / 97,5 / 95 sur 1991-2020 ; vague = au moins un jour ≥ Spic,
du premier au dernier jour ≥ Sdeb, arrêt après 1 jour < Sint ou 3 jours < Sdeb, durée ≥ 3 jours ;
sévérité = Σ max(0 ; Tm − Sdeb) ; cumul = somme des vagues. Hypothèses vdc_* dans hypotheses.xlsx.
- [x] 8 stations de référence (stations des fichiers RE2020 du catalogue) dans hypotheses.xlsx, onglet
  « stations_vague_chaleur ».
- [x] GitHub Action « Seuils vagues de chaleur » (lancement à la main) + outils/calculer_seuils_vdc.py.
  Erreurs de téléchargement : 3 essais si passagères, puis message (URL, cause, piste de correction)
  en annotation rouge et dans le tableau récapitulatif du run.
- [ ] Lancer l'Action (feu vert de Guigui) et relire le journal (complétude, contrôle été 2003).
- [x] Plugins d'indicateur `vdc_severite` (**somme des sévérités de toutes les vagues du fichier, °C·j**) et
  `vdc_nombre` (**nombre de vagues**, détail : jours de vague et plus longue vague) ; calcul dans
  calcul/vagues_chaleur.py. Seuils des 8 stations calculés par l'Action (config/seuils_vague_chaleur.csv). Fichiers concernés : RE2020 et TRACC (station de la zone) et observations de la même
  station (numéro de poste) ; les autres restent à « — ».
- [ ] À vérifier avec l'étude EODD : les jours sous Sdeb en fin de vague ne sont pas comptés dans la durée
  (sa figure semble les compter) ; sans effet sur la sévérité ni le nombre de vagues.
- [ ] Variante sans le 10/07-31/08 (bâtiments scolaires, étude EODD) : calcul prêt (`hors_periode`), pas encore
  affichée (réglage à ajouter).
- [ ] **Autres fichiers** (observations, TRACC, fichiers importés) : seuils de leur propre station à calculer ;
  en attendant, pas d'indicateur (ou zone demandée à l'utilisateur).
- [ ] Analyse des résultats : comparer avec l'étude EODD (G. Le Gall, durée cumulée 2026 record sauf altitude)
  et tester la critique du fichier RE2020 « 2003 » (Bretagne, Manche).

## Points ouverts
- Heure des maximums : affichée en heure légale (16 h) ; l'image de référence est en UTC (14 h). À trancher.
- Bandeau des hypothèses : passe sur deux lignes sur écran moyen.
- Tableau de l'onglet Créer : décimales avec un point (limite du tableau éditable Streamlit).

## Rappels permanents
- Occupation logement : hypothèse CEREMA provisoire, à vérifier par Guigui.
- Source du seuil de nuit à 24 °C : à trouver.
- Liste des fichiers par zone : plus tard.
- Pas encore fait depuis 0.8.0 : boîte aux lettres GitHub + Actions, import multi-séries / zip, version anglaise.
