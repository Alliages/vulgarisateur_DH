"""
============================================================
 FORMAT_FR — dates et nombres en français (sans dépendre de la
 locale du système ni de celle de Plotly)
============================================================
"""

import pandas as pd

# ============================================================
# PARAMÈTRES
# ============================================================
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
        "novembre", "décembre"]
MOIS_COURTS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
JOURS_COURTS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]


def jour_mois(d: pd.Timestamp) -> str:
    """« 1er août », « 11 août »."""
    return f"{'1er' if d.day == 1 else d.day} {MOIS[d.month - 1]}"


def date_longue(d: pd.Timestamp, avec_annee: bool = False) -> str:
    """« lundi 6 août » (+ « 2026 » pour un relevé daté)."""
    return f"{JOURS[d.dayofweek]} {jour_mois(d)}" + (f" {d.year}" if avec_annee else "")


def periode_longue(debut: pd.Timestamp, fin: pd.Timestamp, avec_annee: bool = False) -> str:
    return f"du {date_longue(debut)} au {date_longue(fin, avec_annee)}"


def jour_court(d: pd.Timestamp) -> str:
    """« lun. 6/08 » pour les graduations de la semaine."""
    return f"{JOURS_COURTS[d.dayofweek]} {d.day}/{d.month:02d}"


def heure(d: pd.Timestamp) -> str:
    return f"{d.hour} h"


def nombre(v: float, decimales: int = 1) -> str:
    """Virgule décimale : 39,7."""
    return f"{v:.{decimales}f}".replace(".", ",")
