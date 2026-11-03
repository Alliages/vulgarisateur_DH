"""
============================================================
 CHARTE — couleurs, police et dimensions de l'interface
============================================================
 Tout ce qui règle l'APPARENCE est ici (les valeurs de calcul sont
 dans docs/sources/hypotheses.xlsx, les réglages et libellés dans
 config/reglages.py). Importé par interface/*.py.
============================================================
"""

# ============================================================
# PALETTE DU PROJET
# ============================================================
CARAMEL = "#f7b267"      # barres de DH, écart entre fichiers, hypothèses
CORAIL = "#f05d5e"       # température, DH (cartes), fichier de l'onglet Analyser
TEAL = "#0f7173"         # second fichier (Comparer), température moyenne
VERT = "#5aa77f"         # bas du dégradé des DH (zones et fichiers peu chauds), accordé au TEAL
GRIS = "#272932"         # texte, axes, seuils
INDIGO = "#2e294e"       # nuit (indicateurs nocturnes), barre des onglets, titres
BLEU_MENU = "#48BEFF"    # couleur complémentaire du menu

# --- Teintes dérivées ---
BLEU_CLAIR = "#E4F4FF"   # fond clair (champs de saisie)
CARAMEL_CLAIR = "#FDF0E1"
FOND = "#ECEAE5"         # fond de page gris chaud (les cartes blanches ressortent)
BLANC = "#FFFFFF"
BLEU_FRAIS = "#1C6E9C"   # texte « plus frais » (pastilles d'écart, bande < 20 °C)
GRIS_DOUX = "#6B6B76"
TRAIT = "#D5D3CF"
INDIGO_SURVOL = "#4A4480"   # indigo éclairci (survol des boutons et de « Réglages »)
CONTOUR_ONGLET = "#2C5E6E"  # contour des pastilles de la barre des onglets (bleu canard sombre)

# --- Formes ---
OMBRE = "0 1px 2px rgba(39,41,50,.04), 0 6px 18px rgba(39,41,50,.07)"   # ombre douce des cartes
RAYON = "18px"           # arrondi des cartes
POLICE = "Inter, Segoe UI, sans-serif"

# ============================================================
# COULEURS PAR RÔLE
# ============================================================
# --- Les deux fichiers de l'onglet Comparer (option A, 28/10/2026) ---
COULEUR_FICHIER_1 = CORAIL   # fichier de l'onglet Analyser (même couleur que dans l'onglet 1)
COULEUR_FICHIER_2 = TEAL     # second fichier

# --- Cartes d'indicateurs : la teinte est choisie dans le fichier de l'indicateur (calcul/indicateurs/) ---
COULEURS_TEINTES = {"chaud": CORAIL, "nuit": INDIGO, "moyenne": TEAL}
PART_TEINTE_FOND = 0.09      # fond des cartes : couleur de la carte mêlée de blanc
PART_TEINTE_ICONE = 0.20     # rond de l'icône
COULEURS_STATUT = {"sourcé": TEAL, "provisoire": "#C77D2E", "à préciser": CORAIL, "hypothèse": GRIS_DOUX}

# --- Graphiques ---
JAUNE_FONCE = CARAMEL                 # axe, graduations et titre « °C.h » des DH : la couleur des barres
ORANGE_FONCE = "#B5651D"              # trait et texte de la bande « au-dessus de 28 °C »
TEXTE_ECART = "#9C5A12"               # écart moyen écrit entre deux fichiers
GRIS_INOCCUPE = "rgba(39,41,50,0.08)" # heures d'absence (scénario d'occupation)
GRILLE = "#ECEAE6"
SEPARATEUR = "#E2E0DB"                # traits verticaux entre jours / mois
FOND_BANDE_CHAUDE = "rgba(247,178,103,0.22)"   # caramel clair : au-dessus du seuil chaud (28 °C)
FOND_BANDE_FRAICHE = "rgba(72,190,255,0.13)"   # bleu clair : en dessous du seuil frais (20 °C)
# --- Fenêtre de choix : dégradé des DH vert → caramel → corail (0.9.10) ---
SATURATION_MAX_VERT = 0.36           # vert-jaune doux entre le vert et le caramel (ni kaki, ni vert acide)
COULEURS_NUITS = ["#ECEAF3", "#8C86B8", INDIGO]   # Comparer : < 20 °C · tropicale (≥ 20 °C) · très chaude (≥ 24 °C)
BLEU_NUIT_CLAIR = "#8A9BD6"           # Analyser, bande des nuits : nuit tropicale (≥ 20 °C)
BLEU_NUIT_FONCE = "#111845"           # Analyser, bande des nuits : nuit très chaude (≥ 24 °C)

# ============================================================
# DIMENSIONS DES GRAPHIQUES (px)
# ============================================================
HAUTEUR_PRINCIPAL = 540
HAUTEUR_SECONDAIRE = 400
HAUTEUR_COMPARAISON = 580
HAUTEUR_NUITS = 350
MARGE_COTES = 64                      # à gauche et à droite (titres d'axe horizontaux compris)
MARGE_BAS = 20                        # sous l'axe (Plotly agrandit selon graduations, curseur, source)
PX_LIGNE_TITRE = 21                   # une ligne de titre / sous-titre
PX_LEGENDE = 34                       # légende (une ligne)
PX_TITRE_AXE = 24                     # titre d'axe horizontal au-dessus du tracé (sans légende)
EPAISSEUR_AXE = 2
TAILLE_FLECHE = 1.4
