"""
Pregunta de investigacion 7 (docs/diseno.md seccion 7, parcial): ¿cuantos
soldados vale una colina con cobertura? La parte de "¿que pasa si matan al
general?" no es respondible con este motor: el general es una funcion/politica
abstracta, no una entidad en el campo de batalla que se pueda alcanzar con un
disparo. Eso queda afuera, no es un resultado de este experimento.

Metodo: el mismo escenario de experimentos/terreno_ventaja.py (defensor quieto
sobre la cresta con cobertura, atacante avanzar_y_disparar), pero reduciendo la
cantidad de defensores hasta encontrar en que tamaño el desempeño (bajas del
defensor) se parece al defensor de tamaño completo (100) SIN terreno. Esa
cantidad de soldados que se puede restar sin perder el nivel de bajas es, bajo
este criterio, "lo que vale la loma".

Objetivo de referencia (de experimentos/terreno_ventaja.py, 1000 batallas):
  sin terreno, defensor=100: bajas defensor 6,5% +- 0,2%

Uso: python experimentos/fase6_cuanto_vale_la_loma.py
"""
import sys

import numpy as np

sys.path.insert(0, ".")
from engine import Batalla, Config
from generals import avanzar_y_disparar, quieto

SEMILLAS = (0, 1, 2, 3, 4)
B_POR_SEMILLA = 200
OBJETIVO_BAJAS_DEFENSOR = 6.5  # % , referencia sin terreno a tamaño completo


def correr(n_defensor):
    cfg = Config(
        n_soldados=(100, n_defensor), moral_activa=True, moral_umbral_media=0.4, moral_colapso_umbral=0.15,
        terreno_activo=True, terreno_cresta_y_m=250.0, terreno_cresta_alto_m=8.0, terreno_cresta_ancho_m=40.0,
        terreno_cobertura_y_centro_m=250.0, terreno_cobertura_y_ancho_m=40.0,
        terreno_cobertura_x_centro_m=0.0, terreno_cobertura_x_ancho_m=200.0, terreno_cobertura_reduccion=0.5,
    )
    ganador, bajas_defensor = [], []
    for seed in SEMILLAS:
        b = Batalla(cfg, B=B_POR_SEMILLA, seed=seed).correr(avanzar_y_disparar(), quieto)
        # OJO: cuando n_defensor < 100 = max(n_soldados), hay casillas de relleno en el
        # bando 1 que nunca existieron (salud=0 para siempre). Si no se recortan a
        # los primeros n_defensor indices, se cuentan como bajas fantasma (ver el fix
        # de moral en engine.py, mismo problema, pero este es un bug del script, no
        # del motor: el motor no sabe que "bajas" significa para un script externo).
        bajas = ((b.salud[:, 1, :n_defensor] < 2) | b.huyendo[:, 1, :n_defensor]).sum(-1)
        bajas_defensor.append(100 * bajas / n_defensor)
        ganador.append(b.ganador)
    return np.concatenate(ganador), np.concatenate(bajas_defensor)


print(f"objetivo (sin terreno, defensor=100): bajas defensor {OBJETIVO_BAJAS_DEFENSOR}%")
print(" defensores | gana defensor | bajas defensor")
for n_def in (100, 80, 60, 50, 40, 35, 30, 25, 20):
    g, bd = correr(n_def)
    n = len(g)
    tasa = (g == 1).mean()
    print(f"    {n_def:3d}     | {tasa:5.1%} ± {np.sqrt(tasa*(1-tasa)/n):.1%} | {bd.mean():5.1f}% ± {bd.std()/np.sqrt(n):.1f}%")
