# Informe fase 4a: munición limitada

## Qué se construyó

Cada soldado arranca con `municion_inicial` cartuchos (`Config.municion_activa`,
default `False`). Cada disparo resta uno; al llegar a 0 el soldado deja de poder
disparar (sigue en la formación, sigue pudiendo ser alcanzado, pero no dispara
más). No hay recarga desde un carro de munición ni retirada automática a
rearmarse: al agotarse, el soldado queda "parado" el resto de la batalla salvo
que huya por moral. No hay melé todavía, así que no se modela la opción de
"cargar a la bayoneta" que menciona `docs/diseno.md` para cuando se acaba la
munición.

## Verificación

39 tests, todos pasando (35 anteriores + 4 nuevos): regresión bit a bit con el
flag apagado, un soldado se queda sin munición exactamente en 0 (nunca negativo)
y deja de disparar, con 0 balas de arranque nadie dispara pese a condiciones de
impacto garantizado, y limitar la munición no puede producir más bajas que
dejarla libre (mismo seed, comparación pareada).

## Rendimiento

200 batallas, 100 por bando: 3,63 s sin límite, 3,48 s con munición activa. Sin
overhead.

## Qué falta para la pregunta de investigación real

`docs/diseno.md` pregunta si la batalla "pasa de una ley a otra" cuando se acaba
la munición (¿deja de comportarse como Lanchester cuadrática/lineal y pasa a
otra cosa, por ejemplo un empate por agotamiento?). Esa es una pregunta de fase 6
(necesita corridas de Lanchester con munición limitada variando la dotación
inicial, con barras de error), no algo que se responda con la verificación de
esta fase. Acá solo se confirmó que el mecanismo hace lo que tiene que hacer;
la pregunta de investigación queda pendiente para cuando el motor esté completo.

## Sabido vs. supuesto

**Con fuente parcial:** 60 cartuchos es una cifra que aparece con frecuencia en
fuentes de divulgación sobre la dotación de un soldado de infantería de la época
(caja de cartuchera napoleónica), pero no se verificó contra una fuente primaria
específica ni se confirmó que fuera estándar entre todos los ejércitos y años del
período. Se deja marcada como tal en el código (`# cifra comun citada... sin
verificar con fuente primaria`), no como un hecho confirmado.

**Inventado:** la regla de que agotar la munición simplemente detiene al soldado
(sin retirada automática, sin opción de bayoneta) es una simplificación de
alcance, no un hallazgo ni una fuente histórica.
