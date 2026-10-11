# Defensa de 6 minutos y reparto propuesto

Propuesta entre tres compañeros técnicos equivalentes. No acredita trabajo ya
realizado por una persona ni asigna a Nikolai dirección jerárquica del equipo.
La extensión del informe sigue pendiente: confirmar con el docente sin convertir
la ambigüedad en una obligación inventada. Este material sirve de base modular.

| Tiempo | Participante | Contenido y demostración |
|---|---|---|
| 0:00–2:00 | Compañero A | Pregunta, reglas finitas, información privada y contabilidad. Mostrar una mano y explicar fold/call/raise y capital conservado. |
| 2:00–4:00 | Compañero B | Dos objetivos, ejemplo manual CVaR=60, escenarios de continuación, enumeración e inviabilidad. Mostrar alternativas reales de una decisión. |
| 4:00–6:00 | Compañero C | Diseño emparejado, resultados y sus intervalos, riesgo local frente a sesión, error de rival y limitaciones. |

Repartir aproximadamente dos minutos cada uno. Alternar quién presenta cada bloque
según el trabajo que finalmente revise y comprenda cada persona. Ensayar con
cronómetro; 6 minutos deja margen dentro de 5–7.

Guion verbal:

A: «Estudiamos decisiones bajo incertidumbre. No resolvemos todo Texas Hold’em:
restringimos a una ronda preflop y dos objetivos de aumento. Cada decisión ve
solo cartas propias. Capital y botes se conservan en cada transición.»

B: «Para cada acción simulamos cartas y la respuesta de una regla rival. Maximizar
beneficio con CVaR local es distinto de minimizar riesgo con un beneficio mínimo.
La cola incluye exactamente la masa necesaria. Para pérdidas fijas, el CVaR
también es un LP: el ejemplo 100, 20 y −10 asigna media unidad de peso dual a cada
una de las dos pérdidas mayores y da 60 en primal y dual. KKT certifica ese cálculo;
no convierte la enumeración discreta de póker en un problema convexo. Los escenarios
son una aproximación. Si ninguna acción cumple, registramos la inviabilidad y
continuamos legalmente con una emergencia.»

C: «Comparamos 200 sesiones por combinación con los mismos mazos exógenos. Las
semillas de evaluación son nuevas. Mostramos beneficio y riesgo conjuntamente,
con incertidumbre. Un límite de mano no limita automáticamente la pérdida de
sesión. La referencia de exposición y su equilibrio son un estudio separado.»

Demostración adicional del bloque B, si el tiempo lo permite: mostrar la curva
escalonada `V(R)` construida con las mismas 128 continuaciones y las frecuencias de
cambio al crecer S. Nombrar S=512 como referencia de mayor tamaño; no llamarlo
verdad exacta. Mantener los tres turnos en dos minutos cada uno (vídeo total de
seis minutos) y desplazar detalle del modelo original, no recortar la interpretación
de resultados.

Añadir al bloque C solo cifras verificadas de RESULTADOS.md. No prometer que una
política gane ni que la optimización supere siempre a la referencia fija.

## Revisión técnica propuesta

A revisa reglas, evaluación de manos y pruebas de saldos; B revisa escenarios,
CVaR, enumeración y referencia de exposición; C revisa semillas, estadística,
interfaz y reproducción. Cada uno ejecuta la instalación y explica un módulo de
otro compañero para detectar dependencias conceptuales. El informe debe distinguir
trabajo original, correcciones y material generado durante esta integración.

Preguntas probables: ¿por qué no Cournot clásico?, ¿qué es lo óptimo exactamente?,
¿por qué fold puede ser la única opción factible?, ¿qué cambia cuando el rival no
es el estimado?, ¿por qué no se suman CVaR de manos?, ¿qué ocultan los intervalos
con colas pequeñas?, ¿puede el observador contaminar una decisión? Responder con
las fórmulas y pruebas específicas, no con capturas como evidencia suficiente.
