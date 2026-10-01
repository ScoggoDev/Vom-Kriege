"""
Tests de terreno clave: desempate por tiempo cuando se agota el reloj sin un
ganador decidido (CLAUDE.md: "si se acaba el tiempo, gana quien controle el
terreno clave, para que la pasividad no convenga"). Ver docs/informe_pendientes.md.
"""
import numpy as np

from engine import Batalla, Config, SOSTENER
from generals import avanzar_y_disparar, quieto


def test_flag_apagado_sigue_dando_empate_por_tiempo():
    cfg = Config(max_ticks=20, p_max=0.0)  # nadie recibe dano, nunca hay un ganador por combate
    b = Batalla(cfg, B=5, seed=0).correr(quieto, quieto)
    assert (b.ganador == -1).all()


def test_controla_la_zona_gana_por_tiempo():
    cfg = Config(n_soldados=(10, 10), unidades=1, max_ticks=5, p_max=0.0,
                 terreno_clave_activo=True, terreno_clave_x_centro_m=0.0, terreno_clave_y_centro_m=0.0,
                 terreno_clave_x_ancho_m=1000.0, terreno_clave_y_ancho_m=1000.0)
    b = Batalla(cfg, B=1, seed=0)
    # la zona clave es gigante (cubre todo el mapa): el bando 0 siempre tiene
    # mas soldados existentes (10 vs 10 es empate en cantidad, asi que forzamos
    # una ventaja matando a un soldado del bando 1 para desempatar)
    b.salud[0, 1, 0] = 0
    ordenes = np.full((1, 2, 1), SOSTENER, int)
    for _ in range(5):
        b.paso(ordenes)
    assert b.ganador[0] == 0  # bando 0 controla la zona (mas soldados vivos adentro)


def test_sin_terreno_clave_el_que_tiene_mas_gente_en_una_zona_no_importa():
    cfg = Config(n_soldados=(10, 10), unidades=1, max_ticks=5, p_max=0.0, terreno_clave_activo=False)
    b = Batalla(cfg, B=1, seed=0)
    b.salud[0, 1, 0] = 0
    ordenes = np.full((1, 2, 1), SOSTENER, int)
    for _ in range(5):
        b.paso(ordenes)
    assert b.ganador[0] == -1  # sin el flag, el desempate sigue siendo por tiempo agotado = empate
