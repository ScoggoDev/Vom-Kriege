"""Tests de cansancio (fase 4b, ver docs/informe_fase4b_cansancio.md)."""
import numpy as np

from engine import Batalla, Config
from generals import avanzar_y_disparar, quieto


def test_flag_apagado_no_cambia_nada():
    extremos = dict(cansancio_activo=False, cansancio_por_marcha=1.0, cansancio_por_disparo=1.0,
                     cansancio_penal_punteria=1.0, cansancio_penal_recarga=100.0, cansancio_penal_moral=1.0)
    b1 = Batalla(Config(), B=5, seed=8).correr(avanzar_y_disparar(), avanzar_y_disparar())
    b2 = Batalla(Config(**extremos), B=5, seed=8).correr(avanzar_y_disparar(), avanzar_y_disparar())
    assert np.array_equal(b1.salud, b2.salud)
    assert np.array_equal(b1.ganador, b2.ganador)
    assert (b1.cansancio == 0).all()


def test_marchar_sube_el_cansancio_y_reposar_lo_baja():
    cfg = Config(n_soldados=(5, 5), unidades=1, cansancio_activo=True,
                 cansancio_por_marcha=0.05, cansancio_recuperacion=0.02)
    b = Batalla(cfg, B=1, seed=0)
    ordenes = np.ones((1, 2, 1), int)  # AVANZAR
    for _ in range(5):
        b.paso(ordenes)
    cansancio_tras_marchar = float(b.cansancio[0, 0, 0])
    assert cansancio_tras_marchar > 0

    ordenes_sosten = np.zeros((1, 2, 1), int)  # SOSTENER, sin disparar (nadie en rango)
    for _ in range(5):
        b.paso(ordenes_sosten)
    assert float(b.cansancio[0, 0, 0]) < cansancio_tras_marchar


def test_cansancio_alto_empeora_punteria():
    """Mismo seed, la unica diferencia es el cansancio inicial forzado a maximo:
    tiene que haber menos o igual impactos, nunca mas."""
    cfg = Config(n_soldados=(50, 50), unidades=1, distancia_inicial_m=50, alcance_max_m=200,
                 p_max=0.9, d50_m=1e9, punteria_sd=0.0, cansancio_activo=True,
                 cansancio_penal_punteria=0.8)
    ordenes = np.zeros((1, 2, 1), int)

    b_descansado = Batalla(cfg, B=1, seed=0)
    b_cansado = Batalla(cfg, B=1, seed=0)
    b_cansado.cansancio[:] = 1.0

    for _ in range(3):
        b_descansado.paso(ordenes)
        b_cansado.paso(ordenes)
    heridos_descansado = (b_descansado.salud[0, 1] < 2).sum()
    heridos_cansado = (b_cansado.salud[0, 1] < 2).sum()
    assert heridos_cansado <= heridos_descansado


def test_cansancio_nunca_sale_de_rango():
    cfg = Config(n_soldados=(5, 5), unidades=1, cansancio_activo=True,
                 cansancio_por_marcha=0.9, cansancio_recuperacion=0.9)
    b = Batalla(cfg, B=1, seed=0)
    ordenes = np.ones((1, 2, 1), int)
    for _ in range(20):
        b.paso(ordenes)
    assert b.cansancio.min() >= 0.0
    assert b.cansancio.max() <= 1.0
