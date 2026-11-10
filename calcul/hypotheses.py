"""
============================================================
 HYPOTHÈSES — lecture de config/hypotheses.csv et définitions
 algorithmiques (jour, nuit, occupation, heure légale)
============================================================
 Les VALEURS viennent de hypotheses.csv (lui-même généré depuis
 docs/sources/hypotheses.xlsx). Ce fichier ne contient que la
 façon de s'en servir.
============================================================
"""

import csv
import os
import re

import numpy as np

# Occupation conventionnelle logement (annexe III, 4.1 et classeur des scénarios conventionnels) : une
# seule définition, celle de dh_re2020.py (jour de la semaine, 0 = lundi → (début, fin) d'absence, heure
# légale ; semaine inoccupée de décembre)
from calcul.dh_re2020 import ABSENCES_LOGEMENT_RE2020 as ABSENCES_LOGEMENT
from calcul.dh_re2020 import semaine_inoccupee

# ============================================================
# PARAMÈTRES
# ============================================================
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHEMIN_HYPOTHESES = os.path.join(RACINE, "config", "hypotheses.csv")
CHEMIN_INDICATEURS = os.path.join(RACINE, "config", "indicateurs.csv")
MOTIF_REPERE = re.compile(r"\[\[hyp:([a-z0-9_]+)\]\]")


# ============================================================
# LECTURE
# ============================================================

def _nombre(valeur):
    """Convertit en float si possible (« 0.33 », « 26 »), sinon garde le texte."""
    try:
        return float(str(valeur).replace(",", "."))
    except ValueError:
        return valeur


def lire_csv(chemin):
    with open(chemin, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def charger_hypotheses() -> dict:
    """{id: ligne complète avec 'valeur' convertie en nombre si possible}."""
    hyp = {}
    for ligne in lire_csv(CHEMIN_HYPOTHESES):
        ligne["valeur"] = _nombre(ligne["valeur"])
        hyp[ligne["id"]] = ligne
    return hyp


def charger_indicateurs(tous: bool = False) -> list:
    """
    Indicateurs triés selon la colonne « ordre » (ordre par défaut, modifiable dans l'interface).
    tous=False : seulement les actifs (actif = 1) ; tous=True : aussi ceux proposés en option.
    """
    lignes = lire_csv(CHEMIN_INDICATEURS)
    for l in lignes:
        l["actif"] = str(l["actif"]).strip() in ("1", "1.0")
        l["decimales"] = int(float(l.get("decimales") or 0))     # chiffres après la virgule sur les cartes
    if not tous:
        lignes = [l for l in lignes if l["actif"]]
    return sorted(lignes, key=lambda l: float(l["ordre"]))


def valeur(hyp: dict, identifiant: str):
    return hyp[identifiant]["valeur"]


def remplacer_reperes(texte: str, hyp: dict) -> str:
    """[[hyp:seuil_nuit_tropicale]] → « 20 » (valeur à jour, entiers sans décimale)."""
    def _rempl(m):
        v = hyp.get(m.group(1), {}).get("valeur", f"?{m.group(1)}?")
        return f"{v:g}".replace(".", ",") if isinstance(v, float) else str(v)
    return MOTIF_REPERE.sub(_rempl, texte or "")


# ============================================================
# DÉFINITIONS HORAIRES
# ============================================================

def masque_jour(heure_legale, hyp) -> np.ndarray:
    """Jour = [jour_debut ; jour_fin[ en heure légale (RE2020 : 6h-22h)."""
    return (heure_legale >= valeur(hyp, "jour_debut")) & (heure_legale < valeur(hyp, "jour_fin"))


def masque_occupation(heure_legale, jour_semaine, jour_annee=None) -> np.ndarray:
    """
    True = occupé. Scénario conventionnel du logement (ABSENCES_LOGEMENT).
    jour_annee (1 = 1er janvier) : s'il est fourni, la semaine inoccupée de décembre est retirée.
    """
    occupe = np.ones(len(heure_legale), dtype=bool)
    for jour, (debut, fin) in ABSENCES_LOGEMENT.items():
        occupe &= ~((jour_semaine == jour) & (heure_legale >= debut) & (heure_legale < fin))
    if jour_annee is not None:
        occupe &= ~semaine_inoccupee(jour_annee)
    return occupe
