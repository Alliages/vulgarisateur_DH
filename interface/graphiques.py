"""
============================================================
 GRAPHIQUES — Plotly, charte « Météo et Chaleur »
============================================================
 Inspiré du graphique de référence (docs/references/) :
   - titre en gras + sous-titre gris qui dit comment lire ;
   - légendes avec des noms parlants ;
   - annotations directes des extrêmes (point + étiquette) ;
   - aire colorée entre deux courbes + écart moyen écrit ;
   - noms des mois en gras sous l'axe, séparateurs discrets ;
   - source en pied de graphique ;
   - axes noirs, épais, terminés par des flèches ; zoom partout.
============================================================
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config.reglages import BLEU_MENU, CARAMEL, CORAIL, GRIS, GRIS_DOUX, INDIGO, TEAL
from interface.format_fr import MOIS, heure, jour_court, jour_mois, nombre

# ============================================================
# PARAMÈTRES
# ============================================================
EPAISSEUR_AXE = 2
TAILLE_FLECHE = 1.4
POLICE = "Inter, Segoe UI, sans-serif"
JAUNE_FONCE = "#B8860B"               # axe et texte des DH
GRIS_INOCCUPE = "rgba(39,41,50,0.08)" # heures d'absence (scénario d'occupation)
HAUTEUR_PRINCIPAL = 520
HAUTEUR_SECONDAIRE = 400
HAUTEUR_COMPARAISON = 560
MARGE_COTES = 60                      # px à gauche et à droite
MARGE_BAS = 20                        # px sous l'axe (Plotly agrandit selon graduations, curseur, source)
PX_LIGNE_TITRE = 21                   # hauteur d'une ligne de titre / sous-titre
PX_LEGENDE = 34                       # hauteur réservée à la légende (une ligne)
MARGE_HAUT_DEGRES = 9                 # °C libres au-dessus du maximum (noms des mois + étiquettes)
FORMAT_DATE = "%d/%m"                 # dates numériques (évite les mois en anglais de Plotly)
ANNEE_SUPERPOSITION = 2018            # années ramenées sur une même année pour superposer


# ============================================================
# OUTILS DE STYLE
# ============================================================

def transparent(hexa, alpha):
    h = hexa.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


def pas_rond(etendue, nb=4):
    """Pas de graduation « rond » (1, 2, 5, 10, 20…) pour environ nb intervalles."""
    brut = max(etendue / nb, 1e-9)
    puissance = 10 ** np.floor(np.log10(brut))
    return max(1.0, float(next(k * puissance for k in (1, 2, 2.5, 5, 10) if k * puissance >= brut)))


def _fleches(fig):
    """Flèches au bout des axes x (à droite) et y (en haut)."""
    for x, y, ax, ay in ((1, 0, -14, 0), (0, 1, 0, 14)):
        fig.add_annotation(x=x, y=y, xref="paper", yref="paper", ax=ax, ay=ay, text="", showarrow=True,
                           arrowhead=2, arrowsize=TAILLE_FLECHE, arrowwidth=EPAISSEUR_AXE, arrowcolor="black")


def styler(fig, titre, sous_titre="", hauteur=HAUTEUR_SECONDAIRE, titre_y="°C", double_axe=False, source="",
           legende=True):
    """
    Titre gras + sous-titre gris, légende au-dessus du tracé, source en pied, axes noirs fléchés.
    La marge du haut est calculée d'après le nombre de lignes du titre, pour que rien ne se chevauche.
    """
    texte = f"<b>{titre}</b>" + (f"<br><span style='font-size:12px;color:{GRIS_DOUX}'>{sous_titre}</span>"
                                 if sous_titre else "")
    nb_lignes = titre.count("<br>") + 1 + (sous_titre.count("<br>") + 1 if sous_titre else 0)
    haut = 18 + PX_LIGNE_TITRE * nb_lignes + (PX_LEGENDE if legende else 8)
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
                     showgrid=False, zeroline=False, tickformat=FORMAT_DATE, hoverformat="%d/%m %Hh", automargin=True)
    fig.update_yaxes(showline=True, linecolor="black", linewidth=EPAISSEUR_AXE, ticks="outside", tickcolor="black",
                     gridcolor="#ECEAE6", zeroline=False, tickformat=".0f", title_text=titre_y,
                     **({"secondary_y": False} if double_axe else {}))
    if source:
        # la source sert de titre à l'axe des dates : Plotly la place toujours sous les graduations
        # et sous le curseur de zoom, sans chevauchement (marge du bas ajustée automatiquement)
        fig.update_xaxes(title=dict(text=f"Source : {source}", font=dict(size=10, color=GRIS_DOUX), standoff=12))
    _fleches(fig)
    return fig


def lignes_horizontales(fig, lignes):
    for v in lignes:
        fig.add_hline(y=v, line=dict(color=INDIGO, width=1.4, dash="dash"), annotation_text=f"{v:g} °C",
                      annotation_position="right", annotation_font=dict(color=INDIGO, size=11))


def axe_mois(fig, debut, fin):
    """Noms des mois en gras en haut du tracé (au milieu de chaque mois) + séparateurs discrets entre mois.
    En haut plutôt que sous l'axe : ils ne chevauchent ni les dates ni le curseur de zoom."""
    debut, fin = pd.Timestamp(debut), pd.Timestamp(fin)
    for m in pd.date_range(debut.replace(day=1), fin, freq="MS"):
        milieu = m + pd.Timedelta(days=15)
        fig.add_annotation(x=milieu, y=1, xref="x", yref="paper", yanchor="top", showarrow=False,
                           text=f"<b>{MOIS[m.month - 1].capitalize()}</b>", font=dict(size=13, color=GRIS))
        fig.add_vline(x=m, line=dict(color="#E2E0DB", width=1), layer="below")


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


# ============================================================
# ANALYSER — série de l'année
# ============================================================

def serie_annuelle(analyse, lignes, fenetre, source):
    """Moyenne journalière + bande min-max (rouge clair) + horaire fin, extrêmes annotés, zoom."""
    s, jours = analyse.serie, analyse.jours
    midi = jours.index + pd.Timedelta(hours=12)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=midi, y=jours["tmax"], line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=midi, y=jours["tmin"], fill="tonexty", fillcolor=transparent(CORAIL, 0.18),
                             line=dict(width=0), name="Variation du jour (min → max)", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=s.horodatage, y=s.t, mode="lines", name="Heure par heure",
                             line=dict(color=CORAIL, width=0.7), opacity=0.35, hovertemplate="%{y:.1f} °C"))
    fig.add_trace(go.Scatter(x=midi, y=jours["tmoy"], mode="lines", name="Moyenne de la journée",
                             line=dict(color=CORAIL, width=2.4), hovertemplate="moyenne %{y:.1f} °C"))
    fig.add_trace(go.Scatter(x=s.horodatage, y=analyse.seuil, mode="lines", name="Seuil DH", visible="legendonly",
                             line=dict(color=GRIS, width=1, shape="hv"), hovertemplate="seuil %{y:.0f} °C"))
    # Extrêmes : température maximale et nuit la plus chaude (minimum nocturne le plus élevé)
    i_max = int(np.argmax(s.t))
    t_max = s.horodatage[i_max]
    annoter(fig, t_max, s.t[i_max], f"<b>Tmax : {nombre(s.t[i_max])} °C</b><br>{jour_mois(t_max)} à {heure(t_max)}",
            CORAIL, ax=95, ay=-22)
    if not analyse.nuits_detail.empty:
        n = analyse.nuits_detail.loc[analyse.nuits_detail["tmin"].idxmax()]
        annoter(fig, n["quand"], n["tmin"],
                f"<b>Nuit la plus chaude : {nombre(n['tmin'])} °C au plus bas</b><br>"
                f"nuit du {jour_mois(n.name)} ({heure(n['quand'])})", INDIGO, ax=70, ay=45)
    styler(fig, f"Température extérieure · {s.libelle}",
           "Courbe : moyenne de chaque journée · rouge clair : écart entre le minimum et le maximum du jour · "
           "trait fin : heure par heure. Molette ou curseur pour zoomer.", HAUTEUR_PRINCIPAL, source=source)
    lignes_horizontales(fig, lignes)
    axe_mois(fig, s.horodatage[0], s.horodatage[-1])
    fig.update_yaxes(range=[float(np.floor(np.min(s.t) / 5) * 5), float(np.max(s.t)) + MARGE_HAUT_DEGRES])
    fig.update_xaxes(rangeslider=dict(visible=True, thickness=0.07, bgcolor="#EEF8FF"),
                     range=list(fenetre) if fenetre else None)
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
    haut_dh = max(float(np.max(dh)) * 3, 1)   # barres DH dans le tiers bas du graphique
    _zones_inoccupees(fig, x, occupe)   # après les courbes : sa trace vide ne doit pas fixer le type de l'axe
    styler(fig, titre, sous_titre, double_axe=True, source=source, legende=legende)
    fig.update_xaxes(type="date")
    fig.update_yaxes(title_text="DH (°C.h)", secondary_y=True, showgrid=False, showline=True,
                     linecolor=JAUNE_FONCE, linewidth=EPAISSEUR_AXE, tickcolor=JAUNE_FONCE, ticks="outside",
                     tickfont=dict(color=JAUNE_FONCE), title_font=dict(color=JAUNE_FONCE),
                     range=[0, haut_dh], dtick=pas_rond(haut_dh), tick0=0, tickformat=".0f")
    if echelle == "semaine":
        midis = [d + pd.Timedelta(hours=12) for d in pd.date_range(x[0].normalize(), x[-1].normalize(), freq="D")]
        fig.update_xaxes(tickvals=midis, ticktext=[jour_court(d) for d in midis])
        for d in pd.date_range(x[0].normalize() + pd.Timedelta(days=1), x[-1].normalize(), freq="D"):
            fig.add_vline(x=d, line=dict(color="#E2E0DB", width=1), layer="below")
    else:
        heures = [x[0].normalize() + pd.Timedelta(hours=h) for h in range(0, 24, 3)]
        fig.update_xaxes(tickvals=heures, ticktext=[heure(h) for h in heures])
        i_max, i_min = int(np.argmax(t)), int(np.argmin(t))
        annoter(fig, x[i_max], t[i_max], f"<b>{nombre(t[i_max])} °C</b>", CORAIL, ax=0, ay=-28, secondary_y=False)
        annoter(fig, x[i_min], t[i_min], f"{nombre(t[i_min])} °C", GRIS_DOUX, ax=0, ay=28, secondary_y=False)
    fig.update_layout(bargap=0.1)
    return fig


# ============================================================
# COMPARER
# ============================================================

def _superposable(index):
    """Ramène des dates sur une même année pour superposer deux fichiers."""
    return pd.DatetimeIndex([d.replace(year=ANNEE_SUPERPOSITION) for d in index])


def ete_superpose(a, b, nom_a, nom_b, lignes, fenetre, source):
    """Moyennes journalières des deux fichiers + aire de l'écart + maximums annotés."""
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
                                 fillcolor=transparent(CARAMEL, 0.35), name="Écart entre les deux fichiers", legendrank=1001,
                                 hoverinfo="skip"))
    for jours, nom, c in ((ja, nom_a, TEAL), (jb, nom_b, INDIGO)):
        fig.add_trace(go.Scatter(x=jours.index + pd.Timedelta(hours=12), y=jours["tmoy"], name=nom,
                                 line=dict(color=c, width=2.6), hovertemplate="%{y:.1f} °C"))
    # Écart moyen sur la fenêtre d'été
    f0, f1 = pd.Timestamp(fenetre[0]), pd.Timestamp(fenetre[1])
    ete = commun[(commun >= f0) & (commun <= f1)]
    if len(ete):
        ecart = float((jb.loc[ete, "tmoy"] - ja.loc[ete, "tmoy"]).mean())
        x_txt = ete[len(ete) // 2] + pd.Timedelta(hours=12)
        fig.add_annotation(x=x_txt, y=0.03, yref="paper", yanchor="bottom",   # en bas : loin des courbes
                           showarrow=False, font=dict(size=14, color="#9C5A12"), bgcolor="rgba(255,255,255,0.85)",
                           text=f"<b>{'+' if ecart >= 0 else ''}{nombre(ecart)} °C en moyenne</b><br>"
                                f"{nom_b} par rapport à {nom_a}")
    # Maximums horaires de chaque fichier : l'étiquette du plus tôt part à gauche, celle du plus tard à droite
    maxima = []
    for an, nom, c in ((a, nom_a, TEAL), (b, nom_b, INDIGO)):
        i = int(np.argmax(an.serie.t))
        maxima.append((_superposable(an.serie.horodatage[i:i + 1])[0], an.serie.t[i], an.serie.horodatage[i], nom, c))
    maxima.sort(key=lambda m: m[0])
    for (x, t, quand, nom, c), ax, ay in zip(maxima, (-130, 130), (-14, -26)):
        annoter(fig, x, t, f"<b>Tmax {nom} : {nombre(t)} °C</b><br>{jour_mois(quand)} à {heure(quand)}", c, ax=ax, ay=ay)
    # bas : place pour l'écart moyen écrit en bas ; haut : place pour les mois et les étiquettes Tmax
    if len(ete):
        bas_y = float(min(ja.loc[ete, "tmoy"].min(), jb.loc[ete, "tmoy"].min()))
        fig.update_yaxes(range=[np.floor(bas_y / 5) * 5 - 8, max(a.serie.t.max(), b.serie.t.max()) + MARGE_HAUT_DEGRES])
    styler(fig, "L'été superposé : température moyenne de chaque journée",
           "Aire orange : écart entre les deux fichiers · points : température maximale de chaque fichier (heure par heure)",
           HAUTEUR_COMPARAISON, source=source)
    lignes_horizontales(fig, lignes)
    axe_mois(fig, f0, f1)
    fig.update_xaxes(range=[f0, f1], rangeslider=dict(visible=True, thickness=0.07))
    return fig


def journees_superposees(a, b, nom_a, nom_b, jour_a, jour_b, source):
    """Journée la plus chaude de chaque fichier, heure par heure, aire de l'écart (bas de l'image de référence)."""
    fig = go.Figure()
    h = np.arange(24)
    profils = []
    for an, d in ((a, jour_a), (b, jour_b)):
        s = an.serie
        i0 = s.horodatage.get_indexer([d])[0]
        profils.append(s.t[i0:i0 + 24])
    fig.add_trace(go.Scatter(x=h, y=np.maximum(*profils), line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=h, y=np.minimum(*profils), fill="tonexty", line=dict(width=0),
                             fillcolor=transparent(CARAMEL, 0.35), name="Écart", hoverinfo="skip", legendrank=1001))
    for p, nom, d, c in ((profils[0], nom_a, jour_a, TEAL), (profils[1], nom_b, jour_b, INDIGO)):
        fig.add_trace(go.Scatter(x=h, y=p, mode="lines+markers", marker=dict(size=6),
                                 name=f"{nom} · {jour_mois(d)} (moyenne {nombre(p.mean())} °C)",
                                 line=dict(color=c, width=2.4), hovertemplate="%{y:.1f} °C"))
        i = int(np.argmax(p))
        fig.add_annotation(x=i, y=p[i], text=f"<b>{nombre(p[i])} °C</b>", showarrow=False, yshift=14,
                           font=dict(color=c, size=12))
    ecart = float((profils[1] - profils[0]).mean())
    fig.add_annotation(x=11.5, y=float(np.max(profils)) - 1, showarrow=False, font=dict(size=14, color="#9C5A12"),
                       text=f"<b>{'+' if ecart >= 0 else ''}{nombre(ecart)} °C en moyenne</b>")
    styler(fig, "Journée la plus chaude de chaque fichier, heure par heure", "", HAUTEUR_SECONDAIRE, source=source)
    fig.update_xaxes(tickvals=list(range(0, 24, 3)), ticktext=[f"{k} h" for k in range(0, 24, 3)], tickformat=None,
                     hoverformat=None)
    return fig


def cumul_dh(a, b, nom_a, nom_b, source):
    fig = go.Figure()
    for an, nom, c in ((a, nom_a, TEAL), (b, nom_b, INDIGO)):
        j = an.jours
        x = _superposable(j.index)
        cumul = j["dh"].cumsum()
        fig.add_trace(go.Scatter(x=x, y=cumul, name=nom, line=dict(color=c, width=2.6), hovertemplate="%{y:.0f} °C.h"))
        if len(cumul):
            fig.add_annotation(x=x[-1], y=float(cumul.iloc[-1]), text=f"<b>{cumul.iloc[-1]:.0f} °C.h</b>",
                               showarrow=False, xanchor="left", xshift=6, font=dict(color=c, size=12))
    for v, txt in ((350, "seuil bas RE2020 : 350"), (1250, "DH max courant : 1 250")):
        fig.add_hline(y=v, line=dict(color=GRIS_DOUX, width=1, dash="dot"), annotation_text=txt,
                      annotation_position="top left", annotation_font=dict(size=10, color=GRIS_DOUX))
    styler(fig, "Les DH qui s'accumulent au fil de l'année", "Repères RE2020 donnés à titre indicatif (DH d'un bâtiment)",
           HAUTEUR_SECONDAIRE, "°C.h", source=source)
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
    tout = np.concatenate([np.asarray(re2020, float), np.asarray(en16798, float)])
    fig.update_yaxes(range=[float(np.floor(np.nanmin(tout) / 5) * 5) - 2, float(np.nanmax(tout)) + 6])   # place pour les mois
    axe_mois(fig, x[0], x[-1])
    return fig
