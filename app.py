"""
============================================================
 MÉTÉO ET CHALEUR — point d'entrée Streamlit
============================================================
 Lancement local :  streamlit run app.py
 Onglets : ① Analyser · ② Comparer · ③ Créer · Méthode & sources
 Réglage par défaut : RE2020 (config/reglages.py).
============================================================
"""

from functools import partial

import streamlit as st

from calcul.hypotheses import charger_hypotheses, charger_indicateurs, remplacer_reperes, valeur
from calcul.indicateurs import analyser, calculer_indicateurs
from calcul.serie import charger_catalogue, charger_serie, lire_fichier_importe
from config.reglages import (FAMILLE_IMPORTES, FAMILLES, FICHIER_DEFAUT, LIBELLE_SEUILS_DH, LIBELLES_CRITERE_JOURNEE,
                             LIBELLES_CRITERE_SEMAINE, LIBELLES_METHODE, REGLAGE_RE2020, VERSION)
from export.export import csv_horaire, excel_complet
from interface import onglet_analyser, onglet_comparer, onglet_creer, onglet_methode
from interface.composants import entete, pied

# ============================================================
# PARAMÈTRES
# ============================================================
TITRE_PAGE = "Météo et Chaleur"
ONGLETS = ["①  Analyser", "②  Comparer", "③  Créer jour / semaine", "Méthode & sources"]
CLES_REGLAGE = {"methode": "r_methode", "occupation": "r_occupation",
                "critere_journee": "r_journee", "critere_semaine": "r_semaine"}
CLE_INDICATEURS = "r_indicateurs"        # ordre des cartes choisi dans le menu
BASES_HORAIRES = ["légale", "UTC"]
MESSAGE_FAMILLE_VIDE = ("Pas encore de fichier {famille} dans le catalogue : ils seront ajoutés quand la source et "
                        "le format seront connus. Fichier affiché : celui par défaut.")

st.set_page_config(page_title=TITRE_PAGE, page_icon="☀", layout="wide")


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


HYP, TOUS_INDICATEURS = _hypotheses()
INDICATEURS = {d["id"]: d for d in TOUS_INDICATEURS}
ORDRE_DEFAUT = [d["id"] for d in TOUS_INDICATEURS if d["actif"]]     # ordre de hypotheses.xlsx
CATALOGUE = _catalogue()


# ============================================================
# RÉGLAGES (barre latérale)
# ============================================================

def _reinitialiser():
    for cle, cle_widget in CLES_REGLAGE.items():
        st.session_state[cle_widget] = REGLAGE_RE2020[cle]
    st.session_state["lignes"] = list(REGLAGE_RE2020["lignes"])
    st.session_state[CLE_INDICATEURS] = list(ORDRE_DEFAUT)


def _aller_methode():
    """Lien « Méthode & sources › » du bandeau des hypothèses."""
    st.session_state["onglet"] = ONGLETS[3]


def _mettre_en_tete():
    """Bouton ↑ : l'indicateur choisi passe en première carte."""
    choisi = st.session_state.get("indicateur_tete")
    if choisi:
        st.session_state[CLE_INDICATEURS] = [choisi] + [i for i in st.session_state[CLE_INDICATEURS] if i != choisi]
        st.session_state["indicateur_tete"] = None


def _libelle_indicateur(identifiant):
    return remplacer_reperes(INDICATEURS[identifiant]["libelle"], HYP)


def _choisir_fichier():
    """Famille → zone → fichier (ou recherche libre). Renvoie la série du fichier de l'onglet Analyser."""
    st.sidebar.markdown("### FICHIERS MÉTÉO")
    recherche = st.sidebar.text_input("Rechercher", placeholder="zone, station, type…", label_visibility="collapsed")
    importes = st.session_state.setdefault("importes", {})

    if recherche:                                  # recherche : résultats toutes familles confondues
        texte = recherche.lower()
        trouves = CATALOGUE[CATALOGUE.apply(lambda r: texte in " ".join(map(str, r.values)).lower(), axis=1)]
        options = {f"{r.famille} · {r.zone} · {r.libelle}": partial(_serie_enregistree, r.id) for r in trouves.itertuples()}
        options.update({f"{FAMILLE_IMPORTES} · {nom}": (lambda s=s: s) for nom, s in importes.items()
                        if texte in nom.lower()})
        if options:
            return options[st.sidebar.radio("Résultats", list(options), label_visibility="collapsed")]()
        st.sidebar.warning("Aucun fichier ne correspond.")

    familles = list(FAMILLES) + ([FAMILLE_IMPORTES] if importes else [])
    nb = {f: int((CATALOGUE["famille"] == f).sum()) for f in FAMILLES} | {FAMILLE_IMPORTES: len(importes)}
    famille_defaut = CATALOGUE.set_index("id").loc[FICHIER_DEFAUT, "famille"]
    famille = st.sidebar.radio("Famille", familles, index=familles.index(famille_defaut), horizontal=True,
                               key="famille_a", format_func=lambda f: f"{f} ({nb[f]})" if nb[f] else f"{f} (bientôt)")
    if famille == FAMILLE_IMPORTES:
        nom = st.sidebar.radio("Fichier", list(importes), label_visibility="collapsed", key="fichier_importe")
        return importes[nom]
    lignes = CATALOGUE[CATALOGUE["famille"] == famille]
    if lignes.empty:
        st.sidebar.info(MESSAGE_FAMILLE_VIDE.format(famille=famille))
        return _serie_enregistree(FICHIER_DEFAUT)
    zones = list(dict.fromkeys(lignes["zone"]))
    zone_defaut = CATALOGUE.set_index("id").loc[FICHIER_DEFAUT, "zone"]
    zone = st.sidebar.selectbox("Zone", zones, index=zones.index(zone_defaut) if zone_defaut in zones else 0,
                                key=f"zone_{famille}")
    lignes = lignes[lignes["zone"] == zone]
    ids = list(lignes["id"])
    choix = st.sidebar.radio("Fichier", ids, format_func=lambda i: lignes.set_index("id").loc[i, "libelle"],
                             captions=list(lignes["description"]), label_visibility="collapsed",
                             index=ids.index(FICHIER_DEFAUT) if FICHIER_DEFAUT in ids else 0,
                             key=f"fichier_{famille}_{zone}")
    return _serie_enregistree(choix)


def _importer():
    importes = st.session_state.setdefault("importes", {})
    with st.sidebar.expander("+ Importer un fichier (session)"):
        fichier = st.file_uploader("CSV horaire (heure;T ou date;heure;T)", type=["csv", "txt"])
        base = st.radio("Base horaire du fichier", BASES_HORAIRES, horizontal=True)
        if fichier is not None and st.button("Charger"):
            try:
                s = lire_fichier_importe(fichier.getvalue(), fichier.name, base, int(valeur(HYP, "decalage_heure_ete")),
                                         int(valeur(HYP, "trou_max_heures")))
                s.meta.setdefault("famille", FAMILLE_IMPORTES)
                importes[s.libelle] = s
                st.success(f"{s.libelle} chargé ({len(s.t)} h) : famille « {FAMILLE_IMPORTES} ».")
            except ValueError as e:
                st.error(str(e))
        st.caption("Proposer à l'enregistrement : bientôt.")


def _choisir_indicateurs():
    """Indicateurs affichés et leur ordre (l'ordre de la liste = l'ordre des cartes)."""
    st.session_state.setdefault(CLE_INDICATEURS, list(ORDRE_DEFAUT))
    with st.sidebar.expander("Indicateurs affichés (ordre des cartes)"):
        choisis = st.multiselect("Indicateurs", list(INDICATEURS), key=CLE_INDICATEURS,
                                 format_func=_libelle_indicateur, label_visibility="collapsed")
        col1, col2 = st.columns([4, 1], vertical_alignment="bottom")
        col1.selectbox("Placer en tête", choisis, index=None, placeholder="Placer en tête…", key="indicateur_tete",
                       format_func=_libelle_indicateur, label_visibility="collapsed")
        col2.button("↑", on_click=_mettre_en_tete, help="Mettre l'indicateur choisi en première carte")
        st.caption("L'ordre de la liste est l'ordre des cartes. Un indicateur retiré puis remis passe en dernier.")
    return [INDICATEURS[i] for i in (choisis or ORDRE_DEFAUT)]


def barre_laterale():
    serie = _choisir_fichier()
    _importer()

    st.sidebar.markdown("### RÉGLAGES")
    for cle, cle_widget in CLES_REGLAGE.items():
        st.session_state.setdefault(cle_widget, REGLAGE_RE2020[cle])
    st.session_state.setdefault("lignes", list(REGLAGE_RE2020["lignes"]))
    reglage = {
        "methode": st.sidebar.radio(LIBELLE_SEUILS_DH, list(LIBELLES_METHODE), format_func=LIBELLES_METHODE.get,
                                    horizontal=True, key="r_methode"),
        "occupation": st.sidebar.toggle("DH en occupation (logement)", key="r_occupation"),
        "critere_journee": st.sidebar.radio("Journée la + chaude selon", list(LIBELLES_CRITERE_JOURNEE),
                                            format_func=LIBELLES_CRITERE_JOURNEE.get, horizontal=True, key="r_journee"),
        "critere_semaine": st.sidebar.radio("Semaine la + chaude selon", list(LIBELLES_CRITERE_SEMAINE),
                                            format_func=LIBELLES_CRITERE_SEMAINE.get, key="r_semaine"),
    }
    lignes = st.sidebar.multiselect("Lignes horizontales (°C)", st.session_state["lignes"],
                                    default=st.session_state["lignes"], format_func=lambda v: f"{v:g} °C")
    col1, col2 = st.sidebar.columns([3, 2])
    nouvelle = col1.number_input("Nouvelle ligne", value=35.0, step=1.0, format="%.0f", label_visibility="collapsed")
    if col2.button("+ ligne"):
        lignes = sorted(set(lignes) | {float(nouvelle)})
    st.session_state["lignes"] = lignes
    reglage["lignes"] = lignes
    reglage["indicateurs"] = _choisir_indicateurs()
    st.sidebar.button("↺ Revenir au réglage RE2020", on_click=_reinitialiser)
    return serie, reglage


def _choix_second_fichier(serie_a):
    """Fichiers proposés pour la comparaison : {famille, libelle, charger} (chargement à la demande)."""
    choix = []
    if "fichier_C" in st.session_state:
        c = st.session_state["fichier_C"]
        choix.append({"famille": FAMILLE_IMPORTES, "libelle": c.libelle, "charger": (lambda s=c: s)})
    for nom, s in st.session_state.get("importes", {}).items():
        if s is not serie_a:
            choix.append({"famille": FAMILLE_IMPORTES, "libelle": nom, "charger": (lambda s=s: s)})
    for r in CATALOGUE.itertuples():
        if r.id != serie_a.id:
            choix.append({"famille": r.famille, "libelle": f"{r.zone} · {r.libelle}",
                          "charger": partial(_serie_enregistree, r.id)})
    return choix


# ============================================================
# PAGE
# ============================================================

def main():
    entete()
    serie_a, reglage = barre_laterale()

    def analyser_serie(serie):
        return analyser(serie, reglage, HYP)

    def calculer(analyse):
        return calculer_indicateurs(analyse, reglage, HYP, reglage["indicateurs"])

    analyse_a = analyser_serie(serie_a)
    res_a = calculer(analyse_a)

    with st.sidebar.expander("⤓ Exporter (CSV · Excel)"):
        st.download_button("Série horaire (CSV)", csv_horaire(analyse_a), f"{serie_a.id}_horaire.csv", "text/csv")
        st.download_button("Classeur complet (Excel)", excel_complet(analyse_a, res_a, HYP, reglage, remplacer_reperes),
                           f"{serie_a.id}_meteo_et_chaleur_v{VERSION}.xlsx")

    onglets = st.tabs(ONGLETS, key="onglet", on_change="rerun")
    with onglets[0]:
        onglet_analyser.afficher(analyse_a, res_a, reglage, HYP, _aller_methode)
    with onglets[1]:
        onglet_comparer.afficher(analyse_a, res_a, _choix_second_fichier(serie_a),
                                 lambda s: (lambda a: (a, calculer(a)))(analyser_serie(s)), reglage, HYP)
    with onglets[2]:
        onglet_creer.afficher(analyse_a, reglage, HYP, reglage["indicateurs"], analyser_serie, calculer)
    with onglets[3]:
        onglet_methode.afficher(analyse_a, HYP)
    pied()


main()
