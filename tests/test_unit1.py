import json
from types import SimpleNamespace

import pytest

from poker.academic import (
    _observation,
    _scenarios,
    make_stability_observations,
    run_sensitivity,
    run_stability,
)
from poker.cvar_lp import certify_cvar
from poker.game import deal, legal
from poker.policy import decide, evaluate_actions


def test_cvar_primal_dual_manual_and_kkt():
    result = certify_cvar([100, 20, -10], 0.90, [0.05, 0.15, 0.80])
    assert result["validated"]
    assert result["ordered_value"] == pytest.approx(60)
    assert result["primal_value"] == pytest.approx(60)
    assert result["dual_value"] == pytest.approx(60)
    assert result["eta"] == pytest.approx(20)
    assert result["u"] == pytest.approx([80, 0, 0])
    assert result["z"] == pytest.approx([0.5, 0.5, 0])
    assert max(result["residuals"].values()) < 1e-8


@pytest.mark.parametrize(
    "losses,p",
    [
        ([12, 4, -3], [0.10, 0.25, 0.65]),
        ([9, 9, 1, -2], [0.10, 0.15, 0.25, 0.50]),
        ([-5, -2, -10], [0.20, 0.30, 0.50]),
        ([100, 8, -4], [0.0, 0.25, 0.75]),
        ([7], [1.0]),
    ],
)
def test_cvar_lp_agrees_for_degenerate_and_weighted_distributions(losses, p):
    result = certify_cvar(losses, 0.90, p)
    assert result["validated"]
    assert result["ordered_value"] == pytest.approx(result["primal_value"])
    assert result["primal_value"] == pytest.approx(result["dual_value"])


@pytest.mark.parametrize(
    "losses,alpha,p",
    [
        ([], 0.9, None),
        ([1], 0, None),
        ([1], 1, None),
        ([float("inf")], 0.9, None),
        ([1, 2], 0.9, [0.5]),
        ([1, 2], 0.9, [0.5, -0.5]),
        ([1, 2], 0.9, [0.4, 0.4]),
        ([1, float("nan")], 0.9, None),
    ],
)
def test_cvar_lp_rejects_invalid_inputs(losses, alpha, p):
    with pytest.raises(ValueError):
        certify_cvar(losses, alpha, p)


def test_cvar_lp_reports_nonoptimal_solver_state(monkeypatch):
    def failed_solver(*args, **kwargs):
        return SimpleNamespace(status=2, message="infeasible test state", success=False)

    monkeypatch.setattr("poker.cvar_lp.linprog", failed_solver)
    result = certify_cvar([1, 2], 0.9)
    assert not result["validated"]
    assert result["reason"] == "solver_not_optimal"
    assert result["solver"]["primal"]["status"] == 2
    assert "infeasible" in result["solver"]["dual"]["message"]


def test_cvar_lp_enumeration_of_tiny_uniform_distribution():
    # Una distribución equiprobable de cuatro escenarios tiene cola de masa 0.25.
    losses = [-7, 2, 5, 11]
    result = certify_cvar(losses, 0.75)
    assert result["validated"]
    assert result["ordered_value"] == pytest.approx(11)


def test_cvar_lp_validates_actual_action_scenario_losses():
    cfg, obs = _observation(720001, 455, 0, "small_blind_unraised")
    scenarios = _scenarios(obs, "unit1-cvar-real-actions-v1", 32)
    for candidate in evaluate_actions(obs, cfg, scenarios):
        result = certify_cvar(candidate["losses"], cfg.alpha)
        assert result["validated"]
        assert result["ordered_value"] == pytest.approx(candidate["cvar"])


def test_frozen_scenarios_preserve_action_losses_and_policy_output():
    cfg, obs = _observation(730001, 455, 0, "small_blind_unraised")
    first = _scenarios(obs, "fixed-sensitivity-seed", 32)
    second = _scenarios(obs, "fixed-sensitivity-seed", 32)
    assert first == second
    assert all(len(set(obs.own + cards)) == 9 for cards in first)
    candidates = evaluate_actions(obs, cfg, first)
    assert [c["action"] for c in candidates] == list(legal(obs.public, obs.raises))
    assert all(len(c["losses"]) == 32 for c in candidates)
    chosen, info = decide(obs, "risk", cfg, "fixed-sensitivity-seed", limit=10)
    assert chosen in [c["action"] for c in candidates]
    assert all("losses" not in c for c in info["candidates"])


def test_frozen_scenario_sensitivity_thresholds_and_emergency(tmp_path):
    result = run_sensitivity(tmp_path, 128)
    data = json.loads((tmp_path / "sensitivity.json").read_text())
    assert result["monotone"] and data["monotone_on_feasible_points"]
    by_r = {round(row["R"], 10): row for row in data["points"]}
    for threshold in result["thresholds"]:
        for point in (threshold - data["epsilon"], threshold, threshold + data["epsilon"]):
            assert round(point, 10) in by_r
    impossible = [row for row in data["points"] if not row["feasible"]]
    assert impossible
    assert all(row["accion"] is None and row["objetivo_beneficio_medio"] is None for row in impossible)
    assert all(row["alternativa_emergencia"] is not None for row in impossible)


def test_nested_scenario_prefixes_are_reproducible():
    _, obs = _observation(710001, 455, 0, "small_blind_unraised")
    a = _scenarios(obs, "nested-seed", 512)
    b = _scenarios(obs, "nested-seed", 512)
    assert a == b
    assert a[:32] == b[:32]
    assert a[:128] == b[:128]


def test_stability_fixtures_have_the_declared_blind_facing_raise():
    observations = make_stability_observations()
    big_blind_facing = observations[2][3].public
    small_blind_facing = observations[3][3].public
    assert big_blind_facing.raised and big_blind_facing.small == 0 and big_blind_facing.actor == 1
    assert big_blind_facing.history[-1][0] == 0
    assert small_blind_facing.raised and small_blind_facing.small == 1 and small_blind_facing.actor == 1
    assert small_blind_facing.history[-1][0] == 0
    assert small_blind_facing.history[0][1] == "call"


def test_deal_stream_does_not_depend_on_planner_consumption():
    before = deal(41, 1)
    _scenarios(_observation(710001, 455, 0, "small_blind_unraised")[1], "other", 512)
    assert deal(41, 1) == before


def test_small_stability_experiment_repeats_decisions(tmp_path):
    first = run_stability(tmp_path / "first", 1, 1, 128)
    second = run_stability(tmp_path / "second", 1, 1, 128)
    assert first["runs"] == second["runs"] == 3
    a = json.loads((tmp_path / "first/stability_runs.json").read_text())
    b = json.loads((tmp_path / "second/stability_runs.json").read_text())
    for rows in (a, b):
        for row in rows:
            row.pop("seconds")
    assert a == b


@pytest.mark.parametrize(
    "values,expected_mean,expected_cvar,status",
    [
        ([(1, 2), (1, 2)], 0, 0, "estimable"),
        ([(1, 2), (3, 6), (5, 10)], 2, 4, "estimable"),
        ([(1, 2)], None, None, "no estimable"),
    ],
)
def test_stability_variability_is_within_observation(values, expected_mean, expected_cvar, status):
    from poker.academic import _summarize_stability

    records = []
    for size in (32, 128, 512):
        for obs, offset in (("a", 0), ("b", 100)):
            for seed, (mean, risk) in enumerate(values):
                records.append(dict(
                    S=size, observation=obs, planner_seed=seed, action="fold",
                    feasible_actions=["fold"], emergency=False, seconds=0,
                    estimates={"fold": {"mean": mean + offset, "cvar": risk + offset}},
                ))
    _, estimates = _summarize_stability(records)
    for row in estimates:
        assert row["n_observations"] == 2
        assert row["status"] == status
        assert row["n_observations_estimable"] == (2 if len(values) > 1 else 0)
        for key, expected in (("mean_within_observation_sd", expected_mean), ("cvar_within_observation_sd", expected_cvar)):
            if expected is None:
                assert row[key] is None
            else:
                assert row[key] == pytest.approx(expected)
