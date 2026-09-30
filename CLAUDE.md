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

## Estado actual (v0)

- `engine.py`: motor vectorizado. Grilla de 1 m, tick de 5 s. Capa 1: salud (sano, herido, fuera) y puntería. Fuego simultáneo. Cada unidad le tira a la unidad enemiga viva más cercana y cada soldado elige blanco dentro de ella. Modos `area` (al bulto, la bala puede caer en un hueco) y `apuntado` (a un enemigo vivo).
- `generals.py`: generales de reglas `quieto` y `avanzar_y_disparar(distancia_m)`.
- `experimentos/lanchester.py`: verificación. Con 100 contra 70, el modo apuntado deja 69 sobrevivientes (ley cuadrada: 71) y el modo área deja 49 (fórmula del modo área A0 - B0²/A0: 51).
- `experimentos/cdb90_bajas.py`: objetivo de validación desde datos reales.
- Hallazgo: sin moral las batallas no terminan. A los 30 minutos quedan ~68% de bajas por bando y ningún ganador.

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

0. Base: tests con pytest (incluida la verificación de Lanchester), exportar repeticiones a JSON y un visor HTML estático para mirarlas.
1. Moral y fin de batalla por colapso. Criterio de validación: con generales de reglas, el perdedor termina cerca de 15-35% de bajas (mediana 23%) y el ganador cerca de 8-22% (mediana 11%), según CDB90 1792-1815.
2. Terreno: elevación y cobertura primero; después ríos, puentes, vados y pantanos. Mapas espejados, o aleatorios jugados dos veces cambiando de lado.
3. Clima: lluvia y nieve.
4. Munición limitada, cansancio, humo y disciplina de fuego.
5. General que aprende, primero contra varios generales de reglas distintos y después contra otro general que aprende.
6. Experimentos de investigación (lista en `docs/diseno.md`).

## Comandos

```
pip install -r requirements.txt
git clone --depth 1 https://github.com/jrnold/CDB90.git data/cdb90
python experimentos/lanchester.py apuntado
python experimentos/lanchester.py area
python experimentos/cdb90_bajas.py
pytest -q
```
