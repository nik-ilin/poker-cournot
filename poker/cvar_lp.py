"""Certificación LP primal-dual del CVaR discreto (capa académica)."""

import math

from scipy.optimize import linprog

from .risk import cvar


def _distribution(losses, alpha, probabilities):
    losses = [float(x) for x in losses]
    if not losses or any(not math.isfinite(x) for x in losses):
        raise ValueError("Las pérdidas deben ser una secuencia finita no vacía")
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("Se requiere 0 < alpha < 1")
    p = (
        [1.0 / len(losses)] * len(losses)
        if probabilities is None
        else [float(x) for x in probabilities]
    )
    if (
        len(p) != len(losses)
        or any(not math.isfinite(x) or x < 0 for x in p)
        or not math.isclose(sum(p), 1.0, rel_tol=0.0, abs_tol=1e-10)
    ):
        raise ValueError("Probabilidades finitas, no negativas y de suma uno requeridas")
    return losses, p


def certify_cvar(losses, alpha=0.9, probabilities=None, atol=1e-8, rtol=1e-8):
    """Resuelve y contrasta CVaR por ordenación, LP primal, LP dual y KKT.

    El resultado `validated` solo es cierto si ambos LP finalizan con estado
    óptimo y todas las discrepancias/residuos están dentro de tolerancia.
    """
    losses, p = _distribution(losses, alpha, probabilities)
    if atol <= 0 or rtol < 0 or not math.isfinite(atol + rtol):
        raise ValueError("Tolerancias inválidas")
    n = len(losses)
    c = [weight / (1.0 - alpha) for weight in p]

    # x=(eta,u_1,...,u_n); -eta-u_s <= -ell_s.
    a_ub = [[-1.0] + [-1.0 if j == i else 0.0 for j in range(n)] for i in range(n)]
    primal = linprog(
        [1.0] + c,
        A_ub=a_ub,
        b_ub=[-loss for loss in losses],
        bounds=[(None, None)] + [(0.0, None)] * n,
        method="highs",
    )
    dual = linprog(
        [-loss for loss in losses],
        A_eq=[[1.0] * n],
        b_eq=[1.0],
        bounds=[(0.0, cap) for cap in c],
        method="highs",
    )
    statuses = {
        "primal": {"status": int(primal.status), "message": primal.message},
        "dual": {"status": int(dual.status), "message": dual.message},
    }
    if not primal.success or not dual.success:
        return {"validated": False, "solver": statuses, "reason": "solver_not_optimal"}

    eta = float(primal.x[0])
    u = [float(x) for x in primal.x[1:]]
    # HiGHS reports d(value)/d(rhs)=-z for these <= rows.
    z = [-float(x) for x in primal.ineqlin.marginals]
    beta = [cap - weight for cap, weight in zip(c, z)]
    g = [loss - eta - slack for loss, slack in zip(losses, u)]
    primal_value = float(primal.fun)
    dual_value = float(-dual.fun)
    ordered_value = float(cvar(losses, alpha, p))

    residuals = {
        "stationarity_eta": abs(1.0 - sum(z)),
        "stationarity_u": max(
            abs(cap - weight - bound)
            for cap, weight, bound in zip(c, z, beta)
        ),
        "primal_inequality": max(0.0, *g),
        "primal_u_nonnegative": max(0.0, *(-x for x in u)),
        "dual_z_nonnegative": max(0.0, *(-x for x in z)),
        "dual_upper_bound": max(0.0, *(x - cap for x, cap in zip(z, c))),
        "dual_beta_nonnegative": max(0.0, *(-x for x in beta)),
        "complementarity_z": max(abs(x * slack) for x, slack in zip(z, g)),
        "complementarity_beta": max(abs(x * slack) for x, slack in zip(beta, u)),
        "primal_dual_gap": abs(primal_value - dual_value),
        "ordering_primal": abs(ordered_value - primal_value),
        "ordering_dual": abs(ordered_value - dual_value),
    }
    scales = {
        "stationarity_eta": max(1.0, sum(abs(x) for x in z)),
        "stationarity_u": max(1.0, *(abs(x) for x in c)),
        "primal_inequality": max(1.0, *(abs(x) for x in losses), abs(eta)),
        "primal_u_nonnegative": max(1.0, *(abs(x) for x in u)),
        "dual_z_nonnegative": 1.0,
        "dual_upper_bound": max(1.0, *(abs(x) for x in c)),
        "dual_beta_nonnegative": max(1.0, *(abs(x) for x in beta)),
        "complementarity_z": max(1.0, *(abs(x) for x in losses), abs(eta)),
        "complementarity_beta": max(1.0, *(abs(x) for x in u), *(abs(x) for x in beta)),
        "primal_dual_gap": max(1.0, abs(primal_value), abs(dual_value)),
        "ordering_primal": max(1.0, abs(ordered_value), abs(primal_value)),
        "ordering_dual": max(1.0, abs(ordered_value), abs(dual_value)),
    }
    limits = {k: atol + rtol * scales[k] for k in residuals}
    return {
        "validated": all(residuals[k] <= limits[k] for k in residuals),
        "solver": statuses,
        "n": n,
        "alpha": alpha,
        "probabilities": p,
        "losses": losses,
        "ordered_value": ordered_value,
        "primal_value": primal_value,
        "dual_value": dual_value,
        "eta": eta,
        "u": u,
        "z": z,
        "beta": beta,
        "residuals": residuals,
        "scales": scales,
        "tolerances": limits,
        "atol": atol,
        "rtol": rtol,
    }
