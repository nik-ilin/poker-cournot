"""Juego de exposición entero; no estrategia de información privada."""

import math

from .risk import cvar


def analyze(
    capacity=30, probabilities=(0.3, 0.1, 0.6), limit=50, minimum=5, alpha=0.9, tol=1e-9
):
    if (
        type(capacity) is not int
        or capacity < 0
        or not all(math.isfinite(v) for v in (limit, minimum, tol))
        or tol < 0
    ):
        raise ValueError("Parámetros de exposición inválidos")
    cvar([1, 0, -1], alpha, probabilities)
    table = {}
    for q1 in range(capacity + 1):
        for q2 in range(capacity + 1):
            a = 2 + min(q1, q2)
            x = (a, 0, -a)
            mu = sum(v * p for v, p in zip(x, probabilities))
            table[q1, q2] = (
                mu,
                -mu,
                cvar([-v for v in x], alpha, probabilities),
                cvar(x, alpha, probabilities),
            )
    br1 = {}
    br2 = {}
    for other in range(capacity + 1):
        f1 = [q for q in range(capacity + 1) if table[q, other][2] <= limit + tol]
        f2 = [q for q in range(capacity + 1) if table[other, q][1] >= minimum - tol]
        best1 = max((table[q, other][0] for q in f1), default=None)
        best2 = min((table[other, q][3] for q in f2), default=None)
        br1[other] = [q for q in f1 if best1 - table[q, other][0] <= tol]
        br2[other] = [q for q in f2 if table[other, q][3] - best2 <= tol]
    equilibria = []
    for (q1, q2), v in table.items():
        if q1 in br1[q2] and q2 in br2[q1]:
            d1 = max(table[q, q2][0] - v[0] for q in br1[q2])
            d2 = max(v[3] - table[q1, q][3] for q in br2[q1])
            equilibria.append(
                dict(
                    q1=q1,
                    q2=q2,
                    mu1=v[0],
                    mu2=v[1],
                    risk1=v[2],
                    risk2=v[3],
                    deviation1=d1,
                    deviation2=d2,
                )
            )
    return dict(
        capacity=capacity,
        probabilities=probabilities,
        limit=limit,
        minimum=minimum,
        alpha=alpha,
        tolerance=tol,
        br1=br1,
        br2=br2,
        equilibria=equilibria,
        scope="enumeración exhaustiva del juego entero, distribución fija",
    )
