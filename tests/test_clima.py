"""
Tests de clima: lluvia (fallo de encendido, barro) y nieve (fase 3,
ver docs/informe_fase3_clima.md).
"""
import numpy as np

from engine import Batalla, Config
from generals import avanzar_y_disparar


def test_clima_seco_no_cambia_nada():
    """clima='seco' es el default neutro: incluso con los demas parametros de
    clima en valores extremos, el resultado tiene que ser bit a bit igual."""
    extremos = dict(clima="seco", clima_lluvia_p_fallo=1.0, clima_lluvia_factor_marcha=0.01,
                     clima_nieve_factor_marcha=0.01, clima_nieve_factor_alcance=0.01)
    b1 = Batalla(Config(), B=5, seed=5).correr(avanzar_y_disparar(), avanzar_y_disparar())
    b2 = Batalla(Config(**extremos), B=5, seed=5).correr(avanzar_y_disparar(), avanzar_y_disparar())
    assert np.array_equal(b1.salud, b2.salud)
    assert np.array_equal(b1.ganador, b2.ganador)


def test_lluvia_con_fallo_total_no_deja_disparar():
    cfg = Config(n_soldados=(1, 1), unidades=1, distancia_inicial_m=20, alcance_max_m=200,
                 p_max=1.0, d50_m=1e9, punteria_sd=0.0, clima="lluvia", clima_lluvia_p_fallo=1.0)
    b = Batalla(cfg, B=1, seed=0)
    ordenes = np.zeros((1, 2, 1), int)
    for _ in range(5):
        b.paso(ordenes)
    assert b.salud.min() == 2  # nadie recibio dano: siempre fallo el encendido


def test_lluvia_reduce_el_alcance_efectivo():
    """A una distancia que entra en el alcance normal pero no en el reducido por
    lluvia, con seco el disparo sale y con lluvia (misma semilla) no."""
    cfg_base = dict(n_soldados=(1, 1), unidades=1, distancia_inicial_m=140, alcance_max_m=150,
                     p_max=1.0, d50_m=1e9, punteria_sd=0.0, clima_lluvia_p_fallo=0.0,
                     clima_lluvia_factor_alcance=0.5)
    b_seco = Batalla(Config(**cfg_base, clima="seco"), B=1, seed=0)
    b_lluvia = Batalla(Config(**cfg_base, clima="lluvia"), B=1, seed=0)
    ordenes = np.zeros((1, 2, 1), int)
    b_seco.paso(ordenes)
    b_lluvia.paso(ordenes)
    assert b_seco.salud[0].sum() < 4    # con seco (alcance 150) el disparo a 140 m conecta
    assert b_lluvia.salud[0].sum() == 4  # con lluvia (alcance efectivo 75) no llega


def test_clima_frena_la_marcha_mas_con_nieve_que_con_lluvia():
    ordenes = np.ones((1, 2, 1), int)  # AVANZAR
    avances = {}
    for clima in ("seco", "lluvia", "nieve"):
        cfg = Config(n_soldados=(5, 5), unidades=1, marcha_m_tick=4.5, p_max=0.0, clima=clima)
        b = Batalla(cfg, B=1, seed=0)
        y0 = float(b.y_unidad[0, 0, 0])
        b.paso(ordenes)
        avances[clima] = float(b.y_unidad[0, 0, 0]) - y0
    assert avances["nieve"] < avances["lluvia"] < avances["seco"]


def test_nieve_no_provoca_fallo_de_encendido():
    cfg = Config(n_soldados=(1, 1), unidades=1, distancia_inicial_m=20, alcance_max_m=200,
                 p_max=1.0, d50_m=1e9, punteria_sd=0.0, p_herida_grave=1.0, clima="nieve")
    b = Batalla(cfg, B=1, seed=0)
    ordenes = np.zeros((1, 2, 1), int)
    b.paso(ordenes)
    assert b.salud[0].sum() < 4  # el disparo conecta igual, la nieve no moja la polvora
