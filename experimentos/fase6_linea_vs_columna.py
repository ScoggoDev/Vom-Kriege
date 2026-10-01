"""
Pregunta de investigacion 3 (docs/diseno.md seccion 7), antes marcada como no
respondible por falta de formaciones. Ahora que existen linea y columna (ver
docs/informe_formaciones_mele.md), compara tres doctrinas de ataque contra un
defensor en linea quieto:

  - siempre_linea: avanzar_y_disparar, nunca cambia de formacion (la linea es
    la formacion por defecto).
  - columna_y_despliega: marcha en columna (mas rapido) hasta 100 m del
    enemigo, se despliega en linea, tirotea en linea. Doctrina historica
    estandar.
  - siempre_columna: nunca se despliega, tirotea en columna. Doctrina
    deliberadamente mala, puesta como control: si esto no sale claramente peor
    que las otras dos, hay que sospechar de la implementacion de columna.

Uso: python experimentos/fase6_linea_vs_columna.py
"""
import sys

import numpy as np

sys.path.insert(0, ".")
from engine import Batalla, Config
from generals import avanzar_y_disparar, columna_y_despliega, quieto, siempre_columna_y_dispara

SEMILLAS = (0, 1, 2, 3, 4)
B_POR_SEMILLA = 200

cfg = Config(moral_activa=True, moral_umbral_media=0.4, moral_colapso_umbral=0.15, formaciones_activo=True)


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


doctrinas = {
    "siempre_linea": avanzar_y_disparar(70.0),
    "columna_y_despliega": columna_y_despliega(100.0, 70.0),
    "siempre_columna (control, deberia ser peor)": siempre_columna_y_dispara(70.0),
}

for nombre, general in doctrinas.items():
    g, b0, b1 = correr(general)
    n = len(g)
    tasa = (g == 0).mean()
    print(f"{nombre}:")
    print(f"  gana el atacante: {tasa:.1%} +- {np.sqrt(tasa*(1-tasa)/n):.1%}")
    print(f"  bajas atacante: {b0.mean():.1f}% +- {b0.std()/np.sqrt(n):.1f}%  |  "
          f"bajas defensor: {b1.mean():.1f}% +- {b1.std()/np.sqrt(n):.1f}%")
