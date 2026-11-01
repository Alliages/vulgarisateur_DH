"""Température moyenne nocturne : moyenne des heures de nuit de l'été (heures de nuit des hypothèses)."""

import numpy as np

from calcul.analyse import par_mois
from calcul.indicateurs._communs import heures_de_nuit, periode_des_moyennes
from calcul.indicateurs.base import Indicateur, Resultat


def calculer(a, reglage, hyp):
    masque = a.est_ete & a.est_nuit
    return Resultat(float(a.serie.t[masque].mean()), f"{periode_des_moyennes(a, hyp)} · nuits {heures_de_nuit(hyp)}")


def profil(a, hyp):
    return {"type": "ligne", "valeurs": par_mois(a, np.where(a.est_nuit, a.serie.t, np.nan), "mean")}


INDICATEUR = Indicateur(id="t_moyenne_nuit", calculer=calculer, profil=profil, teinte="nuit", icone="thermometre")
