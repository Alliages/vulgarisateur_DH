"""
============================================================
 MENU DES RÉGLAGES (barre latérale, partie repliée)
============================================================
 Méthode DH, occupation, critères de la journée et de la semaine,
 lignes horizontales, indicateurs affichés et leur ordre.

 Le réglage de référence est gardé À PART des boutons du menu :
 au premier chargement, la mémoire du navigateur relance la page
 pendant le calcul et Streamlit pouvait perdre l'état d'un bouton
 de la partie repliée (l'occupation repassait à « 24h/24 », 0.9.5).
 Les calculs lisent ce réglage ; il ne change que quand
 l'utilisateur clique sur un bouton (_copier_bouton).
============================================================
"""

import streamlit as st

from calcul.hypotheses import remplacer_reperes
from config.reglages import (LIBELLE_SEUILS_DH, LIBELLES_CRITERE_JOURNEE, LIBELLES_CRITERE_SEMAINE, LIBELLES_METHODE,
                             REGLAGE_RE2020)

# ============================================================
# PARAMÈTRES
# ============================================================
CLES_REGLAGE = {"methode": "r_methode", "occupation": "r_occupation",           # clés des boutons du menu
                "critere_journee": "r_journee", "critere_semaine": "r_semaine"}
CLE_REGLAGE_COURANT = "reglage_courant"  # réglage de référence, gardé à part des boutons
CLE_GENERATION_BOUTONS = "generation_boutons"   # change à chaque retour au réglage RE2020
CLE_INDICATEURS = "r_indicateurs"        # ordre des cartes choisi dans le menu (gardé dans le navigateur)
CLE_LIGNES = "lignes"                    # lignes horizontales (gardées dans le navigateur)
CLE_TETE = "indicateur_tete"             # liste « Placer en tête »
LIGNE_PROPOSEE = 35.0                    # valeur proposée pour une nouvelle ligne horizontale (°C)


# ============================================================
# RÉGLAGE DE RÉFÉRENCE
# ============================================================

def _reglage_courant() -> dict:
    return st.session_state.setdefault(CLE_REGLAGE_COURANT, {k: REGLAGE_RE2020[k] for k in CLES_REGLAGE})


def _cle_bouton(cle) -> str:
    """Clé du bouton du menu ; elle change à chaque « Revenir au réglage RE2020 » (boutons recréés, affichage juste)."""
    return f"{CLES_REGLAGE[cle]}_{st.session_state.setdefault(CLE_GENERATION_BOUTONS, 0)}"


def _copier_bouton(cle):
    """Clic sur un bouton du menu : sa valeur devient le réglage de référence."""
    _reglage_courant()[cle] = st.session_state[_cle_bouton(cle)]


def _reinitialiser(ordre_defaut):
    st.session_state[CLE_REGLAGE_COURANT] = {k: REGLAGE_RE2020[k] for k in CLES_REGLAGE}
    st.session_state[CLE_GENERATION_BOUTONS] = st.session_state.get(CLE_GENERATION_BOUTONS, 0) + 1
    st.session_state[CLE_LIGNES] = list(REGLAGE_RE2020["lignes"])
    st.session_state[CLE_INDICATEURS] = list(ordre_defaut)


# ============================================================
# INDICATEURS AFFICHÉS
# ============================================================

def _mettre_en_tete():
    """Bouton ↑ : l'indicateur choisi passe en première carte."""
    choisi = st.session_state.get(CLE_TETE)
    if choisi:
        st.session_state[CLE_INDICATEURS] = [choisi] + [i for i in st.session_state[CLE_INDICATEURS] if i != choisi]
        st.session_state[CLE_TETE] = None


def _choisir_indicateurs(indicateurs: dict, ordre_defaut: list, hyp: dict) -> list:
    """Indicateurs affichés et leur ordre (l'ordre de la liste = l'ordre des cartes)."""
    def libelle(identifiant):
        return remplacer_reperes(indicateurs[identifiant]["libelle"], hyp)

    st.session_state.setdefault(CLE_INDICATEURS, list(ordre_defaut))
    st.markdown('<div class="sous-titre-menu">INDICATEURS AFFICHÉS (ORDRE DES CARTES)</div>', unsafe_allow_html=True)
    choisis = st.multiselect("Indicateurs", list(indicateurs), key=CLE_INDICATEURS, format_func=libelle,
                             label_visibility="collapsed")
    col1, col2 = st.columns([4, 1], vertical_alignment="bottom")
    col1.selectbox("Placer en tête", choisis, index=None, placeholder="Placer en tête…", key=CLE_TETE,
                   format_func=libelle, label_visibility="collapsed")
    col2.button("↑", on_click=_mettre_en_tete, help="Mettre l'indicateur choisi en première carte")
    st.caption("L'ordre de la liste est l'ordre des cartes. Un indicateur retiré puis remis passe en dernier.")
    return [indicateurs[i] for i in (choisis or ordre_defaut)]


# ============================================================
# MENU
# ============================================================

def afficher(indicateurs: dict, ordre_defaut: list, hyp: dict) -> dict:
    """Réglages repliés du menu de gauche ; renvoie le réglage à appliquer (+ lignes et indicateurs)."""
    courant = _reglage_courant()
    st.session_state.setdefault(CLE_LIGNES, list(REGLAGE_RE2020["lignes"]))
    with st.sidebar.expander("RÉGLAGES", expanded=False, key="reglages"):
        methodes, journees, semaines = list(LIBELLES_METHODE), list(LIBELLES_CRITERE_JOURNEE), list(LIBELLES_CRITERE_SEMAINE)
        st.radio(LIBELLE_SEUILS_DH, methodes, index=methodes.index(courant["methode"]), format_func=LIBELLES_METHODE.get,
                 horizontal=True, key=_cle_bouton("methode"), on_change=_copier_bouton, args=("methode",))
        st.toggle("DH en occupation (logement)", value=courant["occupation"], key=_cle_bouton("occupation"),
                  on_change=_copier_bouton, args=("occupation",))
        st.radio("Journée la + chaude selon", journees, index=journees.index(courant["critere_journee"]),
                 format_func=LIBELLES_CRITERE_JOURNEE.get, horizontal=True, key=_cle_bouton("critere_journee"),
                 on_change=_copier_bouton, args=("critere_journee",))
        st.radio("Semaine la + chaude selon", semaines, index=semaines.index(courant["critere_semaine"]),
                 format_func=LIBELLES_CRITERE_SEMAINE.get, key=_cle_bouton("critere_semaine"),
                 on_change=_copier_bouton, args=("critere_semaine",))
        reglage = dict(courant)                     # les calculs lisent le réglage de référence
        lignes = st.multiselect("Lignes horizontales (°C)", st.session_state[CLE_LIGNES],
                                default=st.session_state[CLE_LIGNES], format_func=lambda v: f"{v:g} °C")
        col1, col2 = st.columns([3, 2])
        nouvelle = col1.number_input("Nouvelle ligne", value=LIGNE_PROPOSEE, step=1.0, format="%.0f",
                                     label_visibility="collapsed")
        if col2.button("+ ligne"):
            lignes = sorted(set(lignes) | {float(nouvelle)})
        st.session_state[CLE_LIGNES] = lignes
        reglage["lignes"] = lignes
        reglage["indicateurs"] = _choisir_indicateurs(indicateurs, ordre_defaut, hyp)
        st.button("↺ Revenir au réglage RE2020", on_click=_reinitialiser, args=(ordre_defaut,))
    return reglage
