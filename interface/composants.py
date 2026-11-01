"""
============================================================
 COMPOSANTS — style, en-tête, nom du fichier, bandeau des
 hypothèses, pastilles d'écart, cartouches, pied de page
============================================================
 Style inspiré d'un tableau de bord épuré : fond gris chaud,
 cartes arrondies à ombre douce, pastilles pour les écarts.
 Le CSS est dans interface/style.css ; les cartes d'indicateurs
 dans interface/cartes.py.
============================================================
"""

import html
import os
from functools import lru_cache
from string import Template

import pandas as pd
import streamlit as st

from calcul.format_fr import nombre
from config import charte
from config.charte import BLEU_CLAIR, BLEU_FRAIS, CORAIL, GRIS_DOUX
from config.reglages import AUTEUR, LIEN_CODE_SOURCE, STATUT_VERSION, VERSION
from interface.couleurs import melange

# ============================================================
# PARAMÈTRES
# ============================================================
CHEMIN_CSS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
TRACE_LOGO = "M2 12 C3.2 12 3.6 9.5 4.8 9.5 S6.4 14.5 7.6 14.5 S9.2 6 10.6 6 S12.4 18 13.8 18 S15.6 3.5 17.2 3.5 S19.2 20.5 22 12"
COULEUR_PLUS_CHAUD = "#C23B3C"          # texte des pastilles « plus chaud »
FOND_EGAL = "#EEEDEA"                   # pastille « égal »


# ============================================================
# STYLE
# ============================================================

@lru_cache(maxsize=1)
def css() -> str:
    """Feuille de style, lue une fois : les $NOM de style.css sont remplacés par les valeurs de config/charte.py."""
    with open(CHEMIN_CSS, encoding="utf-8") as f:
        modele = Template(f.read())
    valeurs = {nom: v for nom, v in vars(charte).items() if nom.isupper() and isinstance(v, str)}
    return f"\n<style>\n{modele.substitute(valeurs)}</style>\n"


def logo_onde() -> str:
    """Logo : une onde de température (oscillation qui s'amplifie), trait blanc sur rond indigo."""
    return ('<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round"><path d="{TRACE_LOGO}"/></svg>')


# ============================================================
# EN-TÊTE ET NOM DU FICHIER
# ============================================================

def haut_de_page(serie, onglets: list, cle_onglet: str) -> str:
    """
    Bloc fixé en haut de la page : en-tête, barre des onglets, nom du fichier en cours.
    Renvoie l'onglet choisi (seul son contenu est calculé ensuite).
    """
    st.markdown(css(), unsafe_allow_html=True)
    st.session_state.setdefault(cle_onglet, onglets[0])
    with st.container(key="haut_fixe"):
        st.markdown(
            f'<div class="entete"><div class="logo">{logo_onde()}</div>'
            f'<div><div class="nom">Météo et Chaleur</div>'
            f'<div class="sous">Analyser la météo sous l\'angle de l\'inconfort d\'été</div></div>'
            f'<div class="version">v<b>{VERSION}</b> · {STATUT_VERSION}</div></div>', unsafe_allow_html=True)
        with st.container(key="barre_onglets"):
            onglet = st.segmented_control("Onglets", onglets, key=cle_onglet, required=True,
                                          label_visibility="collapsed")
        titre_fichier(serie)
    return onglet or onglets[0]


def description_fichier(serie) -> str:
    """« Trappes · année type · Scénarios météo RE2020 … · base horaire UTC »."""
    m = serie.meta
    morceaux = [m.get("station"), m.get("periode"), m.get("description"), m.get("source"),
                f"base horaire {m['base_horaire']}" if m.get("base_horaire") else None]
    return " · ".join(str(x) for x in morceaux if x)


def titre_fichier(serie):
    """Nom du fichier en gros entre la barre des onglets et les cartes."""
    st.markdown(f'<div class="fichier"><div class="nom">{html.escape(serie.libelle)}</div>'
                f'<div class="meta">{html.escape(description_fichier(serie))}</div></div>', unsafe_allow_html=True)


# ============================================================
# BANDEAU DES HYPOTHÈSES, PASTILLES, CARTOUCHES, PIED
# ============================================================

def bandeau_hypotheses(reglage, analyse, hyp, libelles_semaine, aller_methode=None):
    puces = []
    if analyse.methode_effective == "RE2020":
        puces += [f"RE2020 · seuil {hyp['seuil_nuit_dh']['valeur']:g} → {hyp['seuil_jour_max']['valeur']:g} °C",
                  "température fichier lissée (RE2020)"]
    else:
        puces.append(f"basic · {hyp['seuil_nuit_dh']['valeur']:g} °C nuit / {hyp['seuil_jour_max']['valeur']:g} °C jour")
    puces.append("occupation logement (provisoire)" if reglage["occupation"] else "24h/24, sans occupation")
    puces.append(f"nuit {hyp['nuit_debut']['valeur']:g}h-{hyp['nuit_fin']['valeur']:g}h")
    if analyse.serie.decalage_utc:
        puces.append(f"heure légale = UTC + {analyse.serie.decalage_utc}")
    puces.append(f"semaine : {libelles_semaine[reglage['critere_semaine']].lower()}")
    contenu = "".join(f'<span class="puce">{html.escape(p)}</span>' for p in puces)
    col_puces, col_lien = st.columns([8, 1.3], vertical_alignment="center")
    col_puces.markdown(f'<div class="hypos"><b>Hypothèses actives :</b>{contenu}</div>', unsafe_allow_html=True)
    if aller_methode is not None:                      # lien fonctionnel vers l'onglet Méthode & sources
        col_lien.button("Méthode & sources ›", on_click=aller_methode, type="tertiary", key="lien_methode")
    if analyse.message_methode:
        st.markdown(f'<div class="message">⚠ {html.escape(analyse.message_methode)}</div>', unsafe_allow_html=True)


def pastille_ecart(ecart: float, unite: str, decimales: int = 0) -> str:
    """Écart en pastille : rouge = plus chaud, bleu = plus frais, gris = égal."""
    if round(ecart, decimales) == 0:
        fond, texte, signe = FOND_EGAL, GRIS_DOUX, ""
    elif ecart > 0:
        fond, texte, signe = melange(CORAIL, 0.16), COULEUR_PLUS_CHAUD, "+"
    else:
        fond, texte, signe = BLEU_CLAIR, BLEU_FRAIS, "−"
    return (f'<span class="pastille" style="background:{fond};color:{texte}">'
            f'{signe}{nombre(abs(ecart), decimales)} {html.escape(unite)}</span>')


def cartouche(role: str, serie, couleur: str):
    """Contenu HTML d'un cartouche de fichier (onglet Comparer) : rôle, nom dans sa couleur, description."""
    st.markdown(f'<div class="cartouche"><div class="role">{html.escape(role)}</div>'
                f'<div class="nom" style="color:{couleur}">{html.escape(serie.libelle)}</div>'
                f'<div class="meta">{html.escape(description_fichier(serie))}</div></div>', unsafe_allow_html=True)


def tableau_html(df: pd.DataFrame) -> str:
    """Tableau simple (sans pyarrow), dans une carte blanche."""
    return f'<div class="tableau">{df.to_html(index=False, escape=True, border=0)}</div>'


def pied():
    """Pied de page : nature des indicateurs, version, auteur, lien vers le code source."""
    st.markdown(
        f'<div class="pied">Indicateurs calculés sur la base de fichiers climatiques · licence GNU GPL v3 · Météo &amp; Chaleur · version '
        f'{VERSION} · {AUTEUR} · <a href="{LIEN_CODE_SOURCE}" target="_blank">Code Source</a></div>',
        unsafe_allow_html=True)
