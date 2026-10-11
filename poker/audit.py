"""Auditoría de registros completos y reproducción de una selección prefijada."""

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from .game import Config, initial, legal, settle, step
from .simulation import session


def audit(directory):
    root = Path(directory)
    manifest = json.loads((root / "manifest.json").read_text())
    cfg = Config(
        **(manifest["config"] | {"raises": tuple(manifest["config"]["raises"])})
    )
    n = manifest["n_per_cell"]
    seed0 = manifest["seed_start"]
    last = {}
    counts = defaultdict(int)
    deals = {}
    examples = defaultdict(list)
    hands = 0
    groups = defaultdict(set)
    with (root / "hands.csv").open() as f:
        for row in csv.DictReader(f):
            key = (row["strategy"], row["opponent"], row["session_id"])
            hand = int(row["hand"])
            hands += 1
            before = last.get(key, (cfg.capital, cfg.capital))
            assert min(before) > 0
            assert hand == counts[key] + 1
            holes = tuple(tuple(tuple(c) for c in h) for h in json.loads(row["holes"]))
            board = tuple(tuple(c) for c in json.loads(row["board"]))
            assert len(set(holes[0] + holes[1] + board)) == 9
            identity = (row["session_id"], hand)
            assert deals.setdefault(identity, (holes, board)) == (holes, board)
            s = initial(before, (hand - 1) % 2)
            for event in json.loads(row["events"]):
                assert event["player"] == s.actor + 1
                assert tuple(event["paid_before"]) == s.paid
                assert event["pot_before"] == sum(s.paid)
                assert tuple(event["legal"]) == legal(s, cfg.raises)
                if event["status"] != "reference":
                    assert event["action"] == event["selected"]["action"]
                    if (
                        row["strategy"].startswith("risk")
                        and event["player"] == 1
                        and event["status"] == "feasible"
                    ):
                        assert event["selected"]["cvar"] <= event["limit"] + 1e-9
                s = step(s, event["action"], cfg.raises)
            assert s.terminal
            after = (int(row["bankroll_1"]), int(row["bankroll_2"]))
            assert after == settle(s, holes, board)
            assert sum(after) == 2 * cfg.capital and min(after) >= 0
            assert int(row["profit_1"]) == after[0] - before[0]
            assert int(row["pot"]) == 2 * min(s.paid)
            assert int(row["refund"]) == abs(s.paid[0] - s.paid[1])
            counts[key] += 1
            last[key] = after
            groups[key[:2]].add(key[2])
            if int(key[2]) in (seed0, seed0 + n - 1):
                examples[key].append(row)
    assert len(groups) == 15 and all(len(ids) == n for ids in groups.values())
    assert all(counts[k] == cfg.hands or min(v) == 0 for k, v in last.items())
    paired = 0
    for key, value in last.items():
        if key[0].startswith("profit:"):
            peer = (key[0].replace("profit:R=10:", "risk:R=30:"), key[1], key[2])
            assert last[peer] == value and counts[peer] == counts[key]
            paired += 1
    for (strategy, opponent, seed), expected in examples.items():
        kind = strategy.split(":")[0]
        limit = int(strategy.split(":")[1].split("=")[1])
        actual = session(cfg, kind, opponent, int(seed), limit)
        assert len(actual) == len(expected)
        for a, e in zip(actual, expected):
            assert a["bankroll_1"] == int(e["bankroll_1"])
            assert a["bankroll_2"] == int(e["bankroll_2"])
            old = json.loads(e["events"])
            new = json.loads(json.dumps(a["events"]))
            for event in old + new:
                event.pop("seconds")
            assert old == new
    base = Path(__file__).resolve().parents[1]
    hashes = {
        str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted((base / "poker").glob("*.py"))
    }
    result = dict(
        hands_checked=hands,
        sessions_checked=len(last),
        cells=len(groups),
        paired_profit_r30_checked=paired,
        replayed_sessions=len(examples),
        all_checks_passed=True,
        source_sha256=hashes,
    )
    (root / "audit.json").write_text(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("directory")
    print(json.dumps(audit(p.parse_args().directory), indent=2))
