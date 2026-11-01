"""Nuits très chaudes : nuits où la température ne descend pas sous 24 °C (seuil proposé, source à préciser)."""

from calcul.hypotheses import valeur
from calcul.indicateurs._communs import nuits_au_dessus, profil_nuits_par_mois
from calcul.indicateurs.base import Indicateur

# ============================================================
# PARAMÈTRES
# ============================================================
SEUIL = "seuil_nuit_tres_chaude"         # identifiant de l'hypothèse


def calculer(a, reglage, hyp):
    return nuits_au_dessus(a, valeur(hyp, SEUIL))


def profil(a, hyp):
    return profil_nuits_par_mois(a, valeur(hyp, SEUIL))


INDICATEUR = Indicateur(id="nuits_24", calculer=calculer, profil=profil, teinte="nuit", icone="lune")
