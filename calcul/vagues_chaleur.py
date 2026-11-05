"""
============================================================
 VAGUES DE CHALEUR — détection et sévérité (méthode Météo-France)
============================================================
 Méthode de Soubeyroux et al. (La Météorologie n° 94, 2016), appliquée
 aux températures moyennes journalières Tm = (Tmin + Tmax) / 2 d'un
 fichier météo, avec les seuils de SA station de référence :
   Spic (pic), Sdeb (début), Sint (interruption), calculés par la
   GitHub Action « Seuils vagues de chaleur » → config/seuils_vague_chaleur.csv.

 Règles (hypothèses vdc_* de docs/sources/hypotheses.xlsx) :
   - une vague existe si Tm ≥ Spic au moins un jour ;
   - elle commence au premier jour d'une suite continue de jours ≥ Sdeb
     qui précède le pic ;
   - elle continue tant que Tm ≥ Sint et que Tm ne reste pas sous Sdeb
     pendant vdc_jours_sous_debut jours consécutifs ;
   - elle se termine au dernier jour ≥ Sdeb (les jours sous Sdeb en
     fin d'épisode ne sont pas comptés) ;
   - elle dure au moins vdc_duree_min jours ;
   - sévérité = Σ max(0 ; Tm − Sdeb) sur ses jours (°C·jour) ;
   - un jour manquant interrompt la vague.
 Indicateurs affichés : somme des sévérités du fichier et nombre de vagues.
 Variante scolaire (prévue, pas encore affichée) : sans les jours du
 vdc_variante_exclusion_debut au vdc_variante_exclusion_fin.
 Aucune dépendance à Streamlit.
============================================================
"""

import os
import re
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import pandas as pd

from calcul.hypotheses import RACINE, lire_csv, valeur

# ============================================================
# PARAMÈTRES
# ============================================================
CHEMIN_SEUILS = os.path.join(RACINE, "config", "seuils_vague_chaleur.csv")
FAMILLES_REFERENCE = {"RE2020", "TRACC"}  # fichiers rattachés à la station de référence de leur zone
MOTIF_POSTE = re.compile(r"\b(\d{8})\b")  # numéro de poste Météo-France cité dans la description
STATUTS_UTILISABLES = {"calculé"}         # « incomplet » : seuils non utilisés
CHAMPS_META_POSTE = ("description", "station", "source")


@dataclass
class Vague:
    debut: pd.Timestamp
    fin: pd.Timestamp
    duree: int                           # jours
    intensite: float                     # Tm maximale de la vague (°C)
    severite: float                      # Σ max(0 ; Tm − Sdeb) (°C·jour)
    jours: pd.Series                     # Tm de chaque jour de la vague


# ============================================================
# SEUILS DE LA STATION
# ============================================================

@lru_cache(maxsize=1)
def charger_seuils(chemin: str = CHEMIN_SEUILS) -> tuple:
    """Lignes de config/seuils_vague_chaleur.csv utilisables (statut « calculé »), ou () si absent."""
    if not os.path.exists(chemin):
        return ()
    lignes = []
    for l in lire_csv(chemin):
        if l.get("statut") in STATUTS_UTILISABLES:
            lignes.append({**l, **{k: float(l[k]) for k in ("spic", "sdeb", "sint")},
                           "numero_poste": str(l["numero_poste"]).zfill(8)})
    return tuple(lignes)


def seuils_du_fichier(meta: dict, seuils=None):
    """
    Seuils de la station du fichier, ou None :
      - fichier RE2020 ou TRACC → station de référence de sa zone ;
      - autre fichier → station dont le numéro de poste est cité dans ses métadonnées (ex. observations).
    """
    seuils = charger_seuils() if seuils is None else seuils
    if meta.get("famille") in FAMILLES_REFERENCE:
        return next((s for s in seuils if s["zone"] == meta.get("zone")), None)
    texte = " ".join(str(meta.get(c, "")) for c in CHAMPS_META_POSTE)
    postes = set(MOTIF_POSTE.findall(texte))
    return next((s for s in seuils if s["numero_poste"] in postes), None)


# ============================================================
# DÉTECTION
# ============================================================

def tm_journaliere(jours: pd.DataFrame) -> pd.Series:
    """Tm = (Tmin + Tmax) / 2 des jours complets, une valeur par date (jour manquant → NaN)."""
    if jours.empty:
        return pd.Series(dtype=float)
    return ((jours["tmin"] + jours["tmax"]) / 2).asfreq("D")


def detecter_vagues(tm: pd.Series, spic: float, sdeb: float, sint: float,
                    jours_sous_debut: int = 3, duree_min: int = 3) -> list:
    """Vagues de chaleur d'une série journalière de Tm (index de dates continu, NaN = jour manquant)."""
    v = tm.to_numpy(dtype=float)
    n, vagues, fin_precedente, i = len(v), [], -1, 0
    while i < n:
        if not v[i] >= spic:                               # NaN compris : pas de pic
            i += 1
            continue
        # --- Début : on remonte la suite continue de jours ≥ Sdeb (sans chevaucher la vague précédente) ---
        d = i
        while d - 1 > fin_precedente and v[d - 1] >= sdeb:
            d -= 1
        # --- Fin : on avance tant que Tm ≥ Sint et pas trop de jours de suite sous Sdeb ---
        f, j, sous = i, i + 1, 0
        while j < n and v[j] >= sint:                      # NaN ou Tm < Sint : arrêt
            if v[j] >= sdeb:
                f, sous = j, 0
            else:
                sous += 1
                if sous >= jours_sous_debut:
                    break
            j += 1
        if f - d + 1 >= duree_min:
            jours = tm.iloc[d:f + 1]
            vagues.append(Vague(jours.index[0], jours.index[-1], len(jours), float(jours.max()),
                                float(np.maximum(jours - sdeb, 0).sum()), jours))
        fin_precedente, i = f, f + 1
    return vagues


def vagues_du_fichier(a, hyp, seuils=None):
    """(vagues, seuils de la station) d'une analyse, ou (None, None) si la station n'a pas de seuils."""
    s = seuils_du_fichier(a.serie.meta, seuils)
    if s is None:
        return None, None
    vagues = detecter_vagues(tm_journaliere(a.jours), s["spic"], s["sdeb"], s["sint"],
                             int(valeur(hyp, "vdc_jours_sous_debut")), int(valeur(hyp, "vdc_duree_min")))
    return vagues, s


# ============================================================
# VARIANTE SCOLAIRE (prévue, pas encore affichée)
# ============================================================

def hors_periode(vagues: list, sdeb: float, debut_mmjj: str, fin_mmjj: str) -> dict:
    """
    Cumuls sans les jours du debut_mmjj au fin_mmjj (ex. « 07-10 » → « 08-31 ») : les vagues sont détectées
    sur toute la série, puis leurs jours exclus ne comptent plus ; une vague entièrement exclue disparaît.
    """
    severite, duree, nombre = 0.0, 0, 0
    for vg in vagues:
        mmjj = vg.jours.index.strftime("%m-%d")
        gardes = vg.jours[(mmjj < debut_mmjj) | (mmjj > fin_mmjj)]
        if len(gardes):
            nombre += 1
            duree += len(gardes)
            severite += float(np.maximum(gardes - sdeb, 0).sum())
    return {"severite": severite, "duree": duree, "nombre": nombre}


# ============================================================
# AGRÉGATS DES CARTES
# ============================================================

def par_mois_vagues(vagues: list, sdeb: float, quoi: str) -> pd.Series:
    """Sévérité (« severite ») ou jours de vague (« jours ») par mois, pour le mini-graphique."""
    if not vagues:
        return pd.Series(dtype=float)
    tm = pd.concat([vg.jours for vg in vagues])
    x = np.maximum(tm - sdeb, 0) if quoi == "severite" else pd.Series(1.0, index=tm.index)
    return x.groupby(x.index.month).sum()
