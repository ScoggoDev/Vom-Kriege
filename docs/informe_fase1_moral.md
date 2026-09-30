# Informe fase 1: moral y fin de batalla por colapso

## Qué se construyó

Cada soldado sortea, al inicio de la batalla, un umbral de huida heterogéneo:
`Normal(moral_umbral_media, moral_umbral_sd)` recortado a [0.05, 0.95]. Cada tick,
si la fracción de su propia unidad ya perdida (fuera de combate o huyendo) supera
ese umbral, el soldado huye: deja de disparar, sale de la formación y se aleja a
`moral_velocidad_huida_m_tick`. La huida es irreversible dentro de la batalla. Un
bando colapsa (y pierde) cuando la fracción de su tropa fuera de combate o huyendo
supera `moral_colapso_umbral`. Todo detrás del flag `moral_activa` (default
`False`); con el flag apagado el motor es bit a bit igual a fase 0 (ver
`tests/test_moral.py::test_flag_apagado_no_activa_nada`).

## Verificación

18 tests, todos pasando (14 de fase 0 sin cambios + 4 nuevos): el flag apagado no
deja rastro ni consume el generador aleatorio, un soldado huyendo no dispara, el
colapso termina batallas que antes no terminaban, y el umbral responde en la
dirección esperada (más fácil huir, batalla más corta).

## Rendimiento

200 batallas, 100 por bando: 5,3 s con moral apagada (no comparable en forma
directa con la referencia de 3,7 s de `CLAUDE.md`, medida en otra máquina; con el
flag apagado el camino de código es idéntico, así que la diferencia es de
hardware, no de esta fase). Con moral activa y la calibración final, 200 batallas
tardan bastante menos porque terminan mucho antes por colapso en vez de agotar
los 360 ticks.

## Análisis de sensibilidad

Barrido completo en `experimentos/moral_sensibilidad.py` (36 combinaciones de
`moral_umbral_media` x `moral_colapso_umbral`, 3 semillas x 200 batallas cada una,
600 batallas por celda). Doctrina `avanzar_y_disparar` simétrica en ambos bandos,
100 vs 100, sin terreno. Métrica de bajas: heridos + fuera de combate + huyendo,
como fracción de la fuerza inicial (ver "Supuestos" más abajo).

`moral_colapso_umbral` es, por lejos, el parámetro que más mueve el resultado:
con 0.1 el perdedor queda entre 17-20% de bajas (por debajo del objetivo), con
0.15 entre 22-25% (muy cerca), con 0.2 entre 28-30% (por encima), y de ahí para
arriba se aleja rápido. `moral_umbral_media` tiene un efecto más chico y separa
sobre todo al ganador: valores bajos (0.2-0.3) dejan al ganador livianamente por
debajo del objetivo (7-9%), valores altos (0.65-0.8) lo empujan muy por encima
(20%+ incluso con colapso bajo).

Mejor combinación encontrada: **`moral_umbral_media=0.40`, `moral_colapso_umbral=0.15`**.

| | mediana simulada | p25-p75 simulado | objetivo CDB90 (1792-1815) | p25-p75 CDB90 |
|---|---|---|---|---|
| Ganador | 12% | 8-15% | 11% | 8-22% |
| Perdedor | 22% | 20-24% | 23% | 15-35% |

93% de las 600 batallas de esa celda terminaron con un ganador decidido (el resto
agotó el tiempo). Estos son los valores que quedaron como default en `Config`.

## Por qué las bajas superan al umbral de colapso

Con `moral_colapso_umbral=0.15`, uno esperaría que las bajas del perdedor ronden
15%, no 22%. La diferencia es que el colapso se dispara por fuera de combate +
huyendo, pero la métrica de "bajas" que se compara con CDB90 suma además a los
heridos que siguen en pie y disparando (con `p_herida_grave=0.5`, la mitad de los
impactos son heridas leves que no sacan a nadie de la formación). Son dos
definiciones distintas a propósito: una mide "¿la unidad todavía funciona como
unidad?" y la otra mide "¿cuánta gente terminó marcada como baja?". No es un bug,
pero conviene tenerlo presente si en el futuro se cambia `p_herida_grave` o se
agrega curación: hay que recalibrar.

## Qué es sabido y qué es supuesto

**Con fuente:**
- El objetivo de validación (11%/23% de mediana) sale de CDB90 1792-1815, 26
  batallas (`experimentos/cdb90_bajas.py`, dataset real clonado de
  github.com/jrnold/CDB90).
- El mecanismo de cascada por umbral heterogéneo es el modelo de Granovetter
  (1978) sobre comportamiento colectivo, aplicado acá como analogía estructural,
  no como un valor de umbral tomado de ese paper (Granovetter no da un número
  para "moral de infantería napoleónica").

**Inventado, sin fuente:**
- `moral_umbral_media` y `moral_colapso_umbral`: no calibrados contra un dato
  independiente, sino ajustados para que el agregado se parezca a CDB90. Con dos
  parámetros libres ajustados contra dos números objetivo (mediana ganador y
  mediana perdedor), esto es más una calibración que una validación real: el
  hecho de que exista una combinación que encaje no prueba que el mecanismo sea
  correcto, solo que es lo bastante flexible como para encajar. Donde sí hay una
  señal más fuerte es en que los p25-p75 simulados, que no se ajustaron a mano,
  caen dentro (aunque más angostos) de los p25-p75 reales.
- `moral_umbral_sd` (0.2) y `moral_velocidad_huida_m_tick` (6.0 m/tick) no se
  barrieron en este análisis, quedaron en su valor de diseño original. Si se
  demuestra sensibilidad fuerte a alguno de los dos, este informe queda
  incompleto y habría que rehacerlo.
- Que la fuga cuente como "baja" a los fines de la comparación con CDB90 es una
  suposición (ver `docs/diseno.md`: un soldado que abandona el campo no vuelve a
  la unidad, similar a un "missing" en el conteo histórico), no algo confirmado
  con los datos.
- La comparación en sí es cruda: un único enfrentamiento simétrico de infantería
  sola, sin terreno ni armas combinadas, con una sola doctrina de ambos lados,
  contra un promedio de 26 batallas reales de distintas doctrinas y terrenos
  dentro del mismo período. Que la mediana coincida no significa que el motor
  capture por qué esas batallas terminaron como terminaron.

## Qué falta antes de sacar conclusiones más fuertes

Esta calibración probablemente deja de servir en cuanto se agregue terreno
(fase 2), municion/cansancio (fase 4) o se cambie `p_herida_grave`, porque todos
esos cambios alteran cuánta gente queda herida-pero-en-pie o fuera de combate
antes de que la unidad colapse. Recalibrar en cada fase siguiente, no asumir que
estos valores quedan fijos para siempre.
