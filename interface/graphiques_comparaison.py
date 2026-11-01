"""
============================================================
 GRAPHIQUES DE L'ONGLET COMPARER — fichier de l'onglet Analyser
 (corail) face au second fichier (bleu canard)
============================================================
 Été superposé, nuits chaudes nuit par nuit, journée et semaine
 les plus chaudes superposées, cumul des DH.
 Outils de style et cache : graphiques_communs.py.
============================================================
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from calcul.analyse import plus_longue_suite, tranche
from calcul.format_fr import heure, jour_court, jour_mois, nombre
from config.charte import (CARAMEL, COULEUR_FICHIER_1, COULEUR_FICHIER_2, COULEURS_NUITS, GRIS, GRIS_DOUX,
                           HAUTEUR_COMPARAISON, HAUTEUR_NUITS, HAUTEUR_SECONDAIRE, SEPARATEUR, TEXTE_ECART)
from interface.couleurs import transparent
from interface.graphiques_communs import (MARGE_HAUT_DEGRES, annoter, axe_mois, bandes_confort, ecart_texte, en_cache,
                                          lignes_horizontales, styler)

# ============================================================
# PARAMÈTRES
# ============================================================
ANNEE_SUPERPOSITION = 2018            # années ramenées sur une même année pour superposer
DEGRES_BANDE_NUITS = 10               # °C libres sous les courbes de l'été superposé (étiquettes de nuit)
Y_ECART_ETE = 0.72                    # position (paper) de l'écart moyen écrit : haut gauche, sous les étiquettes Tmax
DEMI_HAUTEUR_CASE = 0.29              # nuits : demi-hauteur d'une rangée de cases (unités de l'axe Y)
ECART_LIGNES_NUITS = 46               # nuits : px entre les deux rangées (place pour l'étiquette « de suite »)


# ============================================================
# COMPARER — fichier de l'onglet Analyser (corail) / second fichier (bleu canard)
# ============================================================

def _superposable(index):
    """Ramène des dates sur une même année pour superposer deux fichiers."""
    return pd.DatetimeIndex([d.replace(year=ANNEE_SUPERPOSITION) for d in index])


def _deux(a, b, nom_a, nom_b):
    """(analyse, nom, couleur) des deux fichiers, dans l'ordre de l'onglet."""
    return ((a, nom_a, COULEUR_FICHIER_1), (b, nom_b, COULEUR_FICHIER_2))


@en_cache
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
                           showarrow=False, font=dict(size=14, color=TEXTE_ECART), align="left",
                           text=f"<b>{ecart_texte(ecart)}</b><br>{nom_b} par rapport à {nom_a}")
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
    return [tranche(an, d, nb_heures)[0] for an, d in ((a, debut_a), (b, debut_b))]


def _echelle_bandes(profils, bas, haut):
    """Échelle qui laisse voir les deux bandes même si les courbes ne les atteignent pas."""
    y_min = min(float(np.min(profils)) - 2, bas - 3)
    y_max = max(float(np.max(profils)) + 4, haut + 3)
    return np.floor(y_min), np.ceil(y_max)


@en_cache
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
                       font=dict(size=14, color=TEXTE_ECART), bgcolor="rgba(255,255,255,0.85)",
                       text=f"<b>{ecart_texte(float((profils[1] - profils[0]).mean()))}</b>")
    styler(fig, "Journée la plus chaude de chaque fichier, heure par heure",
           f"Fond orangé : au-dessus de {haut:g} °C · fond bleu : en dessous de {bas:g} °C", HAUTEUR_SECONDAIRE,
           source=source, axe_dates=False)
    bandes_confort(fig, bas, haut, y_min, y_max)
    fig.update_xaxes(tickvals=list(range(0, 24, 3)), ticktext=[f"{k} h" for k in range(0, 24, 3)],
                     range=[-0.5, 23.5])
    return fig


@en_cache
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
                       font=dict(size=14, color=TEXTE_ECART), bgcolor="rgba(255,255,255,0.85)",
                       text=f"<b>{ecart_texte(float((profils[1] - profils[0]).mean()))}</b>")
    styler(fig, "Semaine la plus chaude de chaque fichier, heure par heure",
           f"Chaque fichier avec sa propre semaine la plus chaude · fond orangé : au-dessus de {haut:g} °C · "
           f"fond bleu : en dessous de {bas:g} °C", HAUTEUR_SECONDAIRE, source=source, axe_dates=False)
    bandes_confort(fig, bas, haut, y_min, y_max)
    fig.update_xaxes(tickvals=[24 * k + 12 for k in range(nb_jours)],
                     ticktext=[f"jour {k + 1}" for k in range(nb_jours)], range=[-0.5, n - 0.5])
    fig.update_layout(hovermode="closest")
    return fig




@en_cache
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
        suite = plus_longue_suite(n >= seuil_tropical)
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


@en_cache
def cumul_dh(a, b, nom_a, nom_b, source, repere_bas, repere_haut):
    """DH cumulés jour après jour ; repères RE2020 (seuil bas, DH max courant) donnés à titre indicatif."""
    fig = go.Figure()
    for an, nom, c in _deux(a, b, nom_a, nom_b):
        j = an.jours
        x = _superposable(j.index)
        cumul = j["dh"].cumsum()
        fig.add_trace(go.Scatter(x=x, y=cumul, name=nom, line=dict(color=c, width=2.6), hovertemplate="%{y:.0f} °C.h"))
        if len(cumul):
            fig.add_annotation(x=x[-1], y=float(cumul.iloc[-1]), text=f"<b>{nombre(cumul.iloc[-1], 0)} °C.h</b>",
                               showarrow=False, xanchor="left", xshift=6, font=dict(color=c, size=12))
    for v, txt in ((repere_bas, f"seuil bas RE2020 : {nombre(repere_bas, 0)}"),
                   (repere_haut, f"DH max courant : {nombre(repere_haut, 0)}")):
        fig.add_hline(y=v, line=dict(color=GRIS_DOUX, width=1, dash="dot"), annotation_text=txt,
                      annotation_position="top left", annotation_font=dict(size=10, color=GRIS_DOUX))
    styler(fig, "Les DH qui s'accumulent au fil de l'année", "Repères RE2020 donnés à titre indicatif (DH d'un bâtiment)",
           HAUTEUR_SECONDAIRE, "°C.h", source=source)
    fig.update_xaxes(hoverformat="%-d %B")
    plus_haut = max([float(an.jours["dh"].sum()) for an in (a, b)] + [repere_haut])
    fig.update_yaxes(range=[0, plus_haut * 1.22])   # place pour les noms des mois en haut
    debut = _superposable(a.jours.index[:1])[0] if len(a.jours) else pd.Timestamp(f"{ANNEE_SUPERPOSITION}-01-01")
    axe_mois(fig, debut, pd.Timestamp(f"{ANNEE_SUPERPOSITION}-12-31"))
    return fig

