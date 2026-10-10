# Poker–Cournot · Proyecto I de Optimización

## Estudio actual: póker

- [Guía completa y matemáticas](estudio-poker/README.md)
- [Evaluador Python](estudio-poker/estudio.py)
- [Configuración](estudio-poker/config.json)
- [Plantilla de resultados por mano](estudio-poker/plantilla_manos.csv)

Configuración provisional: 455 unidades por jugador, hasta 50 manos y final anticipado por capital cero. La variante y las reglas completas quedan pendientes de confirmación con el equipo. El evaluador recibe registros de un simulador externo; no implementa el juego ni optimiza las políticas.

Python 3.10 o posterior, sin dependencias externas. Desde la raíz del proyecto:

```bash
python3 estudio-poker/estudio.py --config estudio-poker/config.json --example --out resultados_formato_01
```

El ejemplo genera trayectorias aritméticas ficticias, no partidas de póker. Para usar registros del equipo:

```bash
python3 estudio-poker/estudio.py --config estudio-poker/config.json --hands manos_equipo.csv --out resultados_equipo_01
```

## Alternativa anterior: Cournot

[Guía y código](estudio-cournot/README.md): se conservan las formulaciones de beneficio, CVaR y sensibilidad a la producción rival. No procesan registros de póker.

## Estado y procedencia

Archivos copiados desde el vault universitario el 10 de octubre de 2026. Código y documentación preparados con asistencia de Codex; no ejecutados ni probados en esta entrega. No hay resultados reales del equipo incluidos. Los ejemplos son didácticos y no acreditan rendimiento de ninguna estrategia.

La licencia existente del repositorio se conserva en [LICENSE](LICENSE).
