"""Generales de reglas. Devuelven una orden por unidad: array (B, U)."""
import numpy as np
from engine import SOSTENER, AVANZAR, IZQUIERDA, DERECHA


def quieto(bat, lado):
    """Nunca se mueve: sostiene y dispara a discreción."""
    return np.full((bat.B, bat.cfg.unidades), SOSTENER)


def avanzar_y_disparar(distancia_m=70.0):
    """Doctrina mínima: cada unidad avanza hasta tener al enemigo a distancia_m, frena y hace fuego."""
    def general(bat, lado):
        d = bat.distancia_unidades_al_enemigo()[:, lado]
        return np.where(d > distancia_m, AVANZAR, SOSTENER)
    return general


def cruzar_rio_y_disparar(distancia_m=70.0, margen_alineacion_m=2.0):
    """Como avanzar_y_disparar, pero si cfg.rio_activo y la unidad no esta
    alineada con ningun vado, primero se mueve lateralmente hacia el vado mas
    cercano (mirando cfg.rio_vado_x_centros) antes de avanzar. Demuestra el
    movimiento lateral agregado para que los vados sean algo hacia lo que un
    general pueda maniobrar, no solo una coincidencia fija de la formacion
    inicial (ver docs/informe_fase2b_rio.md, limitacion ya anotada ahi)."""
    def general(bat, lado):
        cfg = bat.cfg
        x_u = bat.x_unidad[:, lado]  # (B,U)
        if cfg.rio_activo and cfg.rio_vado_x_centros:
            vados = np.array(cfg.rio_vado_x_centros)
            idx_cercano = np.abs(x_u[..., None] - vados[None, None, :]).argmin(-1)
            vado_cercano = vados[idx_cercano]
            alineada = np.abs(x_u - vado_cercano) < margen_alineacion_m
            mover_der = ~alineada & (vado_cercano > x_u)
            mover_izq = ~alineada & (vado_cercano < x_u)
        else:
            mover_der = np.zeros_like(x_u, dtype=bool)
            mover_izq = np.zeros_like(x_u, dtype=bool)
        d = bat.distancia_unidades_al_enemigo()[:, lado]
        base = np.where(d > distancia_m, AVANZAR, SOSTENER)
        return np.where(mover_der, DERECHA, np.where(mover_izq, IZQUIERDA, base))
    return general
