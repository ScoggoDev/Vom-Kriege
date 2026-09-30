"""
Verificacion de Lanchester: es un test de bugs del motor, no un objetivo cientifico.
Con fuego apuntado y parametros simples tiene que emerger la ley cuadrada; con fuego
al bulto, la formula del modo area (ver docs/diseno.md, seccion 2, para la derivacion).
Mismos parametros que experimentos/lanchester.py, pero con assert en vez de print.
"""
import numpy as np
import pytest

from engine import Batalla, Config
from generals import quieto

A0 = 100
B0S = (50, 60, 70, 80, 90)
TOLERANCIA_SOBREVIVIENTES = 5  # margen absoluto, ver corrida de referencia en CLAUDE.md


def _cfg(B0, modo):
    return Config(
        n_soldados=(A0, B0), unidades=1, distancia_inicial_m=60, p_max=0.1, d50_m=1e9,
        p_herida_grave=1.0, punteria_sd=0.0, modo_fuego=modo, max_ticks=4000,
    )


@pytest.mark.parametrize("B0", B0S)
def test_ley_cuadrada_fuego_apuntado(B0):
    cfg = _cfg(B0, "apuntado")
    b = Batalla(cfg, B=150, seed=B0).correr(quieto, quieto)
    gana = b.ganador == 0
    assert gana.mean() > 0.9
    sim = b.sobrevivientes()[gana, 0].mean()
    esperado = np.sqrt(A0 ** 2 - B0 ** 2)
    assert abs(sim - esperado) < TOLERANCIA_SOBREVIVIENTES


@pytest.mark.parametrize("B0", B0S)
def test_formula_area_con_huecos(B0):
    cfg = _cfg(B0, "area")
    b = Batalla(cfg, B=150, seed=B0).correr(quieto, quieto)
    gana = b.ganador == 0
    assert gana.mean() > 0.8
    sim = b.sobrevivientes()[gana, 0].mean()
    esperado = A0 - B0 ** 2 / A0
    assert abs(sim - esperado) < TOLERANCIA_SOBREVIVIENTES
