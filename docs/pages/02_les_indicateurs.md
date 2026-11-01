# Les indicateurs
DH : somme, heure par heure, de max(0 ; T − seuil) sur les heures retenues.

Méthode RE2020 : seuil de [[hyp:seuil_nuit_dh]] °C la nuit ; le jour, 0,33 × (température fichier lissée) + 20,8 limité entre [[hyp:seuil_nuit_dh]] et [[hyp:seuil_jour_max]] °C ; DH comptés seulement pendant la période de confort adaptatif (température fichier lissée ≥ [[hyp:seuil_periode_adaptative]] °C).

Méthode basic : [[hyp:seuil_nuit_dh]] °C la nuit, [[hyp:seuil_jour_max]] °C le jour, toute l'année.

Journée la plus chaude : critère au choix, température moyenne ou maximale.

Semaine la plus chaude : critère au choix, moyenne des températures moyennes, moyenne des maximales, ou pointe maximale (semaine centrée sur le jour de la pointe).

Nouveaux indicateurs : heures au-dessus de [[hyp:seuil_heures_chaudes]] °C, plus longue suite de nuits tropicales, température moyenne et température moyenne nocturne de l'été.

Les valeurs sont arrondies à l'unité à l'écran et exactes à l'export.

L'ordre des cartes se choisit dans le menu de gauche (« Indicateurs affichés ») ; l'ordre par défaut et le nombre de chiffres après la virgule (colonne « decimales ») viennent de hypotheses.xlsx.
