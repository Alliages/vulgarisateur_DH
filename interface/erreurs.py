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

import logging
import sys
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


# ============================================================
# BRUIT WINDOWS DANS LA CONSOLE
# ============================================================
# Sous Windows, quand le navigateur ferme ou recharge sa connexion, Python (asyncio) écrit dans la console
# « Exception in callback _ProactorBasePipeTransport._call_connection_lost … ConnectionResetError
# [WinError 10054] ». C'est sans conséquence pour l'outil : ces messages-là sont simplement filtrés.

class _FiltreConnexionFermee(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        exception = record.exc_info[1] if record.exc_info else None
        return not isinstance(exception, (ConnectionResetError, ConnectionAbortedError))


def filtrer_bruit_windows():
    """À appeler au démarrage ; sans effet hors Windows, et posé une seule fois."""
    if sys.platform != "win32":
        return
    journal = logging.getLogger("asyncio")
    if not any(type(f).__name__ == "_FiltreConnexionFermee" for f in journal.filters):
        journal.addFilter(_FiltreConnexionFermee())
