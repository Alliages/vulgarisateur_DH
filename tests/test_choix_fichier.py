"""Tests de la fenêtre de choix du fichier météo (0.9.0, carte des zones 0.9.10) : carte, liste, second fichier, recherche."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calcul.serie import charger_catalogue
from interface import carte_zones, choix_fichier as cf

# ============================================================
# DONNÉES (sources minimales : pas de calcul, chiffres factices)
# ============================================================
CAT = charger_catalogue()
SRC = cf.Sources(catalogue=CAT, charger=lambda cle: None, resume=lambda cle: {"dh": 0, "nuits_20": 0, "tmax": 0},
                 importer=lambda *a: None)


def test_carte_couvre_toutes_les_zones_du_catalogue():
    """Chaque zone du catalogue a des départements sur la carte de France (config/carte_france.json)."""
    zones_carte = {d["zone"] for d in carte_zones.CARTE["departements"]}
    assert set(CAT["zone"]) <= zones_carte and set(carte_zones.ZONES) == zones_carte


def test_scenario_de_reference_dans_chaque_zone():
    """La teinte de chaque zone lit son fichier « Th-D canicule » : il doit exister partout."""
    dh = cf._dh_reference(SRC)
    assert set(dh) == set(carte_zones.ZONES)
    assert set(carte_zones.couleurs_zones({z: n for n, z in enumerate(carte_zones.ZONES)})) == set(carte_zones.ZONES)


def test_positions_des_stations():
    """Chaque fichier a un département (2 caractères) ; les coordonnées, facultatives, tombent dans la carte."""
    x0, y0, largeur, hauteur = (float(v) for v in carte_zones.CADRAGE.split())
    codes = {d["code"] for d in carte_zones.CARTE["departements"]}
    for _, l in CAT.iterrows():
        assert l["departement"] in codes, l["id"]
        if l["latitude"]:
            x, y = carte_zones.projeter(l["latitude"], l["longitude"])
            assert x0 <= x <= x0 + largeur and y0 <= y <= y0 + hauteur, l["id"]
    assert carte_zones.projeter(48.7733, 2.0097) == (486.4, 252.1)        # Trappes, comme sur la carte d'origine


def test_donnees_de_la_liste():
    """Observations : une ligne par station, groupées par zone ; RE2020 : 2 fichiers par zone, station en en-tête."""
    resumes = {i: {"dh": 1000, "nuits_20": 10, "tmax": 30} for i in CAT["id"]}
    obs = carte_zones.donnees_famille(CAT[CAT["famille"] == "Observations"].to_dict("records"), resumes, {}, None, None,
                                      "#f05d5e", "station", "titre")
    assert sum(len(g["lignes"]) for g in obs["groupes"]) == 15 and obs["compte"]["H1a"] == 4
    re2020 = carte_zones.donnees_famille(CAT[CAT["famille"] == "RE2020"].to_dict("records"), resumes, {}, "H1a_th_d",
                                         None, "#f05d5e", "fichier", "titre")
    h1a = next(g for g in re2020["groupes"] if g["zone"] == "H1a")
    assert "station Trappes" in h1a["entete"] and [l["nom"] for l in h1a["lignes"]] == ["Th-BC moyen", "Th-D canicule"]
    assert len(re2020["points"]) == 8                                          # un point par station, pas par fichier


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
