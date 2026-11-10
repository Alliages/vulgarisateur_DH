"""
============================================================
 GRAPHIQUES DE L'ONGLET ANALYSER (et Créer, Méthode & sources)
============================================================
 Année heure par heure, semaine / journée la plus chaude, et les
 deux façons de lisser la température (page Méthode).
 Outils de style et cache : graphiques_communs.py.
============================================================
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from calcul.format_fr import heure, jour_court, jour_mois, nombre
from config.charte import (BLEU_MENU, BLEU_NUIT_CLAIR, BLEU_NUIT_FONCE, CARAMEL, CORAIL, GRIS, GRIS_DOUX, GRIS_INOCCUPE,
                           HAUTEUR_PRINCIPAL, HAUTEUR_SECONDAIRE, SEPARATEUR, TEAL)
from interface.couleurs import transparent
from interface.graphiques_communs import (MARGE_HAUT_DEGRES, PART_DH, annoter, axe_dh, axe_mois, en_cache,
                                          lignes_horizontales, styler)

# ============================================================
# PARAMÈTRES
# ============================================================
PART_DH_PERIODE = 1.5                 # semaine et journée : barres sur les deux tiers de la hauteur
# --- Graphique de l'année : bande des nuits sous les DH ---
PART_BANDE_NUITS = 0.10               # hauteur de la bande des nuits (part du tracé)
HAUTEUR_NUIT_TROPICALE, HAUTEUR_NUIT_TRES_CHAUDE = 0.55, 0.95   # dans la bande (1 = toute la bande)
LARGEUR_BARRE_NUIT_MS = 16 * 3600 * 1000   # largeur d'une barre de nuit (lisible au dézoom)
DEGRES_BANDE_NUITS_ANNEE = 7          # °C ajoutés sous le minimum de température (place de la bande)
DH_MAX_ANNEE, PAS_DH_ANNEE = 300, 50  # axe des DH du jour : haut vers 300 °C.h, graduations de 50
MARGE_HAUT_DH = 1.06                  # l'axe monte 6 % au-dessus de la dernière graduation


# ============================================================
# ANALYSER — série de l'année
# ============================================================

@en_cache
def serie_annuelle(analyse, lignes, fenetre, source, seuil_tropical=20.0, seuil_tres_chaud=24.0, nuit_debut=22,
                   nuit_fin=6):
    """
    Températures du fichier (moyenne du jour, bande min-max rouge clair, horaire fin), DH du jour en barres
    caramel, et en bas une bande « nuits » : une barre bleue par nuit ≥ 20 °C (bleu nuit foncé si ≥ 24 °C).
    Seul le Tmax est annoté. Zoom par la molette ou le curseur.
    """
    s, jours, nuits = analyse.serie, analyse.jours, analyse.nuits_detail
    midi = jours.index + pd.Timedelta(hours=12)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    # 1. Températures du fichier
    fig.add_trace(go.Scatter(x=midi, y=jours["tmax"], line=dict(width=0), showlegend=False, hoverinfo="skip"),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=midi, y=jours["tmin"], fill="tonexty", fillcolor=transparent(CORAIL, 0.18),
                             line=dict(width=0), name="Variation du jour (min → max)", hoverinfo="skip"),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=s.horodatage, y=s.t, mode="lines", name="Heure par heure",
                             line=dict(color=CORAIL, width=0.7), opacity=0.35, hovertemplate="%{y:.1f} °C"),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=midi, y=jours["tmoy"], mode="lines", name="Moyenne de la journée",
                             line=dict(color=CORAIL, width=2.4), hovertemplate="moyenne %{y:.1f} °C"),
                  secondary_y=False)
    # 2. DH du jour (caramel plein), au-dessus de la bande des nuits
    fig.add_trace(go.Bar(x=midi, y=jours["dh"], name="DH du jour", marker_color=CARAMEL,
                         hovertemplate="DH du jour %{y:.0f} °C.h"), secondary_y=True)
    # 3. Nuits ≥ 20 °C : une barre par nuit dans la bande basse (axe y3 propre aux nuits, invisible)
    chaudes = nuits[nuits["tmin"] >= seuil_tropical]
    tres_chaudes = chaudes["tmin"] >= seuil_tres_chaud
    milieu_nuit = (24 - nuit_debut + nuit_fin) / 2
    for masque, couleur, hauteur, nom in (
            (~tres_chaudes, BLEU_NUIT_CLAIR, HAUTEUR_NUIT_TROPICALE, "Nuit tropicale"),
            (tres_chaudes, BLEU_NUIT_FONCE, HAUTEUR_NUIT_TRES_CHAUDE, "Nuit très chaude")):
        groupe = chaudes[masque]
        fig.add_trace(go.Bar(x=groupe.index + pd.Timedelta(hours=nuit_debut + milieu_nuit), y=[hauteur] * len(groupe),
                             width=LARGEUR_BARRE_NUIT_MS, marker_color=couleur, name=nom, yaxis="y3",
                             customdata=[f"nuit du {jour_mois(d)} : {nombre(t)} °C au plus bas"
                                         for d, t in groupe["tmin"].items()],
                             hovertemplate="%{customdata}<extra></extra>", showlegend=True))
    # 4. Tmax : la seule annotation
    i_max = int(np.argmax(s.t))
    t_max = s.horodatage[i_max]
    annoter(fig, t_max, s.t[i_max], f"<b>Tmax : {nombre(s.t[i_max])} °C</b><br>{jour_mois(t_max)} à {heure(t_max)}",
            CORAIL, ax=95, ay=-22, secondary_y=False)
    styler(fig, f"Températures fichier · {s.libelle}",
           f"Température fichier · DH du jour · Nuits tropicales (≥ {seuil_tropical:g} °C) et très chaudes "
           f"(≥ {seuil_tres_chaud:g} °C)", HAUTEUR_PRINCIPAL, double_axe=True, source=source)
    # Axe des DH : de la couleur des barres, haut vers 300 °C.h (plus si un jour dépasse), graduations de 50 ;
    # son zéro est relevé pour laisser la bande des nuits dessous
    haut_dh = max(DH_MAX_ANNEE, float(np.ceil(float(jours["dh"].max() or 0) * 1.1 / PAS_DH_ANNEE) * PAS_DH_ANNEE))
    sommet = haut_dh * MARGE_HAUT_DH                      # la dernière graduation reste sous le titre « °C.h »
    bas_dh = -sommet * PART_BANDE_NUITS / (1 - PART_BANDE_NUITS)
    axe_dh(fig, haut_dh / PART_DH)
    fig.update_yaxes(range=[bas_dh, sommet], secondary_y=True, tickvals=list(range(0, int(haut_dh) + 1, PAS_DH_ANNEE)))
    fig.add_hline(y=0, line=dict(color="#C9C6BF", width=1), secondary_y=True)
    fig.update_layout(yaxis3=dict(overlaying="y", range=[0, 1 / PART_BANDE_NUITS], visible=False, fixedrange=True),
                      barmode="overlay", bargap=0.15)
    for texte, couleur, y in ((f"nuits ≥ {seuil_tres_chaud:g} °C", BLEU_NUIT_FONCE, PART_BANDE_NUITS * 0.78),
                              (f"nuits ≥ {seuil_tropical:g} °C", BLEU_NUIT_CLAIR, PART_BANDE_NUITS * 0.30)):
        fig.add_annotation(x=0.004, xref="paper", y=y, yref="paper", xanchor="left", yanchor="middle",
                           text=f"<b>{texte}</b>", showarrow=False, font=dict(size=11, color=couleur))
    lignes_horizontales(fig, lignes, sous_graphiques=True)
    axe_mois(fig, s.horodatage[0], s.horodatage[-1])
    # Températures : un peu de place sous le minimum pour la bande des nuits, pas de graduation dedans
    bas_t = float(np.floor(np.min(s.t) / 5) * 5)
    fig.update_yaxes(range=[bas_t - DEGRES_BANDE_NUITS_ANNEE, float(np.max(s.t)) + MARGE_HAUT_DEGRES],
                     tickvals=list(range(int(bas_t) + 10, int(np.max(s.t)) + 10, 10)), secondary_y=False)
    fig.update_xaxes(type="date", rangeslider=dict(visible=True, thickness=0.07, bgcolor="#EEF8FF"),
                     range=list(fenetre) if fenetre else None)
    return fig


# ============================================================
# ANALYSER / CRÉER — semaine ou journée, style Excel
# ============================================================

def _zones_inoccupees(fig, x, occupe):
    """Bandes grises sur les heures d'absence + entrée de légende."""
    if occupe is None or occupe.all():
        return
    libres = ~np.asarray(occupe)
    pas = pd.Timedelta(hours=1)
    debut = None
    for i, libre in enumerate(np.append(libres, False)):
        if libre and debut is None:
            debut = x[i]
        if not libre and debut is not None:
            fig.add_vrect(x0=debut - pas / 2, x1=x[i - 1] + pas / 2, fillcolor=GRIS_INOCCUPE, line_width=0, layer="below")
            debut = None
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="Absents (scénario RE2020)",
                             marker=dict(symbol="square", size=12, color="rgba(39,41,50,0.15)")))



@en_cache
def courbe_dh(t, seuil, dh, x, titre, sous_titre="", echelle="semaine", occupe=None, source="", legende=True):
    """
    Température (corail), seuil (gris), DH en barres caramel (axe de droite jaune foncé).
    echelle = "semaine" (jours en graduation) ou "jour" (heures + min/max annotés).
    Pas de lignes horizontales utilisateur sur ces graphiques.
    """
    x = pd.DatetimeIndex(x)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=x, y=dh, name="DH de l'heure", marker_color=CARAMEL, opacity=0.9,
                         hovertemplate="DH %{y:.1f} °C.h"), secondary_y=True)
    fig.add_trace(go.Scatter(x=x, y=seuil, name="Seuil d'inconfort", line=dict(color=GRIS, width=1.3, shape="hv"),
                             hovertemplate="seuil %{y:.0f} °C"), secondary_y=False)
    fig.add_trace(go.Scatter(x=x, y=t, name="Température", line=dict(color=CORAIL, width=2.4),
                             hovertemplate="%{y:.1f} °C"), secondary_y=False)
    _zones_inoccupees(fig, x, occupe)   # après les courbes : sa trace vide ne doit pas fixer le type de l'axe
    styler(fig, titre, sous_titre, double_axe=True, source=source, legende=legende)
    fig.update_xaxes(type="date")
    axe_dh(fig, np.max(dh), PART_DH_PERIODE)
    if echelle == "semaine":
        midis = [d + pd.Timedelta(hours=12) for d in pd.date_range(x[0].normalize(), x[-1].normalize(), freq="D")]
        fig.update_xaxes(tickvals=midis, ticktext=[jour_court(d) for d in midis])
        for d in pd.date_range(x[0].normalize() + pd.Timedelta(days=1), x[-1].normalize(), freq="D"):
            fig.add_vline(x=d, line=dict(color=SEPARATEUR, width=1), layer="below")
    else:
        heures = [x[0].normalize() + pd.Timedelta(hours=h) for h in range(0, 24, 3)]
        fig.update_xaxes(tickvals=heures, ticktext=[heure(h) for h in heures])
        i_max, i_min = int(np.argmax(t)), int(np.argmin(t))
        annoter(fig, x[i_max], t[i_max], f"<b>{nombre(t[i_max])} °C</b>", CORAIL, ax=0, ay=-28, secondary_y=False)
        annoter(fig, x[i_min], t[i_min], f"{nombre(t[i_min])} °C", GRIS_DOUX, ax=0, ay=28, secondary_y=False)
    fig.update_layout(bargap=0.1)
    return fig


# ============================================================
# MÉTHODE & SOURCES
# ============================================================

@en_cache
def deux_temperatures_lissees(x, re2020, en16798, seuil):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=re2020, name="RE2020 (référence de calcul)", line=dict(color=TEAL, width=2.6),
                             hovertemplate="%{y:.1f} °C"))
    fig.add_trace(go.Scatter(x=x, y=en16798, name="Norme EN 16798-1",
                             line=dict(color=BLEU_MENU, width=2, dash="dash"), hovertemplate="%{y:.1f} °C"))
    fig.add_hline(y=seuil, line=dict(color=CORAIL, width=1, dash="dot"), annotation_text=f"{seuil:g} °C",
                  annotation_position="right", annotation_font=dict(color=CORAIL))
    styler(fig, "Température fichier lissée : deux façons de la calculer",
           f"Au-dessus de {seuil:g} °C, la méthode RE2020 compte les DH (période de confort adaptatif)",
           HAUTEUR_SECONDAIRE)
    fig.update_xaxes(hoverformat="%A %-d %B")
    tout = np.concatenate([np.asarray(re2020, float), np.asarray(en16798, float)])
    fig.update_yaxes(range=[float(np.floor(np.nanmin(tout) / 5) * 5) - 2, float(np.nanmax(tout)) + 6])   # place pour les mois
    axe_mois(fig, x[0], x[-1])
    return fig
