"""
============================================================
 MÉTÉO ET CHALEUR — point d'entrée Streamlit
============================================================
 Lancement local :  streamlit run app.py
 Onglets : ① Analyser · ② Comparer · ③ Créer · Méthode & sources
 Réglage par défaut : RE2020 (config/reglages.py).
============================================================
"""

import numpy as np
import streamlit as st

from calcul.hypotheses import charger_hypotheses, charger_indicateurs, remplacer_reperes, valeur
from calcul.indicateurs import analyser, calculer_indicateurs
from calcul.serie import charger_catalogue, charger_serie, lire_fichier_importe
from config.reglages import (FAMILLE_IMPORTES, LIBELLE_SEUILS_DH, LIBELLES_CRITERE_JOURNEE, LIBELLES_CRITERE_SEMAINE,
                             LIBELLES_METHODE, ONGLETS, REGLAGE_RE2020, VERSION)
from export.export import csv_horaire, excel_complet
from interface import choix_fichier, onglet_analyser, onglet_comparer, onglet_creer, onglet_methode
from interface.composants import entete, pied

# ============================================================
# PARAMÈTRES
# ============================================================
TITRE_PAGE = "Météo et Chaleur"
CLES_REGLAGE = {"methode": "r_methode", "occupation": "r_occupation",
                "critere_journee": "r_journee", "critere_semaine": "r_semaine"}
CLE_INDICATEURS = "r_indicateurs"        # ordre des cartes choisi dans le menu
INDICATEURS_RESUME = ["dh", "nuits_20"]  # chiffres clés des cartes de la fenêtre de choix (+ T max)

st.set_page_config(page_title=TITRE_PAGE, page_icon="☀", layout="wide")


# ============================================================
# DONNÉES EN CACHE
# ============================================================

@st.cache_data
def _hypotheses():
    return charger_hypotheses(), charger_indicateurs(tous=True)


@st.cache_data
def _catalogue():
    return charger_catalogue()


@st.cache_resource
def _serie_enregistree(identifiant):
    hyp, _ = _hypotheses()
    ligne = _catalogue().set_index("id").loc[identifiant].to_dict()
    ligne["id"] = identifiant
    return charger_serie(ligne, int(valeur(hyp, "decalage_heure_ete")))


def _resumer(serie) -> dict:
    """DH (réglage RE2020), nuits ≥ 20 °C et T max d'une série : chiffres clés de la fenêtre de choix."""
    _, tous = _hypotheses()
    a = analyser(serie, REGLAGE_RE2020, HYP)
    defs = [d for d in tous if d["id"] in INDICATEURS_RESUME]
    v = {d["id"]: r.valeur for d, r in calculer_indicateurs(a, REGLAGE_RE2020, HYP, defs)}
    return {"dh": v.get("dh"), "nuits_20": v.get("nuits_20"), "tmax": float(np.max(serie.t))}


@st.cache_data(show_spinner="Calcul des chiffres clés du fichier…")
def _resume_enregistre(identifiant):
    return _resumer(_serie_enregistree(identifiant))


HYP, TOUS_INDICATEURS = _hypotheses()
INDICATEURS = {d["id"]: d for d in TOUS_INDICATEURS}
ORDRE_DEFAUT = [d["id"] for d in TOUS_INDICATEURS if d["actif"]]     # ordre de hypotheses.xlsx
CATALOGUE = _catalogue()


# ============================================================
# RÉGLAGES (barre latérale)
# ============================================================

def _reinitialiser():
    for cle, cle_widget in CLES_REGLAGE.items():
        st.session_state[cle_widget] = REGLAGE_RE2020[cle]
    st.session_state["lignes"] = list(REGLAGE_RE2020["lignes"])
    st.session_state[CLE_INDICATEURS] = list(ORDRE_DEFAUT)


def _aller_methode():
    """Lien « Méthode & sources › » du bandeau des hypothèses."""
    st.session_state["onglet"] = ONGLETS[3]


def _mettre_en_tete():
    """Bouton ↑ : l'indicateur choisi passe en première carte."""
    choisi = st.session_state.get("indicateur_tete")
    if choisi:
        st.session_state[CLE_INDICATEURS] = [choisi] + [i for i in st.session_state[CLE_INDICATEURS] if i != choisi]
        st.session_state["indicateur_tete"] = None


def _libelle_indicateur(identifiant):
    return remplacer_reperes(INDICATEURS[identifiant]["libelle"], HYP)


def serie_par_cle(cle):
    """Clé de fichier (catalogue, « importe:<nom> », « fichier_C ») → série."""
    if cle == choix_fichier.CLE_FICHIER_C:
        return st.session_state[choix_fichier.CLE_FICHIER_C]
    if cle.startswith(choix_fichier.PREFIXE_IMPORTE):
        return choix_fichier.importes()[cle[len(choix_fichier.PREFIXE_IMPORTE):]]
    return _serie_enregistree(cle)


def _resume(cle):
    ids = set(CATALOGUE["id"])
    return _resume_enregistre(cle) if cle in ids else _resumer(serie_par_cle(cle))


def _importer_fichier(contenu, nom, base):
    s = lire_fichier_importe(contenu, nom, base, int(valeur(HYP, "decalage_heure_ete")), int(valeur(HYP, "trou_max_heures")))
    s.meta.setdefault("famille", FAMILLE_IMPORTES)
    return s


SOURCES = choix_fichier.Sources(catalogue=CATALOGUE, charger=serie_par_cle, resume=_resume, importer=_importer_fichier)


def _choisir_indicateurs():
    """Indicateurs affichés et leur ordre (l'ordre de la liste = l'ordre des cartes)."""
    st.session_state.setdefault(CLE_INDICATEURS, list(ORDRE_DEFAUT))
    with st.sidebar.expander("Indicateurs affichés (ordre des cartes)"):
        choisis = st.multiselect("Indicateurs", list(INDICATEURS), key=CLE_INDICATEURS,
                                 format_func=_libelle_indicateur, label_visibility="collapsed")
        col1, col2 = st.columns([4, 1], vertical_alignment="bottom")
        col1.selectbox("Placer en tête", choisis, index=None, placeholder="Placer en tête…", key="indicateur_tete",
                       format_func=_libelle_indicateur, label_visibility="collapsed")
        col2.button("↑", on_click=_mettre_en_tete, help="Mettre l'indicateur choisi en première carte")
        st.caption("L'ordre de la liste est l'ordre des cartes. Un indicateur retiré puis remis passe en dernier.")
    return [INDICATEURS[i] for i in (choisis or ORDRE_DEFAUT)]


def barre_laterale():
    serie = serie_par_cle(choix_fichier.cle_courante(SOURCES))
    choix_fichier.menu(SOURCES, serie, lambda: choix_fichier.ouvrir("analyser", SOURCES))

    st.sidebar.markdown("### RÉGLAGES")
    for cle, cle_widget in CLES_REGLAGE.items():
        st.session_state.setdefault(cle_widget, REGLAGE_RE2020[cle])
    st.session_state.setdefault("lignes", list(REGLAGE_RE2020["lignes"]))
    reglage = {
        "methode": st.sidebar.radio(LIBELLE_SEUILS_DH, list(LIBELLES_METHODE), format_func=LIBELLES_METHODE.get,
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
    reglage["indicateurs"] = _choisir_indicateurs()
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
        return calculer_indicateurs(analyse, reglage, HYP, reglage["indicateurs"])

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
        serie_b = serie_par_cle(choix_fichier.cle_seconde(SOURCES))
        onglet_comparer.afficher(analyse_a, res_a, serie_b, lambda s: (lambda a: (a, calculer(a)))(analyser_serie(s)),
                                 reglage, HYP, lambda: choix_fichier.ouvrir("comparer", SOURCES))
    with onglets[2]:
        onglet_creer.afficher(analyse_a, reglage, HYP, reglage["indicateurs"], analyser_serie, calculer)
    with onglets[3]:
        onglet_methode.afficher(analyse_a, HYP)
    pied()


main()
