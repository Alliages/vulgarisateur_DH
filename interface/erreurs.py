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

 Appli en ligne : la trace Python (chemins du serveur, versions) n'est
 PAS montrée au visiteur ; il copie une courte référence (version,
 type d'erreur, heure) qui permet de retrouver la trace complète dans
 le journal du serveur. Variable d'environnement METEO_DEBUG=1 : trace
 complète à l'écran (en local, pour corriger).
============================================================
"""

import logging
import os
import sys
import time
import traceback

import streamlit as st

from config.reglages import VERSION

# ============================================================
# PARAMÈTRES
# ============================================================
VARIABLE_DEBUG = "METEO_DEBUG"
MESSAGE = ("L'outil a rencontré une erreur et n'a pas pu finir d'afficher la page. Vous pouvez recharger la page. "
           "Pour aider à la corriger, copiez la référence ci-dessous (bouton ⧉ en haut à droite du cadre) et "
           "envoyez-la avec une phrase sur ce que vous faisiez.")


def afficher(ex: Exception):
    """Message clair + référence copiable ; la trace complète va dans le journal (et à l'écran si METEO_DEBUG=1)."""
    reference = f"Météo et Chaleur v{VERSION} · {type(ex).__name__} · {time.strftime('%Y-%m-%d %H:%M:%S')}"
    trace = "".join(traceback.format_exception(ex))
    print(f"{reference}\n{trace}", flush=True)
    st.error(MESSAGE, icon="⚠️")
    with st.expander("Référence de l'erreur (à copier)", expanded=False):
        st.code(f"{reference}\n{trace}" if os.environ.get(VARIABLE_DEBUG) == "1" else reference, language=None)


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
