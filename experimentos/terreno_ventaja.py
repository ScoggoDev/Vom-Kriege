"""
Sensibilidad/validacion cualitativa de fase 2a (elevacion + cobertura): comparar
un choque simetrico (100 vs 100) donde el defensor sostiene una loma con cobertura
contra el mismo choque sin terreno (terreno_activo=False), para ver si el motor
efectivamente premia sostener terreno alto y cubierto.

No hay un numero de CDB90 para comparar esto directamente (esa base no tiene
"tenia la loma" como variable limpia). Esto es una prueba de coherencia interna:
si defender la loma no ayuda nada, o ayuda de forma absurda, es señal de bug antes
que de un resultado real (ver CLAUDE.md: "cualquier tactica rara... es un posible
bug del simulador hasta demostrar lo contrario").

El defensor (bando 1) no se mueve de su posicion inicial, que coincide con el
centro de la cresta y de la cobertura. El atacante (bando 0) avanza y dispara.

Uso: python experimentos/terreno_ventaja.py
"""
import sys

import numpy as np

sys.path.insert(0, ".")
from engine import Batalla, Config
from generals import avanzar_y_disparar, quieto

SEMILLAS = (0, 1, 2, 3, 4)
B_POR_SEMILLA = 200


def correr(terreno_activo):
    cfg = Config(
        moral_activa=True, moral_umbral_media=0.4, moral_colapso_umbral=0.15,
        terreno_activo=terreno_activo,
        terreno_cresta_y_m=250.0, terreno_cresta_alto_m=8.0, terreno_cresta_ancho_m=40.0,
        terreno_cobertura_y_centro_m=250.0, terreno_cobertura_y_ancho_m=40.0,
        terreno_cobertura_x_centro_m=0.0, terreno_cobertura_x_ancho_m=200.0,
        terreno_cobertura_reduccion=0.5,
    )
    ganador, bajas0, bajas1 = [], [], []
    for seed in SEMILLAS:
        b = Batalla(cfg, B=B_POR_SEMILLA, seed=seed).correr(avanzar_y_disparar(), quieto)
        bajas = ((b.salud < 2) | b.huyendo).sum(-1)  # (B,2)
        n0 = np.array(cfg.n_soldados, dtype=np.float64)
        pct = 100 * bajas / n0[None, :]
        ganador.append(b.ganador)
        bajas0.append(pct[:, 0])
        bajas1.append(pct[:, 1])
    return np.concatenate(ganador), np.concatenate(bajas0), np.concatenate(bajas1)


for terreno_activo in (False, True):
    g, b0, b1 = correr(terreno_activo)
    n = len(g)
    tasa_defensor = (g == 1).mean()
    sem_defensor = np.sqrt(tasa_defensor * (1 - tasa_defensor) / n)
    print(f"terreno_activo={terreno_activo} ({n} batallas)")
    print(f"  bando 1 (defensor, quieto en la loma) gana: {tasa_defensor:.1%} +- {sem_defensor:.1%}")
    print(f"  bajas atacante (bando 0): {b0.mean():.1f}% +- {b0.std()/np.sqrt(n):.1f}%")
    print(f"  bajas defensor (bando 1): {b1.mean():.1f}% +- {b1.std()/np.sqrt(n):.1f}%")
