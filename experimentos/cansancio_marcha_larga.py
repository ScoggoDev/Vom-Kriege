"""
Coherencia interna de fase 4b: un atacante que marcha mas para llegar al combate
deberia llegar mas cansado y pelear peor que uno que arranca mas cerca, en
igualdad de todo lo demas. No hay objetivo de CDB90 para esto (esa base no
registra distancia marchada), es una prueba de que el mecanismo empuja en la
direccion esperada.

Uso: python experimentos/cansancio_marcha_larga.py
"""
import sys

import numpy as np

sys.path.insert(0, ".")
from engine import Batalla, Config
from generals import avanzar_y_disparar, quieto

SEMILLAS = (0, 1, 2, 3, 4)
B_POR_SEMILLA = 200


def correr(distancia_inicial_m, cansancio_activo):
    cfg = Config(distancia_inicial_m=distancia_inicial_m, cansancio_activo=cansancio_activo,
                 moral_activa=True, moral_umbral_media=0.4, moral_colapso_umbral=0.15)
    ganador, bajas0 = [], []
    for seed in SEMILLAS:
        b = Batalla(cfg, B=B_POR_SEMILLA, seed=seed).correr(avanzar_y_disparar(), quieto)
        bajas = ((b.salud < 2) | b.huyendo).sum(-1)
        n0 = np.array(cfg.n_soldados, dtype=np.float64)
        bajas0.append(100 * bajas[:, 0] / n0[0])
        ganador.append(b.ganador)
    return np.concatenate(ganador), np.concatenate(bajas0)


for distancia in (100.0, 250.0, 450.0):
    for cansancio_activo in (False, True):
        g, b0 = correr(distancia, cansancio_activo)
        n = len(g)
        tasa = (g == 0).mean()
        print(f"distancia_inicial={distancia:.0f} m, cansancio_activo={cansancio_activo}: "
              f"gana atacante {tasa:.1%} +- {np.sqrt(tasa*(1-tasa)/n):.1%}, "
              f"bajas atacante {b0.mean():.1f}% +- {b0.std()/np.sqrt(n):.1f}%")
