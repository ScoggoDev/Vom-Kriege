"""
Pregunta de investigacion 6 (docs/diseno.md seccion 7): ¿cerrar filas cambia la
ley de Lanchester que emerge en modo "area"?

Hipotesis del diseño: cerrar filas mantiene constante la densidad de la
formacion (sin huecos) y deberia empujar el modo area hacia la ley cuadrada.
Mecanicamente esto ya se verifico por construccion (cierra_filas reusa la
logica de "apuntado", ver el commit que lo agrego), asi que este experimento es
la confirmacion empirica, con el mismo metodo que experimentos/lanchester.py.

Uso: python experimentos/fase6_cierra_filas.py
"""
import sys

import numpy as np

sys.path.insert(0, ".")
from engine import Batalla, Config
from generals import quieto

A0 = 100
print("modo=area, cierra_filas=True")
print(" B0 | gana A | A final sim | cuadrada | area con huecos (sin cerrar)")
for B0 in (50, 60, 70, 80, 90):
    cfg = Config(n_soldados=(A0, B0), unidades=1, distancia_inicial_m=60, p_max=0.1, d50_m=1e9,
                 p_herida_grave=1.0, punteria_sd=0.0, modo_fuego="area", cierra_filas=True, max_ticks=4000)
    b = Batalla(cfg, B=150, seed=B0).correr(quieto, quieto)
    s = b.sobrevivientes()
    gana = b.ganador == 0
    print(f" {B0:3d} | {gana.mean():5.0%} | {s[gana,0].mean():6.1f} ± {s[gana,0].std()/np.sqrt(gana.sum()):.1f} |"
          f" {np.sqrt(A0**2-B0**2):6.1f}   | {A0-B0**2/A0:6.1f}")
