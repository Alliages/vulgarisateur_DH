"""
============================================================
 CONVERTIR_DOCS — Word + Excel → pages Markdown + CSV
============================================================
 Lancé par la GitHub Action convertir_docs.yml (et exécutable en
 local) :
   docs/sources/documentation.docx → docs/pages/NN_<titre>.md
                                     (une page par style « Titre 1 »)
   docs/sources/hypotheses.xlsx    → config/hypotheses.csv
                                     config/indicateurs.csv
 Contrôles : statuts autorisés, identifiants uniques, [[hyp:…]]
 existants, liens au bon format, valeurs non vides.

 Usage : python3 outils/convertir_docs.py
============================================================
"""

import csv
import os
import re
import sys
import unicodedata

import mammoth
from openpyxl import load_workbook

# ============================================================
# PARAMÈTRES
# ============================================================
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_WORD = os.path.join(RACINE, "docs", "sources", "documentation.docx")
SOURCE_EXCEL = os.path.join(RACINE, "docs", "sources", "hypotheses.xlsx")
DOSSIER_PAGES = os.path.join(RACINE, "docs", "pages")
SORTIES_CSV = {"hypotheses": os.path.join(RACINE, "config", "hypotheses.csv"),
               "indicateurs": os.path.join(RACINE, "config", "indicateurs.csv")}
STATUTS_AUTORISES = {"sourcé", "provisoire", "à préciser", "hypothèse"}
MOTIF_REPERE = re.compile(r"\[\[hyp:([a-z0-9_]+)\]\]")
MOTIF_LIEN = re.compile(r"^https?://\S+$")


# ============================================================
# OUTILS
# ============================================================

def identifiant(titre: str) -> str:
    """« Ce que mesure l'outil » → « ce_que_mesure_l_outil »."""
    t = unicodedata.normalize("NFKD", titre).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_")


def lire_onglet(classeur, nom):
    ws = classeur[nom]
    lignes = list(ws.iter_rows(values_only=True))
    entete = [str(c) for c in lignes[0]]
    return entete, [dict(zip(entete, l)) for l in lignes[1:] if any(v is not None for v in l)]


# ============================================================
# CONVERSIONS
# ============================================================

def convertir_excel(erreurs):
    classeur = load_workbook(SOURCE_EXCEL, data_only=True)
    tables = {}
    for nom, sortie in SORTIES_CSV.items():
        entete, lignes = lire_onglet(classeur, nom)
        ids = [l["id"] for l in lignes]
        if len(ids) != len(set(ids)):
            erreurs.append(f"{nom} : identifiants en double")
        for l in lignes:
            if not l.get("id") or l.get("libelle") in (None, ""):
                erreurs.append(f"{nom} : ligne sans id ou sans libellé ({l})")
            if nom == "hypotheses":
                if l["valeur"] in (None, ""):
                    erreurs.append(f"hypothèse {l['id']} : valeur vide")
                if l["statut"] not in STATUTS_AUTORISES:
                    erreurs.append(f"hypothèse {l['id']} : statut « {l['statut']} » non autorisé")
                if l.get("lien") and not MOTIF_LIEN.match(str(l["lien"])):
                    erreurs.append(f"hypothèse {l['id']} : lien mal formé")
        with open(sortie, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=entete, delimiter=";")
            w.writeheader()
            for l in lignes:
                w.writerow({k: ("" if v is None else v) for k, v in l.items()})
        tables[nom] = lignes
    return tables


def convertir_word(ids_hyp, erreurs):
    with open(SOURCE_WORD, "rb") as f:
        markdown = mammoth.convert_to_markdown(f).value
    markdown = markdown.replace("\\", "")                     # mammoth échappe . - ( )
    for repere in MOTIF_REPERE.findall(markdown):
        if repere not in ids_hyp:
            erreurs.append(f"documentation : repère [[hyp:{repere}]] inconnu")
    os.makedirs(DOSSIER_PAGES, exist_ok=True)
    for ancien in os.listdir(DOSSIER_PAGES):
        if ancien.endswith(".md"):
            os.remove(os.path.join(DOSSIER_PAGES, ancien))
    sections = re.split(r"^# ", markdown, flags=re.M)
    n = 0
    for bloc in sections:
        if not bloc.strip():
            continue
        titre, _, corps = bloc.partition("\n")
        n += 1
        nom = f"{n:02d}_{identifiant(titre)}.md"
        with open(os.path.join(DOSSIER_PAGES, nom), "w", encoding="utf-8") as f:
            f.write(f"# {titre.strip()}\n{corps.strip()}\n")
    return n


def main():
    erreurs = []
    tables = convertir_excel(erreurs)
    n_pages = convertir_word({h["id"] for h in tables["hypotheses"]}, erreurs)
    for nom in ("bulle", "libelle"):
        for ind in tables["indicateurs"]:
            for repere in MOTIF_REPERE.findall(str(ind.get(nom) or "")):
                if repere not in {h["id"] for h in tables["hypotheses"]}:
                    erreurs.append(f"indicateur {ind['id']} : repère [[hyp:{repere}]] inconnu")
    print(f"{len(tables['hypotheses'])} hypothèses, {len(tables['indicateurs'])} indicateurs, {n_pages} pages")
    if erreurs:
        print("ERREURS :\n  - " + "\n  - ".join(erreurs))
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
