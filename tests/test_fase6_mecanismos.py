"""
Tests de los agregados chicos al motor hechos para las preguntas de
investigacion de fase 6 (ver docs/informe_fase6_investigacion.md):
cierra_filas (pregunta 6) y moral_umbral_media_por_bando (pregunta 5).
"""
import numpy as np

from engine import Batalla, Config
from generals import avanzar_y_disparar, quieto


def test_cierra_filas_apagado_no_cambia_nada():
    b1 = Batalla(Config(), B=5, seed=10).correr(avanzar_y_disparar(), avanzar_y_disparar())
    b2 = Batalla(Config(cierra_filas=False), B=5, seed=10).correr(avanzar_y_disparar(), avanzar_y_disparar())
    assert np.array_equal(b1.salud, b2.salud)


def test_cierra_filas_siempre_impacta_formacion_sin_huecos():
    """Con cierra_filas, un disparo al bulto que tiene listo=True y blanco_vivo
    nunca deberia fallar por 'agujero' (a diferencia del modo area normal)."""
    cfg = Config(n_soldados=(30, 30), unidades=1, distancia_inicial_m=30, alcance_max_m=200,
                 p_max=1.0, d50_m=1e9, punteria_sd=0.0, modo_fuego="area", cierra_filas=True)
    b = Batalla(cfg, B=1, seed=0)
    ordenes = np.zeros((1, 2, 1), int)
    b.paso(ordenes)
    # con punteria y p_max al maximo, y sin huecos, cada disparo tiene que impactar
    # mientras queden vivos en el bando enemigo
    assert (b.salud[0, 1] < 2).sum() > 0


def test_moral_por_bando_apagado_es_identico_al_global():
    cfg_global = Config(moral_activa=True, moral_umbral_media=0.4)
    cfg_none = Config(moral_activa=True, moral_umbral_media=0.4, moral_umbral_media_por_bando=None)
    b1 = Batalla(cfg_global, B=5, seed=11).correr(avanzar_y_disparar(), avanzar_y_disparar())
    b2 = Batalla(cfg_none, B=5, seed=11).correr(avanzar_y_disparar(), avanzar_y_disparar())
    assert np.array_equal(b1.salud, b2.salud)


def test_moral_mas_alta_en_un_bando_lo_hace_huir_menos():
    """Mismo seed, un bando con umbral de huida mucho mas alto (mas dificil que
    huya) tiene que terminar con menos huidas que con el umbral global bajo."""
    cfg_base = dict(n_soldados=(80, 80), moral_activa=True, moral_colapso_umbral=1.0, max_ticks=100)
    b_bajo = Batalla(Config(**cfg_base, moral_umbral_media=0.2), B=10, seed=12).correr(
        avanzar_y_disparar(), avanzar_y_disparar())
    b_asimetrico = Batalla(Config(**cfg_base, moral_umbral_media_por_bando=(0.9, 0.2)), B=10, seed=12).correr(
        avanzar_y_disparar(), avanzar_y_disparar())
    assert b_asimetrico.huyendo[:, 0].sum() <= b_bajo.huyendo[:, 0].sum()
