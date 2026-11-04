"""
============================================================
 MÉTÉO ET CHALEUR — point d'entrée Streamlit
============================================================
 Lancement local :  streamlit run app.py
 Onglets : Accueil · ① Analyser · ② Comparer · ③ Créer · ④ Exporter · Méthode & sources
 Seul l'onglet ouvert est calculé (navigation dans le bloc fixe du haut).
 Réglage par défaut : RE2020 (config/reglages.py).
 Ce fichier ne fait que charger les données (en cache) et aiguiller
 vers les onglets : le calcul est dans calcul/, l'affichage dans interface/.
============================================================
"""

import os

import numpy as np
import streamlit as st

from calcul.analyse import analyser
from calcul.hypotheses import (CHEMIN_HYPOTHESES, CHEMIN_INDICATEURS, charger_hypotheses, charger_indicateurs,
                               remplacer_reperes, valeur)
from calcul.indicateurs import calculer_indicateurs, valeurs
from calcul.serie import CHEMIN_CATALOGUE, charger_catalogue, charger_serie, lire_fichier_importe
from config.reglages import (FAMILLE_IMPORTES, ONGLET_ACCUEIL, ONGLET_ANALYSER, ONGLET_COMPARER, ONGLET_CREER,
                             ONGLET_EXPORTER, ONGLET_METHODE, ONGLETS, REGLAGE_RE2020)
from export.export import FichierExport
from interface import (choix_fichier, erreurs, memoire, menu_reglages, onglet_accueil, onglet_analyser,
                       onglet_comparer, onglet_creer, onglet_exporter, onglet_methode)
from interface.composants import haut_de_page, pied

# ============================================================
# PARAMÈTRES
# ============================================================
TITRE_PAGE = "Météo et Chaleur"
ICONE_PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "interface", "favicon.png")  # logo de l'en-tête
INDICATEURS_RESUME = ["dh", "nuits_20"]  # chiffres clés des cartes de la fenêtre de choix (+ T max)
FICHIERS_CONFIG = (CHEMIN_HYPOTHESES, CHEMIN_INDICATEURS, CHEMIN_CATALOGUE)   # leur date invalide les caches

st.set_page_config(page_title=TITRE_PAGE, page_icon=ICONE_PAGE, layout="wide")
erreurs.filtrer_bruit_windows()          # console PowerShell : masque « ConnectionResetError [WinError 10054] »


# ============================================================
# DONNÉES EN CACHE (recalculées si un fichier de config/ change)
# ============================================================

def _signature_config() -> tuple:
    """Date de modification des CSV de config/ : un CSV régénéré invalide les caches sans redémarrer."""
    return tuple(os.path.getmtime(c) for c in FICHIERS_CONFIG)


@st.cache_data
def _hypotheses(signature):
    return charger_hypotheses(), charger_indicateurs(tous=True)


@st.cache_data
def _catalogue(signature):
    return charger_catalogue()


@st.cache_resource
def _serie_enregistree(identifiant, signature):
    """Série du catalogue, partagée entre les visiteurs : ses températures sont en lecture seule."""
    hyp, _ = _hypotheses(signature)
    ligne = _catalogue(signature).set_index("id").loc[identifiant].to_dict()
    ligne["id"] = identifiant
    serie = charger_serie(ligne, int(valeur(hyp, "decalage_heure_ete")))
    serie.t.setflags(write=False)
    return serie


def _resumer(serie) -> dict:
    """DH (réglage RE2020), nuits ≥ 20 °C et T max d'une série : chiffres clés de la fenêtre de choix."""
    v = valeurs(analyser(serie, REGLAGE_RE2020, HYP), REGLAGE_RE2020, HYP, INDICATEURS_RESUME)
    return {"dh": v.get("dh"), "nuits_20": v.get("nuits_20"), "tmax": float(np.max(serie.t))}


@st.cache_data(show_spinner="Calcul des chiffres clés du fichier…")
def _resume_enregistre(identifiant, signature):
    return _resumer(_serie_enregistree(identifiant, signature))


SIGNATURE = _signature_config()
HYP, TOUS_INDICATEURS = _hypotheses(SIGNATURE)
INDICATEURS = {d["id"]: d for d in TOUS_INDICATEURS}
ORDRE_DEFAUT = [d["id"] for d in TOUS_INDICATEURS if d["actif"]]     # ordre de hypotheses.xlsx
CATALOGUE = _catalogue(SIGNATURE)
IDS_CATALOGUE = set(CATALOGUE["id"])


# ============================================================
# FICHIERS : catalogue, importés, fichier C
# ============================================================

def serie_par_cle(cle):
    """Clé de fichier (catalogue, « importe:<nom> », « fichier_C ») → série."""
    if cle == choix_fichier.CLE_FICHIER_C:
        return st.session_state[choix_fichier.CLE_FICHIER_C]
    if cle.startswith(choix_fichier.PREFIXE_IMPORTE):
        return choix_fichier.importes()[cle[len(choix_fichier.PREFIXE_IMPORTE):]]
    return _serie_enregistree(cle, SIGNATURE)


def _resume(cle):
    return _resume_enregistre(cle, SIGNATURE) if cle in IDS_CATALOGUE else _resumer(serie_par_cle(cle))


def _importer_fichier(contenu, nom, base):
    s = lire_fichier_importe(contenu, nom, base, int(valeur(HYP, "decalage_heure_ete")), int(valeur(HYP, "trou_max_heures")))
    s.meta.setdefault("famille", FAMILLE_IMPORTES)
    return s


SOURCES = choix_fichier.Sources(catalogue=CATALOGUE, charger=serie_par_cle, resume=_resume, importer=_importer_fichier)

# --- Mémoire du navigateur : ce qu'on accepte de relire ---
VALIDATEURS_MEMOIRE = {
    choix_fichier.CLE_COURANT: lambda c: c if c in IDS_CATALOGUE else None,
    choix_fichier.CLE_RECENTS: memoire.liste_valide(lambda c: c in IDS_CATALOGUE),   # les imports ne durent pas
    menu_reglages.CLE_LIGNES: memoire.liste_valide(lambda v: isinstance(v, (int, float))),
    menu_reglages.CLE_INDICATEURS: memoire.liste_valide(lambda i: i in INDICATEURS),
}


def _aller_methode():
    """Lien « Méthode & sources › » du bandeau des hypothèses et de l'accueil."""
    st.session_state["onglet"] = ONGLET_METHODE


# ============================================================
# PAGE
# ============================================================

def main():
    stockage = memoire.charger(VALIDATEURS_MEMOIRE)          # avant les widgets du menu
    serie_a = serie_par_cle(choix_fichier.cle_courante(SOURCES))
    choix_fichier.menu(SOURCES, serie_a, lambda: choix_fichier.ouvrir("analyser", SOURCES))
    reglage = menu_reglages.afficher(INDICATEURS, ORDRE_DEFAUT, HYP)
    # Onglet Comparer : le second fichier est chargé tôt pour afficher son nom dans le haut de page
    serie_b = serie_par_cle(choix_fichier.cle_seconde(SOURCES)) if st.session_state.get("onglet") == ONGLET_COMPARER \
        else None
    onglet = haut_de_page(serie_a, ONGLETS, "onglet", serie_b)   # en-tête, onglets, nom(s) du fichier : bloc fixe

    def analyser_serie(serie):
        return analyser(serie, reglage, HYP)

    def calculer(analyse):
        return calculer_indicateurs(analyse, reglage, HYP, reglage["indicateurs"])

    def analyser_et_calculer(serie):
        a = analyser_serie(serie)
        return a, calculer(a)

    # Seul l'onglet ouvert est calculé (l'accueil ne calcule rien)
    if onglet == ONGLET_ACCUEIL:
        onglet_accueil.afficher(_aller_methode)
        pied()
        memoire.enregistrer(stockage)
        return
    analyse_a = analyser_serie(serie_a)
    if onglet == ONGLET_ANALYSER:
        onglet_analyser.afficher(analyse_a, calculer(analyse_a), reglage, HYP, _aller_methode)
    elif onglet == ONGLET_COMPARER:
        serie_b = serie_b or serie_par_cle(choix_fichier.cle_seconde(SOURCES))
        onglet_comparer.afficher(analyse_a, calculer(analyse_a), serie_b, analyser_et_calculer, reglage, HYP,
                                 lambda: choix_fichier.ouvrir("comparer", SOURCES))
    elif onglet == ONGLET_CREER:
        onglet_creer.afficher(analyse_a, reglage, HYP, analyser_serie, calculer)
    elif onglet == ONGLET_EXPORTER:
        analyse_b, res_b = analyser_et_calculer(serie_par_cle(choix_fichier.cle_seconde(SOURCES)))
        onglet_exporter.afficher(FichierExport(serie_a.libelle, analyse_a, calculer(analyse_a)),
                                 FichierExport(analyse_b.serie.libelle, analyse_b, res_b), reglage, HYP,
                                 remplacer_reperes)
    else:
        onglet_methode.afficher(analyse_a, HYP)
    pied()
    memoire.enregistrer(stockage)


try:
    main()
except Exception as erreur:              # message clair en français (+ détail si METEO_DEBUG=1)
    erreurs.afficher(erreur)
