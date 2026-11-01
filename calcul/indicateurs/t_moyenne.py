"""Température moyenne : moyenne des heures de l'été (toute la série pour un relevé qui ne couvre pas l'été)."""

from calcul.analyse import par_mois
from calcul.indicateurs._communs import periode_des_moyennes
from calcul.indicateurs.base import Indicateur, Resultat


def calculer(a, reglage, hyp):
    return Resultat(float(a.serie.t[a.est_ete].mean()), periode_des_moyennes(a, hyp))


def profil(a, hyp):
    return {"type": "ligne", "valeurs": par_mois(a, a.serie.t, "mean")}


INDICATEUR = Indicateur(id="t_moyenne", calculer=calculer, profil=profil, teinte="moyenne", icone="thermometre")
