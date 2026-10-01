"""
Observacion por unidad para el general que aprende (fase 5).

Reduccion de alcance deliberada respecto de docs/diseno.md seccion 4:
- No hay "mapa de terreno como imagen": el motor no tiene una grilla 2D real,
  solo un perfil parametrico (cresta en y, franjas de cobertura/rio/pantano; ver
  docs/informe_fase2a_terreno.md). Por eso se usan features escalares resumidas
  por unidad en vez de una red convolucional.
- No hay ordenes de "cargar" (mele), "retirarse" (deliberada, distinta de la
  huida por moral) ni "cambiar formacion": esas mecanicas no existen todavia
  (ver seccion "Formaciones y mele" de docs/diseno.md, sin fase asignada). El
  general que aprende elige entre las mismas dos ordenes que ya usan los
  generales de reglas, AVANZAR o SOSTENER, una por unidad.

Las ultimas dos features (distancia a la zona clave y si la unidad esta
adentro) se agregaron junto con terreno_clave_activo, para que el general
pueda aprender a disputar el terreno en vez de evitar el combate por completo
(ver el hallazgo de docs/informe_fase5_general.md: sin esto, entrenar contra un
rival quieto producia una politica que nunca avanzaba).
"""
import numpy as np

N_FEATURES = 11


def observar(bat, lado):
    """Devuelve (B, U) x N_FEATURES: una fila de features por unidad del bando `lado`."""
    cfg = bat.cfg
    enemigo = 1 - lado
    U = cfg.unidades
    B = bat.B

    vivo = bat.salud > 0
    vivos_u = bat.vivos_por_unidad(vivo)                       # (B,2,U)
    tam = np.maximum(bat.tam_u[None].astype(np.float32), 1)    # (1,2,U)
    fuerza_u = (vivos_u / tam)[:, lado]                        # (B,U) fraccion viva de cada unidad propia

    dist_norm = bat.distancia_unidades_al_enemigo()[:, lado] / max(cfg.distancia_inicial_m, 1.0)
    dist_norm = np.clip(dist_norm, 0, 3)

    fuerza_total_propia = vivos_u[:, lado].sum(-1, keepdims=True) / max(cfg.n_soldados[lado], 1)
    fuerza_total_enemiga = vivos_u[:, enemigo].sum(-1, keepdims=True) / max(cfg.n_soldados[enemigo], 1)
    ventaja_numerica = np.broadcast_to(fuerza_total_propia - fuerza_total_enemiga, (B, U)).astype(np.float32)

    if cfg.moral_activa:
        perdido = (bat.salud == 0) | bat.huyendo
        perdidos_u = bat.vivos_por_unidad(perdido)
        moral_u = 1 - (perdidos_u / tam)[:, lado]
    else:
        moral_u = np.ones((B, U), np.float32)

    if cfg.municion_activa:
        municion_u = (bat.suma_por_unidad(bat.municion.astype(np.float32)) / tam)[:, lado] / max(cfg.municion_inicial, 1)
    else:
        municion_u = np.ones((B, U), np.float32)

    if cfg.cansancio_activo:
        cansancio_u = (bat.suma_por_unidad(bat.cansancio) / tam)[:, lado]
    else:
        cansancio_u = np.zeros((B, U), np.float32)

    if cfg.terreno_activo:
        altura_u = bat.altura(bat.y_unidad[:, lado]) / max(cfg.terreno_cresta_alto_m, 1e-6)
        en_cobertura_u = bat.en_cobertura(bat.x_unidad[:, lado], bat.y_unidad[:, lado]).astype(np.float32)
    else:
        altura_u = np.zeros((B, U), np.float32)
        en_cobertura_u = np.zeros((B, U), np.float32)

    tick_norm = np.full((B, U), bat.t / max(cfg.max_ticks, 1), np.float32)

    if cfg.terreno_clave_activo:
        x_u = bat.x_unidad[:, lado]
        y_u = bat.y_unidad[:, lado]
        dx_clave = x_u - cfg.terreno_clave_x_centro_m
        dy_clave = y_u - cfg.terreno_clave_y_centro_m
        dist_clave_norm = np.clip(np.hypot(dx_clave, dy_clave) / max(cfg.distancia_inicial_m, 1.0), 0, 3)
        en_zona_clave_u = bat.en_zona_clave(x_u, y_u).astype(np.float32)
    else:
        dist_clave_norm = np.zeros((B, U), np.float32)
        en_zona_clave_u = np.zeros((B, U), np.float32)

    return np.stack([dist_norm, fuerza_u, ventaja_numerica, moral_u, municion_u,
                      cansancio_u, altura_u, en_cobertura_u, tick_norm,
                      dist_clave_norm, en_zona_clave_u], axis=-1).astype(np.float32)
