"""DH (°C.h) : somme, heure par heure, des degrés au-dessus du seuil d'inconfort (méthode et occupation selon le réglage)."""

from calcul.analyse import par_mois
from calcul.hypotheses import valeur
from calcul.indicateurs.base import Indicateur, Resultat


def calculer(a, reglage, hyp):
    occupation = "en occupation" if reglage["occupation"] else "24h/24"
    methode = ("RE2020" if a.methode_effective == "RE2020"
               else f"basic {valeur(hyp, 'seuil_nuit_dh'):g}/{valeur(hyp, 'seuil_jour_max'):g}")
    return Resultat(float(a.dh_h.sum()), f"{methode} · {occupation}")


def profil(a, hyp):
    return {"type": "barres", "valeurs": par_mois(a, a.dh_h, "sum")}


INDICATEUR = Indicateur(id="dh", calculer=calculer, profil=profil, teinte="chaud", icone="soleil", principale=True)
