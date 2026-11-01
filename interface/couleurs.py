"""
============================================================
 COULEURS — conversions hexadécimal → rgba, mélanges, dégradés
============================================================
 Une seule lecture des codes « #rrggbb » pour tout l'outil
 (graphiques, cartes, fenêtre de choix).
============================================================
"""


def rgb(hexa: str) -> tuple:
    """« #f05d5e » → (240, 93, 94)."""
    h = hexa.lstrip("#")
    return tuple(int(h[k:k + 2], 16) for k in (0, 2, 4))


def transparent(hexa: str, alpha: float) -> str:
    """Couleur avec transparence, au format Plotly / CSS « rgba(r,g,b,a) »."""
    r, g, b = rgb(hexa)
    return f"rgba({r},{g},{b},{alpha})"


def melange(hexa: str, part: float) -> str:
    """Couleur mêlée de blanc (part = proportion de la couleur) → hex opaque."""
    return "#" + "".join(f"{round(255 - (255 - c) * part):02x}" for c in rgb(hexa))


def degrade(depart: str, arrivee: str, part: float) -> str:
    """Couleur intermédiaire entre deux couleurs (part = 0 → départ, 1 → arrivée)."""
    return "#" + "".join(f"{round(x + (y - x) * part):02x}" for x, y in zip(rgb(depart), rgb(arrivee)))
