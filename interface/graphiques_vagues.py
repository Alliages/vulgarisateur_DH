"""
============================================================
 GRAPHIQUE DES VAGUES DE CHALEUR (0.9.14) — onglets Analyser et Comparer
============================================================
 Température moyenne du jour Tm = (Tmin + Tmax) / 2, seuils de la
 station (Spic, Sdeb, Sint), vagues sur fond teinté. L'aire entre
 Tm et Sdeb représente la sévérité (°C.j).
 Comparer : les deux fichiers sur un seul graphique, chacun dans sa
 couleur. Seuils en gris s'ils sont communs (même station), sinon
 dans la couleur de chaque fichier.
 Calcul : calcul/vagues_chaleur.py. Style et cache : graphiques_communs.py.
============================================================
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from calcul.format_fr import jour_mois, nombre
from calcul.vagues_chaleur import seuils_du_fichier, tm_journaliere, vagues_du_fichier
from config.charte import COULEUR_FICHIER_1, COULEUR_FICHIER_2, GRIS, GRIS_DOUX
from interface.couleurs import transparent
from interface.graphiques_communs import axe_mois, en_cache, styler

# ============================================================
# PARAMÈTRES
# ============================================================
TEXTE_SANS_SEUILS = ("pas de seuils pour la station de ce fichier "
                     "(fichiers RE2020, TRACC et observations des stations de référence uniquement)")
LECTURE = ("Courbe : moyenne du jour (Tmin + Tmax) / 2 · aire colorée : sévérité, au-dessus de Sdeb · "
           "Spic : pic, Sdeb : début, Sint : interruption")
HAUTEUR_VAGUES, HAUTEUR_VAGUES_COMPAREES = 400, 520
MARGE_DROITE_SEUILS = 96              # px : étiquettes « Spic 26,4 °C » à droite du tracé
PX_MIN_ETIQUETTES = 14                # px entre deux étiquettes de seuil
PX_SOUS_TRACE = 50                    # px sous le tracé (dates), pour estimer le px par °C
MARGE_JOURS = 5                       # jours affichés avant et après une vague hors de la fenêtre
PART_COURBE = 0.68                    # part basse du tracé pour les courbes (au-dessus : mois et étiquettes)
Y_ETIQUETTE, PAS_ETIQUETTE = 0.92, 0.07   # étiquettes des vagues (repère « paper »)
JOURS_ENTRE_ETIQUETTES = 16           # écart mini entre deux étiquettes d'une même rangée
NB_RANGEES = 3                        # rangées d'étiquettes
SEUILS = (("spic", "Spic", "solid"), ("sdeb", "Sdeb", "dash"), ("sint", "Sint", "dot"))


@dataclass
class Trace:
    """Un fichier sur le graphique."""
    nom: str
    couleur: str
    tm: pd.Series
    vagues: list
    seuils: dict


# ============================================================
# DONNÉES
# ============================================================

def _sur_annee(d: pd.Timestamp, annee) -> pd.Timestamp:
    """Date ramenée sur une année commune (Comparer) ; inchangée si annee est None."""
    return d if annee is None else d.replace(year=annee)


def _tm(a, annee):
    """Tm du fichier, éventuellement ramenée sur une année commune (29 février retiré)."""
    tm = tm_journaliere(a.jours)
    if annee is None:
        return tm
    tm = tm[~((tm.index.month == 2) & (tm.index.day == 29))]
    return pd.Series(tm.to_numpy(), index=pd.DatetimeIndex([_sur_annee(d, annee) for d in tm.index]))


def sans_seuils(a) -> bool:
    """Vrai si la station du fichier n'a pas de seuils."""
    return seuils_du_fichier(a.serie.meta) is None


def echelle(analyses, hyp, fenetre, annee=None):
    """
    (fenêtre, bornes de température) communes aux fichiers qui ont des seuils. La fenêtre part de celle
    reçue (l'été) et s'élargit pour montrer toutes les vagues ; bornes None si aucun fichier n'a de seuils.
    """
    donnees = [(a, *vagues_du_fichier(a, hyp)) for a in analyses]
    donnees = [(a, v, s) for a, v, s in donnees if v is not None]
    if not donnees:
        return fenetre, None
    series = [_tm(a, annee).dropna() for a, _, _ in donnees]
    debut = pd.Timestamp(fenetre[0]) if fenetre else min(t.index[0] for t in series)
    fin = pd.Timestamp(fenetre[1]) if fenetre else max(t.index[-1] for t in series)
    marge = pd.Timedelta(days=MARGE_JOURS)
    for _, vagues, _ in donnees:
        for vg in vagues:
            debut = min(debut, _sur_annee(vg.debut, annee) - marge)
            fin = max(fin, _sur_annee(vg.fin, annee) + marge)
    visibles = [t[(t.index >= debut) & (t.index <= fin)] for t in series]
    bas = min([float(t.min()) for t in visibles if len(t)] + [s["sint"] for _, _, s in donnees])
    haut = max([float(t.max()) for t in visibles if len(t)] + [s["spic"] for _, _, s in donnees])
    y_min = float(np.floor(bas / 5) * 5)
    return (debut, fin), (y_min, y_min + (haut - y_min) / PART_COURBE)


# ============================================================
# GRAPHIQUE
# ============================================================

def _rangees(centres) -> list:
    """Rangée de chaque étiquette de vague (dates croissantes) : la première assez loin de sa voisine."""
    dernieres, rangees = [None] * NB_RANGEES, []
    for i, c in enumerate(centres):
        libres = [r for r, d in enumerate(dernieres) if d is None or (c - d).days >= JOURS_ENTRE_ETIQUETTES]
        rangee = libres[0] if libres else i % NB_RANGEES
        dernieres[rangee] = c
        rangees.append(rangee)
    return rangees


def _decalages(valeurs, px_par_degre) -> list:
    """Décalage vertical (px) des étiquettes de seuil, du plus haut au plus bas, pour qu'elles ne se chevauchent pas."""
    decalages, position = [], None
    for v in valeurs:
        px = v * px_par_degre
        decale = px if position is None else min(px, position - PX_MIN_ETIQUETTES)
        decalages.append(decale - px)
        position = decale
    return decalages


def _bilan(t: Trace) -> str:
    if not t.vagues:
        return f"aucune vague · seuils de la station {t.seuils['station']}"
    n, jours = len(t.vagues), sum(vg.duree for vg in t.vagues)
    severite = nombre(sum(vg.severite for vg in t.vagues), 0)
    return f"{n} vague{'s' if n > 1 else ''} · {jours} jours · sévérité {severite} °C.j · seuils de la station {t.seuils['station']}"


def _lignes_seuils(traces) -> list:
    """[(valeur, texte, trait, couleur)] du seuil le plus haut au plus bas : une seule série si les seuils sont communs."""
    communs = len({tuple(t.seuils[c] for c, _, _ in SEUILS) for t in traces}) == 1
    lignes = [(t.seuils[c], texte, trait, GRIS_DOUX if communs else t.couleur)
              for t in (traces[:1] if communs else traces) for c, texte, trait in SEUILS]
    return sorted(lignes, key=lambda l: -l[0])


def _figure(traces, titre, sous_titre, hauteur, fenetre, bornes, annee):
    """Graphique d'un ou deux fichiers ; légende et bord coloré des étiquettes à partir de deux."""
    plusieurs = len(traces) > 1
    midi = pd.Timedelta(hours=12)
    fig = go.Figure()
    etiquettes = []
    survols = []
    # 1. Vagues : fond sur toute leur durée, aire de la sévérité entre Sdeb et Tm
    for t in traces:
        sdeb = t.seuils["sdeb"]
        survol = pd.Series("", index=t.tm.index, dtype=object)
        for vg in t.vagues:
            debut, fin = _sur_annee(vg.debut, annee), _sur_annee(vg.fin, annee)
            fig.add_vrect(x0=debut, x1=fin + pd.Timedelta(days=1), fillcolor=transparent(t.couleur, 0.09), line_width=0,
                          layer="below")
            jours = t.tm[(t.tm.index >= debut) & (t.tm.index <= fin)]
            x = jours.index + midi
            fig.add_trace(go.Scatter(x=x, y=[sdeb] * len(x), mode="lines", line=dict(width=0), showlegend=False,
                                     hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=x, y=np.maximum(jours, sdeb), mode="lines", fill="tonexty",
                                     fillcolor=transparent(t.couleur, 0.45), line=dict(width=0), showlegend=False,
                                     hoverinfo="skip"))
            survol[jours.index] = (f"<br>vague du {jour_mois(debut)} au {jour_mois(fin)} : {vg.duree} jours, "
                                   f"sévérité {nombre(vg.severite, 0)} °C.j")
            etiquettes.append((debut + (fin - debut) / 2 + midi, vg, t.couleur))
        survols.append(survol)
    # 2. Température moyenne du jour
    for t, survol in zip(traces, survols):
        prefixe = f"{t.nom} : " if plusieurs else ""
        fig.add_trace(go.Scatter(x=t.tm.index + midi, y=t.tm, mode="lines", name=t.nom, showlegend=plusieurs,
                                 line=dict(color=t.couleur, width=2), customdata=survol,
                                 hovertemplate=prefixe + "%{y:.1f} °C%{customdata}<extra></extra>"))
    styler(fig, titre, sous_titre, hauteur, legende=plusieurs)
    fig.update_xaxes(type="date", range=list(fenetre), hoverformat="%-d %B")
    fig.update_yaxes(range=list(bornes))
    fig.update_layout(margin=dict(r=MARGE_DROITE_SEUILS))
    # 3. Seuils, étiquetés à droite
    lignes = _lignes_seuils(traces)
    px_par_degre = (hauteur - fig.layout.margin.t - PX_SOUS_TRACE) / (bornes[1] - bornes[0])
    for (v, texte, trait, couleur), decalage in zip(lignes, _decalages([l[0] for l in lignes], px_par_degre)):
        fig.add_hline(y=v, line=dict(color=couleur, width=1.2, dash=trait))
        fig.add_annotation(x=1, xref="paper", xanchor="left", xshift=8, y=v, yshift=decalage, showarrow=False,
                           text=f"{texte} {nombre(v)} °C", font=dict(size=11, color=couleur))
    # 4. Une étiquette par vague (durée, sévérité)
    etiquettes.sort(key=lambda e: e[0])
    for (centre, vg, couleur), rangee in zip(etiquettes, _rangees([e[0] for e in etiquettes])):
        fig.add_annotation(x=centre, y=Y_ETIQUETTE - rangee * PAS_ETIQUETTE, yref="paper", yanchor="top",
                           showarrow=False, text=f"<b>{vg.duree} j</b> · {nombre(vg.severite, 0)} °C.j",
                           font=dict(size=11, color=GRIS), bgcolor="rgba(255,255,255,0.8)",
                           bordercolor=couleur if plusieurs else None, borderwidth=1 if plusieurs else 0, borderpad=3)
    axe_mois(fig, *fenetre)
    return fig


def _trace(a, hyp, nom, couleur, annee):
    """Trace d'un fichier, ou None si sa station n'a pas de seuils."""
    vagues, s = vagues_du_fichier(a, hyp)
    return None if vagues is None else Trace(nom, couleur, _tm(a, annee), vagues, s)


@en_cache
def vagues_chaleur(a, hyp, nom, couleur, fenetre, bornes):
    """Analyser : Tm du fichier, seuils de sa station et vagues ; None si la station n'a pas de seuils."""
    t = _trace(a, hyp, nom, couleur, None)
    if t is None:
        return None
    return _figure([t], f"Vagues de chaleur · {nom}", f"{_bilan(t)}<br>{LECTURE}", HAUTEUR_VAGUES, fenetre, bornes, None)


@en_cache
def vagues_comparees(a, b, hyp, nom_a, nom_b, fenetre, bornes, annee):
    """Comparer : les deux fichiers sur un graphique (seul celui qui a des seuils si l'autre n'en a pas) ; None sinon."""
    traces = [t for t in (_trace(a, hyp, nom_a, COULEUR_FICHIER_1, annee), _trace(b, hyp, nom_b, COULEUR_FICHIER_2, annee))
              if t is not None]
    if not traces:
        return None
    titre = "Vagues de chaleur · " + " et ".join(t.nom for t in traces)
    bilans = "<br>".join((f"{t.nom} : " if len(traces) > 1 else "") + _bilan(t) for t in traces)
    return _figure(traces, titre, f"{bilans}<br>{LECTURE}", HAUTEUR_VAGUES_COMPAREES, fenetre, bornes, annee)
