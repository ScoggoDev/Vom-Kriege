# Informe: formaciones (línea/columna) y mélé

## Qué se construyó

**Formaciones** (`Config.formaciones_activo`): cada unidad tiene un estado
persistente, línea (default) o columna, que cambia con las órdenes
`FORMAR_LINEA`/`FORMAR_COLUMNA` (instantáneo, la unidad no dispara ni se mueve
el tick que cambia). En columna: marcha más rápido
(`columna_factor_marcha`), pero solo una fracción de la unidad puede disparar
de lleno (`columna_factor_disparo`, menos efectivo al tirar) y es más fácil de
alcanzar (`columna_factor_recibido`, más densa).

**Sin cuadro**: no hay caballería en el motor, y el cuadro histórico existía
específicamente para resistirla. Sin caballería, un cuadro sería una línea
estrictamente peor (menos frente de fuego, misma vulnerabilidad a la
infantería) sin ningún beneficio compensatorio. Implementarlo ahora habría
sido construir una mecánica sin ningún caso de uso real en este motor.

**Mélé** (`Config.mele_activo`, orden `CARGAR`): una unidad cargando avanza
como con `AVANZAR` hasta quedar a `mele_distancia_m` del enemigo. En contacto,
dejan de disparar (ninguno de los dos lados, ni el que carga ni el que recibe
la carga) y pelean cuerpo a cuerpo: cada soldado en contacto tiene una
probabilidad (`mele_p_baja`, con bono `mele_bonus_columna` si el que carga
está en columna, el ímpetu de la carga) de causar una baja en el enemigo más
cercano, usando el mismo esquema de blanco que el fuego a distancia.

Siguiendo la idea de `docs/diseno.md` ("una carga es, en el fondo, una prueba
de moral"), el contacto cuerpo a cuerpo suma `mele_choque_moral` a la fracción
de bajas percibida de **ambos** lados en contacto (si `moral_activa`), no solo
del que recibe la carga: la mayoría de las cargas históricas se decidían por
el quiebre de un bando antes del choque físico real, y el motor ahora puede
mostrar ese patrón en vez de asumirlo.

## Simplificaciones deliberadas

- El cambio de formación es instantáneo, no toma varios ticks como en la
  realidad (formar o deshacer un cuadro llevaba tiempo real).
- El emparejamiento de mélé usa la misma pareja "unidad propia, unidad enemiga
  más cercana" que ya usa el fuego a distancia, que no es necesariamente
  simétrica si hay varias unidades enemigas cerca (A puede ver a X como su más
  cercana sin que X vea a A como la suya).
- El daño de mélé se resuelve después del daño a distancia dentro del mismo
  tick (no se puede acuchillar a quien ya murió de un balazo ese tick), una
  decisión de orden, no una regla con fuente.

## Verificación

75 tests, todos pasando (67 anteriores + 8 nuevos): regresión bit a bit con
ambos flags apagados (parámetros extremos incluidos), una orden de cambio de
formación efectivamente cambia el estado, cambiar de formación no dispara ni
mueve, la columna marcha más rápido que la línea (mismo seed, única
diferencia la formación), la columna recibe más o igual impactos que la línea
(comparación pareada), `CARGAR` avanza hasta el contacto y después pelea
cuerpo a cuerpo con bajas garantizadas (`mele_p_baja=1.0`), y el mélé funciona
sin munición ni alcance de fuego (es cuerpo a cuerpo, no depende del arma).

## Rendimiento

200 batallas, 100 por bando: 3,79 s sin nada activo, 3,82 s con formaciones,
4,11 s con mélé. Sin overhead relevante.

## Pregunta de investigación 3: línea contra columna

Antes marcada como no respondible (`docs/informe_fase6_investigacion.md`).
Ahora sí: `experimentos/fase6_linea_vs_columna.py` compara tres doctrinas de
ataque contra un defensor en línea quieto. 1000 batallas por doctrina.

| doctrina | gana el atacante | bajas atacante | bajas defensor |
|---|---|---|---|
| siempre en línea | 10,0% ± 0,9% | 22,0% ± 0,1% | 6,5% ± 0,2% |
| columna hasta 100 m, despliega y tirotea en línea | 7,3% ± 0,8% | 22,4% ± 0,1% | 5,0% ± 0,2% |
| siempre en columna (control, debería ser peor) | 0,4% ± 0,2% | 23,6% ± 0,1% | 1,4% ± 0,1% |

**El control funciona como se esperaba**: pelear todo el combate en columna es
claramente peor (0,4% contra 7-10%), confirmando que la mecánica penaliza
columna-en-combate de forma coherente, no al revés.

**Lo que no se esperaba**: marchar en columna y desplegar en línea antes de
tirotear (la doctrina histórica estándar) no superó a marchar directamente en
línea; salió un poco peor (7,3% contra 10,0%, dentro de un margen moderado
pero consistente también en bajas del defensor, 5,0% contra 6,5%). La
explicación más plausible: en este motor, la velocidad de marcha no es el
factor que determina el resultado (el atacante ya pierde la mayoría de las
veces por la asimetría quieto-vs-avanza de fases anteriores), y el tick que se
"pierde" al desplegarse en línea justo antes de entrar en rango cuesta un poco
sin compensación, porque no hay nada que penalice marchar en línea todo el
trayecto en este escenario puntual (sin artillería ni caballería que castiguen
específicamente a la columna por la distancia, que es el motivo histórico real
para desplegarse antes de llegar al contacto). Dicho de otro modo: el modelo
captura bien que combatir en columna es malo, pero no tiene ninguna mecánica
todavía (artillería) que haga marchar en columna, en sí, riesgoso a distancia.

## Sabido vs. supuesto

**Con fuente:** que la columna era más rápida para marchar y más vulnerable en
combate, que la línea maximizaba el fuego frontal, y que las cargas rara vez
llegaban a mélé real (la mayoría de los bandos se quebraban antes), son hechos
de doctrina napoleónica bien documentados y ya citados en `docs/diseno.md`.

**Inventado, sin calibrar:** los seis parámetros numéricos
(`columna_factor_marcha`, `columna_factor_disparo`, `columna_factor_recibido`,
`mele_distancia_m`, `mele_choque_moral`, `mele_p_baja`, `mele_bonus_columna`)
no tienen fuente ni fueron ajustados contra ningún dato.

**Limitación que condiciona el resultado de línea-vs-columna:** sin
artillería, no hay ninguna fuerza en el motor que castigue específicamente a
una columna por estar expuesta a distancia (que es la razón histórica real
para desplegarse antes de llegar al contacto). El resultado de arriba dice más
sobre esa ausencia que sobre si la columna "sirve" en general.
