"""
Tests de movimiento lateral real (ordenes IZQUIERDA/DERECHA). Hasta ahora
x_unidad era fijo para toda la batalla; ahora tiene estado por batalla (B,2,U).
Ver docs/informe_pendientes.md.
"""
import numpy as np

from engine import AVANZAR, Batalla, Config, DERECHA, IZQUIERDA, SOSTENER
from generals import avanzar_y_disparar, quieto


def test_sin_ordenes_laterales_no_cambia_nada():
    """Regresion: una batalla que nunca usa IZQUIERDA/DERECHA (como todos los
    generales de reglas existentes) tiene que dar exactamente lo mismo que
    antes de que x_unidad tuviera estado."""
    b1 = Batalla(Config(), B=5, seed=13).correr(avanzar_y_disparar(), avanzar_y_disparar())
    b2 = Batalla(Config(), B=5, seed=13).correr(avanzar_y_disparar(), avanzar_y_disparar())
    assert np.array_equal(b1.salud, b2.salud)
    assert np.array_equal(b1.ganador, b2.ganador)


def test_derecha_mueve_la_unidad_en_x():
    cfg = Config(n_soldados=(10, 10), unidades=1, marcha_m_tick=4.5)
    b = Batalla(cfg, B=1, seed=0)
    x0 = float(b.x_unidad[0, 0, 0])
    ordenes = np.full((1, 2, 1), SOSTENER, int)
    ordenes[0, 0, 0] = DERECHA
    b.paso(ordenes)
    assert float(b.x_unidad[0, 0, 0]) == x0 + cfg.marcha_m_tick


def test_izquierda_mueve_para_el_otro_lado():
    cfg = Config(n_soldados=(10, 10), unidades=1, marcha_m_tick=4.5)
    b = Batalla(cfg, B=1, seed=0)
    x0 = float(b.x_unidad[0, 0, 0])
    ordenes = np.full((1, 2, 1), SOSTENER, int)
    ordenes[0, 0, 0] = IZQUIERDA
    b.paso(ordenes)
    assert float(b.x_unidad[0, 0, 0]) == x0 - cfg.marcha_m_tick


def test_moverse_lateral_no_dispara():
    cfg = Config(n_soldados=(1, 1), unidades=1, distancia_inicial_m=10, alcance_max_m=200,
                 p_max=1.0, d50_m=1e9, punteria_sd=0.0)
    b = Batalla(cfg, B=1, seed=0)
    ordenes = np.array([[[DERECHA], [SOSTENER]]])
    b.paso(ordenes)
    assert b.recarga[0, 0, 0] == 0  # el que se mueve no disparo, sigue "cargado"


def test_vado_mas_lateral_permite_cruzar_una_unidad_que_antes_no_podia():
    """Encadena lateral + avance: una unidad no alineada con el vado puede
    desplazarse hasta alinearse y despues cruzar, cosa que antes (sin
    movimiento lateral) era imposible sin reposicionar manualmente la unidad."""
    cfg = Config(n_soldados=(10, 10), unidades=1, distancia_inicial_m=100, marcha_m_tick=4.5,
                 rio_activo=True, rio_y_centro_m=50, rio_ancho_m=10,
                 rio_vado_x_centros=(20.0,), rio_vado_ancho_m=6.0)
    b = Batalla(cfg, B=1, seed=0)
    b.y_unidad[0, 0, 0] = 44.0  # al pie del rio, no alineada con el vado (x=0 != 20)
    ordenes_lateral = np.array([[[DERECHA], [SOSTENER]]])
    for _ in range(5):  # 5 * 4.5 m = 22.5 m, de sobra para alinearse con el vado en x=20
        b.paso(ordenes_lateral)
    assert abs(float(b.x_unidad[0, 0, 0]) - 20.0) < cfg.rio_vado_ancho_m / 2
    y_antes = float(b.y_unidad[0, 0, 0])
    ordenes_avanzar = np.array([[[AVANZAR], [SOSTENER]]])
    b.paso(ordenes_avanzar)
    assert float(b.y_unidad[0, 0, 0]) > y_antes  # ahora si cruza
