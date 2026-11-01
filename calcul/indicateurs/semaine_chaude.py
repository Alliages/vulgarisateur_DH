"""Semaine la plus chaude : DH cumulés sur les jours consécutifs les plus chauds, selon le critère du réglage."""

import pandas as pd

from calcul.analyse import semaine_la_plus_chaude
from calcul.format_fr import jour_mois_court
from calcul.hypotheses import valeur
from calcul.indicateurs.base import Indicateur, Resultat


def calculer(a, reglage, hyp):
    n = int(valeur(hyp, "semaine_jours"))
    debut = semaine_la_plus_chaude(a, reglage["critere_semaine"], n)
    if debut is None:
        return Resultat(None, f"moins de {n} jours complets")
    fin = debut + pd.Timedelta(days=n - 1)
    return Resultat(float(a.jours.loc[debut:fin, "dh"].sum()), f"{jour_mois_court(debut)} → {jour_mois_court(fin)}",
                    {"debut": debut, "fin": fin})


INDICATEUR = Indicateur(id="semaine_chaude", calculer=calculer, teinte="chaud", icone="calendrier")
