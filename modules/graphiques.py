# ============================================================
# MODULE GRAPHIQUES — VISUALISATIONS PLOTLY
# ============================================================
# Génère tous les graphiques interactifs du calculateur DH.
# Utilise exclusivement la librairie Plotly.
# ============================================================

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from modules.variables import (
    HEURES_OCCUPATION, HEURES_NON_OCCUPATION,
    HEURES_PERIODE_JOUR, HEURES_PERIODE_NUIT,
    JOURS_SEMAINE,
    COULEUR_TEMPERATURE, COULEUR_SEUIL_26, COULEUR_SEUIL_28,
    COULEUR_DH_OCCUPE, COULEUR_DH_NON_OCCUPE, COULEUR_FOND_NUIT
)


# ============================================================
# GRAPHIQUE JOURNÉE
# ============================================================

def creer_graphique_jour(resultat: dict) -> go.Figure:
    """
    Crée le graphique principal pour une journée.

    Contient :
      - Courbe de température horaire
      - Seuil DH (26°C nuit / 28°C jour) — ligne en pointillés
      - Zones colorées : DH en occupation (vert) et hors occupation (orange)
      - Fond de couleur pour distinguer les heures occupées / non-occupées
      - Annotations sur les seuils

    Paramètre :
        resultat : Dictionnaire retourné par calculer_jour()
    """
    heures = list(range(24))
    temperatures = resultat['temperatures']
    seuils       = resultat['seuils']
    dh_par_heure = resultat['dh_par_heure']

    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.65, 0.35],
        shared_xaxes=True,
        subplot_titles=(
            "Courbe de température et seuils DH",
            "Degrés-Heures (DH) par heure"
        ),
        vertical_spacing=0.12
    )

    # ── Fonds colorés pour les périodes d'occupation ──────────────────
    # Heures occupées = fond vert très clair ; heures non-occupées = fond orange très clair
    for h in range(24):
        couleur_fond = 'rgba(200,230,200,0.18)' if h in HEURES_OCCUPATION else 'rgba(255,220,180,0.25)'
        fig.add_vrect(
            x0=h - 0.5, x1=h + 0.5,
            fillcolor=couleur_fond,
            opacity=1, layer='below', line_width=0,
            row=1, col=1
        )

    # ── Ligne de seuil DH ─────────────────────────────────────────────
    # Tracée heure par heure pour respecter le changement à 6h et 23h
    for h in range(23):
        fig.add_trace(go.Scatter(
            x=[h, h + 1],
            y=[seuils[h], seuils[h]],
            mode='lines',
            line=dict(
                color=COULEUR_SEUIL_26 if seuils[h] == 26 else COULEUR_SEUIL_28,
                width=2,
                dash='dot'
            ),
            showlegend=(h == 0),
            name='Seuil DH (26/28°C)',
            legendgroup='seuil',
            hoverinfo='skip'
        ), row=1, col=1)

    # ── Zones DH — couleur selon occupation ───────────────────────────
    # DH en OCCUPATION (vert)
    traces_occ_ajoutees = False
    for h in heures:
        if dh_par_heure[h] > 0 and h in HEURES_OCCUPATION:
            fig.add_trace(go.Scatter(
                x=[h, h, h + 0.95, h + 0.95, h],
                y=[seuils[h], temperatures[h], temperatures[h], seuils[h], seuils[h]],
                fill='toself',
                fillcolor=COULEUR_DH_OCCUPE,
                line=dict(width=0),
                mode='lines',
                name='DH en occupation',
                legendgroup='dh_occ',
                showlegend=not traces_occ_ajoutees,
                hovertemplate=f'h={h}h : DH = {dh_par_heure[h]:.2f} °C.h<extra>Occupé</extra>'
            ), row=1, col=1)
            traces_occ_ajoutees = True

    # DH HORS OCCUPATION (orange)
    traces_nok_ajoutees = False
    for h in heures:
        if dh_par_heure[h] > 0 and h in HEURES_NON_OCCUPATION:
            fig.add_trace(go.Scatter(
                x=[h, h, h + 0.95, h + 0.95, h],
                y=[seuils[h], temperatures[h], temperatures[h], seuils[h], seuils[h]],
                fill='toself',
                fillcolor=COULEUR_DH_NON_OCCUPE,
                line=dict(width=0),
                mode='lines',
                name='DH hors occupation',
                legendgroup='dh_nok',
                showlegend=not traces_nok_ajoutees,
                hovertemplate=f'h={h}h : DH = {dh_par_heure[h]:.2f} °C.h<extra>Non-occupé</extra>'
            ), row=1, col=1)
            traces_nok_ajoutees = True

    # ── Courbe de température ─────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=heures,
        y=temperatures,
        mode='lines+markers',
        name='Température (°C)',
        line=dict(color=COULEUR_TEMPERATURE, width=2.5),
        marker=dict(size=5, color=COULEUR_TEMPERATURE),
        hovertemplate='%{x}h : %{y:.1f} °C<extra></extra>'
    ), row=1, col=1)

    # ── Barres DH par heure ───────────────────────────────────────────
    couleurs_barres = [
        COULEUR_DH_OCCUPE.replace('0.4', '0.8') if h in HEURES_OCCUPATION
        else COULEUR_DH_NON_OCCUPE.replace('0.4', '0.8')
        for h in heures
    ]
    fig.add_trace(go.Bar(
        x=heures,
        y=dh_par_heure,
        marker_color=couleurs_barres,
        name='DH horaire',
        showlegend=False,
        hovertemplate='%{x}h : %{y:.2f} °C.h<extra></extra>'
    ), row=2, col=1)

    # ── Mise en forme générale ────────────────────────────────────────
    fig.update_layout(
        height=550,
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02,
            xanchor='right', x=1, bgcolor='rgba(255,255,255,0.8)'
        ),
        margin=dict(l=50, r=20, t=80, b=50),
        hovermode='x unified'
    )

    # Axe X
    fig.update_xaxes(
        tickvals=list(range(24)),
        ticktext=[f'{h}h' for h in range(24)],
        showgrid=True, gridcolor='rgba(200,200,200,0.4)',
        row=2, col=1
    )

    # Axe Y graphique 1 (températures)
    t_min_affiche = min(temperatures) - 3
    t_max_affiche = max(temperatures) + 3
    fig.update_yaxes(
        title_text='Température (°C)',
        range=[t_min_affiche, t_max_affiche],
        showgrid=True, gridcolor='rgba(200,200,200,0.4)',
        row=1, col=1
    )

    # Axe Y graphique 2 (DH)
    fig.update_yaxes(
        title_text='DH (°C.h)',
        showgrid=True, gridcolor='rgba(200,200,200,0.4)',
        row=2, col=1
    )

    # Annotations : seuils
    fig.add_annotation(
        x=23.5, y=26, text='Seuil 26°C', showarrow=False,
        font=dict(color=COULEUR_SEUIL_26, size=10),
        xanchor='right', row=1, col=1
    )
    fig.add_annotation(
        x=11, y=28.5, text='Seuil 28°C', showarrow=False,
        font=dict(color=COULEUR_SEUIL_28, size=10),
        xanchor='center', row=1, col=1
    )

    return fig


# ============================================================
# GRAPHIQUE SEMAINE
# ============================================================

def creer_graphique_semaine(resultat_semaine: dict) -> go.Figure:
    """
    Crée le graphique principal pour une semaine.

    Contient deux sous-graphiques :
      1. Courbes de température des 7 jours superposées
      2. Histogramme DH en occupation par jour

    Paramètre :
        resultat_semaine : Dictionnaire retourné par calculer_semaine()
    """
    resultats_jours = resultat_semaine['resultats_jours']
    heures = list(range(24))

    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.55, 0.45],
        shared_xaxes=False,
        subplot_titles=(
            "Courbes de température — 7 jours",
            "DH en occupation par jour (°C.h)"
        ),
        vertical_spacing=0.14
    )

    # Palette de couleurs pour les 7 jours
    couleurs_jours = [
        '#E63946', '#F4A261', '#2A9D8F',
        '#457B9D', '#6A4C93', '#E9C46A', '#264653'
    ]

    # ── Courbes de température ────────────────────────────────────────
    for i, res in enumerate(resultats_jours):
        fig.add_trace(go.Scatter(
            x=heures,
            y=res['temperatures'],
            mode='lines',
            name=JOURS_SEMAINE[i],
            line=dict(color=couleurs_jours[i], width=2),
            hovertemplate='%{x}h : %{y:.1f}°C<extra>' + JOURS_SEMAINE[i] + '</extra>'
        ), row=1, col=1)

    # Ligne de référence : seuil 28°C (journée)
    fig.add_hline(
        y=28, line_dash='dot', line_color=COULEUR_SEUIL_28,
        annotation_text='Seuil 28°C', annotation_position='right',
        row=1, col=1
    )
    # Ligne de référence : seuil 26°C (nuit)
    fig.add_hline(
        y=26, line_dash='dot', line_color=COULEUR_SEUIL_26,
        annotation_text='Seuil 26°C', annotation_position='right',
        row=1, col=1
    )

    # ── Histogramme DH par jour ───────────────────────────────────────
    dh_occ_par_jour  = [r['dh_occupation'] for r in resultats_jours]
    dh_jour_par_jour = [r['dh_jour'] for r in resultats_jours]
    dh_nuit_par_jour = [r['dh_nuit'] for r in resultats_jours]

    fig.add_trace(go.Bar(
        x=JOURS_SEMAINE,
        y=dh_occ_par_jour,
        name='DH en occupation (RE2020)',
        marker_color='rgba(76, 175, 80, 0.8)',
        hovertemplate='%{x} : %{y:.1f} °C.h<extra>DH occupation</extra>'
    ), row=2, col=1)

    fig.add_trace(go.Bar(
        x=JOURS_SEMAINE,
        y=[r['dh_total'] - r['dh_occupation'] for r in resultats_jours],
        name='DH hors occupation',
        marker_color='rgba(255, 152, 0, 0.6)',
        hovertemplate='%{x} : %{y:.1f} °C.h<extra>DH hors occ.</extra>'
    ), row=2, col=1)

    # ── Mise en forme ─────────────────────────────────────────────────
    fig.update_layout(
        height=600,
        barmode='stack',
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02,
            xanchor='right', x=1, bgcolor='rgba(255,255,255,0.8)'
        ),
        margin=dict(l=50, r=20, t=90, b=50),
        hovermode='x unified'
    )

    fig.update_xaxes(
        tickvals=list(range(24)),
        ticktext=[f'{h}h' for h in range(24)],
        showgrid=True, gridcolor='rgba(200,200,200,0.4)',
        row=1, col=1
    )
    fig.update_yaxes(
        title_text='Température (°C)',
        showgrid=True, gridcolor='rgba(200,200,200,0.4)',
        row=1, col=1
    )
    fig.update_yaxes(
        title_text='DH (°C.h)',
        showgrid=True, gridcolor='rgba(200,200,200,0.4)',
        row=2, col=1
    )

    return fig


# ============================================================
# GRAPHIQUE DH COMPARATIF (DÉTAIL SEMAINE)
# ============================================================

def creer_graphique_detail_semaine(resultat_semaine: dict) -> go.Figure:
    """
    Crée un graphique de détail pour visualiser le DH heure par heure
    pour chaque jour de la semaine (heatmap).

    Paramètre :
        resultat_semaine : Dictionnaire retourné par calculer_semaine()
    """
    resultats_jours = resultat_semaine['resultats_jours']

    # Construire la matrice DH : 7 lignes (jours) × 24 colonnes (heures)
    matrice_dh = np.array([r['dh_par_heure'] for r in resultats_jours])

    fig = go.Figure(data=go.Heatmap(
        z=matrice_dh,
        x=[f'{h}h' for h in range(24)],
        y=JOURS_SEMAINE,
        colorscale=[
            [0.0, 'white'],
            [0.3, '#FFEB3B'],
            [0.6, '#FF9800'],
            [1.0, '#B71C1C']
        ],
        colorbar=dict(title='DH (°C.h)'),
        hovertemplate='%{y} à %{x} : %{z:.2f} °C.h<extra></extra>'
    ))

    # Marquer les heures non-occupées avec un contour
    for h in HEURES_NON_OCCUPATION:
        fig.add_vrect(
            x0=f'{h}h', x1=f'{h+1}h' if h < 23 else '23h',
            fillcolor='rgba(0,0,0,0)', opacity=0.5,
            line=dict(color='rgba(0,0,120,0.3)', width=1),
            layer='above'
        )

    fig.update_layout(
        title='DH par heure et par jour (°C.h) — Zones bleues = non-occupé',
        height=320,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=80, r=20, t=60, b=50),
        xaxis=dict(side='bottom')
    )

    return fig
