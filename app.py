"""
============================================================
 MÉTÉO ET CHALEUR — point d'entrée Streamlit
============================================================
 Lancement local :  streamlit run app.py
 Onglets : ① Analyser · ② Comparer · ③ Créer · ④ Exporter · Méthode & sources
 Seul l'onglet ouvert est calculé (navigation dans le bloc fixe du haut).
 Réglage par défaut : RE2020 (config/reglages.py).
============================================================
"""

import numpy as np
import streamlit as st

from calcul.hypotheses import charger_hypotheses, charger_indicateurs, remplacer_reperes, valeur
from calcul.indicateurs import analyser, calculer_indicateurs
from calcul.serie import charger_catalogue, charger_serie, lire_fichier_importe
from config.reglages import (FAMILLE_IMPORTES, LIBELLE_SEUILS_DH, LIBELLES_CRITERE_JOURNEE, LIBELLES_CRITERE_SEMAINE,
                             LIBELLES_METHODE, ONGLET_ANALYSER, ONGLET_COMPARER, ONGLET_CREER, ONGLET_EXPORTER,
                             ONGLET_METHODE, ONGLETS, REGLAGE_RE2020)
from export.export import FichierExport
from interface import (choix_fichier, erreurs, memoire, onglet_analyser, onglet_comparer, onglet_creer, onglet_exporter,
                       onglet_methode)
from interface.composants import haut_de_page, pied

# ============================================================
# PARAMÈTRES
# ============================================================
TITRE_PAGE = "Météo et Chaleur"
CLES_REGLAGE = {"methode": "r_methode", "occupation": "r_occupation",           # clés des boutons du menu
                "critere_journee": "r_journee", "critere_semaine": "r_semaine"}
CLE_REGLAGE_COURANT = "reglage_courant"  # réglage de référence, gardé à part des boutons (voir _reglage_courant)
CLE_GENERATION_BOUTONS = "generation_boutons"   # change à chaque retour au réglage RE2020
CLE_INDICATEURS = "r_indicateurs"        # ordre des cartes choisi dans le menu
INDICATEURS_RESUME = ["dh", "nuits_20"]  # chiffres clés des cartes de la fenêtre de choix (+ T max)

st.set_page_config(page_title=TITRE_PAGE, page_icon="☀", layout="wide")
erreurs.filtrer_bruit_windows()          # console PowerShell : masque « ConnectionResetError [WinError 10054] »


# ============================================================
# DONNÉES EN CACHE
# ============================================================

@st.cache_data
def _hypotheses():
    return charger_hypotheses(), charger_indicateurs(tous=True)


@st.cache_data
def _catalogue():
    return charger_catalogue()


@st.cache_resource
def _serie_enregistree(identifiant):
    hyp, _ = _hypotheses()
    ligne = _catalogue().set_index("id").loc[identifiant].to_dict()
    ligne["id"] = identifiant
    return charger_serie(ligne, int(valeur(hyp, "decalage_heure_ete")))


def _resumer(serie) -> dict:
    """DH (réglage RE2020), nuits ≥ 20 °C et T max d'une série : chiffres clés de la fenêtre de choix."""
    _, tous = _hypotheses()
    a = analyser(serie, REGLAGE_RE2020, HYP)
    defs = [d for d in tous if d["id"] in INDICATEURS_RESUME]
    v = {d["id"]: r.valeur for d, r in calculer_indicateurs(a, REGLAGE_RE2020, HYP, defs)}
    return {"dh": v.get("dh"), "nuits_20": v.get("nuits_20"), "tmax": float(np.max(serie.t))}


@st.cache_data(show_spinner="Calcul des chiffres clés du fichier…")
def _resume_enregistre(identifiant):
    return _resumer(_serie_enregistree(identifiant))


HYP, TOUS_INDICATEURS = _hypotheses()
INDICATEURS = {d["id"]: d for d in TOUS_INDICATEURS}
ORDRE_DEFAUT = [d["id"] for d in TOUS_INDICATEURS if d["actif"]]     # ordre de hypotheses.xlsx
CATALOGUE = _catalogue()


# ============================================================
# RÉGLAGES (barre latérale)
# ============================================================

def _reglage_courant() -> dict:
    """
    Réglage de référence (méthode, occupation, critères), gardé À PART des boutons du menu.
    Raison : au premier chargement, la mémoire du navigateur relance la page pendant le calcul ; Streamlit
    pouvait alors perdre l'état d'un bouton de la partie repliée (l'occupation repassait à « 24h/24 »).
    Les calculs lisent ce réglage ; il ne change que quand l'utilisateur clique sur un bouton (_copier_bouton).
    """
    return st.session_state.setdefault(CLE_REGLAGE_COURANT, {k: REGLAGE_RE2020[k] for k in CLES_REGLAGE})


def _cle_bouton(cle) -> str:
    """Clé du bouton du menu ; elle change à chaque « Revenir au réglage RE2020 » (boutons recréés, affichage juste)."""
    return f"{CLES_REGLAGE[cle]}_{st.session_state.setdefault(CLE_GENERATION_BOUTONS, 0)}"


def _copier_bouton(cle):
    """Clic sur un bouton du menu : sa valeur devient le réglage de référence."""
    _reglage_courant()[cle] = st.session_state[_cle_bouton(cle)]


def _reinitialiser():
    st.session_state[CLE_REGLAGE_COURANT] = {k: REGLAGE_RE2020[k] for k in CLES_REGLAGE}
    st.session_state[CLE_GENERATION_BOUTONS] = st.session_state.get(CLE_GENERATION_BOUTONS, 0) + 1
    st.session_state["lignes"] = list(REGLAGE_RE2020["lignes"])
    st.session_state[CLE_INDICATEURS] = list(ORDRE_DEFAUT)


def _aller_methode():
    """Lien « Méthode & sources › » du bandeau des hypothèses."""
    st.session_state["onglet"] = ONGLET_METHODE


def _mettre_en_tete():
    """Bouton ↑ : l'indicateur choisi passe en première carte."""
    choisi = st.session_state.get("indicateur_tete")
    if choisi:
        st.session_state[CLE_INDICATEURS] = [choisi] + [i for i in st.session_state[CLE_INDICATEURS] if i != choisi]
        st.session_state["indicateur_tete"] = None


def _libelle_indicateur(identifiant):
    return remplacer_reperes(INDICATEURS[identifiant]["libelle"], HYP)


def serie_par_cle(cle):
    """Clé de fichier (catalogue, « importe:<nom> », « fichier_C ») → série."""
    if cle == choix_fichier.CLE_FICHIER_C:
        return st.session_state[choix_fichier.CLE_FICHIER_C]
    if cle.startswith(choix_fichier.PREFIXE_IMPORTE):
        return choix_fichier.importes()[cle[len(choix_fichier.PREFIXE_IMPORTE):]]
    return _serie_enregistree(cle)


def _resume(cle):
    ids = set(CATALOGUE["id"])
    return _resume_enregistre(cle) if cle in ids else _resumer(serie_par_cle(cle))


def _importer_fichier(contenu, nom, base):
    s = lire_fichier_importe(contenu, nom, base, int(valeur(HYP, "decalage_heure_ete")), int(valeur(HYP, "trou_max_heures")))
    s.meta.setdefault("famille", FAMILLE_IMPORTES)
    return s


SOURCES = choix_fichier.Sources(catalogue=CATALOGUE, charger=serie_par_cle, resume=_resume, importer=_importer_fichier)


def _choisir_indicateurs():
    """Indicateurs affichés et leur ordre (l'ordre de la liste = l'ordre des cartes)."""
    st.session_state.setdefault(CLE_INDICATEURS, list(ORDRE_DEFAUT))
    st.markdown('<div class="sous-titre-menu">INDICATEURS AFFICHÉS (ORDRE DES CARTES)</div>', unsafe_allow_html=True)
    choisis = st.multiselect("Indicateurs", list(INDICATEURS), key=CLE_INDICATEURS,
                             format_func=_libelle_indicateur, label_visibility="collapsed")
    col1, col2 = st.columns([4, 1], vertical_alignment="bottom")
    col1.selectbox("Placer en tête", choisis, index=None, placeholder="Placer en tête…", key="indicateur_tete",
                   format_func=_libelle_indicateur, label_visibility="collapsed")
    col2.button("↑", on_click=_mettre_en_tete, help="Mettre l'indicateur choisi en première carte")
    st.caption("L'ordre de la liste est l'ordre des cartes. Un indicateur retiré puis remis passe en dernier.")
    return [INDICATEURS[i] for i in (choisis or ORDRE_DEFAUT)]


def barre_laterale():
    """Fichier météo (toujours visible) puis réglages, repliés par défaut."""
    serie = serie_par_cle(choix_fichier.cle_courante(SOURCES))
    choix_fichier.menu(SOURCES, serie, lambda: choix_fichier.ouvrir("analyser", SOURCES))

    courant = _reglage_courant()
    st.session_state.setdefault("lignes", list(REGLAGE_RE2020["lignes"]))
    with st.sidebar.expander("RÉGLAGES", expanded=False, key="reglages"):
        methodes, journees, semaines = list(LIBELLES_METHODE), list(LIBELLES_CRITERE_JOURNEE), list(LIBELLES_CRITERE_SEMAINE)
        st.radio(LIBELLE_SEUILS_DH, methodes, index=methodes.index(courant["methode"]), format_func=LIBELLES_METHODE.get,
                 horizontal=True, key=_cle_bouton("methode"), on_change=_copier_bouton, args=("methode",))
        st.toggle("DH en occupation (logement)", value=courant["occupation"], key=_cle_bouton("occupation"),
                  on_change=_copier_bouton, args=("occupation",))
        st.radio("Journée la + chaude selon", journees, index=journees.index(courant["critere_journee"]),
                 format_func=LIBELLES_CRITERE_JOURNEE.get, horizontal=True, key=_cle_bouton("critere_journee"),
                 on_change=_copier_bouton, args=("critere_journee",))
        st.radio("Semaine la + chaude selon", semaines, index=semaines.index(courant["critere_semaine"]),
                 format_func=LIBELLES_CRITERE_SEMAINE.get, key=_cle_bouton("critere_semaine"),
                 on_change=_copier_bouton, args=("critere_semaine",))
        reglage = dict(courant)                     # les calculs lisent le réglage de référence
        lignes = st.multiselect("Lignes horizontales (°C)", st.session_state["lignes"],
                                default=st.session_state["lignes"], format_func=lambda v: f"{v:g} °C")
        col1, col2 = st.columns([3, 2])
        nouvelle = col1.number_input("Nouvelle ligne", value=35.0, step=1.0, format="%.0f",
                                     label_visibility="collapsed")
        if col2.button("+ ligne"):
            lignes = sorted(set(lignes) | {float(nouvelle)})
        st.session_state["lignes"] = lignes
        reglage["lignes"] = lignes
        reglage["indicateurs"] = _choisir_indicateurs()
        st.button("↺ Revenir au réglage RE2020", on_click=_reinitialiser)
    return serie, reglage


# ============================================================
# MÉMOIRE DU NAVIGATEUR : ce qu'on accepte de relire
# ============================================================
VALIDATEURS_MEMOIRE = {
    "fichier_courant": lambda c: c if c in set(CATALOGUE["id"]) else None,
    "fichiers_recents": memoire.liste_valide(lambda c: c in set(CATALOGUE["id"])),   # les imports ne durent pas
    "lignes": memoire.liste_valide(lambda v: isinstance(v, (int, float))),
    CLE_INDICATEURS: memoire.liste_valide(lambda i: i in INDICATEURS),
}


# ============================================================
# PAGE
# ============================================================

def main():
    stockage = memoire.charger(VALIDATEURS_MEMOIRE)          # avant les widgets du menu
    serie_a, reglage = barre_laterale()
    onglet = haut_de_page(serie_a, ONGLETS, "onglet")       # en-tête, onglets, nom du fichier : bloc fixe

    def analyser_serie(serie):
        return analyser(serie, reglage, HYP)

    def calculer(analyse):
        return calculer_indicateurs(analyse, reglage, HYP, reglage["indicateurs"])

    def analyser_et_calculer(serie):
        a = analyser_serie(serie)
        return a, calculer(a)

    analyse_a = analyser_serie(serie_a)
    # Seul l'onglet ouvert est calculé
    if onglet == ONGLET_ANALYSER:
        onglet_analyser.afficher(analyse_a, calculer(analyse_a), reglage, HYP, _aller_methode)
    elif onglet == ONGLET_COMPARER:
        serie_b = serie_par_cle(choix_fichier.cle_seconde(SOURCES))
        onglet_comparer.afficher(analyse_a, calculer(analyse_a), serie_b, analyser_et_calculer, reglage, HYP,
                                 lambda: choix_fichier.ouvrir("comparer", SOURCES))
    elif onglet == ONGLET_CREER:
        onglet_creer.afficher(analyse_a, reglage, HYP, reglage["indicateurs"], analyser_serie, calculer)
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
except Exception as erreur:              # message clair en français + détail copiable (version de test)
    erreurs.afficher(erreur)
