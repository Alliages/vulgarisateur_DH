# 🌡️ Calculateur DH RE2020

Outil de calcul des **Degrés-Heures (DH) d'inconfort thermique estival** selon la réglementation thermique française **RE2020**.

Basé sur l'outil Excel *Vulgarisation_DH.xlsx*.

---

## 📋 Présentation

Le DH (Degré-Heure) est un indicateur de l'inconfort thermique estival :

```
DH(h) = max( T(h) − Seuil(h) , 0 )
```

| Période | Seuil |
|---------|-------|
| 0h–5h et 23h (nuit) | **26°C** |
| 6h–22h (journée) | **28°C** |

**Planning d'occupation résidentielle :**
- ✅ Occupé : 0h–9h et 17h–23h
- ❌ Non-occupé : 10h–16h (travail / école)

---

## 🗂️ Structure du projet

```
calculateur_dh_re2020/
├── app.py                  ← Point d'entrée (application Dash)
├── modules/
│   ├── variables.py        ← Constantes et paramètres RE2020
│   ├── calculs.py          ← Formules : courbes de température + DH
│   ├── interface.py        ← Layout de l'interface web (Dash)
│   └── graphiques.py       ← Graphiques interactifs (Plotly)
├── requirements.txt
├── Procfile                ← Pour déploiement Render / Heroku
└── README.md
```

---

## 🚀 Lancement local

### 1. Cloner le dépôt

```bash
git clone https://github.com/<votre-compte>/calculateur_dh_re2020.git
cd calculateur_dh_re2020
```

### 2. Créer un environnement virtuel (recommandé)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Lancer l'application

```bash
python app.py
```

Ouvrir dans un navigateur : [http://127.0.0.1:8050](http://127.0.0.1:8050)

---

## ☁️ Déploiement gratuit sur Render (depuis GitHub)

1. Pousser le code sur GitHub
2. Aller sur [render.com](https://render.com) → **New Web Service**
3. Connecter votre dépôt GitHub
4. Paramètres :
   - **Build command** : `pip install -r requirements.txt`
   - **Start command** : `gunicorn app:server`
   - **Environment** : Python 3
5. Cliquer **Deploy** → L'URL publique est générée automatiquement

---

## 📐 Formules implémentées

### Courbe linéaire (Brut)

| Phase | Formule |
|-------|---------|
| 0h → 5h (descente) | `T₀ + (T_min − T₀) × h / 5` |
| 5h → H_pic (montée) | `T_min + (T_max − T_min) × (h−5) / (H_pic−5)` |
| H_pic → 24h (descente) | `T_max + (T₀ − T_max) × (h−H_pic) / (24−H_pic)` |

### Courbe lissée (Sinusoïdale)

| Phase | Formule |
|-------|---------|
| 0h → 5h | `T₀ + (T_min − T₀) × sin(π/2 × h/5)` |
| 5h → H_pic | `T_min + (T_max − T_min) × sin(π/2 × (h−5)/(H_pic−5))` |
| H_pic → 24h | `T₀ + (T_max − T₀) × cos(π/2 × (h−H_pic)/(24−H_pic))` |

### Courbe aléatoire

```
T_rand(h) = (T_lin(h) + T_smooth(h)) / 2 + bruit
```
avec `|bruit| ≤ (T_max − T_min) × 8%`

---

## ⚠️ Notes et doutes de transcription

| # | Sujet | Détail |
|---|-------|--------|
| 1 | **Option "13h"** | Dans l'Excel, le pic "13h" correspond à `H_pic = 12` dans les formules (valeur max à h=12). Nommé "13h" selon la convention de l'outil d'origine. |
| 2 | **Bug "15h smooth" semaine** | Pour certains jours de la semaine, la colonne "15h smooth" de l'Excel présente des valeurs inférieures à T_min sur les heures 1h–4h. Semble être un bug Excel (formule incorrecte). Ignoré dans cette implémentation. |
| 3 | **Planning d'occupation** | Déduit des données Excel (cellules NaN pour h=10–16). À confirmer avec le texte réglementaire RE2020. |
| 4 | **Cohérence DH jour/nuit** | L'onglet "journée" de l'Excel affiche DH_jour et DH_nuit sans filtre d'occupation. L'onglet "semaine" les affiche avec filtre. Cette implémentation est cohérente (sans filtre pour les deux). |
| 5 | **Courbe aléatoire** | L'Excel utilise `RAND()` Excel, recalculé à chaque ouverture. L'amplitude des perturbations n'est pas documentée (estimée à ±8%). |

---

## 📊 Métriques DH affichées

| Métrique | Description |
|----------|-------------|
| **DH en occupation** | DH uniquement sur les heures occupées → **Indicateur RE2020** |
| **DH total 24h** | DH sur toutes les heures, sans filtre (hypothétique) |
| **DH jour** | DH sur la période 6h–21h |
| **DH nuit** | DH sur la période 0h–5h + 22h–23h |

---

## 🔧 Dépendances

| Package | Version | Rôle |
|---------|---------|------|
| `dash` | 2.17.1 | Framework web Python |
| `dash-bootstrap-components` | 1.6.0 | Composants UI Bootstrap |
| `plotly` | 5.22.0 | Graphiques interactifs |
| `numpy` | 1.26.4 | Calculs numériques |
| `gunicorn` | 22.0.0 | Serveur WSGI (déploiement) |
