import random
from itertools import combinations
import matplotlib.pyplot as plt

PARAMETROS = {
    "valores_fichas": (1, 5, 10, 25, 50),
    "fichas_por_valor": 5,
    "capital_inicial": 455,
    "ciega_pequena": 1,
    "ciega_grande": 2,
    "maximo_manos": 50,
    "confianza_cvar": 0.90,
    "limite_cvar_jugador1": 50,
    "beneficio_minimo_jugador2": 5,
    "comision": 0
}

historial_manos = []
# Crear la baraja
valores = [2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K", "A"]
palos = ["corazones", "diamantes", "treboles", "picas"]

baraja = [
    (valor, palo)
    for valor in valores
    for palo in palos
]

# Barajar
random.shuffle(baraja)

# Repartir dos cartas a cada jugador
mano_jugador1 = []
mano_jugador2 = []

for _ in range(2):
    mano_jugador1.append(baraja.pop())
    mano_jugador2.append(baraja.pop())

# Comprobar el reparto
print("Jugador 1:", mano_jugador1)
print("Jugador 2:", mano_jugador2)
print("Cartas restantes:", len(baraja))  

# Valores y cantidades de fichas por jugador
valores_fichas = [1, 5, 10, 25, 50]
cantidad_por_valor = 5

capital_inicial = sum(valores_fichas) * cantidad_por_valor  

saldo_jugador1 = capital_inicial
saldo_jugador2 = capital_inicial

# En esta primera mano, el jugador 1 pone la ciega pequeña
ciega_pequena = 1
ciega_grande = 2

saldo_jugador1 -= ciega_pequena
saldo_jugador2 -= ciega_grande

# Aportaciones en la ronda actual
aporte_ronda1 = ciega_pequena
aporte_ronda2 = ciega_grande

bote = aporte_ronda1 + aporte_ronda2

print("Saldo jugador 1:", saldo_jugador1)  
print("Saldo jugador 2:", saldo_jugador2)  
print("Bote:", bote)                      

# Mayor aportación realizada en la ronda
apuesta_actual = max(aporte_ronda1, aporte_ronda2)

# Cantidad que le falta a cada jugador para igualar
por_igualar1 = apuesta_actual - aporte_ronda1
por_igualar2 = apuesta_actual - aporte_ronda2

print("Jugador 1 debe igualar:", por_igualar1)  # 1
print("Jugador 2 debe igualar:", por_igualar2)  # 0

# Saldo de cada jugador antes de poner las ciegas
saldo_inicio_mano1 = saldo_jugador1 + aporte_ronda1
saldo_inicio_mano2 = saldo_jugador2 + aporte_ronda2

# Total aportado por cada jugador durante toda la mano
aporte_total1 = aporte_ronda1
aporte_total2 = aporte_ronda2

def igualar(saldo, aporte_ronda, aporte_total, apuesta_actual, bote):
    cantidad_pendiente = max(0, apuesta_actual - aporte_ronda)
    cantidad_pagada = min(cantidad_pendiente, saldo)

    saldo -= cantidad_pagada
    aporte_ronda += cantidad_pagada
    aporte_total += cantidad_pagada
    bote += cantidad_pagada

    return saldo, aporte_ronda, aporte_total, bote

saldo_jugador1, aporte_ronda1, aporte_total1, bote = igualar(
    saldo_jugador1,
    aporte_ronda1,
    aporte_total1,
    apuesta_actual,
    bote
)

print("Saldo jugador 1:", saldo_jugador1)  # 453
print("Aportación de la ronda:", aporte_ronda1)  # 2
print("Aportación total:", aporte_total1)  # 2
print("Bote:", bote)  # 4

# Prueba: el jugador 2 pasa y termina la ronda preflop

cartas_comunitarias = []
cartas_quemadas = []

# Se aparta una carta sin mostrarla
cartas_quemadas.append(baraja.pop())

# Se descubren las tres cartas del flop
for _ in range(3):
    cartas_comunitarias.append(baraja.pop())

# Empieza una nueva ronda de apuestas
aporte_ronda1 = 0
aporte_ronda2 = 0
apuesta_actual = 0

por_igualar1 = 0
por_igualar2 = 0

print("Flop:", cartas_comunitarias)
print("Bote:", bote)                       # 4
print("Cartas restantes:", len(baraja))    # 44

# Baraja completa de referencia: no modifica el mazo de la partida
baraja_completa = [
    (valor, palo)
    for valor in valores
    for palo in palos
]

# Cada jugador descarta solo sus cartas y las comunitarias visibles
desconocidas_jugador1 = [
    carta for carta in baraja_completa
    if carta not in mano_jugador1 + cartas_comunitarias
]

desconocidas_jugador2 = [
    carta for carta in baraja_completa
    if carta not in mano_jugador2 + cartas_comunitarias
]

print("Desconocidas para jugador 1:", len(desconocidas_jugador1))  
print("Desconocidas para jugador 2:", len(desconocidas_jugador2))  

# Una simulación desde la información del jugador 1
cartas_simuladas = random.sample(desconocidas_jugador1, 4)

mano_rival_simulada = cartas_simuladas[:2]
turn_simulado = cartas_simuladas[2]
river_simulado = cartas_simuladas[3]

mesa_simulada = cartas_comunitarias + [
    turn_simulado,
    river_simulado
]

print("Posible mano del rival:", mano_rival_simulada)
print("Posible mesa completa:", mesa_simulada)

def valor_numerico(carta):
    valor = carta[0]

    figuras = {
        "J": 11,
        "Q": 12,
        "K": 13,
        "A": 14
    }

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
    valores = sorted(
        [valor_numerico(carta) for carta in cartas],
        reverse=True
    )

    grupos = sorted(
        [(cantidad, valor) for valor, cantidad in conteo.items()],
        reverse=True
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

cartas_prueba = [
    ("A", "picas"),
    ("A", "corazones"),
    (7, "treboles"),
    (7, "diamantes"),
    ("K", "picas")
]

def evaluar_mano(cartas):
    if len(cartas) != 7:
        raise ValueError("Debes introducir exactamente siete cartas.")

    combinaciones = combinations(cartas, 5)

    return max(
        evaluar_cinco(combinacion)
        for combinacion in combinaciones
    )

resultado_jugador1 = evaluar_mano(
    mano_jugador1 + mesa_simulada
)

resultado_rival = evaluar_mano(
    mano_rival_simulada + mesa_simulada
)

def mostrar_resultado(resultado):
    categorias = [
        "Carta alta", "Pareja", "Doble pareja", "Trío",
        "Escalera", "Color", "Full", "Póker",
        "Escalera de color", "Escalera real"
    ]

    figuras = {11: "J", 12: "Q", 13: "K", 14: "A"}

    categoria = categorias[resultado[0]]
    cartas = [
        str(figuras.get(valor, valor))
        for valor in resultado[1:]
    ]

    if cartas:
        return categoria + ": " + ", ".join(cartas)

    return categoria

print("Jugador 1:", mostrar_resultado(resultado_jugador1))
print("Rival simulado:", mostrar_resultado(resultado_rival))

if resultado_jugador1 > resultado_rival:
    print("Ganaría el jugador 1.")
elif resultado_jugador1 < resultado_rival:
    print("Ganaría el rival simulado.")
else:
    print("Empatarían.")

def estimar_probabilidades(mano, comunitarias, simulaciones=1000):
    conocidas = mano + comunitarias

    disponibles = [
        carta for carta in baraja_completa
        if carta not in conocidas
    ]

    faltan = 5 - len(comunitarias)

    victorias = 0
    empates = 0
    derrotas = 0

    for _ in range(simulaciones):
        extraidas = random.sample(disponibles, 2 + faltan)

        rival = extraidas[:2]
        mesa = comunitarias + extraidas[2:]

        resultado_propio = evaluar_mano(mano + mesa)
        resultado_rival = evaluar_mano(rival + mesa)

        if resultado_propio > resultado_rival:
            victorias += 1
        elif resultado_propio == resultado_rival:
            empates += 1
        else:
            derrotas += 1

    return (
        victorias / simulaciones,
        empates / simulaciones,
        derrotas / simulaciones
    )

p_ganar, p_empatar, p_perder = estimar_probabilidades(
    mano_jugador1,
    cartas_comunitarias
)

equity = p_ganar + 0.5 * p_empatar

print(f"Probabilidad de ganar: {p_ganar:.2%}")
print(f"Probabilidad de empatar: {p_empatar:.2%}")
print(f"Probabilidad de perder: {p_perder:.2%}")
print(f"Equity: {equity:.2%}")

def beneficios_posibles(bote_final, aportacion_total):
    beneficio_ganar = bote_final - aportacion_total
    beneficio_empatar = bote_final / 2 - aportacion_total
    beneficio_perder = -aportacion_total

    return beneficio_ganar, beneficio_empatar, beneficio_perder


# Ejemplo: ambos llegan al final sin apostar más.
beneficio_ganar, beneficio_empatar, beneficio_perder = (
    beneficios_posibles(bote, aporte_total1)
)

beneficio_esperado = (
    p_ganar * beneficio_ganar
    + p_empatar * beneficio_empatar
    + p_perder * beneficio_perder
)

print("Beneficio si gana:", beneficio_ganar)
print("Beneficio si empata:", beneficio_empatar)
print("Beneficio si pierde:", beneficio_perder)
print(f"Beneficio esperado: {beneficio_esperado:.4f}")

def calcular_cvar(beneficios, probabilidades, confianza=0.90):
    if not 0 <= confianza < 1:
        raise ValueError("La confianza debe estar entre 0 y 1, sin incluir 1.")

    if len(beneficios) != len(probabilidades):
        raise ValueError("Cada beneficio debe tener una probabilidad.")

    if any(p < 0 for p in probabilidades):
        raise ValueError("Las probabilidades no pueden ser negativas.")

    if abs(sum(probabilidades) - 1) > 1e-8:
        raise ValueError("Las probabilidades deben sumar 1.")

    # Ordenamos las pérdidas de mayor a menor.
    escenarios = sorted(
        [(-b, p) for b, p in zip(beneficios, probabilidades)],
        reverse=True
    )

    cola = 1 - confianza
    pendiente = cola
    perdida_acumulada = 0.0

    for perdida, probabilidad in escenarios:
        peso = min(probabilidad, pendiente)
        perdida_acumulada += perdida * peso
        pendiente -= peso

        if pendiente <= 1e-12:
            break

    return perdida_acumulada / cola


beneficios = [
    beneficio_ganar,
    beneficio_empatar,
    beneficio_perder
]

probabilidades = [p_ganar, p_empatar, p_perder]

cvar = calcular_cvar(beneficios, probabilidades)

print(f"CVaR al 90 %: {cvar:.4f}")

ejemplos = [
    ("Ejemplo 1", [2, 0, -2], [0.60, 0.10, 0.30], 0.6, 2),
    ("Ejemplo 2", [2, 0, -2], [0.80, 0.15, 0.05], 1.5, 1),
    ("Ejemplo 3", [10, 0, -20], [0.85, 0.05, 0.10], 6.5, 20)
]

for nombre, ganancias, probs, media_correcta, cvar_correcto in ejemplos:
    media = sum(b * p for b, p in zip(ganancias, probs))
    riesgo = calcular_cvar(ganancias, probs)

    assert abs(media - media_correcta) < 1e-8
    assert abs(riesgo - cvar_correcto) < 1e-8

    print(
        f"{nombre}: beneficio esperado = {media:.2f}, "
        f"CVaR = {riesgo:.2f}. Comprobado."
    )

# Resultados desde la perspectiva del jugador 1:
# gana el jugador 1, empatan, pierde el jugador 1.
beneficios_jugador1 = [
    beneficio_ganar,
    beneficio_empatar,
    beneficio_perder
]

beneficios_jugador2 = [-b for b in beneficios_jugador1]

# Las probabilidades corresponden a los mismos escenarios.
probabilidades = [p_ganar, p_empatar, p_perder]

media_jugador1 = sum(
    b * p for b, p in zip(beneficios_jugador1, probabilidades)
)

media_jugador2 = sum(
    b * p for b, p in zip(beneficios_jugador2, probabilidades)
)

cvar_jugador1 = calcular_cvar(
    beneficios_jugador1, probabilidades
)

cvar_jugador2 = calcular_cvar(
    beneficios_jugador2, probabilidades
)

print(f"Jugador 1: beneficio esperado = {media_jugador1:.4f}")
print(f"Jugador 1: CVaR al 90 % = {cvar_jugador1:.4f}")

print(f"Jugador 2: beneficio esperado = {media_jugador2:.4f}")
print(f"Jugador 2: CVaR al 90 % = {cvar_jugador2:.4f}")

assert abs(media_jugador1 + media_jugador2) < 1e-8

# Probabilidades desde la perspectiva del jugador 2.
p_ganar2, p_empatar2, p_perder2 = estimar_probabilidades(
    mano_jugador2, cartas_comunitarias
)

# Beneficios si el jugador 2 gana, empata o pierde.
beneficios_jugador2_propios = beneficios_posibles(
    bote, aporte_total2
)

probabilidades_jugador2 = [
    p_ganar2,
    p_empatar2,
    p_perder2
]

media_jugador2_propia = sum(
    b * p
    for b, p in zip(
        beneficios_jugador2_propios,
        probabilidades_jugador2
    )
)

cvar_jugador2_propio = calcular_cvar(
    beneficios_jugador2_propios,
    probabilidades_jugador2
)

print("\nEstimación con la información del jugador 2:")
print(f"Probabilidad de ganar: {p_ganar2:.2%}")
print(f"Probabilidad de empatar: {p_empatar2:.2%}")
print(f"Probabilidad de perder: {p_perder2:.2%}")
print(f"Beneficio esperado: {media_jugador2_propia:.4f}")
print(f"CVaR al 90 %: {cvar_jugador2_propio:.4f}")

def resumir_beneficios(beneficios, probabilidades, confianza=0.90):
    # calcular_cvar también comprueba las probabilidades.
    cvar = calcular_cvar(
        beneficios, probabilidades, confianza
    )

    beneficio_esperado = sum(
        b * p for b, p in zip(beneficios, probabilidades)
    )

    probabilidad_perdida = sum(
        p for b, p in zip(beneficios, probabilidades)
        if b < 0
    )

    return {
        "beneficio_esperado": beneficio_esperado,
        "probabilidad_perdida": probabilidad_perdida,
        "cvar": cvar
    }


resumen_jugador2 = resumir_beneficios(
    beneficios_jugador2_propios,
    probabilidades_jugador2
)

print("\nResumen del jugador 2:")
print(
    f"Beneficio esperado: "
    f"{resumen_jugador2['beneficio_esperado']:.4f}"
)
print(
    f"Probabilidad de pérdida: "
    f"{resumen_jugador2['probabilidad_perdida']:.2%}"
)
print(f"CVaR: {resumen_jugador2['cvar']:.4f}")

# Revelamos el turn real.
cartas_quemadas.append(baraja.pop())
cartas_comunitarias.append(baraja.pop())

# Revelamos el river real.
cartas_quemadas.append(baraja.pop())
cartas_comunitarias.append(baraja.pop())

print("\nMesa final:", cartas_comunitarias)

# Evaluamos las cartas reales de ambos jugadores.
resultado1 = evaluar_mano(mano_jugador1 + cartas_comunitarias)
resultado2 = evaluar_mano(mano_jugador2 + cartas_comunitarias)

print("Jugador 1:", mostrar_resultado(resultado1))
print("Jugador 2:", mostrar_resultado(resultado2))

# Repartimos el bote.
if resultado1 > resultado2:
    saldo_jugador1 += bote
    print("Gana el jugador 1.")

elif resultado2 > resultado1:
    saldo_jugador2 += bote
    print("Gana el jugador 2.")

else:
    saldo_jugador1 += bote / 2
    saldo_jugador2 += bote / 2
    print("Empate.")

bote = 0

# Beneficio neto respecto al inicio de esta mano.
beneficio_real1 = saldo_jugador1 - saldo_inicio_mano1
beneficio_real2 = saldo_jugador2 - saldo_inicio_mano2

print("Beneficio real jugador 1:", beneficio_real1)
print("Beneficio real jugador 2:", beneficio_real2)
print("Saldo final jugador 1:", saldo_jugador1)
print("Saldo final jugador 2:", saldo_jugador2)

# Comprobamos que las fichas se conservan.
assert beneficio_real1 + beneficio_real2 == 0
assert saldo_jugador1 + saldo_jugador2 == 2 * capital_inicial

def registrar_mano(historial, beneficio1, beneficio2, saldo1, saldo2):
    historial.append({
        "mano": len(historial) + 1,
        "beneficio1": beneficio1,
        "beneficio2": beneficio2,
        "saldo1": saldo1,
        "saldo2": saldo2
    })


registrar_mano(
    historial_manos,
    beneficio_real1,
    beneficio_real2,
    saldo_jugador1,
    saldo_jugador2
)

print("\nHistorial de la partida:")

for registro in historial_manos:
    print(
        f"Mano {registro['mano']}: "
        f"beneficio J1 = {registro['beneficio1']}, "
        f"beneficio J2 = {registro['beneficio2']}, "
        f"saldo J1 = {registro['saldo1']}, "
        f"saldo J2 = {registro['saldo2']}"
    )

def resumir_historial(historial, confianza=0.90):
    if not historial:
        raise ValueError("Todavía no hay manos registradas.")

    numero_manos = len(historial)
    probabilidades = [1 / numero_manos] * numero_manos

    resumenes = {}

    for jugador in (1, 2):
        beneficios = [
            registro[f"beneficio{jugador}"]
            for registro in historial
        ]

        resumen = resumir_beneficios(
            beneficios, probabilidades, confianza
        )

        resumen["beneficio_total"] = sum(beneficios)
        resumen["manos_jugadas"] = numero_manos
        resumenes[jugador] = resumen

    return resumenes


resumen_partida = resumir_historial(historial_manos)

for jugador, resumen in resumen_partida.items():
    print(f"\nResultados del jugador {jugador}:")
    print("Manos jugadas:", resumen["manos_jugadas"])
    print(f"Beneficio total: {resumen['beneficio_total']:.2f}")
    print(f"Beneficio medio por mano: {resumen['beneficio_esperado']:.4f}")
    print(f"Frecuencia de pérdida: {resumen['probabilidad_perdida']:.2%}")
    print(f"CVaR observado al 90 %: {resumen['cvar']:.4f}")

def preparar_mano(saldo1, saldo2, numero_mano):
    if saldo1 <= 0 or saldo2 <= 0:
        raise ValueError("La partida ha terminado: alguien no tiene fichas.")

    if not 1 <= numero_mano <= 50:
        raise ValueError("El número de mano debe estar entre 1 y 50.")

    saldos = [saldo1, saldo2]
    saldos_iniciales = saldos.copy()

    # Índices: 0 representa al jugador 1 y 1 al jugador 2.
    pequena = (numero_mano - 1) % 2
    grande = 1 - pequena

    mazo = baraja_completa.copy()
    random.shuffle(mazo)

    manos = [[], []]

    # En heads-up, la primera carta se reparte a la ciega grande.
    for _ in range(2):
        manos[grande].append(mazo.pop())
        manos[pequena].append(mazo.pop())

    aportaciones = [0, 0]

    # Nadie puede aportar más fichas de las que tiene.
    aportaciones[pequena] = min(ciega_pequena, saldos[pequena])
    aportaciones[grande] = min(ciega_grande, saldos[grande])

    for jugador in (0, 1):
        saldos[jugador] -= aportaciones[jugador]

    return {
        "numero": numero_mano,
        "baraja": mazo,
        "manos": manos,
        "mesa": [],
        "quemadas": [],
        "saldos_iniciales": saldos_iniciales,
        "saldos": saldos,
        "aporte_ronda": aportaciones.copy(),
        "aporte_total": aportaciones.copy(),
        "bote": sum(aportaciones),
        "jugador_ciega_pequena": pequena,
        "jugador_ciega_grande": grande
    }

def revelar_siguiente_etapa(estado):
    numero_comunitarias = len(estado["mesa"])

    if numero_comunitarias == 0:
        etapa = "Flop"
        cantidad = 3
    elif numero_comunitarias == 3:
        etapa = "Turn"
        cantidad = 1
    elif numero_comunitarias == 4:
        etapa = "River"
        cantidad = 1
    else:
        raise ValueError("No se puede revelar otra etapa.")

    # Quemamos una carta sin mostrarla a los jugadores.
    estado["quemadas"].append(estado["baraja"].pop())

    for _ in range(cantidad):
        estado["mesa"].append(estado["baraja"].pop())

    # Comienza una nueva ronda de apuestas.
    estado["aporte_ronda"] = [0, 0]

    return etapa

def aportar_fichas(estado, jugador, cantidad):
    # 0 = jugador 1; 1 = jugador 2.
    if jugador not in (0, 1):
        raise ValueError("El jugador debe ser 0 o 1.")

    if not isinstance(cantidad, int) or cantidad < 0:
        raise ValueError("La cantidad debe ser un entero no negativo.")

    if cantidad > estado["saldos"][jugador]:
        raise ValueError("El jugador no tiene suficientes fichas.")

    estado["saldos"][jugador] -= cantidad
    estado["aporte_ronda"][jugador] += cantidad
    estado["aporte_total"][jugador] += cantidad
    estado["bote"] += cantidad

    # El dinero total debe conservarse.
    assert (
        sum(estado["saldos"]) + estado["bote"]
        == sum(estado["saldos_iniciales"])
    )

# Conservamos los saldos finales de la primera mano.
estado_prueba = preparar_mano(
    saldo_jugador1,
    saldo_jugador2,
    numero_mano=2
)

pequena = estado_prueba["jugador_ciega_pequena"]
grande = estado_prueba["jugador_ciega_grande"]

print("\nComprobación de la segunda mano:")
print("Ciega pequeña: jugador", pequena + 1)
print("Ciega grande: jugador", grande + 1)
print("Saldos tras las ciegas:", estado_prueba["saldos"])
print("Bote inicial:", estado_prueba["bote"])

# Esta prueba supone que ambos tienen fichas suficientes.
pendiente = (
    estado_prueba["aporte_ronda"][grande]
    - estado_prueba["aporte_ronda"][pequena]
)

aportar_fichas(estado_prueba, pequena, pendiente)

# Suponemos que la ciega grande pasa: termina la ronda.
etapa = revelar_siguiente_etapa(estado_prueba)

print(etapa + ":", estado_prueba["mesa"])
print("Bote después de igualar:", estado_prueba["bote"])
print("Aportaciones de la ronda:", estado_prueba["aporte_ronda"])
print("Aportaciones de la mano:", estado_prueba["aporte_total"])
print("Cartas restantes:", len(estado_prueba["baraja"]))

def cerrar_mano_showdown(estado):
    if estado.get("finalizada", False):
        raise ValueError("Esta mano ya está finalizada.")

    if len(estado["mesa"]) != 5:
        raise ValueError("Deben estar reveladas las cinco comunitarias.")

    if estado["aporte_total"][0] != estado["aporte_total"][1]:
        raise ValueError("Antes hay que devolver la cantidad no igualada.")

    resultados = [
        evaluar_mano(mano + estado["mesa"])
        for mano in estado["manos"]
    ]

    if resultados[0] > resultados[1]:
        estado["saldos"][0] += estado["bote"]
        ganador = 1

    elif resultados[1] > resultados[0]:
        estado["saldos"][1] += estado["bote"]
        ganador = 2

    else:
        mitad = estado["bote"] // 2
        estado["saldos"][0] += mitad
        estado["saldos"][1] += mitad
        ganador = None

    estado["bote"] = 0
    estado["finalizada"] = True

    beneficios = [
        estado["saldos"][i] - estado["saldos_iniciales"][i]
        for i in (0, 1)
    ]

    assert sum(beneficios) == 0

    return ganador, beneficios

revelar_siguiente_etapa(estado_prueba)  # Turn
revelar_siguiente_etapa(estado_prueba)  # River

ganador, beneficios = cerrar_mano_showdown(estado_prueba)

# Actualizamos los saldos para la siguiente mano.
saldo_jugador1, saldo_jugador2 = estado_prueba["saldos"]

registrar_mano(
    historial_manos,
    beneficios[0],
    beneficios[1],
    saldo_jugador1,
    saldo_jugador2
)

print("\nMesa final:", estado_prueba["mesa"])
print("Ganador:", ganador if ganador is not None else "Empate")
print("Beneficios:", beneficios)
print("Saldos finales:", estado_prueba["saldos"])
print("Manos registradas:", len(historial_manos))

def cerrar_mano_retirada(estado, jugador_retirado):
    # 0 = jugador 1; 1 = jugador 2.
    if jugador_retirado not in (0, 1):
        raise ValueError("El jugador debe ser 0 o 1.")

    if estado.get("finalizada", False):
        raise ValueError("Esta mano ya está finalizada.")

    ganador = 1 - jugador_retirado

    estado["saldos"][ganador] += estado["bote"]
    estado["bote"] = 0
    estado["finalizada"] = True

    beneficios = [
        estado["saldos"][i] - estado["saldos_iniciales"][i]
        for i in (0, 1)
    ]

    assert sum(beneficios) == 0

    # Devolvemos el número visible del ganador: 1 o 2.
    return ganador + 1, beneficios

def cerrar_mano_retirada(estado, jugador_retirado):
    # 0 = jugador 1; 1 = jugador 2.
    if jugador_retirado not in (0, 1):
        raise ValueError("El jugador debe ser 0 o 1.")

    if estado.get("finalizada", False):
        raise ValueError("Esta mano ya está finalizada.")

    ganador = 1 - jugador_retirado

    estado["saldos"][ganador] += estado["bote"]
    estado["bote"] = 0
    estado["finalizada"] = True

    beneficios = [
        estado["saldos"][i] - estado["saldos_iniciales"][i]
        for i in (0, 1)
    ]

    assert sum(beneficios) == 0

    # Devolvemos el número visible del ganador: 1 o 2.
    return ganador + 1, beneficios

prueba_retirada = preparar_mano(455, 455, numero_mano=1)

ganador_prueba, beneficios_prueba = cerrar_mano_retirada(
    prueba_retirada,
    jugador_retirado=0
)

assert beneficios_prueba == [-1, 1]
assert prueba_retirada["saldos"] == [454, 456]

print("\nPrueba de retirada:")
print("Ganador:", ganador_prueba)
print("Beneficios:", beneficios_prueba)
print("Saldos finales:", prueba_retirada["saldos"])

def resolver_all_in(estado):
    if estado.get("finalizada", False):
        raise ValueError("Esta mano ya está finalizada.")

    if 0 not in estado["saldos"]:
        raise ValueError("Ningún jugador está all-in.")

    aportaciones = estado["aporte_total"]
    diferencia = abs(aportaciones[0] - aportaciones[1])

    if diferencia > 0:
        mayor = 0 if aportaciones[0] > aportaciones[1] else 1
        menor = 1 - mayor

        # Si quien aportó menos tiene fichas, aún debe decidir.
        if estado["saldos"][menor] > 0:
            raise ValueError("El rival todavía debe igualar o retirarse.")

        # Devolvemos la parte de la apuesta que no está cubierta.
        estado["saldos"][mayor] += diferencia
        estado["aporte_total"][mayor] -= diferencia
        estado["bote"] -= diferencia

    # Ya no habrá más apuestas en esta mano.
    estado["aporte_ronda"] = [0, 0]

    while len(estado["mesa"]) < 5:
        revelar_siguiente_etapa(estado)

    return cerrar_mano_showdown(estado)

prueba_all_in = preparar_mano(30, 10, numero_mano=1)

# El jugador 1 apuesta todo lo que le queda.
aportar_fichas(
    prueba_all_in, 0, prueba_all_in["saldos"][0]
)

# El jugador 2 acepta y aporta sus fichas restantes.
aportar_fichas(
    prueba_all_in, 1, prueba_all_in["saldos"][1]
)

ganador_prueba, beneficios_prueba = resolver_all_in(prueba_all_in)

assert prueba_all_in["aporte_total"] == [10, 10]
assert sum(prueba_all_in["saldos"]) == 40

print("\nPrueba de all-in:")
print("Aportaciones cubiertas:", prueba_all_in["aporte_total"])
print("Mesa final:", prueba_all_in["mesa"])
print("Ganador:", ganador_prueba if ganador_prueba else "Empate")
print("Beneficios:", beneficios_prueba)
print("Saldos finales:", prueba_all_in["saldos"])

def jugar_partida_prueba(capital1=455, capital2=455):
    saldo1, saldo2 = capital1, capital2
    historial = []

    for numero in range(1, 51):
        if saldo1 <= 0 or saldo2 <= 0:
            break

        estado = preparar_mano(saldo1, saldo2, numero)

        # Quien ha aportado menos iguala hasta donde puede.
        aportes = estado["aporte_ronda"]
        jugador = 0 if aportes[0] < aportes[1] else 1
        pendiente = max(aportes) - aportes[jugador]

        cantidad = min(pendiente, estado["saldos"][jugador])
        aportar_fichas(estado, jugador, cantidad)

        if 0 in estado["saldos"]:
            ganador, beneficios = resolver_all_in(estado)
        else:
            # En esta prueba ambos pasan en todas las etapas.
            while len(estado["mesa"]) < 5:
                revelar_siguiente_etapa(estado)

            ganador, beneficios = cerrar_mano_showdown(estado)

        saldo1, saldo2 = estado["saldos"]

        registrar_mano(
            historial,
            beneficios[0],
            beneficios[1],
            saldo1,
            saldo2
        )

        assert saldo1 + saldo2 == capital1 + capital2

    return historial

historial_prueba = jugar_partida_prueba()
resumen_prueba = resumir_historial(historial_prueba)

print("\nPartida continuada de prueba:")
print("Manos jugadas:", len(historial_prueba))

for jugador, resumen in resumen_prueba.items():
    print(f"\nJugador {jugador}:")
    print(f"Beneficio total: {resumen['beneficio_total']:.2f}")
    print(f"Beneficio medio: {resumen['beneficio_esperado']:.4f}")
    print(f"CVaR al 90 %: {resumen['cvar']:.4f}")

print(
    "\nSaldos finales:",
    historial_prueba[-1]["saldo1"],
    historial_prueba[-1]["saldo2"]
)

numero_partidas = 1000
todas_las_manos = []
beneficios_por_partida1 = []
beneficios_por_partida2 = []

for _ in range(numero_partidas):
    historial = jugar_partida_prueba()

    todas_las_manos.extend(historial)

    beneficios_por_partida1.append(
        sum(mano["beneficio1"] for mano in historial)
    )

    beneficios_por_partida2.append(
        sum(mano["beneficio2"] for mano in historial)
    )

resumen_simulacion = resumir_historial(todas_las_manos)

print("\nResultados de las partidas de prueba:")
print("Partidas simuladas:", numero_partidas)
print("Manos totales:", len(todas_las_manos))

for jugador, resumen in resumen_simulacion.items():
    print(f"\nJugador {jugador}:")
    print(f"Beneficio medio por mano: {resumen['beneficio_esperado']:.4f}")
    print(f"Frecuencia de pérdida: {resumen['probabilidad_perdida']:.2%}")
    print(f"CVaR por mano al 90 %: {resumen['cvar']:.4f}")

print(
    "\nBeneficio medio por partida del jugador 1:",
    sum(beneficios_por_partida1) / numero_partidas
)

print(
    "Beneficio medio por partida del jugador 2:",
    sum(beneficios_por_partida2) / numero_partidas
)

def estudiar_informacion(simulaciones=2000):
    ejemplo = preparar_mano(455, 455, numero_mano=1)
    mano = ejemplo["manos"][0]
    resultados = []

    for etapa in ["Preflop", "Flop", "Turn", "River"]:
        if etapa != "Preflop":
            revelar_siguiente_etapa(ejemplo)

        probabilidades = estimar_probabilidades(
            mano,
            ejemplo["mesa"],
            simulaciones
        )

        resumen = resumir_beneficios(
            [2, 0, -2],
            probabilidades
        )

        resultados.append({
            "etapa": etapa,
            "mesa": ejemplo["mesa"].copy(),
            "p_ganar": probabilidades[0],
            "p_empatar": probabilidades[1],
            "beneficio_esperado": resumen["beneficio_esperado"],
            "cvar": resumen["cvar"]
        })

    return mano, resultados


mano_estudio, resultados_informacion = estudiar_informacion()

print("\nEstudio de información:")
print("Cartas del jugador 1:", mano_estudio)

for resultado in resultados_informacion:
    print(f"\n{resultado['etapa']}: {resultado['mesa']}")
    print(f"Probabilidad de ganar: {resultado['p_ganar']:.2%}")
    print(f"Probabilidad de empatar: {resultado['p_empatar']:.2%}")
    print(f"Beneficio esperado: {resultado['beneficio_esperado']:.4f}")
    print(f"CVaR al 90 %: {resultado['cvar']:.4f}")

numero_manos_estudio = 30

estudio_acumulado = {
    etapa: {"varianzas": [], "cvars": []}
    for etapa in ["Preflop", "Flop", "Turn", "River"]
}

for _ in range(numero_manos_estudio):
    _, resultados = estudiar_informacion(simulaciones=500)

    for resultado in resultados:
        p_ganar = resultado["p_ganar"]
        p_empatar = resultado["p_empatar"]
        p_perder = 1 - p_ganar - p_empatar
        media = resultado["beneficio_esperado"]

        varianza = 4 * (p_ganar + p_perder) - media ** 2
        varianza = max(0, varianza)

        etapa = resultado["etapa"]
        estudio_acumulado[etapa]["varianzas"].append(varianza)
        estudio_acumulado[etapa]["cvars"].append(resultado["cvar"])

print("\nComparación de información en varias manos:")

for etapa, datos in estudio_acumulado.items():
    varianza_media = sum(datos["varianzas"]) / numero_manos_estudio
    cvar_medio = sum(datos["cvars"]) / numero_manos_estudio

    print(
        f"{etapa}: "
        f"varianza condicional media = {varianza_media:.4f}, "
        f"CVaR condicional medio = {cvar_medio:.4f}"
    )

etapas = list(estudio_acumulado)

varianzas_medias = [
    sum(estudio_acumulado[etapa]["varianzas"])
    / len(estudio_acumulado[etapa]["varianzas"])
    for etapa in etapas
]

cvars_medios = [
    sum(estudio_acumulado[etapa]["cvars"])
    / len(estudio_acumulado[etapa]["cvars"])
    for etapa in etapas
]

fig, ejes = plt.subplots(1, 2, figsize=(11, 4))

ejes[0].plot(etapas, varianzas_medias, marker="o")
ejes[0].set_title("Incertidumbre del beneficio")
ejes[0].set_ylabel("Varianza condicional media (unidades²)")

ejes[1].plot(etapas, cvars_medios, marker="o", color="darkorange")
ejes[1].set_title("Riesgo de pérdida")
ejes[1].set_ylabel("CVaR condicional medio al 90 % (unidades)")

for eje in ejes:
    eje.set_xlabel("Información disponible")
    eje.grid(alpha=0.3)

fig.suptitle(
    f"{numero_manos_estudio} manos · "
    "500 simulaciones por etapa · aportación fija de 2"
)

plt.tight_layout()
plt.savefig("riesgo_por_etapa.png", dpi=300, bbox_inches="tight")
plt.show()


# Estudio del tamaño de la apuesta y su riesgo

estado_apuestas = preparar_mano(455, 455, numero_mano=1)

incrementos_apuesta = [0, 1, 2, 5, 10, 20, 50]
resultados_apuestas = {0: [], 1: []}

for jugador in (0, 1):
    mano = estado_apuestas["manos"][jugador]

    probabilidades = estimar_probabilidades(
        mano, estado_apuestas["mesa"], simulaciones=2000
    )

    print(f"\nJugador {jugador + 1}: {mano}")

    for subida in incrementos_apuesta:
        # Ambos igualan la subida sobre la ciega grande
        aporte = 2 + subida
        bote_final = 2 * aporte

        beneficios = beneficios_posibles(
            bote_final, aporte
        )

        resumen = resumir_beneficios(
            beneficios, probabilidades, 0.90
        )

        resultados_apuestas[jugador].append({
            "subida": subida,
            "beneficio": resumen["beneficio_esperado"],
            "cvar": resumen["cvar"]
        })

        print(
            f"Subida: {subida:>2} | "
            f"Beneficio esperado: "
            f"{resumen['beneficio_esperado']:.3f} | "
            f"CVaR: {resumen['cvar']:.3f}"
        )

# Representacion grafica
fig, ejes = plt.subplots(1, 2, figsize=(11, 4))

for jugador in (0, 1):
    datos = resultados_apuestas[jugador]

    x = [dato["subida"] for dato in datos]
    beneficios = [dato["beneficio"] for dato in datos]
    riesgos = [dato["cvar"] for dato in datos]

    ejes[0].plot(x, beneficios, marker="o",
                 label=f"Jugador {jugador + 1}")

    ejes[1].plot(x, riesgos, marker="o",
                 label=f"Jugador {jugador + 1}")

ejes[0].set_title("Beneficio esperado según la apuesta")
ejes[0].set_ylabel("Beneficio esperado (fichas)")

ejes[1].set_title("CVaR según la apuesta")
ejes[1].set_ylabel("CVaR al 90 % (fichas)")

for eje in ejes:
    eje.set_xlabel("Subida adicional (fichas)")
    eje.legend()
    eje.grid(alpha=0.3)

plt.tight_layout()
plt.savefig("riesgo_segun_apuesta.png", dpi=300)
plt.show()



# Funciones economicas para ambos jugadores

def crear_modelo_poker(estado, simulaciones=3000):
    probabilidades = [
        estimar_probabilidades(
            estado["manos"][i], estado["mesa"], simulaciones
        )
        for i in (0, 1)
    ]

    # Fichas disponibles despues de cubrir la apuesta base
    capacidades = [
        saldo - 2 for saldo in estado["saldos_iniciales"]
    ]

    def apuesta_efectiva(q1, q2):
        if not (0 <= q1 <= capacidades[0]):
            raise ValueError("Apuesta no valida del jugador 1.")
        if not (0 <= q2 <= capacidades[1]):
            raise ValueError("Apuesta no valida del jugador 2.")

        return 2 + min(q1, q2)

    def beneficio_esperado(jugador, q1, q2):
        aporte = apuesta_efectiva(q1, q2)
        p_ganar, p_empatar, p_perder = probabilidades[jugador]

        return aporte * (p_ganar - p_perder)

    def riesgo_cvar(jugador, q1, q2):
        aporte = apuesta_efectiva(q1, q2)
        beneficios = [aporte, 0, -aporte]

        return calcular_cvar(
            beneficios,
            probabilidades[jugador],
            PARAMETROS["confianza_cvar"]
        )

    def mu1(q1, q2):
        return beneficio_esperado(0, q1, q2)

    def mu2(q1, q2):
        return beneficio_esperado(1, q1, q2)

    def R1(q1, q2):
        return riesgo_cvar(0, q1, q2)

    def R2(q1, q2):
        return riesgo_cvar(1, q1, q2)

    return mu1, mu2, R1, R2, capacidades


# Comprobamos las funciones con una mano
estado_modelo = preparar_mano(455, 455, numero_mano=1)

mu1, mu2, R1, R2, capacidades = crear_modelo_poker(
    estado_modelo
)

print("\nFunciones economicas del poker:")
print("Capacidades:", capacidades)

for q1, q2 in [(0, 0), (5, 5), (10, 20), (20, 10)]:
    print(f"\nApuestas adicionales: q1={q1}, q2={q2}")
    print(f"Beneficio esperado J1: {mu1(q1, q2):.4f}")
    print(f"Beneficio esperado J2: {mu2(q1, q2):.4f}")
    print(f"CVaR jugador 1: {R1(q1, q2):.4f}")
    print(f"CVaR jugador 2: {R2(q1, q2):.4f}")

# Las apuestas no igualadas se devuelven
assert mu1(10, 20) == mu1(20, 10)
assert R2(10, 20) == R2(20, 10)


# Comprobacion de los beneficios con informacion completa

def probabilidades_conjuntas(estado, simulaciones=3000):
    mano1, mano2 = estado["manos"]
    mesa = estado["mesa"]

    conocidas = mano1 + mano2 + mesa
    disponibles = [
        carta for carta in baraja_completa
        if carta not in conocidas
    ]

    victorias1 = 0
    victorias2 = 0
    empates = 0

    for _ in range(simulaciones):
        mesa_final = mesa + random.sample(
            disponibles, 5 - len(mesa)
        )

        resultado1 = evaluar_mano(mano1 + mesa_final)
        resultado2 = evaluar_mano(mano2 + mesa_final)

        if resultado1 > resultado2:
            victorias1 += 1
        elif resultado2 > resultado1:
            victorias2 += 1
        else:
            empates += 1

    return (
        victorias1 / simulaciones,
        empates / simulaciones,
        victorias2 / simulaciones
    )


# Utilizamos la misma mano del estudio anterior
p1, pe, p2 = probabilidades_conjuntas(estado_modelo)

# Ambos aportan 12 fichas en total
aporte = 12

beneficios1 = [aporte, 0, -aporte]
beneficios2 = [-aporte, 0, aporte]

probabilidades = [p1, pe, p2]

resumen1 = resumir_beneficios(
    beneficios1, probabilidades
)

resumen2 = resumir_beneficios(
    beneficios2, probabilidades
)

media1 = resumen1["beneficio_esperado"]
media2 = resumen2["beneficio_esperado"]

print("\nComprobacion con informacion completa:")
print(f"Probabilidad de ganar J1: {p1:.2%}")
print(f"Probabilidad de empate: {pe:.2%}")
print(f"Probabilidad de ganar J2: {p2:.2%}")

print(f"\nBeneficio esperado J1: {media1:.4f}")
print(f"Beneficio esperado J2: {media2:.4f}")
print(f"Suma de beneficios: {media1 + media2:.4f}")

print(f"\nCVaR J1: {resumen1['cvar']:.4f}")
print(f"CVaR J2: {resumen2['cvar']:.4f}")

assert abs(media1 + media2) < 1e-10
assert abs(p1 + pe + p2 - 1) < 1e-10


# Comprobacion de las restricciones de los jugadores

limite_riesgo1 = PARAMETROS["limite_cvar_jugador1"]
beneficio_minimo2 = PARAMETROS["beneficio_minimo_jugador2"]

# Utilizamos probabilidades conjuntas para comprobar
# ambos jugadores bajo los mismos escenarios.
probabilidades_conjuntas_modelo = [p1, pe, p2]

def comprobar_restricciones(q1, q2):
    if not (0 <= q1 <= capacidades[0]):
        raise ValueError("Apuesta no valida del jugador 1.")

    if not (0 <= q2 <= capacidades[1]):
        raise ValueError("Apuesta no valida del jugador 2.")

    aporte = 2 + min(q1, q2)

    beneficios1 = [aporte, 0, -aporte]
    beneficios2 = [-aporte, 0, aporte]

    resumen1 = resumir_beneficios(
        beneficios1, probabilidades_conjuntas_modelo
    )

    resumen2 = resumir_beneficios(
        beneficios2, probabilidades_conjuntas_modelo
    )

    riesgo1 = resumen1["cvar"]
    media2 = resumen2["beneficio_esperado"]

    cumple_j1 = riesgo1 <= limite_riesgo1
    cumple_j2 = media2 >= beneficio_minimo2

    return riesgo1, media2, cumple_j1, cumple_j2


# Comprobamos distintos tamaños de apuesta
print("\nComprobacion de restricciones:")

for q1, q2 in [(0, 0), (5, 5), (10, 10),
               (20, 20), (50, 50), (100, 100)]:

    riesgo, beneficio, cumple1, cumple2 = (
        comprobar_restricciones(q1, q2)
    )

    print(
        f"q1={q1:>3}, q2={q2:>3} | "
        f"CVaR J1={riesgo:>6.2f} | "
        f"Beneficio J2={beneficio:>7.2f} | "
        f"J1={'Cumple' if cumple1 else 'No cumple'} | "
        f"J2={'Cumple' if cumple2 else 'No cumple'}"
    )



# Modelo economico comun para los dos jugadores

def crear_modelo_comun(estado, simulaciones=3000):
    p1, pe, p2 = probabilidades_conjuntas(
        estado, simulaciones
    )

    probabilidades = [p1, pe, p2]

    capacidades = [
        max(0, saldo - 2)
        for saldo in estado["saldos_iniciales"]
    ]

    def evaluar(q1, q2):
        if not (0 <= q1 <= capacidades[0]):
            raise ValueError("Apuesta no valida del jugador 1.")

        if not (0 <= q2 <= capacidades[1]):
            raise ValueError("Apuesta no valida del jugador 2.")

        aporte = 2 + min(q1, q2)

        beneficios1 = [aporte, 0, -aporte]
        beneficios2 = [-aporte, 0, aporte]

        resumen1 = resumir_beneficios(
            beneficios1, probabilidades
        )

        resumen2 = resumir_beneficios(
            beneficios2, probabilidades
        )

        return resumen1, resumen2

    def mu1(q1, q2):
        return evaluar(q1, q2)[0]["beneficio_esperado"]

    def mu2(q1, q2):
        return evaluar(q1, q2)[1]["beneficio_esperado"]

    def R1(q1, q2):
        return evaluar(q1, q2)[0]["cvar"]

    def R2(q1, q2):
        return evaluar(q1, q2)[1]["cvar"]

    return mu1, mu2, R1, R2, capacidades


# Comprobacion del modelo comun
mu1_c, mu2_c, R1_c, R2_c, capacidades_c = (
    crear_modelo_comun(estado_modelo)
)

print("\nModelo economico comun:")

for q1, q2 in [(0, 0), (5, 5), (10, 10),
               (20, 20), (50, 50)]:

    media1 = mu1_c(q1, q2)
    media2 = mu2_c(q1, q2)

    print(
        f"q1={q1}, q2={q2} | "
        f"J1={media1:.3f} | "
        f"J2={media2:.3f} | "
        f"CVaR1={R1_c(q1, q2):.3f} | "
        f"CVaR2={R2_c(q1, q2):.3f}"
    )

    assert abs(media1 + media2) < 1e-10


# Validacion matematica de las funciones economicas

def validar_modelo(mu1, mu2, R1, R2, capacidades):
    pruebas = [
        (0, 0),
        (5, 5),
        (10, 20),
        (20, 10),
        (48, 48),
        (50, 50)
    ]

    print("\nValidacion del modelo economico:")

    for q1, q2 in pruebas:
        if q1 > capacidades[0] or q2 > capacidades[1]:
            continue

        beneficio1 = mu1(q1, q2)
        beneficio2 = mu2(q1, q2)
        riesgo1 = R1(q1, q2)
        riesgo2 = R2(q1, q2)

        # Conservacion del beneficio
        assert abs(beneficio1 + beneficio2) < 1e-8

        # Riesgo no superior a la perdida maxima posible
        aporte = 2 + min(q1, q2)
        assert riesgo1 <= aporte + 1e-8
        assert riesgo2 <= aporte + 1e-8

        print(
            f"q1={q1:>2}, q2={q2:>2} | "
            f"Suma beneficios={beneficio1 + beneficio2:.4f} | "
            f"CVaR1={riesgo1:.2f} | "
            f"CVaR2={riesgo2:.2f} | Correcto"
        )

    # La apuesta no igualada no modifica los resultados
    assert abs(mu1(10, 20) - mu1(10, 10)) < 1e-8
    assert abs(mu2(20, 10) - mu2(10, 10)) < 1e-8

    print("\nTodas las comprobaciones superadas.")


validar_modelo(mu1_c, mu2_c, R1_c, R2_c, capacidades_c)


# Resumen de parametros y funciones del modelo

def mostrar_ficha_modelo(estado, capacidades):
    print("\n========== FICHA DEL MODELO ==========")

    print("\n1. Caracteristicas de la partida")
    print("Modalidad: Texas Hold'em, dos jugadores")
    print("Capital inicial:", PARAMETROS["capital_inicial"])
    print("Ciega pequena:", PARAMETROS["ciega_pequena"])
    print("Ciega grande:", PARAMETROS["ciega_grande"])
    print("Maximo de manos:", PARAMETROS["maximo_manos"])
    print("Comision:", PARAMETROS["comision"])

    print("\n2. Capacidades de apuesta")
    print("Capacidad jugador 1:", capacidades[0])
    print("Capacidad jugador 2:", capacidades[1])

    print("\n3. Restricciones del modelo")
    print("Confianza CVaR:", PARAMETROS["confianza_cvar"])
    print("Limite CVaR jugador 1:",
          PARAMETROS["limite_cvar_jugador1"])
    print("Beneficio minimo jugador 2:",
          PARAMETROS["beneficio_minimo_jugador2"])

    print("\n4. Informacion de la mano")
    print("Cartas jugador 1:", estado["manos"][0])
    print("Cartas jugador 2:", estado["manos"][1])
    print("Cartas comunitarias:", estado["mesa"])

    print("\n5. Funciones disponibles")
    print("mu1(q1, q2): beneficio esperado J1")
    print("mu2(q1, q2): beneficio esperado J2")
    print("R1(q1, q2): CVaR jugador 1")
    print("R2(q1, q2): CVaR jugador 2")

    print("\n6. Hipotesis del modelo comun")
    print("Ambos jugadores llegan al showdown.")
    print("Las apuestas no igualadas se devuelven.")
    print("No se consideran retiradas ni faroles.")
    print("Se utilizan probabilidades conjuntas.")
    print("q1 y q2 representan fichas adicionales.")

    print("\n======================================")


mostrar_ficha_modelo(estado_modelo, capacidades_c)
from optimizacion_cournot_poker import *

graficar_br(
    mu1_c,
    mu2_c,
    R1_c,
    R2_c,
    capacidades_c[0],
    capacidades_c[1]
)

imprimir_resultados(
    mu1_c,
    mu2_c,
    R1_c,
    R2_c,
    capacidades_c[0],
    capacidades_c[1]
)
