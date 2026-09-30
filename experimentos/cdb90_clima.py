"""
Objetivo de validacion para el efecto del clima: bajas de ganador y perdedor en
CDB90 1792-1815, separadas por seco (wx1=D) vs humedo (wx1=W). No distingue
lluvia de nieve (esa base no tiene esa categoria; wx3 in {H,C,T} da una pista de
temperatura, pero no es una etiqueta de "nevo", asi que se reporta aparte, nomas
para curiosidad, sin peso en la conclusion).

Uso: python experimentos/cdb90_clima.py [ruta a data/cdb90/data]
"""
import sys

import numpy as np
import pandas as pd

ruta = sys.argv[1] if len(sys.argv) > 1 else "data/cdb90/data"
b = pd.read_csv(f"{ruta}/battles.csv")
ap = pd.read_csv(f"{ruta}/active_periods.csv")
bel = pd.read_csv(f"{ruta}/belligerents.csv")
wx = pd.read_csv(f"{ruta}/weather.csv")
ap["anio"] = pd.to_datetime(ap.start_time_min.astype(str).str[:10], errors="coerce").dt.year
anios = ap.groupby("isqno")["anio"].min()
rango = anios[(anios >= 1792) & (anios <= 1815)].index


def resumen(ids, etiqueta):
    x = bel[bel.isqno.isin(ids)].copy()
    for c in ("intst", "cas"):
        x[c] = pd.to_numeric(x[c], errors="coerce")
    x = x.merge(b[["isqno", "wina"]], on="isqno")
    x = x[x.wina.isin([1, -1]) & (x.intst > 0) & x.cas.notna()]
    if len(x) == 0:
        print(f"{etiqueta}: sin datos utilizables")
        return
    x["gano"] = np.where(x.attacker == 1, x.wina == 1, x.wina == -1)
    x["pct"] = 100 * x.cas / x.intst
    g = x.groupby("gano")["pct"]
    n_bat = x.isqno.nunique()
    if True in g.groups and False in g.groups:
        print(f"{etiqueta}: {n_bat} batallas | ganador mediana {g.median()[True]:.0f}% | "
              f"perdedor mediana {g.median()[False]:.0f}%")
    else:
        print(f"{etiqueta}: {n_bat} batallas | falta ganador o perdedor con datos")


secas = wx[(wx.isqno.isin(rango)) & (wx.wx1 == "D")].isqno
humedas = wx[(wx.isqno.isin(rango)) & (wx.wx1 == "W")].isqno
humedas_frias = wx[(wx.isqno.isin(rango)) & (wx.wx1 == "W") & (wx.wx3 == "C")].isqno

resumen(secas, "secas (wx1=D)          ")
resumen(humedas, "humedas (wx1=W)         ")
resumen(humedas_frias, "humedas y frias (wx1=W,wx3=C), proxy crudo de nieve")
