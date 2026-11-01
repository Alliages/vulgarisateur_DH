"""
============================================================
 MODÈLE D'INDICATEUR — à copier, pas à modifier
============================================================
 1. Copier ce fichier sous le nom <identifiant>.py (ex. heures_32.py),
    dans ce dossier. Le nom commence sans « _ » : il est alors
    inscrit automatiquement au registre.
 2. Écrire `calculer` (et `profil` si la carte a un mini-graphique).
 3. Ajouter la ligne <identifiant> dans docs/sources/hypotheses.xlsx,
    onglet « indicateurs » (libellé, unité, ordre, actif, bulle,
    décimales), puis : python outils/convertir_docs.py
 4. Tester : python -m pytest
 Un seuil nouveau ? L'ajouter dans l'onglet « hypotheses » de
 l'Excel et le lire avec valeur(hyp, "<id>") : jamais en dur.

 Ce que l'analyse `a` met à disposition (calcul/analyse.py) :
   a.serie.t, a.serie.horodatage   températures horaires, heure légale
   a.dh_h, a.seuil                 DH et seuil de chaque heure
   a.est_jour, a.est_nuit, a.est_ete   masques horaires
   a.jours                         par jour : tmoy, tmax, tmin, dh
   a.nuits                         Tmin de chaque nuit complète
============================================================
"""

from calcul.analyse import par_mois
from calcul.hypotheses import valeur
from calcul.indicateurs.base import Indicateur, Resultat


def calculer(a, reglage, hyp):
    """Exemple : nombre d'heures au-dessus d'un seuil lu dans les hypothèses."""
    seuil = valeur(hyp, "seuil_heures_chaudes")
    return Resultat(int((a.serie.t > seuil).sum()), f"T > {seuil:g} °C")


def profil(a, hyp):
    """Facultatif : mini-graphique (ici, une barre par mois d'été)."""
    return {"type": "barres", "valeurs": par_mois(a, a.serie.t > valeur(hyp, "seuil_heures_chaudes"), "sum")}


INDICATEUR = Indicateur(id="_modele", calculer=calculer, profil=profil, teinte="chaud", icone="horloge")
