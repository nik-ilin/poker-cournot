# Cómo estudiar las matemáticas

Leer primero [la formulación previa](FORMULACION.md) y [las reglas](REGLAS.md).

## Contabilidad: tres cantidades distintas

Sean B_i los fondos al inicio de mano, c_i lo ya aportado al decidir y F_i el
saldo al cerrar la mano. Beneficio neto X_i=F_i−B_i. Incremento desde la decisión
Y_i=F_i−(B_i−c_i)=X_i+c_i. Ganancia terminal de sesión G_i=B_i,tau−B_i,0.

Ejemplo: comienzas con 455, ya aportaste 2, igualas hasta 10 y ganas un bote 20.
Terminas con 465. X=10; Y=12. Si pierdes: F=445, X=−10, Y=−8. Si te retiras
antes de igualar: F=453, X=−2, Y=0. El bote no es capital adicional gratuito.
En cada mano y sesión X1+X2=0 y G1+G2=0. Las medias subjetivas de jugadores con
modelos distintos pueden no sumar cero; eso no cambia la contabilidad real.

## CVaR ponderado

Para pérdidas l_s=−X_s, pesos p_s>=0, suma p_s=1 y alpha<1:

CVaR_alpha(l)=min_eta [eta + sum_s p_s max(l_s−eta,0)/(1−alpha)].

Ordenar l de mayor a menor y consumir exactamente masa 1−alpha da la misma
expresión: para eta en un cuantil, todas las pérdidas superiores se incluyen,
las inferiores no, y la masa que falta procede de las iguales a eta. Esto explica
por qué promediar sin más las pérdidas mayores que un cuantil puede ser incorrecto.

Ejemplo l=(100,20,−10), p=(.05,.15,.80), alpha=.90:
CVaR=(.05*100+.05*20)/.10=60. Para l=(10,4,0), pesos iguales y alpha=.5,
se consume una observación y media: (10+.5*4)/1.5=8. Ambos son pruebas automáticas.
CVaR puede ser negativo cuando incluso la peor cola gana dinero.

## Optimización ejecutada

Para cada acción a, la continuación produce X_s(a). Se calculan media y CVaR
antes de actuar. J1 elige el máximo de la media entre acciones con CVaR<=R;
`minrisk` elige el menor CVaR entre acciones con media>=m. No hay derivadas,
convexidad asumida ni mezcla de acciones promediadas antes de medir riesgo.
La enumeración visita todas las acciones y por ello resuelve exactamente ese
problema finito muestral, sujeto a tolerancia 1e-9 en restricciones. No elimina
el error Monte Carlo ni el sesgo del modelo de continuación.

Las cartas rivales se muestrean uniformemente excluyendo cartas propias. La
continuación aplica `fixed` a ambos jugadores después de la acción candidata.
No ejecuta recursivamente el optimizador. En ejecución real el optimizador puede
volver a decidir si el rival aumenta: diferencia adicional entre planificación
y ejecución, registrada en las acciones efectivas. La política futura de J1 y
el rango condicionado a acciones observadas son aproximaciones del modelo.

Cada candidato usa los mismos escenarios, reduciendo ruido entre acciones.
Los escenarios de planificación son distintos del reparto real. Seleccionar
el mayor estimador puede introducir optimismo; evaluar sesiones con semillas
separadas evita usar el mismo resultado para elegir y medir la estrategia.
32 escenarios implican solo 3.2 escenarios equivalentes en la cola local:
precisión limitada, incluso cuando la enumeración es exacta.

Si el conjunto factible es vacío, se elige mínimo CVaR y después mayor media.
Eso es una emergencia legal, nunca una solución factible. Con R>=2 siempre existe una alternativa factible en los estados alcanzables
de esta ronda: fold pierde como máximo la ciega 2; si no hay deuda, el call de
la grande cierra la ronda con exposición como máximo 2. Con límites inferiores o m=5
puede fallar. No se confunde excepción informática con conjunto vacío.

## Horizonte y equilibrio

No existe aquí una demostración que convierta CVaR por decisión en una cota de
CVaR de sesión. La dependencia de manos, el cambio de saldos y la política
invalidan sumar automáticamente límites locales. Ruina es B1=0; drawdown es
max_t(max_{u<=t} B1,u−B1,t), medido entre manos liquidadas (no intramano).

El juego de exposición se analiza aparte con q1,q2 enteros entre 0 y 30,
A=2+min(q1,q2) y probabilidades ficticias (.3,.1,.6). Sus mejores respuestas
son conjuntos: se guardan todos los empates. Para cada par factible se comprueba
max_desviación(mu1_desv−mu1)<=1e-9 y max_desviación(R2−R2_desv)<=1e-9.
Las desviaciones también deben cumplir la restricción propia. Al depender estas
del rival, se trata de equilibrio generalizado del juego finito. No encontrarlo
por enumeración descarta ese juego finito especificado, no el continuo ni otras
probabilidades. Las dos correspondencias se dibujan en ejes comunes (q1,q2).

El estudio económico cuadrático en `estudio-cournot/` sigue siendo otro modelo,
con demanda inversa y costes: sus conclusiones no se trasladan al póker.

## Referencia primaria

Rockafellar, R. T. y Uryasev, S. (2002), *Conditional Value-at-Risk for General
Loss Distributions*, Journal of Banking & Finance 26(7), 1443–1471.
[Manuscrito de los autores, versión 28-11-2001](https://sites.math.washington.edu/~rtr/papers/rtr187-CVaR2.pdf).
Fundamenta el tratamiento de distribuciones discretas y la fracción del átomo
de probabilidad en la frontera de la cola. Sus resultados de convexidad exigen
hipótesis sobre pérdidas y distribución: no convierten automáticamente nuestra
política discreta en un problema convexo. Los ejemplos, pruebas y el modelo de
póker de este repositorio son desarrollos de la integración, no resultados del artículo.
