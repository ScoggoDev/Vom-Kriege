"""
Entrena al general con estrategias evolutivas y guarda los pesos resultantes.
Ver aprendizaje/es.py para el algoritmo y aprendizaje/observacion.py para la
reduccion de alcance de la observacion (sin mapa como imagen, sin ordenes de
mele/retirada/formacion).

Uso: python experimentos/entrenar_general.py [generaciones] [poblacion] [B]
"""
import sys
import time

import numpy as np

sys.path.insert(0, ".")
from engine import Config
from aprendizaje.es import entrenar

generaciones = int(sys.argv[1]) if len(sys.argv) > 1 else 40
poblacion = int(sys.argv[2]) if len(sys.argv) > 2 else 16
B = int(sys.argv[3]) if len(sys.argv) > 3 else 32

cfg = Config(moral_activa=True, moral_umbral_media=0.4, moral_colapso_umbral=0.15)

t0 = time.perf_counter()


def progreso(gen, f):
    t = time.perf_counter() - t0
    print(f"gen {gen:3d}/{generaciones} | fitness medio {f:+.3f} | {t:6.1f} s", flush=True)


politica = entrenar(cfg, generaciones=generaciones, poblacion=poblacion, B=B,
                     n_ocultas=16, semilla=0, callback=progreso)

np.savez("experimentos/general_entrenado.npz", theta=politica.parametros(), n_ocultas=politica.n_ocultas)
print(f"listo, {time.perf_counter()-t0:.1f} s totales. Pesos guardados en experimentos/general_entrenado.npz")
