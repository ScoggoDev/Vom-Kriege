# Informe fase 6: experimentos de investigación

Respuestas a las 8 preguntas de `docs/diseno.md` sección 7, con el motor tal
como quedó al final de las fases 0-5. Dos no son respondibles con lo que existe
hoy; se explica por qué en cada caso en lugar de forzar una respuesta.

## Un bug de verdad, encontrado armando estos experimentos

Al construir el primer experimento de esta fase (pregunta 1, Lanchester con
ejércitos asimétricos y moral activa), un bando se quebraba sin que hubiera
pasado ningún combate. Causa: las casillas de relleno de un bando más chico
(cuando `n_soldados` no es igual para los dos bandos) tienen `salud=0` para
siempre porque nunca existieron, y el cálculo de moral las contaba como bajas
reales desde el primer tick. Corregido en el motor (`perdido = ((salud==0) &
existe) | huyendo`), con tests de regresión. **Ninguno de los informes de fases
1 a 4 usaba moral con ejércitos asimétricos**, así que ningún resultado anterior
queda afectado; se revisó explícitamente antes de seguir. Un segundo bug
parecido, pero en un script de experimento (no en el motor), apareció en la
pregunta 7: contar bajas como `(salud<2)` sin recortar a los soldados reales
también cuenta casillas fantasma cuando los bandos son de distinto tamaño.
Corregido ahí también. Moraleja para cualquier experimento futuro con ejércitos
asimétricos: cualquier cálculo que use `self.salud` o cuente "bajas" tiene que
filtrar por `self.existe`, no asumir que todas las casillas son soldados reales.

## Pregunta 1: ¿qué ley emerge sumando moral, terreno y humo?

`experimentos/fase6_lanchester_combinado.py`. Terreno se probó y se descartó
para este experimento puntual: poner la cresta en el punto medio entre dos
líneas estáticas enfrentadas bloqueaba la línea de tiro **en las dos
direcciones** (nadie estaba lo bastante alto como para ver por encima), así que
ninguna bala salía nunca. No es un bug del motor, es una geometría degenerada
de este experimento en particular (ver el commit); queda pendiente separar las
posiciones antes de poder sumar terreno acá con sentido. Se corrió con moral +
humo:

| B0 | gana A | A final (sim) | lineal (n=1) | área con huecos | n=1,5 | cuadrada (n=2) |
|---|---|---|---|---|---|---|
| 50 | 97% | 95,0 ± 0,2 | 50,0 | 75,0 | 74,8 | 86,6 |
| 60 | 91% | 94,1 ± 0,2 | 40,0 | 64,0 | 65,9 | 80,0 |
| 70 | 85% | 93,0 ± 0,2 | 30,0 | 51,0 | 55,6 | 71,4 |
| 80 | 75% | 92,5 ± 0,2 | 20,0 | 36,0 | 43,3 | 60,0 |
| 90 | 65% | 91,8 ± 0,2 | 10,0 | 19,0 | 27,8 | 43,6 |

**Ninguna de las leyes clásicas ajusta**: el ganador conserva muchos más
sobrevivientes (92-95 de 100) que lo que predice incluso la ley cuadrada
(43,6-86,6), que ya es la más optimista de las tres. La explicación: con moral
activa la batalla no se decide por atrición continua hasta destruir a uno de
los dos bandos, se decide por una cascada de huida que, una vez arranca, se
retroalimenta muy rápido (cuantos más huyen, más sube la fracción percibida
para los que quedan). El bando que pierde la carrera de pánico deja de
devolver fuego casi de inmediato, así que el ganador apenas sufre bajas. La
respuesta a la pregunta no es "se parece al exponente 1,5", es que **agregar
moral saca a la batalla por completo del marco de atrición continua en el que
tienen sentido las leyes de Lanchester**, al menos con esta calibración del
umbral de colapso.

## Pregunta 2: ¿qué ley ajusta mejor a CDB90?

`experimentos/cdb90_lanchester.py`. Método propio y deliberadamente simple
(no una réplica de Helmbold/Hartley, que ajustan con un coeficiente de
efectividad libre por bando): para cada batalla con ganador claro, se mide qué
tan bien se cumple A0^n−Af^n = B0^n−Bf^n (asume igual efectividad de ambos
lados, un supuesto fuerte y señalado como tal) para una grilla de n.

El error decrece de forma monótona desde n=3,0 hasta n=0,05 sin un mínimo
interior, lo cual es un problema del método, no un hallazgo: cuando n→0,
A0^n→1 para cualquier A0>0, así que la identidad se cumple de forma trivial
para todas las batallas sin que eso signifique nada sobre la dinámica real de
combate. Lo único que se puede decir con algo de confianza es que, **dentro de
un rango donde la métrica no está degenerada (n entre 0,5 y 3), exponentes más
bajos (más cerca de lineal) ajustan mejor que la ley cuadrada** tanto en
1792-1815 (25 batallas) como en todas las épocas (315 batallas). Esto es
compatible con lo que señala la literatura citada en `docs/diseno.md` (el
combate real mezcla ambas leyes, a veces con un exponente de 1,5), pero este
método no alcanza para dar un número preciso. Haría falta implementar la
regresión real de Helmbold/Hartley para responder esto en serio.

## Pregunta 3: línea contra columna

**Actualización**: ya respondida en `docs/informe_formaciones_mele.md`, después
de construir formaciones (sin fase asignada en su momento, ahora resuelto).
Resumen: pelear en columna todo el combate es claramente peor que en línea
(control que confirma que la mecánica funciona), pero marchar en columna y
desplegarse en línea antes de tirotear (la doctrina histórica) no superó a
marchar directamente en línea en este motor, porque no hay artillería que
castigue específicamente a una columna expuesta a distancia, que es la razón
histórica real para desplegarse antes de llegar al contacto.

## Pregunta 4: ¿aguantar el fuego o disparar temprano?

Ya respondida en fase 4c (`docs/informe_fase4c_humo.md`,
`experimentos/disciplina_de_fuego.py`), no se repite el trabajo acá. Resumen:
contra un defensor ya quieto y en rango, aguantar el fuego más tiempo **no
ayuda** en este motor, porque el costo de marchar más tiempo sin devolver fuego
supera la ganancia de precisión al abrir fuego de cerca (la tasa de victoria
del atacante pega un pico a 100 m de apertura y cae fuerte a 40 m). Con la
salvedad ya anotada ahí: es un resultado específico de atacar a un defensor
estático, no necesariamente generalizable a un choque donde ambos bandos
maniobran.

## Pregunta 5: ¿un ejército chico con moral alta le gana a uno grande?

`experimentos/fase6_moral_vs_tamano.py`. Bando A (tamaño variable, umbral de
huida 0,7, difícil que huya) contra bando B (fijo en 100, umbral calibrado de
fase 1, 0,4). 1000 batallas por tamaño.

| tamaño de A | gana A | gana B | empate |
|---|---|---|---|
| 100 | 90,8% ± 0,9% | 5,8% | 3,4% |
| 90 | 79,5% ± 1,3% | 13,1% | 7,4% |
| 80 | 57,3% ± 1,6% | 32,7% | 10,0% |
| 70 | 38,5% ± 1,5% | 52,2% | 9,3% |
| 60 | 15,8% ± 1,2% | 77,7% | 6,5% |
| 50 | 6,8% ± 0,8% | 90,9% | 2,3% |

**Sí, hasta un punto**: el punto de quiebre (50% de victorias) cae entre 70 y
80 soldados de A contra 100 de B, más cerca de 74-75 interpolando. Es decir,
con esta calibración, una diferencia de moral de 0,7 contra 0,4 en el umbral de
huida compensa aproximadamente una desventaja numérica de 25-26%, no más. Por
debajo de ese tamaño, el número gana aunque la moral sea mucho mejor.

## Pregunta 6: ¿cerrar filas empuja el modo área hacia la ley cuadrada?

`experimentos/fase6_cierra_filas.py`. `cierra_filas` se implementó reusando la
lógica de selección de blanco de "apuntado" (ver el commit): si la formación no
tiene huecos, un tiro al bulto siempre encuentra a alguien vivo, que es
estructuralmente lo mismo que elegir entre los vivos. Por construcción, el
resultado tenía que coincidir con la verificación de "apuntado" de fase 0, y
coincidió exactamente (84,8 / 78,0 / 69,0 / 57,0 / 41,7 sobrevivientes para
B0=50..90, idéntico a los números de `experimentos/lanchester.py` modo
apuntado). **Sí, confirmado**: cerrar filas empuja el modo área exactamente a
la ley cuadrada, porque elimina el mecanismo (huecos en la formación) que
producía la fórmula intermedia en primer lugar.

## Pregunta 7: ¿cuántos soldados vale una colina? ¿y matar al general?

La parte de matar al general **no es respondible**: el general es una política
o función abstracta, no una entidad en el campo de batalla con una posición que
se pueda alcanzar con un disparo.

La parte de la colina sí: `experimentos/fase6_cuanto_vale_la_loma.py` reduce el
tamaño del defensor (que sostiene la loma con cobertura) hasta que su
desempeño se parece al defensor de tamaño completo (100) sin ninguna ventaja de
terreno (referencia de fase 2a: gana 87,6%, bajas propias 6,5%).

| defensores | gana el defensor | bajas del defensor |
|---|---|---|
| 100 | 99,8% ± 0,1% | 1,7% ± 0,1% |
| 80 | 97,7% ± 0,5% | 3,6% ± 0,2% |
| 60 | 87,1% ± 1,1% | 7,8% ± 0,3% |
| 50 | 68,6% ± 1,5% | 12,8% ± 0,3% |

Con 60 defensores sobre la loma, la tasa de victoria (87,1%) prácticamente
empata la referencia sin terreno a tamaño completo (87,6%). **Bajo este
criterio, la loma con cobertura vale unos 40 soldados de cada 100** (100-60),
en este escenario puntual (100 atacantes, parámetros de cobertura y cresta de
fase 2a). No es una constante universal del motor, es una medida para esta
configuración exacta.

## Pregunta 8: ¿la lluvia favorece a quien carga?

Ya hay datos de fase 3 (`docs/informe_fase3_clima.md`,
`experimentos/clima_efecto.py`): atacante gana 10,0% seco, 10,0% lluvia, 8,0%
nieve. **No hay evidencia de que la lluvia favorezca al atacante** en este
motor; si acaso la nieve lo perjudica un poco. Igual que la pregunta 4, esto es
específico de atacar a un defensor estático; no se repitió con ambos bandos
maniobrando por acotar el alcance de esta fase.

## Resumen

| pregunta | respondible | resultado |
|---|---|---|
| 1. Ley combinada | sí | ninguna ley clásica ajusta; moral rompe el marco de atrición |
| 2. Ley en CDB90 | parcial | exponentes bajos ajustan mejor que n=2, sin precisión (método propio insuficiente) |
| 3. Línea vs columna | sí (actualizado) | pelear en columna es claramente peor; marchar en columna y desplegar no superó a marchar en línea, sin artillería que lo justifique |
| 4. Disciplina de fuego | sí (fase 4c) | no ayuda contra un defensor estático en este motor |
| 5. Chico con moral vs grande | sí | punto de quiebre ~74-75% del tamaño del rival |
| 6. Cerrar filas | sí | confirma la ley cuadrada, por construcción y empíricamente |
| 7a. Valor de la loma | sí | ~40 de 100 soldados, en este escenario |
| 7b. Matar al general | no | el general no es una entidad en el campo de batalla |
| 8. Lluvia y carga | sí (fase 3) | sin evidencia de que favorezca al atacante |
