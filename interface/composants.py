"""
============================================================
 COMPOSANTS — CSS, en-tête, nom du fichier, cartes d'indicateurs
 (icône, mini-graphique, bulle « i »), bandeau des hypothèses,
 cartouches de l'onglet Comparer, pied de page
============================================================
 Style inspiré d'un tableau de bord épuré : fond gris chaud,
 cartes arrondies à ombre douce, carte principale en couleur
 pleine, pastilles pour les écarts.
 La documentation reste DISCRÈTE à l'écran :
   1. pastille « i » (bulle au survol) ;
   2. bandeau fin des hypothèses actives ;
   3. onglet « Méthode & sources » pour le détail.
============================================================
"""

import html

import numpy as np
import pandas as pd
import streamlit as st

from calcul.hypotheses import MOTIF_REPERE, remplacer_reperes
from calcul.confort_ptc import PTC_VERSION
from config.reglages import (BLEU_CLAIR, BLEU_FRAIS, BLEU_MENU, CARAMEL, CARAMEL_CLAIR, CORAIL, FOND, GRIS,
                             GRIS_DOUX, INDIGO, OMBRE, RAYON, STATUT_VERSION, TEAL, TRAIT, VERSION)
from interface.format_fr import MOIS_COURTS, nombre

# ============================================================
# PARAMÈTRES
# ============================================================
# --- Couleur de chaque carte : DH = rouge (corail), nuit = foncé (indigo) ---
COULEURS_CARTES = {"dh": CORAIL, "heures_chaudes": CORAIL, "journee_chaude": CORAIL, "semaine_chaude": CORAIL,
                   "dh_nuit": INDIGO, "nuits_20": INDIGO, "nuits_24": INDIGO, "nuits_consecutives": INDIGO,
                   "t_moyenne_nuit": INDIGO, "t_moyenne": TEAL}
CARTE_PRINCIPALE = "dh"                 # carte affichée en couleur pleine (texte blanc)
PART_TEINTE_FOND = 0.09                 # fond des cartes : couleur de la carte mêlée de blanc
PART_TEINTE_ICONE = 0.20                # rond de l'icône
COULEURS_STATUT = {"sourcé": TEAL, "provisoire": "#C77D2E", "à préciser": CORAIL, "hypothèse": GRIS_DOUX}

# --- En-tête ---
TRACE_LOGO = "M2 12 C3.2 12 3.6 9.5 4.8 9.5 S6.4 14.5 7.6 14.5 S9.2 6 10.6 6 S12.4 18 13.8 18 S15.6 3.5 17.2 3.5 S19.2 20.5 22 12"
CONTOUR_ONGLET = "#2C5E6E"              # contour des pastilles de la barre des onglets (bleu canard sombre)

# --- Mini-graphique des cartes (px) ---
LARGEUR_MINI, HAUTEUR_MINI, HAUTEUR_LIBELLES = 104, 34, 11
NB_MOIS_LIBELLES = 5                    # au-delà, pas de nom de mois sous les barres
EPAISSEUR_JAUGE = 9                     # épaisseur de l'arc de la jauge (px)

# --- Icônes (tracés simples, style « feather », 24 × 24) ---
ICONES = {
    "soleil": '<circle cx="12" cy="12" r="4.5"/><path d="M12 1.5v2.5M12 20v2.5M4.6 4.6l1.8 1.8M17.6 17.6l1.8 1.8'
              'M1.5 12H4M20 12h2.5M4.6 19.4l1.8-1.8M17.6 6.4l1.8-1.8"/>',
    "lune": '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
    "horloge": '<circle cx="12" cy="12" r="9.5"/><path d="M12 6.5V12l3.5 2"/>',
    "calendrier": '<rect x="3" y="4.5" width="18" height="17" rx="2.5"/><path d="M16 2.5v4M8 2.5v4M3 10h18"/>',
    "thermometre": '<path d="M14 14.8V4.5a2 2 0 0 0-4 0v10.3a4.5 4.5 0 1 0 4 0z"/>',
}
ICONE_INDICATEUR = {"dh": "soleil", "dh_nuit": "lune", "heures_chaudes": "horloge", "nuits_20": "lune",
                    "nuits_24": "lune", "nuits_consecutives": "calendrier", "t_moyenne": "thermometre",
                    "t_moyenne_nuit": "thermometre", "journee_chaude": "soleil", "semaine_chaude": "calendrier"}

CSS = f"""
<style>
  .stApp {{ background: {FOND}; }}
  [data-testid="stSidebar"] {{ background: {BLEU_MENU}; }}
  [data-testid="stSidebar"] h3 {{ color: {INDIGO}; font-size: 0.85rem; letter-spacing: .06em; margin-top: .6rem; }}
  /* Menu de gauche : titres de partie en pastille indigo, panneau bleu clair, bouton de repli indigo */
  .titre-menu {{ background: {INDIGO}; color: white; border-radius: 16px; text-align: center; font-weight: 800;
                 font-size: 1.15rem; letter-spacing: .08em; padding: 7px 10px; text-transform: uppercase; }}
  .st-key-panneau_fichier {{ background: rgba(255,255,255,.28); border-radius: 18px; padding: 10px 10px 12px; }}
  [data-testid="stSidebarCollapseButton"] button, [data-testid="stExpandSidebarButton"] {{ background: {INDIGO};
      color: white; border-radius: 10px; }}
  [data-testid="stSidebarCollapseButton"] button:hover, [data-testid="stExpandSidebarButton"]:hover {{
      background: #45407a; color: white; }}
  .st-key-reglages {{ border: none; }}
  .st-key-reglages details {{ border: none; background: transparent; }}
  .st-key-reglages summary {{ background: {INDIGO}; border-radius: 16px; padding: 7px 14px; color: white; }}
  .st-key-reglages summary:hover {{ color: white; }}
  .st-key-reglages summary p {{ color: white; font-weight: 800; font-size: 1.15rem; letter-spacing: .08em;
                                text-align: center; width: 100%; }}
  .st-key-reglages summary svg {{ fill: white; color: white; }}
  .sous-titre-menu {{ font-size: .8rem; font-weight: 700; color: {INDIGO}; letter-spacing: .05em; margin-top: 4px; }}
  header[data-testid="stHeader"] {{ background: transparent; }}
  [data-testid="stToolbarActions"], [data-testid="stMainMenu"], [data-testid="stAppDeployButton"] {{ display: none; }}
  .block-container {{ padding-top: 1.2rem; max-width: 1500px; }}
  /* En-tête clair : logo rond + nom + sous-titre + version */
  .entete {{ display: flex; align-items: center; gap: 16px; margin: 0 0 14px; }}
  .entete .logo {{ width: 52px; height: 52px; border-radius: 50%; background: {INDIGO}; display: flex;
                   align-items: center; justify-content: center; flex: none; }}
  .entete .nom {{ font-size: 1.7rem; font-weight: 700; color: {GRIS}; line-height: 1.1; }}
  .entete .sous {{ color: {GRIS_DOUX}; font-size: .95rem; }}
  .entete .version {{ margin-left: auto; background: white; color: {INDIGO}; border-radius: 22px;
                      padding: 8px 16px; font-size: .85rem; font-weight: 600; box-shadow: {OMBRE}; }}
  .entete .version b {{ color: {BLEU_MENU}; }}
  /* Bloc fixe en haut : en-tête + barre des onglets + nom du fichier (le reste défile dessous) */
  /*   Streamlit enveloppe le bloc dans un conteneur de même hauteur : c'est l'enveloppe qui doit être collante */
  [data-testid="stLayoutWrapper"]:has(> .st-key-haut_fixe) {{ position: sticky; top: 0; z-index: 990; }}
  .st-key-haut_fixe {{ background: {FOND}; padding-top: .9rem; border-bottom: 1px solid {TRAIT}; padding-bottom: 4px; }}
  /* Barre des onglets (indigo) : pastilles cerclées, onglet actif en bleu */
  .st-key-barre_onglets {{ background: {INDIGO}; border-radius: {RAYON}; padding: 8px 10px; }}
  .st-key-barre_onglets [data-testid="stButtonGroup"] {{ gap: 8px; }}
  .st-key-barre_onglets [data-testid="stButtonGroup"] button {{ background: transparent; color: #CFCBE6;
      border: 2px solid {CONTOUR_ONGLET} !important; border-radius: 22px !important; padding: 5px 18px; }}
  .st-key-barre_onglets [data-testid="stButtonGroup"] button p {{ font-size: 1.02rem; font-weight: 600; }}
  .st-key-barre_onglets [data-testid="stButtonGroup"] button:hover {{ color: white; border-color: {BLEU_MENU} !important; }}
  .st-key-barre_onglets [data-testid="stButtonGroup"] button[aria-checked="true"],
  .st-key-barre_onglets [data-testid="stButtonGroup"] button[aria-checked="true"]:hover {{
      background: {BLEU_MENU}; color: {INDIGO}; border-color: {BLEU_MENU} !important; }}
  /* Nom du fichier en gros, sous les onglets */
  .fichier {{ margin: 8px 0 12px; }}
  .fichier .nom {{ font-size: 2rem; font-weight: 700; color: {GRIS}; line-height: 1.15; }}
  .fichier .nom .point {{ display: inline-block; width: 14px; height: 14px; border-radius: 50%;
                          margin-right: 10px; vertical-align: middle; }}
  .fichier .meta {{ color: {GRIS_DOUX}; font-size: .9rem; margin-top: 2px; }}
  /* Cartes d'indicateurs */
  .cartes {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 4px 0 14px; }}
  @media (max-width: 1100px) {{ .cartes {{ grid-template-columns: repeat(2, 1fr); }} }}
  .carte {{ background: var(--fond); border-top: 4px solid var(--c); border-radius: {RAYON};
            box-shadow: {OMBRE}; padding: 12px 16px 10px; position: relative; color: {GRIS}; }}
  .carte.principale {{ background: var(--c); border-top-color: var(--c); color: white; }}
  .carte .haut {{ display: flex; align-items: center; gap: 10px; padding-right: 22px; }}
  .carte .icone {{ width: 34px; height: 34px; border-radius: 50%; background: var(--icone); flex: none;
                   display: flex; align-items: center; justify-content: center; color: var(--c); }}
  .carte.principale .icone {{ background: rgba(255,255,255,.22); color: white; }}
  .carte .titre {{ color: {GRIS_DOUX}; font-size: .85rem; line-height: 1.2; }}
  .carte.principale .titre, .carte.principale .detail, .carte.principale .valeur span {{ color: rgba(255,255,255,.88); }}
  .carte .milieu {{ display: flex; align-items: flex-end; justify-content: space-between; gap: 8px; margin-top: 6px; }}
  .carte .valeur {{ font-size: 2rem; font-weight: 700; line-height: 1.1; white-space: nowrap; }}
  .carte .valeur span {{ font-size: .85rem; font-weight: 400; color: {GRIS_DOUX}; margin-left: 4px; }}
  .carte .detail {{ color: {GRIS_DOUX}; font-size: .75rem; margin-top: 4px; }}
  .carte svg.mini {{ flex: none; overflow: visible; }}
  .info {{ position: absolute; top: 10px; right: 12px; width: 18px; height: 18px; border-radius: 50%;
           border: 1.5px solid var(--c); color: var(--c); font: 700 11px/15px serif; text-align: center; cursor: help; }}
  .carte.principale .info {{ border-color: white; color: white; }}
  .info .bulle {{ display: none; position: absolute; right: -8px; top: 24px; width: 270px; z-index: 50;
                  background: white; border: 1.5px solid var(--c); border-radius: 12px; padding: 10px 12px;
                  font: 400 .8rem/1.35 Inter, sans-serif; color: {GRIS}; text-align: left;
                  box-shadow: 0 4px 14px rgba(0,0,0,.12); }}
  .info:hover .bulle {{ display: block; }}
  .statut {{ display: inline-block; margin-top: 6px; padding: 1px 8px; border-radius: 10px; border: 1px solid;
             font-size: .72rem; font-weight: 600; }}
  /* Bandeau des hypothèses actives */
  .hypos {{ background: {CARAMEL_CLAIR}; border: 1px solid {CARAMEL}; border-radius: {RAYON}; padding: 6px 12px;
            display: flex; flex-wrap: wrap; gap: 6px; align-items: center; font-size: .78rem; margin-bottom: 8px; }}
  .hypos b {{ margin-right: 4px; }}
  .hypos .puce {{ background: white; border: 1px solid {CARAMEL}; border-radius: 12px; padding: 1px 9px; }}
  .message {{ color: {CORAIL}; font-size: .85rem; margin: 2px 0 6px; }}
  /* Graphiques et tableaux dans des cartes blanches arrondies */
  [data-testid="stPlotlyChart"] {{ background: white; border-radius: {RAYON}; box-shadow: {OMBRE};
                                   overflow: hidden; }}
  .tableau {{ background: white; border-radius: {RAYON}; box-shadow: {OMBRE}; padding: 6px 10px; margin: 6px 0 14px; }}
  .tableau table {{ width: 100%; border-collapse: collapse; font-size: .92rem; }}
  .tableau th, .tableau td {{ border: none !important; }}
  .tableau th {{ padding: 8px 10px; border-bottom: 2px solid {TRAIT} !important; }}
  .tableau td {{ padding: 7px 10px; border-bottom: 1px solid #F0EEEA !important; }}
  .tableau tr:last-child td {{ border-bottom: none !important; }}
  .pastille {{ display: inline-block; border-radius: 12px; padding: 2px 10px; font-weight: 700; font-size: .85rem; }}
  /* Cartouches des deux fichiers (onglet Comparer) */
  .st-key-cartouche_a, .st-key-cartouche_b {{ background: white; border-radius: {RAYON}; box-shadow: {OMBRE};
                                              padding: 12px 16px; border-left: 8px solid var(--c, {GRIS}); }}
  .st-key-cartouche_a {{ --c: {CORAIL}; }}
  .st-key-cartouche_b {{ --c: {TEAL}; }}
  .cartouche .role {{ font-size: .75rem; letter-spacing: .05em; text-transform: uppercase; color: {GRIS_DOUX}; }}
  .cartouche .nom {{ font-size: 1.35rem; font-weight: 700; line-height: 1.2; }}
  .cartouche .meta {{ color: {GRIS_DOUX}; font-size: .82rem; }}
  /* --- Menu de gauche : carte du fichier en cours + récents (0.9.0) --- */
  .st-key-fichier_actuel {{ background: white; border-radius: 16px; padding: 14px 14px 12px; box-shadow: {OMBRE}; }}
  .nom-actuel {{ font-weight: 700; font-size: 1.1rem; display: flex; align-items: center; gap: 8px; line-height: 1.2; }}
  .nom-actuel .point, .tuile .point {{ width: 11px; height: 11px; border-radius: 50%; flex: none; display: inline-block; }}
  .meta-actuel {{ color: {GRIS_DOUX}; font-size: .8rem; margin: 4px 0 8px; line-height: 1.35; }}
  .etiquettes {{ display: flex; flex-wrap: wrap; gap: 5px; }}
  .tag {{ font-size: .7rem; padding: 2px 8px; border-radius: 10px; background: #F1EFEA; color: {GRIS_DOUX}; }}
  .tag.famille {{ background: {BLEU_CLAIR}; color: #13628f; font-weight: 600; }}
  .st-key-fichier_actuel button, .st-key-ouvrir_choix_second button {{ background: {INDIGO}; color: white;
      border: none; border-radius: 22px; font-weight: 600; }}
  .st-key-fichier_actuel button:hover, .st-key-ouvrir_choix_second button:hover {{ background: #45407a; color: white; }}
  .st-key-recents {{ gap: .45rem; margin-top: 4px; }}
  .st-key-recents [data-testid="stMarkdownContainer"] {{ margin-bottom: 0; }}
  .lib-recents {{ font-size: .8rem; color: {INDIGO}; font-weight: 600; padding-bottom: 2px; }}
  .st-key-recents button {{ background: rgba(255,255,255,.75); border: none; border-radius: 14px; min-height: 0;
                            padding: 3px 12px; }}
  .st-key-recents button p {{ font-size: .8rem; }}
  /* --- Fenêtre de choix --- */
  div[role="dialog"] {{ border-radius: 22px; }}
  /*   familles en pilules (onglet actif en indigo, comme la barre des onglets) */
  [data-testid="stDialog"] [data-testid="stButtonGroup"] {{ gap: 8px; }}
  [data-testid="stDialog"] [data-testid="stButtonGroup"] button {{ border-radius: 20px !important; border: none;
      background: #F1EFEA; color: {GRIS}; font-weight: 600; padding: 4px 16px; }}
  [data-testid="stDialog"] [data-testid="stButtonGroup"] button[aria-checked="true"],
  [data-testid="stDialog"] [data-testid="stButtonGroup"] button[aria-checked="true"]:hover {{
      background: {INDIGO}; color: white; }}
  [data-testid="stDialog"] [data-testid="stButtonGroup"] button:last-child {{ background: white;
      border: 1.5px dashed {TEAL}; color: {TEAL}; }}
  [data-testid="stDialog"] [data-testid="stButtonGroup"] button:last-child[kind="segmented_controlActive"] {{
      background: {TEAL}; color: white; }}
  .etape {{ font-size: .85rem; font-weight: 700; color: {INDIGO}; margin: 4px 0 6px; }}
  .etape .num {{ display: inline-flex; width: 20px; height: 20px; border-radius: 50%; background: {BLEU_MENU};
                 color: {INDIGO}; align-items: center; justify-content: center; font-size: .75rem; margin-right: 6px; }}
  .etape small {{ font-weight: 400; color: {GRIS_DOUX}; margin-left: 6px; }}
  /* tuile = dessin HTML + bouton Streamlit transparent posé par-dessus (toute la tuile est cliquable) */
  [class*="st-key-tuile_"] {{ position: relative; }}
  /*   l'enveloppe Streamlit du bouton (stElementContainer) couvre toute la tuile ; le bouton la remplit */
  [class*="st-key-tuile_"] > [data-testid="stElementContainer"]:has([data-testid="stButton"]) {{
      position: absolute; inset: 0; margin: 0; z-index: 2; }}
  [class*="st-key-tuile_"] [data-testid="stButton"], [class*="st-key-tuile_"] [data-testid="stButton"] > div,
  [class*="st-key-tuile_"] [data-testid="stButton"] button {{ width: 100%; height: 100%; }}
  [class*="st-key-tuile_"] [data-testid="stButton"] button {{ opacity: 0; cursor: pointer; }}
  [class*="st-key-tuile_"]:hover .tuile:not(.choisie) {{ border-color: #C9C6BF; background: white; }}
  .tuile {{ border-radius: 14px; border: 1.5px solid #EEECE7; background: #FAF9F6; padding: 9px 12px; }}
  .tuile.choisie {{ border: 2.5px solid var(--c); background: var(--fond-choisi); }}
  .tuile.zone .code {{ font-size: 1.2rem; font-weight: 800; line-height: 1.1; }}
  .tuile.zone .station {{ font-size: .75rem; color: {GRIS_DOUX}; }}
  .tuile .jauge {{ height: 6px; border-radius: 3px; background: #EEECE7; margin: 7px 0 4px; overflow: hidden; }}
  .tuile .jauge div {{ height: 100%; border-radius: 3px; }}
  .tuile .chiffre {{ font-size: .72rem; color: {GRIS_DOUX}; }}
  .tuile .chiffre b {{ color: {GRIS}; font-size: .8rem; }}
  .legende-zones {{ font-size: .72rem; color: {GRIS_DOUX}; padding: 6px 4px; line-height: 1.35; }}
  .legende-zones .degrade {{ height: 7px; border-radius: 4px; margin: 6px 0 3px;
                             background: linear-gradient(90deg, {CARAMEL}, {CORAIL}); }}
  .legende-zones .bornes {{ display: flex; justify-content: space-between; }}
  .tuile.fichier {{ margin-bottom: 8px; padding: 11px 14px; }}
  .tuile.fichier.choisie {{ background: white; box-shadow: {OMBRE}; }}
  .tuile.fichier .haut {{ display: flex; align-items: center; gap: 8px; }}
  .tuile.fichier .nom {{ font-weight: 700; font-size: 1rem; margin-right: auto; }}
  .tuile.fichier .desc {{ font-size: .78rem; color: {GRIS_DOUX}; margin: 3px 0 7px; line-height: 1.35; }}
  .tuile.fichier .chiffres {{ display: flex; gap: 18px; }}
  .tuile.fichier .chiffres div {{ font-size: .72rem; color: {GRIS_DOUX}; }}
  .tuile.fichier .chiffres b {{ display: block; font-size: 1.05rem; color: {GRIS}; }}
  .tuile.fichier .chiffres b.rouge {{ color: {CORAIL}; }}
  .tuile.fichier .chiffres b.nuit {{ color: {INDIGO}; }}
  .badge {{ font-size: .68rem; border-radius: 10px; padding: 2px 8px; font-weight: 600; }}
  .badge.defaut {{ background: {CARAMEL}; color: {GRIS}; }}
  .badge.encours {{ background: {BLEU_CLAIR}; color: #13628f; }}
  .pied-fenetre {{ font-size: .8rem; color: {GRIS_DOUX}; margin-top: 10px; padding-top: 10px;
                   border-top: 1px solid #EEECE7; }}
  .st-key-dlg_analyser button, .st-key-dlg_comparer_second button {{ border-radius: 22px; border: none;
      font-weight: 600; color: white; }}
  .st-key-dlg_analyser button {{ background: {CORAIL}; }}
  .st-key-dlg_comparer_second button {{ background: {TEAL}; }}
  .st-key-dlg_comparer button {{ border-radius: 22px; border: 1.5px solid {INDIGO}; color: {INDIGO}; font-weight: 600; }}
  /* --- Onglet Exporter --- */
  .titre-onglet {{ font-size: 1.9rem; font-weight: 800; margin: 10px 0 0; }}
  .sous-onglet {{ color: {GRIS_DOUX}; font-size: .95rem; margin-bottom: 10px; }}
  .st-key-choix_export, .st-key-carte_copier, .st-key-carte_csv {{ background: white; border-radius: {RAYON};
      box-shadow: {OMBRE}; padding: 14px 18px; }}
  .lib-groupe {{ font-size: .75rem; letter-spacing: .06em; text-transform: uppercase; color: {GRIS_DOUX};
                 font-weight: 700; margin-bottom: 4px; }}
  .puces-export {{ display: flex; flex-wrap: wrap; gap: 6px; }}
  .puces-export .puce {{ background: {CARAMEL_CLAIR}; border: 1px solid {CARAMEL}; border-radius: 12px;
                         padding: 1px 9px; font-size: .78rem; }}
  .entete-carte {{ display: flex; align-items: center; gap: 10px; }}
  .entete-carte .num {{ width: 26px; height: 26px; border-radius: 50%; background: {BLEU_MENU}; color: {INDIGO};
                        font-weight: 800; display: inline-flex; align-items: center; justify-content: center; flex: none; }}
  .entete-carte h3 {{ margin: 0; padding: 0; font-size: 1.2rem; }}
  .st-key-choix_export [data-testid="stButtonGroup"] button, .st-key-carte_copier [data-testid="stButtonGroup"] button,
  .st-key-carte_csv [data-testid="stButtonGroup"] button {{ border-radius: 20px !important; border: none;
      background: #F1EFEA; color: {GRIS}; font-weight: 600; }}
  .st-key-choix_export [data-testid="stButtonGroup"] button[aria-checked="true"],
  .st-key-carte_copier [data-testid="stButtonGroup"] button[aria-checked="true"],
  .st-key-carte_csv [data-testid="stButtonGroup"] button[aria-checked="true"],
  .st-key-choix_export [data-testid="stButtonGroup"] button[aria-checked="true"]:hover,
  .st-key-carte_copier [data-testid="stButtonGroup"] button[aria-checked="true"]:hover,
  .st-key-carte_csv [data-testid="stButtonGroup"] button[aria-checked="true"]:hover {{ background: {INDIGO}; color: white; }}
  .st-key-carte_copier [data-testid="stCode"] code {{ font-size: .78rem; }}
  .bloc-tete {{ background: {CARAMEL_CLAIR}; padding: 8px 12px; border-radius: 12px; font: .74rem/1.55 monospace;
                color: #7a5a2c; white-space: nowrap; overflow-x: auto; margin-bottom: 8px; }}
  .bloc-tete b {{ color: {GRIS}; }}
  .apercu {{ border: 1px solid #E6E4DF; border-radius: 12px; overflow-x: auto; font-size: .74rem; margin-bottom: 10px; }}
  .bloc-tete + div .apercu, .bloc-tete ~ .apercu {{ border-top-left-radius: 0; border-top-right-radius: 0; }}
  .apercu table {{ width: 100%; border-collapse: collapse; font-family: monospace; }}
  .apercu th {{ background: #F7F6F3; text-align: right; padding: 5px 7px; border-bottom: 1.5px solid {TRAIT};
                white-space: nowrap; font-weight: 700; }}
  .apercu td {{ text-align: right; padding: 3px 7px; border-bottom: 1px solid #F0EEEA; white-space: nowrap; }}
  .apercu th:nth-child(-n+2), .apercu td:nth-child(-n+2) {{ text-align: left; }}
  .apercu td.dh {{ color: #9C5A12; }}
  .apercu tr.trous td {{ color: {GRIS_DOUX}; text-align: left; background: #FBFAF8; font-family: Inter, sans-serif;
                         padding-left: 120px; }}
  .st-key-export_telecharger button {{ background: {CORAIL}; border: none; border-radius: 22px; font-weight: 700;
                                        color: white; }}
  .nom-export {{ font-size: .78rem; color: {GRIS_DOUX}; line-height: 1.4; word-break: break-all; }}
  .nom-export b {{ color: {GRIS}; font-family: monospace; font-weight: 600; }}
  .pied {{ color: {GRIS_DOUX}; font-size: .75rem; border-top: 1px solid {TRAIT}; margin-top: 18px; padding-top: 6px;
           display: flex; justify-content: space-between; }}
</style>
"""


# ============================================================
# OUTILS
# ============================================================

def melange(hexa: str, part: float) -> str:
    """Couleur mêlée de blanc (part = proportion de la couleur) → hex opaque."""
    h = hexa.lstrip("#")
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(255 - (255 - c) * part):02x}" for c in rgb)


def _icone(nom: str, taille: int = 18, epaisseur: float = 2) -> str:
    return (f'<svg width="{taille}" height="{taille}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="{epaisseur}" stroke-linecap="round" stroke-linejoin="round">{ICONES[nom]}</svg>')


def logo_onde() -> str:
    """Logo : une onde de température (oscillation qui s'amplifie), trait blanc sur rond indigo."""
    return ('<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round"><path d="{TRACE_LOGO}"/></svg>')


# ============================================================
# EN-TÊTE ET NOM DU FICHIER
# ============================================================

def haut_de_page(serie, onglets: list, cle_onglet: str) -> str:
    """
    Bloc fixé en haut de la page : en-tête, barre des onglets, nom du fichier en cours.
    Renvoie l'onglet choisi (seul son contenu est calculé ensuite).
    """
    st.markdown(CSS, unsafe_allow_html=True)
    st.session_state.setdefault(cle_onglet, onglets[0])
    with st.container(key="haut_fixe"):
        st.markdown(
            f'<div class="entete"><div class="logo">{logo_onde()}</div>'
            f'<div><div class="nom">Météo et Chaleur</div>'
            f'<div class="sous">Analyser la météo sous l\'angle de l\'inconfort d\'été</div></div>'
            f'<div class="version">v<b>{VERSION}</b> · {STATUT_VERSION}</div></div>', unsafe_allow_html=True)
        with st.container(key="barre_onglets"):
            onglet = st.segmented_control("Onglets", onglets, key=cle_onglet, required=True,
                                          label_visibility="collapsed")
        titre_fichier(serie)
    return onglet or onglets[0]


def description_fichier(serie) -> str:
    """« Trappes · année type · Scénarios météo RE2020 … · base horaire UTC »."""
    m = serie.meta
    morceaux = [m.get("station"), m.get("periode"), m.get("description"), m.get("source"),
                f"base horaire {m['base_horaire']}" if m.get("base_horaire") else None]
    return " · ".join(str(x) for x in morceaux if x)


def titre_fichier(serie, couleur=CORAIL):
    """Nom du fichier en gros entre la barre des onglets et les cartes (point de la couleur du fichier)."""
    st.markdown(f'<div class="fichier"><div class="nom"><span class="point" style="background:{couleur}"></span>'
                f'{html.escape(serie.libelle)}</div>'
                f'<div class="meta">{html.escape(description_fichier(serie))}</div></div>', unsafe_allow_html=True)


# ============================================================
# CARTES D'INDICATEURS
# ============================================================

def _statuts_cites(texte, hyp):
    """Statuts non « sourcé » des hypothèses citées par [[hyp:…]] dans un texte."""
    return sorted({hyp[i]["statut"] for i in MOTIF_REPERE.findall(texte or "") if i in hyp
                   and hyp[i]["statut"] != "sourcé"})


def mini_graphique(profil, couleur, unite, decimales, fond_clair) -> str:
    """Petit graphique SVG de la carte : barres ou ligne par mois, ou bande des nuits (une case par nuit)."""
    if profil is None:
        return ""
    v = profil["valeurs"]
    larg, haut, h_lib = LARGEUR_MINI, HAUTEUR_MINI, HAUTEUR_LIBELLES
    attenue = melange(couleur, 0.25) if fond_clair else "rgba(255,255,255,.35)"
    if profil["type"] == "jauge":
        return _jauge(float(v), couleur, attenue, larg, haut + h_lib)
    if profil["type"] == "bande":
        if len(v) < 2:
            return ""
        pas = larg / len(v)
        cases = "".join(f'<rect x="{i * pas:.2f}" y="{haut - 16}" width="{max(pas - 0.4, 0.6):.2f}" height="16" '
                        f'fill="{couleur if chaud else attenue}"><title>nuit du {d.day} {MOIS_COURTS[d.month - 1]}'
                        f'{" : tropicale" if chaud else ""}</title></rect>' for i, (d, chaud) in enumerate(v.items()))
        lib = (f'<text x="0" y="{haut + h_lib - 1}" font-size="8.5" fill="currentColor" opacity=".7">'
               f'{MOIS_COURTS[v.index[0].month - 1]}</text><text x="{larg}" y="{haut + h_lib - 1}" font-size="8.5" '
               f'text-anchor="end" fill="currentColor" opacity=".7">{MOIS_COURTS[v.index[-1].month - 1]}</text>')
        return f'<svg class="mini" width="{larg}" height="{haut + h_lib}">{cases}{lib}</svg>'
    if len(v) < 2:
        return ""
    mois, valeurs = list(v.index), [float(x) for x in v.values]
    n, vmax = len(valeurs), max(max(valeurs), 1e-9)
    pas = larg / n
    libelles = "" if n > NB_MOIS_LIBELLES else "".join(
        f'<text x="{(i + 0.5) * pas:.1f}" y="{haut + h_lib - 1}" font-size="8.5" text-anchor="middle" '
        f'fill="currentColor" opacity=".7">{MOIS_COURTS[m - 1]}</text>' for i, m in enumerate(mois))
    if profil["type"] == "barres":
        barres = "".join(
            f'<rect x="{i * pas + pas * 0.2:.1f}" y="{haut - max(haut * x / vmax, 1.5):.1f}" width="{pas * 0.6:.1f}" '
            f'height="{max(haut * x / vmax, 1.5):.1f}" rx="2" fill="{couleur}">'
            f'<title>{MOIS_COURTS[m - 1]} : {nombre(x, decimales)} {unite}</title></rect>'
            for i, (m, x) in enumerate(zip(mois, valeurs)))
        return f'<svg class="mini" width="{larg}" height="{haut + h_lib}">{barres}{libelles}</svg>'
    vmin = min(valeurs)
    etendue = max(vmax - vmin, 1e-9)
    pts = [((i + 0.5) * pas, 3 + (haut - 6) * (1 - (x - vmin) / etendue)) for i, x in enumerate(valeurs)]
    trace = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    points = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{couleur}"><title>{MOIS_COURTS[m - 1]} : '
                     f'{nombre(val, 1)} {unite}</title></circle>' for (x, y), m, val in zip(pts, mois, valeurs))
    return (f'<svg class="mini" width="{larg}" height="{haut + h_lib}"><polyline points="{trace}" fill="none" '
            f'stroke="{couleur}" stroke-width="2" stroke-linejoin="round"/>{points}{libelles}</svg>')


def _jauge(part, couleur, fond_arc, larg, haut) -> str:
    """Demi-cercle de progression (part entre 0 et 1) avec le pourcentage au centre."""
    part = min(max(part, 0.0), 1.0)
    e = EPAISSEUR_JAUGE
    r = min(larg / 2, haut) - e / 2 - 1
    cx, cy = larg / 2, haut - 1
    angle = np.pi * part
    fin_x, fin_y = cx - r * np.cos(angle), cy - r * np.sin(angle)
    arc_fond = f'M {cx - r:.1f} {cy:.1f} A {r:.1f} {r:.1f} 0 0 1 {cx + r:.1f} {cy:.1f}'
    arc = f'M {cx - r:.1f} {cy:.1f} A {r:.1f} {r:.1f} 0 0 1 {fin_x:.1f} {fin_y:.1f}'
    return (f'<svg class="mini" width="{larg}" height="{haut}"><title>{nombre(100 * part, 0)} % des DH la nuit</title>'
            f'<path d="{arc_fond}" fill="none" stroke="{fond_arc}" stroke-width="{e}"/>'
            + (f'<path d="{arc}" fill="none" stroke="{couleur}" stroke-width="{e}"/>' if part > 0 else "")
            + f'<text x="{cx:.1f}" y="{cy - 2:.1f}" font-size="13" font-weight="700" text-anchor="middle" '
            f'fill="currentColor">{nombre(100 * part, 0)} %</text></svg>')


def valeur_texte(valeur, decimales: int) -> str:
    return "—" if valeur is None else nombre(valeur, decimales)


def cartes(resultats, hyp):
    """Cartes d'indicateurs dans l'ordre reçu ; fond teinté de la couleur de la carte, DH en couleur pleine."""
    blocs = []
    for d, r in resultats:
        c = COULEURS_CARTES.get(d["id"], TEAL)
        principale = d["id"] == CARTE_PRINCIPALE
        titre = html.escape(remplacer_reperes(d["libelle"], hyp))
        dec = int(d.get("decimales", 0) or 0)
        bulle = html.escape(remplacer_reperes(d["bulle"], hyp))
        statuts = "".join(f'<br><span class="statut" style="color:{COULEURS_STATUT[s]};border-color:{COULEURS_STATUT[s]}">'
                          f'source : {s}</span>' for s in _statuts_cites(d["bulle"] + d["libelle"], hyp))
        mini = mini_graphique(r.info.get("profil"), "white" if principale else c, d["unite"], dec, not principale)
        blocs.append(
            f'<div class="carte{" principale" if principale else ""}" style="--c:{c};'
            f'--fond:{melange(c, PART_TEINTE_FOND)};--icone:{melange(c, PART_TEINTE_ICONE)}">'
            f'<div class="haut"><div class="icone">{_icone(ICONE_INDICATEUR.get(d["id"], "thermometre"))}</div>'
            f'<div class="titre">{titre}</div></div>'
            f'<div class="info">i<div class="bulle"><b>{titre}</b><br>{bulle}{statuts}'
            f'<br><span style="color:{TEAL};font-weight:600">Détail : onglet Méthode & sources</span></div></div>'
            f'<div class="milieu"><div class="valeur">{valeur_texte(r.valeur, dec)}<span>{html.escape(d["unite"])}</span></div>'
            f'{mini}</div><div class="detail">{html.escape(r.detail)}</div></div>')
    st.markdown(f'<div class="cartes">{"".join(blocs)}</div>', unsafe_allow_html=True)


# ============================================================
# BANDEAU DES HYPOTHÈSES, PASTILLES, PIED
# ============================================================

def bandeau_hypotheses(reglage, analyse, hyp, libelles_semaine, aller_methode=None):
    puces = []
    if analyse.methode_effective == "RE2020":
        puces += [f"RE2020 · seuil {hyp['seuil_nuit_dh']['valeur']:g} → {hyp['seuil_jour_max']['valeur']:g} °C",
                  "température extérieure lissée (RE2020)"]
    else:
        puces.append(f"basic · {hyp['seuil_nuit_dh']['valeur']:g} °C nuit / {hyp['seuil_jour_max']['valeur']:g} °C jour")
    puces.append("occupation logement (provisoire)" if reglage["occupation"] else "24h/24, sans occupation")
    puces.append(f"nuit {hyp['nuit_debut']['valeur']:g}h-{hyp['nuit_fin']['valeur']:g}h")
    if analyse.serie.decalage_utc:
        puces.append(f"heure légale = UTC + {analyse.serie.decalage_utc}")
    puces.append(f"semaine : {libelles_semaine[reglage['critere_semaine']].lower()}")
    contenu = "".join(f'<span class="puce">{html.escape(p)}</span>' for p in puces)
    col_puces, col_lien = st.columns([8, 1.3], vertical_alignment="center")
    col_puces.markdown(f'<div class="hypos"><b>Hypothèses actives :</b>{contenu}</div>', unsafe_allow_html=True)
    if aller_methode is not None:                      # lien fonctionnel vers l'onglet Méthode & sources
        col_lien.button("Méthode & sources ›", on_click=aller_methode, type="tertiary", key="lien_methode")
    if analyse.message_methode:
        st.markdown(f'<div class="message">⚠ {html.escape(analyse.message_methode)}</div>', unsafe_allow_html=True)


def pastille_ecart(ecart: float, unite: str, decimales: int = 0) -> str:
    """Écart en pastille : rouge = plus chaud, bleu = plus frais, gris = égal."""
    if round(ecart, decimales) == 0:
        fond, texte, signe = "#EEEDEA", GRIS_DOUX, ""
    elif ecart > 0:
        fond, texte, signe = melange(CORAIL, 0.16), "#C23B3C", "+"
    else:
        fond, texte, signe = BLEU_CLAIR, BLEU_FRAIS, "−"
    return (f'<span class="pastille" style="background:{fond};color:{texte}">'
            f'{signe}{nombre(abs(ecart), decimales)} {html.escape(unite)}</span>')


def cartouche(role: str, serie, couleur: str):
    """Contenu HTML d'un cartouche de fichier (onglet Comparer) : rôle, nom dans sa couleur, description."""
    st.markdown(f'<div class="cartouche"><div class="role">{html.escape(role)}</div>'
                f'<div class="nom" style="color:{couleur}">{html.escape(serie.libelle)}</div>'
                f'<div class="meta">{html.escape(description_fichier(serie))}</div></div>', unsafe_allow_html=True)


def tableau_html(df: pd.DataFrame) -> str:
    """Tableau simple (sans pyarrow), dans une carte blanche."""
    return f'<div class="tableau">{df.to_html(index=False, escape=True, border=0)}</div>'


def pied():
    st.markdown(
        f'<div class="pied"><span>Note : indicateur climatique — DH calculés sur la température extérieure, '
        f'pas le DH d\'un bâtiment · méthode RE2020 (arrêté du 4 août 2021, annexe III)</span>'
        f'<span>outil v{VERSION} · pythermalcomfort {PTC_VERSION}</span></div>', unsafe_allow_html=True)
