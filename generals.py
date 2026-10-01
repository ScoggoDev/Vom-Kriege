"""Generales de reglas. Devuelven una orden por unidad: array (B, U)."""
import numpy as np
from engine import SOSTENER, AVANZAR, IZQUIERDA, DERECHA, COLUMNA, FORMAR_COLUMNA, FORMAR_LINEA


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


def columna_y_despliega(distancia_despliegue_m=100.0, distancia_combate_m=70.0):
    """Marcha en columna (mas rapido) mientras el enemigo esta lejos, se despliega
    en linea a distancia_despliegue_m, y de ahi en mas es igual a avanzar_y_disparar.
    Doctrina historica estandar: columna para marchar, linea para tirotear."""
    def general(bat, lado):
        d = bat.distancia_unidades_al_enemigo()[:, lado]
        en_columna = bat.formacion[:, lado] == COLUMNA
        quiere_columna = d > distancia_despliegue_m
        cambia_a_columna = quiere_columna & ~en_columna
        cambia_a_linea = ~quiere_columna & en_columna
        avanzar_o_sostener = np.where(d > distancia_combate_m, AVANZAR, SOSTENER)
        return np.where(cambia_a_columna, FORMAR_COLUMNA,
                         np.where(cambia_a_linea, FORMAR_LINEA, avanzar_o_sostener))
    return general


def siempre_columna_y_dispara(distancia_m=70.0):
    """Doctrina deliberadamente mala, para comparar: se pone en columna al
    arrancar y nunca se despliega en linea, ni para tirotear."""
    def general(bat, lado):
        en_columna = bat.formacion[:, lado] == COLUMNA
        d = bat.distancia_unidades_al_enemigo()[:, lado]
        avanzar_o_sostener = np.where(d > distancia_m, AVANZAR, SOSTENER)
        return np.where(~en_columna, FORMAR_COLUMNA, avanzar_o_sostener)
    return general
