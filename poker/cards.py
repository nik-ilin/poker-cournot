"""Evaluador recuperado de modelo/beep; categorías y desempates originales."""

from itertools import combinations

DECK = tuple((v, s) for v in range(2, 15) for s in range(4))


def valor_numerico(carta):
    valor = carta[0]

    figuras = {"J": 11, "Q": 12, "K": 13, "A": 14}

    if valor in figuras:
        return figuras[valor]

    return valor


def contar_valores(cartas):
    conteo = {}

    for carta in cartas:
        valor = valor_numerico(carta)
        conteo[valor] = conteo.get(valor, 0) + 1

    return conteo


def es_color(cartas):
    if len(cartas) != 5:
        raise ValueError("Debes introducir exactamente cinco cartas.")

    palos_mano = [carta[1] for carta in cartas]

    return len(set(palos_mano)) == 1


def valor_escalera(cartas):
    if len(cartas) != 5:
        raise ValueError("Debes introducir exactamente cinco cartas.")

    valores = sorted(set(valor_numerico(carta) for carta in cartas))

    if len(valores) != 5:
        return 0

    # Caso especial: el as funciona como carta baja
    if valores == [2, 3, 4, 5, 14]:
        return 5

    if valores[-1] - valores[0] == 4:
        return valores[-1]

    return 0


def evaluar_cinco(cartas):
    if len(cartas) != 5:
        raise ValueError("Debes introducir exactamente cinco cartas.")

    conteo = contar_valores(cartas)
    valores = sorted([valor_numerico(carta) for carta in cartas], reverse=True)

    grupos = sorted(
        [(cantidad, valor) for valor, cantidad in conteo.items()], reverse=True
    )

    repeticiones = [cantidad for cantidad, valor in grupos]
    orden_grupos = [valor for cantidad, valor in grupos]

    color = es_color(cartas)
    escalera = valor_escalera(cartas)

    if color and escalera:
        return (8, escalera)

    if repeticiones == [4, 1]:
        return (7, *orden_grupos)

    if repeticiones == [3, 2]:
        return (6, *orden_grupos)

    if color:
        return (5, *valores)

    if escalera:
        return (4, escalera)

    if repeticiones == [3, 1, 1]:
        return (3, *orden_grupos)

    if repeticiones == [2, 2, 1]:
        return (2, *orden_grupos)

    if repeticiones == [2, 1, 1, 1]:
        return (1, *orden_grupos)

    return (0, *valores)


def evaluar_mano(cartas):
    if len(cartas) != 7:
        raise ValueError("Debes introducir exactamente siete cartas.")

    combinaciones = combinations(cartas, 5)

    return max(evaluar_cinco(combinacion) for combinacion in combinaciones)
