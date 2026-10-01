"""
Tests de formaciones (linea/columna) y mele (carga a la bayoneta). Ver
docs/informe_formaciones_mele.md. Sin cuadro: no hay caballeria que lo
justifique, seria una linea estrictamente peor para infanteria contra
infanteria.
"""
import numpy as np

from engine import (AVANZAR, Batalla, CARGAR, COLUMNA, Config, FORMAR_COLUMNA,
                     FORMAR_LINEA, LINEA, SOSTENER)
from generals import avanzar_y_disparar


def test_formaciones_apagado_no_cambia_nada():
    extremos = dict(formaciones_activo=False, columna_factor_marcha=5.0,
                     columna_factor_disparo=0.01, columna_factor_recibido=5.0)
    b1 = Batalla(Config(), B=5, seed=14).correr(avanzar_y_disparar(), avanzar_y_disparar())
    b2 = Batalla(Config(**extremos), B=5, seed=14).correr(avanzar_y_disparar(), avanzar_y_disparar())
    assert np.array_equal(b1.salud, b2.salud)
    assert (b1.formacion == LINEA).all()


def test_mele_apagado_no_cambia_nada():
    extremos = dict(mele_activo=False, mele_distancia_m=1000.0, mele_p_baja=1.0)
    b1 = Batalla(Config(), B=5, seed=15).correr(avanzar_y_disparar(), avanzar_y_disparar())
    b2 = Batalla(Config(**extremos), B=5, seed=15).correr(avanzar_y_disparar(), avanzar_y_disparar())
    assert np.array_equal(b1.salud, b2.salud)


def test_orden_cambia_la_formacion():
    cfg = Config(n_soldados=(10, 10), unidades=1, formaciones_activo=True)
    b = Batalla(cfg, B=1, seed=0)
    assert b.formacion[0, 0, 0] == LINEA
    ordenes = np.full((1, 2, 1), FORMAR_COLUMNA, int)
    b.paso(ordenes)
    assert b.formacion[0, 0, 0] == COLUMNA
    ordenes = np.full((1, 2, 1), FORMAR_LINEA, int)
    b.paso(ordenes)
    assert b.formacion[0, 0, 0] == LINEA


def test_cambiar_formacion_no_dispara_ni_avanza():
    cfg = Config(n_soldados=(1, 1), unidades=1, distancia_inicial_m=10, alcance_max_m=200,
                 p_max=1.0, d50_m=1e9, punteria_sd=0.0, formaciones_activo=True)
    b = Batalla(cfg, B=1, seed=0)
    y0 = float(b.y_unidad[0, 0, 0])
    ordenes = np.array([[[FORMAR_COLUMNA], [SOSTENER]]])
    b.paso(ordenes)
    assert b.recarga[0, 0, 0] == 0  # no disparo, sigue cargado
    assert float(b.y_unidad[0, 0, 0]) == y0  # no se movio


def test_columna_marcha_mas_rapido():
    cfg = Config(n_soldados=(5, 5), unidades=1, marcha_m_tick=4.5, p_max=0.0, formaciones_activo=True)
    ordenes = np.array([[[AVANZAR], [SOSTENER]]])

    b_linea = Batalla(cfg, B=1, seed=0)
    b_linea.paso(ordenes)
    avance_linea = float(b_linea.y_unidad[0, 0, 0])

    b_columna = Batalla(cfg, B=1, seed=0)
    b_columna.formacion[:, 0, 0] = COLUMNA
    b_columna.paso(ordenes)
    avance_columna = float(b_columna.y_unidad[0, 0, 0])

    assert avance_columna > avance_linea


def test_columna_recibe_mas_impactos():
    """Mismo seed: la unica diferencia es la formacion del blanco. Tiene que
    haber mas o igual impactos contra la columna que contra la linea."""
    cfg = Config(n_soldados=(30, 30), unidades=1, distancia_inicial_m=50, alcance_max_m=200,
                 p_max=0.5, d50_m=1e9, punteria_sd=0.0, formaciones_activo=True)
    ordenes = np.zeros((1, 2, 1), int)

    b_linea = Batalla(cfg, B=1, seed=0)
    b_columna = Batalla(cfg, B=1, seed=0)
    b_columna.formacion[:, 1, 0] = COLUMNA  # el bando 1 (blanco) esta en columna

    for _ in range(3):
        b_linea.paso(ordenes)
        b_columna.paso(ordenes)
    heridos_linea = (b_linea.salud[0, 1] < 2).sum()
    heridos_columna = (b_columna.salud[0, 1] < 2).sum()
    assert heridos_columna >= heridos_linea


def test_cargar_avanza_hasta_el_contacto_y_despues_pelea_cuerpo_a_cuerpo():
    cfg = Config(n_soldados=(10, 10), unidades=1, distancia_inicial_m=20, marcha_m_tick=4.5,
                 mele_activo=True, mele_distancia_m=5.0, mele_p_baja=1.0, p_herida_grave=1.0)
    b = Batalla(cfg, B=1, seed=0)
    ordenes = np.array([[[CARGAR], [SOSTENER]]])
    for _ in range(5):  # de sobra para cerrar 20 m a 4.5 m/tick
        b.paso(ordenes)
        if b.distancia_unidades_al_enemigo()[0, 0, 0] <= cfg.mele_distancia_m:
            break
    assert b.distancia_unidades_al_enemigo()[0, 0, 0] <= cfg.mele_distancia_m
    salud_antes = b.salud[0, 1].sum()
    b.paso(ordenes)  # un tick mas, ya en contacto: tiene que pelear cuerpo a cuerpo
    assert b.salud[0, 1].sum() < salud_antes  # con mele_p_baja=1.0, alguien cae seguro


def test_mele_da_bajas_sin_municion_ni_alcance():
    """El mele funciona aunque el blanco este fuera del alcance de fuego o sin
    municion: es cuerpo a cuerpo, no depende del arma a distancia."""
    cfg = Config(n_soldados=(5, 5), unidades=1, distancia_inicial_m=3, alcance_max_m=0,
                 municion_activa=True, municion_inicial=0,
                 mele_activo=True, mele_distancia_m=5.0, mele_p_baja=1.0, p_herida_grave=1.0)
    b = Batalla(cfg, B=1, seed=0)
    ordenes = np.array([[[CARGAR], [SOSTENER]]])
    b.paso(ordenes)
    assert b.salud[0, 1].sum() < 10  # igual hubo bajas en mele, pese a alcance_max_m=0 y 0 municion
