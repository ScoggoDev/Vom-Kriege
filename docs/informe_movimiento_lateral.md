# Informe: movimiento lateral real

## Qué se construyó

`x_unidad` pasó de ser geometría fija por batalla `(2,U)` a tener estado por
batalla `(B,2,U)`. Dos órdenes nuevas, `IZQUIERDA` y `DERECHA`, desplazan la
unidad perpendicular a su eje de avance (afectadas por el freno de pantano y
clima, no por la pendiente del terreno, que es un perfil solo en y). Mientras
se mueve lateralmente, la unidad no dispara (misma regla que `AVANZAR`). El
movimiento lateral no lo bloquea el río (tiene que poder maniobrarse a lo largo
de la orilla para buscar un vado sin que eso cuente como "cruzar").

Esto resuelve la limitación que ya marcaba `docs/informe_fase2b_rio.md`: antes,
estar alineado con un vado era una coincidencia fija de la formación inicial,
no algo hacia lo que un general pudiera maniobrar. `generals.py` ahora tiene
`cruzar_rio_y_disparar`, que mueve cada unidad lateralmente hacia el vado más
cercano antes de avanzar.

Todo lo que grababa el visor (`experimentos/exportar_replay.py`,
`visor/index.html`) se actualizó para grabar `x_unidad` por tick en vez de una
vez por batalla, porque ahora puede cambiar.

## Verificación

67 tests, todos pasando (62 anteriores + 5 nuevos de movimiento lateral):
regresión exacta sin usar las órdenes nuevas (ningún general de reglas
existente las usa), `DERECHA`/`IZQUIERDA` mueven la unidad en la dirección
correcta y por la distancia correcta, moverse lateralmente no dispara, y una
unidad no alineada con ningún vado puede desplazarse hasta alinearse y
entonces cruzar (antes imposible sin reposicionar manualmente la unidad a
mano, como hacían los tests de fase 2b).

## Un hallazgo contraintuitivo

`experimentos/rio_con_movimiento_lateral.py` compara el escenario de
`rio_cuello_de_botella.py` (2 de 4 unidades alineadas con un vado) contra el
mismo escenario pero con `cruzar_rio_y_disparar`, que permite que las 4
unidades terminen cruzando.

| | alineación fija (2/4 cruzan) | maniobra lateral (4/4 cruzan) |
|---|---|---|
| Gana el atacante | 1,0% ± 0,3% | 0,0% ± 0,0% |
| Bajas defensor | 0,5% ± 0,1% | 0,0% ± 0,0% |

**Comprometer a todo el ejército a cruzar no mejora el resultado, lo empeora
levemente** (dentro del margen de error, pero consistente en duración y bajas
del defensor también). La explicación, revisando el mecanismo: `moral_colapso_umbral`
se mide sobre todo el ejército, no por unidad, y la penalidad de moral por
cruzar bajo fuego (`rio_penalidad_moral`) se suma por soldado que está
cruzando. Con 2 unidades varadas (que nunca cruzan, nunca sufren esa
penalidad), el ejército completo acumula fracción de bajas/huida más despacio
que cuando las 4 unidades están expuestas a la penalidad de cruce al mismo
tiempo. Las unidades varadas funcionan, sin que nadie lo haya diseñado así,
como una especie de "reserva de moral" que no arriesga nada.

No es un bug: la duración de la batalla es prácticamente igual en los dos
casos (34-36 ticks), así que no es un problema de tiempo agotado, es el
mecanismo de colapso global interactuando con una penalidad que ahora se paga
más veces. Tampoco es una conclusión general sobre "el movimiento lateral no
sirve": la capacidad en sí está verificada y funciona (ver tests); lo que pasa
es que, con esta calibración puntual de moral y esta penalidad de cruce, comprometer
más fuerza a una maniobra riesgosa no es gratis. Es exactamente el tipo de
interacción entre mecánicas que CLAUDE.md pide marcar de frente en vez de
asumir que "más opciones para el general" siempre es mejor.

## Sabido vs. supuesto

Nada nuevo con fuente en este cambio: es infraestructura (una capacidad de
movimiento que antes no existía), no un parámetro inventado nuevo. El hallazgo
de arriba es una propiedad emergente de parámetros ya marcados como inventados
en fases anteriores (`rio_penalidad_moral` de fase 2b, `moral_colapso_umbral`
de fase 1), no algo que se pueda atribuir a una fuente histórica.
