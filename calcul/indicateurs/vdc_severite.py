"""Sévérité cumulée des vagues de chaleur : somme des sévérités de toutes les vagues du fichier (°C·jour)."""

from calcul.analyse import heures_ete
from calcul.format_fr import nombre
from calcul.indicateurs.base import Indicateur, Resultat
from calcul.vagues_chaleur import par_mois_vagues, vagues_du_fichier

# ============================================================
# PARAMÈTRES
# ============================================================
TEXTE_SANS_SEUILS = "seuils de la station non calculés"


def calculer(a, reglage, hyp):
    vagues, s = vagues_du_fichier(a, hyp)
    if vagues is None:
        return Resultat(None, TEXTE_SANS_SEUILS)
    total = sum(vg.severite for vg in vagues)
    detail = (f"{len(vagues)} vague{'s' if len(vagues) > 1 else ''} · Sdeb {nombre(s['sdeb'], 1)} °C ({s['station']})"
              if vagues else f"aucune vague · Spic {nombre(s['spic'], 1)} °C ({s['station']})")
    return Resultat(total, detail, {"vagues": vagues, "seuils": s})


def profil(a, hyp):
    """Barres : sévérité par mois (mois de l'été et mois des vagues)."""
    vagues, s = vagues_du_fichier(a, hyp)
    if vagues is None:
        return None
    x = par_mois_vagues(vagues, s["sdeb"], "severite")
    mois = sorted(set(heures_ete(a).month) | set(x.index))          # mois de l'été + mois des vagues
    return {"type": "barres", "valeurs": x.reindex(mois, fill_value=0.0)}


INDICATEUR = Indicateur(id="vdc_severite", calculer=calculer, profil=profil, teinte="chaud", icone="soleil")
