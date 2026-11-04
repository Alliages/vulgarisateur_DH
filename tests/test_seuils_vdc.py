"""Seuils des vagues de chaleur (outils/calculer_seuils_vdc.py) : calcul et erreurs, sans réseau."""
import gzip
import io
import json
import os
import shutil
import sys
import urllib.error

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "outils"))
import calculer_seuils_vdc as vdc  # noqa: E402
from calculer_seuils_vdc import ErreurExpliquee, calculer_seuils, jours_au_dessus  # noqa: E402

# ---------- Variables ----------
DEBUT, FIN = 1991, 2020
CENTILES = {"spic": 99.5, "sdeb": 97.5, "sint": 95}
URL_78 = "https://exemple.fr/Q_78_previous-1950-2024_RR-T-Vent.csv.gz"


def serie(tn, tx, debut=DEBUT, fin=FIN):
    dates = pd.date_range(f"{debut}-01-01", f"{fin}-12-31", freq="D")
    return pd.DataFrame({"TN": tn(len(dates)), "TX": tx(len(dates))}, index=dates)


# ============================================================
# CALCUL
# ============================================================

def test_tm_est_la_moyenne_de_tn_et_tx():
    # Tm constante = 20 °C → les trois seuils valent 20 °C
    s = serie(lambda n: np.full(n, 15.0), lambda n: np.full(n, 25.0))
    seuils, n, taux, _ = calculer_seuils(s, DEBUT, FIN, CENTILES)
    assert seuils == {"spic": 20.0, "sdeb": 20.0, "sint": 20.0}
    assert n == 10958 and taux == 1.0          # 30 ans dont 8 années bissextiles


def test_ordre_des_seuils_et_centiles():
    rng = np.random.default_rng(0)
    s = serie(lambda n: rng.normal(8, 6, n), lambda n: rng.normal(18, 7, n))
    seuils, *_ = calculer_seuils(s, DEBUT, FIN, CENTILES)
    assert seuils["spic"] > seuils["sdeb"] > seuils["sint"]
    tm = (s["TN"] + s["TX"]) / 2
    assert abs(seuils["sdeb"] - np.percentile(tm, 97.5)) < 0.05


def test_jours_incomplets():
    s = serie(lambda n: np.full(n, 15.0), lambda n: np.full(n, 25.0))
    s.iloc[::10, 0] = np.nan                    # un jour sur dix sans TN
    _, n, taux, _ = calculer_seuils(s, DEBUT, FIN, CENTILES)
    assert n == 10958 - len(s.iloc[::10]) and 0.89 < taux < 0.91


def test_controle_ete():
    s = serie(lambda n: np.full(n, 15.0), lambda n: np.full(n, 25.0))
    s.loc["2003-08-01":"2003-08-10", ["TN", "TX"]] = [25.0, 35.0]
    _, _, _, tm = calculer_seuils(s, DEBUT, FIN, CENTILES)
    assert jours_au_dessus(tm, 30.0, 2003) == 10


# ============================================================
# ERREURS (faux réseau)
# ============================================================

class FausseReponse(io.BytesIO):
    """Réponse de urlopen : contenu + en-têtes, utilisable dans un « with »."""

    def __init__(self, contenu):
        super().__init__(contenu)
        self.headers = {"Content-Length": str(len(contenu))}


def fichier_gz(postes):
    """Faux fichier Météo-France : Tm = 20 °C tous les jours, 30 °C du 1er au 10 août 2003."""
    dates = pd.date_range(f"{DEBUT}-01-01", f"{FIN}-12-31", freq="D")
    tx = np.where((dates >= "2003-08-01") & (dates <= "2003-08-10"), 40.0, 25.0)
    lignes = ["NUM_POSTE;NOM_USUEL;AAAAMMJJ;RR;TN;TX"]
    for poste in postes:
        lignes += [f"{poste};STATION;{d:%Y%m%d};0;15.0;{x}" for d, x in zip(dates, tx)]
    return gzip.compress("\n".join(lignes).encode())


@pytest.fixture
def reseau(monkeypatch):
    """Faux internet : dictionnaire URL → contenu (bytes) ou liste d'erreurs puis contenu."""
    pages = {}

    def urlopen(url, timeout=None):
        rep = pages.get(url)
        if isinstance(rep, list):
            rep = rep.pop(0)
        if rep is None:
            raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
        if isinstance(rep, Exception):
            raise rep
        return FausseReponse(rep)

    monkeypatch.setattr(vdc.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(vdc, "ATTENTE_ESSAI", 0)
    return pages


def test_erreur_passagere_retentee(reseau):
    reseau[URL_78] = [urllib.error.HTTPError(URL_78, 503, "Service Unavailable", None, None), b"ok"]
    assert vdc.telecharger(URL_78, "essai") == b"ok"


def test_erreur_404_avec_url_et_piste(reseau):
    with pytest.raises(ErreurExpliquee) as e:
        vdc.telecharger(URL_78, "téléchargement")
    assert "HTTP 404" in str(e.value) and URL_78 in str(e.value) and "renommé" in e.value.piste


def test_aucun_fichier_liste_les_noms_trouves():
    ressources = [{"title": "Q_78_1852-1949_RR-T-Vent.csv.gz", "url": "https://x/a.csv.gz"}]
    with pytest.raises(ErreurExpliquee) as e:
        vdc.lister_fichiers(ressources, "78", DEBUT, FIN)
    assert "Q_78_1852-1949" in str(e.value) and "MOTIF_RESSOURCE" in e.value.piste


def test_station_absente_liste_les_postes(reseau):
    reseau[URL_78] = fichier_gz(["78000001"])
    with pytest.raises(ErreurExpliquee) as e:
        vdc.lire_station([URL_78], "78621001", DEBUT, FIN)
    assert "78000001" in str(e.value) and "numero_poste" in e.value.piste


def test_fichier_corrompu(reseau):
    reseau[URL_78] = b"<html>erreur</html>"
    with pytest.raises(ErreurExpliquee) as e:
        vdc.lire_station([URL_78], "78621001", DEBUT, FIN)
    assert "illisible" in str(e.value) and "<html>" in str(e.value)


def test_programme_complet_avec_une_station_en_echec(reseau, monkeypatch, tmp_path, capsys):
    """8 stations : seule Trappes a des données ; les 7 autres échouent sans bloquer Trappes."""
    excel = tmp_path / "hypotheses.xlsx"
    shutil.copy(vdc.SOURCE_EXCEL, excel)
    monkeypatch.setattr(vdc, "SOURCE_EXCEL", str(excel))
    monkeypatch.setattr(vdc, "SORTIE_CSV", str(tmp_path / "seuils.csv"))
    monkeypatch.setattr(vdc, "DANS_GITHUB", True)
    monkeypatch.setattr(vdc, "RESUME_GITHUB", str(tmp_path / "resume.md"))
    reseau[vdc.API_JEU_QUOTIDIEN] = json.dumps(
        {"resources": [{"title": os.path.basename(URL_78), "url": URL_78}]}).encode()
    reseau[URL_78] = fichier_gz(["78621001"])

    with pytest.raises(SystemExit) as fin:
        vdc.main()
    assert fin.value.code == 1
    sortie = capsys.readouterr().out
    assert "::error title=H1b Nancy-Essey::" in sortie          # annotation GitHub
    csv = pd.read_csv(tmp_path / "seuils.csv", sep=";", dtype={"numero_poste": str})
    assert list(csv["numero_poste"]) == ["78621001"] and csv["sdeb"].iloc[0] == 20.0
    resume = (tmp_path / "resume.md").read_text(encoding="utf-8")
    assert "| H1a | Trappes |" in resume and "échec" in resume
