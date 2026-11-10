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
from config.charte import (BLEU_CLAIR, BLEU_FRAIS, CORAIL, COULEUR_FICHIER_1, COULEUR_FICHIER_2, COULEURS_BAISSE,
                           COULEURS_HAUSSE, GRIS_DOUX)
from config.reglages import AUTEUR, LIEN_CODE_SOURCE, ONGLET_ACCUEIL, STATUT_VERSION, VERSION
from interface.couleurs import melange

# ============================================================
# PARAMÈTRES
# ============================================================
CHEMIN_CSS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
TRACE_LOGO = "M2 12 C3.2 12 3.6 9.5 4.8 9.5 S6.4 14.5 7.6 14.5 S9.2 6 10.6 6 S12.4 18 13.8 18 S15.6 3.5 17.2 3.5 S19.2 20.5 22 12"
TRIANGLES_LOGO = ("33.60,29.23 33.60,3.23 56.12,16.23", "35.20,32.00 57.72,19.00 57.72,45.00",
                  "33.60,34.77 56.12,47.77 33.60,60.77", "30.40,34.77 30.40,60.77 7.88,47.77",
                  "28.80,32.00 6.28,45.00 6.28,19.00", "30.40,29.23 7.88,16.23 30.40,3.23")   # hexagone en 6 triangles
PALIERS_AMPLEUR = (1 / 3, 2 / 3)         # remplissage à partir duquel la jauge passe au niveau 1, puis 2
DECIMALES_AMPLEUR = 1
TAILLE_LOGO = 52                        # px, en-tête
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


def logo_onde(taille: int = TAILLE_LOGO) -> str:
    """Logo : une onde de température (oscillation qui s'amplifie), trait blanc sur hexagone indigo en 6 triangles."""
    triangles = "".join(f'<polygon points="{p}"/>' for p in TRIANGLES_LOGO)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{taille}" height="{taille}" viewBox="0 0 64 64">'
            f'<g fill="{charte.INDIGO}" stroke="{charte.INDIGO}" stroke-width="2" stroke-linejoin="round">{triangles}</g>'
            '<g transform="translate(10.4 10.4) scale(1.8)" fill="none" stroke="white" stroke-width="2.2" '
            f'stroke-linecap="round" stroke-linejoin="round"><path d="{TRACE_LOGO}"/></g></svg>')


# ============================================================
# EN-TÊTE ET NOM DU FICHIER
# ============================================================

def haut_de_page(serie, onglets: list, cle_onglet: str, serie_b=None) -> str:
    """
    Bloc fixé en haut de la page : en-tête, barre des onglets, nom du fichier en cours.
    serie_b (onglet Comparer) : les deux noms côte à côte, chacun dans sa couleur.
    Onglet Accueil : pas de nom de fichier (0.9.11).
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
        if (onglet or onglets[0]) != ONGLET_ACCUEIL:
            titre_fichier(serie, serie_b)
    return onglet or onglets[0]


def description_fichier(serie) -> str:
    """« Trappes · année type · Scénarios météo RE2020 … · base horaire UTC »."""
    m = serie.meta
    morceaux = [m.get("station"), m.get("periode"), m.get("description"), m.get("source"),
                f"base horaire {m['base_horaire']}" if m.get("base_horaire") else None]
    return " · ".join(str(x) for x in morceaux if x)


def titre_fichier(serie, serie_b=None):
    """
    Nom du fichier en gros entre la barre des onglets et les cartes.
    Avec serie_b (onglet Comparer) : fichier 1 à gauche, fichier 2 à droite, dans leurs couleurs ;
    la ligne de description reste celle du fichier 1.
    """
    if serie_b is None:
        noms = f'<div class="nom">{html.escape(serie.libelle)}</div>'
    else:
        noms = (f'<div class="noms">'
                f'<div class="nom" style="color:{COULEUR_FICHIER_1}">{html.escape(serie.libelle)}</div>'
                f'<div class="nom nom-b" style="color:{COULEUR_FICHIER_2}">{html.escape(serie_b.libelle)}</div></div>')
    st.markdown(f'<div class="fichier">{noms}'
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
    puces.append("occupation logement" if reglage["occupation"] else "24h/24, sans occupation")
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


def ampleur(va, vb, ecart, mode, seuil):
    """
    Jauge de l'onglet Comparer : {valeur, remplissage (0 → 1), niveau (0, 1, 2)}, ou None si le calcul n'a pas de sens
    (mode relatif et référence nulle). ecart : écart de la pastille, arrondi comme elle, qui décide de l'écart nul.
    """
    if mode == "relatif" and va == 0:
        return None
    valeur = 0.0 if ecart == 0 else (vb - va) / abs(va) * 100 if mode == "relatif" else ecart
    remplissage = min(abs(valeur) / seuil, 1.0)
    return {"valeur": valeur, "remplissage": remplissage, "niveau": sum(remplissage >= s for s in PALIERS_AMPLEUR)}


def _court(v: float) -> str:
    """Une décimale au plus, virgule décimale : 1,9 · 3 · 1 472."""
    texte = nombre(abs(v), DECIMALES_AMPLEUR)
    return texte[:-2] if texte.endswith(",0") else texte


def cellule_ampleur(va, vb, ecart, mode, seuil, unite) -> str:
    """Cellule « Ampleur » : [valeur de l'écart] [jauge] [seuil]. La jauge reprend le sens de la pastille."""
    if va is None or vb is None:
        return "—"
    a = ampleur(va, vb, ecart, mode, seuil)
    if a is None:
        return '<span class="ampleur-na">n/a</span>'
    v = a["valeur"]
    u = "%" if mode == "relatif" else html.escape(unite)
    signe = "+" if v > 0 else "−" if v < 0 else ""
    couleur = COULEURS_HAUSSE[a["niveau"]] if v > 0 else COULEURS_BAISSE[a["niveau"]]
    discret = " discret" if mode == "absolu" or v == 0 else ""       # mode absolu : la valeur répète la pastille
    return (f'<span class="ampleur"><span class="valeur{discret}">{signe}{_court(v)}&nbsp;{u}</span>'
            f'<span class="jauge"><span style="width:{a["remplissage"] * 100:.0f}%;background:{couleur}"></span></span>'
            f'<span class="seuil">{_court(seuil)}&nbsp;{u}</span></span>')


def legende_ampleur() -> str:
    """Légende sous le tableau de l'onglet Comparer."""
    return (f'<div class="legende-ampleur"><span style="background:{COULEURS_HAUSSE[2]}"></span>hausse (intensité = ampleur)'
            f'<span style="background:{COULEURS_BAISSE[2]}"></span>baisse</div>')


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
