"""
============================================================
 COMPOSANTS — CSS, bandeau, cartes avec bulle « i »,
 bandeau des hypothèses actives, pied de page
============================================================
 La documentation est volontairement DISCRÈTE à l'écran :
   1. pastille « i » (bulle au survol) ;
   2. bandeau fin des hypothèses actives ;
   3. onglet « Méthode & sources » pour le détail.
============================================================
"""

import html

import streamlit as st

from calcul.hypotheses import MOTIF_REPERE, remplacer_reperes
from calcul.confort_ptc import PTC_VERSION
from config.reglages import (BLEU_CLAIR, BLEU_MENU, CARAMEL, CARAMEL_CLAIR, CORAIL, FOND, GRIS, GRIS_DOUX,
                             INDIGO, TEAL, TRAIT, VERSION, STATUT_VERSION)

# ============================================================
# PARAMÈTRES
# ============================================================
COULEURS_CARTES = {"dh": CORAIL, "dh_nuit": INDIGO, "heures_chaudes": CORAIL, "nuits_20": CARAMEL, "nuits_24": CORAIL,
                   "nuits_consecutives": CARAMEL, "t_moyenne": TEAL, "t_moyenne_nuit": INDIGO,
                   "journee_chaude": TEAL, "semaine_chaude": TEAL}
COULEURS_STATUT = {"sourcé": TEAL, "provisoire": "#C77D2E", "à préciser": CORAIL, "hypothèse": GRIS_DOUX}

CSS = f"""
<style>
  .stApp {{ background: {FOND}; }}
  [data-testid="stSidebar"] {{ background: {BLEU_MENU}; }}
  [data-testid="stSidebar"] h3 {{ color: {INDIGO}; font-size: 0.85rem; letter-spacing: .06em; margin-top: .6rem; }}
  header[data-testid="stHeader"] {{ background: transparent; }}
  [data-testid="stToolbarActions"], [data-testid="stMainMenu"], [data-testid="stAppDeployButton"] {{ display: none; }}
  .block-container {{ padding-top: 2.4rem; max-width: 1500px; }}
  /* Bandeau + menu */
  .bandeau {{ background: {INDIGO}; color: white; border-radius: 12px; padding: 14px 22px; display: flex;
              align-items: baseline; gap: 18px; margin-bottom: 6px; }}
  .bandeau .nom {{ font-size: 1.6rem; font-weight: 700; }}
  .bandeau .sous {{ color: #CFCBE6; font-size: .95rem; }}
  .bandeau .version {{ margin-left: auto; color: {BLEU_MENU}; font-size: .85rem; font-weight: 600; }}
  .stTabs [role="tablist"] {{ background: {INDIGO}; border-radius: 12px; padding: 6px 10px; gap: 8px; }}
  .stTabs [role="tab"] {{ color: #CFCBE6 !important; border-radius: 18px; padding: 6px 18px !important;
                          height: auto; background: transparent; }}
  .stTabs [role="tab"] p {{ font-size: 1rem; font-weight: 600; color: inherit; }}
  .stTabs [role="tab"][aria-selected="true"] {{ background: {BLEU_MENU}; color: {INDIGO} !important; }}
  .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display: none; }}
  /* Cartes */
  .cartes {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 6px 0 10px; }}
  @media (max-width: 900px) {{ .cartes {{ grid-template-columns: repeat(2, 1fr); }} }}
  .carte {{ background: white; border: 1px solid {TRAIT}; border-top: 5px solid var(--c); border-radius: 8px;
            padding: 10px 14px 8px; position: relative; }}
  .carte .titre {{ color: {GRIS_DOUX}; font-size: .85rem; }}
  .carte .valeur {{ font-size: 2rem; font-weight: 700; color: {GRIS}; line-height: 1.2; }}
  .carte .valeur span {{ font-size: .85rem; font-weight: 400; color: {GRIS_DOUX}; margin-left: 4px; }}
  .carte .detail {{ color: {GRIS_DOUX}; font-size: .75rem; }}
  .info {{ position: absolute; top: 8px; right: 10px; width: 18px; height: 18px; border-radius: 50%;
           border: 1.5px solid var(--c); color: var(--c); font: 700 11px/15px serif; text-align: center; cursor: help; }}
  .info .bulle {{ display: none; position: absolute; right: -8px; top: 24px; width: 270px; z-index: 50;
                  background: white; border: 1.5px solid var(--c); border-radius: 8px; padding: 10px 12px;
                  font: 400 .8rem/1.35 Inter, sans-serif; color: {GRIS}; text-align: left;
                  box-shadow: 0 4px 14px rgba(0,0,0,.12); }}
  .info:hover .bulle {{ display: block; }}
  .statut {{ display: inline-block; margin-top: 6px; padding: 1px 8px; border-radius: 10px; border: 1px solid;
             font-size: .72rem; font-weight: 600; }}
  /* Bandeau des hypothèses actives */
  .hypos {{ background: {CARAMEL_CLAIR}; border: 1px solid {CARAMEL}; border-radius: 18px; padding: 5px 12px;
            display: flex; flex-wrap: wrap; gap: 6px; align-items: center; font-size: .78rem; margin-bottom: 8px; }}
  .hypos b {{ margin-right: 4px; }}
  .hypos .puce {{ background: white; border: 1px solid {CARAMEL}; border-radius: 12px; padding: 1px 9px; }}
  .message {{ color: {CORAIL}; font-size: .85rem; margin: 2px 0 6px; }}
  .pied {{ color: {GRIS_DOUX}; font-size: .75rem; border-top: 1px solid {TRAIT}; margin-top: 18px; padding-top: 6px;
           display: flex; justify-content: space-between; }}
</style>
"""


# ============================================================
# COMPOSANTS
# ============================================================

def entete():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        f'<div class="bandeau"><span class="nom">☀ Météo et Chaleur</span>'
        f'<span class="sous">Analyser la météo sous l\'angle de l\'inconfort d\'été</span>'
        f'<span class="version">v{VERSION} · {STATUT_VERSION}</span></div>', unsafe_allow_html=True)


def _statuts_cites(texte, hyp):
    """Statuts non « sourcé » des hypothèses citées par [[hyp:…]] dans un texte."""
    return sorted({hyp[i]["statut"] for i in MOTIF_REPERE.findall(texte or "") if i in hyp
                   and hyp[i]["statut"] != "sourcé"})


def cartes(resultats, hyp):
    """Cartes d'indicateurs, dans l'ordre de indicateurs.csv, valeurs arrondies à l'unité."""
    blocs = []
    for d, r in resultats:
        c = COULEURS_CARTES.get(d["id"], TEAL)
        titre = html.escape(remplacer_reperes(d["libelle"], hyp))
        val = "—" if r.valeur is None else f"{r.valeur:,.0f}".replace(",", " ")
        bulle = html.escape(remplacer_reperes(d["bulle"], hyp))
        statuts = "".join(f'<br><span class="statut" style="color:{COULEURS_STATUT[s]};border-color:{COULEURS_STATUT[s]}">'
                          f'source : {s}</span>' for s in _statuts_cites(d["bulle"] + d["libelle"], hyp))
        blocs.append(
            f'<div class="carte" style="--c:{c}"><div class="titre">{titre}</div>'
            f'<div class="info">i<div class="bulle"><b>{titre}</b><br>{bulle}{statuts}'
            f'<br><span style="color:{TEAL};font-weight:600">Détail : onglet Méthode & sources</span></div></div>'
            f'<div class="valeur">{val}<span>{html.escape(d["unite"])}</span></div>'
            f'<div class="detail">{html.escape(r.detail)}</div></div>')
    st.markdown(f'<div class="cartes">{"".join(blocs)}</div>', unsafe_allow_html=True)


def bandeau_hypotheses(reglage, analyse, hyp, libelles_semaine, aller_methode=None):
    puces = []
    if analyse.methode_effective == "RE2020":
        puces += [f"RE2020 · seuil {hyp['seuil_nuit_dh']['valeur']:g} → {hyp['seuil_jour_max']['valeur']:g} °C", "température extérieure lissée (RE2020)"]
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


def pied():
    st.markdown(
        f'<div class="pied"><span>Note : indicateur climatique — DH calculés sur la température extérieure, '
        f'pas le DH d\'un bâtiment · méthode RE2020 (arrêté du 4 août 2021, annexe III)</span>'
        f'<span>outil v{VERSION} · pythermalcomfort {PTC_VERSION}</span></div>', unsafe_allow_html=True)
