# ============================================================
# MODULE INTERFACE — LAYOUT DE L'APPLICATION DASH
# ============================================================
# Définit la mise en page complète de l'interface utilisateur.
# Utilise dash-bootstrap-components pour un rendu responsive.
# ============================================================

from dash import dcc, html
import dash_bootstrap_components as dbc
from modules.variables import (
    JOURS_SEMAINE,
    DEFAUT_H_PIC, DEFAUT_TYPE_COURBE, DEFAUT_ALEATOIRE,
    DEFAUT_T_MINUIT, DEFAUT_T_PIC_BAS, DEFAUT_T_PIC_HAUT,
    DEFAUT_SEMAINE, DEFAUT_H_PIC_SEMAINE,
    DEFAUT_TYPE_SEMAINE, DEFAUT_ALEATOIRE_SEMAINE
)

# ============================================================
# COMPOSANTS RÉUTILISABLES
# ============================================================

def input_numerique(id_: str, valeur: float, min_val: float = -10,
                    max_val: float = 60, pas: float = 0.5) -> dbc.Input:
    """Champ de saisie numérique stylé pour les températures."""
    return dbc.Input(
        id=id_,
        type='number',
        value=valeur,
        min=min_val,
        max=max_val,
        step=pas,
        style={'width': '90px', 'textAlign': 'center'}
    )


def carte_resultat(titre: str, id_valeur: str, unite: str = '°C.h',
                   couleur: str = '#1D3557') -> dbc.Card:
    """Carte d'affichage d'un résultat DH."""
    return dbc.Card([
        dbc.CardBody([
            html.P(titre, className='text-muted mb-1',
                   style={'fontSize': '0.82rem', 'fontWeight': '500'}),
            html.H5(
                id=id_valeur,
                children='—',
                style={'color': couleur, 'fontWeight': 'bold', 'marginBottom': '0'}
            ),
            html.Small(unite, className='text-muted')
        ], style={'padding': '12px 16px'})
    ], style={'borderLeft': f'4px solid {couleur}', 'borderRadius': '8px'})


# ============================================================
# ONGLET JOURNÉE
# ============================================================

def creer_onglet_jour() -> dbc.Tab:
    """Crée l'onglet de calcul pour une journée."""
    return dbc.Tab(
        label='📅 Journée',
        tab_id='tab-jour',
        children=[
            dbc.Row([

                # ── Colonne de gauche : paramètres ───────────────────
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H6(
                            '⚙️ Paramètres de la journée',
                            className='mb-0', style={'fontWeight': '600'}
                        )),
                        dbc.CardBody([

                            # Heure de pic
                            dbc.Row([
                                dbc.Col(html.Label(
                                    'Heure de pic',
                                    style={'fontWeight': '500', 'fontSize': '0.9rem'}
                                ), width=7),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id='h-pic-jour',
                                        options=[
                                            {'label': '13h (pic à midi)', 'value': '13h'},
                                            {'label': '15h (canicule)', 'value': '15h'}
                                        ],
                                        value=DEFAUT_H_PIC,
                                        clearable=False,
                                        style={'fontSize': '0.88rem'}
                                    ), width=5
                                )
                            ], className='mb-3 align-items-center'),

                            # Type de courbe
                            dbc.Row([
                                dbc.Col(html.Label(
                                    'Type de courbe',
                                    style={'fontWeight': '500', 'fontSize': '0.9rem'}
                                ), width=7),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id='type-courbe-jour',
                                        options=[
                                            {'label': '〰️ Lissé (sinusoïde)', 'value': 'Lissé'},
                                            {'label': '📐 Brut (linéaire)',    'value': 'Brut'},
                                            {'label': '🎲 Aléatoire',         'value': 'Aléatoire'}
                                        ],
                                        value=DEFAUT_TYPE_COURBE,
                                        clearable=False,
                                        style={'fontSize': '0.88rem'}
                                    ), width=5
                                )
                            ], className='mb-3 align-items-center'),

                            html.Hr(style={'margin': '12px 0'}),

                            # Températures
                            html.P('🌡️ Températures', style={
                                'fontWeight': '600', 'fontSize': '0.9rem', 'marginBottom': '10px'
                            }),

                            dbc.Row([
                                dbc.Col(html.Label(
                                    'T° à minuit (T₀)',
                                    style={'fontSize': '0.88rem'}
                                ), width=7),
                                dbc.Col(dbc.InputGroup([
                                    input_numerique('t-minuit-jour', DEFAUT_T_MINUIT),
                                    dbc.InputGroupText('°C')
                                ], size='sm'), width=5)
                            ], className='mb-2 align-items-center'),

                            dbc.Row([
                                dbc.Col(html.Label(
                                    'T° pic bas (min à 5h)',
                                    style={'fontSize': '0.88rem'}
                                ), width=7),
                                dbc.Col(dbc.InputGroup([
                                    input_numerique('t-pic-bas-jour', DEFAUT_T_PIC_BAS),
                                    dbc.InputGroupText('°C')
                                ], size='sm'), width=5)
                            ], className='mb-2 align-items-center'),

                            dbc.Row([
                                dbc.Col(html.Label(
                                    'T° pic haut (maximum)',
                                    style={'fontSize': '0.88rem'}
                                ), width=7),
                                dbc.Col(dbc.InputGroup([
                                    input_numerique('t-pic-haut-jour', DEFAUT_T_PIC_HAUT),
                                    dbc.InputGroupText('°C')
                                ], size='sm'), width=5)
                            ], className='mb-3 align-items-center'),

                            # Bouton calculer
                            dbc.Button(
                                '🔢 Calculer',
                                id='btn-calculer-jour',
                                color='danger',
                                className='w-100',
                                n_clicks=0,
                                style={'fontWeight': '600'}
                            ),

                            # Message d'alerte (validation)
                            html.Div(id='alerte-jour', className='mt-2'),

                        ])
                    ], className='mb-3 shadow-sm')
                ], md=3),

                # ── Colonne de droite : résultats + graphiques ────────
                dbc.Col([

                    # Cartes de résultats
                    dbc.Row([
                        dbc.Col(carte_resultat(
                            'DH en occupation (RE2020)',
                            'res-dh-occ-jour', '°C.h', '#2E7D32'
                        ), md=3, className='mb-2'),
                        dbc.Col(carte_resultat(
                            'DH total 24h (hypothétique)',
                            'res-dh-total-jour', '°C.h', '#E65100'
                        ), md=3, className='mb-2'),
                        dbc.Col(carte_resultat(
                            'DH jour (6h–21h)',
                            'res-dh-jour', '°C.h', '#1565C0'
                        ), md=3, className='mb-2'),
                        dbc.Col(carte_resultat(
                            'DH nuit (0h–5h + 22h–23h)',
                            'res-dh-nuit-jour', '°C.h', '#4A148C'
                        ), md=3, className='mb-2'),
                    ], className='mb-3'),

                    # Graphique principal
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(
                                id='graphique-jour',
                                config={'displayModeBar': True, 'toImageButtonOptions': {
                                    'format': 'png', 'filename': 'dh_journee'
                                }},
                                style={'height': '550px'}
                            )
                        ], style={'padding': '8px'})
                    ], className='shadow-sm')

                ], md=9)
            ], className='mt-3')
        ]
    )


# ============================================================
# ONGLET SEMAINE
# ============================================================

def creer_ligne_jour_semaine(i: int) -> dbc.Row:
    """
    Génère une ligne de saisie pour le jour i de la semaine.
    Chaque ligne contient : T0, T_max, T_min, H_pic, Type, Aléatoire.
    """
    nom_jour = JOURS_SEMAINE[i]
    T0_def, Tmax_def, Tmin_def = DEFAUT_SEMAINE[i]

    return dbc.Row([
        # Nom du jour
        dbc.Col(html.Span(
            nom_jour,
            style={'fontWeight': '500', 'fontSize': '0.88rem'}
        ), width=1),

        # T° minuit
        dbc.Col(dbc.InputGroup([
            dbc.Input(
                id=f'T0-{i}', type='number',
                value=T0_def, min=-10, max=50, step=0.5,
                style={'textAlign': 'center', 'fontSize': '0.85rem'}
            ),
            dbc.InputGroupText('°C', style={'fontSize': '0.8rem', 'padding': '2px 6px'})
        ], size='sm'), width=2),

        # T° pic haut
        dbc.Col(dbc.InputGroup([
            dbc.Input(
                id=f'Tmax-{i}', type='number',
                value=Tmax_def, min=0, max=60, step=0.5,
                style={'textAlign': 'center', 'fontSize': '0.85rem'}
            ),
            dbc.InputGroupText('°C', style={'fontSize': '0.8rem', 'padding': '2px 6px'})
        ], size='sm'), width=2),

        # T° pic bas
        dbc.Col(dbc.InputGroup([
            dbc.Input(
                id=f'Tmin-{i}', type='number',
                value=Tmin_def, min=-10, max=40, step=0.5,
                style={'textAlign': 'center', 'fontSize': '0.85rem'}
            ),
            dbc.InputGroupText('°C', style={'fontSize': '0.8rem', 'padding': '2px 6px'})
        ], size='sm'), width=2),

        # Heure pic
        dbc.Col(dcc.Dropdown(
            id=f'hpic-{i}',
            options=[
                {'label': '13h', 'value': '13h'},
                {'label': '15h', 'value': '15h'}
            ],
            value=DEFAUT_H_PIC_SEMAINE,
            clearable=False,
            style={'fontSize': '0.82rem'}
        ), width=2),

        # Type courbe
        dbc.Col(dcc.Dropdown(
            id=f'type-{i}',
            options=[
                {'label': 'Lissé',     'value': 'Lissé'},
                {'label': 'Brut',      'value': 'Brut'},
                {'label': 'Aléatoire', 'value': 'Aléatoire'}
            ],
            value=DEFAUT_TYPE_SEMAINE,
            clearable=False,
            style={'fontSize': '0.82rem'}
        ), width=2),

        # Aléatoire
        dbc.Col(dbc.Checklist(
            id=f'alea-{i}',
            options=[{'label': '', 'value': 'oui'}],
            value=['oui'] if DEFAUT_ALEATOIRE_SEMAINE else [],
            style={'paddingTop': '6px'}
        ), width=1),

    ], className='mb-2 align-items-center', style={
        'borderBottom': '1px solid #eee', 'paddingBottom': '8px'
    })


def creer_onglet_semaine() -> dbc.Tab:
    """Crée l'onglet de calcul pour une semaine."""

    # En-tête du tableau de saisie
    entete = dbc.Row([
        dbc.Col(html.Small('Jour',       className='text-muted fw-bold'), width=1),
        dbc.Col(html.Small('T° minuit',  className='text-muted fw-bold'), width=2),
        dbc.Col(html.Small('T° pic haut',className='text-muted fw-bold'), width=2),
        dbc.Col(html.Small('T° pic bas', className='text-muted fw-bold'), width=2),
        dbc.Col(html.Small('H. pic',     className='text-muted fw-bold'), width=2),
        dbc.Col(html.Small('Courbe',     className='text-muted fw-bold'), width=2),
        dbc.Col(html.Small('Aléat.',     className='text-muted fw-bold'), width=1),
    ], className='mb-2 px-2', style={'backgroundColor': '#f8f9fa', 'borderRadius': '4px',
                                      'padding': '6px 8px'})

    # Lignes de saisie pour les 7 jours
    lignes_jours = [creer_ligne_jour_semaine(i) for i in range(7)]

    return dbc.Tab(
        label='📆 Semaine',
        tab_id='tab-semaine',
        children=[
            dbc.Row([

                # ── Colonne de gauche : tableau de saisie ────────────
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H6(
                            '⚙️ Paramètres de la semaine',
                            className='mb-0', style={'fontWeight': '600'}
                        )),
                        dbc.CardBody([
                            entete,
                            *lignes_jours,
                            html.Div(className='mt-3'),
                            dbc.Button(
                                '🔢 Calculer la semaine',
                                id='btn-calculer-semaine',
                                color='danger',
                                className='w-100',
                                n_clicks=0,
                                style={'fontWeight': '600'}
                            ),
                            html.Div(id='alerte-semaine', className='mt-2'),
                        ])
                    ], className='shadow-sm')
                ], md=7),

                # ── Colonne de droite : résultats ─────────────────────
                dbc.Col([
                    # Cartes de résultats semaine
                    dbc.Row([
                        dbc.Col(carte_resultat(
                            'DH en occupation — semaine (RE2020)',
                            'res-dh-occ-sem', '°C.h', '#2E7D32'
                        ), width=6, className='mb-2'),
                        dbc.Col(carte_resultat(
                            'DH total 24h — semaine (hypothétique)',
                            'res-dh-total-sem', '°C.h', '#E65100'
                        ), width=6, className='mb-2'),
                    ]),
                    dbc.Row([
                        dbc.Col(carte_resultat(
                            'DH jour — semaine (6h–21h)',
                            'res-dh-jour-sem', '°C.h', '#1565C0'
                        ), width=6, className='mb-2'),
                        dbc.Col(carte_resultat(
                            'DH nuit — semaine',
                            'res-dh-nuit-sem', '°C.h', '#4A148C'
                        ), width=6, className='mb-2'),
                    ]),

                    # Graphiques
                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(
                                id='graphique-semaine',
                                config={'displayModeBar': True, 'toImageButtonOptions': {
                                    'format': 'png', 'filename': 'dh_semaine'
                                }},
                                style={'height': '600px'}
                            )
                        ], style={'padding': '8px'})
                    ], className='shadow-sm mb-3'),

                    dbc.Card([
                        dbc.CardBody([
                            dcc.Graph(
                                id='graphique-detail-semaine',
                                config={'displayModeBar': False},
                                style={'height': '320px'}
                            )
                        ], style={'padding': '8px'})
                    ], className='shadow-sm')

                ], md=5)
            ], className='mt-3')
        ]
    )


# ============================================================
# LAYOUT PRINCIPAL
# ============================================================

def create_layout() -> html.Div:
    """
    Crée et retourne le layout complet de l'application Dash.
    Contient :
      - En-tête avec titre et description
      - Onglets : Journée / Semaine
      - Légende explicative des couleurs
      - Stockage intermédiaire (dcc.Store)
    """
    return html.Div([

        # ── En-tête ───────────────────────────────────────────────────
        dbc.Navbar([
            dbc.Container([
                html.A([
                    html.Span('🌡️ ', style={'fontSize': '1.4rem'}),
                    html.Span(
                        'Calculateur DH — RE2020',
                        style={'fontWeight': '700', 'fontSize': '1.15rem', 'color': 'white'}
                    )
                ], href='/', style={'textDecoration': 'none'}),
                html.Span(
                    'Degrés-Heures d\'inconfort thermique',
                    style={'color': 'rgba(255,255,255,0.75)', 'fontSize': '0.85rem',
                           'marginLeft': '16px'}
                )
            ], fluid=True)
        ], color='#1D3557', dark=True, className='mb-3'),

        # ── Corps principal ───────────────────────────────────────────
        dbc.Container([

            # Bandeau d'info RE2020
            dbc.Alert([
                html.Strong('ℹ️ Rappel RE2020 : '),
                html.Span(
                    'Le DH mesure l\'inconfort thermique estival. Seuil nuit = 26°C, '
                    'seuil jour = 28°C. Occupation résidentielle : 0h–9h et 17h–23h. '
                    'Zones vertes = heures occupées, zones oranges = heures non-occupées.'
                )
            ], color='light', className='mb-3 border',
               style={'fontSize': '0.85rem', 'borderLeft': '4px solid #1D3557 !important'}),

            # Onglets principaux
            dbc.Tabs([
                creer_onglet_jour(),
                creer_onglet_semaine()
            ], id='tabs-principal', active_tab='tab-jour'),

        ], fluid=True),

        # ── Pied de page ──────────────────────────────────────────────
        html.Footer([
            dbc.Container([
                html.Hr(style={'margin': '8px 0'}),
                html.P(
                    'Calculateur DH RE2020 — Basé sur l\'outil Excel "Vulgarisation_DH" — '
                    'Voir le dépôt GitHub pour la documentation complète.',
                    className='text-muted text-center',
                    style={'fontSize': '0.78rem', 'margin': '4px 0'}
                )
            ], fluid=True)
        ], className='mt-4'),

        # Stockage intermédiaire pour les résultats
        dcc.Store(id='store-resultats-jour'),
        dcc.Store(id='store-resultats-semaine'),

    ], style={'fontFamily': "'Inter', 'Segoe UI', sans-serif", 'backgroundColor': '#FAFAFA'})
