"""① ANALYSER — page d'accueil : cartes, année zoomable, semaine et journée les plus chaudes."""

import numpy as np
import pandas as pd
import streamlit as st

from calcul.hypotheses import masque_occupation, valeur
from calcul.indicateurs import jour_le_plus_chaud, semaine_la_plus_chaude
from config.reglages import LIBELLES_CRITERE_JOURNEE, LIBELLES_CRITERE_SEMAINE
from interface import graphiques as g
from interface.composants import bandeau_hypotheses, cartes
from interface.format_fr import date_longue, periode_longue

# ============================================================
# PARAMÈTRES
# ============================================================
CONFIG_PLOTLY = g.CONFIG_PLOTLY          # zoom à la molette + mois et virgule en français
CRITERES_SEMAINE_TEXTE = {"moyenne": "température moyenne la plus élevée sur 7 jours",
                          "moyenne_max": "moyenne des maximales la plus élevée sur 7 jours",
                          "pointe_max": "semaine centrée sur la pointe de chaleur"}
CRITERES_JOURNEE_TEXTE = {"moyenne": "température moyenne la plus élevée", "max": "température maximale la plus élevée"}


def fenetre_ete(serie, hyp):
    """Fenêtre de zoom par défaut (été), bornée à la série."""
    an = serie.horodatage[len(serie.horodatage) // 2].year
    debut = pd.Timestamp(f"{an}-{valeur(hyp, 'ete_debut')}")
    fin = pd.Timestamp(f"{an}-{valeur(hyp, 'ete_fin')} 23:00")
    if fin < serie.horodatage[0] or debut > serie.horodatage[-1]:
        return None
    return max(debut, serie.horodatage[0]), min(fin, serie.horodatage[-1])


def tranche(analyse, debut, nb_heures):
    """Températures, seuil, DH, horodatage et occupation d'une période."""
    s = analyse.serie
    i0 = s.horodatage.get_indexer([debut])[0]
    sl = slice(i0, i0 + nb_heures)
    return s.t[sl], analyse.seuil[sl], analyse.dh_h[sl], s.horodatage[sl]


def occupation_tranche(x, reglage):
    """Masque d'occupation (scénario RE2020) affiché seulement si l'option « en occupation » est active."""
    if not reglage["occupation"]:
        return None
    return masque_occupation(x.hour.to_numpy(), x.dayofweek.to_numpy())


def source(serie):
    return serie.meta.get("source", "")


def afficher(analyse, resultats, reglage, hyp, aller_methode):
    cartes(resultats, hyp)
    bandeau_hypotheses(reglage, analyse, hyp, LIBELLES_CRITERE_SEMAINE, aller_methode)

    s = analyse.serie
    avec_annee = not s.meta.get("periode", "").startswith("année type")
    st.plotly_chart(g.serie_annuelle(analyse, reglage["lignes"], fenetre_ete(s, hyp), source(s),
                                     valeur(hyp, "seuil_nuit_tropicale"), valeur(hyp, "seuil_nuit_tres_chaude"),
                                     int(valeur(hyp, "nuit_debut")), int(valeur(hyp, "nuit_fin"))),
                    width="stretch", config=CONFIG_PLOTLY, theme=None)

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
            sous = (f"Critère : {CRITERES_SEMAINE_TEXTE[reglage['critere_semaine']]}<br>courbe rouge : température · "
                    f"trait gris : seuil · barres : DH de chaque heure"
                    + (" · fond gris : absents (scénario RE2020)" if reglage["occupation"] else ""))
            st.plotly_chart(g.courbe_dh(t, seuil, dh, x, titre, sous, "semaine", occupation_tranche(x, reglage), source(s),
                                        legende=False),
                            width="stretch", config=CONFIG_PLOTLY, theme=None)
    d = jour_le_plus_chaud(analyse, reglage["critere_journee"])
    with col_j:
        if d is not None:
            t, seuil, dh, x = tranche(analyse, d, 24)
            # colonne étroite : titre sur deux lignes, légende commune avec la semaine (mêmes couleurs)
            titre = f"Journée la plus chaude · {np.sum(dh):.0f} °C.h<br>{date_longue(d, avec_annee)}"
            sous = f"Critère : {CRITERES_JOURNEE_TEXTE[reglage['critere_journee']]}<br>mêmes couleurs que la semaine"
            st.plotly_chart(g.courbe_dh(t, seuil, dh, x, titre, sous, "jour", occupation_tranche(x, reglage), "",
                                        legende=False),
                            width="stretch", config=CONFIG_PLOTLY, theme=None)
    for a in s.avertissements:
        st.caption(f"⚠ {a}")
