"""
Disciplina de fuego (fase 4, ver docs/diseno.md seccion 3) no se construyo como
mecanica nueva del motor: ya esta implicita en el parametro distancia_m del
general avanzar_y_disparar. Mientras la orden es AVANZAR nadie dispara (ver
engine.py: listo exige orden_s == SOSTENER), asi que un general con distancia_m
chico ya "aguanta el fuego hasta corta distancia" sin agregar nada al motor.
Este experimento pone a prueba esa idea: con municion limitada y humo activos,
un distancia_m mas chico (mas disciplina) deberia gastar menos municion, generar
menos humo temprano y (por la caida de precision con la distancia que ya existe
en el motor) pegar con mas efecto cuando abre fuego.

Uso: python experimentos/disciplina_de_fuego.py
"""
import sys

import numpy as np

sys.path.insert(0, ".")
from engine import Batalla, Config
from generals import avanzar_y_disparar, quieto

SEMILLAS = (0, 1, 2, 3, 4)
B_POR_SEMILLA = 200


def correr(distancia_apertura_m):
    cfg = Config(
        moral_activa=True, moral_umbral_media=0.4, moral_colapso_umbral=0.15,
        municion_activa=True, municion_inicial=15, humo_activo=True,
    )
    ganador, bajas0, bajas1, municion_final = [], [], [], []
    general = avanzar_y_disparar(distancia_apertura_m)
    for seed in SEMILLAS:
        b = Batalla(cfg, B=B_POR_SEMILLA, seed=seed).correr(general, quieto)
        bajas = ((b.salud < 2) | b.huyendo).sum(-1)
        n0 = np.array(cfg.n_soldados, dtype=np.float64)
        pct = 100 * bajas / n0[None, :]
        ganador.append(b.ganador)
        bajas0.append(pct[:, 0])
        bajas1.append(pct[:, 1])
        municion_final.append(b.municion[:, 0].mean(-1))  # promedio de balas que le quedan a cada soldado del bando 0
    return (np.concatenate(ganador), np.concatenate(bajas0), np.concatenate(bajas1),
            np.concatenate(municion_final))


for distancia in (150.0, 100.0, 70.0, 40.0):
    g, b0, b1, mun = correr(distancia)
    n = len(g)
    tasa = (g == 0).mean()
    print(f"distancia_apertura={distancia:.0f} m ({n} batallas)")
    print(f"  gana el atacante: {tasa:.1%} +- {np.sqrt(tasa*(1-tasa)/n):.1%}")
    print(f"  bajas atacante: {b0.mean():.1f}% +- {b0.std()/np.sqrt(n):.1f}%  |  "
          f"bajas defensor: {b1.mean():.1f}% +- {b1.std()/np.sqrt(n):.1f}%")
    print(f"  municion promedio restante (de 15): {mun.mean():.1f} +- {mun.std()/np.sqrt(n):.1f}")
