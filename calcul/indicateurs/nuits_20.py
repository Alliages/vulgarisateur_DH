"""Nuits tropicales : nuits où la température ne descend pas sous le seuil tropical (20 °C, Météo-France)."""

from calcul.hypotheses import valeur
from calcul.indicateurs._communs import nuits_au_dessus, profil_nuits_par_mois
from calcul.indicateurs.base import Indicateur

# ============================================================
# PARAMÈTRES
# ============================================================
SEUIL = "seuil_nuit_tropicale"           # identifiant de l'hypothèse


def calculer(a, reglage, hyp):
    return nuits_au_dessus(a, valeur(hyp, SEUIL))


def profil(a, hyp):
    return profil_nuits_par_mois(a, valeur(hyp, SEUIL))


INDICATEUR = Indicateur(id="nuits_20", calculer=calculer, profil=profil, teinte="nuit", icone="lune")
