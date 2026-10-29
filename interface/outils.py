"""
============================================================
 OUTILS D'INTERFACE — détection de pyarrow
============================================================
 Streamlit charge pyarrow seulement pour ses tableaux interactifs
 (st.data_editor, st.dataframe). Sous Windows / Anaconda, une
 version de pyarrow en conflit fait échouer ce chargement
 (« DLL load failed while importing lib »). L'outil reste alors
 utilisable : formulaire simple dans Créer, tableaux HTML ailleurs.

 Variable d'environnement METEO_SANS_PYARROW=1 : force le mode
 de secours (pour le tester sans casser son installation).
============================================================
"""

import os

# ============================================================
# PARAMÈTRES
# ============================================================
VARIABLE_FORCAGE = "METEO_SANS_PYARROW"


def _pyarrow_disponible() -> bool:
    if os.environ.get(VARIABLE_FORCAGE) == "1":
        return False
    try:
        import pyarrow  # noqa: F401  (chargement de la partie compilée, là où l'erreur Windows survient)
        import pyarrow.lib  # noqa: F401
        return True
    except (ImportError, OSError):
        return False


PYARROW_DISPONIBLE = _pyarrow_disponible()
