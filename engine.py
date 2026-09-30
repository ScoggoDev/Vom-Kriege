"""
Motor vectorizado de batallas napoleónicas de línea.
Capa 1: salud y puntería. Capa 2: moral y fin de batalla por colapso (detrás
del flag Config.moral_activa). Sin munición limitada, sin cansancio, sin terreno.

Todos los arrays tienen forma (B, 2, N): batallas en paralelo, bando, soldado.
La grilla es de 1 metro por celda. Un tick son 5 segundos.
El bando 0 avanza hacia +y, el bando 1 hacia -y.
"""
from dataclasses import dataclass
import numpy as np

# Órdenes que el general da a cada unidad
SOSTENER, AVANZAR = 0, 1   # sostener = quedarse y hacer fuego a discreción


@dataclass
class Config:
    n_soldados: tuple = (100, 100)
    unidades: int = 4
    filas: int = 2                   # profundidad de la línea
    frente_m: float = 1.0            # espacio por hombre en el frente
    hueco_unidades_m: float = 8.0
    distancia_inicial_m: float = 250.0
    marcha_m_tick: float = 4.5       # ~0,9 m/s, paso ordinario
    recarga_ticks: int = 4           # ~20-25 s por disparo
    modo_fuego: str = "area"         # "area": al bulto de la formación; "apuntado": a un enemigo vivo
    p_max: float = 0.5               # prob. de impacto a quemarropa con puntería 1
    d50_m: float = 30.0              # a esta distancia la prob. cae a la mitad
    alcance_max_m: float = 150.0
    punteria_media: float = 1.0
    punteria_sd: float = 0.15
    p_herida_grave: float = 0.5      # 1.0 = un impacto deja fuera de combate
    penal_herido_punteria: float = 0.6
    penal_herido_recarga: int = 2
    max_ticks: int = 360             # 30 minutos
    # --- moral (fase 1) ---
    moral_activa: bool = False                 # inventado: flag maestro, apaga toda la mecanica
    moral_umbral_media: float = 0.4            # inventado: calibrado contra CDB90, ver informe de fase 1
    moral_umbral_sd: float = 0.2               # inventado: heterogeneidad del umbral (Granovetter 1978), sin calibrar
    moral_velocidad_huida_m_tick: float = 6.0  # inventado: mas rapido que la marcha ordinaria (4.5), sin calibrar
    moral_colapso_umbral: float = 0.15         # inventado: calibrado contra CDB90, ver informe de fase 1


class Batalla:
    def __init__(self, cfg: Config, B: int, seed: int = 0, grabar: bool = False):
        self.cfg, self.B = cfg, B
        self.rng = np.random.default_rng(seed)
        U, F = cfg.unidades, cfg.filas
        N = max(cfg.n_soldados)
        self.N = N
        self.dir = np.array([1.0, -1.0])

        # Geometría fija de cada bando: unidad, fila y columna de cada soldado
        self.existe = np.zeros((2, N), bool)
        self.unidad = np.zeros((2, N), int)
        self.dx = np.zeros((2, N), np.float32)
        self.fila = np.zeros((2, N), np.float32)
        self.x_unidad = np.zeros((2, U), np.float32)
        self.ini_u = np.zeros((2, U), int)
        self.tam_u = np.zeros((2, U), int)
        for s in (0, 1):
            n = cfg.n_soldados[s]
            por_u = -(-n // U)
            cols = -(-por_u // F)
            ancho = cols * cfg.frente_m
            self.x_unidad[s] = (np.arange(U) - (U - 1) / 2) * (ancho + cfg.hueco_unidades_m)
            i = np.arange(n)
            u, k = i // por_u, i % por_u
            self.existe[s, :n] = True
            self.unidad[s, :n] = u
            self.dx[s, :n] = (k // F - (cols - 1) / 2) * cfg.frente_m
            self.fila[s, :n] = k % F
            self.ini_u[s] = np.arange(U) * por_u
            self.tam_u[s] = np.clip(n - np.arange(U) * por_u, 0, por_u)

        # Estado dinámico
        self.y_unidad = np.zeros((B, 2, U), np.float32)
        self.y_unidad[:, 1] = cfg.distancia_inicial_m
        self.salud = np.where(self.existe, 2, 0)[None].repeat(B, 0).astype(np.int8)  # 2 sano, 1 herido, 0 fuera
        self.punteria = np.clip(self.rng.normal(cfg.punteria_media, cfg.punteria_sd, (B, 2, N)), 0.2, 2).astype(np.float32)
        self.recarga = np.zeros((B, 2, N), np.int16)   # todos arrancan con el arma cargada
        self.huyendo = np.zeros((B, 2, N), bool)
        self.huida_y = np.zeros((B, 2, N), np.float32)
        if cfg.moral_activa:
            self.umbral_huida = np.clip(
                self.rng.normal(cfg.moral_umbral_media, cfg.moral_umbral_sd, (B, 2, N)), 0.05, 0.95
            ).astype(np.float32)
        else:
            self.umbral_huida = None  # no se sortea: con el flag apagado, ni se usa ni se consume el rng
        self.t = 0
        self.terminada = np.zeros(B, bool)
        self.ganador = np.full(B, -1)
        self.duracion = np.zeros(B, int)
        self.grabar = grabar
        self.cuadros = []

    def vivos_por_unidad(self, vivo):
        U = self.cfg.unidades
        idx = (np.arange(self.B)[:, None, None] * 2 + np.arange(2)[None, :, None]) * U + self.unidad[None]
        return np.bincount(idx[vivo], minlength=self.B * 2 * U).reshape(self.B, 2, U)

    # --- geometría ---
    def posiciones(self):
        x = self.x_unidad[:, self.unidad][[0, 1], [0, 1]] + self.dx          # (2,N)
        x = np.broadcast_to(x, (self.B, 2, self.N))
        yu = np.take_along_axis(self.y_unidad, np.broadcast_to(self.unidad, (self.B, 2, self.N)), 2)
        y = yu - self.dir[None, :, None] * self.fila[None] + self.huida_y
        return x, y

    def distancia_unidades_al_enemigo(self):
        """Distancia del frente de cada unidad al enemigo vivo más cercano: (B,2,U)."""
        x, y = self.posiciones()
        vivo = self.salud > 0
        xu = np.broadcast_to(self.x_unidad, (self.B, 2, self.cfg.unidades))
        xe, ye, ve = x[:, [1, 0]], y[:, [1, 0]], vivo[:, [1, 0]]
        d = np.hypot(xu[..., None] - xe[:, :, None, :], self.y_unidad[..., None] - ye[:, :, None, :])
        d = np.where(ve[:, :, None, :], d, np.inf)
        return d.min(-1)

    # --- un tick ---
    def paso(self, ordenes):
        cfg, B, N = self.cfg, self.B, self.N
        activa = ~self.terminada[:, None, None]
        vivo = self.salud > 0
        herido = self.salud == 1
        orden_s = np.take_along_axis(ordenes, np.broadcast_to(self.unidad, (B, 2, N)), 2)

        # Fuego simultáneo: todos disparan con el estado del inicio del tick.
        # Cada unidad le tira a la unidad enemiga viva más cercana; cada soldado elige blanco dentro de ella.
        x, y = self.posiciones()
        vivos_u = self.vivos_por_unidad(vivo)                       # (B,2,U)
        U = cfg.unidades
        xu = self.x_unidad
        du = np.hypot(xu[None, :, :, None] - xu[None, [1, 0], None, :],
                      self.y_unidad[..., None] - self.y_unidad[:, [1, 0], None, :])
        du = np.where(vivos_u[:, [1, 0], None, :] > 0, du, np.inf)
        u_blanco = du.argmin(-1)                                     # (B,2,U)
        tiene = np.isfinite(du.min(-1))
        tu = np.take_along_axis(u_blanco, np.broadcast_to(self.unidad, (B, 2, N)), 2)
        tiene_s = np.take_along_axis(tiene, np.broadcast_to(self.unidad, (B, 2, N)), 2)
        ini_e = np.take_along_axis(np.broadcast_to(self.ini_u[[1, 0]], (B, 2, U)), tu, 2)
        r = self.rng.random((B, 2, N))
        if cfg.modo_fuego == "apuntado":
            # orden aleatorio con los vivos primero dentro de cada unidad enemiga
            clave = self.unidad[None] * 4 + (~vivo) * 2 + self.rng.random((B, 2, N))
            orden = np.argsort(clave, -1)[:, [1, 0]]
            n_e = np.take_along_axis(vivos_u[:, [1, 0]], tu, 2)
            blanco = np.take_along_axis(orden, np.minimum(ini_e + (r * n_e).astype(int), N - 1), 2)
            tiene_s &= n_e > 0
        else:  # al bulto: puede tocarle un hueco donde antes había un hombre
            n_e = np.take_along_axis(np.broadcast_to(self.tam_u[[1, 0]], (B, 2, U)), tu, 2)
            blanco = np.minimum(ini_e + (r * n_e).astype(int), N - 1)
        d_blanco = np.hypot(x - np.take_along_axis(x[:, [1, 0]], blanco, 2),
                            y - np.take_along_axis(y[:, [1, 0]], blanco, 2))
        listo = activa & vivo & ~self.huyendo & (self.recarga == 0) & (orden_s == SOSTENER)
        dispara = listo & tiene_s & (d_blanco <= cfg.alcance_max_m)
        p = self.punteria * np.where(herido, cfg.penal_herido_punteria, 1.0) * cfg.p_max / (1 + (d_blanco / cfg.d50_m) ** 2)
        blanco_vivo = np.take_along_axis(vivo[:, [1, 0]], blanco, 2)
        impacto = dispara & blanco_vivo & (self.rng.random((B, 2, N)) < p)
        grave = self.rng.random((B, 2, N)) < cfg.p_herida_grave
        dano_hecho = np.where(grave, 2, 1)
        idx = (np.arange(B)[:, None, None] * 2 + np.array([1, 0])[None, :, None]) * N + blanco
        dano = np.bincount(idx[impacto], weights=dano_hecho[impacto], minlength=B * 2 * N).reshape(B, 2, N)
        self.salud = np.clip(self.salud - dano, 0, 2).astype(np.int8)

        # Moral: cascada de huida tipo Granovetter dentro de la propia unidad (ver docs/diseno.md).
        # Umbral heterogeneo por soldado, sorteado una vez al inicio. Huida irreversible en la batalla.
        if cfg.moral_activa:
            perdido = (self.salud == 0) | self.huyendo
            perdidos_u = self.vivos_por_unidad(perdido)
            frac_perdida_u = perdidos_u / np.maximum(self.tam_u[None], 1)
            frac_perdida_s = np.take_along_axis(frac_perdida_u, np.broadcast_to(self.unidad, (B, 2, N)), 2)
            vivo_actual = self.salud > 0
            nueva_huida = activa & vivo_actual & ~self.huyendo & (frac_perdida_s > self.umbral_huida)
            self.huyendo |= nueva_huida
            self.huida_y -= np.where(self.huyendo & activa,
                                      self.dir[None, :, None] * cfg.moral_velocidad_huida_m_tick, 0.0)

        # Recarga
        extra = (self.rng.random((B, 2, N)) < 0.5) + herido * cfg.penal_herido_recarga
        self.recarga = np.where(dispara, cfg.recarga_ticks + extra, np.maximum(self.recarga - 1, 0)).astype(np.int16)

        # Movimiento de unidades que avanzan (y que conservan alguien vivo)
        mueve = (ordenes == AVANZAR) & (vivos_u > 0) & activa[..., 0][..., None]
        self.y_unidad += mueve * self.dir[None, :, None] * cfg.marcha_m_tick

        if self.grabar:
            self.cuadros.append((self.salud[0].copy(), self.y_unidad[0].copy(), dispara[0].copy(),
                                  impacto[0].copy(), self.huida_y[0].copy()))

        # Fin de batalla: aniquilacion total, colapso de moral (si esta activa), o tiempo agotado
        self.t += 1
        vivos = (self.salud > 0).sum(-1)
        if cfg.moral_activa:
            aptos = ((self.salud > 0) & ~self.huyendo).sum(-1)
            n0 = np.array(cfg.n_soldados, dtype=np.float32)
            colapsado = (1 - aptos / n0) >= cfg.moral_colapso_umbral
        else:
            colapsado = np.zeros((B, 2), bool)
        derrotado = (vivos == 0) | colapsado
        fin = ~self.terminada & (derrotado.any(-1) | (self.t >= cfg.max_ticks))
        g = np.where(derrotado[:, 1] & ~derrotado[:, 0], 0, np.where(derrotado[:, 0] & ~derrotado[:, 1], 1, -1))
        self.ganador = np.where(fin, g, self.ganador)
        self.duracion = np.where(fin, self.t, self.duracion)
        self.terminada |= fin

    def correr(self, general_0, general_1):
        while not self.terminada.all():
            o = np.stack([general_0(self, 0), general_1(self, 1)], 1)
            self.paso(o)
        return self

    def sobrevivientes(self):
        return (self.salud > 0).sum(-1)   # (B,2)
