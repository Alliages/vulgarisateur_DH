# ☀ Météo et Chaleur

Analyser des fichiers météo horaires sous l'angle de l'inconfort d'été (degrés-heures RE2020, nuits tropicales,
journée et semaine les plus chaudes), comparer deux fichiers et créer des journées ou semaines types.

> Les DH sont calculés sur la **température extérieure** : c'est un indicateur de sévérité du climat,
> pas le DH d'un bâtiment.

Version : voir `CHANGELOG.md` (0.9.2, version de test).

## Lancer en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Sous Windows (Anaconda)

Une version de pyarrow en conflit dans Anaconda fait planter les tableaux interactifs
(`ImportError: DLL load failed while importing lib`). Le plus simple : un environnement dédié, dans le dossier de l'outil.

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Sans cet environnement, l'outil reste utilisable : s'il ne peut pas charger pyarrow, il remplace les tableaux
interactifs par un formulaire simple (onglet Créer) et des tableaux fixes (onglet Méthode).
Pour tester ce mode : variable d'environnement `METEO_SANS_PYARROW=1`.

## Ce que l'outil garde dans le navigateur

Le dernier fichier ouvert, les fichiers récents, les lignes horizontales et l'ordre des cartes sont gardés dans le
navigateur (stockage local, via `streamlit-extras`) d'une visite à l'autre. Rien n'est envoyé ailleurs ; si le
stockage est bloqué (navigation privée), l'outil repart simplement des réglages RE2020.

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
