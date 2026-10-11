# Qué se comprueba y qué no

Las pruebas de `tests/test_core.py` cubren las nueve categorías, rueda, kickers y
empate sobre mesa; CVaR manual ponderado, cola fraccionaria, pérdidas negativas e
inputs inválidos; mazos sin duplicados y reproducibles; árboles completos de
acciones para cinco pares de capitales y ambas posiciones; conservación, límites,
all-in, devolución, pagos y terminalidad; sesiones completas, beneficio acumulado,
exportación al evaluador, cola y trayectorias sin sesgo de supervivencia; privacidad
de observación; selección exhaustiva en ejemplos pequeños; un rollout contrastado
con cálculo manual que incluye fold; inviabilidad; importaciones sin efectos.

`tests/test_ui.py` ejecuta Streamlit mediante AppTest: carga, controles, sesión real
de dos manos y cambio a observador. Se repite con los CSV principales presentes
antes de publicar. Es una comprobación automatizada, no revisión manual en todos
los navegadores ni validación humana por el equipo.

`ruff` comprueba errores básicos, importaciones y nombres; `compileall` comprueba
sintaxis; `pip check` verifica consistencia de dependencias. La comparación AST de
las seis funciones del evaluador de cartas con beep confirma que son las mismas
funciones, aunque extraídas y formateadas. No se ha enumerado aquí la distribución
de todas las manos posibles de siete cartas.

El conjunto principal se verifica también como datos: número de sesiones/celdas,
conservación en todas las filas, acciones legales registradas, factibilidad local,
coincidencia entre la acción seleccionada y la ejecutada, identidad de repartos
entre estrategias y coincidencia de ganancias de beneficio y R=30. La reproducción
adicional de sesiones seleccionadas usa el código final, excluyendo tiempos.

No confundir estas comprobaciones con optimalidad del juego completo, estimación
sin error Monte Carlo, garantía poblacional de riesgo ni capacidad de ganar a
jugadores humanos. Los scripts de Cournot económico histórico no forman parte
del producto de póker probado; permanecen disponibles como material separado.

## Ejecución final

En la validación previa a esta ampliación: 36 pruebas superadas, Ruff sin errores,
compilación correcta y dependencias consistentes. Evidencia de esa tanda en
[validation.txt](../results/validation.txt).
Auditoría del estudio: 150000 manos, 3000 sesiones, 15 celdas, 600 pares
beneficio/R=30 y 30 sesiones reproducidas. Figuras PNG inspeccionadas visualmente;
no se atribuye esa revisión automática a los compañeros.

## Extensión Unidad 1

`tests/test_unit1.py` añade equivalencia entre ordenación/primal/dual, ejemplo
manual con cola fraccionaria, KKT, probabilidades desiguales y nulas, empates,
pérdidas negativas, distribución degenerada, entradas inválidas, pérdidas de
acciones del motor, escenarios congelados y anidados, monotonía de `V(R)` en el
problema factible y separación de inviabilidad/emergencia. La tanda de estabilidad
completa se ejecuta como experimento reproducible, no se usa como prueba unitaria.

Los LP deben terminar en estado óptimo de HiGHS y satisfacer residuos KKT y brecha
primal–dual dentro de `1e-8 + 1e-8*escala`. El ejemplo `(100,20,-10)`, pesos
`(.05,.15,.80)`, `alpha=.90` devuelve `eta=20`, `u=(80,0,0)`, `z=(.5,.5,0)` y
valor 60 por ordenación, primal y dual. Se prueban además cinco distribuciones
manuales y cuatro acciones de una observación del simulador. Esto certifica el
cálculo del CVaR en las distribuciones comprobadas, no el modelo del rival ni el
óptimo del juego de póker.

La sensibilidad congela 128 escenarios y comprueba los umbrales inmediatamente
antes, en y después de cada CVaR de acción. El estudio S=32/128/512 compara muestras
prefijadas anidadas y evalúa las acciones en escenarios independientes; S=512 es
referencia de mayor tamaño, no valor exacto. Ver tablas y semillas en
[`results/unit1/`](../results/unit1/).

En la validación final de esta ampliación: **59 pruebas superadas** en la suite
completa (`python -m pytest -q`), incluidos AppTest de Streamlit; `compileall`,
`pip check` y `ruff check .` pasaron. Para ello se ordenaron imports y se
reemplazaron dos lambdas locales de coordenadas por funciones equivalentes en
`estudio-cournot/estudio.py`; no se alteraron fórmulas ni lógica del estudio.
