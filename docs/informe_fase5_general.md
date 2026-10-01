# Informe fase 5: el general que aprende

## Reducción de alcance frente a `docs/diseno.md` sección 4

Documentada también en los docstrings de `aprendizaje/`:

- **Sin mapa como imagen**: el motor no tiene una grilla 2D real (fase 2a usa un
  perfil paramétrico de una sola cresta, no una grilla cargable ni aleatoria).
  La política usa una red de una sola capa oculta (16 neuronas, tanh) sobre 9
  features escalares por unidad, no una convolucional.
- **Sin cargar, retirarse ni cambiar formación**: esas mecánicas no existen
  (no hay melé ni más de una formación). El general aprendido elige entre las
  mismas dos órdenes que ya usan los generales de reglas: `AVANZAR` o
  `SOSTENER`, una por unidad.
- **Observación** (`aprendizaje/observacion.py`): distancia al enemigo más
  cercano, fuerza propia, ventaja numérica, moral, munición, cansancio, altura,
  si está en cobertura, y tiempo transcurrido. Cada feature es neutral (1,0 o
  0,0) si la mecánica correspondiente está apagada, así que la misma red sirve
  con cualquier combinación de flags.

## Algoritmo: estrategias evolutivas (OpenAI-ES)

Elegido sobre PPO, como preveía `docs/diseno.md`, porque solo necesita el
resultado final de la batalla y se paraleliza gratis: cada evaluación de una
política corre B batallas en paralelo con el motor vectorizado existente, sin
tocar nada del motor para entrenar. Fitness = diferencia de bajas (continua,
dando señal de gradiente desde el principio) más un bono por resultado
decisivo. Oponente rotando entre `quieto` y `avanzar_y_disparar` a 40, 70 y 100
metros, para no sobreajustar a una sola doctrina.

## Bug encontrado armando el entrenamiento

Al construir el experimento de Lanchester combinado (ver más abajo) con
ejércitos asimétricos y moral activa, un bando se quebraba sin que hubiera
pasado ningún combate. La causa: las casillas de relleno (cuando un bando tiene
menos soldados que el máximo) tienen `salud=0` para siempre porque nunca
existieron, y el cálculo de moral las contaba como bajas reales desde el primer
tick. Corregido en un commit aparte (`perdido = ((salud==0) & existe) |
huyendo`), con dos tests de regresión. Ningún informe anterior usaba moral con
ejércitos asimétricos, así que no hay resultados previos para revisar.

## Entrenamiento

40 generaciones, población 12 (24 evaluaciones por generación contando el
muestreo espejado), 24 batallas por evaluación, sigma=0,1, lr=0,05. 731 s
totales en esta máquina. El fitness promedio por generación osciló de forma
consistente según qué oponente tocaba ese turno (quieto: ~0; distancia 40:
~0,71; distancia 70: ~0,52; distancia 100: ~0,32) pero **se mantuvo
prácticamente plano a lo largo de las 40 generaciones dentro de cada
oponente**, sin una tendencia de mejora clara tick a tick. No se investigó a
fondo si esto es convergencia temprana a un óptimo local razonable o una tasa
de aprendizaje/sigma mal calibrados; con más tiempo de cómputo valdría la pena
correr más generaciones y comparar curvas con distintos hiperparámetros antes
de confiar en que 40 generaciones alcanzan.

## Evaluación (500 batallas por emparejamiento, 5 semillas x 100)

Comparado contra una referencia de reglas razonable, `avanzar_y_disparar(70)`
(la distancia por defecto del proyecto), jugando el mismo rol:

| oponente | gana el entrenado | gana la referencia (dist=70) |
|---|---|---|
| quieto | 0,0% ± 0,0% (empate por tiempo, 0% de bajas en ambos lados) | 10,4% ± 1,4% |
| avanzar a 40 m | 98,6% ± 0,5% | 89,4% ± 1,4% |
| avanzar a 70 m | 88,0% ± 1,5% | 46,4% ± 2,2% |
| avanzar a 100 m | 71,8% ± 2,0% | 23,8% ± 1,9% |

Contra los tres oponentes que avanzan, el general entrenado gana claramente más
que la referencia de reglas, en algunos casos por un margen enorme (88,0% contra
46,4% a distancia 70). Contra `quieto` nunca gana, pero tampoco pierde: se
verificó directamente que **no emite una sola orden de avanzar en toda la
batalla** (360 ticks), se queda a los 250 m iniciales y el tiempo se agota sin
bajas de ningún lado.

## ¿Es esto un bug? (control pedido por `docs/diseno.md`)

`docs/diseno.md` sección 4 pide comparar la política aprendida contra la mejor
respuesta posible, por el riesgo de que un aprendiz con estimaciones ruidosas
abandone una opción que le salió mal por mala suerte y no vuelva a probarla
(efecto estufa caliente, Denrell y March 2001). Acá pasa algo parecido pero
explicable: en **todas** las fases anteriores que probaron atacar a un
`quieto` (fase 2a, 2b, 4c), el atacante salió perdiendo la mayoría de las
veces, porque quien se queda quieto dispara sin penalidad de movimiento desde
el arranque mientras el que avanza recién puede devolver fuego después de
cerrar distancia bajo fuego (ver `docs/informe_fase2a_terreno.md`). Un empate
por tiempo (bajas 0%-0%) es, bajo el fitness usado para entrenar (diferencia de
bajas más bono por victoria), estrictamente mejor que atacar y perder. No avanzar
nunca contra un rival que tampoco avanza es, dado ese fitness y esa asimetría ya
documentada, una respuesta razonable, no un comportamiento roto. Pero es una
respuesta poco interesante militarmente (nunca intenta nada), y es exactamente
el tipo de atajo que `docs/diseno.md` pide vigilar: el general optimizó
literalmente lo que se premia (evitar bajas netas), no "ganar batallas" en un
sentido más amplio. Si se quiere un general que efectivamente ataque, el fitness
necesitaría premiar de forma más explícita el control de terreno o penalizar
los empates, no solo la diferencia de bajas.

## Sabido vs. supuesto

**Con fuente:** el algoritmo (OpenAI-ES, muestreo espejado y fitness
estandarizado) es una técnica publicada y bien documentada de aprendizaje por
refuerzo sin gradientes.

**Inventado, sin calibrar:** la arquitectura de la red (una capa oculta, 16
neuronas), los hiperparámetros de ES (sigma, tasa de aprendizaje, tamaño de
población, 40 generaciones), el diseño del fitness (diferencia de bajas más
bono de 0,5 por resultado decisivo), y el pool de oponentes de entrenamiento.
Ninguno se barrió ni se comparó contra alternativas; son la primera
configuración que se probó y corrió sin errores, no un óptimo encontrado por
búsqueda.

**Limitación reconocida:** 40 generaciones con fitness plano no es evidencia
fuerte de convergencia. Este informe reporta un primer resultado de que el
mecanismo de entrenamiento funciona y produce una política no trivial (gana
claramente contra tres de cuatro oponentes), no una demostración de que el
general "aprendió a pelear bien" en un sentido general.
