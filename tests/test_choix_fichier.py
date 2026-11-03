"""Tests de la fenêtre de choix du fichier météo (0.9.0) : carte des zones, second fichier par défaut, recherche."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calcul.serie import charger_catalogue
from interface import choix_fichier as cf

# ============================================================
# DONNÉES (sources minimales : pas de calcul, chiffres factices)
# ============================================================
CAT = charger_catalogue()
SRC = cf.Sources(catalogue=CAT, charger=lambda cle: None, resume=lambda cle: {"dh": 0, "nuits_20": 0, "tmax": 0},
                 importer=lambda *a: None)


def test_carte_couvre_toutes_les_zones_re2020():
    """Chaque zone RE2020 du catalogue a une place sur la carte schématique, et une seule."""
    places = [z for ligne in cf.DISPOSITION_ZONES for z in ligne if z]
    zones = set(CAT.loc[CAT["famille"] == cf.FAMILLE_CARTE, "zone"])
    assert sorted(places) == sorted(zones) and len(places) == len(set(places))


def test_scenario_de_reference_dans_chaque_zone():
    """La barre de chaque zone lit le fichier « Th-D canicule » : il doit exister partout."""
    for zone in set(CAT.loc[CAT["famille"] == cf.FAMILLE_CARTE, "zone"]):
        cle = cf._fichier_de_zone(zone, SRC)
        assert CAT.set_index("id").loc[cle, "libelle"] == cf.SCENARIO_REFERENCE


def test_second_fichier_par_defaut():
    """Même scénario dans une autre zone (le dernier du catalogue) : H1a Th-D → H3 Th-D."""
    assert cf.second_par_defaut("H1a_th_d", SRC) == "H3_th_d"
    assert cf.second_par_defaut("H1a_th_bc", SRC) == "H3_th_bc"


def test_recherche_par_station():
    trouves = [c for c in cf.cles_disponibles(SRC) if "agen" in cf._texte_recherche(c, SRC)]
    assert sorted(trouves) == ["H2c_th_bc", "H2c_th_d", "Obs_agen_2026"]   # RE2020 + observation


if __name__ == "__main__":
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            f(); print("OK ", nom)
