# Diseño experimental fijado

Piloto: 3 sesiones por cada una de 15 celdas, semillas 100–102, 8 escenarios.
No se escogen límites por el beneficio piloto. Estudio: 200 sesiones por celda,
semillas 10000–10199, 32 escenarios, 455 por jugador, 50 manos, alpha .90.
Total: 3000 sesiones. Se conservan todas, incluidas pérdidas y ruinas.

Cinco estrategias: fija estable, máximo beneficio sin límite, CVaR<=2, <=10 y <=30.
Tres rivales: estable; loose (error respecto del estable estimado); estable hasta
mano 25 y loose desde 26. La planificación siempre asume estable. No se afirma
que estos rivales sean representativos de personas ni que haya aprendizaje.
La política `minrisk` y los casos de emergencia se ejecutan aparte como demostración
funcional; no se mezclan con las 15 celdas principales.

Los mazos se obtienen de `Random('deal-v1:semilla:mano')` y no consumen aleatoriedad
de las políticas. Las semillas de escenarios dependen de sesión, mano, paso y actor
mediante otro prefijo. Las estrategias comparten mazos incluso si divergen sus
acciones. Los pares son sesiones con igual semilla frente al mismo rival, no manos
con idéntico estado (que pueden divergir). Se reinicia todo entre sesiones.

## Estadística

Ganancia media, desviación muestral, error estándar s/sqrt(N), CVaR de −G, frecuencia
de pérdida/ruina, drawdown medio y manos medias se calculan en el evaluador original.
Las trayectorias extienden cada saldo terminal hasta la mano 50: no hay eliminación
de sesiones arruinadas. `sessions.csv` permite revisar cada observación final.

`paired.csv` usa diferencias por semilla contra fija. El intervalo media ±1.96*SE
es una aproximación normal; no corrige comparaciones múltiples ni garantiza cobertura
exacta. `uncertainty.csv` ofrece percentiles 2.5/97.5 aproximados (estadísticos de
orden 25 y 975) de 1000 remuestreos de sesiones completas con reemplazo, semillas
separadas, tanto para media como CVaR. No se remuestrean manos como independientes.
Los intervalos bootstrap son descriptivos, especialmente frágiles en colas o masa
en ruina. N=200 y alpha=.90 equivalen a 20 sesiones en cola; no bastan para afirmar
estabilidad general ni extrapolar a rivales nuevos.

`diagnostics.csv` muestra decisiones optimizadas, inviabilidad, emergencia, tiempo
medio y duración por celda. En `profit`, exceso de riesgo es respecto del umbral
comparativo 10: es una referencia sin esa restricción, no una política factible.
En las estrategias con riesgo se comprueba el umbral propio. En fija no se inventan
predicciones: el denominador de decisiones predichas es cero.

El tiempo es medido, no reproducible bit a bit; rankings en caché y orden de celdas
pueden afectarlo. Cartas, acciones y ganancias sí son deterministas en el entorno
registrado. No se afirma reproducibilidad entre cualquier versión futura de Python.

## Archivos

`summary.csv`: métricas; `uncertainty.csv`: intervalos; `paired.csv`: diferencias;
`trajectories.csv`: evolución; `diagnostics.csv`: control local y tiempos;
`manifest.json`: tamaño, semillas, configuración y duración;
`report.html`: tabla y evolución; `risk-return.svg` y PNG: beneficio frente a CVaR con
intervalos marginales bootstrap; `trajectories.svg` y PNG: trayectorias; `best-responses.svg`: referencia de exposición.

Las figuras exportables se generan con Matplotlib desde los CSV compactos:
`python -m poker.figures results/study`. No es necesario repetir las simulaciones.
Los intervalos horizontales/verticales no son una región de confianza conjunta.
Beneficio y R=30 se dibujan juntos porque el límite 30 es redundante en esta
abstracción.

«Rival estable» no significa modelo perfectamente especificado: incluso en esa
celda se ignora el rango condicionado por apuestas y se aproxima la continuación
propia mediante una regla fija. La celda loose añade un cambio de regla rival a
esas aproximaciones preexistentes. No atribuir todo error predictivo a un único
parámetro ni interpretar la comparación como calibración con datos humanos.
