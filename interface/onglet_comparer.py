"""② COMPARER — le fichier de l'onglet Analyser face à un second fichier."""

import html

import pandas as pd
import streamlit as st

from calcul.hypotheses import remplacer_reperes, valeur
from calcul.indicateurs import jour_le_plus_chaud
from config.reglages import CORAIL, GRIS, INDIGO, TEAL, TRAIT
from interface import graphiques as g
from interface.onglet_analyser import CONFIG_PLOTLY

# ============================================================
# PARAMÈTRES
# ============================================================
ANNEE = g.ANNEE_SUPERPOSITION


def _fmt(v, unite):
    if v is None:
        return "—"
    return (f"{v:,.0f}".replace(",", " ")) + f" {unite}"


def _tableau(res_a, res_b, nom_a, nom_b, hyp):
    """Indicateurs côte à côte ; l'écart est exprimé « second fichier par rapport au premier »."""
    lignes = []
    for (d, ra), (_, rb) in zip(res_a, res_b):
        va, vb = ra.valeur, rb.valeur
        if va is None or vb is None:
            ecart = "—"
        else:
            e = round(vb) - round(va)
            couleur = CORAIL if e > 0 else (TEAL if e < 0 else GRIS)
            ecart = f'<b style="color:{couleur}">{"+" if e > 0 else ""}{e:,} {html.escape(d["unite"])}</b>'.replace(",", " ")
        lignes.append(f"<tr><td style='padding:6px 10px'>{html.escape(remplacer_reperes(d['libelle'], hyp))}</td>"
                      f'<td style="color:{TEAL};text-align:right;padding:6px 10px"><b>{_fmt(va, html.escape(d["unite"]))}</b></td>'
                      f'<td style="color:{INDIGO};text-align:right;padding:6px 10px"><b>{_fmt(vb, html.escape(d["unite"]))}</b></td>'
                      f'<td style="text-align:right;padding:6px 10px">{ecart}</td></tr>')
    entete = (f'<tr style="border-bottom:2px solid {GRIS}"><th style="text-align:left;padding:6px 10px">Indicateur</th>'
              f'<th style="color:{TEAL};text-align:right;padding:6px 10px">{html.escape(nom_a)}</th>'
              f'<th style="color:{INDIGO};text-align:right;padding:6px 10px">{html.escape(nom_b)}</th>'
              f'<th style="text-align:right;padding:6px 10px">Écart<br><span style="font-weight:400;font-size:.8rem">'
              f'{html.escape(nom_b)} par rapport à {html.escape(nom_a)}</span></th></tr>')
    st.markdown(f'<table style="width:100%;border-collapse:collapse;background:white;border:1px solid {TRAIT};'
                f'font-size:.92rem">{entete}{"".join(lignes)}</table>', unsafe_allow_html=True)


def afficher(analyse_a, res_a, choix_b, analyser_b, reglage, hyp):
    nom_a = analyse_a.serie.libelle
    options = list(choix_b.keys())
    # par défaut : même scénario dans une autre zone (sinon le premier fichier)
    libelle_a = analyse_a.serie.meta.get("libelle", "")
    meme = [i for i, o in enumerate(options) if o.endswith(libelle_a)]
    col_a, col_b = st.columns(2)
    col_a.markdown(f"**Premier fichier** (celui de l'onglet Analyser)<br>"
                   f"<span style='color:{TEAL};font-size:1.1rem;font-weight:700'>{html.escape(nom_a)}</span>",
                   unsafe_allow_html=True)
    nom_b = col_b.selectbox("Second fichier", options, index=meme[-1] if meme else 0, key="fichier_b")
    analyse_b, res_b = analyser_b(choix_b[nom_b])
    nom_b = analyse_b.serie.libelle
    if analyse_b.message_methode:
        st.caption(f"⚠ {nom_b} : {analyse_b.message_methode}")

    _tableau(res_a, res_b, nom_a, nom_b, hyp)
    fenetre = [pd.Timestamp(f"{ANNEE}-{valeur(hyp, 'ete_debut')}"), pd.Timestamp(f"{ANNEE}-{valeur(hyp, 'ete_fin')} 23:00")]
    sources = " · ".join(dict.fromkeys(filter(None, [analyse_a.serie.meta.get("source"), analyse_b.serie.meta.get("source")])))
    st.plotly_chart(g.ete_superpose(analyse_a, analyse_b, nom_a, nom_b, reglage["lignes"], fenetre, sources),
                    width="stretch", config=CONFIG_PLOTLY, theme=None)
    ja, jb = jour_le_plus_chaud(analyse_a, reglage["critere_journee"]), jour_le_plus_chaud(analyse_b, reglage["critere_journee"])
    if ja is not None and jb is not None:
        st.plotly_chart(g.journees_superposees(analyse_a, analyse_b, nom_a, nom_b, ja, jb, sources),
                        width="stretch", config=CONFIG_PLOTLY, theme=None)
    st.plotly_chart(g.cumul_dh(analyse_a, analyse_b, nom_a, nom_b, sources), width="stretch", config=CONFIG_PLOTLY, theme=None)
    st.caption("Les deux fichiers sont ramenés sur une même année pour être superposés jour par jour.")
