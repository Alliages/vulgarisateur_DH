"""
Tests de non-régression de dh_re2020.calculer_dh.
Lancement : python -m pytest test_dh_re2020.py   (ou python test_dh_re2020.py)
"""

import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from calcul.dh_re2020 import (
    calculer_dh, moyenne_glissante_exterieure, periode_confort_adaptatif,
    masque_occupation_logement_re2020, temperature_operative, delta_top_brasseur,
)

# ============================================================
# DONNÉES DE TEST
# ============================================================
NB_HEURES = 8760
NB_JOURS = 365
HEURES = np.arange(24)
T_30 = np.full(NB_HEURES, 30.0)

# Journée de référence du vulgarisateur Excel (T0=27, Tmin=22, Tmax=39,
# pic 15h, courbe lissée) → DH occupation Excel = 52,47 °C.h/jour
T0, T_MIN, T_MAX, H_MIN, H_PIC = 27.0, 22.0, 39.0, 5, 15


def journee_lissee():
    """Courbe sinusoïdale du vulgarisateur (modules/calculs.py)."""
    t = np.empty(24)
    for h in HEURES:
        if h <= H_MIN:
            t[h] = T0 + (T_MIN - T0) * np.sin(np.pi / 2 * h / H_MIN)
        elif h <= H_PIC:
            t[h] = T_MIN + (T_MAX - T_MIN) * np.sin(np.pi / 2 * (h - H_MIN) / (H_PIC - H_MIN))
        else:
            t[h] = T0 + (T_MAX - T0) * np.cos(np.pi / 2 * (h - H_PIC) / (24 - H_PIC))
    return t


# ============================================================
# SEUILS FIXES
# ============================================================

def test_constante_30_seuils_fixes():
    """30 °C toute l'année : jour 16 h × 2 K + nuit 8 h × 4 K = 64 °C.h/jour."""
    res = calculer_dh(T_30, details=True)
    assert np.isclose(res["dh_jour"], 16 * 2 * NB_JOURS)
    assert np.isclose(res["dh_nuit"], 8 * 4 * NB_JOURS)
    assert np.isclose(res["dh_total"], 64 * NB_JOURS)
    assert np.isclose(calculer_dh(T_30, periode="nuit"), 8 * 4 * NB_JOURS)


def test_sous_le_seuil_zero():
    assert calculer_dh(np.full(NB_HEURES, 25.9)) == 0.0


def test_retrouve_excel_vulgarisateur():
    """Conventions de l'Excel : jour jusqu'à 23h, occupation 0–9h + 17–23h."""
    t = np.tile(journee_lissee(), NB_JOURS)
    occ_jour = np.isin(HEURES, list(range(0, 10)) + list(range(17, 24)))
    dh_occ = calculer_dh(t, heure_fin_jour=23, occupation=np.tile(occ_jour, NB_JOURS))
    assert np.isclose(dh_occ / NB_JOURS, 52.47, atol=0.01)
    assert np.isclose(calculer_dh(t, heure_fin_jour=23) / NB_JOURS, 118.17, atol=0.01)


# ============================================================
# MOYENNE GLISSANTE ET PÉRIODE ADAPTATIVE
# ============================================================

def test_moyenne_glissante_re2020():
    """Init θrm = 0 puis θrm(j) = 0,8·θrm(j−1) + 0,2·20."""
    theta = moyenne_glissante_exterieure(np.full(NB_HEURES, 20.0))
    assert theta[0] == 0.0 and np.isclose(theta[1], 4.0) and np.isclose(theta[2], 7.2)
    assert np.isclose(theta[-1], 20.0)


def test_moyenne_glissante_cyclique():
    theta = moyenne_glissante_exterieure(np.full(NB_HEURES, 20.0), initialisation="cyclique")
    assert np.allclose(theta, 20.0)


def test_periode_adaptative_continue():
    """Du premier au dernier jour où θrm ≥ 16, trous inclus."""
    theta = np.array([10, 17, 12, 18, 10, 9], float)
    assert periode_confort_adaptatif(theta).tolist() == [False, True, True, True, False, False]


def test_exterieur_froid_aucun_dh():
    """θrm jamais ≥ 16 °C → pas de période de confort adaptatif → DH = 0."""
    assert calculer_dh(T_30, np.full(NB_HEURES, 10.0)) == 0.0


# ============================================================
# SEUIL ADAPTATIF (2543)-(2545)
# ============================================================

def test_seuil_adaptatif_intermediaire():
    """θrm = 20 °C → 0,33×20 + 18,8 + 2 = 27,4 °C le jour, 26 la nuit."""
    res = calculer_dh(T_30, np.full(NB_HEURES, 20.0),
                      initialisation_theta_rm="cyclique", details=True)
    assert np.isclose(res["seuil_horaire"][12], 27.4)
    assert np.isclose(res["seuil_horaire"][2], 26.0)


def test_seuil_adaptatif_bornes():
    """Plancher 26 °C, plafond 28 °C (θiifr+ + 2)."""
    tiede = calculer_dh(T_30, np.full(NB_HEURES, 14.0), appliquer_periode_adaptative=False,
                        initialisation_theta_rm="cyclique", details=True)
    chaud = calculer_dh(T_30, np.full(NB_HEURES, 25.0),
                        initialisation_theta_rm="cyclique", details=True)
    assert np.isclose(tiede["seuil_horaire"].max(), 26.0)
    assert np.isclose(chaud["seuil_horaire"].max(), 28.0)
    assert np.isclose(chaud["dh_total"], 64 * NB_JOURS)


def test_usage_autre_adaptatif_la_nuit():
    res = calculer_dh(T_30, np.full(NB_HEURES, 25.0), usage="autre",
                      initialisation_theta_rm="cyclique", details=True)
    assert np.isclose(res["seuil_horaire"][2], 28.0)


def test_decalage_utc():
    """Série en UTC, été (+2) : l'heure UTC 4 est 6h légale → jour."""
    res = calculer_dh(T_30, decalage_heure=2, details=True)
    assert np.isclose(res["seuil_horaire"][4], 28.0)
    assert np.isclose(res["seuil_horaire"][3], 26.0)


def test_indicateurs_pedagogiques():
    res = calculer_dh(np.full(NB_HEURES, 27.5), details=True)   # nuit +1,5 ; jour −0,5
    assert res["nb_h_inconfort"] == 8 * NB_JOURS
    assert res["nb_h_inconfort_1C"] == 8 * NB_JOURS
    assert res["nb_h_inconfort_2C"] == 0


# ============================================================
# OCCUPATION, OPÉRATIVE, BRASSEURS
# ============================================================

def test_occupation_logement():
    """Semaine type : 4 j × 8 h + 1 j × 4 h = 36 h inoccupées / semaine."""
    occ = masque_occupation_logement_re2020(7 * 24)
    assert (~occ).sum() == 36
    assert occ[8] and not occ[9] and not occ[16] and occ[17]                  # lundi : absents de 9h à 17h
    assert occ[2 * 24 + 8] and not occ[2 * 24 + 12] and occ[2 * 24 + 13]      # mercredi : absents de 9h à 13h
    assert occ[5 * 24:].all()                                                 # week-end


def test_occupation_identique_au_classeur_des_scenarios():
    """Semaine type recopiée du classeur « scénarios conventionnels » (usages 1 et 2), cases 1 à 24."""
    semaine = [1] * 9 + [0] * 8 + [1] * 7                 # lundi, mardi, jeudi, vendredi
    mercredi = [1] * 9 + [0] * 4 + [1] * 11
    attendu = np.array(semaine * 2 + mercredi + semaine * 2 + [1] * 48, dtype=bool)
    assert np.array_equal(masque_occupation_logement_re2020(7 * 24), attendu)


def test_semaine_inoccupee_de_decembre():
    """4e semaine de décembre = semaine 52 : jours 358 à 364 inoccupés, jour 365 occupé le soir."""
    occ = masque_occupation_logement_re2020(8760).reshape(365, 24)
    assert not occ[357:364].any()                         # jours 358 à 364 (indices 357 à 363)
    assert occ[356].all()                                 # jour 357 : dimanche de la semaine 51
    assert occ[364, 0] and occ[364, 23]                   # jour 365 : scénario normal (un lundi)


def test_temperature_operative():
    assert np.isclose(temperature_operative(30.0, 26.0), 28.0)   # ptop = 0,5


def test_brasseur():
    assert delta_top_brasseur(0.2, 28, 28) == 0.0
    assert np.isclose(delta_top_brasseur(0.6, 28, 28), 1.8322 * np.log(0.6) + 3.0498)
    t = T_30
    assert np.isclose(calculer_dh(t, delta_corr_syst=1.0), (16 * 1 + 8 * 3) * NB_JOURS)


def test_annee_bissextile():
    assert np.isclose(calculer_dh(np.full(8784, 30.0)), 64 * 366)


if __name__ == "__main__":
    for nom, fonction in list(globals().items()):
        if nom.startswith("test_"):
            fonction()
            print(f"OK  {nom}")
