# Módulos y contratos

| Archivo | Responsabilidad |
|---|---|
| `poker/cards.py` | Evaluación original de cinco/siete cartas y desempates |
| `poker/game.py` | Configuración, estados inmutables, acciones y liquidación |
| `poker/risk.py` | CVaR ponderado, validación de distribución |
| `poker/policy.py` | Reglas rivales, escenarios y enumeración de acciones |
| `poker/simulation.py` | Sesión, separación de streams y exportación |
| `poker/evaluation.py` | Adaptador del evaluador original de main |
| `poker/experiments.py` | Diseño fijo, métricas, incertidumbre y figuras |
| `poker/audit.py` | Auditoría exhaustiva de registros y reproducción seleccionada |
| `poker/figures.py` | Figuras exportables a partir de tablas compactas |
| `poker/exposure.py` | Juego de exposición y desviaciones exhaustivas |
| `poker/cli.py` | Comandos reproducibles |
| `app.py` | Interfaz Streamlit sobre registros reales |
| `tests/` | Pruebas unitarias, integración e interfaz |

`Config` centraliza capital, manos, alpha, escenarios y tamaños; ciegas 1/2
son reglas fijas de esta versión. `session` es una función sin estado de jugador
persistente. El caché de evaluación solo memoriza rankings deterministas, nunca
saldos o aprendizaje. El tiempo puede mejorar por caché; no comparar tiempos
como benchmark independiente de orden/hardware.

## CSV de manos

Se mantienen las siete columnas `strategy,opponent,condition,session_id,hand,
bankroll_1,bankroll_2`. Cada fila es posterior a liquidación. El evaluador anterior
acepta las columnas adicionales y exige continuidad, conservación y fin válido.

Campos añadidos: `seed`, `deal_id`, `profit_1`, `holes`, `board`, `events`, `paid`,
`pot`, `refund`, `folded`, `small`, `config`. Tuplas, listas y diccionarios se
serializan como JSON dentro del CSV. Las cartas son pares (rango 2–14,palo 0–3).
`folded` usa índices 0/1; `small` y `events.player` usan etiquetas 1/2.
`paid` son aportaciones antes de devolver la diferencia; `pot` es el bote igualado.

Cada evento guarda acción, acciones legales, aportaciones/bote previos y duración.
Una decisión optimizada además guarda semilla de escenarios, modelo, S, R, m,
media, media incremental, CVaR y estado. `reference` significa sin optimización;
`feasible` significa factible en el modelo muestral local;
`infeasible_emergency` incluye el motivo explícito. No significa fallo del solver.
La configuración alpha está en cada fila; estrategia incluye versión v1 y límites.

`hands.csv` puede crecer mucho: se regenera, no se versiona. Se publican resúmenes,
sesiones terminales, trayectorias, diagnósticos, incertidumbre, manifiesto y figuras.
La interfaz exporta el JSON de la vista y el resumen CSV; la CLI exporta los registros
completos compatibles con el evaluador. Las predicciones nunca se rellenan a posteriori.

## Migración

`python poker-cournot.py session ...` sustituye las demostraciones automáticas al
importar. `optimizacion_cournot_poker.py` exporta `analyze` y solo imprime al
invocarse como programa. La antigua API de callables `graficar_br` y las mallas
fraccionarias no se conserva: no funcionaba; usar `poker.exposure.analyze`.
El código original exacto se recupera con `git show b8eb6f3:poker-cournot.py` y
`git show b8eb6f3:optimizacion_cournot_poker.py`. No se elimina su historial.
