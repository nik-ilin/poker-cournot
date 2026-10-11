import csv
import json
from dataclasses import asdict

from .game import Config, Observation, deal, initial, legal, settle, step
from .policy import decide


def session(
    cfg=Config(),
    strategy="risk",
    opponent="stable",
    seed=10000,
    limit=10.0,
    minimum=5.0,
    model="stable",
):
    balances = (cfg.capital, cfg.capital)
    rows = []
    for hand in range(1, cfg.hands + 1):
        holes, board = deal(seed, hand)
        s = initial(balances, (hand - 1) % 2)
        events = []
        while not s.terminal:
            i = s.actor
            kind = (
                strategy
                if i == 0
                else ("stable" if hand <= cfg.hands // 2 else "loose")
                if opponent == "changing"
                else opponent
            )
            action, info = decide(
                Observation(s, holes[i], cfg.raises),
                kind,
                cfg,
                f"policy-v1:{seed}:{hand}:{s.steps}:{i}",
                limit,
                minimum,
                model,
            )
            events.append(
                {
                    "player": i + 1,
                    "action": action,
                    "paid_before": s.paid,
                    "pot_before": sum(s.paid),
                    "legal": legal(s, cfg.raises),
                    **info,
                }
            )
            s = step(s, action, cfg.raises)
        end = settle(s, holes, board)
        rows.append(
            dict(
                strategy=f"{strategy}:R={limit}:m={minimum}:v1",
                opponent=opponent,
                condition=f"assumed_{model}",
                session_id=str(seed),
                hand=hand,
                bankroll_1=end[0],
                bankroll_2=end[1],
                seed=seed,
                deal_id=f"v1:{seed}:{hand}",
                profit_1=end[0] - balances[0],
                holes=holes,
                board=board,
                events=events,
                paid=s.paid,
                pot=2 * min(s.paid),
                refund=abs(s.paid[0] - s.paid[1]),
                folded=s.folded,
                small=s.small + 1,
                config=asdict(cfg),
            )
        )
        balances = end
        if min(balances) == 0:
            break
    return rows


def export(path, rows):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            {
                k: json.dumps(v) if isinstance(v, (tuple, list, dict)) else v
                for k, v in r.items()
            }
            for r in rows
        )
