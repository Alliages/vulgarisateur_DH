"""
============================================================
 INDICATEURS — contexte de calcul + REGISTRE paramétrique
============================================================
 1. `analyser(serie, reglage, hyp)` calcule une fois pour toutes
    les grandeurs horaires et journalières (seuil, DH horaire,
    températures par jour, Tmin des nuits…).
 2. Le REGISTRE associe à chaque identifiant d'indicateur une
    fonction `f(analyse, reglage, hyp) -> Resultat`.
    L'ordre, la visibilité, le libellé et la bulle « i » viennent
    de config/indicateurs.csv : pour AJOUTER un indicateur, on
    écrit une fonction ici, on l'inscrit dans REGISTRE et on
    ajoute une ligne dans docs/sources/hypotheses.xlsx.
============================================================
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from calcul.dh_re2020 import calculer_dh
from calcul.hypotheses import masque_jour, masque_occupation, valeur

# ============================================================
# PARAMÈTRES
# ============================================================
DEMI_SEMAINE = 3                         # semaine « pointe max » centrée sur le jour de la pointe


@dataclass
class Resultat:
    valeur: float | None                 # None = non calculable
    detail: str = ""
    info: dict = field(default_factory=dict)


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
    jours = jours[jours["n"] == 24]

    # --- Nuits : de nuit_debut (jour J) à nuit_fin (jour J+1), heure légale ---
    debut_n, fin_n = int(valeur(hyp, "nuit_debut")), int(valeur(hyp, "nuit_fin"))
    est_nuit = (hl >= debut_n) | (hl < fin_n)
    jour_nuit = df.index.normalize() - pd.to_timedelta(np.where(hl < fin_n, 1, 0), unit="D")
    dn = df[est_nuit].assign(nuit=jour_nuit[est_nuit])
    g = dn.groupby("nuit")["t"]
    nuits_detail = pd.DataFrame({"tmin": g.min(), "tmoy": g.mean(), "quand": g.idxmin(), "n": g.size()})
    nuits_detail = nuits_detail[nuits_detail["n"] == (24 - debut_n) + fin_n]

    # --- Période « été » pour les moyennes (repli : toute la série si elle ne couvre pas l'été) ---
    mmjj = serie.horodatage.strftime("%m-%d")
    est_ete = np.asarray((mmjj >= str(valeur(hyp, "ete_debut"))) & (mmjj <= str(valeur(hyp, "ete_fin"))))
    ete_couvert = bool(est_ete.sum() >= 24 * 30)
    if not ete_couvert:
        est_ete = np.ones(len(t), dtype=bool)

    return Analyse(serie, methode, message, seuil, dh_h, est_jour, jours, nuits_detail["tmin"], nuits_detail,
                   est_nuit, est_ete, ete_couvert, theta_rm, periode)


# ============================================================
# FONCTIONS D'INDICATEURS
# ============================================================

def _date(d):
    mois = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
    return f"{'1er' if d.day == 1 else d.day} {mois[d.month - 1]}"


def ind_dh(a: Analyse, reglage, hyp):
    occ = "en occupation" if reglage["occupation"] else "24h/24"
    return Resultat(float(a.dh_h.sum()), f"{'RE2020' if a.methode_effective == 'RE2020' else 'basic 26/28'} · {occ}")


def ind_dh_nuit(a: Analyse, reglage, hyp):
    total = a.dh_h.sum()
    nuit = float(a.dh_h[~a.est_jour].sum())
    return Resultat(nuit, f"{100 * nuit / total:.0f} % du DH" if total > 0 else "—")


def _nuits(a: Analyse, seuil: float):
    if a.nuits.empty:
        return Resultat(None, "aucune nuit complète")
    n = int((a.nuits >= seuil).sum())
    return Resultat(n, f"sur {len(a.nuits)} nuits complètes")


def ind_nuits_20(a, reglage, hyp):
    return _nuits(a, valeur(hyp, "seuil_nuit_tropicale"))


def ind_nuits_24(a, reglage, hyp):
    return _nuits(a, valeur(hyp, "seuil_nuit_tres_chaude"))


def jour_le_plus_chaud(a: Analyse, critere: str):
    if a.jours.empty:
        return None
    return a.jours["tmoy" if critere == "moyenne" else "tmax"].idxmax()


def ind_heures_chaudes(a, reglage, hyp):
    seuil = valeur(hyp, "seuil_heures_chaudes")
    n = int((a.serie.t > seuil).sum())
    etendue = "sur l'année" if a.serie.annee_complete else "sur la série"
    return Resultat(n, f"T > {seuil:g} °C · {etendue}")


def ind_nuits_consecutives(a, reglage, hyp):
    """Plus longue suite de nuits tropicales consécutives (dates qui se suivent)."""
    if a.nuits.empty:
        return Resultat(None, "aucune nuit complète")
    chaudes = (a.nuits >= valeur(hyp, "seuil_nuit_tropicale")).asfreq("D", fill_value=False)
    groupes = (chaudes != chaudes.shift()).cumsum()
    series = chaudes.groupby(groupes).agg(["first", "size"])
    longueurs = series.loc[series["first"], "size"]
    if longueurs.empty:
        return Resultat(0, "aucune nuit tropicale")
    g_max = longueurs.idxmax()
    dates = chaudes.index[groupes == g_max]
    texte = f"le {_date(dates[0])}" if len(dates) == 1 else f"du {_date(dates[0])} au {_date(dates[-1])}"
    return Resultat(int(longueurs.max()), texte)


def _periode_moyenne(a):
    return "été (1/06 → 30/09)" if a.ete_couvert else "toute la série"


def ind_t_moyenne(a, reglage, hyp):
    return Resultat(float(a.serie.t[a.est_ete].mean()), _periode_moyenne(a))


def ind_t_moyenne_nuit(a, reglage, hyp):
    masque = a.est_ete & a.est_nuit
    return Resultat(float(a.serie.t[masque].mean()), f"{_periode_moyenne(a)} · nuits 22h-6h")


def ind_journee_chaude(a, reglage, hyp):
    d = jour_le_plus_chaud(a, reglage["critere_journee"])
    if d is None:
        return Resultat(None, "aucune journée complète")
    j = a.jours.loc[d]
    return Resultat(float(j["dh"]), f"{_date(d)} · Tmoy {j['tmoy']:.0f} · Tmax {j['tmax']:.0f} °C", {"jour": d})


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


def ind_semaine_chaude(a, reglage, hyp):
    n = int(valeur(hyp, "semaine_jours"))
    debut = semaine_la_plus_chaude(a, reglage["critere_semaine"], n)
    if debut is None:
        return Resultat(None, f"moins de {n} jours complets")
    fin = debut + pd.Timedelta(days=n - 1)
    dh = float(a.jours.loc[debut:fin, "dh"].sum())
    return Resultat(dh, f"{_date(debut)} → {_date(fin)}", {"debut": debut, "fin": fin})


# ============================================================
# REGISTRE (identifiant → fonction) — l'ordre vient de indicateurs.csv
# ============================================================
REGISTRE = {
    "dh": ind_dh,
    "dh_nuit": ind_dh_nuit,
    "nuits_20": ind_nuits_20,
    "nuits_24": ind_nuits_24,
    "heures_chaudes": ind_heures_chaudes,
    "nuits_consecutives": ind_nuits_consecutives,
    "t_moyenne": ind_t_moyenne,
    "t_moyenne_nuit": ind_t_moyenne_nuit,
    "journee_chaude": ind_journee_chaude,
    "semaine_chaude": ind_semaine_chaude,
}


# ============================================================
# PROFILS (mini-graphiques des cartes) — un profil par indicateur
# ============================================================
# Chaque profil renvoie {"type": "barres" | "ligne" | "bande" | "jauge", "valeurs": …}.
#   barres / ligne : une valeur par mois (index = numéro du mois), sur l'été si la série le couvre ;
#   bande          : une valeur booléenne par nuit (nuit tropicale ou non), sur l'été ;
#   jauge          : une part entre 0 et 1 (demi-cercle), ex. part des DH tombée la nuit.

def _mois_utiles(a: Analyse) -> pd.DatetimeIndex:
    """Horodatage restreint à l'été (si couvert), sinon toute la série."""
    return a.serie.horodatage[a.est_ete]


def _par_mois(a: Analyse, valeurs: np.ndarray, agregat: str) -> pd.Series:
    x = pd.Series(np.asarray(valeurs, dtype=float)[a.est_ete], index=_mois_utiles(a))
    return getattr(x.groupby(x.index.month), agregat)()


def _nuits_ete(a: Analyse) -> pd.Series:
    """Tmin des nuits complètes, restreint à l'été si la série le couvre."""
    n = a.nuits
    if a.ete_couvert and not n.empty:
        jours_ete = set(_mois_utiles(a).normalize())
        n = n[n.index.isin(jours_ete)]
    return n


def profil_mensuel(a: Analyse, identifiant: str, hyp: dict) -> dict | None:
    t = a.serie.t
    if identifiant == "dh":
        return {"type": "barres", "valeurs": _par_mois(a, a.dh_h, "sum")}
    if identifiant == "dh_nuit":
        total = float(a.dh_h.sum())
        return None if total <= 0 else {"type": "jauge", "valeurs": float(a.dh_h[~a.est_jour].sum()) / total}
    if identifiant == "heures_chaudes":
        return {"type": "barres", "valeurs": _par_mois(a, t > valeur(hyp, "seuil_heures_chaudes"), "sum")}
    if identifiant in ("nuits_20", "nuits_24"):
        seuil = valeur(hyp, "seuil_nuit_tropicale" if identifiant == "nuits_20" else "seuil_nuit_tres_chaude")
        n = _nuits_ete(a)
        return None if n.empty else {"type": "barres", "valeurs": (n >= seuil).groupby(n.index.month).sum()}
    if identifiant == "nuits_consecutives":
        n = _nuits_ete(a)
        return None if n.empty else {"type": "bande", "valeurs": n >= valeur(hyp, "seuil_nuit_tropicale")}
    if identifiant == "t_moyenne":
        return {"type": "ligne", "valeurs": _par_mois(a, t, "mean")}
    if identifiant == "t_moyenne_nuit":
        x = pd.Series(np.where(a.est_nuit, t, np.nan)[a.est_ete], index=_mois_utiles(a))
        return {"type": "ligne", "valeurs": x.groupby(x.index.month).mean()}
    return None


def calculer_indicateurs(a: Analyse, reglage: dict, hyp: dict, definitions: list) -> list:
    """
    [(définition, Resultat)] dans l'ordre des définitions reçues (ordre choisi dans l'interface,
    par défaut celui de indicateurs.csv) ; ignore les id sans fonction. Le profil mensuel
    (mini-graphique de la carte) est rangé dans Resultat.info["profil"].
    """
    resultats = []
    for d in definitions:
        if d["id"] not in REGISTRE:
            continue
        r = REGISTRE[d["id"]](a, reglage, hyp)
        r.info["profil"] = profil_mensuel(a, d["id"], hyp)
        resultats.append((d, r))
    return resultats
