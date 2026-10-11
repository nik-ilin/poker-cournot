"""Riesgo discreto, con masa de frontera exacta."""

import math


def cvar(losses, alpha=0.9, probabilities=None):
    losses = list(losses)
    p = (
        list(probabilities)
        if probabilities is not None
        else [1 / len(losses)] * len(losses)
        if losses
        else []
    )
    if not losses or len(p) != len(losses) or not 0 <= alpha < 1:
        raise ValueError("Distribución o alpha inválidos")
    if (
        any(not math.isfinite(x) for x in losses + p)
        or any(x < 0 for x in p)
        or abs(sum(p) - 1) > 1e-9
    ):
        raise ValueError(
            "Probabilidades finitas, no negativas y de suma uno requeridas"
        )
    remaining = 1 - alpha
    total = 0.0
    for loss, weight in sorted(zip(losses, p), reverse=True):
        used = min(remaining, weight)
        total += used * loss
        remaining -= used
        if remaining <= 1e-15:
            break
    return total / (1 - alpha)
