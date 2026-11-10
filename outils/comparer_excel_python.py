"""
============================================================
 COMPARAISON EXCEL ↔ PYTHON DES DH
============================================================
 Relit un classeur DH_basic_reel_<zone>.xlsx (enregistré par
 Excel ou LibreOffice, donc avec valeurs calculées), reprend ses
 paramètres (onglet Paramètres) et sa série de températures,
 recalcule avec dh_re2020.calculer_dh et compare HEURE PAR HEURE
 les colonnes DH basic (K), seuil réel (O) et DH réel (Q).

 Usage : python3 comparer_excel_python.py DH_basic_reel_H1a.xlsx
============================================================
"""

import sys
import numpy as np
import openpyxl

from dh_re2020 import calculer_dh

# ============================================================
# PARAMÈTRES
# ============================================================
FICHIER = sys.argv[1] if len(sys.argv) > 1 else "DH_basic_reel_H1a.xlsx"
TOLERANCE = 1e-9                     # écart toléré (°C.h ou °C)
NB_HEURES = 8760
L0 = 2                               # première ligne de données
COL = {"t_bc": 2, "t_d": 3, "seuil_reel": 15, "dh_basic": 11, "dh_reel": 17}
LIGNE_PREMIER_PARAM, COL_NOM, COL_VALEUR = 4, 1, 3


# ============================================================
# LECTURE
# ============================================================

def lire_parametres(ws):
    """Dictionnaire {NOM: valeur} de l'onglet Paramètres."""
    params, ligne = {}, LIGNE_PREMIER_PARAM
    while ws.cell(row=ligne, column=COL_NOM).value:
        params[ws.cell(row=ligne, column=COL_NOM).value] = ws.cell(row=ligne, column=COL_VALEUR).value
        ligne += 1
    return params


def lire_colonne(ws, col):
    vals = [ws.cell(row=L0 + k, column=col).value for k in range(NB_HEURES)]
    if any(v is None for v in vals):
        sys.exit(f"Colonne {col} vide : ouvrez et enregistrez le classeur dans Excel pour calculer les formules.")
    return np.array(vals, dtype=float)


# ============================================================
# COMPARAISON
# ============================================================

def main():
    wb = openpyxl.load_workbook(FICHIER, data_only=True)
    p = lire_parametres(wb["Paramètres"])
    ws = wb["Horaire"]
    t = lire_colonne(ws, COL["t_bc"] if p["SCENARIO"] == "Th-BC" else COL["t_d"])

    # Seule différence de paramétrage possible : l'occupation et les heures d'absence
    if (p["ABS_DEBUT"], p["ABS_FIN"], p["ABS_FIN_MER"], p["INOCC_DEBUT"], p["INOCC_FIN"]) != (9, 17, 13, 358, 364):
        print("Attention : heures d'absence ou semaine inoccupée modifiées dans l'Excel, non reprises par calculer_dh.")
    communs = dict(seuil_bas=p["SEUIL_BAS"], seuil_haut=p["SEUIL_HAUT"], decalage_heure=int(p["DECALAGE"]),
                   heure_debut_jour=int(p["H_DEBUT"]), heure_fin_jour=int(p["H_FIN"]), details=True)
    basic = calculer_dh(t, **communs)
    reel = calculer_dh(t, t, occupation="logement_re2020" if p["OCCUPATION"] else None, **communs)
    if (p["PENTE"], p["ORDONNEE"], p["DELTA_CAT"], p["ALPHA"], p["THETA_INIT"], p["SEUIL_RM"]) != \
            (0.33, 18.8, 2.0, 0.8, 0.0, 16.0):
        print("Attention : coefficients adaptatifs modifiés dans l'Excel, calculer_dh garde les valeurs RE2020.")

    comparaisons = [
        ("DH basic horaire", lire_colonne(ws, COL["dh_basic"]), basic["dh_horaire"]),
        ("Seuil réel horaire", lire_colonne(ws, COL["seuil_reel"]), reel["seuil_horaire"]),
        ("DH réel horaire", lire_colonne(ws, COL["dh_reel"]), reel["dh_horaire"]),
    ]
    print(f"{'Grandeur':<22}{'Σ Excel':>14}{'Σ Python':>14}{'écart max':>12}  heures en écart")
    ok = True
    for nom, excel, python in comparaisons:
        ecart = np.abs(excel - python)
        n = int((ecart > TOLERANCE).sum())
        ok &= n == 0
        print(f"{nom:<22}{excel.sum():>14.4f}{python.sum():>14.4f}{ecart.max():>12.2e}  {n}")
        if n:
            premieres = np.flatnonzero(ecart > TOLERANCE)[:5]
            print("   premières heures en écart (indice fichier) :", premieres.tolist())
    print("RÉSULTAT :", "identiques" if ok else "différences à examiner")


if __name__ == "__main__":
    main()
