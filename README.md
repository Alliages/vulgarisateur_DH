# ☀ Météo et Chaleur

Analyser des fichiers météo horaires sous l'angle de l'inconfort d'été (degrés-heures RE2020, nuits tropicales,
journée et semaine les plus chaudes), comparer deux fichiers et créer des journées ou semaines types.

> Les DH sont calculés sur la **température extérieure** : c'est un indicateur de sévérité du climat,
> pas le DH d'un bâtiment.

Version : voir `CHANGELOG.md` (0.8.0, non fonctionnelle).

## Lancer en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Organisation

| Dossier | Contenu |
|---|---|
| `calcul/` | moteur sans interface : séries, hypothèses, DH RE2020, indicateurs, générateur |
| `interface/` | onglets Streamlit, cartes, graphiques Plotly |
| `config/` | réglages, catalogue des fichiers, hypothèses et indicateurs (CSV **générés**) |
| `docs/sources/` | **à modifier** : `documentation.docx` (textes) et `hypotheses.xlsx` (valeurs) |
| `docs/pages/` | pages Markdown générées depuis le Word |
| `donnees/meteo/<zone>/` | fichiers météo enregistrés |
| `outils/` | `convertir_docs.py`, outils Excel ↔ Python |
| `tests/` | tests (`python3 tests/test_dh_re2020.py`, `python3 tests/test_indicateurs.py`) |

## Modifier la documentation

1. Modifier `docs/sources/documentation.docx` (styles Titre 1 / Titre 2) ou `docs/sources/hypotheses.xlsx`.
2. Lancer `python3 outils/convertir_docs.py` (plus tard : automatique via GitHub Action).
3. Dans les textes, `[[hyp:identifiant]]` affiche la valeur à jour d'une hypothèse.

## Sources

Méthode Th-BCE 2020 (annexe III de l'arrêté du 4 août 2021) ; droite adaptative via
[pythermalcomfort](https://pythermalcomfort.readthedocs.io/) ; fichiers météo RE2020 (DHUP / Météo-France).
