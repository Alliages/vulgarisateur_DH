"""
============================================================
 CALCULATEUR DH RE2020 — APPLICATION DASH
============================================================
 Outil de calcul des Degrés-Heures (DH) d'inconfort
 thermique estival selon la réglementation française RE2020.

 Structure du projet :
 ┌─ app.py                ← Ce fichier (point d'entrée)
 └─ modules/
    ├─ variables.py       ← Constantes et paramètres
    ├─ calculs.py         ← Formules de calcul (courbes + DH)
    ├─ interface.py       ← Layout de l'interface (Dash)
    └─ graphiques.py      ← Graphiques Plotly

 Lancement local :
   python app.py
   → Ouvrir http://127.0.0.1:8050 dans un navigateur

 Déploiement Render (GitHub) :
   Voir README.md
============================================================
"""

import time
import dash
from dash import Output, Input, State, no_update
import dash_bootstrap_components as dbc

# Modules du projet
from modules.interface import create_layout
from modules.calculs import calculer_jour, calculer_semaine
from modules.graphiques import (
    creer_graphique_jour,
    creer_graphique_semaine,
    creer_graphique_detail_semaine
)
from modules.variables import JOURS_SEMAINE

# ============================================================
# INITIALISATION DE L'APPLICATION
# ============================================================

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        # Police Inter pour un rendu soigné
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'
    ],
    title='Calculateur DH RE2020',
    meta_tags=[
        {'name': 'viewport', 'content': 'width=device-width, initial-scale=1'},
        {'name': 'description', 'content': 'Calculateur de Degrés-Heures RE2020'}
    ]
)

# Exposer le serveur Flask pour les déploiements (Render, Heroku, etc.)
server = app.server

# Layout de l'application (défini dans modules/interface.py)
app.layout = create_layout()


# ============================================================
# CALLBACK — ONGLET JOURNÉE
# ============================================================

@app.callback(
    # Sorties
    output=[
        Output('graphique-jour',   'figure'),
        Output('res-dh-occ-jour',  'children'),
        Output('res-dh-total-jour','children'),
        Output('res-dh-jour',      'children'),
        Output('res-dh-nuit-jour', 'children'),
        Output('alerte-jour',      'children'),
    ],
    # Déclencheur
    inputs=[Input('btn-calculer-jour', 'n_clicks')],
    # États des inputs (lus au moment du clic, pas déclencheurs)
    state=[
        State('h-pic-jour',      'value'),
        State('type-courbe-jour','value'),
        State('t-minuit-jour',   'value'),
        State('t-pic-bas-jour',  'value'),
        State('t-pic-haut-jour', 'value'),
    ],
    prevent_initial_call=True   # Ne pas calculer au chargement de la page
)
def calculer_et_afficher_jour(n_clicks, h_pic, type_courbe, t_minuit, t_pic_bas, t_pic_haut):
    """
    Callback principal pour l'onglet Journée.
    Déclenché uniquement par le bouton "Calculer".

    Valide les entrées, lance le calcul DH, met à jour le graphique
    et les cartes de résultats.
    """
    # ── Validation des entrées ────────────────────────────────────────
    alerte = None

    # Vérification des valeurs manquantes
    if None in [t_minuit, t_pic_bas, t_pic_haut]:
        alerte = dbc.Alert(
            '⚠️ Veuillez renseigner toutes les températures.',
            color='warning', className='mt-2', style={'fontSize': '0.85rem'}
        )
        return no_update, '—', '—', '—', '—', alerte

    # Vérification de la cohérence des températures
    # DOUTE : L'Excel suppose T_min ≤ T0 ≤ T_max. Si ce n'est pas le cas,
    #         les courbes peuvent être physiquement incohérentes.
    if t_pic_bas > t_minuit:
        alerte = dbc.Alert(
            '⚠️ T° pic bas devrait être ≤ T° à minuit (minimum avant minuit).',
            color='warning', className='mt-2', style={'fontSize': '0.85rem'}
        )
    if t_minuit > t_pic_haut:
        alerte = dbc.Alert(
            '⚠️ T° à minuit devrait être ≤ T° pic haut.',
            color='warning', className='mt-2', style={'fontSize': '0.85rem'}
        )

    # Utiliser un seed basé sur l'heure pour le mode aléatoire
    # → Chaque clic produit une courbe aléatoire différente
    seed = int(time.time() * 1000) % 1_000_000

    # ── Calcul DH ────────────────────────────────────────────────────
    aleatoire = (type_courbe == 'Aléatoire')

    resultat = calculer_jour(
        T0=float(t_minuit),
        T_min=float(t_pic_bas),
        T_max=float(t_pic_haut),
        H_pic_option=h_pic,
        type_courbe_option=type_courbe,
        aleatoire=aleatoire,
        seed=seed
    )

    # ── Génération du graphique ───────────────────────────────────────
    figure = creer_graphique_jour(resultat)

    # ── Formatage des résultats ───────────────────────────────────────
    def fmt(val: float) -> str:
        """Formate une valeur DH avec 2 décimales."""
        return f'{val:.2f} °C.h'

    return (
        figure,
        fmt(resultat['dh_occupation']),
        fmt(resultat['dh_total']),
        fmt(resultat['dh_jour']),
        fmt(resultat['dh_nuit']),
        alerte  # None si pas d'alerte
    )


# ============================================================
# CALLBACK — ONGLET SEMAINE
# ============================================================

# Construire dynamiquement la liste des Input/State pour les 7 jours
# (7 jours × 5 champs = 35 entrées + 1 bouton)
_inputs_semaine = [Input('btn-calculer-semaine', 'n_clicks')]

_states_semaine = []
for i in range(7):
    _states_semaine += [
        State(f'T0-{i}',   'value'),
        State(f'Tmax-{i}', 'value'),
        State(f'Tmin-{i}', 'value'),
        State(f'hpic-{i}', 'value'),
        State(f'type-{i}', 'value'),
        State(f'alea-{i}', 'value'),
    ]


@app.callback(
    output=[
        Output('graphique-semaine',        'figure'),
        Output('graphique-detail-semaine', 'figure'),
        Output('res-dh-occ-sem',           'children'),
        Output('res-dh-total-sem',         'children'),
        Output('res-dh-jour-sem',          'children'),
        Output('res-dh-nuit-sem',          'children'),
        Output('alerte-semaine',           'children'),
    ],
    inputs=_inputs_semaine,
    state=_states_semaine,
    prevent_initial_call=True
)
def calculer_et_afficher_semaine(n_clicks, *valeurs):
    """
    Callback principal pour l'onglet Semaine.
    Reconstruit les paramètres des 7 jours depuis les 35 valeurs d'entrée,
    lance le calcul DH, met à jour les graphiques et les cartes de résultats.
    """
    # ── Reconstruction des paramètres par jour ────────────────────────
    # Les 35 valeurs sont dans l'ordre : (T0, Tmax, Tmin, hpic, type, alea) × 7
    parametres_jours = []
    alertes = []

    for i in range(7):
        base = i * 6
        T0_val   = valeurs[base]
        Tmax_val = valeurs[base + 1]
        Tmin_val = valeurs[base + 2]
        hpic_val = valeurs[base + 3]
        type_val = valeurs[base + 4]
        alea_val = valeurs[base + 5]

        # Vérification des valeurs manquantes
        if None in [T0_val, Tmax_val, Tmin_val]:
            alertes.append(f'{JOURS_SEMAINE[i]} : températures manquantes')
            # Valeur de substitution pour ne pas bloquer les autres jours
            T0_val   = T0_val   or 25.0
            Tmax_val = Tmax_val or 35.0
            Tmin_val = Tmin_val or 20.0

        # Cohérence thermique
        if Tmin_val is not None and T0_val is not None and Tmin_val > T0_val:
            alertes.append(f'{JOURS_SEMAINE[i]} : T° pic bas > T° minuit')

        aleatoire = bool(alea_val) and 'oui' in (alea_val or [])

        parametres_jours.append({
            'T0':                float(T0_val),
            'T_max':             float(Tmax_val),
            'T_min':             float(Tmin_val),
            'H_pic_option':      hpic_val or '15h',
            'type_courbe_option':type_val or 'Lissé',
            'aleatoire':         aleatoire
        })

    # Seed basé sur le timestamp (nouvelles courbes aléatoires à chaque clic)
    seed_base = int(time.time() * 1000) % 1_000_000

    # ── Calcul DH semaine ─────────────────────────────────────────────
    resultat_semaine = calculer_semaine(parametres_jours, seed_base=seed_base)

    # ── Graphiques ────────────────────────────────────────────────────
    fig_semaine = creer_graphique_semaine(resultat_semaine)
    fig_detail  = creer_graphique_detail_semaine(resultat_semaine)

    # ── Résultats ─────────────────────────────────────────────────────
    def fmt(val: float) -> str:
        return f'{val:.2f} °C.h'

    # Alerte d'avertissement si des problèmes détectés
    alerte_html = None
    if alertes:
        alerte_html = dbc.Alert(
            [html.Strong('⚠️ Avertissements : '), html.Br(),
             html.Ul([html.Li(a) for a in alertes])],
            color='warning', className='mt-2', style={'fontSize': '0.85rem'}
        )

    return (
        fig_semaine,
        fig_detail,
        fmt(resultat_semaine['dh_occupation']),
        fmt(resultat_semaine['dh_total']),
        fmt(resultat_semaine['dh_jour']),
        fmt(resultat_semaine['dh_nuit']),
        alerte_html
    )


# ============================================================
# LANCEMENT
# ============================================================

if __name__ == '__main__':
    print("=" * 55)
    print("  Calculateur DH RE2020")
    print("  Ouvrir dans un navigateur : http://127.0.0.1:8050")
    print("=" * 55)
    app.run(debug=True, host='0.0.0.0', port=8050)
