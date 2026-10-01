"""
Evalua al general entrenado (experimentos/entrenar_general.py) contra cada
general de reglas del pool de entrenamiento, con muchas batallas y semillas
(a diferencia del fitness interno del entrenamiento, que usa pocas batallas por
evaluacion para que ES sea rapido). Compara ademas contra un general de reglas
razonable (avanzar_y_disparar(70), la distancia por defecto) jugando el mismo
rol, para ver si lo aprendido mejora sobre una doctrina fija sensata o no.

Esto es el control que pide docs/diseno.md seccion 4 contra el efecto estufa
caliente: un aprendiz con estimaciones ruidosas puede probar algo una vez, le
sale mal por mala suerte, y no volver a intentarlo nunca, sin que eso signifique
que la politica aprendida sea buena en general.

Uso: python experimentos/evaluar_general.py
"""
import sys

import numpy as np

sys.path.insert(0, ".")
from engine import Batalla, Config
from generals import avanzar_y_disparar, quieto
from aprendizaje.politica import PoliticaMLP, general_aprendido

datos = np.load("experimentos/general_entrenado.npz")
politica = PoliticaMLP(n_ocultas=int(datos["n_ocultas"]), semilla=0)
politica.cargar_parametros(datos["theta"])
general_entrenado = general_aprendido(politica)
general_referencia = avanzar_y_disparar(70.0)

cfg = Config(moral_activa=True, moral_umbral_media=0.4, moral_colapso_umbral=0.15)
OPONENTES = {"quieto": quieto, "avanzar_40": avanzar_y_disparar(40.0),
             "avanzar_70": avanzar_y_disparar(70.0), "avanzar_100": avanzar_y_disparar(100.0)}
SEMILLAS = (0, 1, 2, 3, 4)
B_POR_SEMILLA = 100


def evaluar(general_propio, nombre_oponente, general_oponente):
    ganador, bajas_propio, bajas_oponente = [], [], []
    for seed in SEMILLAS:
        b = Batalla(cfg, B=B_POR_SEMILLA, seed=seed).correr(general_propio, general_oponente)
        bajas = ((b.salud < 2) | b.huyendo).sum(-1).astype(np.float64)
        n0 = np.array(cfg.n_soldados, dtype=np.float64)
        pct = bajas / n0[None, :]
        ganador.append(b.ganador)
        bajas_propio.append(pct[:, 0])
        bajas_oponente.append(pct[:, 1])
    g = np.concatenate(ganador)
    bp = np.concatenate(bajas_propio)
    bo = np.concatenate(bajas_oponente)
    n = len(g)
    tasa = (g == 0).mean()
    return tasa, np.sqrt(tasa * (1 - tasa) / n), bp.mean() * 100, bo.mean() * 100


print(f"{'oponente':<12} | {'gana entrenado':<18} | {'gana referencia (dist=70)':<26}")
for nombre, oponente in OPONENTES.items():
    tasa_e, sem_e, bp_e, bo_e = evaluar(general_entrenado, nombre, oponente)
    tasa_r, sem_r, bp_r, bo_r = evaluar(general_referencia, nombre, oponente)
    print(f"{nombre:<12} | {tasa_e:5.1%} +- {sem_e:4.1%}      | {tasa_r:5.1%} +- {sem_r:4.1%}")
    print(f"             | bajas propias {bp_e:4.1f}%, rival {bo_e:4.1f}% | "
          f"bajas propias {bp_r:4.1f}%, rival {bo_r:4.1f}%")
