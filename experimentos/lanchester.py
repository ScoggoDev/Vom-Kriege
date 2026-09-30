"""
Validación: tiroteo estático a 60 m, probabilidad de impacto constante, un impacto = fuera de combate.
A tiene 100 hombres, B varía. Se compara la supervivencia de A contra tres predicciones:
  - Ley cuadrada (fuego apuntado):            A_f = sqrt(A0² - B0²)
  - Ley lineal clásica (área de tamaño fijo):  A_f = A0 - B0
  - Fuego al bulto con huecos (este motor):    A_f = A0 - B0²/A0
    (derivación: dB/dt = -k·A·B/B0 y dA/dt = -k·B·A/A0  =>  A0·(A0-A) = B0·(B0-B))
"""
import sys, numpy as np
sys.path.insert(0, ".")
from engine import Config, Batalla
from generals import quieto

modo = sys.argv[1]
A0 = 100
print(f"modo={modo}")
print(" B0 | gana A | A final sim | cuadrada | bulto c/huecos | lineal")
for B0 in (50, 60, 70, 80, 90):
    cfg = Config(n_soldados=(A0, B0), unidades=1, distancia_inicial_m=60, p_max=0.1, d50_m=1e9,
                 p_herida_grave=1.0, punteria_sd=0.0, modo_fuego=modo, max_ticks=4000)
    b = Batalla(cfg, B=150, seed=B0).correr(quieto, quieto)
    s = b.sobrevivientes()
    gana = b.ganador == 0
    print(f" {B0:3d} | {gana.mean():5.0%} | {s[gana,0].mean():6.1f} ± {s[gana,0].std()/np.sqrt(gana.sum()):.1f} |"
          f" {np.sqrt(A0**2-B0**2):6.1f}   | {A0-B0**2/A0:6.1f}         | {A0-B0:5.1f}")
