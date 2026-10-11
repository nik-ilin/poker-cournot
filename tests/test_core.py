import copy

import pytest

from poker.cards import evaluar_cinco, evaluar_mano
from poker.evaluation import evaluate, legacy
from poker.exposure import analyze
from poker.game import Config, Observation, deal, initial, legal, settle, step
from poker.policy import decide, select
from poker.risk import cvar
from poker.simulation import export, session


def cards(ranks, suits=None):
    return tuple(zip(ranks, suits or range(len(ranks))))


@pytest.mark.parametrize(
    "ranks,suits,category",
    [
        ([14, 2, 3, 4, 5], [0] * 5, 8),
        ([9, 9, 9, 9, 2], [0, 1, 2, 3, 0], 7),
        ([7, 7, 7, 2, 2], [0, 1, 2, 0, 1], 6),
        ([2, 4, 7, 9, 14], [1] * 5, 5),
        ([14, 2, 3, 4, 5], [0, 1, 2, 3, 0], 4),
        ([7, 7, 7, 2, 3], [0, 1, 2, 0, 1], 3),
        ([7, 7, 2, 2, 3], [0, 1, 0, 1, 2], 2),
        ([7, 7, 2, 4, 3], [0, 1, 0, 1, 2], 1),
        ([2, 4, 7, 9, 14], [0, 1, 2, 3, 0], 0),
    ],
)
def test_categories(ranks, suits, category):
    assert evaluar_cinco(cards(ranks, suits))[0] == category


def test_ties_kickers():
    assert evaluar_cinco(cards([8, 8, 14, 7, 3])) > evaluar_cinco(
        cards([8, 8, 13, 7, 3])
    )
    board = cards([10, 11, 12, 13, 14], [0] * 5)
    assert evaluar_mano(cards([2, 3], [1, 1]) + board) == evaluar_mano(
        cards([7, 8], [2, 2]) + board
    )


def test_risk_manual():
    assert cvar([100, 20, -10], 0.9, [0.05, 0.15, 0.8]) == pytest.approx(60)
    assert cvar([10, 4, 0], 0.5) == pytest.approx(8)
    assert cvar([-5, -5], 0.9) == pytest.approx(-5)
    assert cvar([3, 8], 0, [0.8, 0.2]) == pytest.approx(4)
    for alpha in (0.0, 0.5, 0.9):
        assert cvar([1, 5, 10], alpha) == pytest.approx(legacy.cvar([1, 5, 10], alpha))


@pytest.mark.parametrize(
    "losses,alpha,p",
    [
        ([], 0.9, None),
        ([1], 1, None),
        ([1], 0.9, [0.5]),
        ([float("nan")], 0.9, None),
        ([1, 2], 0.9, [-1, 2]),
    ],
)
def test_risk_invalid(losses, alpha, p):
    with pytest.raises(ValueError):
        cvar(losses, alpha, p)


def test_deals():
    for n in range(100):
        h, b = deal(21, n)
        assert len(set(h[0] + h[1] + b)) == 9
        assert (h, b) == deal(21, n)


def test_all_paths():
    # Exhaustive action trees: stacks, short blinds, all-in, folds, refunds.
    h, b = deal(3, 1)
    for stacks in ((1, 9), (9, 1), (3, 10), (10, 3), (455, 455)):
        for small in (0, 1):
            pending = [initial(stacks, small)]
            while pending:
                s = pending.pop()
                assert min(s.paid) >= 0 and all(s.paid[i] <= s.start[i] for i in (0, 1))
                if s.terminal:
                    out = settle(s, h, b)
                    assert sum(out) == sum(stacks) and min(out) >= 0
                    assert not legal(s)
                    with pytest.raises(ValueError):
                        step(s, "call")
                else:
                    assert s.steps < 4
                    pending.extend(step(s, a) for a in legal(s))


def strip_time(rows):
    result = copy.deepcopy(rows)
    for row in result:
        for e in row["events"]:
            e.pop("seconds")
    return result


def test_sessions_and_export(tmp_path):
    cfg = Config(capital=15, hands=50, scenarios=3)
    rows = session(cfg, seed=2)
    assert len(rows) == 50 or min(rows[-1]["bankroll_1"], rows[-1]["bankroll_2"]) == 0
    assert all(r["bankroll_1"] + r["bankroll_2"] == 30 for r in rows)
    assert sum(r["profit_1"] for r in rows) == rows[-1]["bankroll_1"] - 15
    assert strip_time(rows) == strip_time(session(cfg, seed=2))
    export(tmp_path / "hands.csv", rows)
    details, summary, trajectories = evaluate(tmp_path / "hands.csv", cfg, tmp_path)
    assert details[0]["profit"] == rows[-1]["bankroll_1"] - 15
    assert (
        len(trajectories) == 51
        and trajectories[-1]["mean_bankroll"] == rows[-1]["bankroll_1"]
    )


def test_privacy_and_real_control():
    cfg = Config(hands=2, scenarios=4)
    h, b = deal(1, 1)
    obs = Observation(initial((455, 455), 0), h[0], cfg.raises)
    assert set(obs.__dataclass_fields__) == {"public", "own", "raises"}
    action, info = decide(obs, "risk", cfg, "test", limit=-100)
    assert info["status"] == "infeasible_emergency" and action in legal(obs.public)
    assert info["selected"]["cvar"] == min(c["cvar"] for c in info["candidates"])
    for row in session(cfg, "profit", seed=1):
        for e in row["events"]:
            assert e["action"] in e["legal"]
            if e["player"] == 1:
                assert e["action"] == e["selected"]["action"]


def test_optimizer_enumeration_and_comparability():
    candidates = [dict(action="a", mean=10, cvar=30), dict(action="b", mean=5, cvar=3)]
    assert select(candidates, "risk", 4, 0)[0]["action"] == "b"
    assert select(candidates, "profit", 4, 0)[0]["action"] == "a"
    assert select(candidates, "minrisk", 4, 8)[0]["action"] == "a"
    assert not select(candidates, "minrisk", 4, 11)[1]
    cfg = Config(scenarios=4)
    h, b = deal(2, 1)
    obs = Observation(initial((455, 455), 0), h[0], cfg.raises)
    a, info = decide(obs, "profit", cfg, "same")
    b, other = decide(obs, "risk", cfg, "same", limit=1000)
    assert a == b and info["candidates"] == other["candidates"]


def test_exposure_certificate():
    a = analyze(capacity=5, minimum=-100)
    assert a["equilibria"]
    for e in a["equilibria"]:
        assert e["mu1"] + e["mu2"] == pytest.approx(0)
        assert max(e["deviation1"], e["deviation2"]) <= 1e-9
    assert not analyze(capacity=5, minimum=100)["equilibria"]


def test_evaluator_rejects_incomplete(tmp_path):
    rows = session(Config(hands=2, scenarios=1), "fixed")[:1]
    export(tmp_path / "hands.csv", rows)
    with pytest.raises(ValueError):
        legacy.read_sessions(
            tmp_path / "hands.csv", dict(initial_bankroll_each=455, max_hands=50)
        )


def test_short_blind_refund_and_tie():
    s = step(initial((1, 9), 0), "call")
    board = cards([10, 11, 12, 13, 14], [0] * 5)
    holes = (cards([2, 3], [1, 1]), cards([7, 8], [2, 2]))
    assert s.paid == (1, 2)
    assert settle(s, holes, board) == (1, 9)
    assert settle(s, holes, board) == settle(s, holes, board)
    s = step(initial((455, 455), 0), "fold")
    assert settle(s, holes, board) == (454, 456)
    with pytest.raises(ValueError):
        step(initial((455, 455), 0), "raise:29")


def test_minrisk_and_forced_emergency_sessions():
    for strategy, opponent, limit in [
        ("risk", "stable", -100),
        ("fixed", "minrisk", 10),
    ]:
        rows = session(Config(hands=50, scenarios=2), strategy, opponent, 12, limit)
        assert len(rows) == 50
        optimized = [e for r in rows for e in r["events"] if e["status"] != "reference"]
        assert optimized and any(
            e["status"] == "infeasible_emergency" for e in optimized
        )
        assert all(e["action"] in e["legal"] for e in optimized)


def test_hidden_cards_do_not_enter_policy():
    # Two different actual deals sharing our hand produce identical policy input.
    cfg = Config(scenarios=5)
    actual_holes_a = (((14, 0), (14, 1)), ((2, 0), (3, 0)))
    actual_holes_b = (actual_holes_a[0], ((13, 0), (13, 1)))
    observations = [
        Observation(initial((455, 455), 0), h[0], cfg.raises)
        for h in (actual_holes_a, actual_holes_b)
    ]
    decisions = [
        decide(o, "profit", cfg, "independent-policy-stream") for o in observations
    ]
    assert decisions[0][0] == decisions[1][0]
    assert decisions[0][1]["candidates"] == decisions[1][1]["candidates"]


def test_tail_padding_in_evaluator():
    source = {
        ("a", "b", "c", "0"): [(1, 0, 910)],
        ("a", "b", "c", "1"): [(1, 455, 455), (2, 457, 453)],
    }
    _, summary, paths = legacy.summarize(
        source, dict(initial_bankroll_each=455, max_hands=2, alpha=0.9)
    )
    assert paths[-1]["mean_bankroll"] == 228.5
    assert summary[0]["probability_ruin"] == 0.5
    assert summary[0]["cvar_session_loss"] == pytest.approx(455)


def test_invalid_optimization_inputs():
    cfg = Config(scenarios=1)
    h, _ = deal(3, 1)
    obs = Observation(initial((455, 455), 0), h[0], cfg.raises)
    with pytest.raises(ValueError):
        decide(obs, "risk", cfg, "x", limit=float("nan"))
    with pytest.raises(ValueError):
        analyze(capacity=-1)


def test_imports_have_no_simulation_side_effects(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(root)}
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import poker.game, poker.policy, poker.experiments, optimizacion_cournot_poker",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout == result.stderr == ""
    assert not list(tmp_path.iterdir())


def test_continuation_against_hand_calculation(monkeypatch):
    # Aces beat low unpaired cards. Rival folds every raise, so raise is NOT
    # valued as automatically reaching showdown with an enlarged pot.
    import poker.policy as policy

    class Scenario:
        def sample(self, population, size):
            result = [(2, 0), (3, 1), (4, 2), (7, 3), (9, 0), (11, 1), (13, 2)]
            assert len(set(result)) == 7 and all(c in population for c in result)
            return result

    monkeypatch.setattr(policy.random, "Random", lambda seed: Scenario())
    cfg = Config(scenarios=1)
    obs = Observation(initial((455, 455), 0), ((14, 0), (14, 1)), cfg.raises)
    action, info = decide(obs, "profit", cfg, "manual")
    assert action == "call"
    values = {c["action"]: c for c in info["candidates"]}
    assert values["fold"]["mean"] == -1
    for a in ("call", "raise:10", "raise:30"):
        assert values[a]["mean"] == 2
        assert values[a]["cvar"] == -2
        assert values[a]["incremental_mean"] == 3


def test_all_in_winner_payment():
    s = step(initial((3, 9), 0), "raise:3")
    s = step(s, "call")
    h = (((14, 0), (14, 1)), ((2, 0), (3, 1)))
    board = ((4, 2), (7, 3), (9, 0), (11, 1), (13, 2))
    assert settle(s, h, board) == (6, 6)


@pytest.mark.parametrize(
    "kwargs", [{"hands": 51}, {"capital": 0}, {"scenarios": 0}, {"alpha": 1}]
)
def test_configuration_contract(kwargs):
    with pytest.raises(ValueError):
        Config(**kwargs)
