"""
============================================================
 GÉNÉRATEUR — journée et semaine types (formules de l'Excel
 Vulgarisation_DH, reprises du vulgarisateur Dash)
============================================================
 Pour chaque jour : T à minuit (T0), pic bas à 5h (Tmin), pic
 haut (Tmax) à 13h (formule h = 12) ou 15h, courbe :
   « lissée »    : interpolation sinusoïdale
   « brute »     : interpolation linéaire
   « aléatoire » : moyenne des deux + bruit (±8 % de l'amplitude)
============================================================
"""

import numpy as np

# ============================================================
# PARAMÈTRES
# ============================================================
H_MIN = 5                                    # heure du pic bas
H_PIC = {"13h": 12, "15h": 15}               # « 13h » = h 12 dans l'Excel d'origine
AMPLITUDE_ALEATOIRE = 0.08
COURBES = ("lissée", "brute", "aléatoire")


def _lineaire(h, t0, tmin, tmax, hp):
    if h <= H_MIN:
        return t0 + (tmin - t0) * h / H_MIN
    if h <= hp:
        return tmin + (tmax - tmin) * (h - H_MIN) / (hp - H_MIN)
    return tmax + (t0 - tmax) * (h - hp) / (24 - hp)


def _lissee(h, t0, tmin, tmax, hp):
    if h <= H_MIN:
        return t0 + (tmin - t0) * np.sin(np.pi / 2 * h / H_MIN)
    if h <= hp:
        return tmin + (tmax - tmin) * np.sin(np.pi / 2 * (h - H_MIN) / (hp - H_MIN))
    return t0 + (tmax - t0) * np.cos(np.pi / 2 * (h - hp) / (24 - hp))


def journee(t0: float, tmax: float, tmin: float, pic: str = "15h", courbe: str = "lissée",
            graine: int | None = None) -> np.ndarray:
    """24 températures horaires (0h → 23h)."""
    hp = H_PIC[pic]
    rng = np.random.default_rng(graine)
    amp = (tmax - tmin) * AMPLITUDE_ALEATOIRE
    sortie = np.empty(24)
    for h in range(24):
        if courbe == "brute":
            sortie[h] = _lineaire(h, t0, tmin, tmax, hp)
        elif courbe == "aléatoire":
            sortie[h] = (_lineaire(h, t0, tmin, tmax, hp) + _lissee(h, t0, tmin, tmax, hp)) / 2 + rng.uniform(-amp, amp)
        else:
            sortie[h] = _lissee(h, t0, tmin, tmax, hp)
    return sortie


def plusieurs_jours(parametres: list, graine: int | None = None) -> np.ndarray:
    """parametres : liste de dict(t0, tmax, tmin, pic, courbe) → 24 × n températures."""
    return np.concatenate([journee(p["t0"], p["tmax"], p["tmin"], p["pic"], p["courbe"],
                                   None if graine is None else graine + i) for i, p in enumerate(parametres)])
