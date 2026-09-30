"""
Tests de rio, vados y pantano (fase 2b, ver docs/informe_fase2b_rio.md).

Simplificacion deliberada: no hay movimiento lateral en el motor todavia, asi que
el "vado" no es algo hacia lo que una unidad pueda maniobrar, es una coincidencia
fija entre la posicion en x de la unidad (que no cambia en toda la batalla) y la
posicion del vado. Una unidad esta alineada con un vado o no lo esta, para
siempre. Es suficiente para probar la dinamica de cuello de botella (algunas
unidades cruzan, otras quedan varadas en la orilla) sin agregar maniobra lateral.
"""
import numpy as np
import pytest

from engine import Batalla, Config
from generals import avanzar_y_disparar


def test_flag_apagado_rio_pantano_no_cambia_nada():
    extremos = dict(rio_activo=False, rio_ancho_m=1000, rio_vado_x_centros=(9999.0,),
                     pantano_activo=False, pantano_factor_marcha=0.0)
    b1 = Batalla(Config(), B=5, seed=4).correr(avanzar_y_disparar(), avanzar_y_disparar())
    b2 = Batalla(Config(**extremos), B=5, seed=4).correr(avanzar_y_disparar(), avanzar_y_disparar())
    assert np.array_equal(b1.salud, b2.salud)
    assert np.array_equal(b1.ganador, b2.ganador)


def test_rio_bloquea_unidad_no_alineada_con_ningun_vado():
    cfg = Config(n_soldados=(10, 10), unidades=1, distancia_inicial_m=100, marcha_m_tick=4.5,
                 rio_activo=True, rio_y_centro_m=50, rio_ancho_m=10,
                 rio_vado_x_centros=(1000.0,), rio_vado_ancho_m=5)
    b = Batalla(cfg, B=1, seed=0)
    b.y_unidad[0, 0, 0] = 44.0  # el proximo paso la mete en la franja del rio
    ordenes = np.ones((1, 2, 1), int)  # AVANZAR
    y0 = float(b.y_unidad[0, 0, 0])
    b.paso(ordenes)
    assert float(b.y_unidad[0, 0, 0]) == y0


def test_vado_permite_cruzar_a_la_unidad_alineada():
    cfg = Config(n_soldados=(10, 10), unidades=1, distancia_inicial_m=100, marcha_m_tick=4.5,
                 rio_activo=True, rio_y_centro_m=50, rio_ancho_m=10,
                 rio_vado_x_centros=(0.0,), rio_vado_ancho_m=5)  # unidades=1 => x_unidad = 0
    b = Batalla(cfg, B=1, seed=0)
    b.y_unidad[0, 0, 0] = 44.0
    ordenes = np.ones((1, 2, 1), int)
    y0 = float(b.y_unidad[0, 0, 0])
    b.paso(ordenes)
    avance = float(b.y_unidad[0, 0, 0]) - y0
    assert avance == pytest.approx(cfg.marcha_m_tick)


def test_pantano_frena_la_marcha():
    cfg = Config(n_soldados=(10, 10), unidades=1, distancia_inicial_m=100, marcha_m_tick=4.5,
                 pantano_activo=True, pantano_y_centro_m=50, pantano_y_ancho_m=20,
                 pantano_x_centro_m=0, pantano_x_ancho_m=200, pantano_factor_marcha=0.4)
    b = Batalla(cfg, B=1, seed=0)
    b.y_unidad[0, 0, 0] = 45.0  # dentro del pantano (40-60)
    ordenes = np.ones((1, 2, 1), int)
    y0 = float(b.y_unidad[0, 0, 0])
    b.paso(ordenes)
    avance = float(b.y_unidad[0, 0, 0]) - y0
    assert avance == pytest.approx(cfg.marcha_m_tick * cfg.pantano_factor_marcha)


def test_cruce_bajo_fuego_aumenta_la_huida():
    """Dos batallas con la misma semilla (mismos umbrales de huida sorteados) difieren
    solo en si la unidad esta cruzando el rio. Como la penalidad solo suma a la
    fraccion percibida, el conjunto de quien huye cruzando el rio tiene que incluir
    (no solo igualar) al conjunto de quien huye quieto lejos del rio."""
    base = dict(n_soldados=(20, 20), unidades=1, distancia_inicial_m=100, p_max=0.0,
                moral_activa=True, moral_umbral_media=0.5, moral_umbral_sd=0.15,
                moral_colapso_umbral=1.0, rio_activo=True, rio_y_centro_m=50, rio_ancho_m=10)
    ordenes = np.zeros((1, 2, 1), int)

    b_cruzando = Batalla(Config(**base), B=1, seed=7)
    b_cruzando.salud[0, 0, :10] = 0
    b_cruzando.y_unidad[0, 0, 0] = 50.0  # dentro de la franja del rio

    b_lejos = Batalla(Config(**base), B=1, seed=7)
    b_lejos.salud[0, 0, :10] = 0
    b_lejos.y_unidad[0, 0, 0] = 0.0  # lejos del rio

    b_cruzando.paso(ordenes)
    b_lejos.paso(ordenes)
    huyeron_cruzando = int(b_cruzando.huyendo[0, 0].sum())
    huyeron_lejos = int(b_lejos.huyendo[0, 0].sum())
    assert huyeron_cruzando >= huyeron_lejos
    assert huyeron_cruzando > 0
