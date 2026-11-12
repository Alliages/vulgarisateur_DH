"""Tests de l'import d'un fichier par l'utilisateur : formats acceptés, erreurs claires, nom nettoyé."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from calcul.serie import AVERTISSEMENT_JOUR_MOIS, LONGUEUR_NOM_MAX, lire_fichier_importe, nom_affichable

# ============================================================
# DONNÉES
# ============================================================
ANNEE = b"heure;T\n" + b"\n".join(b"%d;%d,5" % (h, 15 + h % 10) for h in range(8760))
RELEVE_ISO = b"date;heure;T\n2026-06-01;00:00;20\n2026-06-01;01:00;21,5\n2026-06-02;00:00;22\n"
RELEVE_FR = b"date;heure;T\n01/06/2026;00:00;20\n01/06/2026;01:00;21,5\n02/06/2026;00:00;22\n"


def _lire(contenu, nom="essai.csv"):
    return lire_fichier_importe(contenu, nom, "légale")


def test_annee_type_et_releve_iso():
    s = _lire(ANNEE)
    assert s.annee_complete and len(s.t) == 8760 and s.t[1] == 16.5
    r = _lire(RELEVE_ISO)
    assert str(r.horodatage[0]) == "2026-06-01 00:00:00" and not r.avertissements


def test_dates_francaises_lues_jour_mois():
    """01/06/2026 = 1er juin (et non 6 janvier), avec un avertissement visible."""
    r = _lire(RELEVE_FR)
    assert (r.horodatage[0].month, r.horodatage[0].day) == (6, 1)
    assert AVERTISSEMENT_JOUR_MOIS in r.avertissements


@pytest.mark.parametrize("contenu, message", [
    (b"", "vide"),
    (b"heure\n" + b"\n".join(b"%d" % h for h in range(8760)), "deux colonnes"),
    (b"heure;T\n0;20\n1;21\n", "8 760 ou 8 784 lignes"),
    (b"heure;T\n" + b"\n".join(b"%d;abc" % h for h in range(8760)), "Température illisible ligne 2"),
    (b"date;heure;T\n31/31/2026;00:00;20\n", "Dates illisibles"),
    (b"heure;T\n" + b"\n".join(b"%d;99" % h for h in range(8760)), "plage plausible"),
])
def test_erreurs_en_francais(contenu, message):
    """Un fichier mal formé est refusé avec un message clair (ValueError), jamais une trace Python."""
    with pytest.raises(ValueError, match=message):
        _lire(contenu)


def test_nom_nettoye():
    assert nom_affichable("C:\\Users\\moi\\releve_paris 2026.csv".replace("\\", "/")) == "releve_paris 2026.csv"
    assert "<" not in nom_affichable("<b>:red[x]</b>") and "[" not in nom_affichable("a[b]c.csv")
    assert len(nom_affichable("a" * 300)) == LONGUEUR_NOM_MAX and nom_affichable("::") == "fichier"


if __name__ == "__main__":
    for nom, f in list(globals().items()):
        if nom.startswith("test_") and nom != "test_erreurs_en_francais":
            f(); print("OK ", nom)


def test_lignes_vides_excel_ignorees():
    """Export Excel : des milliers de lignes « ; » sous les 8 760 lignes de données ne comptent pas (0.9.19)."""
    s = _lire(ANNEE + b"\r\n" + b"\r\n".join([b";"] * 5000) + b"\r\n")
    assert s.annee_complete and len(s.t) == 8760 and s.t[1] == 16.5
    assert any("5 000 lignes vides ignorées" in a for a in s.avertissements)
    assert not _lire(ANNEE).avertissements


def test_trou_de_temperature_non_confondu_avec_ligne_vide():
    """Une heure sans température (mais avec sa date) reste un trou à combler, pas une ligne vide."""
    r = _lire(b"date;heure;T\n2026-06-01;00:00;20\n2026-06-01;01:00;\n2026-06-01;02:00;22\n;\n")
    assert len(r.t) == 3 and r.t[1] == 21 and any("lignes vides" in a for a in r.avertissements)
