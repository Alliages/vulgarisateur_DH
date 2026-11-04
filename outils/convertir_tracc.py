"""
Fichiers TRACC → fichiers météo de l'outil
============================================================

Découpe les 6 fichiers « Données climatiques prospectives » (dossier TRACC/, 8 stations chacun) en
48 fichiers au format « annee_type » des fichiers RE2020 (heure;T, 0 → 8759, UTC, virgule décimale) :
  donnees/meteo/TRACC/<zone>/tracc_plus2_0.csv, tracc_plus2_0_vdc.csv, tracc_plus2_7.csv… tracc_plus4_0_vdc.csv

Seule la température à 2 m (T2m) est gardée. Les valeurs ne sont pas corrigées.
La station, le département et les coordonnées viennent des lignes RE2020 du catalogue : les coordonnées
des fichiers TRACC ne sont pas reprises (la longitude de Carpentras y est celle de Marignane).

Le catalogue (config/catalogue_fichiers.csv) reçoit 48 lignes de la famille TRACC. Relancer le script
remplace ces lignes et ces fichiers ; les autres lignes du catalogue ne changent pas.

Lancé à la main : python outils/convertir_tracc.py
"""
import csv
import os
import sys
from collections import defaultdict

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER_SOURCE = os.path.join(RACINE, "TRACC")
CHEMIN_CATALOGUE = os.path.join(RACINE, "config", "catalogue_fichiers.csv")

NB_HEURES = 8760
RECORD_FRANCE = 46.0     # °C, au-delà la valeur est signalée dans la description du fichier
SOURCE = "Données climatiques prospectives (TRACC), data.ademe.fr"
LIEN = "https://data.ademe.fr/datasets?q=climatique&topics=fJZXrdcRGP"

ZONES = {"TRAPPES": "H1a", "NANCY": "H1b", "MACON": "H1c", "RENNES": "H2a",
         "TOURS": "H2b", "AGEN": "H2c", "CARPENTRAS": "H2d", "MARIGNANE": "H3"}

# (fichier source, nom de sortie, réchauffement affiché, vague de chaleur)
SCENARIOS = [
    ("Données climatiques prospectives - France +2.csv", "tracc_plus2_0", "+2 °C", False),
    ("Données climatiques prospectives - France +2 - Vague de chaleur.csv", "tracc_plus2_0_vdc", "+2 °C", True),
    ("Données climatiques prospectives - France +2-7.csv", "tracc_plus2_7", "+2,7 °C", False),
    ("Données climatiques prospectives - France +2-7 - Vague de chaleur.csv", "tracc_plus2_7_vdc", "+2,7 °C", True),
    ("Données climatiques prospectives - France +4.csv", "tracc_plus4_0", "+4 °C", False),
    ("Données climatiques prospectives - France +4 - Vague de chaleur.csv", "tracc_plus4_0_vdc", "+4 °C", True),
]


def lire_stations(chemin):
    """{station: [T2m, …]} dans l'ordre de l'année ; s'arrête si une station est incomplète ou en désordre."""
    series, derniere = defaultdict(list), {}
    with open(chemin, encoding="utf-8", newline="") as f:
        for ligne in csv.DictReader(f, delimiter=";"):
            station = ligne["STATION"]
            instant = (int(ligne["MOIS"]), int(ligne["JOUR"]), int(ligne["HEURE"]))
            if station in derniere and instant <= derniere[station]:
                raise ValueError(f"{os.path.basename(chemin)} : {station}, heures en désordre à {instant}.")
            derniere[station] = instant
            series[station].append(float(ligne["T2m"]))
    if set(series) != set(ZONES):
        raise ValueError(f"{os.path.basename(chemin)} : stations inattendues {sorted(set(series) ^ set(ZONES))}.")
    for station, t in series.items():
        if len(t) != NB_HEURES:
            raise ValueError(f"{os.path.basename(chemin)} : {station}, {len(t)} heures au lieu de {NB_HEURES}.")
    return series


def ecrire_serie(chemin, t):
    """Même forme que les fichiers RE2020 : heure;T, virgule décimale, fin de ligne CRLF."""
    with open(chemin, "w", encoding="ascii", newline="") as f:
        f.write("heure;T\r\n")
        for heure, valeur in enumerate(t):
            f.write(f"{heure};{valeur:.3f}".replace(".", ",") + "\r\n")


def ligne_catalogue(colonnes, ref, zone, nom, rechauffement, vdc, t_max):
    libelle = f"TRACC {rechauffement}" + (" vague de chaleur" if vdc else "")
    description = f"climat prospectif France {rechauffement}" + (", avec vague de chaleur" if vdc else "")
    if t_max > RECORD_FRANCE:
        description += f", maximum {t_max:.1f} °C (valeur de la source, non corrigée)".replace(".", ",")
    valeurs = dict(id=f"{zone}_{nom}", famille="TRACC", zone=zone, type="TRACC", libelle=libelle,
                   station=ref["station"], periode="année type", base_horaire="UTC", format="annee_type",
                   chemin=f"donnees/meteo/TRACC/{zone}/{nom}.csv", description=description, source=SOURCE, lien=LIEN,
                   departement=ref["departement"], latitude=ref["latitude"], longitude=ref["longitude"], emplacement="")
    return [valeurs[c] for c in colonnes]


def main():
    with open(CHEMIN_CATALOGUE, encoding="utf-8", newline="") as f:
        texte = f.read()
    lignes = texte.splitlines()
    colonnes = lignes[0].split(";")
    catalogue = list(csv.DictReader(lignes, delimiter=";"))
    references = {r["zone"]: r for r in catalogue if r["famille"] == "RE2020"}
    gardees = [l for l in lignes if ";TRACC;" not in l]            # relance : les lignes TRACC sont remplacées

    nouvelles = []
    for source, nom, rechauffement, vdc in SCENARIOS:
        series = lire_stations(os.path.join(DOSSIER_SOURCE, source))
        for station, zone in ZONES.items():
            t = series[station]
            ecrire_serie(os.path.join(RACINE, "donnees", "meteo", "TRACC", zone, f"{nom}.csv"), t)
            nouvelles.append(ligne_catalogue(colonnes, references[zone], zone, nom, rechauffement, vdc, max(t)))
        print(f"{nom} : {len(series)} stations")

    nouvelles.sort(key=lambda l: l[0])
    with open(CHEMIN_CATALOGUE, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(gardees) + "\n")
        csv.writer(f, delimiter=";", lineterminator="\n").writerows(nouvelles)
    print(f"{len(nouvelles)} lignes TRACC dans le catalogue")


if __name__ == "__main__":
    sys.exit(main())
