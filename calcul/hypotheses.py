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

# ============================================================
# PARAMÈTRES
# ============================================================
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHEMIN_HYPOTHESES = os.path.join(RACINE, "config", "hypotheses.csv")
CHEMIN_INDICATEURS = os.path.join(RACINE, "config", "indicateurs.csv")
MOTIF_REPERE = re.compile(r"\[\[hyp:([a-z0-9_]+)\]\]")

# Occupation conventionnelle logement (PROVISOIRE, source CEREMA, à vérifier par Guigui)
# jour de la semaine (0 = lundi) → (début, fin) d'absence, fin exclue, heure légale
ABSENCES_LOGEMENT = {0: (10, 18), 1: (10, 18), 2: (10, 14), 3: (10, 18), 4: (10, 18)}


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


def charger_indicateurs() -> list:
    """Indicateurs actifs, triés selon la colonne « ordre »."""
    lignes = [l for l in lire_csv(CHEMIN_INDICATEURS) if str(l["actif"]).strip() in ("1", "1.0")]
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


def masque_occupation(heure_legale, jour_semaine) -> np.ndarray:
    """True = occupé. Scénario logement provisoire (ABSENCES_LOGEMENT)."""
    occupe = np.ones(len(heure_legale), dtype=bool)
    for jour, (debut, fin) in ABSENCES_LOGEMENT.items():
        occupe &= ~((jour_semaine == jour) & (heure_legale >= debut) & (heure_legale < fin))
    return occupe
