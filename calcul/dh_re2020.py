"""
============================================================
 DH_RE2020 — CALCUL DES DEGRÉS-HEURES D'INCONFORT ESTIVAL
============================================================
 Module autonome (dépendance unique : numpy) qui calcule les
 Degrés-Heures (DH, en °C.h) à partir d'une série horaire
 annuelle de températures (8760 valeurs, ou 8784 en bissextile),
 selon la méthode Th-BCE 2020 (annexe III de l'arrêté du
 4 août 2021).

 Usage minimal :
     from dh_re2020 import calculer_dh
     dh = calculer_dh(t_op)                         # seuils fixes 26/28 °C
     dh = calculer_dh(t_op, t_exterieure=t_ext)     # méthode RE2020
     res = calculer_dh(t_op, t_ext, occupation="logement_re2020",
                       details=True)

------------------------------------------------------------
 MÉTHODE (références = numéros de formule de l'annexe III)
------------------------------------------------------------
 1. Moyenne glissante extérieure — fiche C_Clim, formule (1)
        θei,moy(j) = moyenne des 24 températures extérieures du jour j−1
        θrm(j)     = 0,8 × θrm(j−1) + 0,2 × θei,moy(j)
    θrm est calculée au 1er pas de temps du jour et reprise pour
    tout le jour. Initialisation : θrm = 0 le premier jour (lecture
    du texte, qui écrit « Si IHJ = 1, θrm(j) = 0 »).

 2. Période de confort adaptatif — fiche C_Clim, formule (2)
    Isconf_adapt = 1 du PREMIER au DERNIER jour de l'année où
    θrm(j) ≥ 16 °C (période continue), 0 sinon. Hors de cette
    période, aucun DH n'est compté.

 3. Seuil d'inconfort chaud — fiche C_BAT_Confort d'été (13.5)
    (2543)  θop_inc_max(j) = MAX(θiifr+ ; 0,33 × θrm(j) + 18,8 + Δθop_inc_C)
            Δθop_inc = 2 / 3 / 4 °C en catégorie 1 / 2 / 3 ;
            Cat_amb = 1 pour TOUS les usages (tableau 340) → +2 °C.
    (2544)  Habitation :
              si 6 < hleg ≤ 22 : θconf = MIN(θiifr+ + Δθop_min_max ; θop_inc_max)
              sinon (sommeil)  : θconf = θiifr+
    (2545)  Autres usages : θconf = MIN(θiifr+ + Δθop_min_max ; θop_inc_max)
            à toute heure.
    Avec θiifr+ = consigne de refroidissement en occupation (26 °C)
    et Δθop_min_max = 2 °C → seuil compris entre 26 et 28 °C.
    Ici : seuil_bas = θiifr+, seuil_haut = θiifr+ + Δθop_min_max.
    Remarque : 0,33 × θrm + 20,8 = 26 °C pour θrm ≈ 15,8 °C, d'où
    le critère θrm ≥ 16 °C de la période de confort adaptatif.

 4. Systèmes d'amélioration du confort (brasseurs d'air…)
    (2547)  θconf_corr(h) = θconf(h) + Δθcorr_syst(h)
    Pour un brasseur d'air, voir delta_top_brasseur() — formule (1659).

 5. Température opérative — fiche comportement thermique, (371) et (314)
        θop = ptop × θradiante + (1 − ptop) × θair,  ptop = 0,5
    Si `t_rayonnante` est fourni, `temperatures` est lu comme la
    température d'AIR et converti ; sinon il est supposé opératif.

 6. Indicateur — formule (2551)
        DH = Σ max(0 ; θop(h) − θconf_corr(h))
             sur les heures telles que Iocc(h) = 1 et Isconf_adapt(h) = 1
    + indicateurs pédagogiques (2548–2550) : nombre d'heures où
      θop ≥ θconf_corr, ≥ θconf_corr + 1, ≥ θconf_corr + 2.

------------------------------------------------------------
 OCCUPATION CONVENTIONNELLE DU LOGEMENT
------------------------------------------------------------
 Fiche C_EIN_Scénarios conventionnels (annexe III, 4.1, tableau de
 synthèse) et classeur « scénarios conventionnels » du 29/04/2026,
 usages 1 (maisons individuelles) et 2 (logements collectifs) :
   - lundi, mardi, jeudi, vendredi : occupé de 0h à 9h et de 17h à 0h
     (absents de 9h à 17h) ;
   - mercredi : occupé de 0h à 9h et de 13h à 0h (absents de 9h à 13h) ;
   - samedi, dimanche : occupé 24h/24 ;
   - inoccupé la 4e semaine de décembre, soit la semaine 52 de l'année
     conventionnelle (52 semaines : 4-4-5-4-5-4-4-5-4-4-5-4 par mois),
     jours 358 à 364. Le jour 365, hors des 52 semaines, reste occupé
     (cas non décrit par le texte).
 Heures légales, année débutant un lundi (convention Th-BCE).

------------------------------------------------------------
 CONVENTION HORAIRE
------------------------------------------------------------
 L'indice h d'une série désigne l'heure [h:00 ; h+1:00[.
 La méthode raisonne en heure légale de FIN de pas de temps
 (hleg ∈ 1..24) : « 6 < hleg ≤ 22 » = intervalle légal [6h ; 22h[.
 Les fichiers météo RE2020 sont en UTC ; heure légale = UTC + 1
 en hiver, UTC + 2 en été. Si la série est en UTC, passer
 decalage_heure=2 pour un calcul estival (ou un tableau 8760).

------------------------------------------------------------
 HORS TEXTE CONSULTÉ (hypothèses)
------------------------------------------------------------
 - θiifr+ = 26 °C (valeur citée dans l'annexe pour les graphiques
   de confort adaptatif ; consigne de refroidissement en occupation).
============================================================
"""

import numpy as np

try:                                   # droite adaptative via pythermalcomfort (confort_ptc.py)
    from calcul.confort_ptc import limite_haute_confort
except ImportError:                    # utilisation autonome du module
    limite_haute_confort = None

# ============================================================
# CONSTANTES ET VALEURS PAR DÉFAUT
# ============================================================

# --- Dimensions temporelles ---------------------------------
HEURES_PAR_JOUR = 24
NB_HEURES_ANNEE = (8760, 8784)        # année normale / bissextile

# --- Seuils de température (°C) — formules (2543)-(2545) ----
CONSIGNE_REFROIDISSEMENT = 26.0       # θiifr+ : seuil nuit, plancher du seuil
ECART_MIN_MAX = 2.0                   # Δθop_min_max : adaptation maximale
SEUIL_BAS_DEFAUT = CONSIGNE_REFROIDISSEMENT
SEUIL_HAUT_DEFAUT = CONSIGNE_REFROIDISSEMENT + ECART_MIN_MAX   # 28 °C

# --- Confort adaptatif (NF EN 16798-1 reprise par Th-BCE) ---
PENTE_CONFORT = 0.33                  # pente de la droite de confort
ORDONNEE_CONFORT = 18.8               # ordonnée à l'origine
DELTA_CATEGORIE = {1: 2.0, 2: 3.0, 3: 4.0}  # Δθop_inc par catégorie d'ambiance
CATEGORIE_AMBIANCE_DEFAUT = 1         # Cat_amb = 1 pour tous les usages (tab. 340)

# --- Moyenne glissante extérieure — formule (1) -------------
ALPHA_GLISSANTE = 0.8                 # θrm(j) = 0,8·θrm(j−1) + 0,2·θmoy(j−1)
THETA_RM_INITIALE = 0.0               # θrm du premier jour
SEUIL_THETA_RM_PERIODE = 16.0         # période de confort adaptatif : θrm ≥ 16 °C
JOURS_RODAGE_CYCLIQUE = 30            # option d'initialisation « cyclique »

# --- Période jour (habitation) — formule (2544) -------------
# Condition « 6 < hleg ≤ 22 » en heure de fin de pas → [6h ; 22h[
HEURE_DEBUT_JOUR = 6
HEURE_FIN_JOUR = 22

# --- Température opérative — formules (371) et (314) --------
P_TOP = 0.5                           # poids de la température radiante

# --- Brasseurs d'air — formule (1659) -----------------------
VITESSE_AIR_MIN_BRASSEUR = 0.2        # m/s : en dessous, aucun effet

# --- Occupation conventionnelle logement — annexe III, 4.1 ----
# Jours : 0 = lundi … 6 = dimanche. Heures légales inoccupées, fin exclue.
ABSENCES_LOGEMENT_RE2020 = {
    0: (9, 17),    # lundi
    1: (9, 17),    # mardi
    2: (9, 13),    # mercredi
    3: (9, 17),    # jeudi
    4: (9, 17),    # vendredi
}                  # samedi, dimanche : occupé 24h/24
# Semaine inoccupée : 4e semaine de décembre = semaine 52 de l'année
# conventionnelle. Jours de l'année comptés à partir de 1, bornes incluses.
JOUR_DEBUT_INOCCUPATION = 358
JOUR_FIN_INOCCUPATION = 364
PREMIER_JOUR_SEMAINE_RE2020 = 0       # l'année Th-BCE commence un lundi

# --- Choix autorisés ----------------------------------------
PERIODES_VALIDES = ("total", "jour", "nuit")
USAGES_VALIDES = ("habitation", "autre")
INITIALISATIONS_VALIDES = ("re2020", "cyclique")


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def _verifier_serie(nom: str, serie, n_attendu: int = None) -> np.ndarray:
    """Convertit en tableau float et vérifie la longueur (8760 / 8784)."""
    arr = np.asarray(serie, dtype=float).ravel()
    if n_attendu is None and arr.size not in NB_HEURES_ANNEE:
        raise ValueError(f"{nom} : {arr.size} valeurs, 8760 ou 8784 attendues.")
    if n_attendu is not None and arr.size != n_attendu:
        raise ValueError(f"{nom} : {arr.size} valeurs, {n_attendu} attendues.")
    if np.isnan(arr).any():
        raise ValueError(f"{nom} : contient des valeurs manquantes (NaN).")
    return arr


def temperature_operative(t_air, t_rayonnante, p_top: float = P_TOP) -> np.ndarray:
    """
    Température opérative Th-BCE, formule (371) :
        θop = ptop × θradiante + (1 − ptop) × θair,  ptop = 0,5 (314)
    """
    return p_top * np.asarray(t_rayonnante, float) + (1 - p_top) * np.asarray(t_air, float)


def delta_top_brasseur(vitesse_air, t_rayonnante, t_air) -> np.ndarray:
    """
    Gain de confort d'un brasseur d'air (°C), formule (1659) :
        v ≤ 0,2 m/s : 0
        sinon       : 1,8322·e^(0,0361·(θrad − θair))·ln(v)
                      + 3,0498·e^(0,0368·(θrad − θair))
    θrad et θair sont pris au pas de temps précédent dans la méthode.
    Valeur à passer (éventuellement pondérée par la surface desservie)
    dans le paramètre `delta_corr_syst` de calculer_dh.
    Exemple : v = 0,6 m/s, θrad = θair → ≈ 2,1 °C.
    """
    v = np.asarray(vitesse_air, float)
    ecart = np.asarray(t_rayonnante, float) - np.asarray(t_air, float)
    v_sure = np.maximum(v, VITESSE_AIR_MIN_BRASSEUR)   # évite ln(0)
    gain = (1.8322 * np.exp(0.0361 * ecart) * np.log(v_sure)
            + 3.0498 * np.exp(0.0368 * ecart))
    return np.where(v > VITESSE_AIR_MIN_BRASSEUR, gain, 0.0)


def moyenne_glissante_exterieure(
    t_exterieure, alpha: float = ALPHA_GLISSANTE, initialisation: str = "re2020"
) -> np.ndarray:
    """
    θrm par jour, formule (1) :
        θrm(j) = α·θrm(j−1) + (1 − α)·θmoy_ext(j−1)
    initialisation :
        "re2020"   → θrm = 0 le premier jour (texte Th-BCE)
        "cyclique" → rodage sur les derniers jours de l'année
                     (année météo considérée comme bouclée)
    """
    if initialisation not in INITIALISATIONS_VALIDES:
        raise ValueError(f"initialisation doit valoir {INITIALISATIONS_VALIDES}")

    t_moy_jour = np.asarray(t_exterieure, float).reshape(-1, HEURES_PAR_JOUR).mean(axis=1)
    nb_jours = t_moy_jour.size

    # Valeur du premier jour
    if initialisation == "re2020":
        theta = THETA_RM_INITIALE
    else:
        rodage = t_moy_jour[-JOURS_RODAGE_CYCLIQUE:]
        theta = rodage.mean()
        for t_veille in rodage:                 # le dernier traité = 31/12
            theta = alpha * theta + (1 - alpha) * t_veille

    # Récurrence : θrm(j) dépend de la moyenne de la veille
    theta_rm = np.empty(nb_jours)
    theta_rm[0] = theta
    for j in range(1, nb_jours):
        theta_rm[j] = alpha * theta_rm[j - 1] + (1 - alpha) * t_moy_jour[j - 1]
    return theta_rm


def periode_confort_adaptatif(theta_rm, seuil: float = SEUIL_THETA_RM_PERIODE) -> np.ndarray:
    """
    Masque journalier Isconf_adapt, formule (2) : vrai du premier au
    dernier jour où θrm ≥ 16 °C (période continue).
    """
    jours_chauds = np.flatnonzero(np.asarray(theta_rm) >= seuil)
    masque = np.zeros(len(theta_rm), dtype=bool)
    if jours_chauds.size:
        masque[jours_chauds[0]:jours_chauds[-1] + 1] = True
    return masque


def masque_occupation_logement_re2020(
    nb_heures: int, premier_jour_semaine: int = PREMIER_JOUR_SEMAINE_RE2020,
    decalage_heure=0,
) -> np.ndarray:
    """
    Masque booléen d'occupation conventionnelle logement (True = occupé).
    Les scénarios Th-BCE sont décrits en heure légale : decalage_heure
    convertit l'indice de la série (ex. UTC) en heure légale.
    """
    heures = np.arange(nb_heures) + np.asarray(decalage_heure)
    heure_du_jour = heures % HEURES_PAR_JOUR
    jour_semaine = (heures // HEURES_PAR_JOUR + premier_jour_semaine) % 7

    jour_annee = heures // HEURES_PAR_JOUR + 1      # 1 = 1er janvier

    occupe = np.ones(nb_heures, dtype=bool)
    # Absences de la journée, du lundi au vendredi
    for jour, (debut, fin) in ABSENCES_LOGEMENT_RE2020.items():
        absent = (jour_semaine == jour) & (heure_du_jour >= debut) & (heure_du_jour < fin)
        occupe[absent] = False
    # Semaine inoccupée de décembre
    occupe[semaine_inoccupee(jour_annee)] = False
    return occupe


def semaine_inoccupee(jour_annee) -> np.ndarray:
    """True pendant la semaine inoccupée de décembre (jour de l'année, 1 = 1er janvier)."""
    jour_annee = np.asarray(jour_annee)
    return (jour_annee >= JOUR_DEBUT_INOCCUPATION) & (jour_annee <= JOUR_FIN_INOCCUPATION)


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def calculer_dh(
    temperatures,
    t_exterieure=None,
    *,
    seuil_bas: float = SEUIL_BAS_DEFAUT,
    seuil_haut: float = SEUIL_HAUT_DEFAUT,
    periode: str = "total",
    usage: str = "habitation",
    occupation=None,
    premier_jour_semaine: int = PREMIER_JOUR_SEMAINE_RE2020,
    decalage_heure=0,
    heure_debut_jour: int = HEURE_DEBUT_JOUR,
    heure_fin_jour: int = HEURE_FIN_JOUR,
    categorie_ambiance: int = CATEGORIE_AMBIANCE_DEFAUT,
    appliquer_periode_adaptative: bool = True,
    initialisation_theta_rm: str = "re2020",
    masque_calcul=None,
    t_rayonnante=None,
    delta_corr_syst=0.0,
    details: bool = False,
):
    """
    Calcule les Degrés-Heures d'inconfort (°C.h) sur une année horaire.

    Paramètres
    ----------
    temperatures : 8760 (ou 8784) valeurs horaires intérieures, °C.
        Température opérative, ou température d'air si `t_rayonnante` est donné.
    t_exterieure : 8760 valeurs extérieures, °C.
        Fournie → méthode RE2020 (seuil adaptatif + période de confort adaptatif).
        Absente → seuils fixes : seuil_bas la nuit, seuil_haut le jour.
    seuil_bas : θiifr+, consigne de refroidissement = seuil de nuit (26 °C).
    seuil_haut : θiifr+ + Δθop_min_max, plafond du seuil de jour (28 °C).
    periode : "total", "jour" ou "nuit" — heures cumulées dans le résultat `dh`.
    usage : "habitation" (seuil fixe la nuit) ou "autre" (adaptatif à toute heure).
    occupation : None (toutes heures occupées), "logement_re2020",
        ou tableau booléen de même longueur (True = occupé).
    premier_jour_semaine : jour du 1er janvier, 0 = lundi.
    decalage_heure : heures à ajouter pour passer de la base de temps de la
        série à l'heure légale (0 si déjà en heure légale ; 2 pour de l'UTC
        en été). Entier ou tableau de même longueur.
    heure_debut_jour, heure_fin_jour : jour = [début ; fin[ en heure légale.
    categorie_ambiance : 1, 2 ou 3 (Δθop_inc = 2, 3, 4 °C). RE2020 : 1.
    appliquer_periode_adaptative : compter uniquement la période où θrm ≥ 16 °C.
    initialisation_theta_rm : "re2020" (θrm = 0 au 1er jour) ou "cyclique".
    masque_calcul : tableau booléen optionnel d'heures à retenir en plus.
    t_rayonnante : température radiante moyenne, °C (active θop = 0,5·(θair + θrad)).
    delta_corr_syst : relèvement du seuil en °C (brasseurs d'air…),
        scalaire ou tableau de même longueur. Voir delta_top_brasseur().
    details : False → retourne le DH (float) ; True → dictionnaire complet.

    Retour
    ------
    float, ou dict avec : dh, dh_total, dh_jour, dh_nuit, nb_h_inconfort,
    nb_h_inconfort_1C, nb_h_inconfort_2C, dh_horaire, seuil_horaire,
    t_operative, heures_retenues, theta_rm, periode_adaptative.
    """
    # ---------- Vérification des paramètres ----------
    t_int = _verifier_serie("temperatures", temperatures)
    nb_heures = t_int.size
    nb_jours = nb_heures // HEURES_PAR_JOUR

    if periode not in PERIODES_VALIDES:
        raise ValueError(f"periode doit valoir {PERIODES_VALIDES}")
    if usage not in USAGES_VALIDES:
        raise ValueError(f"usage doit valoir {USAGES_VALIDES}")
    if categorie_ambiance not in DELTA_CATEGORIE:
        raise ValueError("categorie_ambiance doit valoir 1, 2 ou 3")
    if seuil_bas > seuil_haut:
        raise ValueError("seuil_bas doit être ≤ seuil_haut.")
    mode_adaptatif = t_exterieure is not None

    # ---------- 1. Température opérative (371) ----------
    if t_rayonnante is not None:
        t_ray = _verifier_serie("t_rayonnante", t_rayonnante, nb_heures)
        t_op = temperature_operative(t_int, t_ray)
    else:
        t_op = t_int

    # ---------- 2. Jour / nuit en heure légale (2544) ----------
    heure_legale = (np.arange(nb_heures) + np.asarray(decalage_heure)) % HEURES_PAR_JOUR
    est_jour = (heure_legale >= heure_debut_jour) & (heure_legale < heure_fin_jour)
    est_nuit = ~est_jour

    # ---------- 3. Seuil horaire (2543)-(2545) ----------
    theta_rm = None
    adapt_jour = np.ones(nb_jours, dtype=bool)
    if not mode_adaptatif:
        # Seuils fixes (logique du vulgarisateur Excel)
        seuil_adapte = np.full(nb_heures, seuil_haut)
    else:
        t_ext = _verifier_serie("t_exterieure", t_exterieure, nb_heures)
        theta_rm = moyenne_glissante_exterieure(t_ext, initialisation=initialisation_theta_rm)

        # (2543) seuil d'inconfort maximal, puis plafonnement à seuil_haut
        delta = DELTA_CATEGORIE[categorie_ambiance]
        if limite_haute_confort is not None:
            droite = limite_haute_confort(theta_rm, delta)          # pythermalcomfort
        else:
            droite = PENTE_CONFORT * theta_rm + ORDONNEE_CONFORT + delta
        theta_inc_max = np.maximum(seuil_bas, droite)
        seuil_adapte = np.repeat(np.minimum(seuil_haut, theta_inc_max), HEURES_PAR_JOUR)

        # (2) période de confort adaptatif
        if appliquer_periode_adaptative:
            adapt_jour = periode_confort_adaptatif(theta_rm)

    if usage == "habitation":
        seuil = np.where(est_jour, seuil_adapte, seuil_bas)   # nuit : θiifr+
    else:
        seuil = seuil_adapte if mode_adaptatif else np.where(est_jour, seuil_haut, seuil_bas)

    # (2547) systèmes d'amélioration du confort
    seuil = seuil + np.asarray(delta_corr_syst, dtype=float)

    # ---------- 4. Heures retenues : Iocc ∩ Isconf_adapt ∩ masque ----------
    if occupation is None:
        occupe = np.ones(nb_heures, dtype=bool)
    elif isinstance(occupation, str):
        if occupation != "logement_re2020":
            raise ValueError("occupation : None, 'logement_re2020' ou tableau booléen.")
        occupe = masque_occupation_logement_re2020(nb_heures, premier_jour_semaine, decalage_heure)
    else:
        occupe = np.asarray(occupation, dtype=bool).ravel()
        if occupe.size != nb_heures:
            raise ValueError("occupation : longueur différente de temperatures.")

    retenue = occupe & np.repeat(adapt_jour, HEURES_PAR_JOUR)
    if masque_calcul is not None:
        masque = np.asarray(masque_calcul, dtype=bool).ravel()
        if masque.size != nb_heures:
            raise ValueError("masque_calcul : longueur différente de temperatures.")
        retenue &= masque

    # ---------- 5. DH (2551) et indicateurs pédagogiques (2548-2550) ----------
    ecart = t_op - seuil
    dh_horaire = np.maximum(ecart, 0.0) * retenue
    dh_jour = float(dh_horaire[est_jour].sum())
    dh_nuit = float(dh_horaire[est_nuit].sum())
    dh_total = dh_jour + dh_nuit
    dh = {"total": dh_total, "jour": dh_jour, "nuit": dh_nuit}[periode]

    if not details:
        return dh

    return {
        "dh": dh,                                          # selon `periode`
        "dh_total": dh_total,
        "dh_jour": dh_jour,
        "dh_nuit": dh_nuit,
        "nb_h_inconfort": int(((ecart >= 0) & retenue).sum()),      # (2548)
        "nb_h_inconfort_1C": int(((ecart >= 1) & retenue).sum()),   # (2549)
        "nb_h_inconfort_2C": int(((ecart >= 2) & retenue).sum()),   # (2550)
        "dh_horaire": dh_horaire,                          # 8760 valeurs
        "seuil_horaire": seuil,                            # 8760 valeurs
        "t_operative": t_op,                               # 8760 valeurs
        "heures_retenues": retenue,                        # masque booléen
        "theta_rm": theta_rm,                              # θrm par jour
        "periode_adaptative": adapt_jour,                  # Isconf_adapt par jour
    }
