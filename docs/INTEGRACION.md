# Auditoría y atribución

Referencias verificadas tras `git fetch origin`: main `cb5a156`, modelo `058dcaf`,
beep `b8eb6f3`. Copia local inicialmente limpia. `beep` desciende de `modelo` y
ambas de main; se creó `integracion/estudio-reproducible` y se fusionó beep con
commit de merge, preservando las dos aportaciones en la historia.

Atribución según metadatos Git, no una certificación de autoría individual de cada
línea: `058dcaf` figura con autor Iñigo Utande; `3ae55eb` y `b8eb6f3` con
`diegolarizfer-beep`; `cb5a156` con `nik-ilin`. Esta integración se prepara con
asistencia de Codex a petición de Nikolai. Las pruebas son ejecución automática,
no revisión ni validación humana por los tres compañeros.

## Qué se conserva

- Evaluador de cinco/siete cartas de modelo, extraído como funciones sin efectos
  laterales. Mantiene clasificación, rueda A2345, selección de cinco y kickers.
- Dotación, ciegas, capital, horizonte, convención de pérdidas y planteamiento
  diferenciado de objetivos J1/J2.
- Idea de mejores respuestas de beep, reformulada con enumeración entera y
  comprobación exhaustiva de factibilidad/desviaciones, incluyendo empates.
- Evaluador de sesiones de main, usado efectivamente por la nueva CLI; se añade
  validación de entradas al CVaR y se prueba el contrato con sesiones reales.
- Estudio económico de Cournot anterior, separado y conservado; no se presenta
  como motor de póker ni se certifican aquí todas sus capacidades.
- Licencia original íntegra e historia de las ramas remotas, sin force-push.

## Fallos contrastados y tratamiento

| Hallazgo en beep | Tratamiento |
|---|---|
| Espacios U+00A0 y cuerpos sin sangrar | Sustitución del módulo no importable por entrada limpia al juego de exposición |
| `graficar_br` recibe seis argumentos, firma de cuatro | Eliminada conexión rota; figura a partir de correspondencias certificadas |
| `imprimir_resultados` inexistente | Sustituida por resultado estructurado JSON |
| Ejemplos, barajado, simulaciones y gráficos al importar | Funciones puras y entradas bajo `__main__` |
| Variables globales y duplicación de configuraciones | `Config` y estados inmutables |
| Probabilidades comunes conocen ambas cartas | Referencia separada; política usa solo observación propia |
| Apuestas `min(q1,q2)` sin fold | Modelo de exposición separado de las reglas finitas con fold |
| Sesión iguala/pasa sin obedecer optimización | `session` ejecuta exactamente la acción de `decide` y la registra |
| CVaR local confundible con sesión | Fórmulas, métricas y horizontes separados |
| Mínimo residuo llamado equilibrio | Exhaustividad entera, factibilidad, ganancias por desviación y tolerancia |
| Cantidades decimales frente a fichas enteras | Acciones y exposición enteras |
| Sin exportación compatible | CSV extendido leído por el evaluador previo |

No se intentó reparar cada demostración global del archivo de 1684 líneas como
motor reutilizable: se recuperó su evaluador de cartas y se reemplazó la gestión
global de saldos por estado explícito, para hacer comprobable cada transición.
Los originales permanecen recuperables por hash. La nueva ronda preflop es una
decisión de alcance, no una afirmación de que el trabajo original implementase
esta variante.

## Revisión del evaluador previo

Se verificaron cola fraccionaria, ganancia final, conservación, rechazo de sesión
incompleta, horizonte y arrastre de saldo terminal. Su CVaR equal-weight coincide
con el ponderado nuevo cuando todos los pesos son iguales. Sigue sin comprobar
cartas/acciones al importar CSV externos: esa garantía procede de las pruebas del
motor para registros generados aquí. No se confunde conformidad del CSV con
legalidad de cualquier partida externa.
