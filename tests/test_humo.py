"""Tests de humo (fase 4c, ver docs/informe_fase4c_humo.md)."""
import numpy as np
import pytest

from engine import Batalla, Config
from generals import avanzar_y_disparar, quieto


def test_flag_apagado_no_cambia_nada():
    extremos = dict(humo_activo=False, humo_por_disparo=10.0, humo_penal_punteria=10.0, humo_disipacion=0.0)
    b1 = Batalla(Config(), B=5, seed=9).correr(avanzar_y_disparar(), avanzar_y_disparar())
    b2 = Batalla(Config(**extremos), B=5, seed=9).correr(avanzar_y_disparar(), avanzar_y_disparar())
    assert np.array_equal(b1.salud, b2.salud)
    assert np.array_equal(b1.ganador, b2.ganador)
    assert (b1.humo_unidad == 0).all()


def test_disparar_genera_humo():
    cfg = Config(n_soldados=(20, 20), unidades=1, distancia_inicial_m=20, alcance_max_m=200,
                 humo_activo=True)
    b = Batalla(cfg, B=1, seed=0)
    ordenes = np.zeros((1, 2, 1), int)
    assert b.humo_unidad[0, 0, 0] == 0
    b.paso(ordenes)
    assert b.humo_unidad[0, 0, 0] > 0


def test_humo_se_disipa_sin_disparos():
    cfg = Config(n_soldados=(5, 5), unidades=1, p_max=0.0, humo_activo=True, humo_disipacion=0.2)
    b = Batalla(cfg, B=1, seed=0)
    b.humo_unidad[:] = 1.0
    ordenes = np.zeros((1, 2, 1), int)
    b.paso(ordenes)  # p_max=0 => nadie dispara => no se genera humo nuevo, solo se disipa
    assert float(b.humo_unidad[0, 0, 0]) == pytest.approx(0.8)


def test_humo_reduce_impactos():
    """Mismo seed: la unica diferencia es el humo acumulado previo. Tiene que
    haber menos o igual impactos con humo que sin el."""
    cfg = Config(n_soldados=(50, 50), unidades=1, distancia_inicial_m=50, alcance_max_m=200,
                 p_max=0.9, d50_m=1e9, punteria_sd=0.0, humo_activo=True, humo_penal_punteria=2.0)
    ordenes = np.zeros((1, 2, 1), int)

    b_limpio = Batalla(cfg, B=1, seed=0)
    b_humo = Batalla(cfg, B=1, seed=0)
    b_humo.humo_unidad[:] = 1.0

    for _ in range(3):
        b_limpio.paso(ordenes)
        b_humo.paso(ordenes)
    heridos_limpio = (b_limpio.salud[0, 1] < 2).sum()
    heridos_humo = (b_humo.salud[0, 1] < 2).sum()
    assert heridos_humo <= heridos_limpio
