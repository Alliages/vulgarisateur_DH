"""
============================================================
 CONSTRUCTION DE L'EXCEL « DH basic / DH réel » (zone H1a)
============================================================
 Génère un classeur Excel qui recalcule, en FORMULES, les DH
 d'une série horaire de 8760 températures (fichier météo RE2020
 du dépôt zones-climatiques-re2020), pour comparaison avec le
 module Python dh_re2020.calculer_dh.

   DH basic : seuils fixes 26 °C nuit / 28 °C jour, toutes heures.
   DH réel  : méthode Th-BCE 2020 (annexe III, fiche 13.5) —
              seuil adaptatif (2543)-(2544), période θrm ≥ 16 °C,
              occupation conventionnelle logement.

 Les valeurs Python sont écrites en dur dans l'onglet Résultats
 (valeurs de référence), à côté des formules Excel.

 Usage : python3 construire_excel_dh.py
============================================================
"""

import csv
import numpy as np
from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.comments import Comment
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName

from dh_re2020 import calculer_dh

# ============================================================
# PARAMÈTRES
# ============================================================

# --- Fichiers ---------------------------------------------------
ZONE = "H1a"
CSV_METEO = f"/root/zones-climatiques-re2020/data/meteo/meteo_{ZONE}.csv"
SORTIE = f"/home/claude/dh_re2020/DH_basic_reel_{ZONE}.xlsx"
SOURCE_METEO = ("github.com/Alliages/zones-climatiques-re2020, data/meteo/meteo_H1a.csv "
                "(scénarios météo RE2020 DHUP / Météo-France, colonne th_d = Th-D caniculaire)")

# --- Paramètres de calcul (nom défini, valeur, unité, description, source) ---
PARAMETRES = [
    ("SCENARIO",    "Th-D", "",   "Scénario météo utilisé (Th-D ou Th-BC)",
     "Th-D = scénario confort d'été RE2020"),
    ("SEUIL_BAS",   26.0, "°C",   "θiifr+ : consigne de refroidissement = seuil de nuit et plancher",
     "Annexe III, fiche 13.5, (2543)-(2544)"),
    ("SEUIL_HAUT",  28.0, "°C",   "θiifr+ + Δθop_min_max : plafond du seuil de jour",
     "Annexe III, fiche 13.5, Δθop_min_max = 2 °C"),
    ("PENTE",       0.33, "-",    "Pente de la droite de confort adaptatif",
     "Annexe III, (2543)"),
    ("ORDONNEE",    18.8, "°C",   "Ordonnée de la droite de confort adaptatif",
     "Annexe III, (2543)"),
    ("DELTA_CAT",   2.0,  "°C",   "Δθop_inc : catégorie d'ambiance 1 (2 / 3 / 4 °C pour cat. 1 / 2 / 3)",
     "Annexe III, tableau 340 : Cat_amb = 1 pour tous les usages"),
    ("ALPHA",       0.8,  "-",    "Coefficient de la moyenne glissante θrm",
     "Annexe III, fiche climat, formule (1)"),
    ("THETA_INIT",  0.0,  "°C",   "θrm du premier jour de l'année",
     "Annexe III, formule (1) : « θrm(j) = 0 »"),
    ("SEUIL_RM",    16.0, "°C",   "θrm minimale de la période de confort adaptatif",
     "Annexe III, fiche climat, formule (2)"),
    ("H_DEBUT",     6,    "h",    "Début du jour (heure légale, incluse)",
     "Annexe III, (2544) : 6 < hleg ≤ 22 en heure de fin de pas"),
    ("H_FIN",       22,   "h",    "Fin du jour (heure légale, exclue)",
     "Annexe III, (2544)"),
    ("DECALAGE",    2,    "h",    "Heure légale = heure du fichier (UTC) + décalage (été = 2)",
     "Annexe III, fiche climat : Hleg = IHJ + EHLO"),
    ("OCCUPATION",  1,    "0/1",  "1 = occupation logement RE2020 pour le DH réel ; 0 = toujours occupé",
     "Scénario CEREMA (non relu dans l'annexe)"),
    ("ABS_DEBUT",   10,   "h",    "Début d'absence (lun., mar., mer., jeu., ven.)",
     "CEREMA, webinaire RE2020 confort d'été"),
    ("ABS_FIN",     18,   "h",    "Fin d'absence lun., mar., jeu., ven. (exclue)",
     "CEREMA, webinaire RE2020 confort d'été"),
    ("ABS_FIN_MER", 14,   "h",    "Fin d'absence le mercredi (exclue)",
     "CEREMA, webinaire RE2020 confort d'été"),
]
LIGNE_PREMIER_PARAM = 4          # première ligne des paramètres dans l'onglet

# --- Dimensions ---------------------------------------------------
NB_HEURES = 8760
NB_JOURS = 365
L0 = 2                           # première ligne de données (Horaire, Journalier)
LH_FIN = L0 + NB_HEURES - 1      # 8761
LJ_FIN = L0 + NB_JOURS - 1       # 366
ANNEE_LUNDI = 2018               # année débutant un lundi (convention Th-BCE), pour les dates

# --- Mise en forme ---------------------------------------------------
POLICE = "Arial"
BLEU = "0000FF"                  # saisies
VERT = "008000"                  # liens vers un autre onglet
JAUNE = "FFFF00"                 # paramètres modifiables
GRIS = "D9D9D9"                  # en-têtes
ROUGE_CLAIR = "FFC7CE"           # écart Excel / Python non nul
TOLERANCE = 1e-6                 # écart toléré Excel / Python

F_NORMAL = Font(name=POLICE, size=10)
F_GRAS = Font(name=POLICE, size=10, bold=True)
F_TITRE = Font(name=POLICE, size=14, bold=True)
F_SAISIE = Font(name=POLICE, size=10, color=BLEU)
F_LIEN = Font(name=POLICE, size=10, color=VERT)
REMPLI_ENTETE = PatternFill("solid", fgColor=GRIS)
REMPLI_PARAM = PatternFill("solid", fgColor=JAUNE)
BORDURE = Border(bottom=Side(style="thin", color="808080"))
ENVELOPPE = Alignment(wrap_text=True, vertical="top")


# ============================================================
# OUTILS
# ============================================================

def lire_meteo(chemin):
    """Lit le CSV « heure;th_bc;th_d » (virgule décimale)."""
    with open(chemin, encoding="utf-8") as f:
        lignes = list(csv.reader(f, delimiter=";"))[1:]
    heures = [int(l[0]) for l in lignes]
    th_bc = [float(l[1].replace(",", ".")) for l in lignes]
    th_d = [float(l[2].replace(",", ".")) for l in lignes]
    assert heures == list(range(NB_HEURES)), "heures inattendues dans le CSV"
    return heures, th_bc, th_d


def entete(ws, colonnes, ligne=1):
    """Écrit une ligne d'en-tête (texte, largeur) en gras sur fond gris."""
    for i, (texte, largeur) in enumerate(colonnes, start=1):
        c = ws.cell(row=ligne, column=i, value=texte)
        c.font, c.fill, c.alignment, c.border = F_GRAS, REMPLI_ENTETE, Alignment(wrap_text=True, vertical="center"), BORDURE
        ws.column_dimensions[get_column_letter(i)].width = largeur
    ws.row_dimensions[ligne].height = 42


def nom_defini(wb, nom, onglet, cellule):
    """Crée un nom défini classeur (ex. SEUIL_BAS → Paramètres!$C$5)."""
    wb.defined_names[nom] = DefinedName(nom, attr_text=f"'{onglet}'!{cellule}")


# ============================================================
# CALCUL PYTHON DE RÉFÉRENCE
# ============================================================

def references_python(th_d):
    """Valeurs calculer_dh avec les paramètres par défaut de l'Excel."""
    p = {nom: val for nom, val, *_ in PARAMETRES}
    t = np.array(th_d)
    communs = dict(seuil_bas=p["SEUIL_BAS"], seuil_haut=p["SEUIL_HAUT"],
                   decalage_heure=p["DECALAGE"],
                   heure_debut_jour=p["H_DEBUT"], heure_fin_jour=p["H_FIN"], details=True)
    basic = calculer_dh(t, **communs)
    reel = calculer_dh(t, t, occupation="logement_re2020", **communs)
    jours = np.flatnonzero(reel["periode_adaptative"])
    return basic, reel, int(jours[0]), int(jours[-1])


# ============================================================
# CONSTRUCTION DU CLASSEUR
# ============================================================

def main():
    heures, th_bc, th_d = lire_meteo(CSV_METEO)
    basic, reel, premier_py, dernier_py = references_python(th_d)

    wb = Workbook()
    ws_lire = wb.active
    ws_lire.title = "Lisez-moi"
    ws_par = wb.create_sheet("Paramètres")
    ws_h = wb.create_sheet("Horaire")
    ws_j = wb.create_sheet("Journalier")
    ws_r = wb.create_sheet("Résultats")

    # ---------------------------------------------------------
    # Onglet Paramètres
    # ---------------------------------------------------------
    ws_par["A1"] = f"Paramètres du calcul DH — zone {ZONE}"
    ws_par["A1"].font = F_TITRE
    ws_par["A2"] = "Cellules jaunes à texte bleu : modifiables. Les noms (col. A) sont utilisés dans les formules."
    ws_par["A2"].font = F_NORMAL
    entete(ws_par, [("Nom", 14), ("Description", 62), ("Valeur", 10), ("Unité", 7), ("Source", 58)],
           ligne=LIGNE_PREMIER_PARAM - 1)
    for i, (nom, valeur, unite, description, source) in enumerate(PARAMETRES):
        ligne = LIGNE_PREMIER_PARAM + i
        ws_par.cell(row=ligne, column=1, value=nom).font = F_GRAS
        ws_par.cell(row=ligne, column=2, value=description).font = F_NORMAL
        c = ws_par.cell(row=ligne, column=3, value=valeur)
        c.font, c.fill = F_SAISIE, REMPLI_PARAM
        ws_par.cell(row=ligne, column=4, value=unite).font = F_NORMAL
        ws_par.cell(row=ligne, column=5, value=source).font = F_NORMAL
        nom_defini(wb, nom, "Paramètres", f"$C${ligne}")

    # ---------------------------------------------------------
    # Onglet Horaire (8760 lignes)
    # ---------------------------------------------------------
    cols_h = [
        ("Heure (indice fichier, UTC)", 11),       # A
        ("T ext Th-BC (°C)", 10),                  # B
        ("T ext Th-D (°C)", 10),                   # C
        ("T utilisée (°C)", 10),                   # D
        ("Jour j (0-364)", 8),                     # E
        ("Heure légale", 8),                       # F
        ("Jour semaine (1 = lundi)", 9),           # G
        ("Jour (1) / nuit (0)", 8),                # H
        ("Occupé (1/0)", 8),                       # I
        ("Seuil basic (°C)", 9),                   # J
        ("DH basic (°C.h)", 9),                    # K
        ("Inconfort basic (h)", 9),                # L
        ("θrm du jour (°C)", 9),                   # M
        ("Période adaptative (1/0)", 10),          # N
        ("Seuil réel (°C)", 9),                    # O
        ("Heure retenue réel (1/0)", 10),          # P
        ("DH réel (°C.h)", 9),                     # Q
        ("Inconfort réel (h)", 9),                 # R
    ]
    entete(ws_h, cols_h)
    jr = f"$A${L0}:$A${LJ_FIN}"                    # plages Journalier
    rng_rm = f"Journalier!$C${L0}:$C${LJ_FIN}"
    rng_per = f"Journalier!$D${L0}:$D${LJ_FIN}"
    rng_seuil = f"Journalier!$F${L0}:$F${LJ_FIN}"

    for k in range(NB_HEURES):
        r = L0 + k
        ws_h.cell(row=r, column=1, value=heures[k]).font = F_SAISIE
        ws_h.cell(row=r, column=2, value=th_bc[k]).font = F_SAISIE
        ws_h.cell(row=r, column=3, value=th_d[k]).font = F_SAISIE
        formules = [
            f'=IF(SCENARIO="Th-BC",B{r},C{r})',                                   # D
            f"=INT(A{r}/24)",                                                       # E
            f"=MOD(A{r}+DECALAGE,24)",                                              # F
            f"=MOD(INT((A{r}+DECALAGE)/24),7)+1",                                   # G
            f"=IF(AND(F{r}>=H_DEBUT,F{r}<H_FIN),1,0)",                              # H
            f"=IF(OCCUPATION=0,1,IF(G{r}>=6,1,IF(AND(F{r}>=ABS_DEBUT,"
            f"F{r}<IF(G{r}=3,ABS_FIN_MER,ABS_FIN)),0,1)))",                        # I
            f"=IF(H{r}=1,SEUIL_HAUT,SEUIL_BAS)",                                    # J
            f"=MAX(0,D{r}-J{r})",                                                   # K
            f"=IF(D{r}>=J{r},1,0)",                                                 # L
            f"=INDEX({rng_rm},E{r}+1)",                                             # M
            f"=INDEX({rng_per},E{r}+1)",                                            # N
            f"=IF(H{r}=1,INDEX({rng_seuil},E{r}+1),SEUIL_BAS)",                     # O
            f"=I{r}*N{r}",                                                          # P
            f"=MAX(0,D{r}-O{r})*P{r}",                                              # Q
            f"=IF(AND(P{r}=1,D{r}>=O{r}),1,0)",                                     # R
        ]
        for i, f in enumerate(formules, start=4):
            c = ws_h.cell(row=r, column=i, value=f)
            c.font = F_LIEN if i in (13, 14, 15) else F_NORMAL
    for col in "BCDJKMOQ":
        for cell in ws_h[f"{col}{L0}:{col}{LH_FIN}"]:
            cell[0].number_format = "0.00"
    ws_h.freeze_panes = "B2"
    ws_h["A1"].comment = Comment(SOURCE_METEO, "Claude")

    # ---------------------------------------------------------
    # Onglet Journalier (365 lignes)
    # ---------------------------------------------------------
    cols_j = [
        ("Jour j (0-364)", 8),                     # A
        ("T ext moyenne du jour j (°C)", 11),      # B
        ("θrm(j) (°C)", 9),                        # C
        ("Période adaptative (1/0)", 10),          # D
        ("θop_inc_max (°C) (2543)", 11),           # E
        ("Seuil jour réel (°C) (2544)", 11),       # F
        ("DH basic du jour (°C.h)", 10),           # G
        ("DH réel du jour (°C.h)", 10),            # H
        ("Date indicative", 10),                   # I
    ]
    entete(ws_j, cols_j)
    plage_d = f"Horaire!$D${L0}:$D${LH_FIN}"
    plage_k = f"Horaire!$K${L0}:$K${LH_FIN}"
    plage_q = f"Horaire!$Q${L0}:$Q${LH_FIN}"
    for j in range(NB_JOURS):
        r = L0 + j
        ws_j.cell(row=r, column=1, value=j).font = F_SAISIE
        debut, fin = f"A{r}*24+1", f"A{r}*24+24"
        formules = [
            f"=AVERAGE(INDEX({plage_d},{debut}):INDEX({plage_d},{fin}))",                     # B
            "=THETA_INIT" if j == 0 else f"=ALPHA*C{r-1}+(1-ALPHA)*B{r-1}",                   # C
            f"=IF(AND(A{r}>=PREMIER_JOUR,A{r}<=DERNIER_JOUR),1,0)",                           # D
            f"=MAX(SEUIL_BAS,PENTE*C{r}+ORDONNEE+DELTA_CAT)",                                 # E
            f"=MIN(SEUIL_HAUT,E{r})",                                                         # F
            f"=SUM(INDEX({plage_k},{debut}):INDEX({plage_k},{fin}))",                         # G
            f"=SUM(INDEX({plage_q},{debut}):INDEX({plage_q},{fin}))",                         # H
            f"=DATE({ANNEE_LUNDI},1,1)+A{r}",                                                 # I
        ]
        for i, f in enumerate(formules, start=2):
            ws_j.cell(row=r, column=i, value=f).font = F_LIEN if i in (2, 7, 8) else F_NORMAL
        for col in "BCEFGH":
            ws_j[f"{col}{r}"].number_format = "0.00"
        ws_j[f"I{r}"].number_format = "d mmm"
    ws_j["C1"].comment = Comment("θrm(j) = ALPHA × θrm(j−1) + (1 − ALPHA) × Tmoy(j−1) — annexe III, formule (1)", "Claude")
    ws_j["I1"].comment = Comment(f"Année {ANNEE_LUNDI} : débute un lundi comme l'année conventionnelle Th-BCE. Date indicative.", "Claude")
    ws_j.freeze_panes = "B2"

    # Graphique : DH par jour
    graph = LineChart()
    graph.title = "DH par jour — basic et réel"
    graph.y_axis.title = "°C.h"
    graph.x_axis.title = "Jour de l'année"
    graph.height, graph.width = 9, 22
    graph.add_data(Reference(ws_j, min_col=7, max_col=8, min_row=1, max_row=LJ_FIN), titles_from_data=True)
    graph.set_categories(Reference(ws_j, min_col=1, min_row=L0, max_row=LJ_FIN))
    ws_j.add_chart(graph, "K2")

    # ---------------------------------------------------------
    # Onglet Résultats
    # ---------------------------------------------------------
    ws_r["A1"] = f"DH basic et DH réel — zone {ZONE}, température fichier {PARAMETRES[0][1]}"
    ws_r["A1"].font = F_TITRE
    ws_r["A2"] = ("Colonnes Python : valeurs de dh_re2020.calculer_dh avec les paramètres par défaut. "
                  "Si vous modifiez un paramètre, l'écart n'est plus nul : relancez le script Python.")
    ws_r["A2"].font = F_NORMAL
    entete(ws_r, [("Indicateur", 34), ("Basic — Excel", 14), ("Basic — Python", 14), ("Écart basic", 11),
                  ("Réel — Excel", 14), ("Réel — Python", 14), ("Écart réel", 11)], ligne=4)
    hh = f"Horaire!$H${L0}:$H${LH_FIN}"
    lignes_res = [
        ("DH total (°C.h)",
         f"=SUM({plage_k})", basic["dh_total"], f"=SUM({plage_q})", reel["dh_total"]),
        ("DH jour (°C.h)",
         f"=SUMIFS({plage_k},{hh},1)", basic["dh_jour"], f"=SUMIFS({plage_q},{hh},1)", reel["dh_jour"]),
        ("DH nuit (°C.h)",
         f"=SUMIFS({plage_k},{hh},0)", basic["dh_nuit"], f"=SUMIFS({plage_q},{hh},0)", reel["dh_nuit"]),
        ("Heures d'inconfort (h)",
         f"=SUM(Horaire!$L${L0}:$L${LH_FIN})", basic["nb_h_inconfort"],
         f"=SUM(Horaire!$R${L0}:$R${LH_FIN})", reel["nb_h_inconfort"]),
    ]
    for i, (lib, f_b, py_b, f_r, py_r) in enumerate(lignes_res):
        r = 5 + i
        ws_r.cell(row=r, column=1, value=lib).font = F_GRAS
        ws_r.cell(row=r, column=2, value=f_b).font = F_LIEN
        ws_r.cell(row=r, column=3, value=float(py_b)).font = F_SAISIE
        ws_r.cell(row=r, column=4, value=f"=B{r}-C{r}").font = F_NORMAL
        ws_r.cell(row=r, column=5, value=f_r).font = F_LIEN
        ws_r.cell(row=r, column=6, value=float(py_r)).font = F_SAISIE
        ws_r.cell(row=r, column=7, value=f"=E{r}-F{r}").font = F_NORMAL
        fmt = "0" if i == 3 else "#,##0.00"
        for col in "BCEF":
            ws_r[f"{col}{r}"].number_format = fmt
        for col in "DG":
            ws_r[f"{col}{r}"].number_format = "0.000000"

    # Période de confort adaptatif (noms PREMIER_JOUR / DERNIER_JOUR)
    entete(ws_r, [("Période de confort adaptatif", 34), ("Excel (jour j)", 14), ("Python (jour j)", 14),
                  ("Écart", 11), ("Date indicative", 14)], ligne=11)
    rng_jour = f"Journalier!$A${L0}:$A${LJ_FIN}"
    rng_rm_j = f"Journalier!$C${L0}:$C${LJ_FIN}"
    cond = f'">="&SEUIL_RM'
    periode = [
        ("Premier jour où θrm ≥ SEUIL_RM",
         f"=IF(COUNTIF({rng_rm_j},{cond})=0,-1,_xlfn.MINIFS({rng_jour},{rng_rm_j},{cond}))", premier_py),
        ("Dernier jour où θrm ≥ SEUIL_RM",
         f"=IF(COUNTIF({rng_rm_j},{cond})=0,-1,_xlfn.MAXIFS({rng_jour},{rng_rm_j},{cond}))", dernier_py),
    ]
    for i, (lib, f, py) in enumerate(periode):
        r = 12 + i
        ws_r.cell(row=r, column=1, value=lib).font = F_GRAS
        ws_r.cell(row=r, column=2, value=f).font = F_LIEN
        ws_r.cell(row=r, column=3, value=py).font = F_SAISIE
        ws_r.cell(row=r, column=4, value=f"=B{r}-C{r}").font = F_NORMAL
        ws_r.cell(row=r, column=5, value=f"=IF(B{r}<0,\"—\",DATE({ANNEE_LUNDI},1,1)+B{r})").font = F_NORMAL
        ws_r[f"E{r}"].number_format = "d mmmm"
    nom_defini(wb, "PREMIER_JOUR", "Résultats", "$B$12")
    nom_defini(wb, "DERNIER_JOUR", "Résultats", "$B$13")

    # Repères réglementaires
    ws_r["A16"] = "Repères RE2020 (DH d'un bâtiment, à titre indicatif)"
    ws_r["A16"].font = F_GRAS
    ws_r["A17"], ws_r["B17"] = "Seuil bas (°C.h)", 350
    ws_r["A18"], ws_r["B18"] = "DH max courant (°C.h)", 1250
    for c in ("A17", "A18"):
        ws_r[c].font = F_NORMAL
    for c in ("B17", "B18"):
        ws_r[c].font = F_SAISIE
    ws_r["C17"] = "Source : annexe III arrêté 4 août 2021 ; guide RE2020"
    ws_r["C17"].font = F_NORMAL
    ws_r["A20"] = ("Attention : ces DH sont calculés sur la température EXTÉRIEURE, prise comme température "
                   "intérieure. C'est un indicateur de sévérité du climat, pas le DH d'un bâtiment.")
    ws_r["A20"].font = Font(name=POLICE, size=10, italic=True)

    # Mise en évidence des écarts non nuls
    regle = FormulaRule(formula=[f"ABS(D5)>{TOLERANCE}"], fill=PatternFill("solid", fgColor=ROUGE_CLAIR))
    ws_r.conditional_formatting.add("D5:D8", regle)
    ws_r.conditional_formatting.add("G5:G8", FormulaRule(formula=[f"ABS(G5)>{TOLERANCE}"],
                                                         fill=PatternFill("solid", fgColor=ROUGE_CLAIR)))
    ws_r.conditional_formatting.add("D12:D13", FormulaRule(formula=["D12<>0"],
                                                           fill=PatternFill("solid", fgColor=ROUGE_CLAIR)))

    # ---------------------------------------------------------
    # Onglet Lisez-moi
    # ---------------------------------------------------------
    ws_lire.column_dimensions["A"].width = 120
    texte = [
        (f"Calcul DH basic / DH réel — zone {ZONE}", F_TITRE),
        ("", F_NORMAL),
        ("Objet", F_GRAS),
        ("Recalculer en formules Excel les degrés-heures (DH) d'une série horaire de 8760 températures, "
         "et comparer au module Python dh_re2020.calculer_dh (onglet Résultats, colonnes Écart).", F_NORMAL),
        ("Données : " + SOURCE_METEO + ". Fichier horaire en UTC.", F_NORMAL),
        ("Les DH sont calculés sur la température fichier (indicateur climatique), pas sur la température "
         "opérative d'un bâtiment.", F_NORMAL),
        ("", F_NORMAL),
        ("DH basic", F_GRAS),
        ("DH(h) = MAX(0 ; T(h) − seuil(h)), seuil = SEUIL_HAUT (28 °C) le jour [H_DEBUT ; H_FIN[ en heure légale, "
         "SEUIL_BAS (26 °C) la nuit. Toutes les heures de l'année, sans occupation ni période adaptative.", F_NORMAL),
        ("", F_NORMAL),
        ("DH réel (méthode Th-BCE 2020, annexe III de l'arrêté du 4 août 2021)", F_GRAS),
        ("1. θrm(j) = 0,8 × θrm(j−1) + 0,2 × Tmoy(j−1), θrm = 0 le premier jour — fiche climat, formule (1).", F_NORMAL),
        ("2. Période de confort adaptatif : du premier au dernier jour où θrm ≥ 16 °C — formule (2).", F_NORMAL),
        ("3. θop_inc_max(j) = MAX(26 ; 0,33 × θrm(j) + 18,8 + 2) — fiche 13.5, formule (2543), catégorie 1.", F_NORMAL),
        ("4. Habitation : jour → MIN(28 ; θop_inc_max), nuit → 26 °C — formule (2544).", F_NORMAL),
        ("5. DH = Σ MAX(0 ; T(h) − seuil(h)) sur les heures occupées de la période adaptative — formule (2551).", F_NORMAL),
        ("6. Occupation logement : absents 10h–18h lun., mar., jeu., ven. et 10h–14h le mercredi "
         "(année débutant un lundi, heure légale).", F_NORMAL),
        ("", F_NORMAL),
        ("Onglets", F_GRAS),
        ("Paramètres : toutes les valeurs modifiables (cellules jaunes), nommées et utilisées par les formules.", F_NORMAL),
        ("Horaire : une ligne par heure, colonnes de calcul pas à pas jusqu'au DH basic (K) et au DH réel (Q).", F_NORMAL),
        ("Journalier : moyenne extérieure, θrm, période adaptative, seuil de jour, DH par jour et graphique.", F_NORMAL),
        ("Résultats : totaux Excel, valeurs Python de référence et écarts (rouge si non nul).", F_NORMAL),
        ("", F_NORMAL),
        ("Code couleur : bleu = valeur saisie ; noir = formule ; vert = lien vers un autre onglet ; "
         "fond jaune = paramètre modifiable.", F_NORMAL),
    ]
    for i, (t, f) in enumerate(texte, start=1):
        c = ws_lire.cell(row=i, column=1, value=t)
        c.font, c.alignment = f, ENVELOPPE

    wb.save(SORTIE)
    print("Écrit :", SORTIE)
    print(f"Python basic {basic['dh_total']:.2f} / réel {reel['dh_total']:.2f} / période {premier_py}-{dernier_py}")


if __name__ == "__main__":
    main()
