"""
Entrena al general por rondas de fictitious play: cada ronda juega contra una
copia congelada de la politica de la ronda anterior, ademas del pool de reglas
(para no perder diversidad de rivales, ver aprendizaje/es.py). Guarda cada
ronda por separado para poder comparar progreso.

Uso: python experimentos/entrenar_self_play.py [rondas] [generaciones_por_ronda] [poblacion] [B]
"""
import sys
import time

import numpy as np

sys.path.insert(0, ".")
from engine import Config
from aprendizaje.es import entrenar_self_play

rondas = int(sys.argv[1]) if len(sys.argv) > 1 else 3
generaciones_por_ronda = int(sys.argv[2]) if len(sys.argv) > 2 else 15
poblacion = int(sys.argv[3]) if len(sys.argv) > 3 else 12
B = int(sys.argv[4]) if len(sys.argv) > 4 else 24

cfg = Config(moral_activa=True, moral_umbral_media=0.4, moral_colapso_umbral=0.15,
             terreno_clave_activo=True, terreno_clave_x_centro_m=0.0, terreno_clave_y_centro_m=125.0,
             terreno_clave_x_ancho_m=40.0, terreno_clave_y_ancho_m=40.0)

t0 = time.perf_counter()


def progreso(ronda, gen, f):
    t = time.perf_counter() - t0
    print(f"ronda {ronda}/{rondas-1} gen {gen:3d}/{generaciones_por_ronda} | "
          f"fitness medio {f:+.3f} | {t:6.1f} s", flush=True)


politicas = entrenar_self_play(cfg, rondas=rondas, generaciones_por_ronda=generaciones_por_ronda,
                                poblacion=poblacion, B=B, n_ocultas=16, semilla=0, callback=progreso)

for i, pol in enumerate(politicas):
    np.savez(f"experimentos/general_self_play_ronda{i}.npz", theta=pol.parametros(), n_ocultas=pol.n_ocultas)

print(f"listo, {time.perf_counter()-t0:.1f} s totales. "
      f"{len(politicas)} rondas guardadas en experimentos/general_self_play_ronda*.npz")
