"""
============================================================
 EXPORT — copier-coller, CSV et Excel (onglet ④ Exporter)
============================================================
 - Copier-coller : indicateurs arrondis comme à l'écran, en tableau
   (tabulations, pour Excel / Word) ou en texte aligné (mail).
 - CSV « Excel français » : séparateur « ; », virgule décimale,
   UTF-8 avec BOM ; indicateurs en tête (lignes « # ») puis les
   8 760 heures (date, heure légale, T, seuil, DH de chaque fichier).
 - Excel .xlsx : une feuille par contenu + hypothèses et réglage.
 Valeurs au millième dans le CSV, exactes dans l'Excel ; version,
 réglage et sources toujours inscrits, pour rester traçable.
============================================================
"""

import io
from dataclasses import dataclass

import numpy as np
import pandas as pd

from config.reglages import VERSION

# ============================================================
# PARAMÈTRES
# ============================================================
SEPARATEUR_CSV = ";"
DECIMALE_CSV = ","
ENCODAGE_CSV = "utf-8-sig"              # BOM : Excel lit correctement les accents
DECIMALES_CSV = 3                       # CSV : valeurs au millième (sans zéros inutiles pour les indicateurs)
ANNEE_COMMUNE = 2018                    # deux fichiers : dates ramenées sur une même année
UNITES_SANS_PARENTHESE = {"nuits"}      # « Nuits ≥ 24 °C » se lit sans « (nuits) »
COLONNE_INDICATEUR = "Indicateur"
COLONNE_ECART = "Écart"


@dataclass
class FichierExport:
    """Un fichier à exporter : son nom, son analyse et ses indicateurs [(définition, Resultat)]."""
    nom: str
    analyse: object
    resultats: list

    @property
    def source(self) -> str:
        return self.analyse.serie.meta.get("source", "")


# ============================================================
# OUTILS
# ============================================================

def libelle(d: dict, hyp: dict, remplacer) -> str:
    """« DH (°C.h) », « Heures > 28 °C (h) », « Nuits ≥ 24 °C »."""
    texte = remplacer(d["libelle"], hyp)
    return texte if d["unite"] in UNITES_SANS_PARENTHESE else f"{texte} ({d['unite']})"


def _nombre(v, decimales: int, milliers: bool) -> str:
    """Virgule décimale ; espace des milliers seulement pour la lecture (pas pour Excel)."""
    if v is None:
        return "—"
    texte = f"{v:,.{decimales}f}" if milliers else f"{v:.{decimales}f}"
    return texte.replace(",", " ").replace(".", ",")


def _ecart(va, vb, decimales: int, milliers: bool) -> str:
    if va is None or vb is None:
        return "—"
    e = round(vb, decimales) - round(va, decimales)
    signe = "+" if e > 0 else "−" if e < 0 else ""
    return signe + _nombre(abs(e), decimales, milliers)


def _sources(fichiers) -> str:
    return " · ".join(dict.fromkeys(f.source for f in fichiers if f.source))


# ============================================================
# 1. COPIER-COLLER
# ============================================================

def tableau_copier(fichiers, hyp, remplacer, noms=True, ecart=True) -> list:
    """Lignes [[cellule, …], …] des indicateurs, valeurs arrondies comme à l'écran."""
    avec_ecart = ecart and len(fichiers) == 2
    lignes = []
    if noms:
        lignes.append([COLONNE_INDICATEUR] + [f.nom for f in fichiers] + ([COLONNE_ECART] if avec_ecart else []))
    for rangs in zip(*(f.resultats for f in fichiers)):
        d = rangs[0][0]
        dec = int(d.get("decimales", 0) or 0)
        valeurs = [r.valeur for _, r in rangs]
        lignes.append([libelle(d, hyp, remplacer)] + [_nombre(v, dec, milliers=False) for v in valeurs]
                      + ([_ecart(valeurs[0], valeurs[1], dec, milliers=False)] if avec_ecart else []))
    return lignes


def texte_copier(fichiers, hyp, remplacer, format_="tableau", noms=True, ecart=True, texte_reglage=None) -> str:
    """
    format_ = « tableau » : cellules séparées par des tabulations (collage direct dans Excel ou Word) ;
              « texte »   : colonnes alignées par des espaces (mail).
    texte_reglage : si donné, ligne de réglage en tête et ligne de source en pied.
    """
    lignes = tableau_copier(fichiers, hyp, remplacer, noms, ecart)
    if format_ == "tableau":
        corps = ["\t".join(l) for l in lignes]
    else:
        largeurs = [max(len(l[k]) for l in lignes) for k in range(len(lignes[0]))]
        corps = ["  ".join(c.ljust(largeurs[k]) if k == 0 else c.rjust(largeurs[k]) for k, c in enumerate(l)).rstrip()
                 for l in lignes]
    if texte_reglage:
        corps = [f"Météo et Chaleur v{VERSION} · {texte_reglage}"] + corps
        if _sources(fichiers):
            corps.append(f"Source : {_sources(fichiers)}")
    return "\n".join(corps)


# ============================================================
# 2. DONNÉES HORAIRES
# ============================================================

def _date_commune(horodatage: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Même année pour tous (29 février écarté) : sert à mettre deux fichiers côte à côte."""
    garde = ~((horodatage.month == 2) & (horodatage.day == 29))
    h = horodatage[garde]
    return pd.DatetimeIndex(pd.to_datetime(dict(year=ANNEE_COMMUNE, month=h.month, day=h.day, hour=h.hour))), garde


def tableau_horaire(fichiers) -> pd.DataFrame:
    """
    Une ligne par heure : date, heure légale, puis pour chaque fichier T, seuil et DH.
    Un fichier : sa propre date (avec l'année pour un relevé). Deux fichiers : dates ramenées
    sur une même année et alignées (un relevé court n'occupe que ses jours).
    """
    blocs = []
    for f in fichiers:
        a = f.analyse
        horo, garde = _date_commune(a.serie.horodatage) if len(fichiers) > 1 else (a.serie.horodatage,
                                                                                   np.ones(len(a.serie.t), bool))
        blocs.append(pd.DataFrame({f"T {f.nom} (°C)": a.serie.t[garde], f"seuil {f.nom} (°C)": a.seuil[garde],
                                   f"DH {f.nom} (°C.h)": a.dh_h[garde]}, index=horo))
    df = pd.concat(blocs, axis=1, sort=True)
    seul_annee_type = len(fichiers) == 1 and fichiers[0].analyse.serie.meta.get("periode", "").startswith("année type")
    format_date = "%d/%m" if (len(fichiers) > 1 or seul_annee_type) else "%d/%m/%Y"
    df.insert(0, "heure", df.index.hour)
    df.insert(0, "date", df.index.strftime(format_date))
    return df.reset_index(drop=True)


def tableau_indicateurs(fichiers, hyp, remplacer) -> pd.DataFrame:
    """Indicateurs, valeurs exactes : une colonne par fichier (+ écart pour deux fichiers)."""
    lignes = []
    for rangs in zip(*(f.resultats for f in fichiers)):
        d = rangs[0][0]
        ligne = {COLONNE_INDICATEUR: libelle(d, hyp, remplacer)}
        ligne.update({f.nom: r.valeur for f, (_, r) in zip(fichiers, rangs)})
        if len(fichiers) == 2:
            va, vb = (r.valeur for _, r in rangs)
            ligne[f"{COLONNE_ECART} ({fichiers[1].nom} − {fichiers[0].nom})"] = None if va is None or vb is None else vb - va
        lignes.append(ligne)
    return pd.DataFrame(lignes)


# ============================================================
# 3. FICHIERS À TÉLÉCHARGER
# ============================================================

def _valeur_csv(v) -> str:
    """Cellule de CSV : vide si absente, virgule décimale pour les nombres."""
    if v is None or (isinstance(v, (float, np.floating)) and np.isnan(v)):
        return ""
    if isinstance(v, (int, float, np.integer, np.floating)):
        texte = f"{float(v):.{DECIMALES_CSV}f}".rstrip("0").rstrip(".")     # 839,145 · 218 · 150,555
        return (texte if texte not in ("-0", "") else "0").replace(".", DECIMALE_CSV)
    return str(v)


def csv_export(fichiers, hyp, remplacer, texte_reglage, avec_indicateurs=True, avec_horaire=True) -> bytes:
    """CSV « Excel français ». Avec les deux contenus : indicateurs en tête (lignes « # »), puis l'horaire."""
    tete = [f"# Météo et Chaleur v{VERSION} · {texte_reglage}"]
    if _sources(fichiers):
        tete.append(f"# Source : {_sources(fichiers)}")
    texte = ""
    if avec_indicateurs:
        ind = tableau_indicateurs(fichiers, hyp, remplacer)
        prefixe = "# " if avec_horaire else ""
        lignes = [SEPARATEUR_CSV.join(ind.columns)] + [SEPARATEUR_CSV.join(_valeur_csv(v) for v in r)
                                                         for r in ind.itertuples(index=False)]
        tete += [prefixe + l for l in lignes] if avec_horaire else []
        texte = "" if avec_horaire else "\n".join(lignes) + "\n"
    if avec_horaire:
        texte = tableau_horaire(fichiers).to_csv(sep=SEPARATEUR_CSV, decimal=DECIMALE_CSV, index=False,
                                                 float_format=f"%.{DECIMALES_CSV}f")
    return ("\n".join(tete) + "\n" + texte).encode(ENCODAGE_CSV)


def excel_export(fichiers, hyp, remplacer, reglage, texte_reglage, avec_indicateurs=True, avec_horaire=True) -> bytes:
    """Classeur : indicateurs, horaire, hypothèses, réglage et fichiers (valeurs exactes)."""
    tampon = io.BytesIO()
    with pd.ExcelWriter(tampon, engine="openpyxl") as xl:
        if avec_indicateurs:
            tableau_indicateurs(fichiers, hyp, remplacer).to_excel(xl, sheet_name="indicateurs", index=False)
        if avec_horaire:
            tableau_horaire(fichiers).to_excel(xl, sheet_name="horaire", index=False)
        pd.DataFrame(list(hyp.values())).to_excel(xl, sheet_name="hypotheses", index=False)
        infos = [("outil", f"Météo et Chaleur v{VERSION}"), ("réglage", texte_reglage),
                 ("indicateurs (ordre)", ", ".join(d["id"] for d in reglage.get("indicateurs", [])))]
        for n, f in enumerate(fichiers, 1):
            infos += [(f"fichier {n}", f.nom), (f"fichier {n} · méthode DH", f.analyse.methode_effective),
                      (f"fichier {n} · source", f.source)]
        pd.DataFrame(infos, columns=["clé", "valeur"]).to_excel(xl, sheet_name="reglage_et_fichiers", index=False)
    return tampon.getvalue()


def nom_de_fichier(fichiers, extension: str) -> str:
    """meteo_et_chaleur_H1a-th-d_H3-th-d_v0.9.2.csv"""
    morceaux = [f.analyse.serie.id.replace("_", "-") for f in fichiers]
    return f"meteo_et_chaleur_{'_'.join(morceaux)}_v{VERSION}.{extension}"
