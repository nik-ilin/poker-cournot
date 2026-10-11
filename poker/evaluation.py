"""Reutilización explícita del contrato y evaluador de main."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "legacy_evaluator", Path(__file__).resolve().parents[1] / "estudio-poker/estudio.py"
)
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)


def evaluate(path, cfg, out):
    config = dict(
        initial_bankroll_each=cfg.capital,
        max_hands=cfg.hands,
        alpha=cfg.alpha,
        risk_limit=None,
        variant="Hold’em finito: una ronda preflop",
    )
    sessions = legacy.read_sessions(path, config)
    details, summary, trajectories = legacy.summarize(sessions, config)
    for name, rows in [
        ("sessions", details),
        ("summary", summary),
        ("trajectories", trajectories),
    ]:
        legacy.write_csv(out / f"{name}.csv", rows, list(rows[0]))
    legacy.report(out / "report.html", summary, trajectories, config)
    return details, summary, trajectories
