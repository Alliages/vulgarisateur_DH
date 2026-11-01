"""
============================================================
 CONFORT_PTC — SEUL POINT DE CONTACT AVEC PYTHERMALCOMFORT
============================================================
 Toutes les fonctions de la librairie pythermalcomfort utilisées
 par Météo et Chaleur passent par ce fichier.

 Depuis la 0.9.8, la librairie n'est PLUS installée avec l'outil
 (requirements.txt) : son chargement retardait le démarrage en ligne
 d'environ 11 s. Les formules de repli ci-dessous, identiques, sont
 alors utilisées (PTC_DISPONIBLE = False). La librairie reste la
 référence des tests (requirements-dev.txt, tests/test_confort_ptc.py).
============================================================
"""

import numpy as np

# ============================================================
# PARAMÈTRES
# ============================================================
PENTE_EN16798 = 0.33                     # droite de confort NF EN 16798-1
ORDONNEE_EN16798 = 18.8
POIDS_THETA_RM_EN16798 = [1, 0.8, 0.6, 0.5, 0.4, 0.3, 0.2]   # 7 jours, du plus récent au plus ancien
VITESSE_AIR_DEFAUT = 0.1                 # m/s, sans effet sur la limite haute

try:
    from pythermalcomfort.models import adaptive_en
    import pythermalcomfort
    PTC_DISPONIBLE = True
    PTC_VERSION = pythermalcomfort.__version__
except ImportError:                       # repli : formules identiques, codées ici
    PTC_DISPONIBLE = False
    PTC_VERSION = "non installé"


# ============================================================
# DROITE DE CONFORT ADAPTATIF
# ============================================================

def limite_haute_confort(theta_rm, delta_categorie: float = 2.0) -> np.ndarray:
    """
    Limite haute de confort adaptatif : 0,33 × θrm + 18,8 + Δ (Δ = 2 °C en catégorie I).
    Identique à la formule (2543) de l'annexe III Th-BCE 2020 (avant plancher / plafond RE2020).

    Avec pythermalcomfort : adaptive_en(...).tmp_cmf_cat_i_up, en désactivant
    limit_inputs (sinon NaN si θrm hors 10–33,5 °C) et round_output (arrondi 0,1 °C).
    Les catégories II / III (Δ = 3 / 4 °C) sont obtenues en décalant la catégorie I.
    """
    theta_rm = np.asarray(theta_rm, dtype=float)
    if PTC_DISPONIBLE:
        res = adaptive_en(tdb=25.0, tr=25.0, t_running_mean=theta_rm, v=VITESSE_AIR_DEFAUT,
                          limit_inputs=False, round_output=False)
        cat_i = np.asarray(res.tmp_cmf_cat_i_up, dtype=float)
        return cat_i + (delta_categorie - 2.0)
    return PENTE_EN16798 * theta_rm + ORDONNEE_EN16798 + delta_categorie


# ============================================================
# MOYENNE GLISSANTE EN 16798 (comparaison pédagogique)
# ============================================================

def theta_rm_en16798(t_moy_jour) -> np.ndarray:
    """
    θrm EN 16798-1 : somme pondérée des 7 jours précédents (poids 1 ; 0,8 ; … ; 0,2) / 3,8.
    NaN pour les 7 premiers jours. Sert uniquement à COMPARER avec la récurrence RE2020.
    """
    tm = np.asarray(t_moy_jour, dtype=float)
    poids = np.array(POIDS_THETA_RM_EN16798)
    sortie = np.full(tm.size, np.nan)
    for j in range(len(poids), tm.size):
        sortie[j] = np.dot(poids, tm[j - 1::-1][:len(poids)]) / poids.sum()
    return sortie


# ============================================================
# EFFET DES BRASSEURS D'AIR (référence EN 16798)
# ============================================================

def gain_brasseur_en16798(vitesse_air: float) -> float:
    """Paliers EN 16798-1 : +1,2 / 1,8 / 2,2 °C pour v ≥ 0,6 / 0,9 / 1,2 m/s (θop ≥ 25 °C)."""
    if vitesse_air >= 1.2:
        return 2.2
    if vitesse_air >= 0.9:
        return 1.8
    if vitesse_air >= 0.6:
        return 1.2
    return 0.0
