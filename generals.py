"""Generales de reglas. Devuelven una orden por unidad: array (B, U)."""
import numpy as np
from engine import SOSTENER, AVANZAR


def quieto(bat, lado):
    """Nunca se mueve: sostiene y dispara a discreción."""
    return np.full((bat.B, bat.cfg.unidades), SOSTENER)


def avanzar_y_disparar(distancia_m=70.0):
    """Doctrina mínima: cada unidad avanza hasta tener al enemigo a distancia_m, frena y hace fuego."""
    def general(bat, lado):
        d = bat.distancia_unidades_al_enemigo()[:, lado]
        return np.where(d > distancia_m, AVANZAR, SOSTENER)
    return general
