"""Tests du moteur d'indicateurs (valeurs de référence H1a Th-D, réglage RE2020)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calcul.hypotheses import charger_hypotheses, charger_indicateurs
from calcul.indicateurs import analyser, calculer_indicateurs
from calcul.serie import charger_catalogue, charger_serie
from config.reglages import REGLAGE_RE2020

# ============================================================
# DONNÉES
# ============================================================
HYP, DEFS = charger_hypotheses(), charger_indicateurs()
CAT = charger_catalogue().set_index("id")


def _serie(identifiant):
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
    a, v = _valeurs("H1a_releve_trappes_2026")
    assert a.methode_effective == "basic" and a.message_methode
    assert v["heures_chaudes"] == 73 and v["nuits_consecutives"] == 1


def test_ordre_des_indicateurs():
    assert [d["id"] for d in DEFS] == ["dh", "dh_nuit", "heures_chaudes", "nuits_20", "nuits_24", "nuits_consecutives", "t_moyenne", "t_moyenne_nuit"]


if __name__ == "__main__":
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            f(); print("OK ", nom)
