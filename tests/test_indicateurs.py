"""Tests du moteur d'indicateurs (valeurs de référence H1a Th-D, réglage RE2020)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calcul.hypotheses import charger_hypotheses, charger_indicateurs
from calcul.analyse import analyser
from calcul.indicateurs import calculer_indicateurs
from calcul.serie import charger_catalogue, charger_serie
from config.reglages import REGLAGE_RE2020

# ============================================================
# DONNÉES
# ============================================================
HYP, DEFS = charger_hypotheses(), charger_indicateurs()
CAT = charger_catalogue().set_index("id")


# Relevé partiel de référence : fixture de test, hors catalogue de l'outil (retiré du catalogue en 0.9.9)
RELEVE_TEST = {"id": "releve_trappes_2026", "famille": "Observations", "zone": "H1a", "libelle": "Relevé Trappes mai 2026",
               "base_horaire": "légale", "format": "date_heure", "chemin": "tests/donnees/releve_trappes_2026.csv"}


def _serie(identifiant):
    if identifiant == RELEVE_TEST["id"]:
        return charger_serie(dict(RELEVE_TEST))
    ligne = CAT.loc[identifiant].to_dict(); ligne["id"] = identifiant
    return charger_serie(ligne)


def _valeurs(identifiant, **reglage):
    r = dict(REGLAGE_RE2020, **reglage)
    a = analyser(_serie(identifiant), r, HYP)
    return a, {d["id"]: x.valeur for d, x in calculer_indicateurs(a, r, HYP, DEFS)}


def test_non_regression_h1a():
    a, v = _valeurs("H1a_th_d")
    assert a.methode_effective == "RE2020"
    assert round(v["dh"], 3) == 839.145
    assert round(v["dh_nuit"]) == 151 and v["nuits_20"] == 16 and v["nuits_24"] == 1
    assert v["heures_chaudes"] == 218 and v["nuits_consecutives"] == 11
    assert round(v["t_moyenne"], 1) == 19.2 and round(v["t_moyenne_nuit"], 1) == 17.2


def test_basic_sans_occupation_h1a():
    _, v = _valeurs("H1a_th_d", methode="basic", occupation=False)
    assert round(v["dh"], 3) == 1074.935          # valeur de l'Excel DH_basic_reel_H1a


def test_releve_partiel_bascule_en_basic():
    a, v = _valeurs("releve_trappes_2026")
    assert a.methode_effective == "basic" and a.message_methode
    assert v["heures_chaudes"] == 73 and v["nuits_consecutives"] == 1


def test_ordre_des_indicateurs():
    assert [d["id"] for d in DEFS] == ["dh", "heures_chaudes", "dh_nuit", "nuits_20", "nuits_consecutives", "nuits_24", "t_moyenne", "t_moyenne_nuit"]



def test_decimales_et_ordre_personnalise():
    """Températures moyennes à 1 décimale ; l'ordre reçu est l'ordre rendu (choix dans l'interface)."""
    dec = {d["id"]: d["decimales"] for d in charger_indicateurs(tous=True)}
    assert dec["t_moyenne"] == 1 and dec["t_moyenne_nuit"] == 1 and dec["dh"] == 0
    ordre = ["t_moyenne", "dh", "nuits_24"]
    defs = {d["id"]: d for d in charger_indicateurs(tous=True)}
    a = analyser(_serie("H1a_th_d"), REGLAGE_RE2020, HYP)
    assert [d["id"] for d, _ in calculer_indicateurs(a, REGLAGE_RE2020, HYP, [defs[i] for i in ordre])] == ordre


def test_profils_des_cartes():
    """Mini-graphiques : jauge de la part de nuit (≈ 18 % pour H1a Th-D), barres mensuelles pour le DH."""
    a = analyser(_serie("H1a_th_d"), REGLAGE_RE2020, HYP)
    profils = {d["id"]: r.info["profil"] for d, r in calculer_indicateurs(a, REGLAGE_RE2020, HYP, DEFS)}
    assert profils["dh_nuit"]["type"] == "jauge" and round(100 * profils["dh_nuit"]["valeurs"]) == 18
    assert profils["dh"]["type"] == "barres" and list(profils["dh"]["valeurs"].index) == [6, 7, 8, 9]


def test_familles_du_catalogue():
    """Chaque fichier appartient à une famille connue du menu."""
    from config.reglages import FAMILLES
    assert set(CAT["famille"]) <= set(FAMILLES)
    assert (CAT["famille"] == "RE2020").sum() == 16 and (CAT["famille"] == "Observations").sum() == 15


if __name__ == "__main__":
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            f(); print("OK ", nom)
