"""
============================================================
 SÉRIE MÉTÉO — chargement, contrôle, heure légale
============================================================
 Une SerieMeteo est une température fichier horaire avec :
   - ses horodatages en HEURE LÉGALE (toutes les définitions
     jour / nuit / occupation s'y appliquent) ;
   - le décalage UTC → légal (pour la méthode RE2020) ;
   - ses métadonnées (zone, type, station, source…).
 Formats lus :
   « annee_type » : heure;T  (0 → 8759, UTC, fichiers RE2020)
   « date_heure » : date;heure;T  (relevé, heure légale)
============================================================
"""

import io
import os
import re
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
LONGUEUR_NOM_MAX = 80              # nom d'un fichier importé (affiché dans les titres et les boutons)
CARACTERES_INTERDITS = re.compile(r"[<>\[\]{}`*#|:\\]")   # balises, mise en forme Markdown et couleurs Streamlit (:red[…])
AVERTISSEMENT_JOUR_MOIS = "Dates lues au format jour/mois/année (format français)."


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
        return self.horodatage.day_of_week.to_numpy()

    @property
    def jour_annee(self):
        return self.horodatage.day_of_year.to_numpy()      # 1 = 1er janvier


# ============================================================
# LECTURE
# ============================================================

def _nombres(colonne: pd.Series) -> np.ndarray:
    """Températures (virgule ou point décimal) ; cellule vide = trou (comblé ensuite), texte = erreur claire."""
    texte = colonne.astype("string").str.strip().str.replace(",", ".", regex=False)
    valeurs = pd.to_numeric(texte, errors="coerce")
    illisibles = valeurs.isna() & texte.notna() & (texte != "")
    if illisibles.any():
        ligne = int(np.flatnonzero(illisibles.to_numpy())[0])
        raise ValueError(f"Température illisible ligne {ligne + 2} : « {colonne.iloc[ligne]} » (nombre attendu).")
    return valeurs.to_numpy(dtype=float)


def _dates(texte: pd.Series, avertissements: list) -> pd.DatetimeIndex:
    """
    Dates au format ISO (2026-06-01) d'abord, sinon au format français jour/mois/année (01/06/2026), signalé.
    Un format inconnu ou des dates invalides donnent une erreur en français.
    """
    texte = texte.astype(str).str.strip()
    try:
        return pd.DatetimeIndex(pd.to_datetime(texte, format="ISO8601"))
    except (ValueError, TypeError):
        pass
    try:
        dates = pd.DatetimeIndex(pd.to_datetime(texte, dayfirst=True))
    except (ValueError, TypeError) as e:
        raise ValueError(f"Dates illisibles (ex. « {texte.iloc[0]} ») : formats acceptés 2026-06-01 ou "
                         f"01/06/2026, avec l'heure en 14:00.") from e
    avertissements.append(AVERTISSEMENT_JOUR_MOIS)
    return dates


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
    cols = [str(c).strip().lower() for c in df.columns]
    df.columns = cols
    if len(cols) < 2:
        raise ValueError("Le fichier doit avoir au moins deux colonnes (heure;T, date;heure;T ou horodatage;T), "
                         "séparées par « ; » ou « , ».")
    if "date" in cols and "heure" in cols:                        # relevé date;heure;T
        horo = _dates(df["date"].astype(str) + " " + df["heure"].astype(str), avertissements)
        t = _nombres(df[cols[-1]])
    elif cols[0] in ("heure", "h"):                                # année type heure;T
        if len(df) not in NB_HEURES_ANNEE:
            raise ValueError(f"Format heure;T : 8 760 ou 8 784 lignes attendues (une année), {len(df)} trouvées. "
                             "Pour une période courte, utiliser date;heure;T.")
        t = _nombres(df[cols[1]])
        horo = None
    else:                                                          # horodatage;T
        horo = _dates(df[cols[0]], avertissements)
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
    """Fichier importé dans la session (séparateur et décimale détectés). Erreur de format → ValueError en français."""
    nom = nom_affichable(nom)
    texte = contenu.decode("utf-8-sig", errors="replace")
    if not texte.strip():
        raise ValueError("Le fichier est vide.")
    sep = ";" if texte.count(";") >= texte.count(",") else ","
    try:
        df = pd.read_csv(io.StringIO(texte), sep=sep, dtype=str)
    except pd.errors.ParserError as e:
        raise ValueError("Fichier CSV mal formé : le nombre de colonnes varie d'une ligne à l'autre.") from e
    t, horo, decalage, complete, avert = lire_tableau(df, base_horaire, decalage_ete, trou_max)
    meta = dict(zone="import", type="importé", libelle=nom, station="", periode="", base_horaire=base_horaire,
                source="fichier importé (session)", lien="")
    return SerieMeteo(f"import_{nom}", f"Importé · {nom}", t, horo, decalage, complete, meta, avert)


def nom_affichable(nom: str) -> str:
    """Nom d'un fichier importé sans chemin, ni balise, ni mise en forme, limité à LONGUEUR_NOM_MAX caractères."""
    propre = CARACTERES_INTERDITS.sub(" ", os.path.basename(str(nom)))
    propre = re.sub(r"\s+", " ", propre).strip()[:LONGUEUR_NOM_MAX]
    return propre or "fichier"


def serie_depuis_generateur(t, debut: str, libelle: str) -> SerieMeteo:
    """Journée / semaine créée (fichier C), en heure légale à partir de `debut`."""
    horo = pd.date_range(debut, periods=len(t), freq="h")
    meta = dict(zone="créé", type="créé", libelle=libelle, station="", periode="", base_horaire="légale",
                source="onglet Créer", lien="")
    return SerieMeteo("cree_C", f"C · {libelle}", np.asarray(t, float), horo, 0, False, meta, [])
