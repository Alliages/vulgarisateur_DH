"""
Outils partagés par plusieurs indicateurs (nuits chaudes, période des moyennes).
Le nom commence par « _ » : ce fichier n'est pas un indicateur et n'est pas inscrit au registre.
"""

from calcul.analyse import nuits_ete
from calcul.format_fr import jour_slash_mois
from calcul.hypotheses import valeur
from calcul.indicateurs.base import Resultat


def nuits_au_dessus(a, seuil: float) -> Resultat:
    """Nombre de nuits complètes dont la température minimale reste ≥ seuil."""
    if a.nuits.empty:
        return Resultat(None, "aucune nuit complète")
    return Resultat(int((a.nuits >= seuil).sum()), f"sur {len(a.nuits)} nuits complètes")


def profil_nuits_par_mois(a, seuil: float):
    """Mini-graphique : nombre de nuits ≥ seuil par mois d'été."""
    n = nuits_ete(a)
    return None if n.empty else {"type": "barres", "valeurs": (n >= seuil).groupby(n.index.month).sum()}


def periode_des_moyennes(a, hyp) -> str:
    """« été (1/06 → 30/09) », ou « toute la série » pour un relevé qui ne couvre pas l'été."""
    if not a.ete_couvert:
        return "toute la série"
    return f"été ({jour_slash_mois(valeur(hyp, 'ete_debut'))} → {jour_slash_mois(valeur(hyp, 'ete_fin'))})"


def heures_de_nuit(hyp) -> str:
    """« 22h-6h » (heures de nuit des hypothèses)."""
    return f"{valeur(hyp, 'nuit_debut'):g}h-{valeur(hyp, 'nuit_fin'):g}h"
