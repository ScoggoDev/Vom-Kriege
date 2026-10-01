"""
Pregunta de investigacion 2 (docs/diseno.md seccion 7): ¿que ley de Lanchester
ajusta mejor a las batallas reales de CDB90? docs/diseno.md ya menciona que
Helmbold y Hartley hicieron este ejercicio; esto es una version propia y mucho
mas simple, no una replica de su metodo.

Metodo (simplificado, con su propio supuesto fuerte: ver abajo): para cada
batalla con ganador claro, A0/Af son la fuerza inicial y final (sobrevivientes)
del ganador, B0/Bf las del perdedor. Si la ley de potencia n sostuviera con la
MISMA efectividad de ambos lados, deberia valer A0^n - Af^n = B0^n - Bf^n. Se
prueba una grilla de n y se mide, para cada uno, el error cuadratico medio
relativo entre ambos lados de esa igualdad. El n con menor error es "el que
mejor ajusta" bajo este criterio.

Supuesto fuerte y señalado como tal: asume efectividad identica entre bandos,
lo cual CDB90 mezcla doscientos años, armas y dos bandos de un mismo choque que
casi nunca son igual de efectivos. Esto NO es el metodo de Helmbold/Hartley
(que ajustan por regresion con un coeficiente de efectividad libre por banda);
es una aproximacion mucho mas cruda, util para una primera mirada, no una
replica del trabajo citado en docs/diseno.md.

Uso: python experimentos/cdb90_lanchester.py [ruta a data/cdb90/data]
"""
import sys

import numpy as np
import pandas as pd

ruta = sys.argv[1] if len(sys.argv) > 1 else "data/cdb90/data"
b = pd.read_csv(f"{ruta}/battles.csv")
ap = pd.read_csv(f"{ruta}/active_periods.csv")
bel = pd.read_csv(f"{ruta}/belligerents.csv")
ap["anio"] = pd.to_datetime(ap.start_time_min.astype(str).str[:10], errors="coerce").dt.year
anios = ap.groupby("isqno")["anio"].min()

bel = bel.merge(b[["isqno", "wina"]], on="isqno")
bel["intst"] = pd.to_numeric(bel.intst, errors="coerce")
bel["cas"] = pd.to_numeric(bel.cas, errors="coerce")
bel = bel[bel.wina.isin([1, -1]) & (bel.intst > 0) & bel.cas.notna() & (bel.cas >= 0)]

atacantes = bel[bel.attacker == 1].set_index("isqno")
defensores = bel[bel.attacker == 0].set_index("isqno")
comun = atacantes.index.intersection(defensores.index)


def filas(rango_anios, etiqueta):
    filtrado = [i for i in comun if i in anios.index and rango_anios[0] <= anios[i] <= rango_anios[1]]
    datos = []
    for isqno in filtrado:
        a0, a_cas, wina = atacantes.loc[isqno, ["intst", "cas", "wina"]]
        d0, d_cas = defensores.loc[isqno, ["intst", "cas"]]
        af, df = a0 - a_cas, d0 - d_cas
        if af < 0 or df < 0:
            continue
        if wina == 1:
            A0, Af, B0, Bf = a0, af, d0, df
        else:
            A0, Af, B0, Bf = d0, df, a0, af
        if A0 <= Af or A0 <= 0 or B0 <= 0:  # el ganador tiene que haber sufrido alguna baja para que esto tenga sentido
            continue
        datos.append((A0, Af, B0, Bf))
    if len(datos) < 5:
        print(f"{etiqueta}: solo {len(datos)} batallas utilizables, insuficiente")
        return
    datos = np.array(datos)
    A0, Af, B0, Bf = datos.T
    print(f"{etiqueta}: {len(datos)} batallas utilizables")
    print("  n   | error relativo medio |A0^n-Af^n vs B0^n-Bf^n|")
    mejor = None
    for n in (0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0):
        kA = A0 ** n - Af ** n
        kB = B0 ** n - Bf ** n
        escala = (A0 ** n + B0 ** n) / 2
        error = np.abs(kA - kB) / escala
        error_medio = error.mean()
        if mejor is None or error_medio < mejor[1]:
            mejor = (n, error_medio)
        print(f"  {n:.1f} | {error_medio:.3f}")
    print(f"  -> mejor ajuste: n={mejor[0]}")


filas((1792, 1815), "1792-1815")
filas((1600, 1973), "todas las epocas")
