"""
Seuils des vagues de chaleur par station (Spic, Sdeb, Sint)
============================================================

Méthode Météo-France (Soubeyroux et al., La Météorologie n° 94, 2016) appliquée à la station :
  1. données quotidiennes ouvertes Météo-France (meteo.data.gouv.fr, fichiers « RR-T-Vent ») ;
  2. température moyenne journalière Tm = (TN + TX) / 2, pour TOUS les jours de l'année ;
  3. centiles 99,5 / 97,5 / 95 de Tm sur la période de référence → Spic / Sdeb / Sint.

Entrées (docs/sources/hypotheses.xlsx, source unique) :
  - onglet « hypotheses » : période de référence et centiles (ids vdc_*) ;
  - onglet « stations_vague_chaleur » : une station par zone (numéro de poste, département).
Sorties :
  - même onglet « stations_vague_chaleur » complété (seuils, jours valides, statut) ;
  - config/seuils_vague_chaleur.csv, lu par l'outil.

Erreurs : chaque échec est affiché avec ce qui a échoué, l'URL ou la donnée en cause et une piste
de correction. Dans GitHub, il apparaît aussi en rouge en tête du run (annotation) et dans le
tableau récapitulatif. Une station en échec n'arrête pas les autres.

Lancé à la main par la GitHub Action « Seuils vagues de chaleur » (rien d'automatique).
En local : python outils/calculer_seuils_vdc.py   (accès Internet nécessaire)
"""
import csv
import gzip
import http.client
import io
import json
import os
import re
import socket
import sys
import time
import traceback
import urllib.error
import urllib.request

import numpy as np
import pandas as pd
from openpyxl import load_workbook

# ============================================================
# VARIABLES
# ============================================================
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_EXCEL = os.path.join(RACINE, "docs", "sources", "hypotheses.xlsx")
SORTIE_CSV = os.path.join(RACINE, "config", "seuils_vague_chaleur.csv")
ONGLET_HYP = "hypotheses"
ONGLET_STATIONS = "stations_vague_chaleur"

# Jeu de données Météo-France « Données climatologiques de base - quotidiennes » sur data.gouv.fr
PAGE_JEU_QUOTIDIEN = "https://www.data.gouv.fr/datasets/donnees-climatologiques-de-base-quotidiennes"
API_JEU_QUOTIDIEN = "https://www.data.gouv.fr/api/1/datasets/6569b51ae64326786e4e8e1a/"
# Fichier par département : Q_<dép>_<période>_RR-T-Vent.csv.gz (« previous-1950-AAAA », « latest-… »)
MOTIF_RESSOURCE = r"^Q_{dep}_(previous|latest)-(\d{{4}})-(\d{{4}})_RR-T-Vent\.csv\.gz$"
COLONNES = ["NUM_POSTE", "AAAAMMJJ", "TN", "TX"]
TAILLE_BLOC = 500_000          # lignes lues à la fois (mémoire limitée sur GitHub)

DELAI_RESEAU = 300             # secondes avant abandon d'une requête
ESSAIS = 3                     # tentatives par téléchargement (erreurs passagères seulement)
ATTENTE_ESSAI = 20             # secondes d'attente, multipliées par le numéro de l'essai
CODES_PASSAGERS = {408, 429, 500, 502, 503, 504}   # codes HTTP qui justifient un nouvel essai

TAUX_VALIDE_MIN = 0.90         # sous ce taux de jours valides, la station est marquée « incomplet »
ANNEE_CONTROLE = 2003          # contrôle de bon sens : jours ≥ Spic pendant l'été 2003

DANS_GITHUB = os.environ.get("GITHUB_ACTIONS") == "true"
RESUME_GITHUB = os.environ.get("GITHUB_STEP_SUMMARY")      # fichier du tableau récapitulatif du run


# ============================================================
# AFFICHAGE DES ERREURS
# ============================================================

class ErreurExpliquee(Exception):
    """Erreur prévue : `message` dit ce qui a échoué, `piste` comment corriger."""

    def __init__(self, message, piste=""):
        super().__init__(message)
        self.piste = piste


def signaler(titre, message, piste=""):
    """Affiche une erreur dans le journal ; dans GitHub, l'affiche aussi en annotation rouge."""
    texte = message + (f"\n  → {piste}" if piste else "")
    print(f"  ERREUR : {texte}", flush=True)
    if DANS_GITHUB:
        # Format des annotations GitHub : les retours à la ligne s'écrivent %0A
        print(f"::error title={titre}::{texte.replace('%', '%25').replace(chr(10), '%0A')}", flush=True)


def ecrire_resume(lignes):
    """Tableau récapitulatif affiché sur la page du run GitHub (rien en local)."""
    if not RESUME_GITHUB:
        return
    with open(RESUME_GITHUB, "a", encoding="utf-8") as f:
        f.write("## Seuils vagues de chaleur\n\n")
        f.write(f"| Zone | Station | Spic | Sdeb | Sint | Jours valides | Statut | Jours ≥ Spic été {ANNEE_CONTROLE} | Erreur |\n")
        f.write("|---|---|---|---|---|---|---|---|---|\n")
        for l in lignes:
            if "erreur" in l:                      # station en échec : seuils vides
                erreur = l["erreur"].replace("|", "/").replace("\n", "<br>")
                f.write(f"| {l['zone']} | {l['station']} |  |  |  |  | **échec** |  | {erreur} |\n")
            else:
                f.write(f"| {l['zone']} | {l['station']} | {l['spic']} | {l['sdeb']} | {l['sint']} | "
                        f"{l['jours_valides']} ({l['taux_valide']:.0%}) | {l['statut']} | {l['controle']} |  |\n")


# ============================================================
# LECTURE DES PARAMÈTRES (Excel)
# ============================================================

def lire_parametres(classeur):
    """Période de référence et centiles, depuis l'onglet des hypothèses."""
    ws = classeur[ONGLET_HYP]
    valeurs = {r[0]: r[2] for r in ws.iter_rows(min_row=2, values_only=True) if r[0]}
    ids = ["vdc_ref_debut", "vdc_ref_fin", "vdc_centile_pic", "vdc_centile_debut", "vdc_centile_interruption"]
    manquants = [i for i in ids if valeurs.get(i) is None]
    if manquants:
        raise ErreurExpliquee(f"hypothèses absentes ou vides : {', '.join(manquants)}",
                              f"les ajouter dans l'onglet « {ONGLET_HYP} » de docs/sources/hypotheses.xlsx")
    return {
        "debut": int(valeurs["vdc_ref_debut"]),
        "fin": int(valeurs["vdc_ref_fin"]),
        "centiles": {"spic": float(valeurs["vdc_centile_pic"]),
                     "sdeb": float(valeurs["vdc_centile_debut"]),
                     "sint": float(valeurs["vdc_centile_interruption"])},
    }


def lire_stations(classeur):
    """Liste des stations : {ligne Excel, zone, station, numero_poste, departement}."""
    ws = classeur[ONGLET_STATIONS]
    entete = [c.value for c in ws[1]]
    stations = []
    for i, ligne in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if ligne[0] is None:
            continue
        d = dict(zip(entete, ligne))
        d["ligne"] = i
        d["numero_poste"] = str(d["numero_poste"]).zfill(8)
        d["departement"] = str(d["departement"]).zfill(2)
        stations.append(d)
    return entete, stations


# ============================================================
# TÉLÉCHARGEMENT (data.gouv.fr)
# ============================================================

def telecharger(url, quoi):
    """
    Contenu brut d'une URL. Les erreurs passagères (serveur occupé, coupure, délai dépassé,
    fichier tronqué) sont retentées ; les autres sont signalées tout de suite, avec une piste.
    """
    for essai in range(1, ESSAIS + 1):
        debut = time.time()
        try:
            with urllib.request.urlopen(url, timeout=DELAI_RESEAU) as r:
                donnees = r.read()
                attendu = r.headers.get("Content-Length")
            if attendu and len(donnees) != int(attendu):
                raise http.client.IncompleteRead(donnees, int(attendu) - len(donnees))
            print(f"    {quoi} : {len(donnees) / 1e6:.1f} Mo en {time.time() - debut:.0f} s", flush=True)
            return donnees
        except urllib.error.HTTPError as e:
            cause, passagere = f"HTTP {e.code} {e.reason}", e.code in CODES_PASSAGERS
        except urllib.error.URLError as e:
            cause, passagere = f"réseau injoignable ({e.reason})", True
        except (socket.timeout, TimeoutError):
            cause, passagere = f"délai de {DELAI_RESEAU} s dépassé", True
        except (http.client.IncompleteRead, ConnectionError) as e:
            cause, passagere = f"téléchargement interrompu ({type(e).__name__})", True

        print(f"    essai {essai}/{ESSAIS} échoué : {cause}", flush=True)
        if not passagere or essai == ESSAIS:
            if "404" in cause:
                piste = (f"le fichier a sans doute été renommé ou remplacé par Météo-France ; "
                         f"vérifier sur {PAGE_JEU_QUOTIDIEN} puis relancer")
            elif passagere:
                piste = "data.gouv.fr est indisponible ou lent : relancer l'Action plus tard"
            else:
                piste = f"vérifier l'adresse sur {PAGE_JEU_QUOTIDIEN}"
            raise ErreurExpliquee(f"{quoi} impossible après {essai} essai(s) : {cause}\n  URL : {url}", piste)
        time.sleep(ATTENTE_ESSAI * essai)


def lister_ressources():
    """Liste des fichiers du jeu de données (lue une seule fois pour toutes les stations)."""
    brut = telecharger(API_JEU_QUOTIDIEN, "liste des fichiers data.gouv.fr")
    try:
        return json.loads(brut)["resources"]
    except (ValueError, KeyError) as e:
        raise ErreurExpliquee(
            f"réponse inattendue de l'API data.gouv.fr ({type(e).__name__}) ; début : {brut[:200]!r}",
            "l'API a peut-être changé : ouvrir l'URL de l'API dans un navigateur et vérifier le champ « resources »")


def lister_fichiers(ressources, departement, debut, fin):
    """URL des fichiers du département qui recouvrent la période [debut, fin]."""
    motif = re.compile(MOTIF_RESSOURCE.format(dep=departement))
    urls, du_departement = [], []
    for res in ressources:
        nom = os.path.basename(res.get("url", ""))
        if nom.startswith(f"Q_{departement}_") or res.get("title", "").startswith(f"Q_{departement}_"):
            du_departement.append(res.get("title") or nom)
        m = motif.match(res.get("title", "")) or motif.match(nom)
        if m and int(m.group(2)) <= fin and int(m.group(3)) >= debut:
            urls.append(res["url"])
    if urls:
        return urls
    if du_departement:
        raise ErreurExpliquee(
            f"département {departement} : aucun fichier « RR-T-Vent » ne couvre {debut}-{fin} ; "
            f"fichiers trouvés : {', '.join(sorted(du_departement))}",
            "si le nom des fichiers a changé, adapter MOTIF_RESSOURCE dans outils/calculer_seuils_vdc.py")
    raise ErreurExpliquee(
        f"département {departement} : aucun fichier dans le jeu de données ({len(ressources)} fichiers lus)",
        f"vérifier la colonne « departement » de l'onglet « {ONGLET_STATIONS} »")


def lire_station(urls, numero_poste, debut, fin):
    """TN et TX quotidiens d'une station sur la période, lus par blocs pour limiter la mémoire."""
    morceaux, postes_vus = [], {}
    for url in urls:
        nom = os.path.basename(url)
        brut = telecharger(url, f"téléchargement {nom}")
        try:
            with gzip.open(io.BytesIO(brut), "rt", encoding="utf-8") as f:
                entete = f.readline().strip().split(";")
                absentes = [c for c in COLONNES if c not in entete]
                if absentes:
                    raise ErreurExpliquee(
                        f"{nom} : colonnes {absentes} absentes ; colonnes présentes : {entete}",
                        "le format Météo-France a changé : adapter COLONNES dans outils/calculer_seuils_vdc.py")
                f.seek(0)
                for bloc in pd.read_csv(f, sep=";", usecols=COLONNES, dtype={"NUM_POSTE": str},
                                        chunksize=TAILLE_BLOC):
                    postes = bloc["NUM_POSTE"].str.zfill(8)
                    postes_vus.update(dict.fromkeys(postes.unique()))
                    bloc = bloc[postes == numero_poste]
                    if not bloc.empty:
                        morceaux.append(bloc)
        except (OSError, EOFError, UnicodeDecodeError, pd.errors.ParserError) as e:
            raise ErreurExpliquee(
                f"{nom} illisible ({type(e).__name__} : {e}) ; début du fichier : {brut[:80]!r}",
                "fichier corrompu ou page d'erreur au lieu du .gz : relancer l'Action")

    if not morceaux:
        exemples = ", ".join(sorted(postes_vus)[:15])
        raise ErreurExpliquee(
            f"station {numero_poste} absente des fichiers ({len(postes_vus)} postes lus, par ex. {exemples})",
            f"vérifier « numero_poste » dans l'onglet « {ONGLET_STATIONS} » (8 chiffres, département en tête)")
    df = pd.concat(morceaux)
    df["date"] = pd.to_datetime(df["AAAAMMJJ"].astype(str), format="%Y%m%d")
    periode = df[(df["date"].dt.year >= debut) & (df["date"].dt.year <= fin)]
    if periode.empty:
        raise ErreurExpliquee(
            f"station {numero_poste} : aucune donnée sur {debut}-{fin} "
            f"(données du {df['date'].min():%d/%m/%Y} au {df['date'].max():%d/%m/%Y})",
            "choisir une station voisine ouverte sur toute la période de référence")
    return periode.drop_duplicates("date").set_index("date")[["TN", "TX"]].sort_index()


# ============================================================
# CALCUL (sans réseau : testé dans tests/test_seuils_vdc.py)
# ============================================================

def calculer_seuils(tn_tx, debut, fin, centiles):
    """
    Seuils d'une station à partir d'un tableau quotidien (index = dates, colonnes TN et TX).
    Tm = (TN + TX) / 2 ; un jour sans TN ou sans TX est écarté.
    Renvoie les seuils (°C, 1 décimale), le nombre de jours valides et le taux de complétude.
    """
    tm = ((tn_tx["TN"] + tn_tx["TX"]) / 2).dropna()
    if tm.empty:
        raise ErreurExpliquee("aucun jour avec TN et TX renseignés sur la période",
                              "choisir une station qui mesure les températures")
    jours_attendus = len(pd.date_range(f"{debut}-01-01", f"{fin}-12-31", freq="D"))
    seuils = {nom: round(float(np.percentile(tm, c)), 1) for nom, c in centiles.items()}
    return seuils, len(tm), len(tm) / jours_attendus, tm


def jours_au_dessus(tm, seuil, annee):
    """Nombre de jours de l'été (juin-août) de l'année où Tm ≥ seuil (contrôle de bon sens)."""
    ete = tm[(tm.index.year == annee) & (tm.index.month.isin([6, 7, 8]))]
    return int((ete >= seuil).sum())


# ============================================================
# ÉCRITURE
# ============================================================

def ecrire(classeur, entete, resultats):
    """Complète l'onglet des stations et écrit le CSV lu par l'outil."""
    ws = classeur[ONGLET_STATIONS]
    col = {nom: entete.index(nom) + 1 for nom in entete}
    for s in resultats:
        for nom in ("spic", "sdeb", "sint", "jours_valides", "statut"):
            ws.cell(row=s["ligne"], column=col[nom], value=s[nom])
    classeur.save(SOURCE_EXCEL)

    champs = ["zone", "station", "numero_poste", "spic", "sdeb", "sint",
              "periode", "jours_valides", "taux_valide", "statut"]
    with open(SORTIE_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=champs, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(resultats)


# ============================================================
# PROGRAMME
# ============================================================

def traiter_station(s, ressources, p):
    """Seuils d'une station ; lève ErreurExpliquee (prévue) ou une autre exception (imprévue)."""
    urls = lister_fichiers(ressources, s["departement"], p["debut"], p["fin"])
    tn_tx = lire_station(urls, s["numero_poste"], p["debut"], p["fin"])
    seuils, n, taux, tm = calculer_seuils(tn_tx, p["debut"], p["fin"], p["centiles"])
    statut = "calculé" if taux >= TAUX_VALIDE_MIN else "incomplet"
    controle = jours_au_dessus(tm, seuils["spic"], ANNEE_CONTROLE)
    print(f"  Spic {seuils['spic']} · Sdeb {seuils['sdeb']} · Sint {seuils['sint']} °C · "
          f"{n} jours ({taux:.0%}) · {statut} · {controle} j ≥ Spic à l'été {ANNEE_CONTROLE}")
    if statut == "incomplet":
        print(f"  ATTENTION : moins de {TAUX_VALIDE_MIN:.0%} de jours valides, seuils peu fiables")
    return {**s, **seuils, "periode": f"{p['debut']}-{p['fin']}", "jours_valides": n,
            "taux_valide": round(taux, 3), "statut": statut, "controle": controle}


def main():
    classeur = load_workbook(SOURCE_EXCEL)
    p = lire_parametres(classeur)
    entete, stations = lire_stations(classeur)
    print(f"Période {p['debut']}-{p['fin']}, centiles {p['centiles']}, {len(stations)} stations", flush=True)

    # Liste des fichiers : sans elle, aucune station ne peut être traitée → arrêt immédiat
    try:
        ressources = lister_ressources()
    except ErreurExpliquee as e:
        signaler("Liste des fichiers data.gouv.fr", str(e), e.piste)
        ecrire_resume([{**s, "erreur": str(e)} for s in stations])
        sys.exit(1)
    print(f"{len(ressources)} fichiers dans le jeu de données Météo-France", flush=True)

    resultats, recap, erreurs = [], [], []
    for s in stations:
        print(f"\n{s['zone']} {s['station']} ({s['numero_poste']}, dép. {s['departement']})", flush=True)
        try:
            r = traiter_station(s, ressources, p)
            resultats.append(r)
            recap.append(r)
        except ErreurExpliquee as e:               # erreur prévue : message et piste
            signaler(f"{s['zone']} {s['station']}", str(e), e.piste)
            erreurs.append(f"{s['zone']} {s['station']} : {e}")
            recap.append({**s, "erreur": f"{e}\n→ {e.piste}" if e.piste else str(e)})
        except Exception as e:                     # erreur imprévue : détail complet pour la corriger
            print(traceback.format_exc(), flush=True)
            signaler(f"{s['zone']} {s['station']}", f"erreur imprévue {type(e).__name__} : {e}",
                     "voir le détail (traceback) juste au-dessus dans le journal")
            erreurs.append(f"{s['zone']} {s['station']} : {type(e).__name__} : {e}")
            recap.append({**s, "erreur": f"{type(e).__name__} : {e}"})

    if resultats:
        ecrire(classeur, entete, resultats)
    ecrire_resume(recap)
    print(f"\n{len(resultats)} station(s) calculée(s), {len(erreurs)} en échec")
    if erreurs:
        print("Stations en échec :\n  " + "\n  ".join(erreurs))
        sys.exit(1)


if __name__ == "__main__":
    main()
