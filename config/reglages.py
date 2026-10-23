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
VERSION = "0.8.0"
STATUT_VERSION = "non fonctionnelle"

# --- Réglage par défaut (= RE2020) ---------------------------------------
REGLAGE_RE2020 = {
    "methode": "RE2020",              # "RE2020" ou "basic"
    "occupation": True,               # DH en occupation (logement)
    "critere_journee": "moyenne",     # "moyenne" ou "max"
    "critere_semaine": "moyenne",     # "moyenne", "moyenne_max" ou "pointe_max"
    "lignes": [28.0],                 # lignes horizontales (°C)
}
FICHIER_DEFAUT = "H1a_th_d"

# --- Libellés des choix ---------------------------------------------------
LIBELLES_METHODE = {"RE2020": "RE2020", "basic": "Basic 26/28"}
LIBELLES_CRITERE_JOURNEE = {"moyenne": "T moyenne", "max": "T max"}
LIBELLES_CRITERE_SEMAINE = {"moyenne": "T moyenne", "moyenne_max": "Moyenne des T max",
                            "pointe_max": "Pointe T max"}

# --- Palette du projet ------------------------------------------------------
CARAMEL = "#f7b267"      # DH, nuits ≥ 20 °C, hypothèses
CORAIL = "#f05d5e"       # température, nuits ≥ 24 °C
TEAL = "#0f7173"         # fichier A, éléments actifs
GRIS = "#272932"         # texte, axes, seuils
INDIGO = "#2e294e"       # bandeau, fichier B, titres
BLEU_MENU = "#48BEFF"    # couleur complémentaire du menu
BLEU_CLAIR = "#E4F4FF"   # fond clair (champs de saisie)
CARAMEL_CLAIR = "#FDF0E1"
FOND = "#F7F6F3"
GRIS_DOUX = "#6B6B76"
TRAIT = "#D5D3CF"
