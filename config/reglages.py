"""
============================================================
 RÉGLAGES — version, valeurs par défaut et libellés de l'outil
============================================================
 Le réglage par défaut est celui de la RE2020. Les hypothèses
 chiffrées ne sont PAS ici : elles viennent de
 config/hypotheses.csv (généré depuis docs/sources/hypotheses.xlsx).
 Couleurs, police et dimensions : config/charte.py.
============================================================
"""

# --- Version (dernier chiffre pair = gros changement, impair = correction) ---
VERSION = "0.9.12"
STATUT_VERSION = "version de test"

# --- Auteur et liens (pied de page, README) ---
AUTEUR = "Guillaume Meunier"
LIEN_CODE_SOURCE = "https://github.com/Alliages/vulgarisateur_DH"
LIEN_EN_LIGNE = "https://vulgarisateurdh.streamlit.app/"

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
ONGLET_ACCUEIL = "Accueil"                 # page d'explication (0.9.11), ouverte au démarrage
ONGLET_ANALYSER, ONGLET_COMPARER, ONGLET_CREER = "①  Analyser", "②  Comparer", "③  Créer jour / semaine"
ONGLET_EXPORTER, ONGLET_METHODE = "④  Exporter", "Méthode & sources"
ONGLETS = [ONGLET_ACCUEIL, ONGLET_ANALYSER, ONGLET_COMPARER, ONGLET_CREER, ONGLET_EXPORTER, ONGLET_METHODE]

# --- Familles de fichiers météo (colonne « famille » du catalogue), dans l'ordre de la fenêtre de choix ---
FAMILLES = ["RE2020", "Observations", "TRACC"]
FAMILLE_IMPORTES = "Importés"          # fichiers chargés pendant la session (et fichier C)
DH_ECHELLE_CHOIX = 3300                # °C.h : haut de l'échelle des barres de DH de la fenêtre de choix (commune
                                       # à toutes les familles ; au-delà, barre pleine)
LIBELLE_SEUILS_DH = "Seuils d'inconfort pour le DH"

# --- Libellés des choix ---------------------------------------------------
LIBELLES_METHODE = {"RE2020": "RE2020", "basic": "Basic 26/28"}
LIBELLES_CRITERE_JOURNEE = {"moyenne": "T moyenne", "max": "T max"}
LIBELLES_CRITERE_SEMAINE = {"moyenne": "T moyenne", "moyenne_max": "Moyenne des T max",
                            "pointe_max": "Pointe T max"}
# --- … et leur explication sous les graphiques de la semaine et de la journée ---
CRITERES_SEMAINE_TEXTE = {"moyenne": "température moyenne la plus élevée sur {n} jours",
                          "moyenne_max": "moyenne des maximales la plus élevée sur {n} jours",
                          "pointe_max": "semaine centrée sur la pointe de chaleur"}
CRITERES_JOURNEE_TEXTE = {"moyenne": "température moyenne la plus élevée", "max": "température maximale la plus élevée"}
