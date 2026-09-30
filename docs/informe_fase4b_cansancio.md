# Informe fase 4b: cansancio

## Qué se construyó

Un escalar `cansancio` por soldado en [0,1] (`Config.cansancio_activo`, default
`False`). Sube al marchar (orden AVANZAR) o al disparar, baja en reposo (ni
marcha ni dispara). Empeora puntería (multiplicador), recarga (ticks extra) y
moral (suma a la fracción de bajas percibida, mismo mecanismo que ya usan
cobertura y cruce de río).

## Verificación

43 tests, todos pasando (39 anteriores + 4 nuevos): regresión bit a bit con el
flag apagado y parámetros extremos, marchar sube el cansancio y reposar lo baja,
forzar cansancio máximo no puede dar más impactos que descansado (comparación
pareada, misma semilla), y el cansancio nunca sale de [0,1] pese a tasas de
subida/recuperación agresivas.

## Rendimiento

200 batallas, 100 por bando: 3,42 s sin cansancio, 3,50 s con cansancio. Sin
overhead medible.

## Coherencia interna: un hallazgo que merece atención

`experimentos/cansancio_marcha_larga.py` compara un atacante que arranca a 100,
250 y 450 m del defensor, con y sin cansancio (moral activa en los tres casos).
Primera corrida con `cansancio_por_marcha=0.02` (valor de diseño original):

| distancia inicial | cansancio | gana atacante | bajas atacante |
|---|---|---|---|
| 100 m | no | 23,2% ± 1,3% | 20,6% ± 0,2% |
| 100 m | sí | 8,2% ± 0,9% | 21,7% ± 0,1% |
| 250 m | no | 10,0% ± 0,9% | 22,0% ± 0,1% |
| 250 m | sí | **0,0% ± 0,0%** | 18,5% ± 0,1% |
| 450 m | no | 9,7% ± 0,9% | 22,1% ± 0,1% |
| 450 m | sí | **0,0% ± 0,0%** | 18,5% ± 0,1% |

Dos cosas para marcar de frente, siguiendo la regla de CLAUDE.md de tratar
cualquier resultado raro como posible bug hasta demostrar lo contrario:

1. **El efecto satura**: a 250 m y a 450 m el atacante ya gana 0% de las veces
   con cansancio activo, así que la comparación no distingue "más marcha, peor
   todavía" en ese rango. Con `marcha_m_tick=4.5` y `cansancio_por_marcha=0.02`,
   el cansancio llega al tope (1,0) en unos 50 ticks de marcha continua, bastante
   antes de que un atacante que arranca a 250 o 450 m alcance distancia de
   combate.
2. **Las bajas del atacante bajan con cansancio activo a 250-450 m**, al revés
   de lo que uno esperaría de "pelea peor". La explicación: el cansancio también
   suma a la fracción de bajas percibida para la moral, así que el atacante
   colapsa (huye) más rápido, y se lo mide en el momento del colapso, antes de
   acumular tantas bajas como en la corrida sin cansancio. La tropa exhausta se
   quiebra y se retira antes de que la maten, no que sufra menos combate. Es una
   interacción real entre dos mecánicas (cansancio y moral) que no se había
   anticipado al diseñar ninguna de las dos por separado.

Se bajó `cansancio_por_marcha` de 0,02 a 0,01 (queda como default) y se repitió
la corrida:

| distancia inicial | cansancio | gana atacante | bajas atacante |
|---|---|---|---|
| 100 m | no | 23,2% ± 1,3% | 20,6% ± 0,2% |
| 100 m | sí | 13,1% ± 1,1% | 21,3% ± 0,1% |
| 250 m | no | 10,0% ± 0,9% | 22,0% ± 0,1% |
| 250 m | sí | **0,0% ± 0,0%** | 19,5% ± 0,1% |
| 450 m | no | 9,7% ± 0,9% | 22,1% ± 0,1% |
| 450 m | sí | **0,0% ± 0,0%** | 18,2% ± 0,1% |

Mejora la gradación a 100 m (23,2% a 13,1%, antes caía a 8,2%), pero 250 m y
450 m siguen saturando a 0%. Bajar más `cansancio_por_marcha` seguramente
seguiría corriendo el punto de saturación, pero en algún punto el problema deja
de ser ese parámetro solo: `moral_colapso_umbral=0,15` (calibrado en fase 1,
sin cansancio) ya es bastante bajo, y sumarle cualquier penalidad constante de
cansancio empuja rápido hacia el colapso. No se seteó un valor "que ande bien"
por prueba y error indefinido; se documenta el límite y se deja para un barrido
de sensibilidad conjunto (cansancio x moral) en fase 6 si hace falta.

## Sabido vs. supuesto

**Con fuente (cualitativo):** que marchar y combatir cansa, y que el cansancio
empeora el desempeño, es sentido común militar documentado en la doctrina de la
época (por eso existían las columnas de marcha con descansos programados). No
hay cifra de fuente para cuánto exactamente.

**Inventado, sin calibrar:** los seis parámetros numéricos
(`cansancio_por_marcha`, `cansancio_por_disparo`, `cansancio_recuperacion`,
`cansancio_penal_punteria`, `cansancio_penal_recarga`, `cansancio_penal_moral`)
no tienen fuente ni fueron ajustados contra ningún dato. El hallazgo de
saturación de arriba sugiere que al menos `cansancio_por_marcha` está lejos de
un valor razonable para estudiar el fenómeno con gradualidad.
