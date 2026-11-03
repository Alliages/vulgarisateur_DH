"""
============================================================
 CARTE DES ZONES + LISTE DES FICHIERS (fenêtre de choix, 0.9.10)
============================================================
 Un composant Streamlit (st.components.v2) qui dessine, pour une
 famille de fichiers (RE2020, Observations, TRACC…) :
   - à gauche, une mini carte de France : départements colorés
     selon leur zone (dégradé vert → caramel → corail, DH du fichier
     « Th-D canicule » de la zone, réglage RE2020), une étiquette
     « zone · nombre de fichiers » et un point par station ;
   - à droite, les fichiers groupés par zone : nom, barre et chiffre
     du DH, nuits ≥ 20 °C.
 Clic sur une zone (étiquette ou département) : la liste ne garde
 que cette zone ; nouveau clic ou « ✕ Toutes les zones » : tout revoir.
 Clic sur un fichier : il devient le fichier choisi (rappel Python).

 Placement des points : latitude / longitude du catalogue si elles
 sont renseignées (facultatives), sinon centre du département
 (colonne « departement »), sinon centre de la zone.

 Contours et projection : config/carte_france.json, repris de la
 carte zones-climatiques-re2020.
============================================================
"""

import html
import json
import os
from collections import Counter

import streamlit as st

from calcul.format_fr import nombre
from config.charte import CORAIL, GRIS, GRIS_DOUX, INDIGO, TRAIT
from config.reglages import DH_ECHELLE_CHOIX
from interface.couleurs import degrade_dh, melange

# ============================================================
# PARAMÈTRES
# ============================================================
CHEMIN_CARTE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "carte_france.json")
CADRAGE = "80 40 940 900"                 # partie du viewBox montrée (France métropolitaine et Corse)
ZONES = ["H1a", "H1b", "H1c", "H2a", "H2b", "H2c", "H2d", "H3"]
DECALAGE_ETIQUETTES = {"H1a": (-30, -55), "H1b": (10, 0), "H1c": (-75, 30), "H2a": (0, -10),   # unités du viewBox,
                       "H2b": (10, 30), "H2c": (-10, 30), "H2d": (45, -40), "H3": (40, 40)}    # depuis le centre de la zone
ECART_POINTS = 14                          # points superposés (même département) : écartés de ce rayon
PASTILLE = {"largeur": 120, "hauteur": 50, "marge": 6, "pas": 10}   # pastilles « zone · n » (unités du viewBox) :
                                           # taille, marge libre autour, pas de la recherche de place
TEXTE_LEGENDE = "Teinte : DH « Th-D canicule » de la zone (RE2020)"
TEXTE_SOUS_LISTE = "DH (réglage RE2020 ; méthode basic pour une série partielle) · nuits ≥ 20 °C"


# ============================================================
# DONNÉES FIXES : CONTOURS DES DÉPARTEMENTS
# ============================================================
with open(CHEMIN_CARTE, encoding="utf-8") as _f:
    CARTE = json.load(_f)
_A_LON, _B_LON = CARTE["projection"]["x"]
_A_LAT, _B_LAT = CARTE["projection"]["y"]


def projeter(lat, lon):
    """Latitude / longitude (degrés) → point du viewBox de la carte."""
    return round(_A_LON * float(lon) + _B_LON, 1), round(_A_LAT * float(lat) + _B_LAT, 1)


_CHEMINS = "".join(f'<path class="dep" data-code="{d["code"]}" data-zone="{d["zone"]}" d="{d["d"]}"/>'
                   for d in CARTE["departements"])

# ============================================================
# COMPOSANT (HTML, CSS, JS)
# ============================================================
HTML = f"""
<div class="cz">
  <div class="gauche">
    <svg viewBox="{CADRAGE}" role="img" aria-label="Carte des zones climatiques"><g class="deps">{_CHEMINS}</g>
      <g class="marques"></g></svg>
    <div class="legende"><span>{html.escape(TEXTE_LEGENDE)}</span><i class="degrade"></i></div>
  </div>
  <div class="droite">
    <div class="titre"></div>
    <div class="sous">{html.escape(TEXTE_SOUS_LISTE)}</div>
    <div class="liste"></div>
  </div>
</div>
"""

CSS = f"""
.cz {{ display: grid; grid-template-columns: minmax(220px, 34%) 1fr; gap: 22px; font-family: Inter, 'Segoe UI', sans-serif;
      color: {GRIS}; }}
.gauche svg {{ width: 100%; height: auto; display: block; }}
.dep {{ stroke: #fff; stroke-width: .6; stroke-opacity: .6; cursor: pointer; transition: opacity .15s; }}
.dep.pale {{ opacity: .25; }}
.dep:hover {{ opacity: .85; }}
.bz {{ fill: #fff; fill-opacity: .72; stroke: {INDIGO}; stroke-opacity: .75; stroke-width: 1.5; }}
.bz.on {{ fill: {INDIGO}; fill-opacity: .88; }}
.lz {{ font-weight: 700; font-size: 30px; fill: {INDIGO}; }}
.lzc {{ font-weight: 600; font-size: 24px; fill: {INDIGO}; }}
.on-t {{ fill: #fff; }}
.etiquette {{ cursor: pointer; }}
.pt {{ fill: #fff; stroke: {INDIGO}; stroke-width: 3; }} .ptc {{ fill: {INDIGO}; }}
.pale-pt {{ opacity: .25; }}
.legende {{ font-size: 9px; color: #9a9aa3; margin-top: 2px; display: flex; align-items: center; gap: 6px; }}
.legende .degrade {{ display: inline-block; width: 60px; height: 4px; border-radius: 2px; }}
.titre {{ font-size: 13px; color: {GRIS_DOUX}; margin-bottom: 2px; display: flex; align-items: center; gap: 10px; }}
.titre b {{ color: {INDIGO}; }}
.tout {{ border: 1.5px solid {TRAIT}; border-radius: 999px; padding: 1px 10px; color: {INDIGO}; font-weight: 600;
        font-size: 12px; cursor: pointer; background: #fff; }}
.tout:hover {{ border-color: {INDIGO}; }}
.sous {{ font-size: 11px; color: {GRIS_DOUX}; margin-bottom: 10px; }}
.liste {{ columns: 2; column-gap: 22px; }}
.liste.une {{ columns: 1; max-width: 520px; }}
.zone {{ break-inside: avoid; margin-bottom: 12px; }}
.zt {{ display: flex; align-items: center; gap: 8px; margin-bottom: 3px; }}
.pz {{ font-weight: 700; font-size: 12.5px; color: {INDIGO}; padding: 1px 8px; border-radius: 7px; cursor: pointer; }}
.cpt {{ font-size: 12px; color: {GRIS_DOUX}; }}
.st {{ display: grid; grid-template-columns: minmax(130px, 1.5fr) 1fr 66px 24px; align-items: center; gap: 8px;
      font-size: 13px; padding: 4px 6px; border-bottom: 1px solid #F0EEEA; border-radius: 6px; cursor: pointer;
      border-left: 3px solid transparent; }}
.st:hover {{ background: #F6F5F2; }}
.st.choisi {{ border-left-color: var(--c); background: var(--fond-choisi); }}
.sn {{ font-weight: 600; white-space: nowrap; display: flex; align-items: baseline; gap: 5px; min-width: 0; }}
.sn .nm {{ overflow: hidden; text-overflow: ellipsis; min-width: 0; }}
.sn em {{ font-style: normal; font-weight: 500; font-size: 10.5px; color: {GRIS_DOUX}; flex: none; }}
.sn small {{ font-weight: 600; font-size: 9.5px; color: {GRIS_DOUX}; flex: none; }}
.barre {{ height: 7px; background: #F1EFEB; border-radius: 4px; overflow: hidden; }}
.barre i {{ display: block; height: 100%; border-radius: 4px; }}
.dh {{ text-align: right; font-weight: 700; color: {CORAIL}; white-space: nowrap; }}
.dh small {{ font-weight: 400; color: {GRIS_DOUX}; font-size: 10px; }}
.n20 {{ text-align: right; color: {INDIGO}; font-weight: 600; }}
.vide {{ font-size: 13px; color: {GRIS_DOUX}; padding: 8px 0; }}
@media (max-width: 760px) {{ .cz {{ grid-template-columns: 1fr; }} .gauche {{ max-width: 340px; }} .liste {{ columns: 1; }} }}
"""

JS = """
export default function (component) {
  const { data, parentElement, setStateValue, setTriggerValue } = component;
  if (!data) return;
  const racine = parentElement.querySelector(".cz");
  const svg = racine.querySelector("svg"), marques = racine.querySelector(".marques");
  const NS = "http://www.w3.org/2000/svg";
  let zone = data.zone || null;                         // zone filtrée (null = toutes)

  // --- Outils ---
  const centre = (el) => { const b = el.getBBox(); return [b.x + b.width / 2, b.y + b.height / 2, b.width * b.height]; };
  const centreZone = (z) => {                           // centre des départements de la zone, pondéré par leur surface
    let sx = 0, sy = 0, sa = 0;
    svg.querySelectorAll(`.dep[data-zone="${z}"]`).forEach((p) => { const [x, y, a] = centre(p); sx += x * a; sy += y * a; sa += a; });
    return sa ? [sx / sa, sy / sa] : null;
  };
  const el = (nom, attrs, texte, parent) => {
    const e = document.createElementNS(NS, nom);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (texte) e.textContent = texte;
    (parent || marques).appendChild(e);
    return e;
  };
  const choisirZone = (z) => {                          // clic sur une zone : filtre, ou tout revoir si déjà choisie
    zone = (z === zone || !data.compte[z]) ? null : z;
    setStateValue("zone", zone);
    dessiner();
  };

  // --- Carte : couleurs des départements (une fois) ---
  svg.querySelectorAll(".dep").forEach((p) => {
    p.setAttribute("fill", data.couleurs[p.dataset.zone] || "#E4E2DD");
    p.onclick = () => choisirZone(p.dataset.zone);
  });
  racine.querySelector(".legende .degrade").style.background = data.degrade;

  // --- Place des pastilles « zone · n » : dans leur zone, sans recouvrir un point ni une autre pastille ---
  //     Recherche sur une grille autour de la zone, la plus proche de la place préférée (centre + décalage).
  //     Niveau 2 : pastille entièrement dans la zone ; 1 : centre dans la zone ; 0 : n'importe où dans la carte.
  let positions = null;
  function placerPastilles(points) {
    const { largeur: L, hauteur: H, marge: M, pas } = data.pastille;
    const [vx, vy, vl, vh] = svg.getAttribute("viewBox").split(" ").map(Number);
    const deps = (z) => [...svg.querySelectorAll(`.dep[data-zone="${z}"]`)];
    const dedans = (chemins, x, y) => { const pt = new DOMPoint(x, y); return chemins.some((c) => c.isPointInFill(pt)); };
    const coins = [[-1, -1], [1, -1], [-1, 1], [1, 1], [0, -1], [0, 1], [-1, 0], [1, 0]];
    const posees = [], pos = {};
    const libre = (x, y) =>
      x - L / 2 >= vx && x + L / 2 <= vx + vl && y - H / 2 >= vy && y + H / 2 <= vy + vh
      && points.every(([px, py]) => Math.abs(px - x) > L / 2 + 10 + M || Math.abs(py - y) > H / 2 + 10 + M)
      && posees.every(([qx, qy]) => Math.abs(qx - x) > L + M || Math.abs(qy - y) > H + M);
    // zones les plus petites d'abord : elles ont le moins de place
    const surface = (z) => deps(z).reduce((s, c) => { const b = c.getBBox(); return s + b.width * b.height; }, 0);
    const ordre = Object.keys(data.compte).sort((a, b) => surface(a) - surface(b));
    for (const z of ordre) {
      const c = centreZone(z); if (!c) continue;
      const chemins = deps(z), d = data.decalages[z] || [0, 0], prefere = [c[0] + d[0], c[1] + d[1]];
      const b = chemins.map((x) => x.getBBox()).reduce((a, e) => ({ x0: Math.min(a.x0, e.x), y0: Math.min(a.y0, e.y),
        x1: Math.max(a.x1, e.x + e.width), y1: Math.max(a.y1, e.y + e.height) }), { x0: 1e9, y0: 1e9, x1: -1e9, y1: -1e9 });
      let meilleur = null;
      for (const niveau of [2, 1, 0]) {
        let score = Infinity;
        for (let x = b.x0 - L / 2; x <= b.x1 + L / 2; x += pas) {
          for (let y = b.y0 - H / 2; y <= b.y1 + H / 2; y += pas) {
            const s = (x - prefere[0]) ** 2 + (y - prefere[1]) ** 2;
            if (s >= score || !libre(x, y)) continue;
            if (niveau >= 1 && !dedans(chemins, x, y)) continue;
            if (niveau === 2 && !coins.every(([sx, sy]) => dedans(chemins, x + sx * L / 2, y + sy * H / 2))) continue;
            score = s; meilleur = [x, y];
          }
        }
        if (meilleur) break;
      }
      pos[z] = meilleur || prefere;
      posees.push(pos[z]);
    }
    return pos;
  }

  function dessiner() {
    // --- Départements : pâles hors de la zone choisie ---
    svg.querySelectorAll(".dep").forEach((p) => p.classList.toggle("pale", !!zone && p.dataset.zone !== zone));

    // --- Points des stations : coordonnées, sinon centre du département, sinon centre de la zone ---
    marques.innerHTML = "";
    const places = {}, occupes = [];
    for (const p of data.points) {
      let xy = p.x != null ? [p.x, p.y] : null;
      if (!xy && p.dep) { const d = svg.querySelector(`.dep[data-code="${p.dep}"]`); if (d) xy = centre(d).slice(0, 2); }
      if (!xy) xy = centreZone(p.zone);
      if (!xy) continue;
      const cle = xy.map((v) => Math.round(v / 6)).join(",");          // points superposés : écartés en cercle
      const n = (places[cle] = (places[cle] || 0) + 1) - 1;
      const x = xy[0] + (n ? data.ecart * Math.cos(n * 2.1) : 0), y = xy[1] + (n ? data.ecart * Math.sin(n * 2.1) : 0);
      const pale = zone && p.zone !== zone ? " pale-pt" : "";
      el("circle", { class: "pt" + pale, cx: x, cy: y, r: 10 });
      el("circle", { class: "ptc" + pale, cx: x, cy: y, r: 4.5 });
      occupes.push([x, y]);
    }
    if (!positions) positions = placerPastilles(occupes);   // une fois : les points ne bougent pas avec le filtre

    // --- Étiquettes « zone · nombre » (cliquables) ---
    for (const z of Object.keys(data.compte)) {
      const c = centreZone(z); if (!c) continue;
      const [x, y] = positions[z], on = z === zone;
      const g = el("g", { class: "etiquette" });
      el("rect", { class: "bz" + (on ? " on" : ""), x: x - 60, y: y - 25, width: 120, height: 50, rx: 25 }, null, g);
      el("text", { class: "lz" + (on ? " on-t" : ""), x: x - 44, y: y + 10 }, z, g);
      el("text", { class: "lzc" + (on ? " on-t" : ""), x: x + (z.length > 2 ? 14 : 2), y: y + 9 }, "· " + data.compte[z], g);
      g.onclick = () => choisirZone(z);
    }

    // --- Titre de la liste ---
    const titre = racine.querySelector(".titre");
    titre.innerHTML = zone
      ? `Zone <b>${zone}</b> · ${data.compte[zone]} ${data.unite}${data.compte[zone] > 1 ? "s" : ""}<span class="tout">✕ Toutes les zones</span>`
      : data.titre;
    const tout = titre.querySelector(".tout"); if (tout) tout.onclick = () => choisirZone(zone);

    // --- Liste des fichiers, groupés par zone ---
    const liste = racine.querySelector(".liste");
    liste.classList.toggle("une", !!zone);
    const groupes = data.groupes.filter((g) => !zone || g.zone === zone);
    liste.innerHTML = groupes.length ? "" : `<div class="vide">Aucun fichier dans cette zone.</div>`;
    for (const g of groupes) {
      const bloc = document.createElement("div"); bloc.className = "zone";
      bloc.innerHTML = `<div class="zt"><span class="pz" style="background:${g.couleur}">${g.zone}</span>`
        + `<span class="cpt">${g.entete}</span></div>`;
      bloc.querySelector(".pz").onclick = () => choisirZone(g.zone);
      for (const f of g.lignes) {
        const ligne = document.createElement("div");
        ligne.className = "st" + (f.id === data.choisi ? " choisi" : "");
        ligne.style.setProperty("--c", data.couleur_role);
        ligne.style.setProperty("--fond-choisi", data.fond_choisi);
        ligne.title = f.titre;
        ligne.innerHTML = `<span class="sn"><span class="nm">${f.nom}</span>${f.emplacement ? `<em>${f.emplacement}</em>` : ""}`
          + `${f.en_cours ? "<small>en cours</small>" : ""}</span>`
          + `<span class="barre"><i style="width:${f.largeur}%;background:${f.couleur}"></i></span>`
          + `<span class="dh">${f.dh} <small>°C.h</small></span><span class="n20">${f.n20}</span>`;
        ligne.onclick = () => {                            // fichier choisi : surligné tout de suite, Python prévenu
          racine.querySelectorAll(".st.choisi").forEach((x) => x.classList.remove("choisi"));
          ligne.classList.add("choisi");
          setTriggerValue("fichier", f.id);
        };
        bloc.appendChild(ligne);
      }
      liste.appendChild(bloc);
    }
  }
  dessiner();
}
"""

_COMPOSANT = st.components.v2.component("carte_zones_fichiers", html=HTML, css=CSS, js=JS)


# ============================================================
# DONNÉES D'UNE FAMILLE
# ============================================================

def couleurs_zones(dh_reference: dict) -> dict:
    """Teinte de chaque zone : DH de son fichier de référence, étalé du plus faible (vert) au plus fort (corail)."""
    valeurs = [v for v in dh_reference.values() if v is not None]
    if not valeurs:
        return {}
    bas, haut = min(valeurs), max(valeurs)
    return {z: degrade_dh((v - bas) / ((haut - bas) or 1)) for z, v in dh_reference.items() if v is not None}


def _point(ligne) -> dict:
    """Position d'un fichier : coordonnées si renseignées, sinon département (centre calculé dans la page)."""
    lat, lon = str(ligne.get("latitude") or "").strip(), str(ligne.get("longitude") or "").strip()
    try:
        x, y = projeter(lat.replace(",", "."), lon.replace(",", "."))
    except ValueError:
        x = y = None
    return {"x": x, "y": y, "dep": str(ligne.get("departement") or "").strip(), "zone": ligne["zone"]}


def _texte(v, decimales=0) -> str:
    return "—" if v is None else nombre(v, decimales)


def donnees_famille(lignes: list, resumes: dict, couleurs: dict, choisi: str, en_cours: str, couleur_role: str,
                    unite: str, titre: str) -> dict:
    """
    Données du composant pour une famille.
    lignes : lignes du catalogue (dict) ; resumes : id → {"dh", "nuits_20", "tmax"}.
    Nom d'une ligne : le libellé si la zone a plusieurs fichiers d'une même station (station en en-tête,
    cas RE2020), sinon la station.
    """
    par_zone = {}
    for l in lignes:
        par_zone.setdefault(l["zone"], []).append(l)
    groupes, points, deja = [], [], set()
    for z in [z for z in ZONES if z in par_zone] + [z for z in par_zone if z not in ZONES]:
        ls = par_zone[z]
        stations = {l["station"] for l in ls}
        une_station = len(ls) > 1 and len(stations) == 1
        entete = f"{len(ls)} {unite}{'s' if len(ls) > 1 else ''}" + (f" · station {ls[0]['station']}" if une_station else "")
        rangees = []
        for l in ls:
            r = resumes.get(l["id"]) or {}
            dh = r.get("dh")
            part = (dh or 0) / DH_ECHELLE_CHOIX
            nom, emplacement = l["libelle"] if une_station else l["station"], str(l.get("emplacement") or "")
            if emplacement and nom.endswith(f" ({emplacement})"):          # « Lille-Lesquin (aéroport) » : nom + étiquette
                nom = nom[: -len(emplacement) - 3]
            rangees.append({"id": l["id"], "nom": html.escape(nom), "emplacement": html.escape(emplacement),
                            "titre": f"{l['zone']} · {l['libelle']}", "dh": _texte(dh), "n20": _texte(r.get("nuits_20")),
                            "largeur": round(100 * min(1, part)), "couleur": degrade_dh(part),
                            "en_cours": l["id"] == en_cours})
            position = (l["station"], l.get("departement"), l.get("latitude"), l.get("longitude"))
            if position not in deja:                         # un point par station (pas un par fichier)
                deja.add(position)
                points.append(_point(l))
        groupes.append({"zone": z, "couleur": couleurs.get(z, "#E4E2DD"), "entete": html.escape(entete), "lignes": rangees})
    return {"couleurs": couleurs, "compte": dict(Counter(l["zone"] for l in lignes)), "points": points, "groupes": groupes,
            "decalages": DECALAGE_ETIQUETTES, "ecart": ECART_POINTS, "pastille": PASTILLE, "unite": unite, "titre": html.escape(titre),
            "choisi": choisi, "couleur_role": couleur_role, "fond_choisi": melange(couleur_role, 0.07),
            "degrade": "linear-gradient(90deg," + ",".join(degrade_dh(i / 10) for i in range(11)) + ")",
            "zone": None}


def _valeur(cle: str, nom: str):
    """Valeur « nom » (état ou déclencheur) du composant de clé « cle », lue dans l'état de session."""
    valeur = st.session_state.get(cle)
    if valeur is None:
        return None
    return valeur.get(nom) if hasattr(valeur, "get") else getattr(valeur, nom, None)


def afficher(cle: str, donnees: dict, sur_fichier):
    """
    Monte le composant ; sur_fichier(id) est appelé quand un fichier de la liste est cliqué.
    La zone filtrée est gardée dans l'état du composant (elle survit aux passages suivants).
    """
    def _rappel():
        fichier = _valeur(cle, "fichier")
        if fichier:
            sur_fichier(fichier)
    donnees = dict(donnees, zone=_valeur(cle, "zone"))
    return _COMPOSANT(key=cle, data=donnees, default={"zone": None}, on_fichier_change=_rappel,
                      on_zone_change=lambda: None)
