"""
============================================================
 ERREURS LISIBLES (version de test)
============================================================
 En cas d'erreur, la page affiche un message clair en français et le
 détail technique dans un cadre copiable (bouton ⧉), à envoyer pour
 correction, au lieu de la trace Python brute.

 Solution native : app.py appelle la page dans un try/except.
 (L'extra streamlit-extras « exception_handler » ne fonctionne plus
 avec Streamlit 1.66 : il modifie une fonction qui n'est plus appelée.)
 Les arrêts internes de Streamlit (relance, st.stop) ne sont pas des
 « Exception » et passent donc normalement.
============================================================
"""

import traceback

import streamlit as st

from config.reglages import VERSION

# ============================================================
# PARAMÈTRES
# ============================================================
MESSAGE = ("L'outil a rencontré une erreur et n'a pas pu finir d'afficher la page. Le détail ci-dessous permet de "
           "la corriger : copiez-le (bouton ⧉ en haut à droite du cadre) et envoyez-le avec une phrase sur ce que "
           "vous faisiez. Vous pouvez aussi recharger la page.")


def afficher(ex: Exception):
    """Message clair + détail copiable ; la trace complète reste aussi dans la console."""
    detail = f"Météo et Chaleur v{VERSION}\n" + "".join(traceback.format_exception(ex))
    print(detail, flush=True)
    st.error(MESSAGE, icon="⚠️")
    with st.expander("Détail de l'erreur (à copier)", expanded=False):
        st.code(detail, language=None)
