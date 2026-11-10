"""
④ EXPORTER — copier-coller des indicateurs et téléchargement (CSV ou Excel).

Choix en haut : 1 fichier (celui de l'onglet Analyser) ou 2 fichiers (+ le second fichier de
l'onglet Comparer), avec ou sans indicateurs, avec ou sans données horaires.
"""

import html

import numpy as np
import streamlit as st

from calcul.format_fr import nombre
from config.charte import COULEUR_FICHIER_1, COULEUR_FICHIER_2
from config.reglages import LIBELLES_METHODE
from export.export import (ENCODAGE_CSV, FichierExport, csv_export, excel_export, nom_de_fichier, tableau_copier,
                           tableau_horaire, texte_copier)

# ============================================================
# PARAMÈTRES
# ============================================================
UN, DEUX = "1 fichier", "2 fichiers"
FORMATS_COPIER = {"Tableau (Excel)": "tableau", "Texte (mail)": "texte"}
FORMATS_FICHIER = {"CSV (Excel français)": "csv", "Excel .xlsx": "xlsx"}
NB_LIGNES_DEBUT = 3                      # aperçu : premières heures du fichier…
NB_LIGNES_CHAUDES = 2                    # … puis les heures autour du maximum de température
NB_LIGNES_TETE = 6                       # aperçu : lignes d'en-tête du CSV montrées
ECART_TABULATION = 3                     # caractères ajoutés à la plus longue cellule (affichage du tableau)


def texte_reglage(reglage: dict, hyp: dict) -> str:
    """« réglage RE2020, DH en occupation (logement) · nuit 22h-6h · heure légale »."""
    occupation = "DH en occupation (logement)" if reglage["occupation"] else "DH 24h/24"
    return (f"réglage {LIBELLES_METHODE[reglage['methode']]}, {occupation} · nuit "
            f"{hyp['nuit_debut']['valeur']:g}h-{hyp['nuit_fin']['valeur']:g}h · heure légale")


def _puces(reglage, hyp) -> str:
    morceaux = [f"{LIBELLES_METHODE[reglage['methode']]} · seuil {hyp['seuil_nuit_dh']['valeur']:g} → "
                f"{hyp['seuil_jour_max']['valeur']:g} °C",
                "DH en occupation" if reglage["occupation"] else "DH 24h/24",
                f"nuit {hyp['nuit_debut']['valeur']:g}h-{hyp['nuit_fin']['valeur']:g}h", "heure légale"]
    return "".join(f'<span class="puce">{html.escape(m)}</span>' for m in morceaux)


def _entete_carte(numero: str, titre: str):
    st.markdown(f'<div class="entete-carte"><span class="num">{numero}</span><h3>{html.escape(titre)}</h3></div>',
                unsafe_allow_html=True)


def _apercu_tableau(df, couleurs) -> str:
    """Aperçu HTML : premières heures, « … », heures autour du maximum de température du premier fichier."""
    col_t = [c for c in df.columns if c.startswith("T ")]
    i_max = int(np.nanargmax(df[col_t[0]].to_numpy()))
    debut, chaud = df.iloc[:NB_LIGNES_DEBUT], df.iloc[i_max - NB_LIGNES_CHAUDES + 1:i_max + 1]
    entete = "".join(f'<th style="color:{couleurs.get(c, "inherit")}">{html.escape(c)}</th>' for c in df.columns)

    def lignes(bloc):
        return "".join("<tr>" + "".join(
            f"<td>{v}</td>" if k < 2 else f'<td class="{"dh" if df.columns[k].startswith("DH") else ""}">'
            f'{nombre(v, 2 if df.columns[k].startswith("DH") else 1)}</td>' for k, v in enumerate(r)) + "</tr>"
            for r in bloc.itertuples(index=False))
    milieu = (f'<tr class="trous"><td colspan="{len(df.columns)}">… {nombre(len(df), 0)} lignes, une par heure '
              f'…</td></tr>')
    return (f'<div class="apercu"><table><tr>{entete}</tr>{lignes(debut)}{milieu}{lignes(chaud)}</table></div>')


def _tableau_aligne(fichiers, hyp, remplacer, noms, ecart, texte_complet, avec_reglage) -> str:
    """
    Version « tableau » affichée : les cellules restent séparées par des tabulations (collage Excel), la
    1re colonne est complétée par des espaces et la largeur de tabulation réglée (CSS) pour que les colonnes
    s'alignent à l'écran.
    """
    cellules = tableau_copier(fichiers, hyp, remplacer, noms, ecart)
    pas = max(len(c) for l in cellules for c in l[1:]) + ECART_TABULATION
    largeur = -(-max(len(l[0]) for l in cellules) // pas) * pas - 1          # multiple du pas, moins la tabulation
    corps = [l[0].ljust(largeur) + "\t" + "\t".join(l[1:]) for l in cellules]
    if avec_reglage:                                       # ligne de réglage en tête, source en pied
        complet = texte_complet.split("\n")
        corps = [complet[0]] + corps + complet[1 + len(cellules):]
    st.markdown(f"<style>.st-key-carte_copier code {{ tab-size: {pas}; -moz-tab-size: {pas}; }}</style>",
                unsafe_allow_html=True)
    return "\n".join(corps)


def afficher(fichier_a: FichierExport, fichier_b: FichierExport, reglage: dict, hyp: dict, remplacer):
    st.markdown('<div class="sous-onglet">Copier les indicateurs dans un mail ou un rapport, ou télécharger les '
                'données heure par heure avec les indicateurs.</div>', unsafe_allow_html=True)

    # --- Que voulez-vous exporter ? ---
    with st.container(key="choix_export"):
        col_f, col_c, col_r = st.columns([1.55, 1, 1.25], gap="large")
        with col_f:
            st.markdown('<div class="lib-groupe">Fichiers</div>', unsafe_allow_html=True)
            nb = st.segmented_control("Fichiers", [UN, DEUX], key="export_nb", required=True, default=UN,
                                      label_visibility="collapsed",
                                      format_func=lambda o: f"{o} · {fichier_a.nom}" if o == UN
                                      else f"{o} · + {fichier_b.nom}")
            st.caption("Le 2ᵉ fichier est le second fichier de l'onglet Comparer.")
        with col_c:
            st.markdown('<div class="lib-groupe">Contenu</div>', unsafe_allow_html=True)
            avec_ind = st.checkbox("Indicateurs (ordre des cartes)", value=True, key="export_ind")
            avec_hor = st.checkbox(f"Données horaires ({nombre(len(fichier_a.analyse.serie.t), 0)} h)", value=True,
                                   key="export_hor")
        with col_r:
            st.markdown('<div class="lib-groupe">Réglage utilisé (inscrit dans l\'export)</div>'
                        f'<div class="puces-export">{_puces(reglage, hyp)}</div>', unsafe_allow_html=True)

    fichiers = [fichier_a] + ([fichier_b] if nb == DEUX else [])
    couleurs = {}
    for f, c in zip(fichiers, (COULEUR_FICHIER_1, COULEUR_FICHIER_2)):
        couleurs.update({f"T {f.nom} (°C)": c, f"seuil {f.nom} (°C)": c, f"DH {f.nom} (°C.h)": c})
    reglage_txt = texte_reglage(reglage, hyp)
    if not (avec_ind or avec_hor):
        st.warning("Cochez au moins un contenu : indicateurs ou données horaires.")
        return

    # --- 1. Copier-coller (pleine largeur : deux fichiers + écart tiennent sur une ligne) ---
    with st.container(key="carte_copier"):
        _entete_carte("1", "Copier-coller les indicateurs")
        format_ = FORMATS_COPIER[st.segmented_control("Format", list(FORMATS_COPIER), key="export_format_copier",
                                                      required=True, default=list(FORMATS_COPIER)[0],
                                                      label_visibility="collapsed")]
        st.caption("Bouton ⧉ en haut à droite du cadre (au survol), puis coller dans Excel, Word ou un mail.")
        o1, o2, o3, _ = st.columns([1, 1, 1, 2])
        noms = o1.checkbox("Noms des fichiers", value=True, key="export_noms")
        ecart = o2.checkbox("Colonne « Écart »", value=True, key="export_ecart", disabled=nb == UN)
        avec_reglage = o3.checkbox("Réglage et source", value=False, key="export_reglage")
        texte = texte_copier(fichiers, hyp, remplacer, format_, noms, ecart, reglage_txt if avec_reglage else None)
        if format_ == "tableau":
            texte = _tableau_aligne(fichiers, hyp, remplacer, noms, ecart, texte, avec_reglage)
        st.code(texte, language=None)
        if not avec_ind:
            st.caption("Les indicateurs ne seront pas dans le fichier téléchargé (case « Indicateurs » décochée), "
                       "mais restent copiables ici.")

    # --- 2. Fichier à télécharger ---
    with st.container(key="carte_csv"):
        _entete_carte("2", "Télécharger le fichier")
        format_fichier = FORMATS_FICHIER[st.segmented_control("Format du fichier", list(FORMATS_FICHIER),
                                                              key="export_format_fichier", required=True,
                                                              default=list(FORMATS_FICHIER)[0],
                                                              label_visibility="collapsed")]
        if format_fichier == "csv":
            st.caption("Séparateur « ; », virgule décimale : s'ouvre directement dans Excel. Début du fichier :")
            donnees = csv_export(fichiers, hyp, remplacer, reglage_txt, avec_ind, avec_hor)
            mime = "text/csv"
        else:
            st.caption("Un onglet par contenu, plus les hypothèses et le réglage. Aperçu des données horaires :")
            donnees = excel_export(fichiers, hyp, remplacer, reglage, reglage_txt, avec_ind, avec_hor)
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if format_fichier == "csv":              # en-tête réel du fichier (réglage, source, indicateurs)
            tete = [l for l in donnees.decode(ENCODAGE_CSV).split("\n") if l.startswith("#")] if avec_hor else \
                donnees.decode(ENCODAGE_CSV).split("\n")[:NB_LIGNES_TETE]
            st.markdown(f'<div class="bloc-tete">{"<br>".join(html.escape(l) for l in tete[:NB_LIGNES_TETE])}'
                        f'{"<br>…" if len(tete) > NB_LIGNES_TETE else ""}</div>', unsafe_allow_html=True)
        else:
            feuilles = ["indicateurs"] * avec_ind + ["horaire"] * avec_hor + ["hypotheses", "reglage_et_fichiers"]
            st.markdown(f'<div class="bloc-tete">Feuilles du classeur : <b>{" · ".join(feuilles)}</b></div>',
                        unsafe_allow_html=True)
        if avec_hor:
            st.markdown(_apercu_tableau(tableau_horaire(fichiers), couleurs), unsafe_allow_html=True)
        nom = nom_de_fichier(fichiers, format_fichier)
        col_b, col_n, _ = st.columns([1, 2.2, 2], vertical_alignment="center")
        col_b.download_button(f"⤓ Télécharger le {'CSV' if format_fichier == 'csv' else 'fichier Excel'}", donnees,
                              file_name=nom, mime=mime, type="primary", key="export_telecharger")
        contenu = " + ".join(x for x, ok in (("indicateurs", avec_ind), ("données horaires", avec_hor)) if ok)
        col_n.markdown(f'<div class="nom-export"><b>{html.escape(nom)}</b><br>{len(fichiers)} fichier'
                       f'{"s" if len(fichiers) > 1 else ""} · {contenu} · {nombre(len(donnees) / 1e6, 1)} Mo</div>',
                       unsafe_allow_html=True)
