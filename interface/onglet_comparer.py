"""
② COMPARER — le fichier de l'onglet Analyser (corail) face à un second fichier (bleu canard).

Chaque fichier garde sa couleur partout : cartouche, colonne du tableau, courbes.
"""

import html

import pandas as pd
import streamlit as st

from calcul.hypotheses import remplacer_reperes, valeur
from calcul.indicateurs import jour_le_plus_chaud, semaine_la_plus_chaude
from config.reglages import COULEUR_FICHIER_1, COULEUR_FICHIER_2, FAMILLES, GRIS
from interface import graphiques as g
from interface.composants import cartouche, pastille_ecart, valeur_texte

# ============================================================
# PARAMÈTRES
# ============================================================
ANNEE = g.ANNEE_SUPERPOSITION
CONFIG_PLOTLY = g.CONFIG_PLOTLY
ROLE_A, ROLE_B = "Fichier de l'onglet Analyser", "Second fichier"
SEUIL_FRAIS, SEUIL_CHAUD = "seuil_nuit_tropicale", "seuil_heures_chaudes"   # bandes bleu / orangé (20 / 28 °C)


# ============================================================
# TABLEAU DES INDICATEURS
# ============================================================

def _tableau(res_a, res_b, nom_a, nom_b, hyp):
    """Indicateurs côte à côte ; l'écart (pastille) est « second fichier par rapport au premier »."""
    lignes = []
    for (d, ra), (_, rb) in zip(res_a, res_b):
        dec = int(d.get("decimales", 0) or 0)
        unite = html.escape(d["unite"])
        va, vb = ra.valeur, rb.valeur
        ecart = "—" if va is None or vb is None else pastille_ecart(round(vb, dec) - round(va, dec), d["unite"], dec)
        lignes.append(
            f"<tr><td>{html.escape(remplacer_reperes(d['libelle'], hyp))}</td>"
            f'<td style="color:{COULEUR_FICHIER_1};text-align:right"><b>{valeur_texte(va, dec)} {unite}</b></td>'
            f'<td style="color:{COULEUR_FICHIER_2};text-align:right"><b>{valeur_texte(vb, dec)} {unite}</b></td>'
            f'<td style="text-align:right">{ecart}</td></tr>')
    entete = (f'<tr><th style="text-align:left">Indicateur</th>'
              f'<th style="color:{COULEUR_FICHIER_1};text-align:right">● {html.escape(nom_a)}</th>'
              f'<th style="color:{COULEUR_FICHIER_2};text-align:right">● {html.escape(nom_b)}</th>'
              f'<th style="text-align:right;color:{GRIS}">Écart<br><span style="font-weight:400;font-size:.8rem">'
              f'{html.escape(nom_b)} par rapport à {html.escape(nom_a)}</span></th></tr>')
    st.markdown(f'<div class="tableau"><table>{entete}{"".join(lignes)}</table></div>', unsafe_allow_html=True)


# ============================================================
# CHOIX DU SECOND FICHIER (famille → fichier)
# ============================================================

def _choisir_second(choix_b, analyse_a):
    """
    choix_b : liste de dict {famille, libelle, charger} (catalogue sans le fichier A, importés, fichier C).
    Par défaut : même scénario dans une autre zone (dernier trouvé), sinon le premier fichier.
    """
    familles = [f for f in FAMILLES if any(c["famille"] == f for c in choix_b)]
    familles += [f for f in dict.fromkeys(c["famille"] for c in choix_b) if f not in familles]
    libelle_a = analyse_a.serie.meta.get("libelle", "")
    meme = [c for c in choix_b if libelle_a and c["libelle"].endswith(libelle_a)]
    defaut = meme[-1] if meme else choix_b[0]
    famille = st.radio("Famille", familles, index=familles.index(defaut["famille"]), horizontal=True,
                       key="famille_b", label_visibility="collapsed")
    options = [c for c in choix_b if c["famille"] == famille]
    libelles = [c["libelle"] for c in options]
    index = libelles.index(defaut["libelle"]) if defaut in options else 0
    nom = st.selectbox("Second fichier", libelles, index=index, key=f"fichier_b_{famille}",
                       label_visibility="collapsed")
    return options[libelles.index(nom)]["charger"]()


# ============================================================
# ONGLET
# ============================================================

def afficher(analyse_a, res_a, choix_b, analyser_b, reglage, hyp):
    nom_a = analyse_a.serie.libelle
    col_a, col_b = st.columns(2)
    with col_a, st.container(key="cartouche_a"):
        cartouche(ROLE_A, analyse_a.serie, COULEUR_FICHIER_1)
        st.caption("Pour le changer : menu de gauche.")
    with col_b, st.container(key="cartouche_b"):
        tete = st.empty()                      # rempli après le choix (le nom dépend de la sélection)
        serie_b = _choisir_second(choix_b, analyse_a)
        with tete.container():
            cartouche(ROLE_B, serie_b, COULEUR_FICHIER_2)
    analyse_b, res_b = analyser_b(serie_b)
    nom_b = analyse_b.serie.libelle
    if analyse_b.message_methode:
        st.caption(f"⚠ {nom_b} : {analyse_b.message_methode}")

    _tableau(res_a, res_b, nom_a, nom_b, hyp)
    sources = " · ".join(dict.fromkeys(filter(None, [analyse_a.serie.meta.get("source"), analyse_b.serie.meta.get("source")])))
    bas, haut = valeur(hyp, SEUIL_FRAIS), valeur(hyp, SEUIL_CHAUD)

    # 1. L'été superposé
    fenetre = [pd.Timestamp(f"{ANNEE}-{valeur(hyp, 'ete_debut')}"), pd.Timestamp(f"{ANNEE}-{valeur(hyp, 'ete_fin')} 23:00")]
    st.plotly_chart(g.ete_superpose(analyse_a, analyse_b, nom_a, nom_b, reglage["lignes"], fenetre, sources),
                    width="stretch", config=CONFIG_PLOTLY, theme=None)
    # 2. Journées les plus chaudes, 3. semaines les plus chaudes (chacune selon le critère des réglages)
    ja, jb = jour_le_plus_chaud(analyse_a, reglage["critere_journee"]), jour_le_plus_chaud(analyse_b, reglage["critere_journee"])
    if ja is not None and jb is not None:
        st.plotly_chart(g.journees_superposees(analyse_a, analyse_b, nom_a, nom_b, ja, jb, bas, haut, sources),
                        width="stretch", config=CONFIG_PLOTLY, theme=None)
    n = int(valeur(hyp, "semaine_jours"))
    sa = semaine_la_plus_chaude(analyse_a, reglage["critere_semaine"], n)
    sb = semaine_la_plus_chaude(analyse_b, reglage["critere_semaine"], n)
    if sa is not None and sb is not None:
        st.plotly_chart(g.semaines_superposees(analyse_a, analyse_b, nom_a, nom_b, sa, sb, n, bas, haut, sources),
                        width="stretch", config=CONFIG_PLOTLY, theme=None)
    else:
        st.caption(f"Semaine la plus chaude : il faut au moins {n} jours complets dans chaque fichier.")
    # 4. Cumul des DH
    st.plotly_chart(g.cumul_dh(analyse_a, analyse_b, nom_a, nom_b, sources), width="stretch", config=CONFIG_PLOTLY,
                    theme=None)
    st.caption("Les deux fichiers sont ramenés sur une même année pour être superposés jour par jour.")
