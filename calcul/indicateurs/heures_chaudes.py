"""Heures > seuil (28 °C par défaut) : nombre d'heures où la température dépasse le seuil des heures chaudes."""

from calcul.analyse import par_mois
from calcul.hypotheses import valeur
from calcul.indicateurs.base import Indicateur, Resultat


def calculer(a, reglage, hyp):
    seuil = valeur(hyp, "seuil_heures_chaudes")
    etendue = "sur l'année" if a.serie.annee_complete else "sur la série"
    return Resultat(int((a.serie.t > seuil).sum()), f"T > {seuil:g} °C · {etendue}")


def profil(a, hyp):
    return {"type": "barres", "valeurs": par_mois(a, a.serie.t > valeur(hyp, "seuil_heures_chaudes"), "sum")}


INDICATEUR = Indicateur(id="heures_chaudes", calculer=calculer, profil=profil, teinte="chaud", icone="horloge")
