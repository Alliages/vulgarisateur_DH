"""
============================================================
 RÉGLAGES — valeurs par défaut de l'outil et charte graphique
============================================================
 Le réglage par défaut est celui de la RE2020. Les hypothèses
 chiffrées ne sont PAS ici : elles viennent de
 config/hypotheses.csv (généré depuis docs/sources/hypotheses.xlsx).
============================================================
"""

# --- Version (dernier chiffre pair = gros changement, impair = correction) ---
VERSION = "0.9.2"
STATUT_VERSION = "version de test"

# --- Réglage par défaut (= RE2020) ---------------------------------------
REGLAGE_RE2020 = {
    "methode": "RE2020",              # "RE2020" ou "basic"
    "occupation": True,               # DH en occupation (logement)
    "critere_journee": "moyenne",     # "moyenne" ou "max"
    "critere_semaine": "moyenne",     # "moyenne", "moyenne_max" ou "pointe_max"
    "lignes": [28.0],                 # lignes horizontales (°C)
}
FICHIER_DEFAUT = "H1a_th_d"

# --- Onglets de la page (le nom sert aussi de clé pour passer d'un onglet à l'autre) ---
ONGLET_ANALYSER, ONGLET_COMPARER, ONGLET_CREER = "①  Analyser", "②  Comparer", "③  Créer jour / semaine"
ONGLET_EXPORTER, ONGLET_METHODE = "④  Exporter", "Méthode & sources"
ONGLETS = [ONGLET_ANALYSER, ONGLET_COMPARER, ONGLET_CREER, ONGLET_EXPORTER, ONGLET_METHODE]

# --- Familles de fichiers météo (colonne « famille » du catalogue), dans l'ordre de la fenêtre de choix ---
FAMILLES = ["RE2020", "Relevés", "TRACC"]
FAMILLE_IMPORTES = "Importés"          # fichiers chargés pendant la session (et fichier C)
LIBELLE_SEUILS_DH = "Seuils d'inconfort pour le DH"

# --- Libellés des choix ---------------------------------------------------
LIBELLES_METHODE = {"RE2020": "RE2020", "basic": "Basic 26/28"}
LIBELLES_CRITERE_JOURNEE = {"moyenne": "T moyenne", "max": "T max"}
LIBELLES_CRITERE_SEMAINE = {"moyenne": "T moyenne", "moyenne_max": "Moyenne des T max",
                            "pointe_max": "Pointe T max"}

# --- Palette du projet ------------------------------------------------------
CARAMEL = "#f7b267"      # barres de DH, écart entre fichiers, hypothèses
CORAIL = "#f05d5e"       # température, DH (cartes), fichier de l'onglet Analyser
TEAL = "#0f7173"         # second fichier (Comparer), température moyenne
GRIS = "#272932"         # texte, axes, seuils
INDIGO = "#2e294e"       # nuit (indicateurs nocturnes), barre des onglets, titres
BLEU_MENU = "#48BEFF"    # couleur complémentaire du menu
BLEU_CLAIR = "#E4F4FF"   # fond clair (champs de saisie)
CARAMEL_CLAIR = "#FDF0E1"
FOND = "#ECEAE5"          # fond de page gris chaud (les cartes blanches ressortent)
BLANC = "#FFFFFF"
OMBRE = "0 1px 2px rgba(39,41,50,.04), 0 6px 18px rgba(39,41,50,.07)"   # ombre douce des cartes
RAYON = "18px"            # arrondi des cartes
BLEU_FRAIS = "#1C6E9C"    # texte « plus frais » (pastilles d'écart, bande < 20 °C)

# --- Couleurs des deux fichiers de l'onglet Comparer (option A, 28/10/2026) ---
COULEUR_FICHIER_1 = CORAIL   # fichier de l'onglet Analyser (même couleur que dans l'onglet 1)
COULEUR_FICHIER_2 = TEAL     # second fichier
GRIS_DOUX = "#6B6B76"
TRAIT = "#D5D3CF"
