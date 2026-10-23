"""
============================================================
 EXPORT — CSV et Excel (valeurs exactes, non arrondies)
============================================================
 Chaque export contient les hypothèses et le réglage utilisés,
 pour qu'un résultat reste toujours traçable.
============================================================
"""

import io

import pandas as pd

from config.reglages import VERSION


def tableau_horaire(analyse) -> pd.DataFrame:
    s = analyse.serie
    return pd.DataFrame({"horodatage_legal": s.horodatage, "T_degC": s.t, "seuil_degC": analyse.seuil,
                         "DH_degCh": analyse.dh_h, "jour_1_nuit_0": analyse.est_jour.astype(int)})


def tableau_indicateurs(resultats, hyp, remplacer) -> pd.DataFrame:
    return pd.DataFrame([{"id": d["id"], "indicateur": remplacer(d["libelle"], hyp), "valeur": r.valeur,
                          "unite": d["unite"], "detail": r.detail} for d, r in resultats])


def csv_horaire(analyse) -> bytes:
    return tableau_horaire(analyse).to_csv(sep=";", decimal=",", index=False).encode("utf-8-sig")


def excel_complet(analyse, resultats, hyp, reglage, remplacer) -> bytes:
    tampon = io.BytesIO()
    with pd.ExcelWriter(tampon, engine="openpyxl") as xl:
        tableau_indicateurs(resultats, hyp, remplacer).to_excel(xl, sheet_name="indicateurs", index=False)
        tableau_horaire(analyse).to_excel(xl, sheet_name="horaire", index=False)
        analyse.jours.rename_axis("jour_legal").to_excel(xl, sheet_name="journalier")
        pd.DataFrame(list(hyp.values())).to_excel(xl, sheet_name="hypotheses", index=False)
        meta = dict(analyse.serie.meta, version_outil=VERSION, methode_effective=analyse.methode_effective,
                    **{f"reglage_{k}": str(v) for k, v in reglage.items()})
        pd.DataFrame(list(meta.items()), columns=["clé", "valeur"]).to_excel(xl, sheet_name="fichier_et_reglage", index=False)
    return tampon.getvalue()
