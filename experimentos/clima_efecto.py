"""
Coherencia interna de fase 3 (clima): CDB90 1792-1815 tiene solo 4 batallas
humedas utilizables (contra 22 secas) y 0 humedas-y-frias, ver
experimentos/cdb90_clima.py. Demasiado poco para calibrar nada. Esto es,
entonces, una prueba de que el mecanismo mueve el resultado en la direccion
esperada (atacar bajo lluvia o nieve deberia costar mas), no una validacion.

Uso: python experimentos/clima_efecto.py
"""
import sys

import numpy as np

sys.path.insert(0, ".")
from engine import Batalla, Config
from generals import avanzar_y_disparar, quieto

SEMILLAS = (0, 1, 2, 3, 4)
B_POR_SEMILLA = 200


def correr(clima):
    cfg = Config(moral_activa=True, moral_umbral_media=0.4, moral_colapso_umbral=0.15, clima=clima)
    ganador, bajas0, bajas1, duraciones = [], [], [], []
    for seed in SEMILLAS:
        b = Batalla(cfg, B=B_POR_SEMILLA, seed=seed).correr(avanzar_y_disparar(), quieto)
        bajas = ((b.salud < 2) | b.huyendo).sum(-1)
        n0 = np.array(cfg.n_soldados, dtype=np.float64)
        pct = 100 * bajas / n0[None, :]
        ganador.append(b.ganador)
        bajas0.append(pct[:, 0])
        bajas1.append(pct[:, 1])
        duraciones.append(b.duracion)
    return (np.concatenate(ganador), np.concatenate(bajas0), np.concatenate(bajas1),
            np.concatenate(duraciones))


for clima in ("seco", "lluvia", "nieve"):
    g, b0, b1, dur = correr(clima)
    n = len(g)
    tasa_atacante = (g == 0).mean()
    sem = np.sqrt(tasa_atacante * (1 - tasa_atacante) / n)
    print(f"clima={clima} ({n} batallas)")
    print(f"  gana el atacante: {tasa_atacante:.1%} +- {sem:.1%}")
    print(f"  bajas atacante: {b0.mean():.1f}% +- {b0.std()/np.sqrt(n):.1f}%")
    print(f"  bajas defensor: {b1.mean():.1f}% +- {b1.std()/np.sqrt(n):.1f}%")
    print(f"  duracion media: {dur.mean():.0f} ticks ({dur.mean()*5:.0f} s)")
