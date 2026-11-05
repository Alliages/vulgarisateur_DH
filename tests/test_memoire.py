"""Mémoire du navigateur : les nouveaux indicateurs rejoignent l'ordre des cartes gardé d'une visite à l'autre."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from types import SimpleNamespace

import pytest

from interface import memoire

# ============================================================
# DONNÉES
# ============================================================
DEFAUT = ["dh", "nuits_20", "vdc_severite", "vdc_nombre"]


class Navigateur(dict):
    """Stockage du navigateur simulé."""
    def ready(self):
        return True


@pytest.fixture
def session(monkeypatch):
    etat = {}
    monkeypatch.setattr(memoire, "st", SimpleNamespace(session_state=etat))
    return etat


def _charger(monkeypatch, navigateur):
    monkeypatch.setattr(memoire, "_gestionnaire", lambda: navigateur)
    memoire.charger({}, DEFAUT)


def test_ancienne_memoire_recoit_les_nouvelles_cartes(session, monkeypatch):
    _charger(monkeypatch, Navigateur(ordre_cartes=["nuits_20", "dh"]))
    assert session["r_indicateurs"] == ["nuits_20", "dh", "vdc_severite", "vdc_nombre"]
    assert session["cartes_connues"] == DEFAUT


def test_carte_retiree_reste_retiree(session, monkeypatch):
    _charger(monkeypatch, Navigateur(ordre_cartes=["dh", "vdc_nombre"], cartes_connues=DEFAUT))
    assert session["r_indicateurs"] == ["dh", "vdc_nombre"]


def test_seule_la_carte_inconnue_est_ajoutee(session, monkeypatch):
    _charger(monkeypatch, Navigateur(ordre_cartes=["dh"], cartes_connues=["dh", "nuits_20", "vdc_severite"]))
    assert session["r_indicateurs"] == ["dh", "vdc_nombre"]


def test_premiere_visite_garde_le_defaut(session, monkeypatch):
    _charger(monkeypatch, Navigateur())
    assert "r_indicateurs" not in session and session["cartes_connues"] == DEFAUT
