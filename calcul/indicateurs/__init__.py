"""
============================================================
 INDICATEURS — registre découvert automatiquement
============================================================
 Au chargement, chaque fichier de ce dossier (sauf base.py et les
 noms commençant par « _ ») est importé et son INDICATEUR inscrit
 dans REGISTRE. Pour AJOUTER un indicateur :
   1. copier _modele.py sous le nom <identifiant>.py et l'écrire ;
   2. ajouter une ligne <identifiant> dans docs/sources/hypotheses.xlsx
      (onglet « indicateurs ») puis lancer outils/convertir_docs.py ;
   3. lancer les tests (python -m pytest).
 Rien d'autre à modifier : cartes, export et comparaison suivent.
============================================================
"""

import importlib
import pkgutil
from dataclasses import replace

from calcul.indicateurs.base import Indicateur, Resultat
from config.reglages import AMPLEUR_INDICATEURS

__all__ = ["Indicateur", "Resultat", "REGISTRE", "calculer_indicateurs", "valeurs"]

# ============================================================
# PARAMÈTRES
# ============================================================
MODULES_IGNORES = {"base"}               # + tout nom commençant par « _ » (modèle, brouillons)


def _decouvrir() -> dict:
    """{identifiant : Indicateur} des fichiers du dossier, avec contrôle des erreurs courantes."""
    registre = {}
    for module in sorted(m.name for m in pkgutil.iter_modules(__path__)):
        if module in MODULES_IGNORES or module.startswith("_"):
            continue
        ind = getattr(importlib.import_module(f"{__name__}.{module}"), "INDICATEUR", None)
        if not isinstance(ind, Indicateur):
            raise TypeError(f"calcul/indicateurs/{module}.py : variable INDICATEUR = Indicateur(...) manquante")
        if ind.id != module:
            raise ValueError(f"calcul/indicateurs/{module}.py : l'identifiant « {ind.id} » doit être le nom du fichier")
        registre[ind.id] = replace(ind, **AMPLEUR_INDICATEURS.get(ind.id, {}))    # ampleur : table centrale
    return registre


REGISTRE = _decouvrir()


def calculer_indicateurs(a, reglage: dict, hyp: dict, definitions: list) -> list:
    """
    [(définition, Resultat)] dans l'ordre des définitions reçues (ordre choisi dans l'interface,
    par défaut celui de indicateurs.csv) ; ignore les identifiants sans fichier. Le mini-graphique
    de la carte est rangé dans Resultat.info["profil"].
    """
    resultats = []
    for d in definitions:
        ind = REGISTRE.get(d["id"])
        if ind is None:
            continue
        r = ind.calculer(a, reglage, hyp)
        r.info["profil"] = ind.profil(a, hyp) if ind.profil else None
        resultats.append((d, r))
    return resultats


def valeurs(a, reglage: dict, hyp: dict, identifiants) -> dict:
    """{identifiant : valeur} de quelques indicateurs, sans mini-graphique (chiffres clés de la fenêtre de choix)."""
    return {i: REGISTRE[i].calculer(a, reglage, hyp).valeur for i in identifiants if i in REGISTRE}
