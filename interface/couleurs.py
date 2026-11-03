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


def degrade_tsl(depart: str, arrivee: str, part: float, saturation_max: float) -> str:
    """
    Dégradé en teinte / luminosité, saturation plafonnée (0 → départ, 1 → arrivée).
    Entre deux teintes éloignées (vert → orange), un mélange RVB passe par un gris kaki : ici la teinte
    tourne par un vert-jaune, dont la saturation est plafonnée pour rester doux.
    """
    import colorsys
    (h1, l1, s1), (h2, l2, s2) = (colorsys.rgb_to_hls(*(c / 255 for c in rgb(x))) for x in (depart, arrivee))
    sat = min(s1 + (s2 - s1) * part, saturation_max + (s2 - saturation_max) * part ** 3)
    r, g, b = colorsys.hls_to_rgb(h1 + (h2 - h1) * part, l1 + (l2 - l1) * part, sat)
    return "#" + "".join(f"{round(255 * x):02x}" for x in (r, g, b))


def degrade_dh(part: float) -> str:
    """Couleur d'un DH sur l'échelle de l'outil (part 0 → 1) : vert → caramel → corail (fenêtre de choix, 0.9.10)."""
    from config.charte import CARAMEL, CORAIL, SATURATION_MAX_VERT, VERT
    part = min(1.0, max(0.0, part))
    if part < 0.5:
        return degrade_tsl(VERT, CARAMEL, 2 * part, SATURATION_MAX_VERT)
    return degrade(CARAMEL, CORAIL, 2 * part - 1)
