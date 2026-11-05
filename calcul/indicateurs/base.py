"""
============================================================
 INDICATEURS — ce qu'un indicateur doit fournir
============================================================
 Chaque fichier de calcul/indicateurs/ (sauf base.py et les noms
 commençant par « _ ») décrit UN indicateur : il définit une
 variable INDICATEUR = Indicateur(...). Le fichier porte le nom
 de l'identifiant (dh.py → « dh »).

 Le code de l'indicateur vit ici ; ses TEXTES (libellé, unité,
 bulle « i », ordre par défaut, décimales, affiché ou non) vivent
 dans docs/sources/hypotheses.xlsx, onglet « indicateurs ».
 Modèle commenté : calcul/indicateurs/_modele.py.
============================================================
"""

from dataclasses import dataclass, field
from typing import Callable

# ============================================================
# PARAMÈTRES
# ============================================================
TEINTES = ("chaud", "nuit", "moyenne")                       # couleur de la carte (config/charte.py)
ICONES = ("soleil", "lune", "horloge", "calendrier", "thermometre")   # dessins de interface/cartes.py
MODES_AMPLEUR = ("relatif", "absolu")                        # écart en % ou dans l'unité de l'indicateur
MODE_AMPLEUR_DEFAUT, SEUIL_AMPLEUR_DEFAUT = "relatif", 100   # indicateur absent de AMPLEUR_INDICATEURS


@dataclass
class Resultat:
    """Valeur d'un indicateur pour une série : None = non calculable."""
    valeur: float | None
    detail: str = ""                     # petite ligne sous la valeur de la carte
    info: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Indicateur:
    """
    id         : identifiant, identique au nom du fichier et à la colonne « id » de l'Excel ;
    calculer   : fonction (analyse, reglage, hyp) → Resultat ;
    profil     : fonction (analyse, hyp) → mini-graphique de la carte, ou None
                 ({"type": "barres" | "ligne", "valeurs": série par mois}, {"type": "bande", "valeurs": booléens
                 par nuit}, {"type": "jauge", "valeurs": part entre 0 et 1}) ;
    teinte     : « chaud » (rouge), « nuit » (foncé) ou « moyenne » (bleu canard) ;
    icone      : dessin de la carte (voir ICONES) ;
    principale : carte en couleur pleine (une seule : le DH) ;
    mode_ampleur, seuil_ampleur : jauge de l'onglet Comparer, mode (voir MODES_AMPLEUR) et écart d'une jauge pleine
                 (en % si relatif, en unité sinon). Valeurs réglées dans config/reglages.py, AMPLEUR_INDICATEURS.
    """
    id: str
    calculer: Callable
    profil: Callable | None = None
    teinte: str = "moyenne"
    icone: str = "thermometre"
    principale: bool = False
    mode_ampleur: str = MODE_AMPLEUR_DEFAUT
    seuil_ampleur: float = SEUIL_AMPLEUR_DEFAUT

    def __post_init__(self):
        if self.teinte not in TEINTES:
            raise ValueError(f"indicateur {self.id} : teinte « {self.teinte} » inconnue ({', '.join(TEINTES)})")
        if self.icone not in ICONES:
            raise ValueError(f"indicateur {self.id} : icône « {self.icone} » inconnue ({', '.join(ICONES)})")
        if self.mode_ampleur not in MODES_AMPLEUR:
            raise ValueError(f"indicateur {self.id} : mode d'ampleur « {self.mode_ampleur} » inconnu "
                             f"({', '.join(MODES_AMPLEUR)})")
        if self.seuil_ampleur <= 0:
            raise ValueError(f"indicateur {self.id} : le seuil d'ampleur doit être positif")
