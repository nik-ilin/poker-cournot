# Proyecto I: evaluación de estrategias de póker

Actualización del 10 de octubre de 2026. Sustituye el estudio activo de Cournot por un evaluador de sesiones de póker. El código de Cournot se conserva como alternativa anterior; sus fórmulas no se aplican al póker.

## Decisiones recibidas y supuestos

La captura del equipo indica fichas de valores 1, 5, 10, 25 y 50, cinco de cada tipo, y un horizonte propuesto de 50 manos.

Si esa dotación corresponde a cada jugador, el capital inicial individual es 5×(1+5+10+25+50)=455 unidades, repartidas en 25 fichas físicas. Esta interpretación está marcada como provisional en `config.json`.

Para que el evaluador tenga un contrato concreto se propone: dos jugadores, sin comisiones ni recompras, máximo 50 manos, fin anticipado cuando cualquiera alcanza capital cero. Son supuestos del código pendientes de acuerdo del equipo; la captura no confirma todos ellos. La variante, las apuestas permitidas, las aportaciones iniciales, el tratamiento de apuestas no cubiertas y los empates siguen pendientes. Las denominaciones de fichas no son automáticamente los tamaños de apuesta permitidos.

El evaluador comprueba saldos, continuidad y final de sesión bajo este contrato. No comprueba la legalidad de las jugadas: eso corresponde al simulador de tus compañeros. Si el equipo adopta otras reglas, habrá que ajustar estas comprobaciones antes de usarlo.

## Tu trabajo y las entregas del equipo

1. El responsable del modelo entrega las reglas, el simulador y las definiciones de beneficio y riesgo.
2. El responsable de la optimización entrega una estrategia ejecutable: una regla que transforma la información disponible en probabilidades de acción. Debe documentar objetivo, restricciones, método, versión y, si existe, certificado de optimalidad.
3. El simulador enfrenta esa estrategia a rivales especificados y exporta una fila después de cada mano liquidada.
4. Tu evaluador recibe esos registros y compara resultados por estrategia, rival y condición experimental.

Una estrategia o una matriz de probabilidades por sí sola no basta para obtener el beneficio de 50 manos: hace falta el motor del juego que produzca las trayectorias. Este paquete cubre la etapa 4. No implementa un motor de póker ni resuelve una nueva optimización; hacerlo requeriría conocer la variante y las reglas completas.

## Contrato de entrada

[plantilla_manos.csv](plantilla_manos.csv) contiene los encabezados:

```csv
strategy,opponent,condition,session_id,hand,bankroll_1,bankroll_2
```

| Columna | Contenido |
|---|---|
| strategy | Identificador de nuestra estrategia y su versión/configuración |
| opponent | Identificador de la política rival |
| condition | Condición experimental, por ejemplo rival estable, error de estimación o cambio de política |
| session_id | Identificador único dentro de la combinación anterior |
| hand | Mano terminada, empezando por 1 y sin saltos |
| bankroll_1 | Nuestro saldo después de liquidar completamente la mano |
| bankroll_2 | Saldo rival después de liquidar completamente la mano |

Las filas de una sesión deben representar todos sus resultados hasta la mano 50 o hasta capital cero de un jugador. No se admiten sesiones incompletas como si fueran resultados finales. Los saldos no pueden ser negativos y deben sumar 910 en la configuración inicial propuesta. No introducir saldos con fichas todavía en el bote.

El programa trabaja con valor agregado del capital, no con un inventario físico de denominaciones. Se presupone que el simulador permite los cambios de fichas necesarios; si hay restricciones de inventario, deben implementarse allí.

Para estudiar distintos límites de riesgo, incluirlos en los identificadores de estrategia y documentar su valor y unidad. `risk_limit` en el JSON es un umbral común opcional de CVaR de pérdida por sesión, no un parámetro que optimice el evaluador. Dejarlo en `null` mientras no esté acordado. Si cada estrategia tiene un límite distinto, ejecutar evaluaciones separadas con su configuración correspondiente antes de interpretar los incumplimientos.

## Ejecutar

Python 3.10 o posterior, sin paquetes externos. Abrir la terminal en esta carpeta.

Para aprender el formato sin esperar al equipo:

```bash
python3 estudio.py --config config.json --example --out resultados_formato_01
```

Esta opción crea trayectorias aritméticas artificiales, etiquetadas como `DEMO_NO_POKER`. No simula repartos, apuestas ni políticas legales y sus cifras no sirven para defender una estrategia. Incluye finales anticipados para ilustrar su registro.

Para estudiar las simulaciones del equipo:

```bash
python3 estudio.py --config config.json --hands manos_equipo.csv --out resultados_equipo_01
```

Cada ejecución debe utilizar una carpeta nueva. Abrir `informe.html` para ver la tabla y el gráfico de capital medio. Es un informe estático, no una mesa interactiva. Si una entrada es inválida, el programa lanza un error; la carpeta recién creada puede permanecer, por lo que se debe elegir otro nombre al repetir.

## Matemáticas: qué mide cada resultado

Sea B0=455 y tau el instante final, como máximo 50 manos. En cada sesión j:

\[
G_j=B_{1,\tau,j}-B_0,\qquad L_j=-G_j.
\]

### Ganancia y dispersión

Con N sesiones completas:

\[
\widehat\mu=\frac1N\sum_jG_j.
\]

El resumen incluye desviación típica muestral de G y su error estándar s/sqrt(N). El error estándar solo tiene la interpretación usual si las sesiones son independientes, comparables y de una misma distribución. Si el agente aprende entre sesiones sin reiniciarse, esa hipótesis puede fallar. El programa no impone un intervalo de confianza ni prueba significación estadística.

### CVaR de la sesión

\[
\widehat{\operatorname{CVaR}}_\alpha(L)=
\min_{\eta\in\mathbb R}\left[\eta+\frac{1}{N(1-\alpha)}\sum_j\max(L_j-\eta,0)\right].
\]

El código ordena pérdidas de mayor a menor y toma exactamente la masa N(1-alpha), fraccionando la observación frontera. Todas las sesiones tienen el mismo peso. Si los datos provienen de muestreo ponderado o importance sampling, esta implementación no debe usarse sin modificar los pesos.

CVaR mide aquí el resultado terminal de la sesión, no una mano. No se calcula sumando CVaR de manos. Puede ser negativo si incluso la peor cola tiene ganancias. No mide directamente las oscilaciones del capital dentro de la sesión: para eso se incluye drawdown.

`tail_equivalent_sessions` muestra N(1-alpha). Con N=100 y alpha=0.95, solo hay masa equivalente a cinco sesiones en la cola: una cifra de CVaR puede ser muy inestable aunque el programa la calcule exactamente para la muestra. No hay un tamaño muestral universalmente suficiente; estudiar estabilidad aumentando sesiones y repitiendo semillas.

### Ruina, pérdida y caída máxima

La frecuencia de ruina es la fracción de sesiones donde nuestro capital llega a cero hasta la mano 50 incluida. La frecuencia de pérdida cuenta sesiones con G<0: perder parte del capital no equivale a arruinarse.

El máximo drawdown por sesión es:

\[
D_j=\max_{0\le t\le\tau}\left(\max_{0\le u\le t}B_{1,u,j}-B_{1,t,j}\right).
\]

Se mide en unidades de capital, no en porcentaje. El resumen informa su media entre sesiones. El peor beneficio observado es un extremo de la muestra, no una garantía frente a toda estrategia rival.

### Trayectorias con final anticipado

Después de terminar una sesión se conserva su saldo final hasta la mano 50 para calcular el capital medio por mano. Así se incluye a quienes se arruinaron y a quienes ganaron todo. Se exportan también mínimo y máximo por mano; estos extremos no son intervalos de confianza.

## Archivos de salida

- `sesiones.csv`: beneficio final, ruina, manos jugadas, razón del final y máximo drawdown de cada sesión.
- `resumen.csv`: medias, dispersión, CVaR, pérdida, ruina, drawdown y tamaño de cola por estrategia/rival/condición.
- `trayectorias.csv`: saldo medio, mínimo y máximo por mano, incluyendo saldos finales de sesiones terminadas.
- `informe.html`: tabla y gráfico con etiquetas y leyenda.
- `config_utilizada.json` y `manos_utilizadas.csv`: entradas conservadas para reproducir la evaluación. En la demo se guarda `manos_artificiales.csv`.

Si se proporciona R, `empirical_risk_excess=max(0,CVaR_muestral−R)` describe el incumplimiento en esa muestra. No certifica ni refuta por sí solo una restricción poblacional de riesgo: hay error de estimación.

## Diseño de tu estudio

Comparar estrategias bajo la misma variante, capital, horizonte y política rival. Definir antes del experimento qué se considera mejora: mayor ganancia, menor CVaR, menor ruina o un intercambio entre ellos.

1. **Rival estable:** comparar estrategias fijas en nuevas sesiones, separadas de las utilizadas para ajustar la política.
2. **Error sobre el rival:** el optimizador utiliza una estimación; el motor simula otra conducta real. Etiquetar cada magnitud de error en `condition`. El evaluador no inventa ni aplica ese error por su cuenta.
3. **Rival que cambia:** programar el cambio en el motor y documentar la mano en que sucede. Las acciones anteriores al cambio no pueden utilizar conocimiento de ese cambio futuro, salvo que forme parte explícita de la información del juego.
4. **Adaptación dentro de la sesión:** permitir aprendizaje solo a partir de observaciones ya disponibles. Para comparar sesiones independientes, reiniciar el estado de aprendizaje al principio de cada una.

Se pueden compartir secuencias de repartos predefinidas entre estrategias para una comparación emparejada; no basta con usar la misma semilla si las decisiones alteran el orden de consumo de números aleatorios. Este evaluador no calcula diferencias emparejadas ni presupone que `session_id` indique emparejamiento. Guardar semillas, versiones y configuración del motor en el registro experimental del equipo.

## Qué cambia respecto de Cournot

Se conservan las ideas de evaluar fuera de las condiciones de ajuste, analizar riesgo y comparar comportamientos. Desaparecen q1, la curva de precio y las identidades de sensibilidad b*q1*delta. En póker, el motor genera las ganancias a partir de repartos y acciones.

La variable de decisión del optimizador será una política de juego o sus parámetros. Su objetivo podría ser maximizar E[G] sujeto a CVaR_alpha(−G)<=R. Esto no demuestra que el problema sea convexo. El CVaR empírico es una función convexa de un vector de pérdidas dado, pero las pérdidas pueden depender de la política de forma no convexa.

Si se usa el modelo de matriz de pagos de Kuhn, la protección minimax en ganancia esperada es distinta del CVaR del capital tras 50 manos. Es necesario elegir cuál se optimiza y cuál se evalúa. No se trasladan las demostraciones KKT o de concavidad de Cournot al póker sin una nueva formulación.

## Estado

Código y documentación preparados; no ejecutados ni probados en esta actualización. No hay resultados reales del equipo importados. Las reglas pendientes deben confirmarse antes de presentar conclusiones académicas. No se han alterado los PDF fuente.
