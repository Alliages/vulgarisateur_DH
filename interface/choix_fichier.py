"""
============================================================
 CHOIX DU FICHIER MÉTÉO (0.9.0)
============================================================
 - Menu de gauche : carte du fichier en cours, bouton « Changer de
   fichier », fichiers récents.
 - Fenêtre de choix (st.dialog) : recherche dans toutes les familles,
   familles en onglets, zones RE2020 sur une carte schématique
   (barre = DH du fichier canicule), fichiers en cartes avec 3
   chiffres clés, import d'un fichier.
 - La même fenêtre choisit le second fichier de l'onglet Comparer.

 Clé d'un fichier : id du catalogue · « importe:<nom> » (fichier
 importé pendant la session) · « fichier_C » (créé dans l'onglet Créer).

 Tuiles cliquables : chaque tuile est un conteneur à clé
 (classe CSS « st-key-… ») qui contient le dessin HTML et un bouton
 Streamlit transparent posé par-dessus (CSS dans composants.py).
============================================================
"""

import html
from dataclasses import dataclass
from typing import Callable

import pandas as pd
import streamlit as st

from config.reglages import (CARAMEL, CORAIL, COULEUR_FICHIER_1, COULEUR_FICHIER_2, FAMILLE_IMPORTES, FAMILLES,
                             FICHIER_DEFAUT, ONGLETS)
from interface.composants import melange
from interface.format_fr import nombre

# ============================================================
# PARAMÈTRES
# ============================================================
# --- Clés de l'état de session ---
CLE_COURANT = "fichier_courant"          # fichier de l'onglet Analyser
CLE_SECOND = "fichier_second"            # second fichier de l'onglet Comparer
CLE_RECENTS = "fichiers_recents"
CLE_IMPORTES = "importes"                # {nom : SerieMeteo} chargés pendant la session
CLE_FICHIER_C = "fichier_C"              # série créée dans l'onglet Créer
PREFIXE_IMPORTE = "importe:"
NB_RECENTS = 3

# --- Fenêtre de choix ---
FAMILLE_CARTE = "RE2020"                 # famille présentée par zones sur la carte schématique
SCENARIO_REFERENCE = "Th-D canicule"     # la barre de chaque zone = DH de ce fichier
DISPOSITION_ZONES = [["H2a", "H1a", "H1b"],      # nord-ouest · Paris · nord-est
                     ["H2b", "H1c", "H2d"],      # centre-ouest · centre-est · sud-est intérieur
                     ["H2c", None, "H3"]]        # sud-ouest · (légende) · Méditerranée
SEGMENT_IMPORTER = "+ Importer"
BASES_HORAIRES = ["légale", "UTC"]
COULEUR_ROLE = {"analyser": COULEUR_FICHIER_1, "comparer": COULEUR_FICHIER_2}
TEXTE_RECHERCHE = "Rechercher une zone, une station, un type de fichier… (ex. « Agen », « canicule », « relevé »)"
DESCRIPTION_IMPORTE = "fichier importé pendant la session"
DESCRIPTION_FICHIER_C = "semaine ou journée créée dans l'onglet Créer"

# --- Clés internes de la fenêtre ---
D_FAMILLE, D_ZONE, D_FICHIER, D_RECHERCHE = "dlg_famille", "dlg_zone", "dlg_fichier", "dlg_recherche"
D_FERMER, D_APRES_IMPORT = "dlg_fermer", "dlg_apres_import"


# ============================================================
# SOURCES DES FICHIERS (fournies par app.py)
# ============================================================

@dataclass
class Sources:
    catalogue: pd.DataFrame                          # config/catalogue_fichiers.csv
    charger: Callable[[str], object]                 # clé → SerieMeteo
    resume: Callable[[str], dict]                    # clé → {"dh", "nuits_20", "tmax"} (réglage RE2020)
    importer: Callable[[bytes, str, str], object]    # (contenu, nom, base horaire) → SerieMeteo


def importes() -> dict:
    return st.session_state.setdefault(CLE_IMPORTES, {})


def cles_disponibles(src: Sources) -> list:
    """Toutes les clés de fichiers : catalogue, importés, fichier C."""
    cles = list(src.catalogue["id"]) + [PREFIXE_IMPORTE + n for n in importes()]
    return cles + ([CLE_FICHIER_C] if CLE_FICHIER_C in st.session_state else [])


def _ligne(cle: str, src: Sources):
    lignes = src.catalogue[src.catalogue["id"] == cle]
    return None if lignes.empty else lignes.iloc[0]


def infos(cle: str, src: Sources) -> dict:
    """Nom, description, famille, zone et station d'un fichier (pour les cartes et la recherche)."""
    r = _ligne(cle, src)
    if r is not None:
        return {"nom": r["libelle"], "titre": f"{r['zone']} · {r['libelle']}", "desc": r["description"],
                "famille": r["famille"], "zone": r["zone"], "station": r["station"], "periode": r["periode"],
                "base": r["base_horaire"]}
    s = src.charger(cle)
    desc = DESCRIPTION_FICHIER_C if cle == CLE_FICHIER_C else DESCRIPTION_IMPORTE
    return {"nom": s.libelle, "titre": s.libelle, "desc": desc, "famille": FAMILLE_IMPORTES, "zone": "",
            "station": s.meta.get("station", ""), "periode": s.meta.get("periode", ""),
            "base": s.meta.get("base_horaire", "")}


def _texte_recherche(cle: str, src: Sources) -> str:
    i = infos(cle, src)
    return " ".join(str(v) for v in i.values()).lower()


# ============================================================
# FICHIER EN COURS, SECOND FICHIER, RÉCENTS
# ============================================================

def cle_courante(src: Sources) -> str:
    cle = st.session_state.setdefault(CLE_COURANT, FICHIER_DEFAUT)
    if cle not in cles_disponibles(src):                  # import perdu, fichier retiré du catalogue…
        cle = st.session_state[CLE_COURANT] = FICHIER_DEFAUT
    return cle


def second_par_defaut(cle_a: str, src: Sources) -> str:
    """Même scénario dans une autre zone (le dernier du catalogue), sinon le premier autre fichier."""
    cat = src.catalogue
    a = _ligne(cle_a, src)
    if a is not None:
        memes = cat[(cat["libelle"] == a["libelle"]) & (cat["id"] != cle_a)]
        if not memes.empty:
            return memes.iloc[-1]["id"]
    return next(c for c in cles_disponibles(src) if c != cle_a)


def cle_seconde(src: Sources) -> str:
    cle_a = cle_courante(src)
    cle = st.session_state.get(CLE_SECOND)
    if cle is None or cle == cle_a or cle not in cles_disponibles(src):
        cle = second_par_defaut(cle_a, src)
    return cle


def _ajouter_recent(cle: str):
    recents = [c for c in st.session_state.get(CLE_RECENTS, []) if c != cle]
    st.session_state[CLE_RECENTS] = [cle] + recents[:NB_RECENTS * 2]


def _choisir_recent(cle: str):
    """Clic sur un récent : il devient le fichier en cours ; l'ancien reste dans les récents."""
    ancien = st.session_state.get(CLE_COURANT)
    if ancien and ancien != cle:
        _ajouter_recent(ancien)
    st.session_state[CLE_COURANT] = cle
    _ajouter_recent(cle)


# ============================================================
# MENU DE GAUCHE
# ============================================================

def _etiquettes(serie, i: dict) -> str:
    morceaux = [(i["famille"], "famille"), (i["periode"], ""), (f"heure {i['base']}" if i["base"] else "", ""),
                (f"{nombre(len(serie.t), 0)} h", "")]
    return "".join(f'<span class="tag {c}">{html.escape(str(t))}</span>' for t, c in morceaux if t)


def menu(src: Sources, serie, ouvrir_choix: Callable[[], None]):
    """Carte du fichier en cours + bouton « Changer de fichier » + récents (barre latérale)."""
    cle = cle_courante(src)
    i = infos(cle, src)
    st.sidebar.markdown("### FICHIER MÉTÉO")
    with st.sidebar.container(key="fichier_actuel"):
        st.markdown(f'<div class="nom-actuel"><span class="point" style="background:{COULEUR_FICHIER_1}"></span>'
                    f'{html.escape(serie.libelle)}</div>'
                    f'<div class="meta-actuel">{html.escape(" · ".join(x for x in (i["station"], i["desc"]) if x))}</div>'
                    f'<div class="etiquettes">{_etiquettes(serie, i)}</div>', unsafe_allow_html=True)
        if st.button("⌕  Changer de fichier", key="ouvrir_choix", width="stretch"):
            ouvrir_choix()
    recents = [c for c in st.session_state.get(CLE_RECENTS, []) if c != cle and c in cles_disponibles(src)]
    if recents:
        with st.sidebar.container(key="recents"):
            st.markdown('<div class="lib-recents">Récents</div>', unsafe_allow_html=True)
            for n, c in enumerate(recents[:NB_RECENTS]):
                st.button(f":gray[●] {infos(c, src)['titre']}", key=f"recent_{n}", on_click=_choisir_recent, args=(c,))


# ============================================================
# FENÊTRE DE CHOIX
# ============================================================

def preparer(role: str, cle: str, src: Sources):
    """État initial de la fenêtre : famille, zone et fichier du fichier déjà choisi."""
    i = infos(cle, src)
    st.session_state[D_FAMILLE] = i["famille"] if i["famille"] in FAMILLES else FAMILLE_IMPORTES
    st.session_state[D_ZONE] = i["zone"] or _premiere_zone(src)
    st.session_state[D_FICHIER] = cle
    st.session_state[D_RECHERCHE] = ""


def _premiere_zone(src: Sources) -> str:
    return next(z for ligne in DISPOSITION_ZONES for z in ligne if z)


def _fichier_de_zone(zone: str, src: Sources) -> str | None:
    """Fichier proposé quand on choisit une zone : le scénario de référence, sinon le premier."""
    cat = src.catalogue
    lignes = cat[(cat["famille"] == FAMILLE_CARTE) & (cat["zone"] == zone)]
    if lignes.empty:
        return None
    ref = lignes[lignes["libelle"] == SCENARIO_REFERENCE]
    return (ref if not ref.empty else lignes).iloc[0]["id"]


def _choisir_zone(zone: str, src: Sources):
    st.session_state[D_ZONE] = zone
    st.session_state[D_FICHIER] = _fichier_de_zone(zone, src)


def _choisir_fichier(cle: str):
    st.session_state[D_FICHIER] = cle


def _valider(action: str, cle: str):
    """Bouton final : « analyser » (fichier de l'onglet 1) ou « comparer » (second fichier)."""
    if action == "analyser":
        ancien = st.session_state.get(CLE_COURANT)
        if ancien and ancien != cle:
            _ajouter_recent(ancien)
        st.session_state[CLE_COURANT] = cle
        _ajouter_recent(cle)
        st.session_state["onglet"] = ONGLETS[0]
    else:
        st.session_state[CLE_SECOND] = cle
        st.session_state["onglet"] = ONGLETS[1]
    st.session_state[D_FERMER] = True                      # fermeture au passage suivant (st.rerun)


def _fermer():
    st.session_state[D_FERMER] = True


def _degrade(part: float) -> str:
    """Couleur de la barre : caramel (moins chaud) → corail (plus chaud)."""
    a, b = CARAMEL.lstrip("#"), CORAIL.lstrip("#")
    ca = [int(a[k:k + 2], 16) for k in (0, 2, 4)]
    cb = [int(b[k:k + 2], 16) for k in (0, 2, 4)]
    return "#" + "".join(f"{round(x + (y - x) * part):02x}" for x, y in zip(ca, cb))


def _etape(numero: str, texte: str, petit: str = ""):
    st.markdown(f'<div class="etape"><span class="num">{numero}</span>{html.escape(texte)}'
                f'{f"<small>{html.escape(petit)}</small>" if petit else ""}</div>', unsafe_allow_html=True)


def _carte_zones(src: Sources, couleur: str):
    """Étape 1 : les zones RE2020 placées comme sur la carte de France, barre = DH du scénario de référence."""
    cat = src.catalogue
    ref = cat[(cat["famille"] == FAMILLE_CARTE) & (cat["libelle"] == SCENARIO_REFERENCE)]
    dh = {r.zone: src.resume(r.id)["dh"] or 0 for r in ref.itertuples()}
    stations = dict(zip(ref["zone"], ref["station"]))
    dh_max = max(dh.values(), default=1) or 1
    zone_choisie = st.session_state.get(D_ZONE)
    _etape("1", "Zone climatique", "placée comme sur la carte de France")
    for ligne in DISPOSITION_ZONES:
        for col, zone in zip(st.columns(3, gap="small"), ligne):
            with col:
                if zone is None:
                    st.markdown(f'<div class="legende-zones">Barre : DH du fichier « {SCENARIO_REFERENCE} » '
                                f'(réglage RE2020)<div class="degrade"></div><div class="bornes"><span>moins chaud'
                                f'</span><span>plus chaud</span></div></div>', unsafe_allow_html=True)
                    continue
                if zone not in dh:
                    continue
                part = dh[zone] / dh_max
                choisie = zone == zone_choisie
                with st.container(key=f"tuile_zone_{zone}", gap=None):
                    st.markdown(
                        f'<div class="tuile zone{" choisie" if choisie else ""}" style="--c:{couleur};'
                        f'--fond-choisi:{melange(couleur, 0.07)}"><div class="code">{zone}</div>'
                        f'<div class="station">{html.escape(stations.get(zone, ""))}</div>'
                        f'<div class="jauge"><div style="width:{100 * part:.0f}%;background:{_degrade(part)}"></div></div>'
                        f'<div class="chiffre">DH canicule <b>{nombre(dh[zone], 0)}</b></div></div>',
                        unsafe_allow_html=True)
                    st.button(f"Zone {zone}", key=f"b_zone_{zone}", on_click=_choisir_zone, args=(zone, src))


def _cartes_fichiers(cles: list, src: Sources, couleur: str, cle_en_cours: str, titre_long: bool,
                     nb_colonnes: int = 1):
    """Fichiers en cartes : nom, usage, 3 chiffres clés ; la carte choisie est encadrée de la couleur du rôle."""
    choisi = st.session_state.get(D_FICHIER)
    colonnes = st.columns(nb_colonnes, gap="small")
    for n, cle in enumerate(cles):
        i, r = infos(cle, src), src.resume(cle)
        badges = ("".join([f'<span class="badge defaut">par défaut</span>' if cle == FICHIER_DEFAUT else "",
                           f'<span class="badge encours">en cours</span>' if cle == cle_en_cours else ""]))
        chiffres = (f'<div><b class="rouge">{"—" if r["dh"] is None else nombre(r["dh"], 0)}</b>DH (°C.h)</div>'
                    f'<div><b class="nuit">{"—" if r["nuits_20"] is None else nombre(r["nuits_20"], 0)}</b>'
                    f'nuits ≥ 20 °C</div><div><b>{nombre(r["tmax"], 1)} °C</b>T max</div>')
        precision = " · ".join(x for x in (i["station"] if titre_long else "", i["periode"],
                                           f"heure {i['base']}" if i["base"] else "") if x)
        with colonnes[n % nb_colonnes], st.container(key=f"tuile_fichier_{n}", gap=None):
            st.markdown(
                f'<div class="tuile fichier{" choisie" if cle == choisi else ""}" style="--c:{couleur};'
                f'--fond-choisi:{melange(couleur, 0.07)}"><div class="haut"><span class="point" '
                f'style="background:{couleur if cle == choisi else "#B9B7B0"}"></span>'
                f'<span class="nom">{html.escape(i["titre"] if titre_long else i["nom"])}</span>{badges}</div>'
                f'<div class="desc">{html.escape(" · ".join(x for x in (i["desc"], precision) if x))}</div>'
                f'<div class="chiffres">{chiffres}</div></div>', unsafe_allow_html=True)
            st.button(f"Choisir {i['titre']}", key=f"b_fichier_{n}", on_click=_choisir_fichier, args=(cle,))


def _importer(src: Sources):
    """Import d'un CSV horaire : il rejoint la famille « Importés » et devient le fichier choisi."""
    _etape("+", "Importer un fichier CSV horaire", "colonnes heure;T ou date;heure;T · gardé pendant la session")
    fichier = st.file_uploader("Fichier", type=["csv", "txt"], label_visibility="collapsed", key="dlg_fichier_import")
    base = st.radio("Base horaire du fichier", BASES_HORAIRES, horizontal=True, key="dlg_base_import")
    if fichier is not None and st.button("Charger ce fichier", type="primary", key="dlg_charger"):
        try:
            s = src.importer(fichier.getvalue(), fichier.name, base)
        except ValueError as e:
            st.error(str(e))
            return
        importes()[s.libelle] = s
        st.session_state[D_APRES_IMPORT] = PREFIXE_IMPORTE + s.libelle
        st.rerun(scope="fragment")


def _libelle_famille(f: str, src: Sources) -> str:
    if f == SEGMENT_IMPORTER:
        return f
    n = len(importes()) + (CLE_FICHIER_C in st.session_state) if f == FAMILLE_IMPORTES \
        else int((src.catalogue["famille"] == f).sum())
    return f"{f} · {n}" if n else f"{f} · bientôt" if f != FAMILLE_IMPORTES else f"{f} · 0"


def _contenu(src: Sources, role: str):
    """Corps commun des deux fenêtres (« analyser » ou « comparer »)."""
    if st.session_state.pop(D_FERMER, False):
        st.rerun()                                         # passage complet : ferme la fenêtre
    if D_APRES_IMPORT in st.session_state:                 # après un import : montrer le fichier importé
        st.session_state[D_FAMILLE] = FAMILLE_IMPORTES
        st.session_state[D_FICHIER] = st.session_state.pop(D_APRES_IMPORT)
    couleur = COULEUR_ROLE[role]
    cle_en_cours = cle_courante(src) if role == "analyser" else cle_seconde(src)

    recherche = st.text_input("Rechercher", key=D_RECHERCHE, placeholder=TEXTE_RECHERCHE,
                              label_visibility="collapsed").strip().lower()
    if recherche:
        trouves = [c for c in cles_disponibles(src) if recherche in _texte_recherche(c, src)]
        _etape("⌕", f"{len(trouves)} fichier{'s' if len(trouves) > 1 else ''} trouvé{'s' if len(trouves) > 1 else ''}",
               "toutes familles")
        if trouves:
            _cartes_fichiers(trouves, src, couleur, cle_en_cours, titre_long=True, nb_colonnes=2)
        else:
            st.info("Aucun fichier ne correspond.")
    else:
        options = FAMILLES + [FAMILLE_IMPORTES, SEGMENT_IMPORTER]
        famille = st.segmented_control("Famille", options, key=D_FAMILLE, label_visibility="collapsed", required=True,
                                       format_func=lambda f: _libelle_famille(f, src)) or FAMILLE_CARTE
        if famille == SEGMENT_IMPORTER:
            _importer(src)
        elif famille == FAMILLE_CARTE:
            col_zones, col_fichiers = st.columns([1.15, 1], gap="medium")
            with col_zones:
                _carte_zones(src, couleur)
            with col_fichiers:
                zone = st.session_state.get(D_ZONE)
                cat = src.catalogue
                lignes = cat[(cat["famille"] == FAMILLE_CARTE) & (cat["zone"] == zone)]
                station = lignes["station"].iloc[0] if not lignes.empty else ""
                _etape("2", f"Fichier de la zone {zone}", station)
                _cartes_fichiers(list(lignes["id"]), src, couleur, cle_en_cours, titre_long=False)
        else:
            cles = [c for c in cles_disponibles(src) if infos(c, src)["famille"] == famille]
            if not cles:
                st.info(f"Pas encore de fichier « {famille} » : ils seront ajoutés quand la source et le format "
                        f"seront connus." if famille != FAMILLE_IMPORTES else
                        "Aucun fichier importé pendant cette session : onglet « + Importer ».")
            else:
                _etape("✓", f"Fichiers « {famille} »")
                _cartes_fichiers(cles, src, couleur, cle_en_cours, titre_long=True, nb_colonnes=2)
    _pied(src, role)


def _pied(src: Sources, role: str):
    choisi = st.session_state.get(D_FICHIER)
    nom = infos(choisi, src)["titre"] if choisi in cles_disponibles(src) else None
    st.markdown(f'<div class="pied-fenetre">{"Choisi : <b>" + html.escape(nom) + "</b>" if nom else "Aucun fichier choisi"}'
                f' · la recherche cherche dans toutes les familles</div>', unsafe_allow_html=True)
    with st.container(key="boutons_fenetre", horizontal=True, horizontal_alignment="right"):
        st.button("Annuler", key="dlg_annuler", type="tertiary", on_click=_fermer)
        if role == "analyser":
            st.button("Comparer avec le fichier en cours", key="dlg_comparer", on_click=_valider,
                      args=("comparer", choisi), disabled=nom is None or choisi == cle_courante(src))
            st.button("Analyser ce fichier", key="dlg_analyser", type="primary", on_click=_valider,
                      args=("analyser", choisi), disabled=nom is None)
        else:
            st.button("Comparer ce fichier", key="dlg_comparer_second", type="primary", on_click=_valider,
                      args=("comparer", choisi), disabled=nom is None or choisi == cle_courante(src))


@st.dialog("Choisir un fichier météo", width="large")
def fenetre_analyser(src: Sources):
    _contenu(src, "analyser")


@st.dialog("Choisir le second fichier (onglet Comparer)", width="large")
def fenetre_comparer(src: Sources):
    _contenu(src, "comparer")


def ouvrir(role: str, src: Sources):
    """Ouvre la fenêtre de choix, positionnée sur le fichier déjà choisi pour ce rôle."""
    preparer(role, cle_courante(src) if role == "analyser" else cle_seconde(src), src)
    (fenetre_analyser if role == "analyser" else fenetre_comparer)(src)
