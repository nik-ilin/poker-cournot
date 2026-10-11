# Póker finito: decisiones, beneficio y CVaR

Proyecto universitario de Optimización. Integra el historial de `modelo` y `beep`
con el evaluador de sesiones de `main`. **Variante finita de una ronda preflop**,
no un solucionador general ni una implementación completa de no-limit Hold’em.

El optimizador controla las acciones del simulador: maximiza beneficio esperado
bajo CVaR local, o minimiza CVaR con beneficio mínimo. Enumera acciones legales
sobre escenarios de continuación. El riesgo de sesión se evalúa aparte.

## Instalar y ejecutar

Usar Python 3.13 para el entorno fijado en `requirements-lock.txt`; comprobado en macOS ARM64.
Desde la raíz real del repositorio (el nombre local puede diferir en mayúsculas
respecto de «Proyecto 1» y la tilde puede estar descompuesta):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m pytest -q
python -m poker.cli session --strategy risk --limit 10 --seed 10000 --out run
python -m streamlit run app.py
```

La interfaz abre en la dirección local mostrada por Streamlit. Permite cambiar
estrategia/rival, parámetros y semilla; recorrer manos; alternar vista privada y
observador; consultar estimaciones reales y exportar. Pulsar «Ejecutar sesión»
tras modificar controles. Los resultados agregados publicados aparecen al pie.

Para reproducir tablas, figuras y registros del estudio en una carpeta nueva:

```bash
python -m poker.cli experiment --sessions 200 --scenarios 32 --seed 10000 --out results/reproduction
python -m poker.audit results/reproduction
python optimizacion_cournot_poker.py
```

Abrir `results/reproduction/report.html` para la tabla y trayectoria; consultar
los CSV y SVG para incertidumbre, comparaciones y mejores respuestas. Los tiempos
varían con el equipo. Los registros completos se generan localmente y se excluyen
de Git para evitar archivos masivos. No sobrescribir una carpeta de ejecución.

Ejemplos de los dos objetivos y de emergencia:

```bash
python -m poker.cli session --strategy fixed --opponent minrisk --minimum 5 --out results/demo-j2
python -m poker.cli session --strategy risk --limit 0 --out results/demo-emergency
```

## Ruta de estudio

1. [Reglas, información y procedencia](docs/REGLAS.md).
2. [Formulación escrita antes del optimizador](docs/FORMULACION.md) y
   [explicación matemática con ejemplos](docs/MATEMATICAS.md).
3. [Módulos, exportación y migración](docs/ARQUITECTURA.md).
4. [Diseño experimental e incertidumbre](docs/EXPERIMENTOS.md).
5. [Resultados ejecutados y límites](docs/RESULTADOS.md).
6. [Conexión con Unidad 1: CVaR primal-dual, KKT y sensibilidad](docs/UNIDAD1.md).
7. [Pruebas y alcance](docs/VALIDACION.md), [auditoría y atribución](docs/INTEGRACION.md).
8. [Reparto técnico y guion de seis minutos](docs/PRESENTACION.md).

## Experimentos de Unidad 1

```bash
python -m poker.academic cvar --out results/unit1/cvar
python -m poker.academic sensitivity --out results/unit1/sensitivity --scenarios 128
python -m poker.academic stability --out results/unit1/stability --observations 8 --planner-seeds 5 --evaluation-scenarios 2048
```

Los LP académicos verifican el CVaR de distribuciones fijadas; no sustituyen la
selección discreta de acciones. Los nuevos artefactos están separados de las
sesiones originales en `results/study/`.

[Resultados compactos](results/study/) · [Pruebas](tests/) ·
[Evaluador previo](estudio-poker/) · [Cournot económico anterior](estudio-cournot/).
Los documentos de esos dos directorios describen entregas históricas; el estado
actual del producto integrado está aquí. Se conserva [la licencia](LICENSE).

No se demuestra optimalidad en el juego completo, garantía de riesgo de sesión,
rentabilidad contra rivales humanos ni validación humana de los resultados.
