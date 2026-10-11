# Formulación previa a la implementación

Decisión de integración, 11-10-2026. No es no-limit Hold’em completo.
Se conserva la evaluación de las mejores cinco de siete cartas del equipo.
Dos jugadores; una ronda preflop; posiciones alternas; pequeña actúa primero.
Cada jugador puede retirarse si debe fichas, igualar/pasar o elevar el total
comprometido a 10 o 30. Como máximo un aumento por mano; tras él solo fold/call.
Si ambos igualan o pasan termina la ronda. Se completa la mesa y se liquida.
Los aumentos se limitan al capital efectivo de ambos y son enteros. La parte
no cubierta de ciegas se devuelve antes de liquidar. Sin botes laterales.
Empate divide el bote igualado (siempre par). All-in impide más apuestas.

## Información y escenarios
La observación contiene cartas propias, aportaciones, saldos iniciales,
posición, historial público y acciones legales; nunca cartas rivales ni mazo.
En cada decisión se muestrean uniformemente dos cartas rivales y cinco
comunitarias sin reemplazo del conjunto desconocido. El historial previo
NO actualiza el rango rival: aproximación explícita, especialmente después
de un aumento. Un rival de continuación fijo toma decisiones según una
puntuación preflop de sus propias cartas; nunca según cartas ajenas.
Después de la acción candidata ambos usan esa regla de continuación hasta
fold/showdown. Por tanto se simula la probabilidad de retirada, no solo equity.
Las acciones candidatas comparten escenarios y números aleatorios.

## Programa finito
Variable a en conjunto legal A(o), acción determinista. Escenarios s=1,...,S
con pesos 1/S. X_s(a)=saldo final menos saldo al inicio de la mano, en unidades
de fichas. Incremento desde decidir = X_s(a)+aportación ya realizada; se registra
aparte. Ganancia de sesión = saldo final menos capital inicial.
Jugador 1: maximizar media X sujeto a CVaR_alpha(-X)<=R.
Jugador 2 (política opcional minrisk): minimizar CVaR_alpha(-X) sujeto a media X>=m.
CVaR es la media de la peor masa 1-alpha, fraccionando la frontera.
Enumeración de TODAS las acciones legales: óptimo del problema muestral finito,
no óptimo de Hold’em ni de la sesión. No se necesita ni se afirma convexidad.
Empates: menor riesgo, después orden de acciones. Tolerancia absoluta 1e-9.
Si no existe acción admisible: inviabilidad demostrada SOLO en este conjunto y
muestra; elegir menor CVaR (desempate mayor media), registrar emergencia.
Errores de ejecución se propagan; nunca se convierten en inviabilidad.

Horizonte de planificación: resto de una mano. Evaluación: hasta 50 manos.
La restricción local no garantiza CVaR de sesión, ruina ni protección minimax.
No se optimizan mezclas aleatorias. No se estima equilibrio en este simulador.

## Referencia de exposición
A=2+min(q1,q2), ganancias (A,0,-A) y opuestas bajo probabilidades comunes.
mu1+mu2=0; exigir mu2>=5 fuerza mu1<=-5 en cada punto factible.
No se alteran probabilidades para evitar este conflicto. Restricciones dependen
del rival: equilibrio generalizado. Se enumeran cantidades enteras y todas las
mejores respuestas empatadas, verificando factibilidad y desviaciones con
1e-9. Certificado solo del juego finito y distribución especificada; no de
cantidades continuas ni del póker con información privada.

## Notación formal del programa implementado

Para observación permitida \(o\), acción \(a\in\mathcal A(o)\) y escenarios
\(\omega_s\sim\widehat P(\cdot\mid o)\), sea \(T(o,a,\omega_s;\rho)\) la
liquidación obtenida al ejecutar la acción y continuar con la regla fija \(\rho\).
El beneficio de mano del actor es
\(X_s(a)=T_i(o,a,\omega_s;\rho)-B_{i,\mathrm{inicio}}\).

\[
\widehat\mu(a)=\frac1S\sum_{s=1}^S X_s(a),\qquad
\widehat C_\alpha(a)=\min_{\eta\in\mathbb R}
\left\{\eta+\frac{1}{S(1-\alpha)}\sum_{s=1}^S[-X_s(a)-\eta]_+\right\}.
\]

\[
 a_1\in\arg\max_{a\in\mathcal A(o):\widehat C_\alpha(a)\le R}\widehat\mu(a),
 \qquad
 a_2\in\arg\min_{a\in\mathcal A(o):\widehat\mu(a)\ge m}\widehat C_\alpha(a).
\]

La probabilidad estimada de una retirada se induce por \(\rho\) aplicada a la mano
rival simulada, con las aportaciones públicas de la acción candidata. No se toma
una probabilidad de victoria fija para todas las acciones. \(\widehat P\) ignora
la selección de rango inducida por acciones anteriores: esa es una hipótesis
aproximada explícita, no una distribución posterior obtenida por Bayes.
