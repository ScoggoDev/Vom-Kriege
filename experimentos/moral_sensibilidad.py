"""
Barrido de sensibilidad de los dos parametros de moral sin fuente
(moral_umbral_media, moral_colapso_umbral) contra el objetivo de validacion
de CDB90 1792-1815 (ver experimentos/cdb90_bajas.py):
    bajas ganador mediana 11% (p25-p75 8-22)
    bajas perdedor mediana 23% (p25-p75 15-35)

Esto es calibracion, no verificacion. Verificar que el mecanismo de huida
funciona es el trabajo de tests/test_moral.py; esto solo busca, dado que el
mecanismo ya funciona como se espera, que combinacion de los dos parametros
inventados hace que el agregado de bajas se parezca a datos reales.

La comparacion es cruda a proposito, no una prueba definitiva: es un choque
simetrico de infanteria sola, sin terreno ni armas combinadas, con una unica
doctrina (avanzar_y_disparar de ambos lados) contra un promedio de CDB90 que
mezcla epocas, doctrinas y tipos de batalla dentro de 1792-1815.

"Bajas" se define como herido + fuera de combate + huyendo (supuesto: se
cuenta la fuga como baja a los fines de esta comparacion, con el argumento
de docs/diseno.md de que un soldado que abandona el campo no vuelve a la
unidad, igual que un "missing" en el conteo historico; no hay forma de
confirmar esto con el motor actual).

Uso: python experimentos/moral_sensibilidad.py
Tarda unos 4-5 minutos (36 combinaciones x 3 semillas x 200 batallas).
"""
import sys

import numpy as np

sys.path.insert(0, ".")
from engine import Batalla, Config
from generals import avanzar_y_disparar

# Objetivo (experimentos/cdb90_bajas.py, 1792-1815, 26 batallas)
OBJ_GANADOR = 11.0
OBJ_PERDEDOR = 23.0

SEMILLAS = (0, 1, 2)
B_POR_SEMILLA = 200
MIN_DECIDIDAS = 20  # por debajo de esto, no reporto mediana/percentiles

UMBRAL_MEDIA = (0.2, 0.3, 0.4, 0.5, 0.65, 0.8)
COLAPSO_UMBRAL = (0.1, 0.15, 0.2, 0.3, 0.4, 0.5)


def bajas_pct(b):
    bajas = ((b.salud < 2) | b.huyendo).sum(-1)  # (B,2)
    n0 = np.array(b.cfg.n_soldados, dtype=np.float64)
    return 100 * bajas / n0[None, :]


def correr_combo(umbral_media, colapso_umbral):
    ganador_pct, perdedor_pct, n_total, n_decididas = [], [], 0, 0
    for seed in SEMILLAS:
        cfg = Config(moral_activa=True, moral_umbral_media=umbral_media,
                     moral_colapso_umbral=colapso_umbral)
        b = Batalla(cfg, B=B_POR_SEMILLA, seed=seed).correr(avanzar_y_disparar(), avanzar_y_disparar())
        pct = bajas_pct(b)
        decidida = b.ganador != -1
        gan = b.ganador[decidida]
        idx = np.arange(len(gan))
        ganador_pct.append(pct[decidida][idx, gan])
        perdedor_pct.append(pct[decidida][idx, 1 - gan])
        n_total += B_POR_SEMILLA
        n_decididas += int(decidida.sum())
    return (np.concatenate(ganador_pct), np.concatenate(perdedor_pct),
            n_decididas, n_total)


filas = []
for um in UMBRAL_MEDIA:
    for cu in COLAPSO_UMBRAL:
        g, p, n_decididas, n_total = correr_combo(um, cu)
        frac_decididas = n_decididas / n_total
        if n_decididas < MIN_DECIDIDAS:
            filas.append(dict(um=um, cu=cu, frac=frac_decididas, score=np.inf))
            continue
        gm, gp25, gp75 = np.median(g), np.percentile(g, 25), np.percentile(g, 75)
        pm, pp25, pp75 = np.median(p), np.percentile(p, 25), np.percentile(p, 75)
        score = abs(gm - OBJ_GANADOR) + abs(pm - OBJ_PERDEDOR)
        filas.append(dict(um=um, cu=cu, frac=frac_decididas, gm=gm, gp25=gp25, gp75=gp75,
                           pm=pm, pp25=pp25, pp75=pp75, score=score))

print(f"objetivo CDB90 1792-1815: ganador mediana {OBJ_GANADOR:.0f}% | perdedor mediana {OBJ_PERDEDOR:.0f}%")
print(f"cada celda: {len(SEMILLAS)} semillas x {B_POR_SEMILLA} batallas = {len(SEMILLAS) * B_POR_SEMILLA} batallas\n")
print(" umbral | colapso | % decid | ganador med (p25-p75) | perdedor med (p25-p75) | score")
for f in sorted(filas, key=lambda f: f["score"]):
    if f["score"] == np.inf:
        print(f" {f['um']:.2f}   | {f['cu']:.2f}    | {f['frac']:6.0%} | pocas batallas decididas, no se reporta")
        continue
    print(f" {f['um']:.2f}   | {f['cu']:.2f}    | {f['frac']:6.0%} | "
          f"{f['gm']:5.1f}% ({f['gp25']:.0f}-{f['gp75']:.0f})      | "
          f"{f['pm']:5.1f}% ({f['pp25']:.0f}-{f['pp75']:.0f})      | {f['score']:.1f}")
