# Informe fase 2b: río, vados y pantano

## Qué se construyó

- **Río**: una franja en `y` (`rio_y_centro_m` ± `rio_ancho_m`/2) intransitable,
  salvo en uno o más vados definidos por su posición en `x`
  (`rio_vado_x_centros`, ancho `rio_vado_ancho_m`). Cruzar bajo fuego suma una
  penalidad a la fracción de bajas percibida por la moral (`rio_penalidad_moral`,
  solo si `moral_activa`).
- **Pantano**: una zona rectangular en x,y donde la marcha se multiplica por
  `pantano_factor_marcha` (< 1).
- Ambos detrás de sus flags (`rio_activo`, `pantano_activo`, default `False`).

**Simplificación deliberada e importante**: el motor todavía no tiene movimiento
lateral. Cada unidad tiene una posición en `x` fija para toda la batalla (definida
por la formación, nunca elegida por el general). Así que un "vado" no es un lugar
hacia el que una unidad pueda maniobrar: una unidad está alineada con un vado o no
lo está, desde el arranque y para siempre. Esto alcanza para probar la dinámica
de cuello de botella (algunas unidades cruzan, otras quedan varadas en la orilla
sin poder acercarse), pero no representa a un general decidiendo por dónde cruzar.
Agregar eso es un cambio de arquitectura más grande (habría que sumar una orden de
movimiento lateral y hacer que la posición en x de la unidad deje de ser fija),
que no se justificaba para esta fase. Si en fase 5 el general que aprende necesita
elegir puntos de cruce, ahí sí habría que revisar esto.

## Verificación

30 tests, todos pasando (25 anteriores sin cambios + 5 nuevos): regresión bit a
bit con los flags apagados (parámetros extremos incluidos), una unidad no
alineada con ningún vado queda completamente bloqueada al llegar al río, una
unidad alineada cruza a marcha normal, el pantano frena la marcha en la
proporción exacta esperada, y cruzar bajo fuego aumenta la fracción de soldados
que huyen (comparación con la misma semilla, así que el conjunto de quienes huyen
cruzando el río tiene que incluir, no solo empatar, al conjunto de quienes huyen
lejos del río).

## Rendimiento

200 batallas, 100 por bando: 3,51 s sin nada activo, 3,38 s con río, 3,40 s con
pantano. Sin overhead medible.

## Coherencia interna

`experimentos/rio_cuello_de_botella.py`: atacante con 4 unidades, solo 2
alineadas con un vado, contra un defensor quieto del otro lado del río. 1000
batallas por condición.

| | sin río | con río |
|---|---|---|
| Gana el atacante | 10,0% ± 0,9% | 1,0% ± 0,3% |
| Bajas del atacante | 22,0% ± 0,1% | 23,5% ± 0,2% |
| Bajas del defensor | 6,5% ± 0,2% | 0,5% ± 0,1% |

Igual que en fase 2a, el punto de partida sin terreno ya favorece mucho al
defensor quieto (asimetría quieto-vs-avanza, ver informe de fase 2a). Con el río,
la mitad de la fuerza atacante queda varada fuera de alcance y las otras dos
unidades cruzan solas contra las cuatro del defensor: el resultado (el defensor
casi no sufre bajas, el atacante prácticamente nunca gana) es la consecuencia
lógica y esperable de atacar con la mitad de la fuerza, no una sorpresa. Sirve
como chequeo de que el bloqueo funciona como se espera, no como una validación
de que el motor "descubrió" algo sobre ríos reales.

## Sabido vs. supuesto

**Con fuente:** que los cruces de río bajo fuego eran particularmente costosos y
que los vados/puentes se volvían cuellos de botella es un patrón histórico
documentado (por ejemplo, el cruce del Berézina en 1812, aunque ese caso es una
retirada en invierno, no un choque simétrico como el que modela este motor).

**Inventado, sin calibrar:** los cinco parámetros numéricos
(`rio_ancho_m`, `rio_vado_ancho_m`, `rio_penalidad_moral`, `pantano_factor_marcha`,
y las posiciones concretas de río/vados/pantano) no tienen fuente ni fueron
ajustados contra ningún dato. Tampoco hay, como en fase 2a, un número de CDB90
contra el cual calibrar cuánto exactamente debería costar cruzar un río.

**Limitación de alcance, no hallazgo:** la ausencia de movimiento lateral hace
que el "cuello de botella" sea una propiedad fija de la formación inicial, no
una decisión táctica del general. El resultado de arriba dice "si la mitad de tu
fuerza no puede cruzar, te va mal", que es casi una tautología del diseño, no un
descubrimiento sobre ríos.
