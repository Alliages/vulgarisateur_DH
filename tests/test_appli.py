"""
Test de l'interface (Streamlit AppTest) : chaque onglet s'ouvre sans erreur, avec le réglage RE2020.
La mémoire du navigateur (composant JavaScript) est désactivée : elle ne fonctionne que dans un vrai navigateur.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from streamlit.testing.v1 import AppTest

from config.reglages import ONGLET_ANALYSER, ONGLETS

# ============================================================
# PARAMÈTRES
# ============================================================
APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
DELAI = 180                                  # secondes (premier calcul + construction des graphiques)


@pytest.fixture(autouse=True)
def _sans_memoire(monkeypatch):
    monkeypatch.setenv("METEO_SANS_MEMOIRE", "1")


@pytest.mark.parametrize("onglet", ONGLETS)
def test_onglet_sans_erreur(onglet):
    at = AppTest.from_file(APP, default_timeout=DELAI)
    at.session_state["onglet"] = onglet
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert not [e for e in at.error if "erreur" in e.value], [e.value for e in at.error]


def test_dh_de_reference_affiche():
    """La carte DH affiche 839 °C.h pour le fichier par défaut (H1a Th-D, réglage RE2020)."""
    at = AppTest.from_file(APP, default_timeout=DELAI)
    at.session_state["onglet"] = ONGLET_ANALYSER       # l'app s'ouvre sur l'Accueil depuis la 0.9.11
    at.run()
    html = " ".join(m.value for m in at.markdown)
    assert 'class="carte principale"' in html and ">839<" in html
