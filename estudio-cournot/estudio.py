"""Estudio de sensibilidad de Cournot. Python 3.10+, solo biblioteca estándar.

Ver README.md para contratos, matemáticas, límites y comandos.
El programa evalúa distribuciones discretas exactamente: no usa Monte Carlo.
"""

import argparse
import csv
import html
import json
import math
from pathlib import Path

TOL = 1e-8


def number(value, label):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label}: se necesita un número finito")
    return value


def tail_mean(values, probabilities, mass, largest=True):
    """Media de una cola de masa exacta, fraccionando el escenario frontera."""
    remaining, total = mass, 0.0
    for value, probability in sorted(zip(values, probabilities), reverse=largest):
        used = min(remaining, probability)
        total += used * value
        remaining -= used
        if remaining <= 0:
            break
    if remaining > TOL:
        raise ValueError("Probabilidad insuficiente para calcular la cola")
    return total / mass


def read_model(path):
    model = json.loads(path.read_text(encoding="utf-8"))
    for key in ("b", "c1", "q1_max", "alpha", "q_fixed"):
        model[key] = number(model[key], key)
    if model["b"] <= 0 or model["c1"] < 0 or model["q1_max"] <= 0:
        raise ValueError("Se requiere b > 0, c1 >= 0 y q1_max > 0")
    if not 0 < model["alpha"] < 1:
        raise ValueError("alpha debe estar entre 0 y 1, excluidos")
    if not 0 <= model["q_fixed"] <= model["q1_max"]:
        raise ValueError("q_fixed está fuera de capacidad")
    for key in ("risk_limits", "rival_errors"):
        model[key] = sorted(set(number(v, key) for v in model[key]))
        if not model[key]:
            raise ValueError(f"{key} no puede estar vacío")
    model["rival_errors"] = sorted(set(model["rival_errors"] + [0.0]))
    scenarios = model["scenarios"]
    if not scenarios:
        raise ValueError("Faltan escenarios")
    ids = set()
    for s in scenarios:
        if s["id"] in ids:
            raise ValueError("Identificadores de escenario duplicados")
        ids.add(s["id"])
        for key in ("probability", "a", "q2"):
            s[key] = number(s[key], key)
        if s["probability"] <= 0:
            raise ValueError("Cada escenario debe tener probabilidad positiva")
        for error in model["rival_errors"]:
            real_q2 = s["q2"] + error
            if real_q2 < 0:
                raise ValueError("Un desplazamiento produce q2 negativa")
            if s["a"] - model["b"] * (model["q1_max"] + real_q2) < 0:
                raise ValueError("Hay precios negativos en el dominio. Revisar parámetros; no se recortan precios.")
    total = sum(s["probability"] for s in scenarios)
    if abs(total - 1) > TOL:
        raise ValueError("Las probabilidades deben sumar 1")
    for s in scenarios:
        s["probability"] /= total  # Solo corrige redondeo dentro de la tolerancia.
    return model


def evaluate(model, q1, error=0.0):
    """error = q2 real - q2 estimada; q1 ya se eligió antes de conocer error."""
    profits, prices, probabilities = [], [], []
    for s in model["scenarios"]:
        price = s["a"] - model["b"] * (q1 + s["q2"] + error)
        prices.append(price)
        profits.append(q1 * (price - model["c1"]))
        probabilities.append(s["probability"])
    expected = sum(p * v for p, v in zip(probabilities, profits))
    risk = tail_mean([-v for v in profits], probabilities, 1 - model["alpha"])
    return {
        "expected_profit": expected,
        "cvar_loss": risk,
        "worst_profit": min(profits),
        "probability_loss": sum(p for p, v in zip(probabilities, profits) if v < 0),
        "expected_price": sum(p * v for p, v in zip(probabilities, prices)),
    }


def coefficients(model):
    """mu(q)=d_mean*q-b*q²; CVaR(-profit)=b*q²-d_tail*q para q>=0."""
    probabilities = [s["probability"] for s in model["scenarios"]]
    d = [s["a"] - model["c1"] - model["b"] * s["q2"] for s in model["scenarios"]]
    return (sum(p * value for p, value in zip(probabilities, d)),
            tail_mean(d, probabilities, 1 - model["alpha"], largest=False))


def nominal_quantity(model):
    d_mean, _ = coefficients(model)
    return min(model["q1_max"], max(0.0, d_mean / (2 * model["b"])))


def analytic_solution(model, risk_limit):
    """Solución analítica SOLO para el modelo lineal-cuadrático documentado."""
    _, d_tail = coefficients(model)
    b = model["b"]
    discriminant = d_tail ** 2 + 4 * b * risk_limit
    if discriminant < -TOL:
        return None
    root = math.sqrt(max(0.0, discriminant))
    lower = max(0.0, (d_tail - root) / (2 * b))
    upper = min(model["q1_max"], (d_tail + root) / (2 * b))
    if lower > upper:
        return None
    return min(upper, max(lower, nominal_quantity(model)))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def demo_decisions(model):
    result = []
    for limit in model["risk_limits"]:
        q = analytic_solution(model, limit)
        result.append({"risk_limit": limit, "q1": q,
                       "status": "infeasible" if q is None else "optimal",
                       "method": "referencia_analitica_datos_ficticios"})
    return result


def read_decisions(path, model):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    found = set()
    for row in rows:
        limit = number(row["risk_limit"], "risk_limit")
        if limit not in model["risk_limits"] or limit in found:
            raise ValueError("El CSV debe tener exactamente una fila por risk_limit del JSON")
        found.add(limit)
        row["risk_limit"] = limit
        if row["status"] not in ("optimal", "feasible", "infeasible", "unknown"):
            raise ValueError("status debe ser optimal, feasible, infeasible o unknown")
        row["method"] = row.get("method", "sin_especificar")
        if row["status"] in ("infeasible", "unknown"):
            if row["q1"].strip():
                raise ValueError("Una fila infeasible/unknown debe dejar q1 vacía")
            row["q1"] = None
        else:
            row["q1"] = number(row["q1"], "q1")
            if not 0 <= row["q1"] <= model["q1_max"]:
                raise ValueError("La producción recibida está fuera de capacidad")
            if evaluate(model, row["q1"])["cvar_loss"] > limit + TOL:
                raise ValueError("La decisión recibida incumple el riesgo en sus escenarios de planificación")
    if found != set(model["risk_limits"]):
        raise ValueError("Faltan límites de riesgo en el CSV")
    return sorted(({key: row[key] for key in ("risk_limit", "q1", "status", "method")}
                   for row in rows), key=lambda row: row["risk_limit"])


def study(model, decisions):
    results = []
    for decision in decisions:
        limit = decision["risk_limit"]
        choices = [("fija", model["q_fixed"]),
                   ("optima_sin_limite_riesgo", nominal_quantity(model))]
        if decision["q1"] is not None:
            choices.append(("decision_companero_2", decision["q1"]))
        for strategy, q in choices:
            planned = evaluate(model, q)
            for error in model["rival_errors"]:
                actual = evaluate(model, q, error)
                baseline = evaluate(model, model["q_fixed"], error)
                results.append({
                    "risk_limit": limit, "strategy": strategy, "q1": q,
                    "rival_error": error, "planned_expected_profit": planned["expected_profit"],
                    "planned_cvar": planned["cvar_loss"], **actual,
                    "gain_vs_fixed": actual["expected_profit"] - baseline["expected_profit"],
                    "risk_excess": max(0.0, actual["cvar_loss"] - limit),
                    "risk_feasible": actual["cvar_loss"] <= limit + TOL,
                })
    return results


def frontier(model, decisions):
    result = []
    previous = None
    for decision in decisions:
        q, limit = decision["q1"], decision["risk_limit"]
        row = {**decision, "expected_profit": None, "cvar_loss": None,
               "risk_slack": None, "risk_active": None,
               "previous_limit": None, "profit_secant": None,
               "secant_both_reported_optimal": None}
        if q is not None:
            values = evaluate(model, q)
            row.update(expected_profit=values["expected_profit"], cvar_loss=values["cvar_loss"],
                       risk_slack=limit - values["cvar_loss"],
                       risk_active=abs(limit - values["cvar_loss"]) <= TOL)
            if previous is not None:
                row["previous_limit"] = previous["risk_limit"]
                row["profit_secant"] = ((row["expected_profit"] - previous["expected_profit"])
                                         / (limit - previous["risk_limit"]))
                row["secant_both_reported_optimal"] = (
                    decision["status"] == previous["status"] == "optimal")
            previous = row
        else:
            previous = None  # No calcular pendientes a través de huecos.
        result.append(row)
    return result


def chart(rows, metric, title):
    groups = {}
    for row in rows:
        key = f'{row["strategy"]}, R={row["risk_limit"]:g}'
        groups.setdefault(key, []).append((row["rival_error"], row[metric]))
    xs = [x for group in groups.values() for x, _ in group]
    ys = [y for group in groups.values() for _, y in group]
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    if xmin == xmax:
        xmin, xmax = xmin - 1, xmax + 1
    if ymin == ymax:
        ymin, ymax = ymin - 1, ymax + 1
    pad = (ymax - ymin) * .05
    ymin, ymax = ymin - pad, ymax + pad
    def sx(x):
        return 85 + (x - xmin) / (xmax - xmin) * 610

    def sy(y):
        return 285 - (y - ymin) / (ymax - ymin) * 250
    parts = [f'<h2>{html.escape(title)}</h2>',
             '<svg viewBox="0 0 760 340" role="img" aria-label="' + html.escape(title) + '">']
    for k in range(6):
        y = ymin + (ymax - ymin) * k / 5
        parts.append(f'<line x1="85" y1="{sy(y)}" x2="695" y2="{sy(y)}" stroke="#ddd"/>')
        parts.append(f'<text x="75" y="{sy(y)+4}" text-anchor="end">{y:.2f}</text>')
    for x in sorted(set(xs)):
        parts.append(f'<text x="{sx(x)}" y="310" text-anchor="middle">{x:g}</text>')
    legend = []
    for index, (name, points) in enumerate(groups.items()):
        color = f'hsl({index * 137.5 % 360:.1f},65%,35%)'
        coords = ' '.join(f'{sx(x)},{sy(y)}' for x, y in sorted(points))
        parts.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2"/>')
        for x, y in points:
            parts.append(f'<circle cx="{sx(x)}" cy="{sy(y)}" r="3" fill="{color}"><title>{html.escape(name)}: {y:.6g}</title></circle>')
        legend.append(f'<li style="color:{color}">{html.escape(name)}</li>')
    parts.append('<text x="390" y="336" text-anchor="middle">Error: q2 real − q2 estimada (unidades)</text></svg>')
    return ''.join(parts) + '<ul>' + ''.join(legend) + '</ul>'


def report(path, rows, front, demo):
    heading = "EJEMPLO FICTICIO" if demo else "Evaluación de entradas aportadas por el equipo"
    table = '<table><tr><th>R</th><th>Estado comunicado</th><th>q1</th><th>Beneficio esperado</th><th>CVaR</th></tr>'
    for row in front:
        cells = [row[k] for k in ("risk_limit", "status", "q1", "expected_profit", "cvar_loss")]
        table += '<tr>' + ''.join('<td>' + html.escape('—' if c is None else str(c)) + '</td>' for c in cells) + '</tr>'
    table += '</table>'
    text = ('<!doctype html><html lang="es"><meta charset="utf-8"><title>Estudio de Cournot</title>'
            '<style>body{font:16px system-ui;max-width:1000px;margin:40px auto;padding:0 20px;color:#182434}'
            'svg{width:100%;font:12px system-ui}td,th{padding:8px;border:1px solid #ddd}table{border-collapse:collapse}'
            'li{margin:4px 0}</style>'
            f'<h1>{heading}</h1><p>Evaluación exacta de escenarios discretos. Las decisiones se mantienen fijas al cambiar el rival. '
            'El estado optimal procede de la entrada y no constituye una certificación independiente.</p>'
            '<p>Beneficio, CVaR y exceso de riesgo: unidades monetarias. CVaR se aplica a la pérdida = −beneficio; '
            'puede ser negativo. Las referencias pueden incumplir el límite de riesgo.</p>' + table)
    for metric, title in (("expected_profit", "Beneficio esperado"), ("cvar_loss", "CVaR de pérdidas"),
                          ("risk_excess", "Exceso sobre el límite de riesgo"), ("gain_vs_fixed", "Ganancia adicional frente a producción fija")):
        text += chart(rows, metric, title)
    text += '<p>Las líneas de referencias repetidas para distintos límites R se superponen. Ver CSV para todos los valores.</p></html>'
    path.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--decisions", type=Path)
    source.add_argument("--demo", action="store_true")
    parser.add_argument("--out", type=Path, required=True, help="Directorio nuevo: no sobrescribe resultados previos")
    args = parser.parse_args()
    model = read_model(args.scenarios)
    decisions = demo_decisions(model) if args.demo else read_decisions(args.decisions, model)
    rows, front = study(model, decisions), frontier(model, decisions)
    args.out.mkdir(parents=True, exist_ok=False)
    write_csv(args.out / "decisiones_utilizadas.csv", decisions, ["risk_limit", "q1", "status", "method"])
    write_csv(args.out / "evaluacion.csv", rows, list(rows[0]))
    write_csv(args.out / "frontera.csv", front, list(front[0]))
    (args.out / "escenarios_utilizados.json").write_text(json.dumps(model, ensure_ascii=False, indent=2), encoding="utf-8")
    report(args.out / "informe.html", rows, front, args.demo)
    print(f"Resultados escritos en {args.out.resolve()}")


if __name__ == "__main__":
    main()
