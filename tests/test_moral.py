"""
Tests de la mecanica de moral (fase 1, ver docs/diseno.md seccion 3).
Son tests de humo del motor, no de validacion contra CDB90 (eso va en un
experimento de sensibilidad aparte, con muchas semillas y barras de error).
"""
import numpy as np

from engine import Batalla, Config
from generals import avanzar_y_disparar


def test_flag_apagado_no_activa_nada():
    """Con moral_activa=False (default) la mecanica no debe dejar rastro alguno,
    ni siquiera consumir el generador aleatorio: es la garantia de que fase 0 no cambia."""
    cfg = Config(max_ticks=100)
    b = Batalla(cfg, B=5, seed=1).correr(avanzar_y_disparar(), avanzar_y_disparar())
    assert b.umbral_huida is None
    assert not b.huyendo.any()
    assert (b.huida_y == 0).all()


def test_huyendo_no_dispara():
    """Un soldado marcado como huyendo, aunque este cargado y tenga blanco a tiro,
    no debe disparar el tick siguiente (se ve en que su arma sigue 'cargada')."""
    cfg = Config(n_soldados=(2, 2), unidades=1, distancia_inicial_m=10, alcance_max_m=150)
    b = Batalla(cfg, B=1, seed=0)
    b.huyendo[0, 0, 0] = True  # bando 0, soldado 0: forzado a huir
    ordenes = np.zeros((1, 2, 1), int)  # SOSTENER para ambos bandos
    b.paso(ordenes)
    assert b.recarga[0, 0, 0] == 0  # no disparo: sigue con el arma cargada
    assert b.recarga[0, 0, 1] > 0   # el companero que no huye si disparo


def test_colapso_termina_batallas_que_antes_no_terminaban():
    """Hallazgo de CLAUDE.md: sin moral, avanzar_y_disparar simetrico no termina en 30 min.
    Con moral activa, la mayoria de las batallas deberian terminar por colapso antes de tiempo."""
    cfg = Config(moral_activa=True, moral_umbral_media=0.4, moral_colapso_umbral=0.5)
    b = Batalla(cfg, B=40, seed=7).correr(avanzar_y_disparar(), avanzar_y_disparar())
    assert b.terminada.all()
    assert (b.duracion < cfg.max_ticks).mean() > 0.7
    assert (b.ganador != -1).mean() > 0.7


def test_umbral_mas_bajo_acorta_la_batalla():
    """Sanity de monotonia: mas facil huir (umbral mas bajo) deberia acortar la batalla,
    no es una calibracion contra datos reales, solo un chequeo de que el mecanismo anda al reves."""
    duraciones = {}
    for umbral in (0.2, 0.7):
        cfg = Config(moral_activa=True, moral_umbral_media=umbral, moral_colapso_umbral=0.5)
        b = Batalla(cfg, B=40, seed=11).correr(avanzar_y_disparar(), avanzar_y_disparar())
        duraciones[umbral] = b.duracion.mean()
    assert duraciones[0.2] < duraciones[0.7]
