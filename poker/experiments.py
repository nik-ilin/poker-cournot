import json
import math
import random
import time
from dataclasses import asdict
from pathlib import Path
from statistics import mean, stdev

from .evaluation import evaluate, legacy
from .exposure import analyze
from .game import Config
from .risk import cvar
from .simulation import export, session


def run(out, n=200, scenarios=Config().scenarios, base=10000):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    cfg = Config(scenarios=scenarios)
    started = time.perf_counter()
    rows = []
    diagnostics = []
    variants = [("fixed", 10), ("profit", 10), ("risk", 2), ("risk", 10), ("risk", 30)]
    for opponent in ("stable", "loose", "changing"):
        for strategy, limit in variants:
            group = []
            begin = time.perf_counter()
            for j in range(n):
                group.extend(session(cfg, strategy, opponent, base + j, limit))
            events = [e for r in group for e in r["events"] if e["player"] == 1]
            emergency = sum(e["status"] == "infeasible_emergency" for e in events)
            predicted = [e for e in events if "selected" in e]
            excess = sum(e["selected"]["cvar"] > limit + 1e-9 for e in predicted)
            diagnostics.append(
                dict(
                    strategy=group[0]["strategy"],
                    opponent=opponent,
                    decisions=len(events),
                    infeasible=emergency,
                    predicted_decisions=len(predicted),
                    predicted_risk_excess_count=excess,
                    emergency_frequency=emergency / len(events),
                    mean_decision_seconds=mean(e["seconds"] for e in events),
                    experiment_seconds=time.perf_counter() - begin,
                )
            )
            rows.extend(group)
            print(opponent, strategy, limit, "complete", flush=True)
    export(out / "hands.csv", rows)
    details, summary, trajectories = evaluate(out / "hands.csv", cfg, out)
    legacy.write_csv(out / "diagnostics.csv", diagnostics, list(diagnostics[0]))
    uncertainty = []
    for group in summary:
        profits = [
            r["profit"]
            for r in details
            if r["strategy"] == group["strategy"] and r["opponent"] == group["opponent"]
        ]
        rng = random.Random(f"bootstrap-v1:{group['strategy']}:{group['opponent']}")
        samples = [rng.choices(profits, k=n) for _ in range(1000)]
        means = sorted(mean(x) for x in samples)
        risks = sorted(cvar([-v for v in x], cfg.alpha) for x in samples)
        uncertainty.append(
            dict(
                strategy=group["strategy"],
                opponent=group["opponent"],
                bootstrap_repetitions=1000,
                mean_low=means[24],
                mean_high=means[974],
                cvar_low=risks[24],
                cvar_high=risks[974],
                tail_observations=math.ceil(n * (1 - cfg.alpha) - 1e-9),
            )
        )
    legacy.write_csv(out / "uncertainty.csv", uncertainty, list(uncertainty[0]))
    # Pares válidos: mismos mazos exógenos, política reiniciada; bloques independientes.
    paired = []
    for opponent in ("stable", "loose", "changing"):
        baseline = {
            r["session_id"]: r["profit"]
            for r in details
            if r["opponent"] == opponent and r["strategy"].startswith("fixed:")
        }
        for strategy in sorted(
            {r["strategy"] for r in details if not r["strategy"].startswith("fixed:")}
        ):
            diffs = [
                r["profit"] - baseline[r["session_id"]]
                for r in details
                if r["opponent"] == opponent and r["strategy"] == strategy
            ]
            se = stdev(diffs) / math.sqrt(n) if n > 1 else None
            paired.append(
                dict(
                    opponent=opponent,
                    strategy=strategy,
                    n=n,
                    mean_difference=mean(diffs),
                    paired_se=se,
                    normal_95_low=mean(diffs) - 1.96 * se if se is not None else None,
                    normal_95_high=mean(diffs) + 1.96 * se if se is not None else None,
                )
            )
    legacy.write_csv(out / "paired.csv", paired, list(paired[0]))
    exposure = analyze()
    (out / "exposure.json").write_text(json.dumps(exposure, indent=2))
    (out / "manifest.json").write_text(
        json.dumps(
            dict(
                config=asdict(cfg),
                n_per_cell=n,
                cells=15,
                seed_start=base,
                seed_end=base + n - 1,
                pilot_seeds="100..102",
                parameter_selection="predefined; no outcome-based tuning",
                seconds=time.perf_counter() - started,
                version="v1",
            ),
            indent=2,
        )
    )
    from .figures import render

    render(out)
    return summary
