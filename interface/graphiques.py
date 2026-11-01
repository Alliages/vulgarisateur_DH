"""
============================================================
 GRAPHIQUES — Plotly, charte « Météo et Chaleur »
============================================================
 Inspiré du graphique de référence (docs/references/) :
   - titre en gras + sous-titre gris qui dit comment lire ;
   - légendes avec des noms parlants ;
   - annotations directes des extrêmes (point + étiquette) ;
   - aire colorée entre deux courbes + écart moyen écrit ;
   - noms des mois en gras, séparateurs discrets ;
   - source en pied de graphique ;
   - axes noirs, épais, terminés par des flèches ; zoom partout ;
   - titre d'axe (°C, °C.h) écrit à l'horizontale au-dessus de l'axe ;
   - dates au format long, en français (dictionnaire de langue passé à Plotly).
============================================================
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config.reglages import (BLEU_FRAIS, BLEU_MENU, CARAMEL, COULEUR_FICHIER_1, COULEUR_FICHIER_2, CORAIL, GRIS,
                             GRIS_DOUX, INDIGO, TEAL)
from interface.format_fr import LOCALE_PLOTLY, MOIS, heure, jour_court, jour_mois, nombre

# ============================================================
# PARAMÈTRES
# ============================================================
# --- Affichage Plotly (à passer à chaque st.plotly_chart) ---
CONFIG_PLOTLY = {"displaylogo": False, "scrollZoom": True, "locale": "fr", "locales": LOCALE_PLOTLY}

# --- Style ---
EPAISSEUR_AXE = 2
TAILLE_FLECHE = 1.4
POLICE = "Inter, Segoe UI, sans-serif"
JAUNE_FONCE = "#B8860B"               # axe, texte et titre d'axe des DH
ORANGE_FONCE = "#B5651D"              # trait et texte de la bande « au-dessus de 28 °C »
GRIS_INOCCUPE = "rgba(39,41,50,0.08)" # heures d'absence (scénario d'occupation)
GRILLE = "#ECEAE6"
SEPARATEUR = "#E2E0DB"                # traits verticaux entre jours / mois
FOND_BANDE_CHAUDE = "rgba(247,178,103,0.22)"   # caramel clair : au-dessus du seuil chaud (28 °C)
FOND_BANDE_FRAICHE = "rgba(72,190,255,0.13)"   # bleu clair : en dessous du seuil frais (20 °C)

# --- Contenu ---
AFFICHER_SOURCES = False              # source sous chaque graphique : retirée (01/11) ; elle reste dans l'export et la doc

# --- Dimensions (px) ---
HAUTEUR_PRINCIPAL = 540
HAUTEUR_SECONDAIRE = 400
HAUTEUR_COMPARAISON = 580
MARGE_COTES = 64                      # à gauche et à droite (titres d'axe horizontaux compris)
MARGE_BAS = 20                        # sous l'axe (Plotly agrandit selon graduations, curseur, source)
PX_LIGNE_TITRE = 21                   # une ligne de titre / sous-titre
PX_LEGENDE = 34                       # légende (une ligne)
PX_TITRE_AXE = 24                     # titre d'axe horizontal au-dessus du tracé (sans légende)

# --- Échelles ---
DEGRES_BANDE_NUITS = 10              # °C libres sous les courbes de l'été superposé (étiquettes de nuit)
Y_ECART_ETE = 0.72                    # position (paper) de l'écart moyen écrit : haut gauche, sous les étiquettes Tmax
DEGRES_ETIQUETTE_NUIT = 2.5           # °C au-dessus du maximum : hauteur de l'étiquette « nuit la plus chaude »
MARGE_HAUT_DEGRES = 9                 # °C libres au-dessus du maximum (noms des mois + étiquettes)
PART_DH = 3.2                         # année : l'axe des DH monte à PART_DH × max (barres dans le tiers bas)
PART_DH_PERIODE = 1.5                 # semaine et journée : barres sur les deux tiers de la hauteur

# --- Nuits chaudes (Comparer) : une case par nuit, du clair au foncé ---
COULEURS_NUITS = ["#ECEAF3", "#8C86B8", INDIGO]   # < 20 °C · tropicale (≥ 20 °C) · très chaude (≥ 24 °C)
HAUTEUR_NUITS = 350
FOND_NUIT_CHAUDE = "rgba(140,134,184,0.16)"   # bande violette claire sur chaque nuit tropicale (graphique de l'année)
DEMI_HAUTEUR_CASE = 0.29              # demi-hauteur d'une rangée de cases (unités de l'axe Y) : cadre ajusté aux cases
ECART_LIGNES_NUITS = 46               # px entre les deux rangées de nuits (place pour l'étiquette « de suite »)
FORMAT_DATE = "%-d %B"                # « 10 juin » (mois en français grâce à CONFIG_PLOTLY)
FORMAT_SURVOL = "%A %-d %B, %-H h"    # « lundi 6 août, 16 h » au survol
ANNEE_SUPERPOSITION = 2018            # années ramenées sur une même année pour superposer


# ============================================================
# OUTILS DE STYLE
# ============================================================

def transparent(hexa, alpha):
    h = hexa.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


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
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="Absents (scénario RE2020, provisoire)",
                             marker=dict(symbol="square", size=12, color="rgba(39,41,50,0.15)")))


def _ecart_texte(ecart):
    return f"{'+' if ecart >= 0 else ''}{nombre(ecart)} °C en moyenne"


# ============================================================
# ANALYSER — série de l'année
# ============================================================

def serie_annuelle(analyse, lignes, fenetre, source, seuil_tropical=20.0, seuil_tres_chaud=24.0, nuit_debut=22,
                   nuit_fin=6):
    """Moyenne journalière + bande min-max (rouge clair) + horaire fin + DH du jour en barres jaunes,
    nuits ≥ 20 °C (bandes et points violets), extrêmes annotés, zoom."""
    s, jours = analyse.serie, analyse.jours
    midi = jours.index + pd.Timedelta(hours=12)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=midi, y=jours["dh"], name="DH du jour", marker_color=CARAMEL, opacity=0.85,
                         hovertemplate="DH du jour %{y:.0f} °C.h"), secondary_y=True)
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
    fig.add_trace(go.Scatter(x=s.horodatage, y=analyse.seuil, mode="lines", name="Seuil DH", visible="legendonly",
                             line=dict(color=GRIS, width=1, shape="hv"), hovertemplate="seuil %{y:.0f} °C"),
                  secondary_y=False)
    # Nuits chaudes : bande violette claire sur la nuit + point au minimum de la nuit (couleurs de Comparer)
    nuits = analyse.nuits_detail
    for seuil, plafond, couleur, nom, taille in (
            (seuil_tropical, seuil_tres_chaud, COULEURS_NUITS[1], f"Nuit tropicale (min ≥ {seuil_tropical:g} °C)", 7),
            (seuil_tres_chaud, np.inf, COULEURS_NUITS[2], f"Nuit très chaude (min ≥ {seuil_tres_chaud:g} °C)", 8)):
        choix = nuits[(nuits["tmin"] >= seuil) & (nuits["tmin"] < plafond)]
        if choix.empty:
            continue
        fig.add_trace(go.Scatter(x=choix["quand"], y=choix["tmin"], mode="markers", name=nom,
                                 marker=dict(color=couleur, size=taille, line=dict(color="white", width=1)),
                                 customdata=[f"nuit du {jour_mois(d)}" for d in choix.index],
                                 hovertemplate="%{customdata} : %{y:.1f} °C au plus bas<extra></extra>"),
                      secondary_y=False)
    for d in nuits.index[nuits["tmin"] >= seuil_tropical]:
        fig.add_vrect(x0=d + pd.Timedelta(hours=nuit_debut), x1=d + pd.Timedelta(days=1, hours=nuit_fin),
                      fillcolor=FOND_NUIT_CHAUDE, line_width=0, layer="below")
    # Extrêmes : température maximale et nuit la plus chaude (minimum nocturne le plus élevé)
    i_max = int(np.argmax(s.t))
    t_max = s.horodatage[i_max]
    annoter(fig, t_max, s.t[i_max], f"<b>Tmax : {nombre(s.t[i_max])} °C</b><br>{jour_mois(t_max)} à {heure(t_max)}",
            CORAIL, ax=95, ay=-22, secondary_y=False)
    if not analyse.nuits_detail.empty:
        n = analyse.nuits_detail.loc[analyse.nuits_detail["tmin"].idxmax()]
        # étiquette dans la bande libre du haut, à gauche (Tmax est à droite) : elle ne masque pas les courbes
        fig.add_trace(go.Scatter(x=[n["quand"]], y=[n["tmin"]], mode="markers", showlegend=False, hoverinfo="skip",
                                 marker=dict(color=INDIGO, size=9, line=dict(color="white", width=1.5))),
                      secondary_y=False)
        fig.add_annotation(x=n["quand"], y=n["tmin"], xref="x", yref="y", ax=-150, ayref="y",
                           ay=float(np.max(s.t)) + DEGRES_ETIQUETTE_NUIT, showarrow=True, arrowhead=0,
                           arrowwidth=1.2, arrowcolor=INDIGO, font=dict(size=12, color=GRIS), align="left",
                           bgcolor="rgba(255,255,255,0.9)",
                           text=f"<b>Nuit la plus chaude : {nombre(n['tmin'])} °C au plus bas</b><br>"
                                f"nuit du {jour_mois(n.name)} ({heure(n['quand'])})")
    styler(fig, f"Température extérieure · {s.libelle}",
           "Courbe : moyenne de chaque journée · rouge clair : écart entre le minimum et le maximum du jour · "
           "trait fin : heure par heure<br>"
           f"barres jaunes : DH du jour · violet : nuits ≥ {seuil_tropical:g} °C (point au minimum de la nuit). "
           "Molette ou curseur pour zoomer.",
           HAUTEUR_PRINCIPAL, double_axe=True, source=source)
    axe_dh(fig, jours["dh"].max() if len(jours) else 1)
    lignes_horizontales(fig, lignes, sous_graphiques=True)
    axe_mois(fig, s.horodatage[0], s.horodatage[-1])
    fig.update_yaxes(range=[float(np.floor(np.min(s.t) / 5) * 5), float(np.max(s.t)) + MARGE_HAUT_DEGRES],
                     secondary_y=False)
    fig.update_xaxes(type="date", rangeslider=dict(visible=True, thickness=0.07, bgcolor="#EEF8FF"),
                     range=list(fenetre) if fenetre else None)
    fig.update_layout(bargap=0.15)
    return fig


# ============================================================
# ANALYSER / CRÉER — semaine ou journée, style Excel
# ============================================================

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
# COMPARER — fichier de l'onglet Analyser (corail) / second fichier (bleu canard)
# ============================================================

def _superposable(index):
    """Ramène des dates sur une même année pour superposer deux fichiers."""
    return pd.DatetimeIndex([d.replace(year=ANNEE_SUPERPOSITION) for d in index])


def _deux(a, b, nom_a, nom_b):
    """(analyse, nom, couleur) des deux fichiers, dans l'ordre de l'onglet."""
    return ((a, nom_a, COULEUR_FICHIER_1), (b, nom_b, COULEUR_FICHIER_2))


def ete_superpose(a, b, nom_a, nom_b, lignes, fenetre, source):
    """Moyennes journalières des deux fichiers + aire de l'écart + maximums et nuits les plus chaudes annotés."""
    ja, jb = a.jours.copy(), b.jours.copy()
    ja.index, jb.index = _superposable(ja.index), _superposable(jb.index)
    commun = ja.index.intersection(jb.index)
    fig = go.Figure()
    if len(commun):
        haut = np.maximum(ja.loc[commun, "tmoy"], jb.loc[commun, "tmoy"])
        bas = np.minimum(ja.loc[commun, "tmoy"], jb.loc[commun, "tmoy"])
        fig.add_trace(go.Scatter(x=commun + pd.Timedelta(hours=12), y=haut, line=dict(width=0), showlegend=False,
                                 hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=commun + pd.Timedelta(hours=12), y=bas, fill="tonexty", line=dict(width=0),
                                 fillcolor=transparent(CARAMEL, 0.35), name="Écart entre les deux fichiers",
                                 legendrank=1001, hoverinfo="skip"))
    for (an, nom, c), jours in zip(_deux(a, b, nom_a, nom_b), (ja, jb)):
        fig.add_trace(go.Scatter(x=jours.index + pd.Timedelta(hours=12), y=jours["tmoy"], name=nom,
                                 line=dict(color=c, width=2.6), hovertemplate="%{y:.1f} °C"))
    # Écart moyen sur la fenêtre d'été, écrit en haut à gauche (sous les noms des mois, loin des maximums)
    f0, f1 = pd.Timestamp(fenetre[0]), pd.Timestamp(fenetre[1])
    ete = commun[(commun >= f0) & (commun <= f1)]
    if len(ete):
        ecart = float((jb.loc[ete, "tmoy"] - ja.loc[ete, "tmoy"]).mean())
        fig.add_annotation(x=0.01, xref="paper", y=Y_ECART_ETE, yref="paper", xanchor="left", yanchor="top",
                           showarrow=False, font=dict(size=14, color="#9C5A12"), align="left",
                           text=f"<b>{_ecart_texte(ecart)}</b><br>{nom_b} par rapport à {nom_a}")
    # Maximums horaires : étiquette du plus tôt à gauche, du plus tard à droite (au-dessus des courbes)
    maxima, nuits = [], []
    for an, nom, c in _deux(a, b, nom_a, nom_b):
        i = int(np.argmax(an.serie.t))
        maxima.append((_superposable(an.serie.horodatage[i:i + 1])[0], an.serie.t[i], an.serie.horodatage[i], nom, c))
        if not an.nuits_detail.empty:
            n = an.nuits_detail.loc[an.nuits_detail["tmin"].idxmax()]
            nuits.append((_superposable(pd.DatetimeIndex([n["quand"]]))[0], n["tmin"], n.name, nom, c))
    maxima.sort(key=lambda m: m[0])
    for (x, t, quand, nom, c), ax, ay in zip(maxima, (-130, 130), (-14, -26)):
        annoter(fig, x, t, f"<b>Tmax {nom} : {nombre(t)} °C</b><br>{jour_mois(quand)} à {heure(quand)}", c, ax=ax, ay=ay)
    # Échelle : en haut, place pour les mois et les Tmax ; en bas, une bande libre pour les étiquettes de nuit
    y_bas = 0.0
    if len(ete):
        bas_y = float(min(ja.loc[ete, "tmoy"].min(), jb.loc[ete, "tmoy"].min()))
        y_bas = float(np.floor(bas_y / 5) * 5 - DEGRES_BANDE_NUITS)
        fig.update_yaxes(range=[y_bas, max(a.serie.t.max(), b.serie.t.max()) + MARGE_HAUT_DEGRES])
    # Nuits les plus chaudes (minimum nocturne le plus élevé) : point sur la nuit, étiquette dans la bande libre
    # du bas (ayref = axe y : position en °C), pour ne pas masquer les courbes
    nuits.sort(key=lambda m: m[0])
    for (x, t, nuit, nom, c), ax in zip(nuits, (-140, 140)):
        fig.add_trace(go.Scatter(x=[x], y=[t], mode="markers", showlegend=False, hoverinfo="skip",
                                 marker=dict(color=c, size=9, symbol="diamond", line=dict(color="white", width=1.5))))
        fig.add_annotation(x=x, y=t, ax=ax, ayref="y", ay=y_bas + DEGRES_BANDE_NUITS / 2, showarrow=True, arrowhead=0,
                           arrowwidth=1, arrowcolor=c, font=dict(size=12, color=GRIS), align="center",
                           bgcolor="rgba(255,255,255,0.9)",
                           text=f"<b>Nuit la + chaude · {nom} : {nombre(t)} °C</b><br>au plus bas, nuit du {jour_mois(nuit)}")
    styler(fig, "L'été superposé : température moyenne de chaque journée",
           "Aire orange : écart entre les deux fichiers · points : température maximale et nuit la plus chaude "
           "de chaque fichier (heure par heure)", HAUTEUR_COMPARAISON, source=source)
    lignes_horizontales(fig, lignes)
    axe_mois(fig, f0, f1)
    fig.update_xaxes(range=[f0, f1], rangeslider=dict(visible=True, thickness=0.07), hoverformat="%A %-d %B")
    return fig


def _profils(a, b, debut_a, debut_b, nb_heures):
    """Températures horaires des deux périodes (même longueur)."""
    sortie = []
    for an, d in ((a, debut_a), (b, debut_b)):
        i0 = an.serie.horodatage.get_indexer([d])[0]
        sortie.append(an.serie.t[i0:i0 + nb_heures])
    return sortie


def _echelle_bandes(profils, bas, haut):
    """Échelle qui laisse voir les deux bandes même si les courbes ne les atteignent pas."""
    y_min = min(float(np.min(profils)) - 2, bas - 3)
    y_max = max(float(np.max(profils)) + 4, haut + 3)
    return np.floor(y_min), np.ceil(y_max)


def journees_superposees(a, b, nom_a, nom_b, jour_a, jour_b, bas, haut, source):
    """Journée la plus chaude de chaque fichier, heure par heure, sur fonds bleu (< bas) et orangé (> haut)."""
    fig = go.Figure()
    h = np.arange(24)
    profils = _profils(a, b, jour_a, jour_b, 24)
    for (an, nom, c), p, d in zip(_deux(a, b, nom_a, nom_b), profils, (jour_a, jour_b)):
        fig.add_trace(go.Scatter(x=h, y=p, mode="lines+markers", marker=dict(size=6),
                                 name=f"{nom} · {jour_mois(d)} (moyenne {nombre(p.mean())} °C)",
                                 line=dict(color=c, width=2.4), hovertemplate="%{y:.1f} °C"))
        i = int(np.argmax(p))
        fig.add_annotation(x=i, y=p[i], text=f"<b>{nombre(p[i])} °C</b>", showarrow=False, yshift=14,
                           font=dict(color=c, size=12))
    y_min, y_max = _echelle_bandes(profils, bas, haut)
    fig.add_annotation(x=11.5, y=0.97, yref="paper", yanchor="top", showarrow=False,
                       font=dict(size=14, color="#9C5A12"), bgcolor="rgba(255,255,255,0.85)",
                       text=f"<b>{_ecart_texte(float((profils[1] - profils[0]).mean()))}</b>")
    styler(fig, "Journée la plus chaude de chaque fichier, heure par heure",
           f"Fond orangé : au-dessus de {haut:g} °C · fond bleu : en dessous de {bas:g} °C", HAUTEUR_SECONDAIRE,
           source=source, axe_dates=False)
    bandes_confort(fig, bas, haut, y_min, y_max)
    fig.update_xaxes(tickvals=list(range(0, 24, 3)), ticktext=[f"{k} h" for k in range(0, 24, 3)],
                     range=[-0.5, 23.5])
    return fig


def semaines_superposees(a, b, nom_a, nom_b, debut_a, debut_b, nb_jours, bas, haut, source):
    """Semaine la plus chaude de chaque fichier, heure par heure (jour 1 → jour 7), mêmes fonds que la journée."""
    fig = go.Figure()
    n = 24 * nb_jours
    h = np.arange(n)
    profils = _profils(a, b, debut_a, debut_b, n)
    for (an, nom, c), p, d in zip(_deux(a, b, nom_a, nom_b), profils, (debut_a, debut_b)):
        fin = d + pd.Timedelta(days=nb_jours - 1)
        fig.add_trace(go.Scatter(x=h, y=p, mode="lines", name=f"{nom} · {jour_mois(d)} → {jour_mois(fin)} "
                                 f"(moyenne {nombre(p.mean())} °C)", line=dict(color=c, width=2.2),
                                 customdata=[jour_court(d + pd.Timedelta(hours=int(k))) + f", {int(k) % 24} h"
                                             for k in h],
                                 hovertemplate="%{customdata} : %{y:.1f} °C"))
    for k in range(1, nb_jours):
        fig.add_vline(x=24 * k - 0.5, line=dict(color=SEPARATEUR, width=1), layer="below")
    y_min, y_max = _echelle_bandes(profils, bas, haut)
    fig.add_annotation(x=n / 2, y=0.97, yref="paper", yanchor="top", showarrow=False,
                       font=dict(size=14, color="#9C5A12"), bgcolor="rgba(255,255,255,0.85)",
                       text=f"<b>{_ecart_texte(float((profils[1] - profils[0]).mean()))}</b>")
    styler(fig, "Semaine la plus chaude de chaque fichier, heure par heure",
           f"Chaque fichier avec sa propre semaine la plus chaude · fond orangé : au-dessus de {haut:g} °C · "
           f"fond bleu : en dessous de {bas:g} °C", HAUTEUR_SECONDAIRE, source=source, axe_dates=False)
    bandes_confort(fig, bas, haut, y_min, y_max)
    fig.update_xaxes(tickvals=[24 * k + 12 for k in range(nb_jours)],
                     ticktext=[f"jour {k + 1}" for k in range(nb_jours)], range=[-0.5, n - 0.5])
    fig.update_layout(hovermode="closest")
    return fig


def _plus_longue_suite(chaudes: pd.Series):
    """(début, fin, longueur) de la plus longue suite de nuits consécutives à True (None si aucune)."""
    meilleure, debut, n = (None, None, 0), None, 0
    for d, oui in chaudes.items():
        if oui:
            debut, n = (d if n == 0 else debut), n + 1
            if n > meilleure[2]:
                meilleure = (debut, d, n)
        else:
            n = 0
    return meilleure if meilleure[2] else None


def nuits_comparees(a, b, nom_a, nom_b, fenetre, seuil_tropical, seuil_tres_chaud, source):
    """
    Les nuits chaudes des deux fichiers, nuit par nuit sur l'été : une case par nuit (température minimale
    22h-6h), claire sous le seuil tropical, moyenne au-dessus, foncée au-dessus du seuil « très chaude ».
    La plus longue suite de nuits tropicales est encadrée de la couleur du fichier.
    """
    f0, f1 = pd.Timestamp(fenetre[0]).normalize(), pd.Timestamp(fenetre[1]).normalize()
    jours = pd.date_range(f0, f1, freq="D")
    fig = go.Figure()
    noms, z, textes, etiquettes = [], [], [], []
    for k, (an, nom, c) in enumerate(_deux(a, b, nom_a, nom_b)):
        n = an.nuits.copy()
        n.index = _superposable(n.index)
        n = n[~n.index.duplicated()].reindex(jours)
        categorie = np.where(n.isna(), np.nan, np.where(n >= seuil_tres_chaud, 2, np.where(n >= seuil_tropical, 1, 0)))
        noms.append(nom)
        z.append(categorie)
        textes.append([f"nuit du {jour_mois(d)} : {nombre(v)} °C au plus bas" if pd.notna(v) else
                       f"nuit du {jour_mois(d)} : pas de donnée" for d, v in n.items()])
        suite = _plus_longue_suite(n >= seuil_tropical)
        nb_20, nb_24 = int((n >= seuil_tropical).sum()), int((n >= seuil_tres_chaud).sum())
        etiquettes.append(f"<b style='color:{c}'>{nom}</b><br><span style='font-size:11px'>{nb_20} nuits ≥ "
                          f"{seuil_tropical:g} °C · {nb_24} ≥ {seuil_tres_chaud:g} °C en été</span>")
        if suite:
            debut, fin, longueur = suite
            fig.add_shape(type="rect", x0=debut - pd.Timedelta(hours=12), x1=fin + pd.Timedelta(hours=12),
                          y0=k - DEMI_HAUTEUR_CASE, y1=k + DEMI_HAUTEUR_CASE, xref="x", yref="y", line=dict(color=c, width=3),
                          fillcolor="rgba(0,0,0,0)")
            fig.add_annotation(x=debut + (fin - debut) / 2, y=k - DEMI_HAUTEUR_CASE, xref="x", yref="y", yanchor="bottom",
                               showarrow=False, font=dict(size=12, color=c),
                               text=f"<b>{longueur} nuit{'s' if longueur > 1 else ''} tropicale{'s' if longueur > 1 else ''}"
                                    f" de suite</b> · {jour_mois(debut)} → {jour_mois(fin)}")
    pas = 2 / 3
    echelle = [[0, COULEURS_NUITS[0]], [pas / 2, COULEURS_NUITS[0]], [pas / 2, COULEURS_NUITS[1]],
               [1 - pas / 4, COULEURS_NUITS[1]], [1 - pas / 4, COULEURS_NUITS[2]], [1, COULEURS_NUITS[2]]]
    fig.add_trace(go.Heatmap(x=jours, y=list(range(len(noms))), z=z, text=textes, zmin=0, zmax=2,
                             colorscale=echelle, showscale=False, xgap=1, ygap=ECART_LIGNES_NUITS,
                             hovertemplate="%{text}<extra></extra>"))
    # légende : trois carrés
    for nom_cat, c in zip((f"moins de {seuil_tropical:g} °C", f"tropicale (≥ {seuil_tropical:g} °C)",
                           f"très chaude (≥ {seuil_tres_chaud:g} °C)"), COULEURS_NUITS):
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=nom_cat,
                                 marker=dict(symbol="square", size=13, color=c, line=dict(color="#C9C6BF", width=1))))
    styler(fig, "Les nuits chaudes, nuit par nuit",
           "Une case par nuit (température minimale entre 22 h et 6 h) · cadre : plus longue suite de nuits tropicales",
           HAUTEUR_NUITS, titre_y="", source=source)
    fig.update_xaxes(type="date", range=[f0 - pd.Timedelta(hours=12), f1 + pd.Timedelta(hours=12)])
    fig.update_yaxes(tickvals=list(range(len(noms))), ticktext=etiquettes, autorange="reversed", showgrid=False,
                     tickformat=None, automargin=True, range=None)
    fig.update_layout(hovermode="closest")
    return fig


def cumul_dh(a, b, nom_a, nom_b, source):
    fig = go.Figure()
    for an, nom, c in _deux(a, b, nom_a, nom_b):
        j = an.jours
        x = _superposable(j.index)
        cumul = j["dh"].cumsum()
        fig.add_trace(go.Scatter(x=x, y=cumul, name=nom, line=dict(color=c, width=2.6), hovertemplate="%{y:.0f} °C.h"))
        if len(cumul):
            fig.add_annotation(x=x[-1], y=float(cumul.iloc[-1]), text=f"<b>{nombre(cumul.iloc[-1], 0)} °C.h</b>",
                               showarrow=False, xanchor="left", xshift=6, font=dict(color=c, size=12))
    for v, txt in ((350, "seuil bas RE2020 : 350"), (1250, "DH max courant : 1 250")):
        fig.add_hline(y=v, line=dict(color=GRIS_DOUX, width=1, dash="dot"), annotation_text=txt,
                      annotation_position="top left", annotation_font=dict(size=10, color=GRIS_DOUX))
    styler(fig, "Les DH qui s'accumulent au fil de l'année", "Repères RE2020 donnés à titre indicatif (DH d'un bâtiment)",
           HAUTEUR_SECONDAIRE, "°C.h", source=source)
    fig.update_xaxes(hoverformat="%-d %B")
    plus_haut = max([float(an.jours["dh"].sum()) for an in (a, b)] + [1250])
    fig.update_yaxes(range=[0, plus_haut * 1.22])   # place pour les noms des mois en haut
    debut = _superposable(a.jours.index[:1])[0] if len(a.jours) else pd.Timestamp(f"{ANNEE_SUPERPOSITION}-01-01")
    axe_mois(fig, debut, pd.Timestamp(f"{ANNEE_SUPERPOSITION}-12-31"))
    return fig


# ============================================================
# MÉTHODE & SOURCES
# ============================================================

def deux_temperatures_lissees(x, re2020, en16798, seuil):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=re2020, name="RE2020 (référence de calcul)", line=dict(color=TEAL, width=2.6),
                             hovertemplate="%{y:.1f} °C"))
    fig.add_trace(go.Scatter(x=x, y=en16798, name="Norme EN 16798 (pythermalcomfort)",
                             line=dict(color=BLEU_MENU, width=2, dash="dash"), hovertemplate="%{y:.1f} °C"))
    fig.add_hline(y=seuil, line=dict(color=CORAIL, width=1, dash="dot"), annotation_text=f"{seuil:g} °C",
                  annotation_position="right", annotation_font=dict(color=CORAIL))
    styler(fig, "Température extérieure lissée : deux façons de la calculer",
           f"Au-dessus de {seuil:g} °C, la méthode RE2020 compte les DH (période de confort adaptatif)",
           HAUTEUR_SECONDAIRE)
    fig.update_xaxes(hoverformat="%A %-d %B")
    tout = np.concatenate([np.asarray(re2020, float), np.asarray(en16798, float)])
    fig.update_yaxes(range=[float(np.floor(np.nanmin(tout) / 5) * 5) - 2, float(np.nanmax(tout)) + 6])   # place pour les mois
    axe_mois(fig, x[0], x[-1])
    return fig
