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
    (`pantano_activo`): cuellos de botella y freno de marcha; con movimiento
    lateral (`IZQUIERDA`/`DERECHA`) un general puede maniobrar hasta alinearse
    con un vado (`generals.cruzar_rio_y_disparar`). Terreno clave
    (`terreno_clave_activo`): desempate por tiempo segun quien controla una
    zona, para que la pasividad no sea gratis (`CLAUDE.md`, decisión vieja,
    implementada recién ahora).
  - Clima (`clima`: "seco"/"lluvia"/"nieve"): fallo de encendido, freno de
    marcha, menos alcance efectivo.
  - Munición limitada (`municion_activa`), cansancio (`cansancio_activo`), humo
    (`humo_activo`). Disciplina de fuego no es una mecánica aparte: ya emerge de
    `avanzar_y_disparar(distancia_m)`, que no dispara nada mientras avanza.
  - Formaciones línea/columna (`formaciones_activo`, sin cuadro: no hay
    caballería que lo justifique) y mélé a la bayoneta (`mele_activo`, orden
    `CARGAR`): el contacto es, si `moral_activa`, ante todo una prueba de
    moral para ambos lados, no solo daño físico.
- `generals.py`: generales de reglas `quieto`, `avanzar_y_disparar(distancia_m)`,
  `cruzar_rio_y_disparar`, `columna_y_despliega`, `siempre_columna_y_dispara`.
- `aprendizaje/`: general entrenado con estrategias evolutivas (fase 5). Red
  chica (sin convoluciones, no hay mapa como imagen) sobre 11 features por
  unidad; todavía solo elige AVANZAR/SOSTENER (no usa movimiento lateral,
  formaciones ni mélé, aunque el motor ya las tiene). `entrenar_self_play`
  entrena por rondas contra versiones congeladas de sí mismo (fictitious play),
  además del pool de reglas. El problema de fitness (no ataca a un rival
  pasivo) sigue sin resolver pese a varios intentos, ver informe de fase 5.
- `experimentos/`: scripts de verificación (`lanchester.py`), validación
  (`cdb90_bajas.py`, `cdb90_clima.py`, `cdb90_lanchester.py`), sensibilidad por
  fase, entrenamiento (`entrenar_general.py`, `entrenar_self_play.py`,
  `evaluar_general.py`), y las preguntas de investigación de fase 6 (`fase6_*.py`).
- `visor/index.html`: visor HTML estático de repeticiones exportadas con
  `experimentos/exportar_replay.py`.
- Hallazgos que vale la pena recordar: sin moral las batallas no terminan
  (fase 1). Con moral, ninguna ley de Lanchester clásica ajusta porque la
  cascada de huida saca al combate del régimen de atrición continua (fase 6,
  pregunta 1). Dos bugs reales de "casillas fantasma" (soldados de relleno
  cuando los bandos tienen distinto tamaño, contados como bajas) aparecieron
  recién en fase 6 al probar ejércitos asimétricos con moral; ya corregidos,
  ningún informe anterior estaba afectado. Comprometer más unidades a cruzar un
  río bajo fuego puede salir peor, no mejor, porque la penalidad de moral por
  cruzar se paga por soldado y el colapso se mide sobre todo el ejército
  (`docs/informe_movimiento_lateral.md`). Marchar en columna y desplegarse en
  línea antes de tirotear no superó a marchar directamente en línea, porque no
  hay artillería que castigue a una columna expuesta a distancia
  (`docs/informe_formaciones_mele.md`).

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
2. ✅ Terreno: elevación y cobertura (`docs/informe_fase2a_terreno.md`); río, vados y pantano (`docs/informe_fase2b_rio.md`). Movimiento lateral real agregado despues (`docs/informe_movimiento_lateral.md`): los vados ya son algo hacia lo que un general puede maniobrar (`generals.cruzar_rio_y_disparar`), no solo una alineación fija. Sin mapas 2D cargables ni aleatorios todavía (pendiente si el general que aprende lo necesita como imagen).
3. ✅ Clima: lluvia y nieve (`docs/informe_fase3_clima.md`). CDB90 no tiene muestra suficiente para calibrar (solo 4 batallas húmedas en 1792-1815).
4. ✅ Munición limitada (`docs/informe_fase4a_municion.md`), cansancio (`docs/informe_fase4b_cansancio.md`, encontró una interacción real con moral: la tropa exhausta colapsa antes de acumular bajas), humo (`docs/informe_fase4c_humo.md`). Disciplina de fuego no se construyó como mecánica aparte, ya emerge de la distancia de apertura del general.
5. ✅ (parcial) General que aprende con estrategias evolutivas, evaluado contra varios generales de reglas y con self-play por rondas (fictitious play, `docs/informe_fase5_general.md`). **Sin resolver**: con el fitness actual (incluso agregando terreno clave y un término de cercanía a la zona) aprendió a no atacar nunca a un rival quieto (empate por tiempo en vez de arriesgarse a perder). Es coherente con los hallazgos de fases 2-4, pero varios intentos de arreglarlo con reward shaping no cambiaron el resultado; hace falta un barrido de hiperparámetros de ES o repensar el fitness desde cero antes de confiar en que este general "sabe pelear".
6. ✅ Experimentos de investigación (`docs/informe_fase6_investigacion.md`): 7 de 8 preguntas respondidas (línea vs columna ya respondida en `docs/informe_formaciones_mele.md` una vez agregadas las formaciones), 1 no respondible (matar al general, porque el general no es una entidad física en el campo).

### Pendiente, sin fase asignada

- ✅ Formaciones (línea y columna, sin cuadro: no hay caballería que lo justifique) y mélé (`docs/informe_formaciones_mele.md`).
- ✅ Movimiento lateral real (`docs/informe_movimiento_lateral.md`).
- ✅ Self-play por rondas (fictitious play, `aprendizaje/es.py:entrenar_self_play`), aunque hereda el problema de fitness de fase 5 sin resolver.
- Mapas de terreno como grilla 2D real, cargable o aleatoria (mapas espejados o random-jugado-dos-veces, como pide la sección de terreno), si el general que aprende lo necesita como imagen. El general sigue usando una red chica sobre features escalares, no una convolucional.
- Ampliar el espacio de acciones del general que aprende para que use movimiento lateral, formaciones y mélé (hoy solo elige AVANZAR/SOSTENER).
- Resolver el problema de fitness de fase 5: el general entrenado no ataca a un rival pasivo pese a varios intentos de reward shaping (terreno clave, término de cercanía a la zona con coeficiente hasta -1,5). Sospecha principal: la señal de los otros oponentes del pool domina el gradiente de ES antes de que el término nuevo mueva algo en pocas generaciones; no descartado del todo. Antes de seguir, probar: barrido de sigma/tasa de aprendizaje, más generaciones, o entrenar contra quieto en solitario (sin rotar oponentes) para aislar la señal.
- Comparar ES contra PPO si estrategias evolutivas se quedan cortas (decisión original de `docs/diseno.md`, todavía no evaluada).

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
python experimentos/entrenar_self_play.py 3 15 12 24

# fase 6: preguntas de investigacion
python experimentos/fase6_lanchester_combinado.py
python experimentos/cdb90_lanchester.py
python experimentos/fase6_moral_vs_tamano.py
python experimentos/fase6_cierra_filas.py
python experimentos/fase6_cuanto_vale_la_loma.py
python experimentos/fase6_linea_vs_columna.py

# movimiento lateral y formaciones
python experimentos/rio_con_movimiento_lateral.py
```
