# ============================================================
# MODULE DE CALCUL — TEMPÉRATURES ET DEGRÉS-HEURES (DH)
# ============================================================
# Implémente les formules vérifiées sur les données de l'Excel
# "Vulgarisation_DH.xlsx" (RE2020).
#
# Formules validées sur les cas :
#   - Journée : T0=27, T_min=22, T_max=39, 15h smooth → DH occ=52.47 ✓
#   - Semaine : T0=21..26 sur 7 jours              → DH=217.12 ✓
# ============================================================

import numpy as np
from modules.variables import (
    H_MIN, H_PIC_OPTIONS, TYPES_COURBES, AMPLITUDE_ALEATOIRE,
    SEUIL_NUIT, SEUIL_JOUR,
    HEURES_SEUIL_NUIT, HEURES_SEUIL_JOUR,
    HEURES_OCCUPATION, HEURES_NON_OCCUPATION,
    HEURES_PERIODE_JOUR, HEURES_PERIODE_NUIT,
    JOURS_SEMAINE
)


# ============================================================
# UTILITAIRES : SEUIL ET OCCUPATION
# ============================================================

def get_seuil(h: int) -> float:
    """
    Retourne le seuil DH (°C) pour l'heure h selon RE2020.
      - h ∈ {0,1,2,3,4,5,23} → 26°C (seuil nocturne)
      - h ∈ {6,...,22}        → 28°C (seuil diurne)
    Vérification : hour 22 → seuil=28°C, hour 23 → seuil=26°C (confirmé Excel).
    """
    return SEUIL_NUIT if h in HEURES_SEUIL_NUIT else SEUIL_JOUR


def get_seuils_tableau() -> np.ndarray:
    """Retourne un tableau numpy des 24 seuils horaires."""
    return np.array([get_seuil(h) for h in range(24)])


def est_occupe(h: int) -> bool:
    """True si l'heure h est une heure d'occupation (0-9h et 17-23h)."""
    return h in HEURES_OCCUPATION


# ============================================================
# COURBES DE TEMPÉRATURE
# ============================================================

def temperature_lin(h: int, T0: float, T_min: float, T_max: float, H_pic: int) -> float:
    """
    Température à l'heure h — interpolation LINÉAIRE (courbe "brute").

    Trois phases vérifiées sur les données Excel :
      Phase 1 [0h → H_MIN=5h]   : descente linéaire T0 → T_min
      Phase 2 [H_MIN → H_pic]   : montée linéaire T_min → T_max
      Phase 3 [H_pic → 24h]     : descente linéaire T_max → T0

    Exemple vérifié (13h lin, T0=27, T_min=22, T_max=39, H_pic=12) :
      h=6 → 22 + 17*(1/7) = 24.43 ✓
      h=12 → 39 ✓
      h=13 → 39 + (27-39)*(1/12) = 38 ✓
    """
    if h <= H_MIN:
        return T0 + (T_min - T0) * h / H_MIN
    elif h <= H_pic:
        return T_min + (T_max - T_min) * (h - H_MIN) / (H_pic - H_MIN)
    else:
        return T_max + (T0 - T_max) * (h - H_pic) / (24 - H_pic)


def temperature_smooth(h: int, T0: float, T_min: float, T_max: float, H_pic: int) -> float:
    """
    Température à l'heure h — interpolation SINUSOÏDALE (courbe "lissée").

    Formules vérifiées sur les données Excel :

      Phase 1 [0h → H_MIN=5h] :
        T(h) = T0 + (T_min - T0) * sin(π/2 * h / H_MIN)
        Vérifié : h=1 → 27 + (22-27)*sin(18°) = 25.455 ✓

      Phase 2 [H_MIN → H_pic] :
        T(h) = T_min + (T_max - T_min) * sin(π/2 * (h-H_MIN)/(H_pic-H_MIN))
        Vérifié : h=6, 15h smooth → 22 + 17*sin(π/2*1/10) = 24.659 ✓

      Phase 3 [H_pic → 24h] :
        T(h) = T0 + (T_max - T0) * cos(π/2 * (h-H_pic)/(24-H_pic))
        Vérifié : h=16, 15h smooth → 27 + 12*cos(π/2*1/9) = 38.818 ✓
                  h=23            → 27 + 12*cos(π/2*8/9) = 29.084 ✓

    DOUTE : Pour certains jours de la semaine dans l'Excel, la colonne
    "15h smooth" présente des valeurs anormalement basses (< T_min) pour
    les heures 1h-4h. Cela ressemble à un bug dans les formules Excel.
    La formule ci-dessus est mathématiquement correcte et vérifiée sur
    l'ensemble des autres cas.
    """
    if h <= H_MIN:
        return T0 + (T_min - T0) * np.sin(np.pi / 2 * h / H_MIN)
    elif h <= H_pic:
        return T_min + (T_max - T_min) * np.sin(np.pi / 2 * (h - H_MIN) / (H_pic - H_MIN))
    else:
        return T0 + (T_max - T0) * np.cos(np.pi / 2 * (h - H_pic) / (24 - H_pic))


def temperature_rand(h: int, T0: float, T_min: float, T_max: float,
                     H_pic: int, bruit: float = 0.0) -> float:
    """
    Température à l'heure h — courbe ALÉATOIRE.

    Formule : T_rand = (T_lin + T_smooth) / 2 + bruit
    Avec : |bruit| ≤ (T_max - T_min) * AMPLITUDE_ALEATOIRE

    Vérifiée sur l'Excel :
      h=1, 13h rand → (26 + 25.455)/2 = 25.727 ✓ (sans bruit)
    L'Excel utilise RAND() Excel qui produit des valeurs différentes
    à chaque recalcul. Ici le bruit est généré au moment du calcul.
    """
    T_l = temperature_lin(h, T0, T_min, T_max, H_pic)
    T_s = temperature_smooth(h, T0, T_min, T_max, H_pic)
    return (T_l + T_s) / 2.0 + bruit


def generer_courbe_temperature(
    T0: float, T_min: float, T_max: float,
    H_pic: int, type_courbe: str,
    seed: int = None
) -> np.ndarray:
    """
    Génère un tableau de 24 températures horaires (0h à 23h).

    Paramètres :
        T0          : Température à minuit (°C)
        T_min       : Température minimale, atteinte à H_MIN=5h (°C)
        T_max       : Température maximale, atteinte à H_pic (°C)
        H_pic       : Heure du pic (12 pour "13h", 15 pour "15h")
        type_courbe : 'smooth', 'lin' ou 'rand'
        seed        : Graine aléatoire pour reproductibilité (optionnel)

    DOUTE VALIDATION :
        La formule suppose T_min ≤ T0 ≤ T_max.
        Si T_min > T0, la phase 1 produit une montée instead d'une descente
        (non testé dans l'Excel). L'interface doit avertir l'utilisateur.
    """
    temperatures = np.zeros(24)

    rng = None
    amplitude_max = 0.0
    if type_courbe == 'rand':
        rng = np.random.default_rng(seed)
        amplitude_max = (T_max - T_min) * AMPLITUDE_ALEATOIRE

    for h in range(24):
        if type_courbe == 'lin':
            temperatures[h] = temperature_lin(h, T0, T_min, T_max, H_pic)
        elif type_courbe == 'smooth':
            temperatures[h] = temperature_smooth(h, T0, T_min, T_max, H_pic)
        elif type_courbe == 'rand':
            bruit = rng.uniform(-amplitude_max, amplitude_max) if rng else 0.0
            temperatures[h] = temperature_rand(h, T0, T_min, T_max, H_pic, bruit)

    return temperatures


# ============================================================
# CALCUL DES DEGRÉS-HEURES (DH)
# ============================================================

def calculer_dh_heure(temperature: float, h: int) -> float:
    """
    DH pour une heure h : max(T(h) - seuil(h), 0).
    Si la température est inférieure au seuil → DH = 0.
    """
    return max(temperature - get_seuil(h), 0.0)


def calculer_metriques_dh(temperatures: np.ndarray) -> dict:
    """
    Calcule toutes les métriques DH à partir de 24 températures horaires.

    Métriques retournées :
    ┌─────────────────┬──────────────────────────────────────────────────────┐
    │ dh_occupation   │ DH uniquement sur les heures occupées (0-9h, 17-23h) │
    │                 │ → Métrique principale RE2020                          │
    ├─────────────────┼──────────────────────────────────────────────────────┤
    │ dh_total        │ DH sur 24h sans filtre (hypothétique 100% occupé)    │
    │                 │ = "DH hors occupation" dans l'Excel jour              │
    │                 │ = "DH 100% occupé" dans l'Excel semaine               │
    ├─────────────────┼──────────────────────────────────────────────────────┤
    │ dh_jour         │ DH heures 6h-21h (sans filtre occupation)            │
    │                 │ Vérifié Excel : 110.98 °C.h ✓                        │
    ├─────────────────┼──────────────────────────────────────────────────────┤
    │ dh_nuit         │ DH heures 0h-5h + 22h-23h (sans filtre)             │
    │                 │ Vérifié Excel : 7.19 °C.h ✓                          │
    │                 │ Note : ces heures sont toutes occupées donc           │
    │                 │ dh_nuit = dh_nuit_occ (pas de différence)            │
    └─────────────────┴──────────────────────────────────────────────────────┘

    DOUTE COHÉRENCE EXCEL :
        L'onglet "interface jour" affiche DH_jour et DH_nuit sans filtre
        d'occupation (somme = DH total = 118.17).
        L'onglet "interface semaine" affiche DH_jour et DH_nuit dont
        la somme égale le DH en occupation (217.12), suggérant un filtre.
        Cette implémentation est cohérente : DH_jour/nuit = sans filtre.
    """
    assert len(temperatures) == 24, "24 valeurs de température attendues (0h-23h)"

    dh_par_heure = np.array([calculer_dh_heure(float(temperatures[h]), h) for h in range(24)])
    seuils = get_seuils_tableau()

    # Métriques agrégées
    dh_occupation = float(sum(dh_par_heure[h] for h in HEURES_OCCUPATION))
    dh_total      = float(np.sum(dh_par_heure))
    dh_jour       = float(sum(dh_par_heure[h] for h in HEURES_PERIODE_JOUR))
    dh_nuit       = float(sum(dh_par_heure[h] for h in HEURES_PERIODE_NUIT))

    return {
        'dh_occupation':  dh_occupation,   # DH RE2020 (heures occupées)
        'dh_total':       dh_total,         # DH 24h sans filtre (hypothétique)
        'dh_jour':        dh_jour,          # DH période 6h-21h
        'dh_nuit':        dh_nuit,          # DH période 0h-5h + 22h-23h
        'dh_par_heure':   dh_par_heure,     # Tableau 24 valeurs DH
        'temperatures':   temperatures,     # Tableau 24 températures
        'seuils':         seuils            # Tableau 24 seuils
    }


# ============================================================
# POINT D'ENTRÉE : CALCUL JOURNÉE
# ============================================================

def calculer_jour(
    T0: float, T_min: float, T_max: float,
    H_pic_option: str, type_courbe_option: str,
    aleatoire: bool, seed: int = None
) -> dict:
    """
    Calcule les métriques DH pour une journée complète.

    Paramètres :
        T0                 : Température à minuit (°C)
        T_min              : Température pic bas / minimum à 5h (°C)
        T_max              : Température pic haut (°C)
        H_pic_option       : "13h" (→ H_pic=12) ou "15h" (→ H_pic=15)
        type_courbe_option : "Lissé", "Brut", ou "Aléatoire"
        aleatoire          : Si True, force l'utilisation de la courbe rand
        seed               : Graine aléatoire (optionnel, pour reproductibilité)

    Retourne : Dictionnaire de métriques DH (voir calculer_metriques_dh)
    """
    H_pic = H_PIC_OPTIONS.get(H_pic_option, H_PIC_OPTIONS["15h"])

    # Le flag 'aleatoire' ou le type "Aléatoire" sélectionnent la courbe rand
    if aleatoire or type_courbe_option == "Aléatoire":
        type_courbe = 'rand'
    else:
        type_courbe = TYPES_COURBES.get(type_courbe_option, 'smooth')

    temperatures = generer_courbe_temperature(T0, T_min, T_max, H_pic, type_courbe, seed)
    return calculer_metriques_dh(temperatures)


# ============================================================
# POINT D'ENTRÉE : CALCUL SEMAINE
# ============================================================

def calculer_semaine(parametres_jours: list, seed_base: int = 0) -> dict:
    """
    Calcule les métriques DH pour une semaine complète (7 jours).

    Paramètre :
        parametres_jours : Liste de 7 dictionnaires, un par jour, avec :
            - T0                 : float — Température à minuit (°C)
            - T_min              : float — Température pic bas (°C)
            - T_max              : float — Température pic haut (°C)
            - H_pic_option       : str   — "13h" ou "15h"
            - type_courbe_option : str   — "Lissé", "Brut" ou "Aléatoire"
            - aleatoire          : bool  — Forcer la courbe aléatoire
        seed_base : Graine de base pour les calculs aléatoires
                    (chaque jour reçoit seed_base + i)

    Retourne un dictionnaire avec :
        - dh_occupation  : DH total en occupation sur 7 jours (RE2020)
        - dh_total       : DH total 24h sur 7 jours (hypothétique)
        - dh_jour        : Somme DH_jour (6h-21h) sur 7 jours
        - dh_nuit        : Somme DH_nuit (0h-5h + 22h-23h) sur 7 jours
        - resultats_jours: Liste des 7 dictionnaires journaliers (pour graphiques)
    """
    resultats_jours = []

    for i, params in enumerate(parametres_jours):
        seed = seed_base + i * 100  # Seed différent par jour, même session

        resultat = calculer_jour(
            T0=float(params['T0']),
            T_min=float(params['T_min']),
            T_max=float(params['T_max']),
            H_pic_option=params['H_pic_option'],
            type_courbe_option=params['type_courbe_option'],
            aleatoire=bool(params['aleatoire']),
            seed=seed
        )
        resultat['jour'] = JOURS_SEMAINE[i]
        resultats_jours.append(resultat)

    # Agrégation sur 7 jours
    return {
        'dh_occupation':   sum(r['dh_occupation'] for r in resultats_jours),
        'dh_total':        sum(r['dh_total'] for r in resultats_jours),
        'dh_jour':         sum(r['dh_jour'] for r in resultats_jours),
        'dh_nuit':         sum(r['dh_nuit'] for r in resultats_jours),
        'resultats_jours': resultats_jours
    }
