"""DH nuit (°C.h) : part des DH tombée hors des heures de jour (RE2020 : 22h-6h, heure légale)."""

from calcul.indicateurs.base import Indicateur, Resultat


def calculer(a, reglage, hyp):
    total = a.dh_h.sum()
    nuit = float(a.dh_h[~a.est_jour].sum())
    return Resultat(nuit, f"{100 * nuit / total:.0f} % du DH" if total > 0 else "—")


def profil(a, hyp):
    """Jauge en demi-cercle : part des DH tombée la nuit."""
    total = float(a.dh_h.sum())
    return None if total <= 0 else {"type": "jauge", "valeurs": float(a.dh_h[~a.est_jour].sum()) / total}


INDICATEUR = Indicateur(id="dh_nuit", calculer=calculer, profil=profil, teinte="nuit", icone="lune")
