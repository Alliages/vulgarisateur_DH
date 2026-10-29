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
    """« lun. 6 août » pour les graduations de la semaine (date au format long)."""
    return f"{JOURS_COURTS[d.dayofweek]} {jour_mois(d)}"


def heure(d: pd.Timestamp) -> str:
    return f"{d.hour} h"


def nombre(v: float, decimales: int = 1) -> str:
    """Virgule décimale et espace des milliers : 39,7 · 1 472."""
    return f"{v:,.{decimales}f}".replace(",", " ").replace(".", ",")


# Dictionnaire de langue passé à Plotly (config « locales ») : mois, jours et virgule décimale
# en français sur tous les axes, à tous les niveaux de zoom (évite les graduations calculées à la main).
LOCALE_PLOTLY = {"fr": {"dictionary": {}, "format": {
    "days": [JOURS[6]] + JOURS[:6], "shortDays": [JOURS_COURTS[6]] + JOURS_COURTS[:6],
    "months": MOIS, "shortMonths": MOIS_COURTS, "decimal": ",", "thousands": " "}}}
