"""
Exporta una repeticion de batalla a JSON para mirarla en visor/index.html.
Cada corrida (semilla distinta, generales distintos) se exporta a su propio archivo;
el visor es generico y abre cualquiera de ellos.

Uso: python experimentos/exportar_replay.py [salida.json] [semilla]
"""
import json
import sys

sys.path.insert(0, ".")
from engine import Batalla, Config
from generals import avanzar_y_disparar

salida = sys.argv[1] if len(sys.argv) > 1 else "visor/replay.json"
semilla = int(sys.argv[2]) if len(sys.argv) > 2 else 0

cfg = Config(moral_activa=True, moral_umbral_media=0.4)
general = avanzar_y_disparar(cfg.alcance_max_m * 0.6)
b = Batalla(cfg, B=1, seed=semilla, grabar=True).correr(general, general)

soldados = [
    {"lado": lado, "idx": int(i), "unidad": int(b.unidad[lado, i]),
     "dx": float(b.dx[lado, i]), "fila": float(b.fila[lado, i])}
    for lado in (0, 1) for i in range(b.N) if b.existe[lado, i]
]
ticks = [
    {"salud": salud.tolist(), "y_unidad": y_unidad.tolist(), "x_unidad": x_unidad.tolist(),
     "dispara": dispara.tolist(), "impacto": impacto.tolist(), "huida_y": huida_y.tolist()}
    for salud, y_unidad, dispara, impacto, huida_y, x_unidad in b.cuadros
]
datos = {
    "meta": {
        "dir": b.dir.tolist(),
        "ganador": int(b.ganador[0]),
        "duracion_ticks": int(b.duracion[0]),
        "tick_s": 5,
    },
    "soldados": soldados,
    "ticks": ticks,
}
with open(salida, "w", encoding="utf-8") as f:
    json.dump(datos, f)
print(f"exportado {len(ticks)} ticks, {len(soldados)} soldados -> {salida} "
      f"(ganador={datos['meta']['ganador']})")
