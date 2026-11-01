"""Tests des recherches partagées de calcul/analyse.py (suites de nuits, tranches, semaine type de l'onglet Créer)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from calcul.analyse import analyser, journees_de_la_periode_chaude, plus_longue_suite, tranche
from calcul.hypotheses import charger_hypotheses
from calcul.serie import charger_catalogue, charger_serie
from config.reglages import REGLAGE_RE2020

# ============================================================
# DONNÉES
# ============================================================
HYP = charger_hypotheses()
CAT = charger_catalogue().set_index("id")


def _suite_par_boucle(chaudes: pd.Series):
    """Version lente et évidente (celle de la 0.9.7), pour comparer."""
    meilleure, debut, n = (None, None, 0), None, 0
    for d, oui in chaudes.items():
        if oui:
            debut, n = (d if n == 0 else debut), n + 1
            if n > meilleure[2]:
                meilleure = (debut, d, n)
        else:
            n = 0
    return meilleure if meilleure[2] else None


def test_plus_longue_suite_identique_a_la_boucle():
    jours = pd.date_range("2018-06-01", periods=120, freq="D")
    alea = np.random.default_rng(1)
    for _ in range(200):
        chaudes = pd.Series(alea.random(120) < alea.random(), index=jours)
        assert plus_longue_suite(chaudes) == _suite_par_boucle(chaudes)
    assert plus_longue_suite(pd.Series(False, index=jours)) is None


def test_tranche_et_semaine_de_l_onglet_creer():
    s = charger_serie(CAT.loc["H1a_th_d"].to_dict() | {"id": "H1a_th_d"})
    a = analyser(s, REGLAGE_RE2020, HYP)
    debut = a.jours.index[200]
    t, seuil, dh, x = tranche(a, debut, 24)
    assert len(t) == len(seuil) == len(dh) == 24 and x[0] == debut
    jours = journees_de_la_periode_chaude(a, "moyenne", 7, 7)
    assert len(jours) == 7 and all(tmax >= tmin for _, _, tmax, tmin in jours)


if __name__ == "__main__":
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            f(); print("OK ", nom)
