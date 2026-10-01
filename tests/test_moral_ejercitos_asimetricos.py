"""
Regresion de un bug real: cuando un bando tiene menos soldados que
max(n_soldados), las casillas de relleno tienen salud=0 para siempre (nunca
existieron) pero antes se contaban como "perdidos" en el calculo de moral desde
el primer tick, haciendo que el bando mas chico huyera sin ningun combate.
Encontrado al armar experimentos/fase6_lanchester_combinado.py.
"""
import numpy as np

from engine import Batalla, Config


def test_bando_mas_chico_no_huye_sin_combate():
    cfg = Config(n_soldados=(100, 60), unidades=1, distancia_inicial_m=60, p_max=0.0,
                 moral_activa=True, moral_umbral_media=0.4, moral_colapso_umbral=1.0)
    b = Batalla(cfg, B=20, seed=0)
    ordenes = np.zeros((20, 2, 1), int)  # SOSTENER, p_max=0 => nadie recibe dano nunca
    for _ in range(10):
        b.paso(ordenes)
    assert not b.huyendo.any()
    assert (b.salud[:, 1, :60] == 2).all()  # los 60 soldados reales siguen sanos
    assert (b.salud[:, 1, 60:] == 0).all()  # las casillas de relleno siguen en 0, como corresponde


def test_bando_mas_chico_con_terreno_y_humo_no_huye_sin_combate():
    """El bug original aparecia especificamente con terreno activo bloqueando la
    linea de tiro (combate real = 0) y humo activo, con ejercitos asimetricos."""
    cfg = Config(n_soldados=(100, 90), unidades=1, distancia_inicial_m=60,
                 moral_activa=True, moral_umbral_media=0.4, moral_colapso_umbral=1.0,
                 terreno_activo=True, terreno_cresta_y_m=30.0, terreno_cresta_alto_m=8.0,
                 terreno_cresta_ancho_m=20.0, humo_activo=True)
    b = Batalla(cfg, B=1, seed=90)
    ordenes = np.zeros((1, 2, 1), int)
    b.paso(ordenes)
    assert b.huyendo[0, 1].sum() == 0
