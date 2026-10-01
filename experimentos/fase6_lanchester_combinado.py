"""
Pregunta de investigacion 1 (docs/diseno.md seccion 7): ¿que ley de Lanchester
emerge cuando se suman moral, terreno y humo? ¿Se parece al exponente 1,5?

Mismo metodo que experimentos/lanchester.py (quieto vs quieto, A0=100, B0
variable, p_herida_grave=1.0 para que un impacto saque de combate, modo "area"
sin cerrar filas) pero con moral y humo activos. moral_colapso_umbral se deja
en 1.0 (nunca colapsa por eso) para que la batalla siga terminando por
aniquilacion, como en la verificacion original, y lo que cambia sea el combate
en si, no el criterio de corte.

Terreno se probo y se descarto para este experimento especifico: poner la
cresta en el punto medio entre dos lineas estaticas que se tirotean de frente
bloqueaba la linea de tiro en las DOS direcciones (nadie estaba lo bastante
alto como para ver por encima), asi que ninguna bala salia nunca y la batalla
terminaba siempre en empate por tiempo sin un solo impacto. No es un bug (dos
ejercitos a 60 m con una loma de 8 m justo en el medio realmente podrian no
verse), pero es un artefacto de esta geometria en particular, no algo que
aporte a responder la pregunta. Habria que separar las posiciones de la cresta
para evitar el bloqueo total antes de poder sumar terreno a este experimento
con sentido; queda pendiente, no se fuerzo un ajuste ad hoc solo para que diera
un numero.

Uso: python experimentos/fase6_lanchester_combinado.py
"""
import sys

import numpy as np

sys.path.insert(0, ".")
from engine import Batalla, Config
from generals import quieto

A0 = 100
DISTANCIA = 60.0


def predicho(n, A0, B0):
    if n == 1:
        return A0 - B0
    return (A0 ** n - B0 ** n) ** (1 / n)


print("modo=area, moral+humo activos (moral_colapso_umbral=1.0, no corta por colapso)")
print(" B0 | gana A | A final sim | lineal(n=1) | area(huecos) | n=1.5 | cuadrada(n=2)")
for B0 in (50, 60, 70, 80, 90):
    cfg = Config(
        n_soldados=(A0, B0), unidades=1, distancia_inicial_m=DISTANCIA, p_max=0.1, d50_m=1e9,
        p_herida_grave=1.0, punteria_sd=0.0, modo_fuego="area", max_ticks=4000,
        moral_activa=True, moral_umbral_media=0.4, moral_colapso_umbral=1.0,
        humo_activo=True,
    )
    b = Batalla(cfg, B=150, seed=B0).correr(quieto, quieto)
    s = b.sobrevivientes()
    gana = b.ganador == 0
    sim = s[gana, 0].mean()
    sem = s[gana, 0].std() / np.sqrt(gana.sum())
    print(f" {B0:3d} | {gana.mean():5.0%} | {sim:6.1f} ± {sem:.1f} |"
          f" {predicho(1,A0,B0):6.1f}    | {A0-B0**2/A0:6.1f}    |"
          f" {predicho(1.5,A0,B0):5.1f} | {predicho(2,A0,B0):6.1f}")
