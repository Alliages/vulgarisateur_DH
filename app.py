"""
============================================================
 MÉTÉO ET CHALEUR — point d'entrée Streamlit
============================================================
 Lancement local :  streamlit run app.py
 Onglets : ① Analyser · ② Comparer · ③ Créer · Méthode & sources
 Réglage par défaut : RE2020 (config/reglages.py).
============================================================
"""

import pandas as pd
import streamlit as st

from calcul.hypotheses import charger_hypotheses, charger_indicateurs, remplacer_reperes, valeur
from calcul.indicateurs import analyser, calculer_indicateurs
from calcul.serie import charger_catalogue, charger_serie, lire_fichier_importe
from config.reglages import (FICHIER_DEFAUT, LIBELLES_CRITERE_JOURNEE, LIBELLES_CRITERE_SEMAINE,
                             LIBELLES_METHODE, REGLAGE_RE2020, VERSION)
from export.export import csv_horaire, excel_complet
from interface import onglet_analyser, onglet_comparer, onglet_creer, onglet_methode
from interface.composants import entete, pied

# ============================================================
# PARAMÈTRES
# ============================================================
TITRE_PAGE = "Météo et Chaleur"
ONGLETS = ["①  Analyser", "②  Comparer", "③  Créer jour / semaine", "Méthode & sources"]
CLES_REGLAGE = {"methode": "r_methode", "occupation": "r_occupation",
                "critere_journee": "r_journee", "critere_semaine": "r_semaine"}
BASES_HORAIRES = ["légale", "UTC"]

st.set_page_config(page_title=TITRE_PAGE, page_icon="☀", layout="wide")


# ============================================================
# DONNÉES EN CACHE
# ============================================================

@st.cache_data
def _hypotheses():
    return charger_hypotheses(), charger_indicateurs()


@st.cache_data
def _catalogue():
    return charger_catalogue()


@st.cache_resource
def _serie_enregistree(identifiant):
    hyp, _ = _hypotheses()
    ligne = _catalogue().set_index("id").loc[identifiant].to_dict()
    ligne["id"] = identifiant
    return charger_serie(ligne, int(valeur(hyp, "decalage_heure_ete")))


HYP, DEFINITIONS = _hypotheses()
CATALOGUE = _catalogue()


# ============================================================
# RÉGLAGES (barre latérale)
# ============================================================

def _reinitialiser():
    for cle, cle_widget in CLES_REGLAGE.items():
        st.session_state[cle_widget] = REGLAGE_RE2020[cle]
    st.session_state["lignes"] = list(REGLAGE_RE2020["lignes"])


def _aller_methode():
    """Lien « Méthode & sources › » du bandeau des hypothèses."""
    st.session_state["onglet"] = ONGLETS[3]


def barre_laterale():
    st.sidebar.markdown("### FICHIERS MÉTÉO")
    recherche = st.sidebar.text_input("Rechercher", placeholder="zone, station, type…", label_visibility="collapsed")
    cat = CATALOGUE
    if recherche:
        masque = cat.apply(lambda r: recherche.lower() in " ".join(map(str, r.values)).lower(), axis=1)
        cat = cat[masque]
    zones = list(dict.fromkeys(cat["zone"]))
    importes = st.session_state.setdefault("importes", {})
    if importes:
        zones.append("Importés (session)")
    if not zones:
        st.sidebar.warning("Aucun fichier ne correspond.")
        zones = list(dict.fromkeys(CATALOGUE["zone"])); cat = CATALOGUE
    zone_defaut = CATALOGUE.set_index("id").loc[FICHIER_DEFAUT, "zone"]
    zone = st.sidebar.selectbox("Zone", zones, index=zones.index(zone_defaut) if zone_defaut in zones else 0)
    if zone == "Importés (session)":
        choix = {nom: s for nom, s in importes.items()}
        nom = st.sidebar.radio("Fichier", list(choix), label_visibility="collapsed")
        serie = choix[nom]
    else:
        lignes = cat[cat["zone"] == zone]
        libelles = {f"{r.libelle}   ·   {r.type}": r.id for r in lignes.itertuples()}
        ids = list(libelles.values())
        nom = st.sidebar.radio("Fichier", list(libelles), label_visibility="collapsed",
                               index=ids.index(FICHIER_DEFAUT) if FICHIER_DEFAUT in ids else 0)
        serie = _serie_enregistree(libelles[nom])

    with st.sidebar.expander("+ Importer un fichier (session)"):
        fichier = st.file_uploader("CSV horaire (heure;T ou date;heure;T)", type=["csv", "txt"])
        base = st.radio("Base horaire du fichier", BASES_HORAIRES, horizontal=True)
        if fichier is not None and st.button("Charger"):
            try:
                s = lire_fichier_importe(fichier.getvalue(), fichier.name, base, int(valeur(HYP, "decalage_heure_ete")),
                                         int(valeur(HYP, "trou_max_heures")))
                importes[s.libelle] = s
                st.success(f"{s.libelle} chargé ({len(s.t)} h).")
            except ValueError as e:
                st.error(str(e))
        st.caption("Proposer à l'enregistrement : bientôt.")

    st.sidebar.markdown("### RÉGLAGES")
    for cle, cle_widget in CLES_REGLAGE.items():
        st.session_state.setdefault(cle_widget, REGLAGE_RE2020[cle])
    st.session_state.setdefault("lignes", list(REGLAGE_RE2020["lignes"]))
    reglage = {
        "methode": st.sidebar.radio("Méthode DH", list(LIBELLES_METHODE), format_func=LIBELLES_METHODE.get,
                                    horizontal=True, key="r_methode"),
        "occupation": st.sidebar.toggle("DH en occupation (logement)", key="r_occupation"),
        "critere_journee": st.sidebar.radio("Journée la + chaude selon", list(LIBELLES_CRITERE_JOURNEE),
                                            format_func=LIBELLES_CRITERE_JOURNEE.get, horizontal=True, key="r_journee"),
        "critere_semaine": st.sidebar.radio("Semaine la + chaude selon", list(LIBELLES_CRITERE_SEMAINE),
                                            format_func=LIBELLES_CRITERE_SEMAINE.get, key="r_semaine"),
    }
    lignes = st.sidebar.multiselect("Lignes horizontales (°C)", st.session_state["lignes"],
                                    default=st.session_state["lignes"], format_func=lambda v: f"{v:g} °C")
    col1, col2 = st.sidebar.columns([3, 2])
    nouvelle = col1.number_input("Nouvelle ligne", value=35.0, step=1.0, format="%.0f", label_visibility="collapsed")
    if col2.button("+ ligne"):
        lignes = sorted(set(lignes) | {float(nouvelle)})
    st.session_state["lignes"] = lignes
    reglage["lignes"] = lignes
    st.sidebar.button("↺ Revenir au réglage RE2020", on_click=_reinitialiser)
    return serie, reglage


# ============================================================
# PAGE
# ============================================================

def main():
    entete()
    serie_a, reglage = barre_laterale()

    def analyser_serie(serie):
        return analyser(serie, reglage, HYP)

    def calculer(analyse):
        return calculer_indicateurs(analyse, reglage, HYP, DEFINITIONS)

    analyse_a = analyser_serie(serie_a)
    res_a = calculer(analyse_a)

    with st.sidebar.expander("⤓ Exporter (CSV · Excel)"):
        st.download_button("Série horaire (CSV)", csv_horaire(analyse_a), f"{serie_a.id}_horaire.csv", "text/csv")
        st.download_button("Classeur complet (Excel)", excel_complet(analyse_a, res_a, HYP, reglage, remplacer_reperes),
                           f"{serie_a.id}_meteo_et_chaleur_v{VERSION}.xlsx")

    onglets = st.tabs(ONGLETS, key="onglet", on_change="rerun")
    with onglets[0]:
        onglet_analyser.afficher(analyse_a, res_a, reglage, HYP, _aller_methode)
    with onglets[1]:
        choix_b = {f"{r.zone} · {r.libelle}": r.id for r in CATALOGUE.itertuples() if r.id != serie_a.id}
        choix_b = {k: _serie_enregistree(v) for k, v in choix_b.items()}
        for nom, s in st.session_state.get("importes", {}).items():
            choix_b[nom] = s
        if "fichier_C" in st.session_state:
            choix_b = {st.session_state["fichier_C"].libelle: st.session_state["fichier_C"], **choix_b}
        onglet_comparer.afficher(analyse_a, res_a, choix_b,
                                 lambda s: (lambda a: (a, calculer(a)))(analyser_serie(s)), reglage, HYP)
    with onglets[2]:
        onglet_creer.afficher(analyse_a, reglage, HYP, DEFINITIONS, analyser_serie, calculer)
    with onglets[3]:
        onglet_methode.afficher(analyse_a, HYP)
    pied()


main()
