"""
============================================================
 MÉMOIRE DU NAVIGATEUR (streamlit-extras local_storage_manager)
============================================================
 Garde d'une visite à l'autre, dans le navigateur de l'utilisateur :
 le dernier fichier ouvert, les fichiers récents, les lignes horizontales
 et l'ordre des cartes.
 - En début de page, `charger` recopie ces valeurs dans la session
   (une seule fois, quand le navigateur a répondu).
 - En fin de page, `enregistrer` écrit ce qui a changé (et relance la page
   une fois pour que l'écriture parte vers le navigateur).
 Tout est protégé : si le stockage est vide, bloqué ou indisponible
 (navigation privée, test sans navigateur), l'outil marche normalement.
============================================================
"""

import os
from typing import Callable

import streamlit as st

# ============================================================
# PARAMÈTRES
# ============================================================
CLE_COMPOSANT = "memoire_navigateur"
VARIABLE_SANS_MEMOIRE = "METEO_SANS_MEMOIRE"   # variable d'environnement : =1 désactive la mémoire
CLE_CHARGEE = "memoire_chargee"           # vrai quand le navigateur a été lu pour cette session
CLE_ENVOYE = "memoire_envoyee"            # dernières valeurs envoyées au navigateur (évite les relances en boucle)
CLE_ORDRE_CARTES = "r_indicateurs"        # ordre des cartes choisi dans le menu
CLE_CARTES_CONNUES = "cartes_connues"     # indicateurs proposés lors de la dernière visite
# clé de session → nom dans le navigateur
A_GARDER = {"fichier_courant": "fichier", "fichiers_recents": "recents", "lignes": "lignes",
            CLE_ORDRE_CARTES: "ordre_cartes", CLE_CARTES_CONNUES: CLE_CARTES_CONNUES}


def _gestionnaire():
    if os.environ.get(VARIABLE_SANS_MEMOIRE) == "1":       # pour les tests : pas de mémoire du navigateur
        return None
    try:
        from streamlit_extras.local_storage_manager import local_storage_manager
        return local_storage_manager(key=CLE_COMPOSANT)
    except Exception:                       # bibliothèque absente, composant indisponible…
        return None


def _ajouter_nouvelles_cartes(memoire, ordre_defaut: list):
    """
    Un indicateur apparu depuis la dernière visite s'ajoute à la fin de l'ordre gardé dans le navigateur ;
    un indicateur que l'utilisateur a retiré reste retiré. Mémoire d'avant cette règle (sans liste des
    indicateurs connus) : tous les indicateurs par défaut absents de l'ordre gardé sont ajoutés, une fois.
    """
    ordre = st.session_state.get(CLE_ORDRE_CARTES)
    if ordre:
        connues = memoire[CLE_CARTES_CONNUES] if CLE_CARTES_CONNUES in memoire else ordre
        st.session_state[CLE_ORDRE_CARTES] = ordre + [i for i in ordre_defaut if i not in connues and i not in ordre]
    st.session_state[CLE_CARTES_CONNUES] = list(ordre_defaut)


def charger(valider: dict, ordre_defaut: list = ()) -> object:
    """
    À appeler avant les widgets. valider : {clé de session : fonction(valeur lue) → valeur propre ou None} ;
    ordre_defaut : indicateurs proposés par défaut. Renvoie le gestionnaire (à passer à `enregistrer`), ou None.
    """
    memoire = _gestionnaire()
    if memoire is None or st.session_state.get(CLE_CHARGEE):
        return memoire
    try:
        if not memoire.ready():             # le navigateur n'a pas encore répondu : au passage suivant
            return memoire
        for cle_session, cle_nav in A_GARDER.items():
            if cle_nav in memoire:
                propre = valider.get(cle_session, lambda v: v)(memoire[cle_nav])
                if propre:
                    st.session_state[cle_session] = propre
        _ajouter_nouvelles_cartes(memoire, ordre_defaut)
    except Exception:
        pass
    st.session_state[CLE_CHARGEE] = True
    return memoire


def enregistrer(memoire):
    """
    À appeler en fin de page : écrit dans le navigateur les valeurs qui ont changé.
    L'extra n'envoie une écriture au navigateur qu'au passage suivant de la page : on relance donc la page
    une fois après une écriture. Ce qui a déjà été envoyé est retenu (CLE_ENVOYE) pour éviter une boucle.
    """
    if memoire is None or not st.session_state.get(CLE_CHARGEE):
        return                              # ne pas écraser la mémoire avant de l'avoir lue
    envoye = st.session_state.setdefault(CLE_ENVOYE, {})
    nouveau = False
    try:
        for cle_session, cle_nav in A_GARDER.items():
            valeur = st.session_state.get(cle_session)
            if valeur is None or envoye.get(cle_nav) == valeur:
                continue
            envoye[cle_nav] = valeur
            if memoire.get(cle_nav) != valeur:
                memoire[cle_nav] = valeur
                nouveau = True
    except Exception:
        return
    if nouveau:
        st.rerun()                          # transmet l'écriture au navigateur


def liste_valide(permis: Callable[[object], bool]):
    """Validateur : garde les éléments permis d'une liste lue dans le navigateur."""
    def valider(v):
        return [x for x in v if permis(x)] if isinstance(v, list) else None
    return valider
