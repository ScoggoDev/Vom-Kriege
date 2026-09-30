"""Tests de municion limitada (fase 4a, ver docs/informe_fase4a_municion.md)."""
import numpy as np

from engine import Batalla, Config
from generals import avanzar_y_disparar, quieto


def test_flag_apagado_no_cambia_nada():
    b1 = Batalla(Config(), B=5, seed=6).correr(avanzar_y_disparar(), avanzar_y_disparar())
    b2 = Batalla(Config(municion_activa=False, municion_inicial=1), B=5, seed=6).correr(
        avanzar_y_disparar(), avanzar_y_disparar())
    assert np.array_equal(b1.salud, b2.salud)
    assert np.array_equal(b1.ganador, b2.ganador)
    assert b1.municion is None


def test_se_queda_sin_municion_y_deja_de_disparar():
    cfg = Config(n_soldados=(1, 1), unidades=1, distancia_inicial_m=20, alcance_max_m=200,
                 municion_activa=True, municion_inicial=3)
    b = Batalla(cfg, B=1, seed=0)
    ordenes = np.zeros((1, 2, 1), int)  # SOSTENER
    for _ in range(60):  # de sobra para agotar 3 balas aun con demoras de recarga
        b.paso(ordenes)
    assert int(b.municion[0, 0, 0]) == 0  # nunca queda en negativo, se detiene justo en 0


def test_sin_municion_nunca_hace_dano():
    cfg = Config(n_soldados=(1, 1), unidades=1, distancia_inicial_m=20, alcance_max_m=200,
                 p_max=1.0, d50_m=1e9, punteria_sd=0.0, recarga_ticks=0,
                 municion_activa=True, municion_inicial=0)
    b = Batalla(cfg, B=1, seed=0)
    ordenes = np.zeros((1, 2, 1), int)
    for _ in range(5):
        b.paso(ordenes)
    assert b.salud.min() == 2  # con 0 balas, nadie dispara pese a condiciones de impacto garantizado


def test_municion_limitada_reduce_bajas_totales():
    """Con menos balas disponibles, deberia haber menos impactos en total que sin limite,
    en igualdad de condiciones (misma semilla, mismo resto de parametros)."""
    base = dict(n_soldados=(60, 60), distancia_inicial_m=250)
    b_limitado = Batalla(Config(**base, municion_activa=True, municion_inicial=5), B=50, seed=1).correr(
        avanzar_y_disparar(), avanzar_y_disparar())
    b_libre = Batalla(Config(**base), B=50, seed=1).correr(avanzar_y_disparar(), avanzar_y_disparar())
    bajas_limitado = (b_limitado.salud < 2).sum()
    bajas_libre = (b_libre.salud < 2).sum()
    assert bajas_limitado <= bajas_libre
