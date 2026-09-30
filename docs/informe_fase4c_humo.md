# Informe fase 4c: humo y disciplina de fuego

## Qué se construyó

**Humo**: cada unidad acumula una nube de humo (`Config.humo_activo`, default
`False`) que sube con cada disparo de esa unidad y se disipa una fracción por
tick. La puntería de un disparo se reduce según el humo de la unidad que dispara
más el humo de la unidad blanco (así que el humo afecta a ambos bandos, como
pide `docs/diseno.md`). Se usa el humo acumulado *hasta el tick anterior* para
calcular la probabilidad de impacto de este tick, y recién después se suma el
humo que generan los disparos de este mismo tick (causalidad: el humo de ahora
mismo no puede haber afectado a la puntería de ahora mismo).

**Disciplina de fuego**: no se construyó ninguna mecánica nueva. Ya está
implícita en el motor: mientras la orden de una unidad es `AVANZAR`, nadie
dispara (`listo` exige `orden_s == SOSTENER`, ver `engine.py`). Un general que
usa `avanzar_y_disparar(distancia_m)` con `distancia_m` chico ya "aguanta el
fuego hasta distancia corta" sin agregar nada: gasta menos munición, genera
menos humo temprano, y dispara con más efecto cuando abre fuego, porque la
caída de precisión con la distancia ya existe desde fase 0. Agregar un parámetro
nuevo de "disciplina" hubiera sido duplicar algo que el motor ya expresa.

## Verificación

47 tests, todos pasando (43 anteriores + 4 nuevos): regresión bit a bit con el
flag apagado y parámetros extremos, disparar genera humo, el humo se disipa
solo (sin disparos nuevos) en la fracción exacta esperada, y más humo previo no
puede dar más impactos que menos humo (comparación pareada, misma semilla).

## Coherencia interna: disciplina de fuego no siempre ayuda

`experimentos/disciplina_de_fuego.py`: atacante con `avanzar_y_disparar` contra
defensor quieto, con munición limitada (15 tiros) y humo activos, variando la
distancia a la que el atacante abre fuego. 1000 batallas por condición.

| distancia de apertura | gana atacante | bajas atacante | bajas defensor | munición restante (de 15) |
|---|---|---|---|---|
| 150 m | 28,1% ± 1,4% | 10,8% ± 0,2% | 10,6% ± 0,2% | 4,2 ± 0,1 |
| 100 m | 35,6% ± 1,5% | 16,6% ± 0,2% | 11,3% ± 0,3% | 9,1 ± 0,1 |
| 70 m | 26,0% ± 1,4% | 18,8% ± 0,2% | 9,2% ± 0,3% | 12,3 ± 0,1 |
| 40 m | 12,1% ± 1,0% | 21,2% ± 0,1% | 6,1% ± 0,2% | 14,2 ± 0,0 |

Esto contradice la hipótesis ingenua de "más disciplina, siempre mejor", y es un
resultado real a marcar de frente (CLAUDE.md: cualquier resultado raro es
sospechoso hasta demostrar lo contrario, así que se revisó el mecanismo antes de
escribir esto). La munición ahorrada sube monótonamente con la disciplina, como
se esperaba: eso confirma que el mecanismo de disciplina (via `distancia_m`)
funciona. Pero la tasa de victoria del atacante **no** es monótona: pega un pico
en 100 m y cae fuerte en 40 m, y sus propias bajas suben cuanto más aguanta.

La explicación, revisando el motor: mientras la orden es `AVANZAR`, la unidad no
dispara **nada**, ni siquiera al alcance máximo. Contra un defensor que ya está
quieto y en rango desde temprano, aguantar más significa caminar más tiempo bajo
fuego enemigo sin devolverlo. El costo de ese tramo de marcha silenciosa termina
pesando más que la ganancia de precisión al abrir fuego de cerca. Esto puede ser
una limitación real de este escenario particular, no necesariamente un hallazgo
generalizable: en un choque donde ambos bandos avanzan (ninguno tiene la ventaja
de quedarse quieto disparando desde el arranque), o donde el terreno/humo oculta
el avance, la disciplina de fuego podría pagar distinto. No se probó ese caso
por acotar el alcance de esta fase; queda anotado para la pregunta de
investigación 4 de fase 6 ("¿aguantar el fuego o disparar temprano?").

## Rendimiento

La primera medición aislada dio 6,26 s sin humo contra 12,91 s con humo, más
del doble, lo que CLAUDE.md pide reportar explícitamente. Antes de aceptar eso
como una regresión real, se perfiló con `cProfile` (mismo overhead de perfilado
para ambos casos): 6,32 s sin humo contra 8,46 s con humo, un 34% más, no el
doble. Repitiendo la medición simple varias veces seguidas, el propio caso base
(sin humo) varió entre 7,15 s y 11,51 s corrida a corrida, sin tocar nada. La
conclusión es que la máquina venía de más de una hora de cómputo numpy
continuo (todas las fases y experimentos de esta sesión) y las mediciones
aisladas de una sola corrida no son confiables en ese estado: el ruido de la
máquina (throttling térmico, otros procesos) es del mismo orden que el efecto
que se quería medir. El overhead real de humo, con `cProfile` como vara
consistente, es de un ~30-35%, en línea con el resto de las mecánicas de esta
fase. Ninguna corrida cambió la duración en ticks (siempre 360, el máximo), así
que la diferencia es puramente costo por tick, no más ticks.

Lección para próximas fases: medir rendimiento en una máquina "fría" o con
`cProfile` como comparación pareada, no con una sola corrida de reloj de pared
después de una sesión larga.

## Sabido vs. supuesto

**Con fuente:** que el humo de la pólvora negra reducía la visibilidad en el
campo de batalla, a veces al punto de no ver al enemigo, es un hecho histórico
bien documentado de la guerra de la época de mosquete de ánima lisa.

**Inventado, sin calibrar:** los tres parámetros numéricos (`humo_por_disparo`,
`humo_disipacion`, `humo_penal_punteria`) no tienen fuente ni fueron ajustados
contra ningún dato.

**Decisión de diseño con justificación, no un hallazgo de fuente:** no construir
una mecánica separada de "disciplina de fuego" porque ya emerge de la
combinación de reglas existentes. Es una decisión de `docs/diseno.md` bien
razonada (menos código, menos parámetros inventados), pero vale la pena
revisarla si en el futuro se necesita separar "disciplina" de "distancia de
apertura" como conceptos distintos (por ejemplo, si se agrega una orden de
"fuego a discreción con más alcance pero peor puntería").
