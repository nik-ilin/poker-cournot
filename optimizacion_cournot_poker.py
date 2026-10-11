"""Entrada compatible por nombre; sustituye el borrador no ejecutable.

La antigua API de callables/mallas decimales se retira. Véase docs/INTEGRACION.md.
"""

from poker.exposure import analyze

if __name__ == "__main__":
    import json

    print(json.dumps(analyze(), indent=2))
