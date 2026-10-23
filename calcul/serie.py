"""
============================================================
 SÉRIE MÉTÉO — chargement, contrôle, heure légale
============================================================
 Une SerieMeteo est une température extérieure horaire avec :
   - ses horodatages en HEURE LÉGALE (toutes les définitions
     jour / nuit / occupation s'y appliquent) ;
   - le décalage UTC → légal (pour la méthode RE2020) ;
   - ses métadonnées (zone, type, station, source…).
 Formats lus :
   « annee_type » : heure;T  (0 → 8759, UTC, fichiers RE2020)
   « date_heure » : date;heure;T  (relevé, heure légale)
============================================================
"""

import csv
import io
import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from calcul.hypotheses import RACINE, lire_csv

# ============================================================
# PARAMÈTRES
# ============================================================
CHEMIN_CATALOGUE = os.path.join(RACINE, "config", "catalogue_fichiers.csv")
ANNEE_TYPE = 2018                  # année non bissextile débutant un lundi (convention Th-BCE)
NB_HEURES_ANNEE = (8760, 8784)
T_MIN_PLAUSIBLE, T_MAX_PLAUSIBLE = -40.0, 55.0


@dataclass
class SerieMeteo:
    id: str
    libelle: str
    t: np.ndarray                        # températures (°C), pas horaire
    horodatage: pd.DatetimeIndex         # heure légale
    decalage_utc: int = 0                # heures à ajouter à l'indice pour passer en légal
    annee_complete: bool = False
    meta: dict = field(default_factory=dict)
    avertissements: list = field(default_factory=list)

    @property
    def heure_legale(self):
        return self.horodatage.hour.to_numpy()

    @property
    def jour_semaine(self):
        return self.horodatage.dayofweek.to_numpy()


# ============================================================
# LECTURE
# ============================================================

def _nombres(colonne):
    return np.array([float(str(v).replace(",", ".")) for v in colonne], dtype=float)


def _controler(t, avertissements, trou_max=3):
    """Plausibilité + comblement des petits trous (≤ trou_max h)."""
    t = np.asarray(t, dtype=float)
    hors = (t < T_MIN_PLAUSIBLE) | (t > T_MAX_PLAUSIBLE)
    if hors.any():
        raise ValueError(f"{int(hors.sum())} valeurs hors de la plage plausible ({T_MIN_PLAUSIBLE} / {T_MAX_PLAUSIBLE} °C).")
    trous = np.isnan(t)
    if trous.any():
        s = pd.Series(t)
        longueur_max = s.isna().astype(int).groupby(s.notna().cumsum()).sum().max()
        if longueur_max > trou_max:
            raise ValueError(f"Trou de {longueur_max} h : au-delà de {trou_max} h, la série est refusée.")
        t = s.interpolate(limit_direction="both").to_numpy()
        avertissements.append(f"{int(trous.sum())} heures manquantes comblées par interpolation.")
    return t


def lire_tableau(df: pd.DataFrame, base_horaire: str = "légale", decalage_ete: int = 2, trou_max: int = 3):
    """
    Interprète un tableau déjà lu (colonnes heure;T ou date;heure;T ou horodatage;T).
    Retourne (t, horodatage légal, décalage, année complète, avertissements).
    """
    avertissements = []
    cols = [c.strip().lower() for c in df.columns]
    df.columns = cols
    if "date" in cols and "heure" in cols:                        # relevé date;heure;T
        horo = pd.to_datetime(df["date"].astype(str) + " " + df["heure"].astype(str), dayfirst=False)
        t = _nombres(df[cols[-1]])
    elif cols[0] in ("heure", "h") and len(df) in NB_HEURES_ANNEE:  # année type heure;T
        t = _nombres(df[cols[1]])
        horo = None
    else:                                                          # horodatage;T
        horo = pd.to_datetime(df[cols[0]], dayfirst=True)
        t = _nombres(df[cols[1]])
    t = _controler(t, avertissements, trou_max)

    if horo is None:                                               # année type en UTC
        decalage = decalage_ete if base_horaire == "UTC" else 0
        horo = pd.date_range(f"{ANNEE_TYPE}-01-01", periods=len(t), freq="h") + pd.Timedelta(hours=decalage)
        return t, horo, decalage, True, avertissements
    ordre = np.argsort(horo.to_numpy())
    horo, t = pd.DatetimeIndex(horo[ordre]), t[ordre]
    if base_horaire == "UTC":
        horo = horo + pd.Timedelta(hours=decalage_ete)
    return t, horo, 0, len(t) in NB_HEURES_ANNEE, avertissements


def charger_catalogue() -> pd.DataFrame:
    return pd.DataFrame(lire_csv(CHEMIN_CATALOGUE))


def charger_serie(ligne: dict, decalage_ete: int = 2) -> SerieMeteo:
    """Charge un fichier enregistré décrit par une ligne du catalogue."""
    df = pd.read_csv(os.path.join(RACINE, ligne["chemin"]), sep=";", dtype=str)
    t, horo, decalage, complete, avert = lire_tableau(df, ligne["base_horaire"], decalage_ete)
    return SerieMeteo(ligne["id"], f"{ligne['zone']} · {ligne['libelle']}", t, horo, decalage, complete,
                      dict(ligne), avert)


def lire_fichier_importe(contenu: bytes, nom: str, base_horaire: str, decalage_ete: int = 2,
                         trou_max: int = 3) -> SerieMeteo:
    """Fichier importé dans la session (séparateur et décimale détectés)."""
    texte = contenu.decode("utf-8-sig", errors="replace")
    sep = ";" if texte.count(";") >= texte.count(",") else ","
    df = pd.read_csv(io.StringIO(texte), sep=sep, dtype=str)
    t, horo, decalage, complete, avert = lire_tableau(df, base_horaire, decalage_ete, trou_max)
    meta = dict(zone="import", type="importé", libelle=nom, station="", periode="", base_horaire=base_horaire,
                source="fichier importé (session)", lien="")
    return SerieMeteo(f"import_{nom}", f"Importé · {nom}", t, horo, decalage, complete, meta, avert)


def serie_depuis_generateur(t, debut: str, libelle: str) -> SerieMeteo:
    """Journée / semaine créée (fichier C), en heure légale à partir de `debut`."""
    horo = pd.date_range(debut, periods=len(t), freq="h")
    meta = dict(zone="créé", type="créé", libelle=libelle, station="", periode="", base_horaire="légale",
                source="onglet Créer", lien="")
    return SerieMeteo("cree_C", f"C · {libelle}", np.asarray(t, float), horo, 0, False, meta, [])
