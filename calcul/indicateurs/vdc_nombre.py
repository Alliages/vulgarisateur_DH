"""Nombre de vagues de chaleur du fichier (méthode Météo-France, seuils de la station)."""

from calcul.analyse import heures_ete
from calcul.format_fr import jour_mois_court
from calcul.indicateurs.base import Indicateur, Resultat
from calcul.indicateurs.vdc_severite import TEXTE_SANS_SEUILS
from calcul.vagues_chaleur import par_mois_vagues, vagues_du_fichier


def calculer(a, reglage, hyp):
    vagues, s = vagues_du_fichier(a, hyp)
    if vagues is None:
        return Resultat(None, TEXTE_SANS_SEUILS)
    if not vagues:
        return Resultat(0, "aucune vague")
    jours = sum(vg.duree for vg in vagues)
    longue = max(vagues, key=lambda vg: vg.duree)                 # à égalité : la première
    detail = f"{jours} jours · plus longue du {jour_mois_court(longue.debut)} au {jour_mois_court(longue.fin)}"
    return Resultat(len(vagues), detail, {"jours": jours})


def profil(a, hyp):
    """Barres : jours de vague par mois."""
    vagues, s = vagues_du_fichier(a, hyp)
    if vagues is None:
        return None
    x = par_mois_vagues(vagues, s["sdeb"], "jours")
    mois = sorted(set(heures_ete(a).month) | set(x.index))          # mois de l'été + mois des vagues
    return {"type": "barres", "valeurs": x.reindex(mois, fill_value=0.0)}


INDICATEUR = Indicateur(id="vdc_nombre", calculer=calculer, profil=profil, teinte="chaud", icone="calendrier")
