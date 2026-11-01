"""
============================================================
 GRAPHIQUES — outils communs (charte « Météo et Chaleur »)
============================================================
 Inspiré du graphique de référence (docs/references/) :
   - titre en gras + sous-titre gris qui dit comment lire ;
   - légendes avec des noms parlants ;
   - annotations directes des extrêmes (point + étiquette) ;
   - noms des mois en gras, séparateurs discrets ;
   - axes noirs, épais, terminés par des flèches ; zoom partout ;
   - titre d'axe (°C, °C.h) écrit à l'horizontale au-dessus de l'axe ;
   - dates au format long, en français (dictionnaire de langue passé à Plotly).
 Graphiques de l'onglet Analyser (et Créer, Méthode) : graphiques_analyse.py ;
 de l'onglet Comparer : graphiques_comparaison.py.

 CACHE : les fonctions décorées par @en_cache ne reconstruisent pas
 un graphique déjà fait pour les mêmes données (annuel : 218 → 14 ms).
 Une analyse est reconnue à ses températures, seuils et DH.
============================================================
"""

import hashlib

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from calcul.analyse import Analyse
from calcul.format_fr import LOCALE_PLOTLY, MOIS, nombre
from config.charte import (BLEU_FRAIS, EPAISSEUR_AXE, FOND_BANDE_CHAUDE, FOND_BANDE_FRAICHE, GRILLE, GRIS, GRIS_DOUX,
                           HAUTEUR_SECONDAIRE, INDIGO, JAUNE_FONCE, MARGE_BAS, MARGE_COTES, ORANGE_FONCE, POLICE,
                           PX_LEGENDE, PX_LIGNE_TITRE, PX_TITRE_AXE, SEPARATEUR, TAILLE_FLECHE)

# ============================================================
# PARAMÈTRES
# ============================================================
# --- Affichage Plotly (passé à chaque st.plotly_chart par afficher()) ---
CONFIG_PLOTLY = {"displaylogo": False, "scrollZoom": True, "locale": "fr", "locales": LOCALE_PLOTLY}
AFFICHER_SOURCES = False              # source sous chaque graphique : retirée (01/11) ; elle reste dans l'export et la doc
FORMAT_DATE = "%-d %B"                # « 10 juin » (mois en français grâce à CONFIG_PLOTLY)
FORMAT_SURVOL = "%A %-d %B, %-H h"    # « lundi 6 août, 16 h » au survol
MARGE_HAUT_DEGRES = 9                 # °C libres au-dessus du maximum (noms des mois + étiquettes)
PART_DH = 3.2                         # l'axe des DH monte à PART_DH × max (barres dans le tiers bas)
NB_GRAPHIQUES_EN_CACHE = 48           # graphiques gardés en mémoire (0,2 Mo au plus chacun, mesuré)


# ============================================================
# CACHE ET AFFICHAGE
# ============================================================

def _empreinte(a: Analyse) -> str:
    """Identité d'une analyse pour le cache : fichier, méthode, températures, seuils et DH heure par heure."""
    h = hashlib.md5(a.serie.t.tobytes() + a.seuil.tobytes() + a.dh_h.tobytes())
    h.update(f"{a.serie.id}|{a.serie.libelle}|{a.methode_effective}|{a.serie.horodatage[0]}".encode())
    return h.hexdigest()


def _empreinte_dates(index: pd.DatetimeIndex) -> str:
    """Identité d'un horodatage (Streamlit ne sait pas le reconnaître seul)."""
    return hashlib.md5(index.asi8.tobytes() + str(index.dtype).encode()).hexdigest()


en_cache = st.cache_data(hash_funcs={Analyse: _empreinte, pd.DatetimeIndex: _empreinte_dates},
                         max_entries=NB_GRAPHIQUES_EN_CACHE, show_spinner=False)


def afficher(fig):
    """Affiche un graphique avec la configuration commune (zoom à la molette, mois et virgule en français)."""
    st.plotly_chart(fig, width="stretch", config=CONFIG_PLOTLY, theme=None)


# ============================================================
# OUTILS DE STYLE
# ============================================================

def pas_rond(etendue, nb=4):
    """Pas de graduation « rond » (1, 2, 2,5, 5, 10…) pour environ nb intervalles."""
    brut = max(etendue / nb, 1e-9)
    puissance = 10 ** np.floor(np.log10(brut))
    return max(1.0, float(next(k * puissance for k in (1, 2, 2.5, 5, 10) if k * puissance >= brut)))


def _fleches(fig):
    """Flèches au bout des axes x (à droite) et y (en haut)."""
    # repères « x domain / y domain » : le bout de l'axe lui-même (avec un second axe, Plotly réduit le domaine
    # des X pour lui faire de la place : « paper » placerait la flèche trop loin à droite)
    for x, y, ax, ay in ((1, 0, -14, 0), (0, 1, 0, 14)):
        fig.add_annotation(x=x, y=y, xref="x domain", yref="y domain", ax=ax, ay=ay, text="", showarrow=True,
                           arrowhead=2, arrowsize=TAILLE_FLECHE, arrowwidth=EPAISSEUR_AXE, arrowcolor="black")


def titre_axe(fig, texte, cote="gauche", couleur=GRIS):
    """Titre d'axe horizontal, posé au-dessus de la graduation la plus haute (à gauche ou à droite)."""
    a_gauche = cote == "gauche"
    fig.add_annotation(x=0 if a_gauche else 1, y=1, xref="x domain", yref="y domain", showarrow=False,
                       xanchor="right" if a_gauche else "left", yanchor="bottom",
                       xshift=-8 if a_gauche else 8, yshift=4, text=f"<b>{texte}</b>",
                       font=dict(size=12, color=couleur))


def styler(fig, titre, sous_titre="", hauteur=HAUTEUR_SECONDAIRE, titre_y="°C", double_axe=False, source="",
           legende=True, axe_dates=True):
    """
    Titre gras + sous-titre gris, légende au-dessus du tracé, source en pied, axes noirs fléchés,
    titre de l'axe Y à l'horizontale. La marge du haut dépend du nombre de lignes du titre.
    """
    texte = f"<b>{titre}</b>" + (f"<br><span style='font-size:12px;color:{GRIS_DOUX}'>{sous_titre}</span>"
                                 if sous_titre else "")
    nb_lignes = titre.count("<br>") + 1 + (sous_titre.count("<br>") + 1 if sous_titre else 0)
    haut = 18 + PX_LIGNE_TITRE * nb_lignes + (PX_LEGENDE if legende else PX_TITRE_AXE)
    fig.update_layout(
        title=dict(text=texte, x=0, xanchor="left", xref="paper", yref="container", y=1 - 14 / hauteur,
                   yanchor="top", font=dict(size=16, color=GRIS, family=POLICE)),
        height=hauteur, margin=dict(l=MARGE_COTES, r=MARGE_COTES, t=haut, b=MARGE_BAS),
        plot_bgcolor="white", paper_bgcolor="white", showlegend=legende,
        font=dict(family=POLICE, color=GRIS), hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, font=dict(size=12),
                    traceorder="normal"),   # sinon Plotly inverse l'ordre dès qu'une aire « tonexty » existe
    )
    fig.update_xaxes(showline=True, linecolor="black", linewidth=EPAISSEUR_AXE, ticks="outside", tickcolor="black",
                     showgrid=False, zeroline=False, automargin=True,
                     **({"tickformat": FORMAT_DATE, "hoverformat": FORMAT_SURVOL} if axe_dates else {}))
    fig.update_yaxes(showline=True, linecolor="black", linewidth=EPAISSEUR_AXE, ticks="outside", tickcolor="black",
                     gridcolor=GRILLE, zeroline=False, tickformat=".0f", title_text="",
                     **({"secondary_y": False} if double_axe else {}))
    titre_axe(fig, titre_y)
    if source and AFFICHER_SOURCES:
        # la source sert de titre à l'axe des X : Plotly la place toujours sous les graduations
        # et sous le curseur de zoom, sans chevauchement (marge du bas ajustée automatiquement)
        fig.update_xaxes(title=dict(text=f"Source : {source}", font=dict(size=10, color=GRIS_DOUX), standoff=12))
    _fleches(fig)
    return fig


def axe_dh(fig, maximum, part=PART_DH):
    """Axe de droite des DH (jaune foncé) ; l'axe monte à part × maximum (plus part est faible, plus les barres sont hautes)."""
    haut_dh = max(float(maximum) * part, 1)
    fig.update_yaxes(title_text="", secondary_y=True, showgrid=False, showline=True, zeroline=False,
                     linecolor=JAUNE_FONCE, linewidth=EPAISSEUR_AXE, tickcolor=JAUNE_FONCE, ticks="outside",
                     tickfont=dict(color=JAUNE_FONCE), range=[0, haut_dh], dtick=pas_rond(haut_dh), tick0=0,
                     tickformat=".0f")
    titre_axe(fig, "°C.h", "droite", JAUNE_FONCE)


def lignes_horizontales(fig, lignes, sous_graphiques=False):
    """Lignes choisies par l'utilisateur (menu de gauche), sur l'axe des températures."""
    kw = {"secondary_y": False} if sous_graphiques else {}
    position = "top left" if sous_graphiques else "right"   # à droite, l'étiquette chevaucherait l'axe des DH
    for v in lignes:
        fig.add_hline(y=v, line=dict(color=INDIGO, width=1.4, dash="dash"), annotation_text=f"{v:g} °C",
                      annotation_position=position, annotation_font=dict(color=INDIGO, size=11), **kw)


def bandes_confort(fig, bas, haut, y_min, y_max):
    """
    Fond bleu clair sous le seuil frais (20 °C), fond orangé clair au-dessus du seuil chaud (28 °C),
    deux traits étiquetés. L'échelle est fixée à [y_min, y_max] pour que les bandes remplissent le tracé.
    """
    fig.add_hrect(y0=haut, y1=y_max, fillcolor=FOND_BANDE_CHAUDE, line_width=0, layer="below")
    fig.add_hrect(y0=y_min, y1=bas, fillcolor=FOND_BANDE_FRAICHE, line_width=0, layer="below")
    for v, c in ((haut, ORANGE_FONCE), (bas, BLEU_FRAIS)):
        fig.add_hline(y=v, line=dict(color=c, width=1.3, dash="dash"), annotation_text=f"<b>{v:g} °C</b>",
                      annotation_position="right", annotation_font=dict(color=c, size=11))
    fig.update_yaxes(range=[y_min, y_max])


def axe_mois(fig, debut, fin):
    """Noms des mois en gras en haut du tracé (au milieu de chaque mois) + séparateurs discrets entre mois.
    En haut plutôt que sous l'axe : ils ne chevauchent ni les dates ni le curseur de zoom."""
    debut, fin = pd.Timestamp(debut), pd.Timestamp(fin)
    for m in pd.date_range(debut.replace(day=1), fin, freq="MS"):
        milieu = m + pd.Timedelta(days=15)
        fig.add_annotation(x=milieu, y=1, xref="x", yref="paper", yanchor="top", showarrow=False,
                           text=f"<b>{MOIS[m.month - 1].capitalize()}</b>", font=dict(size=13, color=GRIS))
        fig.add_vline(x=m, line=dict(color=SEPARATEUR, width=1), layer="below")


def annoter(fig, x, y, texte, couleur, ax=40, ay=-40, secondary_y=None):
    """Point + trait + étiquette sur un extrême (style de l'image de référence)."""
    kw = dict(secondary_y=secondary_y) if secondary_y is not None else {}
    fig.add_trace(go.Scatter(x=[x], y=[y], mode="markers", marker=dict(color=couleur, size=9,
                             line=dict(color="white", width=1.5)), showlegend=False, hoverinfo="skip"), **kw)
    fig.add_annotation(x=x, y=y, text=texte, showarrow=True, arrowhead=0, arrowwidth=1.2, arrowcolor=couleur,
                       ax=ax, ay=ay, font=dict(size=12, color=GRIS), align="left",
                       bgcolor="rgba(255,255,255,0.85)", **({"yref": "y"} if secondary_y is not None else {}))



def ecart_texte(ecart):
    return f"{'+' if ecart >= 0 else ''}{nombre(ecart)} °C en moyenne"

