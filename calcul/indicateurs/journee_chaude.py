"""Journée la plus chaude : DH de la journée (minuit à minuit, heure légale) choisie selon le critère du réglage."""

from calcul.analyse import jour_le_plus_chaud
from calcul.format_fr import jour_mois_court
from calcul.indicateurs.base import Indicateur, Resultat


def calculer(a, reglage, hyp):
    d = jour_le_plus_chaud(a, reglage["critere_journee"])
    if d is None:
        return Resultat(None, "aucune journée complète")
    j = a.jours.loc[d]
    return Resultat(float(j["dh"]), f"{jour_mois_court(d)} · Tmoy {j['tmoy']:.0f} · Tmax {j['tmax']:.0f} °C", {"jour": d})


INDICATEUR = Indicateur(id="journee_chaude", calculer=calculer, teinte="chaud", icone="soleil")
