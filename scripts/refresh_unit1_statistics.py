"""Recalcula únicamente resúmenes estadísticos desde registros existentes."""
import csv
import hashlib
import json
from pathlib import Path

from poker.academic import _summarize_stability, _write_csv, _write_json


def refresh(folder):
    folder = Path(folder)
    source = folder / "stability_runs.json"
    before = source.read_bytes()
    records = json.loads(before)
    removed = "eval_cvar_standard_error_approx"
    for row in records:
        row.pop(removed, None)
    _, estimates = _summarize_stability(records)
    _write_csv(folder / "stability_estimates.csv", estimates)
    _write_json(source, records)
    # Preserve all other CSV fields verbatim, including original timings.
    for name in ("stability_runs.csv", "stability_external.csv", "stability_external_summary.csv"):
        with (folder / name).open(newline="") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            for key in (removed, "cvar_standard_error_approx", "average_cvar_mc_se_approx"):
                row.pop(key, None)
        _write_csv(folder / name, rows)
    manifest = json.loads((folder / "manifest.json").read_text())
    manifest.setdefault("statistics_correction", {
        "source": "stability_runs.json from original experiment; no scenarios regenerated",
        "source_sha256_before_correction": hashlib.sha256(before).hexdigest(),
        "method": "mean of within-observation sample SD across distinct planner seeds, by action and S",
        "missing": "fewer than two seeds: not estimable; excluded from average, counts reported",
        "cvar_evaluation_uncertainty": "no standard error provided",
        "figures": "stability.png unchanged: only action/feasibility changes and original timings",
    })
    _write_json(folder / "manifest.json", manifest)


if __name__ == "__main__":
    for folder in ("results/unit1/stability", "results/unit1/stability-pilot"):
        refresh(folder)
