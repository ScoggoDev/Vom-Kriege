"""
Entrenamiento del general que aprende con estrategias evolutivas (variante
OpenAI-ES: muestreo espejado, ranking de fitness, sin backpropagation).

Se eligio ES antes que PPO porque, como anota docs/diseno.md seccion 4, solo
necesita el resultado final de la batalla (no que orden fue la buena) y se
paraleliza de forma trivial: cada evaluacion de una politica corre B batallas
en paralelo con el motor vectorizado que ya existe.

Oponentes: un pool de generales de reglas con doctrinas distintas (quieto y
avanzar_y_disparar a varias distancias), elegido al azar en cada generacion,
para que la politica no aprenda a explotar las maneras de uno solo (ver
docs/diseno.md seccion 4, riesgo de sobreajuste a un rival).
"""
import numpy as np

from engine import Batalla, Config
from generals import avanzar_y_disparar, quieto
from aprendizaje.politica import PoliticaMLP, general_aprendido

POOL_OPONENTES = [
    quieto,
    avanzar_y_disparar(40.0),
    avanzar_y_disparar(70.0),
    avanzar_y_disparar(100.0),
]


def fitness(cfg, politica, oponente, lado_entrenado, B, seed):
    """Promedio sobre B batallas de: diferencia de bajas (en fraccion) mas un
    bonus por resultado decisivo. Da señal de gradiente incluso cuando todavia
    no se gana ninguna batalla (algo que un fitness binario de solo ganar/perder
    no daria al principio del entrenamiento).

    Si hay terreno clave, se suma un termino continuo de cercania a la zona al
    terminar la batalla. Sin esto, con un rival que tampoco se mueve (quieto),
    "nadie controla la zona" es un empate tan bueno como cualquier otro para el
    fitness, y la politica aprende a no moverse nunca (hallazgo real de
    docs/informe_fase5_general.md): agregar terreno_clave_activo sin este
    termino no alcanza, porque el desempate de la batalla solo se nota si
    alguien efectivamente entra en la zona."""
    generales = [None, None]
    generales[lado_entrenado] = general_aprendido(politica)
    generales[1 - lado_entrenado] = oponente
    b = Batalla(cfg, B=B, seed=seed).correr(generales[0], generales[1])
    bajas = ((b.salud < 2) | b.huyendo).sum(-1).astype(np.float64)
    n0 = np.array(cfg.n_soldados, dtype=np.float64)
    pct = bajas / n0[None, :]
    propio, enemigo = lado_entrenado, 1 - lado_entrenado
    margen = pct[:, enemigo] - pct[:, propio]
    bonus = np.where(b.ganador == propio, 0.5, np.where(b.ganador == enemigo, -0.5, 0.0))
    if cfg.terreno_clave_activo:
        dx = b.x_unidad[:, propio] - cfg.terreno_clave_x_centro_m
        dy = b.y_unidad[:, propio] - cfg.terreno_clave_y_centro_m
        dist_zona = np.hypot(dx, dy).min(-1) / max(cfg.distancia_inicial_m, 1.0)
        bonus_zona = -1.5 * np.clip(dist_zona, 0, 1)
    else:
        bonus_zona = 0.0
    return float((margen + bonus + bonus_zona).mean())


def entrenar(cfg, generaciones=30, poblacion=12, sigma=0.1, lr=0.05, B=24,
             n_ocultas=16, semilla=0, callback=None):
    """Devuelve la PoliticaMLP entrenada. `callback(gen, fitness_medio)` opcional
    para loguear progreso."""
    rng = np.random.default_rng(semilla)
    politica = PoliticaMLP(n_ocultas=n_ocultas, semilla=semilla)
    theta = politica.parametros()
    n_params = politica.n_parametros

    for gen in range(generaciones):
        oponente = POOL_OPONENTES[gen % len(POOL_OPONENTES)]
        ruido = rng.normal(size=(poblacion, n_params)).astype(np.float32)
        fit_pos = np.zeros(poblacion)
        fit_neg = np.zeros(poblacion)
        for i in range(poblacion):
            politica.cargar_parametros(theta + sigma * ruido[i])
            fit_pos[i] = fitness(cfg, politica, oponente, 0, B, seed=gen * 1000 + i)
            politica.cargar_parametros(theta - sigma * ruido[i])
            fit_neg[i] = fitness(cfg, politica, oponente, 0, B, seed=gen * 1000 + i)

        todos = np.concatenate([fit_pos, fit_neg])
        escala = todos.std() + 1e-8
        ventaja = (fit_pos - fit_neg) / escala  # (poblacion,)
        gradiente = (ventaja[:, None] * ruido).mean(0)
        theta = theta + lr / sigma * gradiente

        if callback is not None:
            callback(gen, todos.mean())

    politica.cargar_parametros(theta)
    return politica
