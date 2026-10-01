"""
Pregunta de investigacion 5 (docs/diseno.md seccion 7): ¿un ejercito chico con
moral alta le gana a uno grande? ¿Donde esta el punto de quiebre?

Bando A (chico, tamaño variable) con moral_umbral_media alto (0.7, mas dificil
que huya) contra bando B (fijo en 100) con la moral calibrada en fase 1 (0.4).
Usa moral_umbral_media_por_bando, agregado para esta pregunta (ver el commit que
lo agrego: necesita moral distinta por bando, cosa que Config no permitia antes).

Uso: python experimentos/fase6_moral_vs_tamano.py
"""
import sys

import numpy as np

sys.path.insert(0, ".")
from engine import Batalla, Config
from generals import quieto

SEMILLAS = (0, 1, 2, 3, 4)
B_POR_SEMILLA = 200
UMBRAL_A, UMBRAL_B = 0.7, 0.4


def correr(n_a):
    cfg = Config(
        n_soldados=(n_a, 100), unidades=1, distancia_inicial_m=60, p_max=0.1, d50_m=1e9,
        p_herida_grave=0.5, punteria_sd=0.0,
        moral_activa=True, moral_umbral_media_por_bando=(UMBRAL_A, UMBRAL_B), moral_colapso_umbral=0.15,
        max_ticks=2000,
    )
    ganador = []
    for seed in SEMILLAS:
        b = Batalla(cfg, B=B_POR_SEMILLA, seed=seed).correr(quieto, quieto)
        ganador.append(b.ganador)
    return np.concatenate(ganador)


print(f"bando A: moral_umbral_media={UMBRAL_A} (dificil que huya) | bando B fijo en 100, moral_umbral_media={UMBRAL_B}")
print(" tamaño A | gana A | gana B | empate/tiempo")
for n_a in (100, 90, 80, 70, 60, 50, 40, 30):
    g = correr(n_a)
    n = len(g)
    gana_a, gana_b, empate = (g == 0).mean(), (g == 1).mean(), (g == -1).mean()
    sem = np.sqrt(gana_a * (1 - gana_a) / n)
    print(f"   {n_a:3d}    | {gana_a:5.1%} ± {sem:.1%} | {gana_b:5.1%} | {empate:5.1%}")
