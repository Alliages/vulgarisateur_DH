"""Tests de l'export (onglet ④ Exporter) : copier-coller, CSV « Excel français », Excel, alignement de 2 fichiers."""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from calcul.hypotheses import charger_hypotheses, charger_indicateurs, remplacer_reperes
from calcul.analyse import analyser
from calcul.indicateurs import calculer_indicateurs
from calcul.serie import charger_catalogue, charger_serie
from config.reglages import REGLAGE_RE2020
from export.export import ENCODAGE_CSV, FichierExport, csv_export, excel_export, tableau_horaire, texte_copier

# ============================================================
# DONNÉES
# ============================================================
HYP, DEFS = charger_hypotheses(), charger_indicateurs()
CAT = charger_catalogue().set_index("id")
REGLAGE = dict(REGLAGE_RE2020, indicateurs=DEFS)
TEXTE_REGLAGE = "réglage RE2020"


# Relevé partiel de référence : fixture de test, hors catalogue de l'outil (retiré du catalogue en 0.9.9)
RELEVE_TEST = {"id": "releve_trappes_2026", "famille": "Observations", "zone": "H1a", "libelle": "Relevé Trappes mai 2026",
               "base_horaire": "légale", "format": "date_heure", "chemin": "tests/donnees/releve_trappes_2026.csv"}


def _fichier(identifiant):
    ligne = dict(RELEVE_TEST) if identifiant == RELEVE_TEST["id"] else CAT.loc[identifiant].to_dict()
    ligne["id"] = identifiant
    a = analyser(charger_serie(ligne), REGLAGE_RE2020, HYP)
    return FichierExport(a.serie.libelle, a, calculer_indicateurs(a, REGLAGE_RE2020, HYP, DEFS))


A, B, R = _fichier("H1a_th_d"), _fichier("H3_th_d"), _fichier("releve_trappes_2026")


def test_copier_coller_tableau_et_ecart():
    lignes = texte_copier([A, B], HYP, remplacer_reperes, "tableau").split("\n")
    assert lignes[0].split("\t") == ["Indicateur", A.nom, B.nom, "Écart"]
    assert lignes[1].split("\t") == ["DH (°C.h)", "908", "1660", "+752"]       # nombres lisibles par Excel
    assert len(lignes) == 1 + len(DEFS)


def test_copier_coller_texte_avec_reglage():
    texte = texte_copier([A], HYP, remplacer_reperes, "texte", texte_reglage=TEXTE_REGLAGE)
    assert texte.startswith("Météo et Chaleur v") and "Source :" in texte.splitlines()[-1]
    assert "19,2" in texte                                                        # 1 décimale, virgule


def test_csv_indicateurs_puis_horaire():
    lignes = csv_export([A, B], HYP, remplacer_reperes, TEXTE_REGLAGE).decode(ENCODAGE_CSV).splitlines()
    tete = [l for l in lignes if l.startswith("#")]
    assert len(tete) == 2 + 1 + len(DEFS)                                         # réglage, source, en-tête, indicateurs
    assert tete[3].startswith("# DH (°C.h);908,464;")
    donnees = pd.read_csv(io.StringIO("\n".join(lignes[len(tete):])), sep=";", decimal=",")
    assert len(donnees) == 8760 and list(donnees.columns[:2]) == ["date", "heure"]
    assert abs(donnees[f"DH {A.nom} (°C.h)"].sum() - 908.464) < 0.05


def test_csv_indicateurs_seuls():
    lignes = csv_export([A], HYP, remplacer_reperes, TEXTE_REGLAGE, avec_horaire=False).decode(ENCODAGE_CSV).splitlines()
    assert lignes[2].startswith("Indicateur;") and len(lignes) == 3 + len(DEFS)


def test_releve_et_annee_type_alignes():
    """Un relevé de 9 jours à côté d'une année type : 8 760 lignes, le relevé n'occupe que ses jours."""
    df = tableau_horaire([A, R])
    assert len(df) == 8760
    assert df[f"T {R.nom} (°C)"].notna().sum() == len(R.analyse.serie.t)


def test_excel_feuilles():
    classeur = pd.ExcelFile(io.BytesIO(excel_export([A, B], HYP, remplacer_reperes, REGLAGE, TEXTE_REGLAGE)))
    assert classeur.sheet_names == ["indicateurs", "horaire", "hypotheses", "reglage_et_fichiers"]


if __name__ == "__main__":
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            f(); print("OK ", nom)
