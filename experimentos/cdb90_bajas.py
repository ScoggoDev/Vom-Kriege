"""
Objetivo de validación: bajas típicas de ganadores y perdedores en batallas reales 1792-1815.
Datos: CDB90 (U.S. Army Concepts Analysis Agency), versión limpia en github.com/jrnold/CDB90
  git clone --depth 1 https://github.com/jrnold/CDB90.git data/cdb90
Uso: python experimentos/cdb90_bajas.py [ruta a data/cdb90/data]
Cuidados: muestra chica, la base tiene errores de codificación conocidos, datos agregados por ejército.
"""
import sys, pandas as pd, numpy as np

ruta = sys.argv[1] if len(sys.argv) > 1 else "data/cdb90/data"
b = pd.read_csv(f"{ruta}/battles.csv")
ap = pd.read_csv(f"{ruta}/active_periods.csv")
bel = pd.read_csv(f"{ruta}/belligerents.csv")
ap["anio"] = pd.to_datetime(ap.start_time_min.astype(str).str[:10], errors="coerce").dt.year
anios = ap.groupby("isqno")["anio"].min()


def resumen(ids, etiqueta):
    x = bel[bel.isqno.isin(ids)].copy()
    for c in ("intst", "cas"):
        x[c] = pd.to_numeric(x[c], errors="coerce")
    x = x.merge(b[["isqno", "wina"]], on="isqno")
    x = x[x.wina.isin([1, -1]) & (x.intst > 0) & x.cas.notna()]   # wina: 1 gana atacante, -1 pierde, 0 empate
    x["gano"] = np.where(x.attacker == 1, x.wina == 1, x.wina == -1)
    x["pct"] = 100 * x.cas / x.intst
    g = x.groupby("gano")["pct"]
    print(f"{etiqueta}: {x.isqno.nunique()} batallas | bajas ganador mediana {g.median()[True]:.0f}% "
          f"(p25-p75 {g.quantile(.25)[True]:.0f}-{g.quantile(.75)[True]:.0f}) | perdedor mediana {g.median()[False]:.0f}% "
          f"(p25-p75 {g.quantile(.25)[False]:.0f}-{g.quantile(.75)[False]:.0f})")


resumen(anios[(anios >= 1792) & (anios <= 1815)].index, "1792-1815")
resumen(anios.index, "todas    ")
