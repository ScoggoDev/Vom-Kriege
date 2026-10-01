"""
Politica del general que aprende: una red chica (una capa oculta, sin
convoluciones, ver aprendizaje/observacion.py sobre por que no hay imagen de
mapa) aplicada de forma independiente a cada unidad, con los mismos pesos para
las cuatro. Devuelve AVANZAR si la salida es positiva, SOSTENER si no.

No usa autodiferenciacion porque se entrena con estrategias evolutivas
(aprendizaje/es.py), que solo necesitan evaluar la red hacia adelante.
"""
import numpy as np

from engine import AVANZAR, SOSTENER
from aprendizaje.observacion import N_FEATURES, observar


class PoliticaMLP:
    def __init__(self, n_ocultas=16, semilla=0):
        self.n_entradas = N_FEATURES
        self.n_ocultas = n_ocultas
        rng = np.random.default_rng(semilla)
        self.w1 = rng.normal(0, 0.5, (self.n_entradas, n_ocultas)).astype(np.float32)
        self.b1 = np.zeros(n_ocultas, np.float32)
        self.w2 = rng.normal(0, 0.5, n_ocultas).astype(np.float32)
        self.b2 = np.float32(0.0)

    @property
    def n_parametros(self):
        return self.w1.size + self.b1.size + self.w2.size + 1

    def parametros(self):
        return np.concatenate([self.w1.ravel(), self.b1.ravel(), self.w2.ravel(), [self.b2]]).astype(np.float32)

    def cargar_parametros(self, vector):
        i = 0
        n1 = self.w1.size
        self.w1 = vector[i:i + n1].reshape(self.w1.shape).astype(np.float32); i += n1
        n2 = self.b1.size
        self.b1 = vector[i:i + n2].astype(np.float32); i += n2
        n3 = self.w2.size
        self.w2 = vector[i:i + n3].astype(np.float32); i += n3
        self.b2 = np.float32(vector[i])

    def forward(self, obs):
        """obs: (..., N_FEATURES) -> (...) logit por unidad."""
        h = np.tanh(obs @ self.w1 + self.b1)
        return h @ self.w2 + self.b2


def general_aprendido(politica):
    """Adapta una PoliticaMLP a la interfaz de generals.py: bat, lado -> ordenes (B,U)."""
    def general(bat, lado):
        obs = observar(bat, lado)
        logits = politica.forward(obs)
        return np.where(logits > 0, AVANZAR, SOSTENER)
    return general
