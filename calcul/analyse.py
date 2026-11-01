"""
============================================================
 ANALYSE — contexte de calcul commun à tous les indicateurs
============================================================
 `analyser(serie, reglage, hyp)` calcule une fois pour toutes les
 grandeurs horaires et journalières d'une série (seuil, DH horaire,
 températures par jour, Tmin des nuits, masques jour / nuit / été).
 Les indicateurs (calcul/indicateurs/) et les graphiques lisent
 ce contexte au lieu de refaire le calcul.

 On trouve aussi ici les recherches partagées : journée et semaine
 les plus chaudes, plus longue suite de nuits, tranche horaire
 d'une période, agrégats par mois des mini-graphiques.
 Aucune dépendance à Streamlit.
============================================================
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from calcul.dh_re2020 import calculer_dh
from calcul.hypotheses import masque_jour, masque_occupation, valeur

# ============================================================
# PARAMÈTRES
# ============================================================
DEMI_SEMAINE = 3                         # semaine « pointe max » centrée sur le jour de la pointe
JOURS_ETE_MINIMUM = 30                   # en deçà, la série « ne couvre pas l'été » : moyennes sur toute la série
HEURES_PAR_JOUR = 24


@dataclass
class Analyse:
    serie: object
    methode_effective: str
    message_methode: str
    seuil: np.ndarray
    dh_h: np.ndarray
    est_jour: np.ndarray
    jours: pd.DataFrame                  # une ligne par jour légal complet
    nuits: pd.Series                     # Tmin de la nuit commençant le jour J
    nuits_detail: pd.DataFrame           # par nuit : tmin, tmoy, horodatage du minimum
    est_nuit: np.ndarray                 # heures de nuit (nuits caniculaires, T moyenne nocturne)
    est_ete: np.ndarray                  # heures de la période « été » (moyennes)
    ete_couvert: bool                    # la série couvre-t-elle l'été ?
    theta_rm: np.ndarray | None
    periode_adaptative: np.ndarray | None


# ============================================================
# CONTEXTE DE CALCUL
# ============================================================

def analyser(serie, reglage: dict, hyp: dict) -> Analyse:
    t = serie.t
    hl, js = serie.heure_legale, serie.jour_semaine
    est_jour = masque_jour(hl, hyp)
    occ = masque_occupation(hl, js) if reglage["occupation"] else np.ones(len(t), dtype=bool)
    bas, haut = valeur(hyp, "seuil_nuit_dh"), valeur(hyp, "seuil_jour_max")

    theta_rm = periode = None
    methode, message = reglage["methode"], ""
    if methode == "RE2020" and serie.annee_complete:
        res = calculer_dh(t, t, seuil_bas=bas, seuil_haut=haut, decalage_heure=serie.decalage_utc,
                          heure_debut_jour=int(valeur(hyp, "jour_debut")), heure_fin_jour=int(valeur(hyp, "jour_fin")),
                          occupation=occ, details=True)
        seuil, dh_h = res["seuil_horaire"], res["dh_horaire"]
        theta_rm, periode = res["theta_rm"], res["periode_adaptative"]
    else:
        if methode == "RE2020":
            message = "Série de moins d'un an : DH RE2020 non calculable (moyenne glissante), DH basic affiché."
            methode = "basic"
        seuil = np.where(est_jour, haut, bas)
        dh_h = np.maximum(t - seuil, 0.0) * occ

    # --- Agrégats journaliers (jours légaux complets uniquement) ---
    df = pd.DataFrame({"t": t, "dh": dh_h, "h": hl}, index=serie.horodatage)
    groupe = df.groupby(df.index.normalize())
    jours = pd.DataFrame({"tmoy": groupe["t"].mean(), "tmax": groupe["t"].max(), "tmin": groupe["t"].min(),
                          "dh": groupe["dh"].sum(), "n": groupe["t"].size()})
    jours = jours[jours["n"] == HEURES_PAR_JOUR]

    # --- Nuits : de nuit_debut (jour J) à nuit_fin (jour J+1), heure légale ---
    debut_n, fin_n = int(valeur(hyp, "nuit_debut")), int(valeur(hyp, "nuit_fin"))
    est_nuit = (hl >= debut_n) | (hl < fin_n)
    jour_nuit = df.index.normalize() - pd.to_timedelta(np.where(hl < fin_n, 1, 0), unit="D")
    dn = df[est_nuit].assign(nuit=jour_nuit[est_nuit])
    g = dn.groupby("nuit")["t"]
    nuits_detail = pd.DataFrame({"tmin": g.min(), "tmoy": g.mean(), "quand": g.idxmin(), "n": g.size()})
    nuits_detail = nuits_detail[nuits_detail["n"] == (HEURES_PAR_JOUR - debut_n) + fin_n]

    # --- Période « été » pour les moyennes (repli : toute la série si elle ne couvre pas l'été) ---
    mmjj = serie.horodatage.strftime("%m-%d")
    est_ete = np.asarray((mmjj >= str(valeur(hyp, "ete_debut"))) & (mmjj <= str(valeur(hyp, "ete_fin"))))
    ete_couvert = bool(est_ete.sum() >= HEURES_PAR_JOUR * JOURS_ETE_MINIMUM)
    if not ete_couvert:
        est_ete = np.ones(len(t), dtype=bool)

    return Analyse(serie, methode, message, seuil, dh_h, est_jour, jours, nuits_detail["tmin"], nuits_detail,
                   est_nuit, est_ete, ete_couvert, theta_rm, periode)


# ============================================================
# RECHERCHES PARTAGÉES (indicateurs, graphiques, onglet Créer)
# ============================================================

def jour_le_plus_chaud(a: Analyse, critere: str):
    """Jour (minuit) de la journée la plus chaude selon « moyenne » ou « max », ou None."""
    if a.jours.empty:
        return None
    return a.jours["tmoy" if critere == "moyenne" else "tmax"].idxmax()


def semaine_la_plus_chaude(a: Analyse, critere: str, nb_jours: int = 7):
    """Premier jour de la semaine la plus chaude, ou None (moins de nb_jours jours complets consécutifs)."""
    j = a.jours.asfreq("D")                               # trous de dates → NaN
    if j["tmoy"].notna().sum() < nb_jours:
        return None
    if critere == "pointe_max":
        d = j["tmax"].idxmax()
        debut = max(j.index[0], d - pd.Timedelta(days=DEMI_SEMAINE))
        debut = min(debut, j.index[-1] - pd.Timedelta(days=nb_jours - 1))
        return debut
    col = "tmoy" if critere == "moyenne" else "tmax"
    glissante = j[col].rolling(nb_jours, min_periods=nb_jours).mean()   # fenêtre se terminant au jour J
    if glissante.notna().sum() == 0:
        return None
    return glissante.idxmax() - pd.Timedelta(days=nb_jours - 1)


def plus_longue_suite(chaudes: pd.Series):
    """
    (début, fin, longueur) de la plus longue suite de jours consécutifs à True, ou None.
    `chaudes` : une valeur par jour, sans trou de dates (sinon la suite est coupée là où il manque des jours).
    À égalité, la première suite l'emporte.
    """
    v = chaudes.to_numpy(dtype=bool)
    if not v.any():
        return None
    bloc = np.cumsum(np.r_[True, v[1:] != v[:-1]])        # un numéro par bloc de valeurs identiques
    longueurs = np.bincount(bloc, weights=v)               # nombre de True par bloc (0 pour un bloc de False)
    jours = np.flatnonzero(bloc == int(np.argmax(longueurs)))   # argmax : la première suite la plus longue
    return chaudes.index[jours[0]], chaudes.index[jours[-1]], len(jours)


def tranche(a: Analyse, debut, nb_heures: int):
    """Températures, seuil, DH et horodatage d'une période de nb_heures à partir de `debut`."""
    s = a.serie
    i0 = s.horodatage.get_indexer([debut])[0]
    sl = slice(i0, i0 + nb_heures)
    return s.t[sl], a.seuil[sl], a.dh_h[sl], s.horodatage[sl]


def occupation_affichee(horodatage: pd.DatetimeIndex, avec_occupation: bool):
    """Masque d'occupation (scénario logement) d'une période, ou None si les DH sont comptés 24h/24."""
    if not avec_occupation:
        return None
    return masque_occupation(horodatage.hour.to_numpy(), horodatage.day_of_week.to_numpy())


def journees_de_la_periode_chaude(a: Analyse, critere: str, nb_jours: int, jours_semaine: int):
    """
    Pour l'onglet Créer : [(date, T à minuit, T max, T min)] des nb_jours premiers jours de la semaine la
    plus chaude (arrondis à 0,1 °C), ou None s'il n'y a pas de semaine complète.
    """
    debut = semaine_la_plus_chaude(a, critere, jours_semaine)
    if debut is None:
        return None
    t = pd.Series(a.serie.t, index=a.serie.horodatage)
    sortie = []
    for k in range(nb_jours):
        d = debut + pd.Timedelta(days=k)
        jour = t.loc[d:d + pd.Timedelta(hours=HEURES_PAR_JOUR - 1)]
        sortie.append((d, round(float(jour.iloc[0]), 1), round(float(jour.max()), 1), round(float(jour.min()), 1)))
    return sortie


# ============================================================
# AGRÉGATS DES MINI-GRAPHIQUES (cartes)
# ============================================================

def heures_ete(a: Analyse) -> pd.DatetimeIndex:
    """Horodatage restreint à l'été (si couvert), sinon toute la série."""
    return a.serie.horodatage[a.est_ete]


def par_mois(a: Analyse, valeurs, agregat: str) -> pd.Series:
    """Agrégat (« sum », « mean »…) par mois des valeurs horaires, sur l'été si la série le couvre."""
    x = pd.Series(np.asarray(valeurs, dtype=float)[a.est_ete], index=heures_ete(a))
    return getattr(x.groupby(x.index.month), agregat)()


def nuits_ete(a: Analyse) -> pd.Series:
    """Tmin des nuits complètes, restreint à l'été si la série le couvre."""
    n = a.nuits
    if a.ete_couvert and not n.empty:
        jours_ete = set(heures_ete(a).normalize())
        n = n[n.index.isin(jours_ete)]
    return n
