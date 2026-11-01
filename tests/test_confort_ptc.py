"""
pythermalcomfort comme RÉFÉRENCE des tests (décision du 24/10/2026) : la droite de confort adaptatif écrite dans
l'outil doit être celle de la librairie. Depuis la 0.9.8, l'outil n'a plus besoin de la librairie pour tourner ;
ce test ne s'exécute que si elle est installée (pip install -r requirements-dev.txt).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest

from calcul.confort_ptc import ORDONNEE_EN16798, PENTE_EN16798

try:
    from pythermalcomfort.models import adaptive_en
except ImportError:                       # librairie absente (ou dossier vide laissé par une désinstallation)
    pytest.skip("pythermalcomfort absent : pip install -r requirements-dev.txt", allow_module_level=True)


def test_droite_de_confort_identique_a_pythermalcomfort():
    theta_rm = np.linspace(5, 35, 61)
    res = adaptive_en(tdb=25.0, tr=25.0, t_running_mean=theta_rm, v=0.1, limit_inputs=False, round_output=False)
    reference = np.asarray(res.tmp_cmf_cat_i_up, dtype=float)                 # catégorie I : Δ = 2 °C
    assert np.allclose(PENTE_EN16798 * theta_rm + ORDONNEE_EN16798 + 2.0, reference, atol=1e-9)
