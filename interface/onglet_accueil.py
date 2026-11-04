"""
============================================================
 ONGLET ACCUEIL (0.9.11) — page d'explication de l'outil
============================================================
 Texte dans docs/accueil.md (Markdown, modifiable sans toucher
 au code). Le repère <!-- bouton_methode --> y place le bouton
 qui ouvre l'onglet Méthode & sources.
 Mise en forme (titres sur fond coloré, encadrés des notions) :
 interface/style.css, bloc « Onglet Accueil ».
============================================================
"""

import os
from functools import lru_cache

import streamlit as st

from calcul.hypotheses import RACINE

# ============================================================
# PARAMÈTRES
# ============================================================
CHEMIN_ACCUEIL = os.path.join(RACINE, "docs", "accueil.md")
REPERE_BOUTON = "<!-- bouton_methode -->"
LIBELLE_BOUTON = "Méthode & sources ›"


@lru_cache(maxsize=1)
def _texte() -> tuple:
    """Texte de l'accueil, lu une fois, coupé en deux autour du repère du bouton."""
    with open(CHEMIN_ACCUEIL, encoding="utf-8") as f:
        avant, _, apres = f.read().partition(REPERE_BOUTON)
    return avant, apres


def afficher(aller_methode):
    """Page d'accueil : texte de docs/accueil.md + bouton vers Méthode & sources."""
    avant, apres = _texte()
    with st.container(key="accueil"):
        st.markdown(avant, unsafe_allow_html=True)
        st.button(LIBELLE_BOUTON, on_click=aller_methode, type="tertiary", key="accueil_methode")
        if apres.strip():
            st.markdown(apres, unsafe_allow_html=True)
