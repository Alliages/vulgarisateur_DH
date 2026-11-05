"""Vagues de chaleur (calcul/vagues_chaleur.py) et indicateurs vdc_severite / vdc_nombre."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import pytest

import calcul.vagues_chaleur as vc
from calcul.analyse import analyser
from calcul.hypotheses import charger_hypotheses
from calcul.indicateurs import REGISTRE
from calcul.serie import charger_catalogue, charger_serie
from config.reglages import REGLAGE_RE2020
from interface import graphiques_vagues as gv

# ============================================================
# DONNÉES
# ============================================================
SPIC, SDEB, SINT = 25.3, 23.4, 22.4                      # seuils de l'exemple des slides
HYP = charger_hypotheses()
CAT = charger_catalogue().set_index("id")
SEUILS_H1A = ({"zone": "H1a", "station": "Trappes", "numero_poste": "78621001", "statut": "calculé",
               "spic": 24.0, "sdeb": 22.0, "sint": 21.0},)  # seuils fictifs, le temps que l'Action tourne


def tm(valeurs, debut="2003-08-01"):
    return pd.Series(valeurs, index=pd.date_range(debut, periods=len(valeurs), freq="D"), dtype=float)


def detecter(valeurs, **kw):
    return vc.detecter_vagues(tm(valeurs), SPIC, SDEB, SINT, **kw)


def analyse(identifiant):
    ligne = CAT.loc[identifiant].to_dict() | {"id": identifiant}
    return analyser(charger_serie(ligne), REGLAGE_RE2020, HYP)


# ============================================================
# DÉTECTION
# ============================================================

def test_exemple_des_slides():
    """J2 → J6 : un jour sous Sdeb (J5) compte dans la durée, pas dans la sévérité ; J7 < Sint arrête."""
    (v,) = detecter([21.5, 24.5, 26.5, 28.0, 23.0, 24.5, 21.0])
    assert v.debut == pd.Timestamp("2003-08-02") and v.fin == pd.Timestamp("2003-08-06")
    assert v.duree == 5 and v.intensite == 28.0 and v.severite == pytest.approx(9.9)


def test_trois_jours_sous_sdeb_coupent_la_vague():
    vagues = detecter([24, 26, 24, 23, 23, 23, 24, 26, 24])
    assert [(v.duree, round(v.severite, 1)) for v in vagues] == [(3, 3.8), (3, 3.8)]
    assert len(detecter([24, 26, 24, 23, 23, 24, 26, 24])) == 1          # 2 jours sous Sdeb : même vague


def test_jours_sous_sdeb_en_fin_de_vague_non_comptes():
    (v,) = detecter([24, 26, 24, 23, 22])
    assert v.duree == 3 and v.fin == pd.Timestamp("2003-08-03")


def test_duree_minimale_et_jour_manquant():
    assert detecter([22, 26, 22]) == []                                   # pic isolé : 1 jour
    assert detecter([24, 26, np.nan, 26, 24]) == []                       # le trou coupe : 2 jours + 2 jours
    assert len(detecter([24, 26, 24, np.nan])) == 1


def test_pas_de_vague_sans_pic():
    assert detecter([24, 25, 25.2, 24, 25]) == []


def test_variante_scolaire():
    vagues = vc.detecter_vagues(tm([24, 26, 24, 26, 24], debut="2003-07-08"), SPIC, SDEB, SINT)
    r = vc.hors_periode(vagues, SDEB, "07-10", "08-31")                  # garde le 8 et le 9 juillet
    assert r["nombre"] == 1 and r["duree"] == 2 and r["severite"] == pytest.approx(0.6 + 2.6)
    assert vc.hors_periode(vagues, SDEB, "07-01", "08-31")["nombre"] == 0


# ============================================================
# SEUILS DE LA STATION
# ============================================================

def test_seuils_absents(tmp_path):
    assert vc.charger_seuils.__wrapped__(str(tmp_path / "absent.csv")) == ()


def test_seuils_incomplets_ignores(tmp_path):
    f = tmp_path / "seuils.csv"
    f.write_text("zone;station;numero_poste;spic;sdeb;sint;statut\nH1a;Trappes;78621001;24;22;21;calculé\n"
                 "H1b;Nancy;54526001;24;22;21;incomplet\n", encoding="utf-8")
    assert [s["zone"] for s in vc.charger_seuils.__wrapped__(str(f))] == ["H1a"]


def test_choix_de_la_station():
    assert vc.seuils_du_fichier({"famille": "RE2020", "zone": "H1a"}, SEUILS_H1A)["station"] == "Trappes"
    assert vc.seuils_du_fichier({"famille": "TRACC", "zone": "H1a"}, SEUILS_H1A)["station"] == "Trappes"
    obs = {"famille": "Observations", "zone": "H1a", "description": "observations horaires, station 78621001"}
    assert vc.seuils_du_fichier(obs, SEUILS_H1A)["station"] == "Trappes"
    autre = {"famille": "Observations", "zone": "H1a", "description": "station 75114001"}   # Paris-Montsouris
    assert vc.seuils_du_fichier(autre, SEUILS_H1A) is None
    assert vc.seuils_du_fichier({"zone": "import"}, SEUILS_H1A) is None


# ============================================================
# INDICATEURS
# ============================================================

def test_indicateurs_sans_seuils(monkeypatch):
    monkeypatch.setattr(vc, "charger_seuils", lambda: ())
    a = analyse("H1a_th_d")
    for i in ("vdc_severite", "vdc_nombre"):
        r = REGISTRE[i].calculer(a, REGLAGE_RE2020, HYP)
        assert r.valeur is None and "non calculés" in r.detail
        assert REGISTRE[i].profil(a, HYP) is None


def test_indicateurs_avec_seuils(monkeypatch):
    monkeypatch.setattr(vc, "charger_seuils", lambda: SEUILS_H1A)
    a = analyse("H1a_th_d")
    sev = REGISTRE["vdc_severite"].calculer(a, REGLAGE_RE2020, HYP)
    nb = REGISTRE["vdc_nombre"].calculer(a, REGLAGE_RE2020, HYP)
    vagues = sev.info["vagues"]
    assert nb.valeur == len(vagues) >= 1 and sev.valeur > 0
    assert sev.valeur == pytest.approx(sum(v.severite for v in vagues))
    assert "Trappes" in sev.detail and "jours" in nb.detail
    p = REGISTRE["vdc_severite"].profil(a, HYP)
    assert p["type"] == "barres" and p["valeurs"].sum() == pytest.approx(sev.valeur)


# ============================================================
# GRAPHIQUE (onglets Analyser et Comparer)
# ============================================================

def test_graphique_avec_seuils(monkeypatch):
    monkeypatch.setattr(vc, "charger_seuils", lambda: SEUILS_H1A)
    a = analyse("H1a_th_d")
    ete = (pd.Timestamp("2018-06-01"), pd.Timestamp("2018-09-30 23:00"))
    fenetre, bornes = gv.echelle((a,), HYP, ete, 2018)
    assert fenetre[0] <= ete[0] and fenetre[1] >= ete[1] and bornes[0] < bornes[1]
    fig = gv.vagues_chaleur.__wrapped__(a, HYP, "Fichier A", "#f05d5e", fenetre, bornes)
    assert "Vagues de chaleur · Fichier A" in fig.layout.title.text
    assert tuple(fig.layout.yaxis.range) == bornes


def _seuils_annotes(fig):
    return [x.text for x in fig.layout.annotations if x.text.startswith(("Spic", "Sdeb", "Sint"))]


def test_graphique_compare_seuils_communs_ou_non(monkeypatch):
    autre = ({**SEUILS_H1A[0], "zone": "H3", "station": "Marignane", "spic": 29.0, "sdeb": 27.0, "sint": 26.0},)
    monkeypatch.setattr(vc, "charger_seuils", lambda: SEUILS_H1A + autre)
    a, tracc, h3 = analyse("H1a_th_d"), analyse("H1a_tracc_plus4_0_vdc"), analyse("H3_th_d")
    ete = (pd.Timestamp("2018-06-01"), pd.Timestamp("2018-09-30 23:00"))
    fenetre, bornes = gv.echelle((a, tracc), HYP, ete, 2018)
    fig = gv.vagues_comparees.__wrapped__(a, tracc, HYP, "A", "B", fenetre, bornes, 2018)
    assert len(_seuils_annotes(fig)) == 3                  # même station : une seule série de seuils
    assert [t.name for t in fig.data if t.showlegend] == ["A", "B"]
    fenetre, bornes = gv.echelle((a, h3), HYP, ete, 2018)
    fig = gv.vagues_comparees.__wrapped__(a, h3, HYP, "A", "B", fenetre, bornes, 2018)
    assert len(_seuils_annotes(fig)) == 6                  # deux stations : les seuils de chacune


def test_graphique_compare_un_seul_fichier_avec_seuils(monkeypatch):
    monkeypatch.setattr(vc, "charger_seuils", lambda: SEUILS_H1A)
    a, h3 = analyse("H1a_th_d"), analyse("H3_th_d")
    assert gv.sans_seuils(h3) and not gv.sans_seuils(a)
    ete = (pd.Timestamp("2018-06-01"), pd.Timestamp("2018-09-30 23:00"))
    fenetre, bornes = gv.echelle((a, h3), HYP, ete, 2018)
    fig = gv.vagues_comparees.__wrapped__(a, h3, HYP, "A", "B", fenetre, bornes, 2018)
    assert fig.layout.title.text.startswith("<b>Vagues de chaleur · A</b>") and len(_seuils_annotes(fig)) == 3


def test_graphique_sans_seuils(monkeypatch):
    monkeypatch.setattr(vc, "charger_seuils", lambda: ())
    a = analyse("H1a_th_d")
    assert gv.echelle((a,), HYP, None)[1] is None
    assert gv.vagues_chaleur.__wrapped__(a, HYP, "Fichier A", "#f05d5e", None, None) is None


def test_etiquettes_de_seuils_sans_chevauchement():
    px, valeurs = 12, [27.6, 27.1, 26.6]
    positions = [v * px + d for v, d in zip(valeurs, gv._decalages(valeurs, px))]
    assert all(haut - bas >= gv.PX_MIN_ETIQUETTES for haut, bas in zip(positions, positions[1:]))
