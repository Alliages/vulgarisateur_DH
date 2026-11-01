"""① ANALYSER — page d'accueil : cartes, année zoomable, semaine et journée les plus chaudes."""

import numpy as np
import pandas as pd
import streamlit as st

from calcul.analyse import jour_le_plus_chaud, occupation_affichee, semaine_la_plus_chaude, tranche
from calcul.format_fr import date_longue, periode_longue
from calcul.hypotheses import valeur
from config.reglages import CRITERES_JOURNEE_TEXTE, CRITERES_SEMAINE_TEXTE, LIBELLES_CRITERE_SEMAINE
from interface import graphiques_analyse as ga
from interface.cartes import cartes
from interface.composants import bandeau_hypotheses
from interface.graphiques_communs import afficher as afficher_graphique

# ============================================================
# PARAMÈTRES
# ============================================================
LEGENDE_PERIODE = "courbe rouge : température · trait gris : seuil · barres : DH de chaque heure"
LEGENDE_ABSENCE = " · fond gris : absents (scénario RE2020)"


def fenetre_ete(serie, hyp):
    """Fenêtre de zoom par défaut (été), bornée à la série."""
    an = serie.horodatage[len(serie.horodatage) // 2].year
    debut = pd.Timestamp(f"{an}-{valeur(hyp, 'ete_debut')}")
    fin = pd.Timestamp(f"{an}-{valeur(hyp, 'ete_fin')} 23:00")
    if fin < serie.horodatage[0] or debut > serie.horodatage[-1]:
        return None
    return max(debut, serie.horodatage[0]), min(fin, serie.horodatage[-1])


def source(serie):
    return serie.meta.get("source", "")


def afficher(analyse, resultats, reglage, hyp, aller_methode):
    cartes(resultats, hyp)
    bandeau_hypotheses(reglage, analyse, hyp, LIBELLES_CRITERE_SEMAINE, aller_methode)

    s = analyse.serie
    avec_annee = not s.meta.get("periode", "").startswith("année type")
    afficher_graphique(ga.serie_annuelle(analyse, reglage["lignes"], fenetre_ete(s, hyp), source(s),
                                         valeur(hyp, "seuil_nuit_tropicale"), valeur(hyp, "seuil_nuit_tres_chaude"),
                                         int(valeur(hyp, "nuit_debut")), int(valeur(hyp, "nuit_fin"))))

    col_s, col_j = st.columns([2, 1])
    n = int(valeur(hyp, "semaine_jours"))
    debut = semaine_la_plus_chaude(analyse, reglage["critere_semaine"], n)
    with col_s:
        if debut is None:
            st.info(f"Semaine la plus chaude : il faut au moins {n} jours complets.")
        else:
            t, seuil, dh, x = tranche(analyse, debut, 24 * n)
            fin = debut + pd.Timedelta(days=n - 1)
            titre = f"Semaine la plus chaude · {periode_longue(debut, fin, avec_annee)} · {np.sum(dh):.0f} °C.h"
            sous = (f"Critère : {CRITERES_SEMAINE_TEXTE[reglage['critere_semaine']].format(n=n)}<br>{LEGENDE_PERIODE}"
                    + (LEGENDE_ABSENCE if reglage["occupation"] else ""))
            afficher_graphique(ga.courbe_dh(t, seuil, dh, x, titre, sous, "semaine",
                                            occupation_affichee(x, reglage["occupation"]), source(s), legende=False))
    d = jour_le_plus_chaud(analyse, reglage["critere_journee"])
    with col_j:
        if d is not None:
            t, seuil, dh, x = tranche(analyse, d, 24)
            # colonne étroite : titre sur deux lignes, légende commune avec la semaine (mêmes couleurs)
            titre = f"Journée la plus chaude · {np.sum(dh):.0f} °C.h<br>{date_longue(d, avec_annee)}"
            sous = f"Critère : {CRITERES_JOURNEE_TEXTE[reglage['critere_journee']]}<br>mêmes couleurs que la semaine"
            afficher_graphique(ga.courbe_dh(t, seuil, dh, x, titre, sous, "jour",
                                            occupation_affichee(x, reglage["occupation"]), "", legende=False))
    for a in s.avertissements:
        st.caption(f"⚠ {a}")
