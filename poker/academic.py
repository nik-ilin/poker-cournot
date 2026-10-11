"""Experimentos reproducibles para la conexión del CVaR con Unidad 1."""

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import random
import statistics
import tempfile
import time
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "poker-cournot-mpl"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy
import scipy

from .cards import DECK
from .cvar_lp import certify_cvar
from .game import Config, Observation, deal, initial, step
from .policy import evaluate_actions, select

ALPHA = 0.90
MODEL = "stable"
RISK_LIMIT = 10.0
RAISES = (10, 30)


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def _write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _scenarios(obs, seed, count):
    unknown = [card for card in DECK if card not in obs.own]
    rng = random.Random(seed)
    return [tuple(rng.sample(unknown, 7)) for _ in range(count)]


def _mean_se(values):
    return statistics.stdev(values) / math.sqrt(len(values)) if len(values) > 1 else 0.0


def _cvar_tail_se(losses, alpha):
    """Error estándar de la media de cola, aproximación por masa fraccionaria."""
    mass = 1.0 - alpha
    remaining = mass
    tail = []
    for loss in sorted(losses, reverse=True):
        used = min(1.0 / len(losses), remaining)
        if used > 0:
            tail.append((loss, used / mass))
            remaining -= used
        if remaining <= 1e-15:
            break
    center = sum(x * w for x, w in tail)
    variance = sum(w * (x - center) ** 2 for x, w in tail)
    effective_n = mass * len(losses)
    return math.sqrt(variance / effective_n) if effective_n > 1 else 0.0


def _observation(seed, capital, small, actor_mode):
    cfg = Config(capital=capital, hands=1, alpha=ALPHA, scenarios=32, raises=RAISES)
    holes, _ = deal(seed, 1)
    state = initial((capital, capital), small)
    if actor_mode == "big_blind_unraised":
        state = step(state, "call", cfg.raises)
    elif actor_mode == "big_blind_facing_raise":
        raise_action = next(a for a in cfg.raises if a > max(state.paid))
        state = step(state, f"raise:{raise_action}", cfg.raises)
    elif actor_mode == "small_blind_facing_raise":
        state = step(state, "call", cfg.raises)
        raise_action = next(a for a in cfg.raises if a > max(state.paid))
        state = step(state, f"raise:{raise_action}", cfg.raises)
    obs = Observation(state, holes[state.actor], cfg.raises)
    return cfg, obs


def make_stability_observations():
    # Estratos fijados antes de observar resultados; no se selecciona por beneficio.
    specs = [
        (710001, 455, 0, "small_blind_unraised"),
        (710002, 455, 0, "big_blind_unraised"),
        (710003, 455, 0, "big_blind_facing_raise"),
        (710004, 455, 1, "small_blind_facing_raise"),
        (710005, 120, 0, "small_blind_unraised"),
        (710006, 60, 0, "big_blind_unraised"),
        (710007, 120, 1, "big_blind_facing_raise"),
        (710008, 60, 1, "small_blind_facing_raise"),
    ]
    return [
        (label, seed, *_observation(seed, capital, small, mode))
        for seed, capital, small, mode in specs
        for label in [mode]
    ]


def run_cvar(out):
    out = Path(out)
    run_started = time.perf_counter()
    examples = [
        ("manual_colafraccionaria", [100, 20, -10], [0.05, 0.15, 0.80]),
        ("probabilidades_desiguales", [12, 4, -3], [0.10, 0.25, 0.65]),
        ("empates", [9, 9, 1, -2], [0.10, 0.15, 0.25, 0.50]),
        ("perdidas_negativas", [-5, -2, -10], [0.20, 0.30, 0.50]),
        ("probabilidad_cero", [100, 8, -4], [0.0, 0.25, 0.75]),
    ]
    rows, kkt_rows, results = [], [], {}
    for name, losses, probabilities in examples:
        result = certify_cvar(losses, ALPHA, probabilities)
        results[name] = result
        rows.append(
            {
                "caso": name,
                "n": len(losses),
                "cvar_ordenacion": result["ordered_value"],
                "cvar_primal": result["primal_value"],
                "cvar_dual": result["dual_value"],
                "eta": result["eta"],
                "validado": result["validated"],
                "status_primal": result["solver"]["primal"]["status"],
                "status_dual": result["solver"]["dual"]["status"],
            }
        )
        kkt_rows.append({"caso": name, **result["residuals"], "validado": result["validated"]})
    if not results["manual_colafraccionaria"]["validated"]:
        raise RuntimeError("Falló la certificación del ejemplo manual")
    manual = results["manual_colafraccionaria"]
    assert math.isclose(manual["eta"], 20.0, abs_tol=1e-8)
    assert all(math.isclose(a, b, abs_tol=1e-8) for a, b in zip(manual["u"], [80, 0, 0]))
    assert all(math.isclose(a, b, abs_tol=1e-8) for a, b in zip(manual["z"], [0.5, 0.5, 0]))

    cfg, obs = _observation(720001, 455, 0, "small_blind_unraised")
    scenarios = _scenarios(obs, "unit1-cvar-real-actions-v1", 32)
    action_results = evaluate_actions(obs, cfg, scenarios, MODEL)
    action_rows = []
    action_kkt_rows = []
    for candidate in action_results:
        certificate = certify_cvar(candidate["losses"], cfg.alpha)
        if not certificate["validated"]:
            raise RuntimeError(f"KKT no validado para acción {candidate['action']}")
        action_rows.append(
            {
                "action": candidate["action"],
                "n_escenarios": len(scenarios),
                "beneficio_medio": candidate["mean"],
                "cvar_ordenacion": certificate["ordered_value"],
                "cvar_primal": certificate["primal_value"],
                "cvar_dual": certificate["dual_value"],
                "brecha_primal_dual": certificate["residuals"]["primal_dual_gap"],
                "validado": certificate["validated"],
            }
        )
        action_kkt_rows.append(
            {"accion": candidate["action"], **certificate["residuals"], "validado": certificate["validated"]}
        )
        results[f"action_{candidate['action']}"] = certificate
    _write_csv(out / "cvar_examples.csv", rows)
    _write_csv(out / "cvar_project_actions.csv", action_rows)
    _write_csv(out / "cvar_kkt_residuals.csv", kkt_rows)
    _write_csv(out / "cvar_project_kkt_residuals.csv", action_kkt_rows)
    _write_json(out / "cvar_certificates.json", results)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    order = sorted(range(len(manual["losses"])), key=lambda i: manual["losses"][i], reverse=True)
    xs = [str(i + 1) for i in order]
    ax.bar(xs, [manual["losses"][i] for i in order], color="#6b8db5", label="Pérdida")
    ax.set_xlabel("Escenario, ordenado por pérdida decreciente")
    ax.set_ylabel("Pérdida (fichas)")
    ax.set_title("CVaR 0,90: masa dual concentrada en la cola")
    ax2 = ax.twinx()
    ax2.plot(xs, [manual["z"][i] for i in order], "o-", color="#c44e52", label="Peso dual $z_s$")
    ax2.set_ylabel("Peso dual $z_s$")
    ax.legend(loc="upper right")
    ax2.legend(loc="upper center")
    fig.tight_layout()
    fig.savefig(out / "cvar_dual_tail.png", dpi=160)
    plt.close(fig)
    _write_json(
        out / "manifest.json",
        {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "scipy": scipy.__version__,
            "numpy": numpy.__version__,
            "alpha": ALPHA,
            "solver": "scipy.optimize.linprog(method=highs), primal and dual",
            "atol": 1e-8,
            "rtol": 1e-8,
            "manual_cases": [name for name, _, _ in examples],
            "project_observation_deal_seed": 720001,
            "project_scenario_seed": "unit1-cvar-real-actions-v1",
            "project_scenarios": 32,
            "continuation_model": MODEL,
            "wall_seconds": time.perf_counter() - run_started,
        },
    )
    return {"cases": len(rows), "project_actions": len(action_rows), "all_validated": all(r["validado"] for r in rows + action_rows)}


def run_sensitivity(out, scenarios_n=128):
    out = Path(out)
    run_started = time.perf_counter()
    cfg, obs = _observation(730001, 455, 0, "small_blind_unraised")
    scenario_seed = "unit1-sensitivity-fixed-scenarios-v1"
    scenarios = _scenarios(obs, scenario_seed, scenarios_n)
    evaluated = evaluate_actions(obs, cfg, scenarios, MODEL)
    thresholds = sorted({round(c["cvar"], 12) for c in evaluated})
    points = []
    smallest_gap = min((b - a for a, b in zip(thresholds, thresholds[1:])), default=1.0)
    epsilon = min(1e-5, smallest_gap / 4)
    risks = [thresholds[0] - epsilon]
    for threshold in thresholds:
        risks.extend((threshold - epsilon, threshold, threshold + epsilon))
    risks.append(thresholds[-1] + epsilon)
    for limit in sorted(set(risks)):
        feasible = [c for c in evaluated if c["cvar"] <= limit + 1e-9]
        if feasible:
            chosen = min(feasible, key=lambda c: (-c["mean"], c["cvar"]))
            points.append(
                {
                    "R": limit,
                    "feasible": True,
                    "acciones_factibles": [c["action"] for c in feasible],
                    "accion": chosen["action"],
                    "objetivo_beneficio_medio": chosen["mean"],
                    "cvar_accion": chosen["cvar"],
                    "holgura": limit - chosen["cvar"],
                    "alternativa_emergencia": None,
                }
            )
        else:
            emergency, _ = select(evaluated, "risk", limit, 0.0)
            points.append(
                {
                    "R": limit,
                    "feasible": False,
                    "acciones_factibles": [],
                    "accion": None,
                    "objetivo_beneficio_medio": None,
                    "cvar_accion": None,
                    "holgura": None,
                    "alternativa_emergencia": emergency["action"],
                }
            )
    feasible_values = [p["objetivo_beneficio_medio"] for p in points if p["feasible"]]
    monotone = all(b >= a - 1e-10 for a, b in zip(feasible_values, feasible_values[1:]))
    if not monotone:
        raise AssertionError("V(R) disminuyó al relajar la cota en la misma muestra")
    _write_json(
        out / "sensitivity.json",
        {
            "observation_protocol": {
                "seed_deal": 730001,
                "hand": 1,
                "actor": obs.public.actor,
                "position": "ciega_pequena",
                "capital_each": 455,
                "preflop": "sin subida rival; estado inicial",
                "own_cards": obs.own,
                "scenario_seed": scenario_seed,
                "scenario_count": scenarios_n,
                "scenario_sha256": hashlib.sha256(
                    repr(scenarios).encode()
                ).hexdigest(),
                "selection": "observación ilustrativa predeterminada por protocolo, no representativa",
            },
            "actions": evaluated,
            "epsilon": epsilon,
            "monotone_on_feasible_points": monotone,
            "points": points,
            "interpretation": "Emergencia mostrada aparte; no se incluye en V(R).",
        },
    )
    _write_csv(out / "sensitivity.csv", points)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = [p["R"] for p in points if p["feasible"]]
    y = [p["objetivo_beneficio_medio"] for p in points if p["feasible"]]
    ax.step(x, y, where="post", color="#276749", linewidth=2, label="$V(R)$ factible")
    for c in evaluated:
        ax.axvline(c["cvar"], color="#999999", alpha=0.35, linestyle=":")
        ax.annotate(c["action"], (c["cvar"], max(y) if y else 0), rotation=90, va="top")
    if thresholds[0] > 0:
        ax.axvspan(thresholds[0] - epsilon, thresholds[0], color="#c44e52", alpha=0.13, label="Sin acción factible")
    ax.set_xlabel("Límite local de CVaR $R$ (fichas de pérdida)")
    ax.set_ylabel("Máximo beneficio neto medio estimado (fichas)")
    ax.set_title("Sensibilidad discreta con escenarios congelados")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "sensitivity_step.png", dpi=160)
    plt.close(fig)
    _write_json(
        out / "manifest.json",
        {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "scipy": scipy.__version__,
            "numpy": numpy.__version__,
            "alpha": ALPHA,
            "deal_seed": 730001,
            "scenario_seed": scenario_seed,
            "scenario_count": scenarios_n,
            "continuation_model": MODEL,
            "wall_seconds": time.perf_counter() - run_started,
            "risk_thresholds": thresholds,
            "epsilon_before_after": epsilon,
        },
    )
    return {"actions": len(evaluated), "thresholds": thresholds, "monotone": monotone, "infeasible_points": sum(not p["feasible"] for p in points)}


def _summarize_stability(records):
    ref = {(r["observation"], r["planner_seed"]): r for r in records if r["S"] == 512}
    summaries, estimate_rows = [], []
    for size in (32, 128, 512):
        selected, changed, changed_feas, emergencies = [], 0, 0, 0
        grouped = {}
        for row in records:
            if row["S"] != size:
                continue
            selected.append(row)
            baseline = ref[(row["observation"], row["planner_seed"])]
            changed += row["action"] != baseline["action"]
            changed_feas += set(row["feasible_actions"]) != set(baseline["feasible_actions"])
            emergencies += row["emergency"]
            for action, values in row["estimates"].items():
                grouped.setdefault(action, []).append(values)
        summaries.append(
            {
                "S": size,
                "decision_count": len(selected),
                "action_changes_vs_S512": changed / len(selected),
                "feasible_set_changes_vs_S512": changed_feas / len(selected),
                "emergency_frequency": emergencies / len(selected),
                "mean_decision_seconds": statistics.mean(r["seconds"] for r in selected),
                "median_decision_seconds": statistics.median(r["seconds"] for r in selected),
            }
        )
        for action, values in sorted(grouped.items()):
            means = [v["mean"] for v in values]
            risks = [v["cvar"] for v in values]
            estimate_rows.append(
                {
                    "S": size,
                    "action": action,
                    "n_observation_seed": len(values),
                    "mean_estimate_average": statistics.mean(means),
                    "mean_estimate_sd": statistics.stdev(means) if len(means) > 1 else 0,
                    "cvar_estimate_average": statistics.mean(risks),
                    "cvar_estimate_sd": statistics.stdev(risks) if len(risks) > 1 else 0,
                }
            )
    return summaries, estimate_rows


def run_stability(out, observations_n=8, planner_seeds_n=5, evaluation_scenarios=2048):
    if not 1 <= observations_n <= 8 or planner_seeds_n < 1 or evaluation_scenarios < 100:
        raise ValueError("Configuración de estabilidad fuera de rango")
    out = Path(out)
    run_started = time.perf_counter()
    specs = make_stability_observations()[:observations_n]
    records, external, observation_manifest = [], [], []
    planner_seeds = [f"planner-v1:{760000 + i}" for i in range(planner_seeds_n)]
    for obs_index, (label, deal_seed, cfg, obs) in enumerate(specs, start=1):
        observation_id = f"obs{obs_index:02d}"
        observation_manifest.append(
            {
                "id": observation_id,
                "stratum": label,
                "deal_seed": deal_seed,
                "actor": obs.public.actor,
                "small": obs.public.small,
                "start": obs.public.start,
                "paid": obs.public.paid,
                "raised": obs.public.raised,
                "history": obs.public.history,
                "own_cards": obs.own,
                "legal_actions": __import__("poker.game", fromlist=["legal"]).legal(obs.public, obs.raises),
            }
        )
        eval_scenarios = _scenarios(obs, f"independent-eval-v1:{deal_seed}", evaluation_scenarios)
        eval_actions = evaluate_actions(obs, cfg, eval_scenarios, MODEL)
        eval_map = {c["action"]: c for c in eval_actions}
        for seed in planner_seeds:
            all_scenarios = _scenarios(obs, seed, 512)
            for size in (32, 128, 512):
                begin = time.perf_counter()
                candidates = evaluate_actions(obs, cfg, all_scenarios[:size], MODEL)
                chosen, feasible = select(candidates, "risk", RISK_LIMIT, 0.0)
                seconds = time.perf_counter() - begin
                eval_chosen = eval_map[chosen["action"]]
                eval_feasible = [c for c in eval_actions if c["cvar"] <= RISK_LIMIT + 1e-9]
                benchmark = max(eval_feasible, key=lambda c: c["mean"]) if eval_feasible else None
                records.append(
                    {
                        "observation": observation_id,
                        "planner_seed": seed,
                        "S": size,
                        "action": chosen["action"],
                        "feasible": feasible,
                        "emergency": not feasible,
                        "feasible_actions": [c["action"] for c in candidates if c["cvar"] <= RISK_LIMIT + 1e-9],
                        "train_mean": chosen["mean"],
                        "train_cvar": chosen["cvar"],
                        "eval_mean": eval_chosen["mean"],
                        "eval_cvar": eval_chosen["cvar"],
                        "eval_feasible": eval_chosen["cvar"] <= RISK_LIMIT + 1e-9,
                        "eval_mean_standard_error": _mean_se([ -x for x in eval_chosen["losses"] ]),
                        "eval_cvar_standard_error_approx": _cvar_tail_se(
                            eval_chosen["losses"], ALPHA
                        ),
                        "eval_cvar_tail_observations": evaluation_scenarios * (1 - ALPHA),
                        "eval_mean_regret_vs_feasible_action": (benchmark["mean"] - eval_chosen["mean"]) if benchmark else None,
                        "seconds": seconds,
                        "estimates": {c["action"]: {"mean": c["mean"], "cvar": c["cvar"]} for c in candidates},
                    }
                )
                external.append(
                    {
                        "observation": observation_id,
                        "planner_seed": seed,
                        "S": size,
                        "selected_action": chosen["action"],
                        "independent_mean": eval_chosen["mean"],
                        "independent_cvar": eval_chosen["cvar"],
                        "independent_feasible": eval_chosen["cvar"] <= RISK_LIMIT + 1e-9,
                        "mean_standard_error": _mean_se([-x for x in eval_chosen["losses"]]),
                        "cvar_standard_error_approx": _cvar_tail_se(eval_chosen["losses"], ALPHA),
                        "feasible_action_benchmark_mean": benchmark["mean"] if benchmark else None,
                        "mean_regret": (benchmark["mean"] - eval_chosen["mean"]) if benchmark else None,
                        "evaluation_scenarios": evaluation_scenarios,
                        "tail_scenario_mass_count": evaluation_scenarios * (1 - ALPHA),
                    }
                )
    summaries, estimate_rows = _summarize_stability(records)
    _write_json(out / "observations.json", observation_manifest)
    # JSON compacto conserva las estimaciones accion-por-acción para reproducir tablas.
    _write_json(out / "stability_runs.json", records)
    flat = [{k: v for k, v in row.items() if k != "estimates"} for row in records]
    _write_csv(out / "stability_runs.csv", flat)
    _write_csv(out / "stability_external.csv", external)
    _write_csv(out / "stability_summary.csv", summaries)
    _write_csv(out / "stability_estimates.csv", estimate_rows)
    external_summary = []
    for size in (32, 128, 512):
        group = [r for r in external if r["S"] == size]
        means = [r["independent_mean"] for r in group]
        risks = [r["independent_cvar"] for r in group]
        regrets = [r["mean_regret"] for r in group if r["mean_regret"] is not None]
        external_summary.append(
            {
                "S": size,
                "observation_seed_pairs": len(group),
                "independent_mean_average": statistics.mean(means),
                "independent_mean_sd_across_fixtures": statistics.stdev(means) if len(means) > 1 else 0,
                "average_mean_mc_se": statistics.mean(r["mean_standard_error"] for r in group),
                "independent_cvar_average": statistics.mean(risks),
                "independent_cvar_sd_across_fixtures": statistics.stdev(risks) if len(risks) > 1 else 0,
                "average_cvar_mc_se_approx": statistics.mean(r["cvar_standard_error_approx"] for r in group),
                "empirical_risk_limit_violations": sum(not r["independent_feasible"] for r in group),
                "mean_regret_vs_feasible_sample_benchmark": statistics.mean(regrets) if regrets else None,
            }
        )
    _write_csv(out / "stability_external_summary.csv", external_summary)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.3))
    axes[0].plot([r["S"] for r in summaries], [r["action_changes_vs_S512"] for r in summaries], "o-", label="Acción distinta de S=512")
    axes[0].plot([r["S"] for r in summaries], [r["feasible_set_changes_vs_S512"] for r in summaries], "s--", label="Conjunto factible distinto")
    axes[0].set_xscale("log", base=2)
    axes[0].set_xticks([32, 128, 512], labels=["32", "128", "512"])
    axes[0].set_ylim(-0.05, 1.05)
    axes[0].set_xlabel("Escenarios de planificación S")
    axes[0].set_ylabel("Frecuencia")
    axes[0].legend(fontsize=8)
    axes[1].errorbar(
        [r["S"] for r in summaries],
        [r["mean_decision_seconds"] for r in summaries],
        yerr=[0] * len(summaries),
        marker="o",
    )
    axes[1].set_xscale("log", base=2)
    axes[1].set_xticks([32, 128, 512], labels=["32", "128", "512"])
    axes[1].set_xlabel("Escenarios de planificación S")
    axes[1].set_ylabel("Tiempo medio por decisión (s)")
    fig.suptitle("Estabilidad de planificación; S=512 es referencia de mayor tamaño")
    fig.tight_layout()
    fig.savefig(out / "stability.png", dpi=160)
    plt.close(fig)
    manifest = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "scipy": scipy.__version__,
        "numpy": numpy.__version__,
        "alpha": ALPHA,
        "risk_limit_chips": RISK_LIMIT,
        "rival_continuation": MODEL,
        "raises": RAISES,
        "sizes": [32, 128, 512],
        "planner_seeds": planner_seeds,
        "planner_sampling": "random.Random(seed).sample(unknown_own_deck, 7), one stream per observation and planner seed",
        "evaluation_seed_prefix": "independent-eval-v1:<deal_seed>",
        "observations": observation_manifest,
        "independent_evaluation_scenarios_per_observation": evaluation_scenarios,
        "independent_evaluation_tail_mass_scenarios": evaluation_scenarios * (1 - ALPHA),
        "total_wall_seconds": time.perf_counter() - run_started,
        "common_random_scenarios_across_actions": True,
        "nested_planning_samples_per_seed": True,
        "reference_interpretation": "S=512 solo es referencia de mayor tamaño, no valor verdadero",
        "rule": "No se modifican parámetros según los resultados de evaluación.",
    }
    _write_json(out / "manifest.json", manifest)
    return {"observations": observations_n, "planner_seeds": planner_seeds_n, "runs": len(records), "summary": summaries}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("cvar", "sensitivity", "stability"):
        command = sub.add_parser(name)
        command.add_argument("--out", default=f"results/unit1/{name}")
        if name == "stability":
            command.add_argument("--observations", type=int, default=8)
            command.add_argument("--planner-seeds", type=int, default=5)
            command.add_argument("--evaluation-scenarios", type=int, default=2048)
        if name == "sensitivity":
            command.add_argument("--scenarios", type=int, default=128)
    args = parser.parse_args(argv)
    if args.command == "cvar":
        result = run_cvar(args.out)
    elif args.command == "sensitivity":
        result = run_sensitivity(args.out, args.scenarios)
    else:
        result = run_stability(args.out, args.observations, args.planner_seeds, args.evaluation_scenarios)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
