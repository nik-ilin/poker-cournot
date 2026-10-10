# Estudio de Cournot: beneficio, CVaR y error de estimación

**Alternativa anterior.** Desde la actualización del 10 de octubre de 2026, el trabajo activo se encuentra en [estudio de póker](../estudio-poker/README.md). Este código se conserva como referencia y no procesa resultados de póker.

Material de trabajo para la aportación de Nikolai al Proyecto I. Modelo propuesto en la conversación; no se presenta como requisito confirmado del temario. Los datos incluidos son ficticios. Código preparado, no ejecutado ni probado en esta entrega.

## 1. Pregunta de investigación y alcance

¿Cómo cambia el beneficio de una estrategia de producción cuando nos equivocamos sobre la producción del rival, y qué protección proporciona un límite de CVaR?

Controlamos una cantidad determinista `q1`, elegida antes de conocer el escenario. El rival y la demanda se representan mediante una distribución conjunta discreta. Se compara una cantidad fija, una decisión que maximiza beneficio esperado sin límite de riesgo y las decisiones con límite de riesgo enviadas por el compañero 2.

Este estudio toma el comportamiento del rival como entrada. No calcula por sí mismo un equilibrio de Cournot ni simula que el rival observe nuestra decisión y reaccione. Tampoco determina la estrategia óptima del jugador 2. Si sus cantidades se obtienen de otro modelo, el equipo debe documentar cómo se han obtenido sin introducir información futura en la decisión del jugador 1.

## 2. Entregas de los compañeros

### Compañero 1: archivo JSON de escenarios y parámetros

Usar [escenarios_ejemplo.json](escenarios_ejemplo.json) como plantilla.

| Campo | Significado |
|---|---|
| `description` | Procedencia, supuestos y versión de los datos |
| `b` | Pendiente positiva de la demanda inversa, común a todos los escenarios |
| `c1` | Coste marginal constante del jugador 1 |
| `q1_max` | Capacidad de producción del jugador 1 |
| `alpha` | Nivel de CVaR, entre 0 y 1 |
| `q_fixed` | Producción fija de referencia, elegida antes del estudio |
| `risk_limits` | Límites R que se estudiarán |
| `rival_errors` | Desplazamientos de la producción real del rival respecto de la estimada |
| `scenarios` | Filas con `id`, `probability`, `a`, `q2` |

Cada fila es un escenario conjunto: demanda y producción rival suceden juntos con esa probabilidad. No se supone independencia entre ambas variables. Las probabilidades deben ser positivas y sumar 1. Las unidades deben ser coherentes: producción en unidades de producto, precios y costes en dinero/unidad, beneficios y R en dinero.

El compañero 1 debe justificar los escenarios, las probabilidades, el horizonte de decisión y los parámetros. Si también ha programado el cálculo de beneficios/CVaR, este contrato permite comparar sus cifras con las del evaluador posteriormente. No se ha realizado esa comparación todavía.

### Compañero 2: archivo CSV de decisiones

Entregar exactamente una fila por límite R del JSON, calculada usando los escenarios de planificación, sin desplazamientos del rival:

```csv
risk_limit,q1,status,method
-650,,infeasible,mi_optimizador
-620,27.23606797749979,optimal,mi_optimizador
-610,28.872983346207416,optimal,mi_optimizador
-600,30,optimal,mi_optimizador
-500,30,optimal,mi_optimizador
```

Estos valores corresponden únicamente al ejemplo ficticio. Estados admitidos:

- `optimal`: el compañero afirma que ha encontrado y justificado el óptimo.
- `feasible`: entrega una decisión factible, sin afirmar optimalidad.
- `infeasible`: afirma que ha establecido que no existe solución factible.
- `unknown`: no ha podido resolver o clasificar el problema.

En `infeasible` y `unknown`, `q1` debe estar vacío. Un fallo del optimizador debe etiquetarse como `unknown`, no como `infeasible`.

El evaluador comprueba capacidad y riesgo de las cantidades recibidas en los escenarios de planificación. No certifica la optimalidad ni las afirmaciones de inviabilidad. Para la entrega académica, el compañero debe acompañar `optimal` de su método, tolerancias y justificación matemática. Las derivadas KKT y los multiplicadores no son necesarios para ejecutar este evaluador; sirven para interpretar y justificar los resultados.

## 3. Ejecutar el ejemplo sin esperar a los compañeros

Se necesita Python 3.10 o posterior. Solo se utiliza la biblioteca estándar: no hay paquetes que instalar. Abre una terminal en esta carpeta y ejecuta:

```bash
python3 estudio.py --scenarios escenarios_ejemplo.json --demo --out resultados_demo_01
```

`--demo` genera las decisiones mediante una solución analítica específica de este modelo. No representa resultados aportados por tus compañeros. Usa un directorio de salida nuevo cada vez; el programa no sobrescribe resultados anteriores.

Para utilizar sus archivos:

```bash
python3 estudio.py --scenarios escenarios_equipo.json --decisions decisiones_equipo.csv --out resultados_equipo_01
```

Abrir `informe.html` en un navegador. El informe es estático, con gráficos SVG; no es la simulación interactiva de póker que se discutió como alternativa.

## 4. Matemáticas del modelo

### Precio, beneficio y decisión

En el escenario s:

\[
P_s(q)=a_s-b(q+q_{2,s}),\qquad
\pi_s(q)=q[a_s-c_1-bq_{2,s}-bq].
\]

Definimos \(d_s=a_s-c_1-bq_{2,s}\). Entonces:

\[
\mu(q)=\sum_s p_s\pi_s(q)=\bar d q-bq^2,
\qquad \bar d=\sum_s p_s d_s.
\]

Como \(\mu''(q)=-2b<0\), el objetivo es estrictamente cóncavo. El óptimo sin límite de riesgo es:

\[
q_0=\min\{\bar q_1,\max\{0,\bar d/(2b)\}\}.
\]

El programa exige que todos los precios sean no negativos en todo el intervalo de capacidad y en todos los escenarios de evaluación. No introduce un suelo de precio automáticamente, porque eso cambiaría el modelo y sus derivaciones.

### Qué calcula CVaR

La pérdida es \(\ell_s=-\pi_s\). CVaR es la media de las peores pérdidas en una cola de probabilidad \(1-\alpha\). En el caso discreto se utiliza la formulación:

\[
\operatorname{CVaR}_{\alpha}(\ell)=
\min_{\eta\in\mathbb R}\left[\eta+\frac{1}{1-\alpha}\sum_s p_s\max(\ell_s-\eta,0)\right].
\]

`tail_mean` calcula ese mismo valor ordenando las pérdidas de mayor a menor y tomando exactamente la probabilidad necesaria, fraccionando el último escenario si hace falta. No redondea el número de escenarios ni promedia todos los escenarios por encima de un cuantil sin ajustar sus masas.

Ejemplo manual: pérdidas 100, 20 y −10 con probabilidades 0.05, 0.15 y 0.80. Para alpha=0.90, la cola tiene masa 0.10. CVaR=(0.05×100+0.05×20)/0.10=60. Este ejemplo es explicativo, no una prueba automatizada ejecutada.

Un CVaR negativo es posible: CVaR=−600 significa que el beneficio medio en la peor cola es 600. Un límite R=−620 es más exigente que R=−600. No equivale a imponer un beneficio de 620 en cada escenario. Si se quisiera estudiar la pérdida truncada max(0,−beneficio) o una pérdida respecto a un objetivo, habría que cambiar el contrato, las fórmulas y el optimizador.

### Por qué la demo tiene solución analítica

Para q no negativa, los menores valores de d generan las mayores pérdidas. Sea \(d_{\mathrm{cola}}\) la media de los menores d en una masa de probabilidad \(1-\alpha\). Como b es el mismo en todos los escenarios:

\[
\operatorname{CVaR}_{\alpha}(-\pi(q))=bq^2-d_{\mathrm{cola}}q.
\]

Por tanto, el problema se reduce a:

\[
\max_{0\le q\le\bar q_1}\bar d q-bq^2
\quad\text{sujeto a}\quad bq^2-d_{\mathrm{cola}}q\le R.
\]

Con \(D=d_{\mathrm{cola}}^2+4bR\), si D es negativo no hay soluciones. Si D es no negativo, las raíces son:

\[
q_-=(d_{\mathrm{cola}}-\sqrt D)/(2b),\qquad
q_+=(d_{\mathrm{cola}}+\sqrt D)/(2b).
\]

Se intersecta [q_-,q_+] con [0,q1_max]. Si la intersección es vacía, el problema es inviable. Si no, el óptimo es la proyección de q0 sobre ese intervalo. Esta fórmula no se debe reutilizar sin derivación si cambiáis la función de costes, b entre escenarios, el precio o la dependencia del rival respecto de q1.

En el ejemplo: d=(50,60,70), media 60 y d_cola=50. Así, mu(q)=60q−q² y CVaR(q)=q²−50q. El mínimo CVaR posible es −625, alcanzado en q=25. R=−650 es inviable; con R=−620, el extremo superior factible es 25+sqrt(5), y con R=−600 el óptimo es q=30.

## 5. Tu experimento de error de estimación

El programa define:

\[
\delta=q_{2,s}^{\mathrm{real}}-q_{2,s}^{\mathrm{estimada}},
\qquad q_{2,s}^{\mathrm{real}}=q_{2,s}+\delta.
\]

Un delta positivo significa que el rival produce más de lo que esperábamos. Se aplica el mismo desplazamiento en todos los escenarios y se mantienen a y p. Es un experimento controlado sobre un error sistemático; no cubre todos los errores posibles de distribución o correlación.

Secuencia temporal:

1. Recibir los escenarios estimados.
2. Recibir o calcular las decisiones con esos escenarios.
3. Fijar las decisiones.
4. Cambiar delta para construir escenarios de evaluación.
5. Calcular beneficio, riesgo y diferencias con la referencia fija.

Nunca se recalcula la decisión utilizando el delta real. Hacerlo introduciría información futura en la estrategia.

Para una producción fija q, se cumplen estas identidades:

\[
\mu(q;\delta)=\mu(q;0)-bq\delta,
\qquad
\operatorname{CVaR}(q;\delta)=\operatorname{CVaR}(q;0)+bq\delta.
\]

Por tanto, las curvas de este experimento son lineales en delta. Una producción mayor genera mayor sensibilidad. Si S=R−CVaR(q;0) es la holgura prevista y q>0, el máximo desplazamiento positivo tolerable antes de incumplir el riesgo es:

\[
\delta_{\max}=S/(bq).
\]

Para q=0 no se utiliza esta división. Si la restricción está activa, S=0: cualquier desplazamiento positivo viola el límite bajo este modelo. Este es un límite de una restricción calculada con una distribución estimada, no una garantía robusta frente a cualquier distribución.

Otra derivación para tu informe: sin restricción de riesgo y con ambos óptimos interiores, el óptimo con información correcta cambia en −delta/2. La pérdida de beneficio de la decisión nominal respecto de esa referencia con información correcta es b×delta²/4. Esta identidad no se atribuye automáticamente a las decisiones con riesgo o capacidad activa. El programa no usa ese óptimo informado como estrategia disponible al jugador.

## 6. Qué archivos se obtienen

### evaluacion.csv

Una fila por límite R, estrategia y delta:

| Columna | Interpretación |
|---|---|
| `q1` | Cantidad decidida antes de observar el error |
| `planned_expected_profit`, `planned_cvar` | Resultados previstos con delta=0 |
| `expected_profit`, `cvar_loss` | Resultados en la distribución de evaluación |
| `worst_profit` | Mínimo beneficio entre los escenarios enumerados |
| `probability_loss` | Probabilidad de beneficio estrictamente negativo |
| `expected_price` | Precio esperado con esta estrategia y rival |
| `gain_vs_fixed` | Beneficio esperado menos el de la referencia fija en los mismos escenarios |
| `risk_excess` | max(0, CVaR−R), magnitud del incumplimiento |
| `risk_feasible` | Si CVaR cumple R dentro de la tolerancia numérica |

`worst_profit` solo se refiere a los escenarios enumerados, no a todos los sucesos posibles. Las estrategias fija y sin límite de riesgo pueden incumplir R: son referencias cuyo incumplimiento se muestra, no alternativas necesariamente admisibles. No se puede declarar superior una estrategia solo porque gane más si opera bajo restricciones distintas.

### frontera.csv

Muestra las decisiones del compañero 2 en los escenarios de planificación al variar R. Incluye holgura, actividad de la restricción y pendiente secante entre límites consecutivos con decisión disponible:

\[
\frac{V(R_{k+1})-V(R_k)}{R_{k+1}-R_k}.
\]

La columna `profit_secant` es una pendiente sobre un intervalo, no un multiplicador KKT exacto. Si ambas decisiones son óptimas, el intervalo es pequeño y la función valor es diferenciable con las condiciones de regularidad adecuadas, permite aproximar el valor marginal de relajar R. `secant_both_reported_optimal` indica si las dos filas fueron declaradas óptimas; no verifica esa declaración.

Con la convención de maximización L=mu(q)−lambda(CVaR(q)−R), lambda>=0, y bajo esas condiciones, V'(R)=lambda. Una restricción activa no implica necesariamente lambda estrictamente positivo. Por ejemplo, en q=30 y R=−600, el óptimo sin riesgo ya está sobre la frontera y el multiplicador puede ser cero.

### informe.html y entradas utilizadas

El HTML incluye tabla de decisiones y gráficos de beneficio, CVaR, exceso de riesgo y ganancia frente a la referencia fija. Incluye unidades y leyendas. Las líneas de referencias iguales para varios R se superponen.

Se guardan `escenarios_utilizados.json` y `decisiones_utilizadas.csv` para conservar las entradas del cálculo. El JSON incluye probabilidades normalizadas únicamente cuando la discrepancia con 1 está dentro de la tolerancia de redondeo.

## 7. Cómo está organizado el código

| Función | Papel |
|---|---|
| `read_model` | Lee y valida el contrato del compañero 1 |
| `tail_mean` | Calcula una media de cola ponderada exacta |
| `evaluate` | Calcula los resultados de una cantidad ya elegida |
| `coefficients` | Obtiene media y cola de d para el modelo cuadrático |
| `nominal_quantity` | Calcula la referencia óptima sin restricción de riesgo |
| `analytic_solution` | Resuelve el modelo sencillo usado en la demo |
| `read_decisions` | Lee las cantidades del compañero 2 y comprueba factibilidad prevista |
| `study` | Mantiene las decisiones y recorre errores y estrategias |
| `frontier` | Organiza sensibilidad al límite R y pendientes secantes |
| `report` | Genera el informe con gráficos |

Si los compañeros ya disponen de funciones Python, pueden exportar sus resultados con este formato; no necesitáis integrar sus optimizadores internamente para empezar. Cambiar la ecuación económica sí exige revisar `evaluate`, `coefficients`, `nominal_quantity` y la demo; no basta con cambiar el CSV.

## 8. Cómo convertir los resultados en tu sección del informe

1. Explica la pregunta, el modelo y la información disponible antes de decidir.
2. Deriva concavidad, la solución nominal y el efecto de delta.
3. Presenta las decisiones recibidas y la evidencia de optimalidad de tu compañero.
4. Describe el barrido de R y delta, manteniendo constantes las demás entradas.
5. Presenta beneficio y CVaR juntos, señalando inviabilidad e incumplimientos.
6. Explica el intercambio entre beneficio previsto, holgura de riesgo y sensibilidad al rival.
7. Reconoce que un desplazamiento uniforme, los escenarios finitos y un rival exógeno limitan las conclusiones.

Este estudio calcula expectativas exactamente sobre las distribuciones especificadas. No utiliza datos observados nuevos, no estima intervalos de confianza y no demuestra rendimiento empírico fuera de muestra. Si los escenarios son inventados, las conclusiones son experimentos numéricos sobre un modelo. La interpretación causal o empírica requeriría un diseño y datos adicionales.

## 9. Estado de entrega

- Código, contrato de entrada y datos didácticos preparados.
- Sin dependencias externas.
- No se han ejecutado el programa ni pruebas en esta entrega.
- No se han generado resultados ni integrado archivos reales del equipo todavía.
- La tolerancia absoluta interna es 1e-8; al cambiar mucho la escala monetaria se debe revisar junto con la precisión de los optimizadores del equipo.
