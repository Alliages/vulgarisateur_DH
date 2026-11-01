"""
============================================================
 CARTES D'INDICATEURS — icône, valeur, mini-graphique, bulle « i »
============================================================
 Une carte par indicateur, dans l'ordre reçu. La teinte, l'icône
 et la carte « principale » (couleur pleine) sont choisies dans le
 fichier de chaque indicateur (calcul/indicateurs/<id>.py).
 La documentation reste DISCRÈTE : pastille « i » (bulle au
 survol) et statut des hypothèses citées (« provisoire »…).
============================================================
"""

import html

import numpy as np
import streamlit as st

from calcul.format_fr import MOIS_COURTS, nombre
from calcul.hypotheses import MOTIF_REPERE, remplacer_reperes
from calcul.indicateurs import REGISTRE
from config.charte import COULEURS_STATUT, COULEURS_TEINTES, GRIS_DOUX, PART_TEINTE_FOND, PART_TEINTE_ICONE, TEAL
from interface.couleurs import melange

# ============================================================
# PARAMÈTRES
# ============================================================
# --- Mini-graphique des cartes (px) ---
LARGEUR_MINI, HAUTEUR_MINI, HAUTEUR_LIBELLES = 104, 34, 11
NB_MOIS_LIBELLES = 5                    # au-delà, pas de nom de mois sous les barres
EPAISSEUR_JAUGE = 9                     # épaisseur de l'arc de la jauge (px)

# --- Icônes (tracés simples, style « feather », 24 × 24) : noms autorisés dans calcul/indicateurs/base.py ---
ICONES = {
    "soleil": '<circle cx="12" cy="12" r="4.5"/><path d="M12 1.5v2.5M12 20v2.5M4.6 4.6l1.8 1.8M17.6 17.6l1.8 1.8'
              'M1.5 12H4M20 12h2.5M4.6 19.4l1.8-1.8M17.6 6.4l1.8-1.8"/>',
    "lune": '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
    "horloge": '<circle cx="12" cy="12" r="9.5"/><path d="M12 6.5V12l3.5 2"/>',
    "calendrier": '<rect x="3" y="4.5" width="18" height="17" rx="2.5"/><path d="M16 2.5v4M8 2.5v4M3 10h18"/>',
    "thermometre": '<path d="M14 14.8V4.5a2 2 0 0 0-4 0v10.3a4.5 4.5 0 1 0 4 0z"/>',
}


# ============================================================
# DESSINS
# ============================================================

def _icone(nom: str, taille: int = 18, epaisseur: float = 2) -> str:
    return (f'<svg width="{taille}" height="{taille}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="{epaisseur}" stroke-linecap="round" stroke-linejoin="round">{ICONES[nom]}</svg>')


def mini_graphique(profil, couleur, unite, decimales, fond_clair) -> str:
    """Petit graphique SVG de la carte : barres ou ligne par mois, ou bande des nuits (une case par nuit)."""
    if profil is None:
        return ""
    v = profil["valeurs"]
    larg, haut, h_lib = LARGEUR_MINI, HAUTEUR_MINI, HAUTEUR_LIBELLES
    attenue = melange(couleur, 0.25) if fond_clair else "rgba(255,255,255,.35)"
    if profil["type"] == "jauge":
        return _jauge(float(v), couleur, attenue, larg, haut + h_lib)
    if profil["type"] == "bande":
        if len(v) < 2:
            return ""
        pas = larg / len(v)
        cases = "".join(f'<rect x="{i * pas:.2f}" y="{haut - 16}" width="{max(pas - 0.4, 0.6):.2f}" height="16" '
                        f'fill="{couleur if chaud else attenue}"><title>nuit du {d.day} {MOIS_COURTS[d.month - 1]}'
                        f'{" : tropicale" if chaud else ""}</title></rect>' for i, (d, chaud) in enumerate(v.items()))
        lib = (f'<text x="0" y="{haut + h_lib - 1}" font-size="8.5" fill="currentColor" opacity=".7">'
               f'{MOIS_COURTS[v.index[0].month - 1]}</text><text x="{larg}" y="{haut + h_lib - 1}" font-size="8.5" '
               f'text-anchor="end" fill="currentColor" opacity=".7">{MOIS_COURTS[v.index[-1].month - 1]}</text>')
        return f'<svg class="mini" width="{larg}" height="{haut + h_lib}">{cases}{lib}</svg>'
    if len(v) < 2:
        return ""
    mois, valeurs = list(v.index), [float(x) for x in v.values]
    n, vmax = len(valeurs), max(max(valeurs), 1e-9)
    pas = larg / n
    libelles = "" if n > NB_MOIS_LIBELLES else "".join(
        f'<text x="{(i + 0.5) * pas:.1f}" y="{haut + h_lib - 1}" font-size="8.5" text-anchor="middle" '
        f'fill="currentColor" opacity=".7">{MOIS_COURTS[m - 1]}</text>' for i, m in enumerate(mois))
    if profil["type"] == "barres":
        barres = "".join(
            f'<rect x="{i * pas + pas * 0.2:.1f}" y="{haut - max(haut * x / vmax, 1.5):.1f}" width="{pas * 0.6:.1f}" '
            f'height="{max(haut * x / vmax, 1.5):.1f}" rx="2" fill="{couleur}">'
            f'<title>{MOIS_COURTS[m - 1]} : {nombre(x, decimales)} {unite}</title></rect>'
            for i, (m, x) in enumerate(zip(mois, valeurs)))
        return f'<svg class="mini" width="{larg}" height="{haut + h_lib}">{barres}{libelles}</svg>'
    vmin = min(valeurs)
    etendue = max(vmax - vmin, 1e-9)
    pts = [((i + 0.5) * pas, 3 + (haut - 6) * (1 - (x - vmin) / etendue)) for i, x in enumerate(valeurs)]
    trace = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    points = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{couleur}"><title>{MOIS_COURTS[m - 1]} : '
                     f'{nombre(val, 1)} {unite}</title></circle>' for (x, y), m, val in zip(pts, mois, valeurs))
    return (f'<svg class="mini" width="{larg}" height="{haut + h_lib}"><polyline points="{trace}" fill="none" '
            f'stroke="{couleur}" stroke-width="2" stroke-linejoin="round"/>{points}{libelles}</svg>')


def _jauge(part, couleur, fond_arc, larg, haut) -> str:
    """Demi-cercle de progression (part entre 0 et 1) avec le pourcentage au centre."""
    part = min(max(part, 0.0), 1.0)
    e = EPAISSEUR_JAUGE
    r = min(larg / 2, haut) - e / 2 - 1
    cx, cy = larg / 2, haut - 1
    angle = np.pi * part
    fin_x, fin_y = cx - r * np.cos(angle), cy - r * np.sin(angle)
    arc_fond = f'M {cx - r:.1f} {cy:.1f} A {r:.1f} {r:.1f} 0 0 1 {cx + r:.1f} {cy:.1f}'
    arc = f'M {cx - r:.1f} {cy:.1f} A {r:.1f} {r:.1f} 0 0 1 {fin_x:.1f} {fin_y:.1f}'
    return (f'<svg class="mini" width="{larg}" height="{haut}"><title>{nombre(100 * part, 0)} % des DH la nuit</title>'
            f'<path d="{arc_fond}" fill="none" stroke="{fond_arc}" stroke-width="{e}"/>'
            + (f'<path d="{arc}" fill="none" stroke="{couleur}" stroke-width="{e}"/>' if part > 0 else "")
            + f'<text x="{cx:.1f}" y="{cy - 2:.1f}" font-size="13" font-weight="700" text-anchor="middle" '
            f'fill="currentColor">{nombre(100 * part, 0)} %</text></svg>')


# ============================================================
# CARTES
# ============================================================

def valeur_texte(valeur, decimales: int) -> str:
    return "—" if valeur is None else nombre(valeur, decimales)


def _statuts_cites(texte, hyp):
    """Statuts non « sourcé » des hypothèses citées par [[hyp:…]] dans un texte."""
    return sorted({hyp[i]["statut"] for i in MOTIF_REPERE.findall(texte or "") if i in hyp
                   and hyp[i]["statut"] != "sourcé"})


def cartes(resultats, hyp):
    """Cartes d'indicateurs dans l'ordre reçu ; fond teinté de la couleur de la carte, principale en couleur pleine."""
    blocs = []
    for d, r in resultats:
        ind = REGISTRE[d["id"]]
        c = COULEURS_TEINTES[ind.teinte]
        titre = html.escape(remplacer_reperes(d["libelle"], hyp))
        dec = int(d.get("decimales", 0) or 0)
        bulle = html.escape(remplacer_reperes(d["bulle"], hyp))
        statuts = "".join(f'<br><span class="statut" style="color:{COULEURS_STATUT.get(s, GRIS_DOUX)};'
                          f'border-color:{COULEURS_STATUT.get(s, GRIS_DOUX)}">source : {html.escape(s)}</span>'
                          for s in _statuts_cites(d["bulle"] + d["libelle"], hyp))
        mini = mini_graphique(r.info.get("profil"), "white" if ind.principale else c, d["unite"], dec,
                              not ind.principale)
        blocs.append(
            f'<div class="carte{" principale" if ind.principale else ""}" style="--c:{c};'
            f'--fond:{melange(c, PART_TEINTE_FOND)};--icone:{melange(c, PART_TEINTE_ICONE)}">'
            f'<div class="haut"><div class="icone">{_icone(ind.icone)}</div>'
            f'<div class="titre">{titre}</div></div>'
            f'<div class="info">i<div class="bulle"><b>{titre}</b><br>{bulle}{statuts}'
            f'<br><span style="color:{TEAL};font-weight:600">Détail : onglet Méthode & sources</span></div></div>'
            f'<div class="milieu"><div class="valeur">{valeur_texte(r.valeur, dec)}<span>{html.escape(d["unite"])}</span></div>'
            f'{mini}</div><div class="detail">{html.escape(r.detail)}</div></div>')
    st.markdown(f'<div class="cartes">{"".join(blocs)}</div>', unsafe_allow_html=True)
