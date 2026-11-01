"""MÉTHODE & SOURCES — pages générées depuis docs/sources/ (Word + Excel)."""

import glob
import os

import numpy as np
import pandas as pd
import streamlit as st

from calcul.confort_ptc import theta_rm_en16798
from calcul.dh_re2020 import moyenne_glissante_exterieure
from calcul.format_fr import nombre
from calcul.hypotheses import RACINE, remplacer_reperes, valeur
from interface import graphiques_analyse as ga
from interface.composants import tableau_html
from interface.graphiques_communs import afficher as afficher_graphique
from interface.outils import PYARROW_DISPONIBLE

# ============================================================
# PARAMÈTRES
# ============================================================
DOSSIER_PAGES = os.path.join(RACINE, "docs", "pages")
PAGE_HYPOTHESES = "Hypothèses (tableau)"
PAGE_THETA = "Température fichier lissée (graphique)"
JOURS_ECART_MAX = slice(120, 273)        # page « température lissée » : écart maximal calculé de mai à septembre
JOUR_ZOOM_DEBUT, JOUR_ZOOM_FIN = 90, 300  # zoom par défaut du graphique : d'avril à octobre (numéro du jour)


@st.cache_data
def _pages():
    """Pages Markdown de la documentation (lues une seule fois)."""
    pages = {}
    for chemin in sorted(glob.glob(os.path.join(DOSSIER_PAGES, "*.md"))):
        with open(chemin, encoding="utf-8") as f:
            texte = f.read()
        titre = texte.splitlines()[0].lstrip("# ").strip()
        pages[titre] = texte
    return pages


@st.fragment
def afficher(analyse_a, hyp):
    """
    Fragment : changer de page dans le sommaire ne recalcule que cet onglet,
    pas toute l'application (c'était la cause de la lenteur).
    """
    pages = _pages()
    titres = list(pages)
    sommaire = titres[:2] + [PAGE_HYPOTHESES] + titres[2:3] + [PAGE_THETA] + titres[3:]
    col_nav, col_page = st.columns([1, 3])
    with col_nav:
        choix = st.radio("Sommaire", sommaire, key="methode_page", label_visibility="collapsed")
        st.caption("Pages générées depuis docs/sources/documentation.docx et hypotheses.xlsx : "
                   "une seule source pour l'interface et la documentation.")
    with col_page:
        if choix == PAGE_HYPOTHESES:
            st.markdown("### Hypothèses")
            st.caption("Toutes les valeurs utilisées par les calculs, avec leur source. "
                       "Modifiables dans docs/sources/hypotheses.xlsx.")
            df = pd.DataFrame(list(hyp.values()))
            df["valeur"] = df["valeur"].map(lambda v: f"{v:g}".replace(".", ",") if isinstance(v, float) else str(v))
            df = df[["libelle", "valeur", "unite", "reference", "statut", "source",
                                                   "lien", "explication"]]
            if PYARROW_DISPONIBLE:
                st.dataframe(df, hide_index=True, width="stretch", height=560,
                             column_config={"lien": st.column_config.LinkColumn("lien", display_text="ouvrir ↗"),
                                            "libelle": "hypothèse",
                                            "explication": st.column_config.TextColumn(width="large")})
            else:                                   # secours sans pyarrow : tableau HTML simple
                st.markdown(tableau_html(df.rename(columns={"libelle": "hypothèse"})), unsafe_allow_html=True)
        elif choix == PAGE_THETA:
            st.markdown("### Température fichier lissée : pourquoi deux calculs ?")
            s = analyse_a.serie
            if not s.annee_complete:
                st.info("Graphique disponible pour une année complète.")
                return
            tm = s.t.reshape(-1, 24).mean(axis=1)
            x = pd.date_range(f"{s.horodatage[0].year}-01-01", periods=tm.size, freq="D")
            re = moyenne_glissante_exterieure(s.t)
            en = theta_rm_en16798(tm)
            st.write("La température fichier lissée est une moyenne des jours précédents, où chaque jour compte un "
                     "peu moins que le suivant (notée θrm dans la méthode). La RE2020 la calcule par récurrence "
                     "(valeur 0 le 1er janvier) ; la norme EN 16798-1 sur les 7 derniers jours. "
                     f"Écart maximal de mai à septembre pour ce fichier : "
                     f"{nombre(np.nanmax(np.abs(re - en)[JOURS_ECART_MAX]))} °C.")
            fig = ga.deux_temperatures_lissees(x, re, en, valeur(hyp, "seuil_periode_adaptative"))
            fig.update_xaxes(range=[x[JOUR_ZOOM_DEBUT], x[JOUR_ZOOM_FIN]], rangeslider=dict(visible=True, thickness=0.08))
            afficher_graphique(fig)
        else:
            st.markdown(remplacer_reperes(pages[choix], hyp).replace("\n# ", "\n### ").replace("# ", "### ", 1))
