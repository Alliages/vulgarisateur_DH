# Journal des versions — Météo et Chaleur

Règle : `0.8.x` tant que l'outil ne fonctionne pas bien, `0.9.0` quand il commence à bien fonctionner.
Dernier chiffre **pair** = gros changement, **impair** = correction.

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
