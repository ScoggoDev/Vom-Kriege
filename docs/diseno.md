# Diseño del simulador

Este documento guarda el razonamiento detrás de las decisiones. Lo marcado como "supuesto" o "inventado" necesita fuente o análisis de sensibilidad antes de sacar conclusiones.

## 1. Por qué napoleónico de línea

- La moral decidía. La táctica de línea existía para mantener a los hombres juntos y parados bajo fuego. Muchos relatos y registros médicos de la época sugieren que las cargas a bayoneta rara vez terminaban en melé real: casi siempre un bando se quebraba antes del choque (supuesto a verificar con fuentes). Una carga es, en el fondo, una prueba de moral.
- Pocas decisiones bien definidas: formar en línea, columna o cuadro; avanzar, sostener, disparar, cargar, meter la reserva. Eso hace manejable al general que aprende.
- La demora de las órdenes es histórica: viajaban con ayudantes de campo a caballo.
- La puntería individual pesa poco. El mosquete de ánima lisa era impreciso y lento, del orden de 2 o 3 disparos por minuto con tropa entrenada (supuesto común, buscar fuente). Importan más el entrenamiento (velocidad de recarga) y la disciplina de fuego (aguantar hasta distancia corta).

## 2. Lanchester: qué se puede y qué no se puede concluir

- Ley cuadrada (fuego apuntado): la fuerza crece con el cuadrado del tamaño. Sobrevivientes del ganador: sqrt(A0² - B0²).
- Ley lineal (combate uno a uno, o fuego a un área de tamaño fijo): A0 - B0.
- Fuego al bulto con huecos (modo `area` de este motor): cada bala va a un lugar de la formación enemiga, que conserva los lugares de los caídos. Deducción: dB/dt = -k·A·B/B0 y dA/dt = -k·B·A/A0, entonces A0·(A0 - A) = B0·(B0 - B), y el ganador termina con A0 - B0²/A0. Queda entre las dos leyes.
- En la práctica se usa a menudo un exponente 1,5 porque el combate real mezcla ambas leyes (fuente: artículo de Wikipedia sobre las leyes de Lanchester y sus referencias).
- Límite epistemológico: cada regla de elección de blanco produce su ley por construcción, y la verificación v0 lo confirma. Un motor más realista responde "¿Lanchester sobrevive cuando se suman moral, terreno y humo?", que es una pregunta sobre el modelo. Para decir algo sobre la realidad, el motor tiene que estar validado contra datos históricos.
- Hipótesis a probar: cerrar filas mantiene constante la densidad de la formación y debería empujar el modo área hacia la ley cuadrada; no cerrarlas deja huecos por donde pasan las balas.

## 3. Mecánicas planeadas

Cada una detrás de un flag de `Config`.

### Moral (fase 1)
- Baja con: compañeros caídos cerca, compañeros huyendo cerca, flanco o retaguardia amenazados, cansancio, huecos en la línea, carga enemiga que se acerca.
- Sube o se sostiene con: compañeros a los costados (cohesión), cercanía de oficiales o del general, estar ganando el intercambio de fuego.
- Bajo un umbral, el soldado huye: sale de la formación, deja de disparar y se aleja. La huida es contagiosa, en cascada, como los modelos de umbral de Granovetter (1978). Umbrales heterogéneos entre soldados.
- Se suele señalar que en batallas preindustriales la mayoría de las muertes ocurría durante la huida (supuesto a verificar). Si es así, el motor debería mostrar picos de bajas en la persecución.
- La batalla termina cuando un bando colapsa (proporción de hombres en huida o fuera de combate sobre un umbral) o por tiempo.
- Validación: bajas finales de ganador y perdedor comparadas con CDB90 (ver sección 6).

### Terreno (fase 2)
- Elevación: más visión y alcance; subir cansa y frena; detrás de la cresta se está protegido del fuego directo (defensa en contrapendiente).
- Cobertura (granjas, muros, bosques): menos probabilidad de recibir impactos y más moral para quien la ocupa. Hougoumont, en Waterloo, es el ejemplo clásico de un punto fuerte.
- Ríos: intransitables salvo por puentes o vados, que se vuelven cuellos de botella. Cruzar bajo fuego castiga la moral y desordena la formación.
- Pantanos: movimiento lento, más cansancio y pérdida de cohesión.
- Mapas: en un choque simétrico, espejados; o aleatorios jugados dos veces cambiando de lado para cancelar la suerte del terreno. Para entrenar, mapas aleatorios, si no el general memoriza un mapa en vez de aprender principios.

### Clima (fase 3)
- Lluvia: la pólvora mojada hace fallar el encendido del mosquete (probabilidad de fallo alta, buscar fuente con cifras), barro que frena y cansa, menos visibilidad.
- Nieve: movimiento más lento y visibilidad reducida. Eylau (1807) se peleó bajo una tormenta de nieve.
- CDB90 codifica el clima como seco o húmedo; sirve para un chequeo grueso.

### Munición, cansancio, humo y disciplina de fuego (fase 4)
- Munición limitada por soldado. Al agotarse, solo queda cargar o retirarse. Pregunta: ¿la batalla pasa de una ley a otra cuando se acaban las balas?
- Cansancio: sube al marchar, cargar y pelear; baja en reposo; empeora puntería, recarga y moral.
- Humo: cada descarga agrega humo local que reduce la visibilidad de ambos bandos y se disipa con el tiempo (y el viento, si se agrega).
- Disciplina de fuego: tropa que aguanta hasta corta distancia gasta menos, genera menos humo temprano y dispara con más efecto.

### Formaciones y melé
- Línea (máximo fuego, frágil de flanco), columna (movimiento y empuje, poco fuego), cuadro (contra caballería).
- Melé simple para cuando dos formaciones realmente chocan.

### Futuro
- Caballería y artillería: el piedra-papel-tijera real de la época (el cuadro frena a la caballería pero es un blanco ideal para los cañones).

## 4. El general que aprende (fase 5)

- Manda unidades con órdenes discretas: avanzar, sostener y disparar, cargar, retirarse, cambiar formación, meter la reserva.
- Decide cada cierta cantidad de ticks; la orden llega con demora proporcional a la distancia.
- Observación: resumen por unidad (fuerza, moral, munición, cansancio, formación, posición) más el mapa de terreno como imagen. Implica una red chica con capas convolucionales.
- Recompensa: ganar, perder o empatar, con desempate por control del terreno clave. Vigilar atajos: el general optimiza exactamente lo que se premia.
- Algoritmo: estrategias evolutivas primero, porque usan solo el resultado final de la batalla y no necesitan saber qué orden fue la buena, y se paralelizan bien. PPO si se quedan cortas.
- Oponentes: varios generales de reglas con doctrinas distintas, para que no aprenda a explotar las manías de uno solo. Después, dos generales aprendiendo entre sí, que puede ciclar.
- Riesgo medido antes, efecto estufa caliente (Denrell y March, 2001): un aprendiz con estimaciones ruidosas deja de probar las opciones que le salieron mal y nunca corrige esa mala impresión. En un experimento previo con subastas, agentes Q-learning sobrepujaban por este motivo: el sesgo crecía con la tasa de aprendizaje y los errores eran asimétricos (71% hacia arriba contra 5% hacia abajo). Acá podría verse como un general que prueba una carga, la pierde por mala suerte y no vuelve a cargar nunca. Control: comparar la política aprendida con la mejor respuesta contra el mismo rival.

## 5. JEV (descartado por ahora)

JEV (TypeSafe) es un modelo que devuelve decisiones con probabilidades en vez de texto. No aprende de nuestras batallas, así que no puede ser el general que aprende. Roles posibles a futuro, siempre como experimento comparado: juez que puntúa cada orden (riesgo: mete su idea de táctica real, que puede no valer con nuestras reglas) o rival sin entrenamiento ("¿la experiencia le gana al sentido común?").

## 6. Datos de validación: CDB90

- Base del U.S. Army Concepts Analysis Agency: más de 600 batallas terrestres entre 1600 y 1973, con fuerzas, bajas, ganador, duración y descriptores de terreno y clima. Versión limpia en github.com/jrnold/CDB90.
- Archivos útiles: `battles.csv` (ganador en `wina`: 1 gana el atacante, -1 pierde, 0 empate), `belligerents.csv` (fuerza inicial `intst`, bajas `cas`, `attacker`), `active_periods.csv` (fechas, `start_time_min`), `terrain.csv` y `weather.csv` (códigos gruesos: llano, ondulado, abrupto; seco o húmedo).
- Resultado de `experimentos/cdb90_bajas.py` para 1792-1815: 26 batallas utilizables; el ganador pierde una mediana de 11% (p25-p75: 8-22%) y el perdedor 23% (p25-p75: 15-35%). Para todas las épocas (329 batallas): 6% y 19%.
- Cuidados: muestra chica; la base se cargó con errores de codificación conocidos; los datos son agregados por ejército y por batalla entera, con armas combinadas, mientras que nuestro motor es solo infantería; verificar si `cas` incluye heridos y prisioneros.
- Con esta base también se puede ajustar Lanchester directamente a batallas reales, como hicieron Helmbold y Hartley. Sería la comparación de fondo para el motor.

## 7. Preguntas de investigación (fase 6)

1. ¿Qué ley de Lanchester emerge cuando se suman moral, terreno y humo? ¿Se parece al exponente 1,5?
2. ¿Qué ley ajusta mejor a las batallas reales de CDB90?
3. Línea contra columna, el debate clásico de la época: ¿de qué depende quién gana?
4. ¿Aguantar el fuego o disparar temprano, con humo y munición limitada?
5. ¿Un ejército chico con moral alta le gana a uno grande? ¿Dónde está el punto de quiebre?
6. ¿Cerrar filas cambia la ley que emerge?
7. ¿Cuántos soldados vale una colina, una granja o un general? ¿Qué pasa si matan al general?
8. ¿La lluvia favorece al que carga?
