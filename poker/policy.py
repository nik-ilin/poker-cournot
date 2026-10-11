"""Políticas sobre observaciones; enumeración de continuaciones."""

import math
import random
import time
from statistics import mean

from .cards import DECK
from .game import Observation, legal, settle, step
from .risk import cvar


def strength(own):
    a, b = sorted((c[0] for c in own), reverse=True)
    return (
        (a + b) / 28 + (0.35 if a == b else 0) + (0.05 if own[0][1] == own[1][1] else 0)
    )


def fixed(obs, model="stable"):
    actions = legal(obs.public, obs.raises)
    score = strength(obs.own)
    threshold = {"stable": 0.85, "loose": 0.55, "tight": 1.05}[model]
    raises = [a for a in actions if a.startswith("raise")]
    if raises and score >= threshold:
        return raises[-1]
    if "fold" in actions and obs.public.raised and score < threshold - 0.2:
        return "fold"
    return "call"


def select(candidates, kind, limit, minimum, tol=1e-9):
    feasible = [
        c
        for c in candidates
        if kind == "profit"
        or (c["cvar"] <= limit + tol if kind == "risk" else c["mean"] >= minimum - tol)
    ]
    pool = feasible or candidates
    if kind == "minrisk" or not feasible:
        chosen = min(pool, key=lambda c: (c["cvar"], -c["mean"]))
    else:
        chosen = min(pool, key=lambda c: (-c["mean"], c["cvar"]))
    return chosen, bool(feasible)


def evaluate_actions(obs, cfg, scenarios, model="stable"):
    """Evalúa todas las acciones legales sobre exactamente los escenarios dados.

    Expone también las pérdidas por escenario para análisis académicos; la política
    operativa sigue usando CVaR por ordenación y el mismo modelo de continuación.
    """
    if model not in ("stable", "loose", "tight"):
        raise ValueError("Modelo rival desconocido")
    scenarios = tuple(tuple(cards) for cards in scenarios)
    if not scenarios:
        raise ValueError("Se requiere al menos un escenario")
    i = obs.public.actor
    candidates = []
    for action in legal(obs.public, obs.raises):
        profits = []
        for cards in scenarios:
            if len(cards) != 7 or len(set(obs.own + cards)) != 9:
                raise ValueError("Escenario debe contener siete cartas distintas")
            holes = [None, None]
            holes[i] = obs.own
            holes[1 - i] = tuple(cards[:2])
            board = cards[2:]
            s = step(obs.public, action, obs.raises)
            while not s.terminal:
                follow = Observation(s, holes[s.actor], obs.raises)
                s = step(s, fixed(follow, model), obs.raises)
            profits.append(settle(s, holes, board)[i] - s.start[i])
        losses = [-x for x in profits]
        candidates.append(
            {
                "action": action,
                "mean": mean(profits),
                "incremental_mean": mean(profits) + obs.public.paid[i],
                "cvar": cvar(losses, cfg.alpha),
                "losses": losses,
            }
        )
    return candidates


def decide(obs, kind, cfg, seed, limit=10.0, minimum=5.0, model="stable"):
    if not math.isfinite(limit) or not math.isfinite(minimum):
        raise ValueError("Límites finitos requeridos")
    if model not in ("stable", "loose", "tight"):
        raise ValueError("Modelo rival desconocido")
    begin = time.perf_counter()
    if kind in ("fixed", "stable", "loose", "tight"):
        return fixed(obs, "stable" if kind == "fixed" else kind), {
            "status": "reference",
            "seconds": time.perf_counter() - begin,
            "candidates": [],
        }
    if kind not in ("profit", "risk", "minrisk"):
        raise ValueError(kind)
    rng = random.Random(seed)
    unknown = [c for c in DECK if c not in obs.own]
    scenarios = [rng.sample(unknown, 7) for _ in range(cfg.scenarios)]
    candidates = evaluate_actions(obs, cfg, scenarios, model)
    chosen, feasible = select(candidates, kind, limit, minimum)
    diagnostics = [
        {k: v for k, v in c.items() if k != "losses"} for c in candidates
    ]
    selected = {k: v for k, v in chosen.items() if k != "losses"}
    return chosen["action"], {
        "status": "feasible" if feasible else "infeasible_emergency",
        "reason": None if feasible else "no_action_satisfies_sample_constraint",
        "selected": selected,
        "candidates": diagnostics,
        "seconds": time.perf_counter() - begin,
        "scenario_seed": seed,
        "scenarios": cfg.scenarios,
        "model": model,
        "limit": limit,
        "minimum": minimum,
    }
