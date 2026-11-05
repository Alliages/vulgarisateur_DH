"""Colonne « Ampleur » de l'onglet Comparer : registre, calcul de la jauge, cellule."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from calcul.analyse import analyser
from calcul.hypotheses import charger_hypotheses, charger_indicateurs
from calcul.indicateurs import REGISTRE, Indicateur, calculer_indicateurs
from calcul.serie import charger_catalogue, charger_serie
from config.charte import COULEURS_BAISSE, COULEURS_HAUSSE
from config.reglages import AMPLEUR_INDICATEURS, REGLAGE_RE2020
from interface.composants import ampleur, cellule_ampleur


def test_registre_porte_la_table_centrale():
    assert set(AMPLEUR_INDICATEURS) <= set(REGISTRE)
    assert (REGISTRE["dh"].mode_ampleur, REGISTRE["dh"].seuil_ampleur) == ("relatif", 50)
    assert (REGISTRE["t_moyenne"].mode_ampleur, REGISTRE["t_moyenne"].seuil_ampleur) == ("absolu", 3)


def test_valeurs_par_defaut_sans_attributs():
    assert (REGISTRE["journee_chaude"].mode_ampleur, REGISTRE["journee_chaude"].seuil_ampleur) == ("relatif", 100)


def test_attributs_invalides_refuses():
    with pytest.raises(ValueError):
        Indicateur(id="x", calculer=print, mode_ampleur="autre")
    with pytest.raises(ValueError):
        Indicateur(id="x", calculer=print, seuil_ampleur=0)


@pytest.mark.parametrize("va, vb, mode, seuil, remplissage, niveau", [
    (100, 103, "relatif", 50, 0.06, 0),
    (100, 170, "relatif", 100, 0.70, 2),
    (100, 69, "relatif", 50, 0.62, 1),
    (1, 3, "absolu", 5, 0.40, 1),
    (0, 9, "absolu", 5, 1.0, 2),
])
def test_remplissage_et_niveau(va, vb, mode, seuil, remplissage, niveau):
    a = ampleur(va, vb, vb - va, mode, seuil)
    assert a["remplissage"] == pytest.approx(remplissage) and a["niveau"] == niveau


def test_garde_fou_reference_nulle():
    assert ampleur(0, 5, 5, "relatif", 100) is None
    assert "n/a" in cellule_ampleur(0, 5, 5, "relatif", 100, "h")
    assert ampleur(0, 5, 5, "absolu", 10)["remplissage"] == 0.5


def test_sens_et_couleurs():
    assert COULEURS_HAUSSE[2] in cellule_ampleur(100, 200, 100, "relatif", 100, "h")
    assert COULEURS_BAISSE[1] in cellule_ampleur(100, 50, -50, "relatif", 100, "h")


def test_ecart_nul_gris_et_jauge_vide():
    c = cellule_ampleur(5, 5, 0, "absolu", 3, "°C")
    assert "width:0%" in c and "discret" in c


def test_mise_en_forme():
    c = cellule_ampleur(19.2, 21.1, 1.9, "absolu", 3, "°C")
    assert "+1,9&nbsp;°C" in c and 'class="valeur discret"' in c and '"seuil">3&nbsp;°C' in c
    c = cellule_ampleur(100, 170, 70, "relatif", 100, "h")
    assert "+70&nbsp;%" in c and 'class="valeur"' in c and '"seuil">100&nbsp;%' in c
    assert cellule_ampleur(None, 3, None, "relatif", 100, "h") == "—"


def test_exemple_h1a_th_d_contre_tracc():
    """Cas de vérification du cahier des charges (TRACC +2,7 °C vague de chaleur)."""
    hyp, defs = charger_hypotheses(), charger_indicateurs()
    cat = charger_catalogue().set_index("id")

    def valeurs(i):
        ligne = cat.loc[i].to_dict()
        ligne["id"] = i
        res = calculer_indicateurs(analyser(charger_serie(ligne), REGLAGE_RE2020, hyp), REGLAGE_RE2020, hyp, defs)
        return {d["id"]: (r.valeur, int(d.get("decimales", 0) or 0)) for d, r in res}

    a, b = valeurs("H1a_th_d"), valeurs("H1a_tracc_plus2_7_vdc")

    def jauge(i):
        (va, dec), (vb, _) = a[i], b[i]
        ind = REGISTRE[i]
        return ampleur(va, vb, round(round(vb, dec) - round(va, dec), dec), ind.mode_ampleur, ind.seuil_ampleur)

    attendu = {"dh": (3, 0.06, 0), "heures_chaudes": (70, 0.70, 2), "dh_nuit": (-31, 0.62, 1),
               "nuits_24": (2, 0.40, 1), "t_moyenne": (1.9, 0.63, 1)}
    for i, (valeur, remplissage, niveau) in attendu.items():
        j = jauge(i)
        assert j["valeur"] == pytest.approx(valeur, abs=0.5) and j["niveau"] == niveau, i
        assert j["remplissage"] == pytest.approx(remplissage, abs=0.015), i
