# Reglas e información

## Procedencia de la configuración

| Elemento | Procedencia | Estado |
|---|---|---|
| Cinco fichas de cada valor 1,5,10,25,50; capital 455 | `modelo` y conversación | Confirmado para cada jugador |
| Ciegas 1/2; 50 manos; alpha=.90 | Archivos originales y conversación | Valores por defecto |
| Sin comisiones ni recompras; fin por capital cero | Conversación | Implementado |
| Una ronda preflop, objetivos totales 10 y 30, un solo aumento | Decisión de integración | Abstracción, no regla de Hold’em completo |
| R=2,10,30; 32 escenarios; 200 sesiones/celda | Diseño de integración | No escogidos por rentabilidad observada |
| Beneficio mínimo 5 para `minrisk` | Archivo original y orientación solicitada | Restricción local, puede ser inviable |

No se simula inventario de denominaciones: se permite cambio ilimitado y apuestas
enteras. No hay apuestas de tamaño arbitrario, rondas postflop, recompras ni rake.
No se queman cartas: omitir quemadas invisibles conserva la distribución marginal
uniforme de cartas repartidas. No es un simulador general de no-limit Hold’em.

## Secuencia de una mano

1. Se conserva el saldo de la mano anterior; se reparte un mazo nuevo uniforme.
2. J1 pone pequeña en manos impares y J2 en pares. Cada ciega se limita al saldo.
3. La pequeña decide primero. Si debe dinero puede retirarse o igualar. Si no
   debe, `call` significa pasar. Si no hubo aumento, puede elevar su aportación
   total a 10 o 30, limitada al mínimo de los capitales iniciales de la mano;
   objetivos repetidos se deduplican y los que no elevan se eliminan.
4. Tras el primer aumento el rival solo puede retirarse o igualar. Sin aumento,
   dos actuaciones cierran la ronda; la grande puede elevar tras la igualación
   de la pequeña. Un all-in seguido de igualación cierra inmediatamente.
5. En retirada gana el otro; en showdown se escogen las mejores cinco de siete.
   Se devuelve la diferencia de aportaciones antes de repartir el bote igualado.
   Así no existen botes laterales ni fichas no cubiertas en juego.
6. El bote igualado vale dos veces la aportación mínima. En empate se divide
   exactamente; nunca hay ficha impar en ese bote. Los saldos finales son enteros.
7. Cada mano se registra una vez. El estado terminal no admite acciones.
   `settle` es una función pura: repetirla devuelve los mismos saldos, no abona
   el bote dos veces a un objeto mutable.
8. Al llegar al horizonte o a saldo cero de cualquiera termina la sesión.

Al reiniciar sesión se reinician capital, posición y cualquier estado de decisión.
Las políticas actuales no aprenden. Cambiar de rival en la mano 26 no modifica el
modelo estimado: estudia falta de adaptación, no un algoritmo adaptativo.

## Privacidad

`Observation` contiene solo cartas propias y `Public`: saldos iniciales,
aportaciones, actor, posición e historial de acciones. No contiene cartas rivales,
comunitarias futuras, semilla del mazo ni resultados futuros. La política recibe
una semilla separada para sus propios escenarios. El motor guarda ambas manos y
la mesa para auditoría; estos datos no se pasan a `decide`.

No hay comunitarias visibles antes de decidir en esta abstracción. La interfaz
separa predicciones preflop de resultados posteriores. En vista de jugador no
muestra cartas rivales ni predicciones del rival; en retirada oculta la mesa.
El observador tiene información completa y puede exportarla; no es una política.

## Rivales explicables

Puntuación h=(rango alto+rango bajo)/28 + .35 si pareja + .05 si mismo palo.
Umbral t: estable=.85, loose=.55, tight=1.05. Si hay aumento legal y h>=t,
se elige el mayor objetivo permitido. Si se enfrenta a un aumento y h<t−.2,
se retira; en otro caso iguala/pasa. La referencia fija usa el rival estable.
`changing` usa estable hasta la mitad del horizonte y loose después.
No son aproximaciones de jugadores humanos calibradas con datos.

`minrisk` permite aplicar al jugador 2 el objetivo de mínimo CVaR sujeto a media
mínima. En el estudio principal los rivales son reglas fijas, para no confundir
el problema de control contra un rival especificado con un equilibrio.
