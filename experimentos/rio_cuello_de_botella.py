"""
Coherencia interna de fase 2b: si un rio con vados fuerza a la mitad de las
unidades atacantes a quedar varadas en la orilla (no estan alineadas con ningun
vado), el atacante deberia salir mucho peor parado que sin el rio, porque cruza
con la mitad de la fuerza contra el total del defensor.

No hay maniobra lateral todavia (ver tests/test_rio_pantano.py), asi que esto es
una prueba de que el cuello de botella funciona como cabria esperar en el caso
mas simple (alineacion fija), no una simulacion de que tan bien un general real
elegiria por donde cruzar.

Uso: python experimentos/rio_cuello_de_botella.py
"""
import sys

import numpy as np

sys.path.insert(0, ".")
from engine import Batalla, Config
from generals import avanzar_y_disparar, quieto

SEMILLAS = (0, 1, 2, 3, 4)
B_POR_SEMILLA = 200


def correr(rio_activo):
    cfg = Config(
        moral_activa=True, moral_umbral_media=0.4, moral_colapso_umbral=0.15,
        rio_activo=rio_activo, rio_y_centro_m=150.0, rio_ancho_m=10.0,
        rio_vado_x_centros=(-10.5, 10.5), rio_vado_ancho_m=6.0,  # alinea 2 de las 4 unidades (ver x_unidad por defecto)
    )
    ganador, bajas0, bajas1 = [], [], []
    for seed in SEMILLAS:
        b = Batalla(cfg, B=B_POR_SEMILLA, seed=seed).correr(avanzar_y_disparar(), quieto)
        bajas = ((b.salud < 2) | b.huyendo).sum(-1)
        n0 = np.array(cfg.n_soldados, dtype=np.float64)
        pct = 100 * bajas / n0[None, :]
        ganador.append(b.ganador)
        bajas0.append(pct[:, 0])
        bajas1.append(pct[:, 1])
    return np.concatenate(ganador), np.concatenate(bajas0), np.concatenate(bajas1)


for rio_activo in (False, True):
    g, b0, b1 = correr(rio_activo)
    n = len(g)
    tasa_atacante = (g == 0).mean()
    sem_atacante = np.sqrt(tasa_atacante * (1 - tasa_atacante) / n)
    print(f"rio_activo={rio_activo} ({n} batallas, 2 de 4 unidades atacantes alineadas con un vado)")
    print(f"  gana el atacante: {tasa_atacante:.1%} +- {sem_atacante:.1%}")
    print(f"  bajas atacante: {b0.mean():.1f}% +- {b0.std()/np.sqrt(n):.1f}%")
    print(f"  bajas defensor: {b1.mean():.1f}% +- {b1.std()/np.sqrt(n):.1f}%")
