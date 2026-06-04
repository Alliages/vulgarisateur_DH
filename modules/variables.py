# ============================================================
# VARIABLES ET PARAMÈTRES DU CALCULATEUR DH RE2020
# ============================================================
# Ce fichier contient toutes les constantes utilisées dans
# le calcul des Degrés-Heures (DH) d'inconfort thermique,
# indicateur de la réglementation thermique française RE2020.
# ============================================================

# ============================================================
# PARAMÈTRES DES COURBES DE TEMPÉRATURE
# ============================================================

# Heure du minimum de température journalier (fixé à 5h dans l'Excel)
H_MIN = 5  # heure

# Options d'heure de pic disponibles dans l'interface
# DOUTE DE TRANSCRIPTION :
#   L'option "13h" dans l'interface Excel correspond à H_pic = 12
#   dans les formules (le maximum se produit à l'heure 12).
#   C'est cohérent avec les données vérifiées : T_max à h=12 pour "13h lin/smooth".
#   L'option "15h" est directement cohérente : H_pic = 15.
#   Hypothèse : la convention "13h" désigne la 13e période horaire,
#   qui débute à 12h00.
H_PIC_OPTIONS = {
    "13h": 12,   # Pic réel à l'heure 12 (vérif. données Excel)
    "15h": 15    # Pic réel à l'heure 15
}

# Types de courbes de température disponibles
TYPES_COURBES = {
    "Lissé":     "smooth",  # Interpolation sinusoïdale (plus réaliste)
    "Brut":      "lin",     # Interpolation linéaire (droite entre les points)
    "Aléatoire": "rand"     # Moyenne lin+smooth avec perturbation aléatoire
}

# Amplitude maximale de la perturbation aléatoire
# (fraction de l'amplitude thermique journalière)
# Ex : 0.08 → perturbation max = ±8% de (T_max - T_min)
# DOUTE : L'Excel utilise RAND() recalculé, sans amplitude définie explicitement.
#         La valeur 0.08 est une approximation raisonnable.
AMPLITUDE_ALEATOIRE = 0.08

# ============================================================
# SEUILS DH SELON RE2020 (°C)
# ============================================================

SEUIL_NUIT = 26.0  # Seuil de confort nocturne (°C)
SEUIL_JOUR = 28.0  # Seuil de confort diurne (°C)

# Heures avec seuil NOCTURNE (26°C) — vérifiées sur les données Excel
# Heures 0h-5h et 23h → seuil = 26°C
HEURES_SEUIL_NUIT = list(range(0, 6)) + [23]   # [0, 1, 2, 3, 4, 5, 23]

# Heures avec seuil DIURNE (28°C)
# Heures 6h-22h (inclus) → seuil = 28°C
HEURES_SEUIL_JOUR = list(range(6, 23))          # [6, 7, ..., 22]

# ============================================================
# PLANNING D'OCCUPATION (LOGEMENT — RE2020)
# ============================================================
# Déduit des données Excel : colonne "DH occ" = NaN pour heures 10h-16h
# → Ces heures sont non-occupées (occupants au travail/école).
# DOUTE : Ce planning est lu dans l'Excel mais non explicitement documenté.
#         À confirmer avec le texte réglementaire RE2020.

# Heures occupées : nuit + matin (0h-9h) et soirée (17h-23h)
HEURES_OCCUPATION = list(range(0, 10)) + list(range(17, 24))  # 17 heures

# Heures non-occupées : journée de travail (10h-16h)
HEURES_NON_OCCUPATION = list(range(10, 17))  # 7 heures

# ============================================================
# DÉCOUPAGE JOUR / NUIT POUR LES MÉTRIQUES DH
# ============================================================
# Vérification sur les données Excel :
#   DH jour (6h-21h) = 110.98 °C.h ✓
#   DH nuit (0h-5h + 22h-23h) = 7.19 °C.h ✓

HEURES_PERIODE_JOUR = list(range(6, 22))          # 6h à 21h inclus
HEURES_PERIODE_NUIT = list(range(0, 6)) + [22, 23]  # 0h-5h + 22h + 23h

# ============================================================
# JOURS DE LA SEMAINE
# ============================================================
JOURS_SEMAINE = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']

# ============================================================
# VALEURS PAR DÉFAUT — ONGLET JOURNÉE
# (reproduites depuis l'interface Excel)
# ============================================================
DEFAUT_H_PIC          = "15h"
DEFAUT_TYPE_COURBE    = "Lissé"
DEFAUT_ALEATOIRE      = False
DEFAUT_T_MINUIT       = 27.0   # °C - Température à minuit
DEFAUT_T_PIC_BAS      = 22.0   # °C - Température minimale (pic bas, atteinte à 5h)
DEFAUT_T_PIC_HAUT     = 39.0   # °C - Température maximale (pic haut)

# ============================================================
# VALEURS PAR DÉFAUT — ONGLET SEMAINE
# (reproduites depuis l'interface Excel d'origine)
# Format : [T_minuit, T_pic_haut, T_pic_bas]
# ============================================================
DEFAUT_SEMAINE = [
    [21, 32, 20],  # Lundi
    [24, 36, 20],  # Mardi
    [25, 37, 21],  # Mercredi
    [26, 38, 24],  # Jeudi
    [26, 36, 22],  # Vendredi
    [25, 32, 21],  # Samedi
    [25, 31, 23],  # Dimanche
]
DEFAUT_H_PIC_SEMAINE       = "15h"
DEFAUT_TYPE_SEMAINE        = "Lissé"
DEFAUT_ALEATOIRE_SEMAINE   = True   # L'Excel utilise aléatoire=oui pour la semaine

# ============================================================
# COULEURS POUR LES GRAPHIQUES PLOTLY
# ============================================================
COULEUR_TEMPERATURE     = '#E63946'  # Rouge vif — courbe de température
COULEUR_SEUIL_26        = '#457B9D'  # Bleu moyen — seuil 26°C
COULEUR_SEUIL_28        = '#1D3557'  # Bleu foncé — seuil 28°C
COULEUR_DH_OCCUPE       = 'rgba(76, 175, 80, 0.4)'    # Vert transparent — DH en occupation
COULEUR_DH_NON_OCCUPE   = 'rgba(255, 152, 0, 0.4)'   # Orange transparent — DH hors occupation
COULEUR_FOND_NUIT       = 'rgba(200, 220, 255, 0.15)' # Bleu très clair — fond période nuit
