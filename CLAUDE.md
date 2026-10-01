# Simulador de batalla napoleónica

Simulador de batallas de infantería de línea (1792-1815) en una grilla, con soldados como agentes y un general que aprende. Objetivo científico: construir un motor lo bastante realista, validado contra datos históricos, para poner a prueba las leyes de Lanchester en vez de programarlas.

Leé `docs/diseno.md` antes de empezar cualquier fase nueva. Ahí está el razonamiento detrás de cada decisión.

## Cómo trabajar en este repo

- Tono crítico, científico y pragmático. Marcá los problemas de frente. Separá siempre lo sabido (con fuente) de lo supuesto o inventado.
- Nunca uses rayas largas (em dash) en ningún texto, código ni comentario. Usá guion común.
- Cambios mínimos sobre lo que funciona. No refactorices código que anda solo para unificar caminos. Antes de proponer un cambio de arquitectura, preguntá alcance y motivo.
- Código, comentarios, commits y documentación en español.
- Antes de programar una mecánica nueva, proponé el diseño (reglas, parámetros, cuáles tienen fuente y cuáles son inventados) y esperá el OK.
- Toda mecánica nueva va detrás de un flag en `Config`, para poder apagarla y medir su efecto.
- Cada parámetro de `Config` lleva un comentario `# fuente: ...` o `# inventado`.
- Todo resultado se reporta con cantidad de batallas, semillas y barras de error. Nada de conclusiones con una sola corrida.
- Un commit por paso con sentido; no mezcles mecánicas en el mismo commit.

## Verificación y validación

- Verificación: ¿el código hace lo que creemos? Se hace con tests. La prueba de Lanchester es un test de bugs, no un objetivo: con fuego apuntado y parámetros simples tiene que salir la ley cuadrada, y con fuego al bulto la fórmula del modo área.
- Validación: ¿el modelo se parece a la realidad? Se hace contra CDB90 y fuentes históricas. Recién con un motor validado se lo usa para poner a prueba a Lanchester.
- Cualquier táctica rara del general que aprende es un posible bug del simulador hasta demostrar lo contrario.

## Rendimiento

- El motor trabaja con arrays de numpy de forma `(B, 2, N)`: batallas en paralelo, bando, soldado.
- Prohibido: loops de Python por soldado y matrices de todos contra todos (N x N) por tick. Una versión con distancias N x N tardó más de 300 s en la prueba de Lanchester.
- Referencia actual: 200 batallas completas (360 ticks, 100 por bando) en 3,7 s. Medí después de cada fase y avisá si baja más de 2 veces.
- Si la máquina lleva rato corriendo numpy sin parar, una sola medición de reloj de pared deja de ser confiable (ver `docs/informe_fase4c_humo.md`: una corrida pareada con `cProfile`, que agrega el mismo overhead a ambos casos, es más confiable que dos `time.perf_counter()` sueltos).

## Estado actual

Fases 0 a 6 de la hoja de ruta completas (ver informes en `docs/informe_fase*.md`
para el detalle de cada una, incluido qué es sabido y qué es inventado).

- `engine.py`: motor vectorizado. Grilla de 1 m, tick de 5 s. Capas, todas detrás
  de un flag en `Config` y apagadas por defecto salvo la primera:
  - Salud (sano, herido, fuera) y puntería. Fuego simultáneo, cada unidad le
    tira a la unidad enemiga viva más cercana, cada soldado elige blanco dentro
    de ella. Modos `area` (al bulto, puede caer en un hueco) y `apuntado` (a un
    enemigo vivo). `cierra_filas` hace que "area" se comporte como "apuntado"
    (sin huecos), confirmado que empuja la ley hacia la cuadrada (fase 6).
  - Moral (`moral_activa`): cascada de huida tipo Granovetter por fracción de
    bajas de la propia unidad, umbral heterogéneo por soldado (con variante
    `moral_umbral_media_por_bando` para moral asimétrica). Fin de batalla por
    colapso. Calibrado contra CDB90 en fase 1.
  - Terreno (`terreno_activo`): una cresta (perfil en y, no mapa 2D) con ventaja
    de altura y defensa en contrapendiente (bloqueo total de línea de tiro), y
    cobertura rectangular. Río con vados (`rio_activo`) y pantano
    (`pantano_activo`): cuellos de botella fijos (sin maniobra lateral, ver
    fase 2b) y freno de marcha.
  - Clima (`clima`: "seco"/"lluvia"/"nieve"): fallo de encendido, freno de
    marcha, menos alcance efectivo.
  - Munición limitada (`municion_activa`), cansancio (`cansancio_activo`), humo
    (`humo_activo`). Disciplina de fuego no es una mecánica aparte: ya emerge de
    `avanzar_y_disparar(distancia_m)`, que no dispara nada mientras avanza.
- `generals.py`: generales de reglas `quieto` y `avanzar_y_disparar(distancia_m)`.
- `aprendizaje/`: general entrenado con estrategias evolutivas (fase 5). Red
  chica (sin convoluciones, no hay mapa como imagen) sobre 9 features por
  unidad; solo elige AVANZAR/SOSTENER (no hay melé ni formaciones todavía). Entrenado
  solo contra generales de reglas, no contra otro general que aprende (pendiente).
- `experimentos/`: scripts de verificación (`lanchester.py`), validación
  (`cdb90_bajas.py`, `cdb90_clima.py`, `cdb90_lanchester.py`), sensibilidad por
  fase, y las 8 preguntas de investigación de fase 6 (`fase6_*.py`).
- `visor/index.html`: visor HTML estático de repeticiones exportadas con
  `experimentos/exportar_replay.py`.
- Hallazgos que vale la pena recordar: sin moral las batallas no terminan
  (fase 1). Con moral, ninguna ley de Lanchester clásica ajusta porque la
  cascada de huida saca al combate del régimen de atrición continua (fase 6,
  pregunta 1). Dos bugs reales de "casillas fantasma" (soldados de relleno
  cuando los bandos tienen distinto tamaño, contados como bajas) aparecieron
  recién en fase 6 al probar ejércitos asimétricos con moral; ya corregidos,
  ningún informe anterior estaba afectado.

## Decisiones tomadas

- Choque simétrico en campo abierto, ~100 soldados por bando.
- Si se acaba el tiempo, gana quien controle el terreno clave, para que la pasividad no convenga.
- El general ordena unidades, no soldados. Las unidades ejecutan con reglas y los soldados reaccionan según su moral.
- Las órdenes viajan con demora (ayudantes de campo a caballo, que pueden morir en el camino).
- Fidelidad plausible, no exacta. No buscamos reproducir Waterloo.
- Sin JEV por ahora. Queda como experimento opcional futuro (juez de recompensa o rival sin entrenamiento).
- Aprendizaje: estrategias evolutivas primero; PPO si se quedan cortas.

## Hoja de ruta

Cada fase termina con tests pasando, benchmark, análisis de sensibilidad de los parámetros inventados y un informe corto que separe lo sabido de lo supuesto.

0. ✅ Base: tests con pytest (incluida la verificación de Lanchester), exportar repeticiones a JSON y un visor HTML estático para mirarlas.
1. ✅ Moral y fin de batalla por colapso. Calibrado contra CDB90 1792-1815 (`docs/informe_fase1_moral.md`).
2. ✅ Terreno: elevación y cobertura (`docs/informe_fase2a_terreno.md`); río, vados y pantano (`docs/informe_fase2b_rio.md`). Sin maniobra lateral todavía, así que los vados son chequeos de alineación fija, no algo hacia lo que el general pueda maniobrar. Sin mapas 2D cargables ni aleatorios (pendiente si el general que aprende lo necesita).
3. ✅ Clima: lluvia y nieve (`docs/informe_fase3_clima.md`). CDB90 no tiene muestra suficiente para calibrar (solo 4 batallas húmedas en 1792-1815).
4. ✅ Munición limitada (`docs/informe_fase4a_municion.md`), cansancio (`docs/informe_fase4b_cansancio.md`, encontró una interacción real con moral: la tropa exhausta colapsa antes de acumular bajas), humo (`docs/informe_fase4c_humo.md`). Disciplina de fuego no se construyó como mecánica aparte, ya emerge de la distancia de apertura del general.
5. ✅ (parcial) General que aprende con estrategias evolutivas, evaluado contra varios generales de reglas (`docs/informe_fase5_general.md`). **Pendiente**: entrenar contra otro general que aprende (self-play). Con el fitness actual aprendió a no atacar nunca a un rival quieto (empate por tiempo en vez de arriesgarse a perder), lo cual es coherente con los hallazgos de fases 2-4 pero no es una política interesante; revisar el diseño del fitness antes de confiar en el resultado.
6. ✅ (parcial) Experimentos de investigación (`docs/informe_fase6_investigacion.md`): 6 de 8 preguntas respondidas, 2 no respondibles todavía (línea vs columna, matar al general) porque faltan formaciones/melé y el general no es una entidad física en el campo.

### Pendiente, sin fase asignada

- Formaciones (columna, cuadro) y melé: necesario para la pregunta 3 y para que "cargar" sea una orden real del general que aprende.
- Movimiento lateral real (el general solo puede ordenar avanzar/sostener en línea recta hoy; los vados de fase 2b son un chequeo de alineación fija, no maniobra).
- Mapas de terreno como grilla 2D real, cargable o aleatoria (mapas espejados o random-jugado-dos-veces, como pide la sección de terreno), si el general que aprende lo necesita como imagen.
- Self-play (general que aprende contra otro general que aprende) y comparación con PPO si ES se queda corta.
- Revisar el diseño del fitness del general que aprende (ver hallazgo de fase 5).

## Comandos

```
pip install -r requirements.txt
git clone --depth 1 https://github.com/jrnold/CDB90.git data/cdb90
python experimentos/lanchester.py apuntado
python experimentos/lanchester.py area
python experimentos/cdb90_bajas.py
pytest -q

# fase 5: entrenar y evaluar al general
python experimentos/entrenar_general.py 40 16 32
python experimentos/evaluar_general.py

# fase 6: preguntas de investigacion
python experimentos/fase6_lanchester_combinado.py
python experimentos/cdb90_lanchester.py
python experimentos/fase6_moral_vs_tamano.py
python experimentos/fase6_cierra_filas.py
python experimentos/fase6_cuanto_vale_la_loma.py
```
