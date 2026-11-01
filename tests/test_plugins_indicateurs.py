"""Tests du registre d'indicateurs (un fichier par indicateur dans calcul/indicateurs/, découverte automatique)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from calcul.analyse import analyser
from calcul.hypotheses import charger_hypotheses, charger_indicateurs
from calcul.indicateurs import REGISTRE, Indicateur, Resultat, calculer_indicateurs
from calcul.indicateurs import _modele
from calcul.serie import charger_catalogue, charger_serie
from config.charte import COULEURS_TEINTES
from config.reglages import REGLAGE_RE2020
from interface.cartes import ICONES

# ============================================================
# DONNÉES
# ============================================================
DOSSIER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "calcul", "indicateurs")
HYP = charger_hypotheses()
TOUS = charger_indicateurs(tous=True)
LIGNE = charger_catalogue().set_index("id").loc["H1a_th_d"].to_dict() | {"id": "H1a_th_d"}
ANALYSE = analyser(charger_serie(LIGNE), REGLAGE_RE2020, HYP)


def test_chaque_fichier_est_inscrit():
    """Un fichier <id>.py (hors base.py et « _… ») = un indicateur du registre, au nom du fichier."""
    fichiers = {f[:-3] for f in os.listdir(DOSSIER) if f.endswith(".py") and not f.startswith("_") and f != "base.py"}
    assert fichiers == set(REGISTRE)
    assert all(ind.id == i for i, ind in REGISTRE.items())


def test_registre_et_excel_correspondent():
    """Chaque indicateur a sa ligne dans hypotheses.xlsx (onglet indicateurs), et inversement."""
    assert {d["id"] for d in TOUS} == set(REGISTRE)


def test_teintes_et_icones_connues():
    for ind in REGISTRE.values():
        assert ind.teinte in COULEURS_TEINTES and ind.icone in ICONES
    assert [i for i, ind in REGISTRE.items() if ind.principale] == ["dh"]       # une seule carte en couleur pleine


def test_tous_les_indicateurs_se_calculent():
    """Chaque indicateur renvoie un Resultat (nombre ou None) et un mini-graphique connu, ou aucun."""
    for d, r in calculer_indicateurs(ANALYSE, REGLAGE_RE2020, HYP, TOUS):
        assert isinstance(r, Resultat) and (r.valeur is None or float(r.valeur) == float(r.valeur))
        profil = r.info["profil"]
        assert profil is None or profil["type"] in ("barres", "ligne", "bande", "jauge")


def test_le_modele_fonctionne_mais_reste_hors_registre():
    """_modele.py sert d'exemple : il calcule, mais n'est pas inscrit (nom en « _ »)."""
    r = _modele.INDICATEUR.calculer(ANALYSE, REGLAGE_RE2020, HYP)
    assert r.valeur == 218 and "_modele" not in REGISTRE                     # = heures > 28 °C de H1a Th-D
    assert _modele.INDICATEUR.profil(ANALYSE, HYP)["type"] == "barres"


def test_erreurs_de_declaration_explicites():
    with pytest.raises(ValueError, match="teinte"):
        Indicateur(id="x", calculer=lambda a, r, h: Resultat(0), teinte="violet")
    with pytest.raises(ValueError, match="icône"):
        Indicateur(id="x", calculer=lambda a, r, h: Resultat(0), icone="nuage")


if __name__ == "__main__":
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            f(); print("OK ", nom)
