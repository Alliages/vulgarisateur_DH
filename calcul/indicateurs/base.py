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
    principale : carte en couleur pleine (une seule : le DH).
    """
    id: str
    calculer: Callable
    profil: Callable | None = None
    teinte: str = "moyenne"
    icone: str = "thermometre"
    principale: bool = False

    def __post_init__(self):
        if self.teinte not in TEINTES:
            raise ValueError(f"indicateur {self.id} : teinte « {self.teinte} » inconnue ({', '.join(TEINTES)})")
        if self.icone not in ICONES:
            raise ValueError(f"indicateur {self.id} : icône « {self.icone} » inconnue ({', '.join(ICONES)})")
