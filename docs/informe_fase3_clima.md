# Informe fase 3: clima (lluvia y nieve)

## Qué se construyó

`Config.clima` con tres valores: `"seco"` (default, sin efecto), `"lluvia"` y
`"nieve"`. Efectos:

- **Lluvia**: probabilidad de fallo de encendido por pólvora mojada
  (`clima_lluvia_p_fallo`), barro que frena la marcha
  (`clima_lluvia_factor_marcha`), y menos visibilidad que reduce el alcance
  efectivo (`clima_lluvia_factor_alcance`).
- **Nieve**: sin fallo de encendido (la nieve no moja la pólvora del mismo
  modo), pero frena más la marcha que el barro (`clima_nieve_factor_marcha`) y
  reduce más el alcance por visibilidad (`clima_nieve_factor_alcance`).

No se modela el cansancio de moverse en barro o nieve (no existe hasta fase 4).

## Verificación

35 tests, todos pasando (30 anteriores + 5 nuevos): `clima="seco"` con
parámetros extremos en los otros dos climas da resultado bit a bit idéntico al
default; con fallo de encendido al 100% nadie recibe daño pese a condiciones que
garantizarían un impacto en seco; la lluvia reduce el alcance efectivo lo
suficiente como para que un disparo que conectaría en seco no llegue; nieve y
lluvia frenan la marcha, nieve más que lluvia; y la nieve no causa fallos de
encendido (el disparo conecta igual que en seco).

## Rendimiento

200 batallas, 100 por bando: 3,43 s seco, 3,14 s lluvia, 3,18 s nieve. Sin
overhead medible.

## Por qué no hay calibración contra CDB90

Se intentó: `experimentos/cdb90_clima.py` separa CDB90 1792-1815 por `wx1`
(seco/húmedo). El resultado es que hay 22 batallas secas pero **solo 4
húmedas**, y **0 húmedas-y-frías** (el proxy más cercano a "nieve" que permite
esa base, cruzando húmedo con `wx3=frío`). Con 4 batallas no hay manera honesta
de calibrar nada: cualquier ajuste sería ruido, no señal. Por eso esta fase no
tiene un barrido de calibración como el de moral (fase 1): sería fabricar
precisión donde no la hay.

Dato de referencia igual, con la advertencia de arriba: en esas 4 batallas
húmedas la mediana de bajas del ganador fue 15% y del perdedor 18% (contra 11%
y 29% en las 22 secas). La brecha entre ganador y perdedor se achica bajo
lluvia/humedad en esta muestra chiquita, lo cual sería compatible con la idea de
que el mal tiempo empareja a los bandos (menos alcance, más fallos, todos
peor), pero con n=4 esto no es una conclusión, apenas una anécdota numérica.

## Coherencia interna

`experimentos/clima_efecto.py`: mismo choque asimétrico de fase 2 (atacante
avanza y dispara, defensor quieto), comparando seco/lluvia/nieve. 1000 batallas
por condición.

| | seco | lluvia | nieve |
|---|---|---|---|
| Gana el atacante | 10,0% ± 0,9% | 10,0% ± 0,9% | 8,0% ± 0,9% |
| Bajas atacante | 22,0% ± 0,1% | 21,9% ± 0,1% | 22,5% ± 0,1% |
| Bajas defensor | 6,5% ± 0,2% | 5,9% ± 0,2% | 5,7% ± 0,2% |
| Duración media | 40 ticks (202 s) | 51 ticks (253 s) | 67 ticks (337 s) |

El efecto más claro y esperable es sobre el **tiempo**: la batalla se estira un
27% bajo lluvia y un 68% bajo nieve, porque el atacante tarda más en cerrar
distancia. El efecto sobre las bajas es chico y en la dirección esperada (el
defensor sufre algo menos bajo mal tiempo), pero modesto en este escenario
puntual porque el defensor está quieto: no tiene marcha que frenar, así que solo
lo benefician el alcance reducido del atacante y los fallos de encendido en
lluvia. Un escenario con ambos bandos maniobrando probablemente mostraría un
efecto mayor; no se probó por acotar el alcance de esta fase.

## Sabido vs. supuesto

**Con fuente:** que la pólvora mojada podía fallar el encendido, que el barro
frenaba la marcha, y que la nieve reducía la visibilidad y el paso, son hechos
históricos documentados de forma cualitativa (Eylau 1807 bajo tormenta de nieve
es el ejemplo que ya cita `docs/diseno.md`). La categoría CDB90 seco/húmedo
(`wx1`) es un dato real.

**Inventado, sin fuente ni calibración:** los cinco parámetros numéricos
(`clima_lluvia_p_fallo`, `clima_lluvia_factor_marcha`,
`clima_lluvia_factor_alcance`, `clima_nieve_factor_marcha`,
`clima_nieve_factor_alcance`). CLAUDE.md ya marcaba esto de entrada: "buscar
fuente con cifras" para la probabilidad de fallo de la pólvora mojada; no se
encontró una cifra citable, y CDB90 no tiene muestra suficiente para calibrar
por ajuste. Quedan como valores de diseño razonables, no como resultado de
ningún proceso de validación.

**Simplificación deliberada:** no distinguir lluvia de nieve en términos de
humedad real (nieve no moja la pólvora en este modelo) es una decisión de
diseño basada en intuición física, no en una fuente que lo confirme para el
contexto de mosquetes de la época.
