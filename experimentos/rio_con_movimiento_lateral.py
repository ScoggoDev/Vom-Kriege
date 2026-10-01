"""
Compara el atacante fijo de experimentos/rio_cuello_de_botella.py (2 de 4
unidades alineadas con un vado, las otras dos quedan varadas para siempre)
contra el mismo escenario con cruzar_rio_y_disparar, que maniobra lateralmente
hacia el vado mas cercano antes de avanzar. Pone a prueba si el movimiento
lateral agregado efectivamente resuelve la limitacion que ya marcaba
docs/informe_fase2b_rio.md.

Uso: python experimentos/rio_con_movimiento_lateral.py
"""
import sys

import numpy as np

sys.path.insert(0, ".")
from engine import Batalla, Config
from generals import avanzar_y_disparar, cruzar_rio_y_disparar, quieto

SEMILLAS = (0, 1, 2, 3, 4)
B_POR_SEMILLA = 200

cfg = Config(
    moral_activa=True, moral_umbral_media=0.4, moral_colapso_umbral=0.15,
    rio_activo=True, rio_y_centro_m=150.0, rio_ancho_m=10.0,
    rio_vado_x_centros=(-10.5, 10.5), rio_vado_ancho_m=6.0,
)


def correr(general_atacante):
    ganador, bajas0, bajas1 = [], [], []
    for seed in SEMILLAS:
        b = Batalla(cfg, B=B_POR_SEMILLA, seed=seed).correr(general_atacante, quieto)
        bajas = ((b.salud < 2) | b.huyendo).sum(-1)
        n0 = np.array(cfg.n_soldados, dtype=np.float64)
        pct = 100 * bajas / n0[None, :]
        ganador.append(b.ganador)
        bajas0.append(pct[:, 0])
        bajas1.append(pct[:, 1])
    return np.concatenate(ganador), np.concatenate(bajas0), np.concatenate(bajas1)


for nombre, general in (("alineacion fija (avanzar_y_disparar)", avanzar_y_disparar()),
                         ("maniobra lateral (cruzar_rio_y_disparar)", cruzar_rio_y_disparar())):
    g, b0, b1 = correr(general)
    n = len(g)
    tasa = (g == 0).mean()
    print(f"{nombre}:")
    print(f"  gana el atacante: {tasa:.1%} +- {np.sqrt(tasa*(1-tasa)/n):.1%}")
    print(f"  bajas atacante: {b0.mean():.1f}% +- {b0.std()/np.sqrt(n):.1f}%  |  "
          f"bajas defensor: {b1.mean():.1f}% +- {b1.std()/np.sqrt(n):.1f}%")
