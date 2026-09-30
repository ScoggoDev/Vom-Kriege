"""
Tests de terreno: elevacion, defensa en contrapendiente y cobertura (fase 2a,
ver docs/diseno.md seccion 3 y docs/informe_fase2a_terreno.md).
"""
import numpy as np
import pytest

from engine import Batalla, Config
from generals import avanzar_y_disparar


def test_flag_apagado_terreno_no_cambia_nada():
    """Con terreno_activo=False, ni siquiera parametros de terreno extremos deben
    cambiar el resultado: el flag tiene que gatear todo el mecanismo."""
    extremos = dict(terreno_activo=False, terreno_cresta_alto_m=1000,
                     terreno_cobertura_reduccion=0.0, terreno_frena_por_m_subida=1.0)
    b1 = Batalla(Config(), B=5, seed=3).correr(avanzar_y_disparar(), avanzar_y_disparar())
    b2 = Batalla(Config(**extremos), B=5, seed=3).correr(avanzar_y_disparar(), avanzar_y_disparar())
    assert np.array_equal(b1.salud, b2.salud)
    assert np.array_equal(b1.ganador, b2.ganador)


def test_altura_pico_en_la_cresta():
    cfg = Config(terreno_cresta_y_m=100, terreno_cresta_alto_m=10, terreno_cresta_ancho_m=20)
    b = Batalla(cfg, B=1, seed=0)
    h = b.altura(np.array([100.0, 80.0, 120.0, 300.0]))
    assert h[0] == pytest.approx(10.0)
    assert h[1] < h[0] and h[2] < h[0]
    assert h[3] < 0.01


def test_en_cobertura_geometria():
    cfg = Config(terreno_cobertura_x_centro_m=0, terreno_cobertura_x_ancho_m=20,
                 terreno_cobertura_y_centro_m=100, terreno_cobertura_y_ancho_m=20)
    b = Batalla(cfg, B=1, seed=0)
    assert b.en_cobertura(np.array(0.0), np.array(100.0))
    assert not b.en_cobertura(np.array(50.0), np.array(100.0))
    assert not b.en_cobertura(np.array(0.0), np.array(200.0))


def test_cresta_bloquea_la_linea_de_tiro():
    """Una cresta alta entre tirador y blanco tiene que impedir el disparo por completo
    (defensa en contrapendiente), no solo reducir la probabilidad de impacto."""
    cfg = Config(n_soldados=(1, 1), unidades=1, distancia_inicial_m=100, alcance_max_m=200,
                 p_max=1.0, d50_m=1e9, punteria_sd=0.0, terreno_activo=True,
                 terreno_cresta_y_m=50, terreno_cresta_alto_m=50, terreno_cresta_ancho_m=15)
    b = Batalla(cfg, B=1, seed=0)
    ordenes = np.zeros((1, 2, 1), int)  # SOSTENER
    for _ in range(5):
        b.paso(ordenes)
    assert b.salud.min() == 2  # nadie recibio dano pese a p_max=1.0 y alcance de sobra


def test_sin_cresta_el_disparo_pasa():
    """Mismo escenario que el anterior pero sin cresta (control): el disparo si conecta."""
    cfg = Config(n_soldados=(1, 1), unidades=1, distancia_inicial_m=100, alcance_max_m=200,
                 p_max=1.0, d50_m=1e9, punteria_sd=0.0, p_herida_grave=1.0,
                 terreno_activo=True, terreno_cresta_y_m=50, terreno_cresta_alto_m=0)
    b = Batalla(cfg, B=1, seed=0)
    ordenes = np.zeros((1, 2, 1), int)
    b.paso(ordenes)
    assert b.salud[0].sum() < 4


def test_cobertura_reduce_impactos():
    """Con las dos corridas usando la misma semilla, la unica diferencia es la
    reduccion de cobertura, asi que consumen el generador aleatorio identico: la
    comparacion es practicamente determinista, no solo estadistica."""
    base = dict(n_soldados=(50, 50), unidades=1, distancia_inicial_m=50, alcance_max_m=200,
                p_max=0.9, d50_m=1e9, punteria_sd=0.0, p_herida_grave=0.0,
                terreno_activo=True, terreno_cresta_alto_m=0,
                terreno_cobertura_y_centro_m=50, terreno_cobertura_y_ancho_m=200,
                terreno_cobertura_x_centro_m=0, terreno_cobertura_x_ancho_m=200)
    ordenes = np.zeros((1, 2, 1), int)

    b_con = Batalla(Config(**base, terreno_cobertura_reduccion=0.3), B=1, seed=0)
    b_sin = Batalla(Config(**base, terreno_cobertura_reduccion=1.0), B=1, seed=0)
    for _ in range(3):
        b_con.paso(ordenes)
        b_sin.paso(ordenes)
    heridos_con = (b_con.salud[0, 1] < 2).sum()
    heridos_sin = (b_sin.salud[0, 1] < 2).sum()
    assert heridos_con < heridos_sin


def test_pendiente_frena_el_avance():
    cfg = Config(n_soldados=(10, 10), unidades=1, distancia_inicial_m=100, marcha_m_tick=4.5,
                 terreno_activo=True, terreno_cresta_y_m=50, terreno_cresta_alto_m=20,
                 terreno_cresta_ancho_m=10, terreno_frena_por_m_subida=0.1, p_max=0.0)
    b = Batalla(cfg, B=1, seed=0)
    b.y_unidad[0, 0, 0] = 45.0  # al pie de la cresta, subiendo
    ordenes = np.ones((1, 2, 1), int)  # AVANZAR
    y0 = float(b.y_unidad[0, 0, 0])
    b.paso(ordenes)
    avance = float(b.y_unidad[0, 0, 0]) - y0
    assert 0 < avance < cfg.marcha_m_tick
