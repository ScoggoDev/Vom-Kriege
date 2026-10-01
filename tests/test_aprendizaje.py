"""
Tests del general que aprende (fase 5, ver docs/informe_fase5_general.md).
No prueban que el entrenamiento converja (eso es un resultado empírico, no algo
verificable con un assert), solo que el mecanismo (observacion, politica, ES)
hace lo que se espera: formas correctas, sin NaN/infinitos, y que corre.
"""
import numpy as np

from engine import AVANZAR, Batalla, Config, SOSTENER
from generals import avanzar_y_disparar, quieto
from aprendizaje.observacion import N_FEATURES, observar
from aprendizaje.politica import PoliticaMLP, general_aprendido
from aprendizaje.es import entrenar, fitness


def test_observacion_forma_y_finitud():
    cfg = Config(moral_activa=True, municion_activa=True, cansancio_activo=True, terreno_activo=True)
    b = Batalla(cfg, B=5, seed=0)
    for lado in (0, 1):
        obs = observar(b, lado)
        assert obs.shape == (5, cfg.unidades, N_FEATURES)
        assert np.isfinite(obs).all()


def test_observacion_con_todo_apagado_no_rompe():
    b = Batalla(Config(), B=3, seed=0)
    obs = observar(b, 0)
    assert obs.shape == (3, Config().unidades, N_FEATURES)
    assert np.isfinite(obs).all()


def test_politica_forward_y_roundtrip_de_parametros():
    politica = PoliticaMLP(n_ocultas=8, semilla=1)
    obs = np.random.default_rng(0).normal(size=(4, 3, N_FEATURES)).astype(np.float32)
    salida = politica.forward(obs)
    assert salida.shape == (4, 3)
    assert np.isfinite(salida).all()

    theta = politica.parametros()
    assert theta.shape == (politica.n_parametros,)
    politica2 = PoliticaMLP(n_ocultas=8, semilla=99)
    politica2.cargar_parametros(theta)
    np.testing.assert_allclose(politica2.forward(obs), salida)


def test_general_aprendido_corre_una_batalla():
    politica = PoliticaMLP(n_ocultas=8, semilla=2)
    general = general_aprendido(politica)
    cfg = Config(max_ticks=50)
    b = Batalla(cfg, B=4, seed=0).correr(general, quieto)
    assert b.terminada.all()


def test_fitness_es_finito():
    cfg = Config(max_ticks=50)
    politica = PoliticaMLP(n_ocultas=8, semilla=3)
    f = fitness(cfg, politica, quieto, lado_entrenado=0, B=8, seed=0)
    assert np.isfinite(f)


def test_entrenar_corre_sin_crashear():
    cfg = Config(max_ticks=40, moral_activa=True, moral_umbral_media=0.4, moral_colapso_umbral=0.15)
    politica = entrenar(cfg, generaciones=2, poblacion=2, B=4, n_ocultas=6, semilla=0)
    assert isinstance(politica, PoliticaMLP)
    general = general_aprendido(politica)
    b = Batalla(cfg, B=4, seed=1).correr(general, quieto)
    assert b.terminada.all()
