"""③ CRÉER — journée ou semaine type (formules de l'Excel), utilisable comme fichier C."""

import pandas as pd
import streamlit as st

from calcul import generateur
from calcul.indicateurs import semaine_la_plus_chaude
from calcul.hypotheses import masque_occupation
from calcul.serie import serie_depuis_generateur
from interface.format_fr import date_longue, periode_longue
from interface import graphiques as g
from interface.composants import cartes
from interface.onglet_analyser import CONFIG_PLOTLY
from interface.outils import PYARROW_DISPONIBLE

# ============================================================
# PARAMÈTRES
# ============================================================
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
# Semaine « juin 2026 » de l'Excel Vulgarisation_DH CANICULE 2026 : (minuit, pic haut, pic bas)
SEMAINE_EXEMPLE = [(28, 34.8, 19), (29, 36.2, 23.7), (29, 36.8, 23.6), (29.4, 38.7, 25.2),
                   (30.5, 38.4, 25.2), (30.5, 35.4, 24), (26, 33, 21.5)]
DEBUT_DEFAUT = pd.Timestamp("2026-06-22")          # un lundi
COLONNES = ["Jour", "T° minuit", "T° pic haut", "T° pic bas", "Heure du pic", "Courbe"]
LARGEURS_FORMULAIRE = [1.1, 1, 1, 1, 1, 1]          # formulaire de secours (sans pyarrow)


def _tableau_defaut(nb_jours):
    return pd.DataFrame([[JOURS[i % 7], a, b, c, "15h", "lissée"] for i, (a, b, c) in
                         enumerate(SEMAINE_EXEMPLE[:nb_jours])], columns=COLONNES)


def _depuis_semaine_chaude(analyse_a, reglage, nb_jours):
    """Préremplit avec la semaine (ou la journée) la plus chaude du fichier de l'onglet Analyser."""
    debut = semaine_la_plus_chaude(analyse_a, reglage["critere_semaine"], 7)
    if debut is None:
        return None
    s = analyse_a.serie
    df = pd.DataFrame({"t": s.t}, index=s.horodatage)
    lignes = []
    for k in range(nb_jours):
        d = debut + pd.Timedelta(days=k)
        jour = df.loc[d:d + pd.Timedelta(hours=23), "t"]
        lignes.append([JOURS[d.dayofweek], round(float(jour.iloc[0]), 1), round(float(jour.max()), 1),
                       round(float(jour.min()), 1), "15h", "lissée"])
    return pd.DataFrame(lignes, columns=COLONNES)


def _tableau_editable(df, cle):
    """Tableau éditable Streamlit (nécessite pyarrow)."""
    return st.data_editor(
        df, hide_index=True, width="stretch", key=cle, disabled=["Jour"],
        column_config={
            "T° minuit": st.column_config.NumberColumn(format="%.1f °C", step=0.5),
            "T° pic haut": st.column_config.NumberColumn(format="%.1f °C", step=0.5),
            "T° pic bas": st.column_config.NumberColumn(format="%.1f °C", step=0.5),
            "Heure du pic": st.column_config.SelectboxColumn(options=list(generateur.H_PIC)),
            "Courbe": st.column_config.SelectboxColumn(options=list(generateur.COURBES))})


def _formulaire(df, cle):
    """Formulaire de secours, une ligne par jour, sans pyarrow (champs numériques et listes)."""
    for c, t in zip(st.columns(LARGEURS_FORMULAIRE), COLONNES):
        c.caption(t)
    pics, courbes = list(generateur.H_PIC), list(generateur.COURBES)
    lignes = []
    for i, r in df.reset_index(drop=True).iterrows():
        cols = st.columns(LARGEURS_FORMULAIRE, vertical_alignment="center")
        cols[0].markdown(f"**{r['Jour']}**")
        temperatures = [cols[k].number_input(COLONNES[k], value=float(r[COLONNES[k]]), step=0.5, format="%.1f",
                                             key=f"{cle}_{i}_{k}", label_visibility="collapsed") for k in (1, 2, 3)]
        pic = cols[4].selectbox("Heure du pic", pics, index=pics.index(r["Heure du pic"]), key=f"{cle}_{i}_pic",
                                label_visibility="collapsed")
        courbe = cols[5].selectbox("Courbe", courbes, index=courbes.index(r["Courbe"]), key=f"{cle}_{i}_courbe",
                                   label_visibility="collapsed")
        lignes.append([r["Jour"], *temperatures, pic, courbe])
    return pd.DataFrame(lignes, columns=COLONNES)


def afficher(analyse_a, reglage, hyp, definitions, analyser_serie, calculer):
    mode = st.radio("Créer", ["Semaine", "Journée"], horizontal=True, key="creer_mode")
    nb = 7 if mode == "Semaine" else 1
    if st.session_state.get("creer_nb") != nb:
        st.session_state["creer_tableau"] = _tableau_defaut(nb)
        st.session_state["creer_nb"] = nb
    if st.button(f"↻ Préremplir avec la période la plus chaude de « {analyse_a.serie.libelle} »"):
        t = _depuis_semaine_chaude(analyse_a, reglage, nb)
        if t is not None:
            st.session_state["creer_tableau"] = t
            st.session_state["creer_version"] = st.session_state.get("creer_version", 0) + 1   # rafraîchit la saisie
    version = st.session_state.get("creer_version", 0)
    if PYARROW_DISPONIBLE:
        tableau = _tableau_editable(st.session_state["creer_tableau"], f"editeur_{nb}_{version}")
    else:
        st.caption("Saisie simplifiée : le tableau éditable de Streamlit a besoin de pyarrow, introuvable ici "
                   "(voir README, installation sous Windows).")
        tableau = _formulaire(st.session_state["creer_tableau"], f"form_{nb}_{version}")

    params = [dict(t0=r["T° minuit"], tmax=r["T° pic haut"], tmin=r["T° pic bas"], pic=r["Heure du pic"],
                   courbe=r["Courbe"]) for _, r in tableau.iterrows()]
    t = generateur.plusieurs_jours(params, graine=1)
    serie_c = serie_depuis_generateur(t, str(DEBUT_DEFAUT.date()), f"{mode.lower()} créée")
    analyse_c = analyser_serie(serie_c)
    cartes(calculer(analyse_c), hyp)
    x = serie_c.horodatage
    occupe = masque_occupation(x.hour.to_numpy(), x.dayofweek.to_numpy()) if reglage["occupation"] else None
    titre = f"{mode} créée · {periode_longue(x[0], x[-1].normalize()) if nb > 1 else date_longue(x[0])} · {analyse_c.dh_h.sum():.0f} °C.h"
    st.plotly_chart(g.courbe_dh(t, analyse_c.seuil, analyse_c.dh_h, x, titre,
                                "Courbe générée avec les formules de l'Excel Vulgarisation_DH · barres : DH de chaque heure",
                                "semaine" if nb > 1 else "jour", occupe), width="stretch", config=CONFIG_PLOTLY, theme=None)
    if analyse_c.message_methode:
        st.caption(f"⚠ {analyse_c.message_methode}")
    if st.button("+ Comparer comme fichier C", type="primary"):
        st.session_state["fichier_C"] = serie_c
        st.success("Fichier C disponible dans l'onglet Comparer.")
