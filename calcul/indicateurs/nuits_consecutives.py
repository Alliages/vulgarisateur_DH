"""Nuits tropicales consécutives (max) : plus longue suite de nuits tropicales dont les dates se suivent."""

from calcul.analyse import nuits_ete, plus_longue_suite
from calcul.format_fr import jour_mois_court
from calcul.hypotheses import valeur
from calcul.indicateurs.base import Indicateur, Resultat


def calculer(a, reglage, hyp):
    if a.nuits.empty:
        return Resultat(None, "aucune nuit complète")
    chaudes = (a.nuits >= valeur(hyp, "seuil_nuit_tropicale")).asfreq("D", fill_value=False)   # trou = suite coupée
    suite = plus_longue_suite(chaudes)
    if suite is None:
        return Resultat(0, "aucune nuit tropicale")
    debut, fin, longueur = suite
    texte = f"le {jour_mois_court(debut)}" if longueur == 1 else f"du {jour_mois_court(debut)} au {jour_mois_court(fin)}"
    return Resultat(longueur, texte)


def profil(a, hyp):
    """Bande : une case par nuit d'été, foncée si tropicale."""
    n = nuits_ete(a)
    return None if n.empty else {"type": "bande", "valeurs": n >= valeur(hyp, "seuil_nuit_tropicale")}


INDICATEUR = Indicateur(id="nuits_consecutives", calculer=calculer, profil=profil, teinte="nuit", icone="calendrier")
