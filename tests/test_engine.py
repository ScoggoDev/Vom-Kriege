"""
Tests de humo del motor: verifican que el codigo hace lo que creemos que hace,
no que el modelo se parezca a la realidad (eso es validacion, ver CLAUDE.md).
"""
import numpy as np

from engine import Batalla, Config
from generals import avanzar_y_disparar, quieto


def test_salud_en_rango():
    cfg = Config(max_ticks=50)
    b = Batalla(cfg, B=5, seed=1).correr(avanzar_y_disparar(), avanzar_y_disparar())
    assert b.salud.min() >= 0
    assert b.salud.max() <= 2


def test_batalla_termina():
    cfg = Config(max_ticks=100)
    b = Batalla(cfg, B=10, seed=2).correr(avanzar_y_disparar(), avanzar_y_disparar())
    assert b.terminada.all()
    assert (b.duracion <= cfg.max_ticks).all()
    assert set(np.unique(b.ganador)) <= {-1, 0, 1}


def test_fuerza_mayor_gana_mas():
    cfg = Config(n_soldados=(150, 30), unidades=1, distancia_inicial_m=60)
    b = Batalla(cfg, B=100, seed=3).correr(quieto, quieto)
    assert (b.ganador == 0).mean() > 0.95


def test_simetria_sin_sesgo_de_bando():
    """Misma doctrina y fuerza en ambos bandos: ningun lado deberia ganar sistematicamente.
    Un sesgo fuerte aca suele ser un bug de geometria (bando 0 vs bando 1), no una ventaja real.
    Se usa una pelea a muerte (quieto/quieto, un impacto = fuera) para que siempre haya
    ganador: con avanzar_y_disparar y sin moral la batalla no termina (ver CLAUDE.md)."""
    cfg = Config(n_soldados=(80, 80), unidades=1, distancia_inicial_m=60, p_max=0.1,
                 d50_m=1e9, p_herida_grave=1.0, max_ticks=4000)
    tasas = []
    for seed in range(5):
        b = Batalla(cfg, B=40, seed=seed).correr(quieto, quieto)
        decididas = b.ganador != -1
        assert decididas.mean() > 0.8  # empates por aniquilacion mutua simultanea son raros pero posibles
        tasas.append((b.ganador[decididas] == 0).mean())
    assert 0.3 < np.mean(tasas) < 0.7
