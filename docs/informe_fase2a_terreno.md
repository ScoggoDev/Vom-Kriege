# Informe fase 2a: elevación y cobertura

## Qué se construyó

Un perfil de terreno simplificado, en `y` solamente (una cresta que cruza todo el
frente, no un mapa 2D completo): `altura(y)` es una campana centrada en
`terreno_cresta_y_m`. Efectos, todos detrás de `terreno_activo` (default `False`):

- **Ventaja de altura**: bonus multiplicativo a la puntería y al alcance efectivo
  proporcional a la diferencia de altura entre tirador y blanco.
- **Defensa en contrapendiente**: si la cresta queda entre tirador y blanco y es
  más alta que la línea recta que uniría sus posiciones, el disparo directamente
  no sale (no es una reducción de probabilidad, es un bloqueo total de la línea de
  tiro).
- **Cobertura**: una franja rectangular en x,y (bosque o granja) que reduce la
  probabilidad de ser alcanzado para quien la ocupa, y reduce la fracción de
  bajas que un soldado "percibe" en su propia unidad a los fines de la moral (si
  `moral_activa`).
- **Pendiente que frena**: subir la cresta reduce la distancia que avanza una
  unidad en el tick, proporcional a cuánto sube.

No se modela el cansancio de subir (no existe hasta fase 4) ni un mapa 2D real
(no hay todavía infraestructura de mapas cargados o aleatorios). Es un perfil de
una sola cresta, elegido para que alcance a probar las hipótesis de
`docs/diseno.md` sin construir de entrada la maquinaria completa de mapas.

## Verificación

25 tests, todos pasando (18 anteriores sin cambios + 7 nuevos de terreno):
regresión bit a bit con el flag apagado (probado con parámetros de terreno
extremos, no solo default), la cresta bloquea el disparo por completo (no solo lo
degrada), el control sin cresta sí conecta, la cobertura reduce impactos (mismo
seed en ambas corridas, así que es casi determinista, no solo estadístico), y la
pendiente frena el avance sin detenerlo.

**Bug encontrado y corregido durante la verificación**: al desactivar el flag
usé `bloqueada = False` (un bool de Python) en la rama else. `~False` en Python
da `-1`, no `True`, y al combinarlo con arrays booleanos de numpy corrompía la
máscara de disparo entera (`ValueError: object too deep for desired array` en
`np.bincount`). Los tests de regresión lo agarraron al toque. Se corrigió
inicializando `bloqueada` como array de numpy (`np.zeros_like(d_blanco, bool)`).

## Rendimiento

200 batallas, 100 por bando: 3,29 s con terreno apagado, 4,35 s con terreno
activo (~1,3x, dentro de lo aceptable).

## Sensibilidad / coherencia interna

No hay un número de CDB90 limpio para "tenía la loma" (esa base no separa esa
variable), así que en vez de calibrar contra un objetivo externo, se corrió una
prueba de coherencia: `experimentos/terreno_ventaja.py`, defensor quieto sobre la
cresta con cobertura vs atacante que avanza y dispara, comparado con el mismo
enfrentamiento sin terreno. 1000 batallas por condición (5 semillas x 200).

| | sin terreno | con terreno |
|---|---|---|
| Gana el defensor | 87,6% ± 1,0% | 99,8% ± 0,1% |
| Bajas del atacante | 22,0% ± 0,1% | 22,9% ± 0,1% |
| Bajas del defensor | 6,5% ± 0,2% | 1,7% ± 0,1% |

**Ojo con el resultado sin terreno**: el defensor ya gana 87,6% de las veces
aunque no haya ninguna ventaja de terreno. Eso es un artefacto de la asimetría
táctica quieto-vs-avanza (quien se queda quieto dispara sin penalidad de
movimiento desde el primer tick, mientras el atacante recién puede disparar
después de cerrar distancia bajo fuego), no del terreno. Por eso la lectura
correcta no es "el terreno hace ganar al defensor", sino la diferencia entre las
dos filas: con terreno, las bajas del defensor caen a un tercio (6,5% a 1,7%) y
el atacante casi no nota diferencia en las suyas (22,0% a 22,9%). Es coherente
con el diseño: elevación y cobertura protegen a quien las ocupa, no perjudican al
que ataca por otra vía. No es un resultado absurdo, pero tampoco prueba nada
contra datos reales, es solo una verificación de que el mecanismo se comporta
como se espera antes de construir mapas más completos encima.

## Sabido vs. supuesto

**Con fuente:** la idea de que la defensa en contrapendiente protegía del fuego
directo es doctrina napoleónica documentada (Wellington en Waterloo, entre
otros). La dirección del efecto (loma + cobertura ayuda al que las ocupa) tiene
respaldo histórico.

**Inventado, sin calibrar:** los seis parámetros numéricos de terreno
(`terreno_cresta_alto_m`, `terreno_bonus_punteria_por_m`,
`terreno_bonus_alcance_por_m`, `terreno_frena_por_m_subida`,
`terreno_cobertura_reduccion`, `terreno_cobertura_bonus_moral`) no tienen fuente
ni fueron ajustados contra ningún dato, quedaron en valores de diseño
razonables. A diferencia de fase 1, acá no hay un número de CDB90 limpio contra
el cual calibrar, así que no hay barrido de calibración, solo la prueba de
coherencia de arriba. Cuando se aborde la pregunta 7 de investigación
(`docs/diseno.md`: "¿cuántos soldados vale una colina?") en fase 6, ahí sí va a
hacer falta pensar en una fuente real o al menos un rango de sensibilidad más
amplio.

**Simplificación deliberada:** el perfil de una sola cresta en 1D (no un mapa
2D real) es una decisión de alcance, no un hallazgo. Cuando el general que
aprende (fase 5) necesite "el mapa como imagen" va a hacer falta construir mapas
de verdad, y en ese momento esta representación probablemente se reemplace.
