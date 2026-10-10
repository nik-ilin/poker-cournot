"""Evaluación de registros de póker; Python 3.10+, biblioteca estándar.

No implementa las reglas, ni optimiza estrategias, ni certifica su legalidad.
Cada registro contiene los saldos DESPUÉS de una mano liquidada.
"""
import argparse
import csv
import html
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

FIELDS = ['strategy', 'opponent', 'condition', 'session_id', 'hand', 'bankroll_1', 'bankroll_2']
TOL = 1e-7


def finite(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('Se requiere un número finito')
    return result


def read_config(path):
    config = json.loads(path.read_text(encoding='utf-8'))
    for key in ('initial_bankroll_each', 'alpha'):
        config[key] = finite(config[key])
    hands = finite(config['max_hands'])
    if not hands.is_integer() or hands < 1:
        raise ValueError('max_hands debe ser un entero positivo')
    config['max_hands'] = int(hands)
    if config['initial_bankroll_each'] <= 0 or not 0 < config['alpha'] < 1:
        raise ValueError('Capital positivo y 0 < alpha < 1 requeridos')
    if config.get('risk_limit') is not None:
        config['risk_limit'] = finite(config['risk_limit'])
    return config


def write_csv(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def cvar(losses, alpha):
    """Media de la peor masa (1-alpha), fraccionando la observación frontera."""
    mass = len(losses) * (1 - alpha)
    remaining, total = mass, 0.0
    for loss in sorted(losses, reverse=True):
        used = min(1.0, remaining)
        total += used * loss
        remaining -= used
        if remaining <= 0:
            break
    return total / mass


def read_sessions(path, config):
    sessions = defaultdict(list)
    with path.open(newline='', encoding='utf-8-sig') as handle:
        reader = csv.DictReader(handle)
        if not set(FIELDS).issubset(reader.fieldnames or []):
            raise ValueError('Faltan columnas; consultar plantilla_manos.csv')
        for row in reader:
            key = tuple(row[k].strip() for k in FIELDS[:4])
            if not all(key):
                raise ValueError('Identificadores vacíos')
            hand = finite(row['hand'])
            if not hand.is_integer():
                raise ValueError('hand debe ser entero')
            balances = [finite(row[k]) for k in ('bankroll_1', 'bankroll_2')]
            if min(balances) < 0:
                raise ValueError('Capital negativo')
            if abs(sum(balances) - 2 * config['initial_bankroll_each']) > TOL:
                raise ValueError('No se conserva el capital: revisar botes, comisiones o recompras')
            sessions[key].append((int(hand), *balances))
    if not sessions:
        raise ValueError('El CSV está vacío; la plantilla solo contiene encabezados')
    for key, rows in sessions.items():
        rows.sort()
        if [r[0] for r in rows] != list(range(1, len(rows) + 1)):
            raise ValueError(f'{key}: manos duplicadas, ausentes o inicio distinto de 1')
        if len(rows) > config['max_hands']:
            raise ValueError(f'{key}: supera el horizonte')
        if any(min(r[1:]) <= TOL for r in rows[:-1]):
            raise ValueError(f'{key}: hay manos posteriores al fin por capital cero')
        if len(rows) < config['max_hands'] and min(rows[-1][1:]) > TOL:
            raise ValueError(f'{key}: sesión incompleta; no se admite como finalizada')
    return sessions


def summarize(sessions, config):
    bankroll, horizon = config['initial_bankroll_each'], config['max_hands']
    details, groups, paths = [], defaultdict(list), defaultdict(list)
    for key, hands in sorted(sessions.items()):
        strategy, opponent, condition, session_id = key
        path = [bankroll] + [row[1] for row in hands]
        peak, drawdown = bankroll, 0.0
        for balance in path:
            peak = max(peak, balance)
            drawdown = max(drawdown, peak - balance)
        row = dict(zip(FIELDS[:4], key))
        row.update(hands_played=len(hands), final_bankroll=path[-1],
                   profit=path[-1] - bankroll, ruined=hands[-1][1] <= TOL,
                   opponent_ruined=hands[-1][2] <= TOL,
                   end_reason='bankruptcy' if min(hands[-1][1:]) <= TOL else 'horizon',
                   max_drawdown=drawdown)
        details.append(row)
        groups[key[:3]].append(row)
        # Conservar el saldo final tras terminar evita sesgo de supervivencia.
        paths[key[:3]].append(path + [path[-1]] * (horizon + 1 - len(path)))
    summaries, trajectories = [], []
    for key, rows in sorted(groups.items()):
        profits = [r['profit'] for r in rows]
        risk = cvar([-g for g in profits], config['alpha'])
        limit = config.get('risk_limit')
        row = dict(zip(FIELDS[:3], key))
        row.update(sessions=len(rows), mean_profit=mean(profits),
                   std_profit=stdev(profits) if len(profits) > 1 else None,
                   mean_standard_error_iid=stdev(profits)/math.sqrt(len(rows)) if len(rows) > 1 else None,
                   cvar_session_loss=risk, tail_equivalent_sessions=len(rows)*(1-config['alpha']),
                   observed_worst_profit=min(profits), probability_loss=mean(g < 0 for g in profits),
                   probability_ruin=mean(r['ruined'] for r in rows),
                   mean_max_drawdown=mean(r['max_drawdown'] for r in rows),
                   mean_hands=mean(r['hands_played'] for r in rows), risk_limit=limit,
                   empirical_risk_excess=None if limit is None else max(0.0, risk-limit))
        summaries.append(row)
        for hand in range(horizon + 1):
            values = [p[hand] for p in paths[key]]
            trajectories.append({**dict(zip(FIELDS[:3], key)), 'hand': hand,
                                 'mean_bankroll': mean(values), 'min_bankroll': min(values),
                                 'max_bankroll': max(values)})
    return details, summaries, trajectories


def svg_paths(trajectories, config):
    grouped = defaultdict(list)
    for row in trajectories:
        grouped[tuple(row[k] for k in FIELDS[:3])].append(row)
    capital, horizon = config['initial_bankroll_each'], config['max_hands']
    parts = ['<svg viewBox="0 0 850 350" role="img" aria-label="Capital medio por mano">']
    for fraction in (0, .25, .5, .75, 1):
        y = 290 - 250*fraction
        parts.append(f'<line x1="75" x2="810" y1="{y}" y2="{y}" stroke="#ddd"/>'
                     f'<text x="65" y="{y+4}" text-anchor="end">{2*capital*fraction:g}</text>')
    legends = []
    for i, (key, rows) in enumerate(sorted(grouped.items())):
        color = f'hsl({i*137.5%360:.1f},65%,35%)'
        points = ' '.join(f'{75+735*r["hand"]/horizon},{290-250*r["mean_bankroll"]/(2*capital)}' for r in rows)
        label = html.escape(' / '.join(key))
        parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{points}"><title>{label}</title></polyline>')
        legends.append(f'<li style="color:{color}">{label}</li>')
    for hand in sorted(set((0, horizon//2, horizon))):
        parts.append(f'<text x="{75+735*hand/horizon}" y="310">{hand}</text>')
    parts.append('<text x="400" y="340">Mano</text><text x="75" y="20">Capital medio (unidades)</text></svg>')
    return ''.join(parts) + '<ul>' + ''.join(legends) + '</ul>'


def report(path, summaries, trajectories, config):
    columns = ['strategy', 'opponent', 'condition', 'sessions', 'mean_profit',
               'cvar_session_loss', 'probability_ruin', 'tail_equivalent_sessions']
    labels = ['Estrategia', 'Rival', 'Condición', 'Sesiones', 'Ganancia media',
              'CVaR pérdida/sesión', 'Frecuencia de ruina', 'Masa de cola en sesiones']
    body = '<table><tr>' + ''.join(f'<th>{label}</th>' for label in labels) + '</tr>'
    for row in summaries:
        body += '<tr>' + ''.join('<td>'+html.escape(f'{row[c]:.5g}' if isinstance(row[c], float) else str(row[c]))+'</td>' for c in columns) + '</tr>'
    body += '</table>'
    path.write_text('<!doctype html><html lang="es"><meta charset="utf-8"><title>Estudio de póker</title>'
                    '<style>body{font:16px system-ui;max-width:1200px;margin:35px auto;padding:20px}td,th{padding:8px;border:1px solid #ccc}table{border-collapse:collapse}svg{max-width:900px;width:100%;font:13px system-ui}</style>'
                    '<h1>Estudio de resultados de póker</h1><p>Resultados empíricos de sesiones completas. '
                    'CVaR de pérdida = CVaR de −ganancia neta. Cantidades monetarias en unidades de fichas.</p>'
                    '<p>Variante: '+html.escape(str(config.get('variant', 'no indicada')))+'. '
                    +html.escape(str(config.get('rules_status', '')))+' '
                    +html.escape(str(config.get('bankroll_status', '')))+ '</p>'
                    +body+'<h2>Evolución del capital medio</h2>'+svg_paths(trajectories, config)
                    +'<p>Las sesiones terminadas mantienen su saldo final. La línea media no muestra por sí sola '
                    'la dispersión. Consultar los CSV. Una cola con pocas sesiones aporta una estimación inestable; '
                    'no es una garantía de riesgo futuro. Solo comparar grupos bajo condiciones compatibles.</p></html>', encoding='utf-8')


def example(path, config):
    """Registros aritméticos artificiales para aprender el formato; NO motor de póker."""
    rows = []
    initial = config['initial_bankroll_each']
    for strategy, factor in [('ficticia_A', 1), ('ficticia_B', 2)]:
        for session in range(12):
            capital = initial
            for hand in range(1, config['max_hands']+1):
                delta = factor*((session % 5)-2) * initial / 455
                capital = min(2*initial, max(0.0, capital+delta))
                # Dos trayectorias muestran cómo registrar un final anticipado.
                if session == 0 and hand == 3:
                    capital = 0.0
                if session == 1 and hand == 4:
                    capital = 2*initial
                rows.append(dict(zip(FIELDS, [strategy, 'rival_ficticio', 'DEMO_NO_POKER',
                                              str(session), hand, capital, 2*initial-capital])))
                if capital in (0, 2*initial):
                    break
    write_csv(path, rows, FIELDS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--hands', type=Path)
    modes.add_argument('--example', action='store_true', help='Genera datos artificiales, no una simulación de póker')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    config = read_config(args.config)
    args.out.mkdir(parents=True, exist_ok=False)
    if args.example:
        config['variant'] = 'DEMO ARITMÉTICA: NO SIMULA PÓKER'
        source = args.out / 'manos_artificiales.csv'
        example(source, config)
    else:
        source = args.hands
    sessions = read_sessions(source, config)
    details, summaries, trajectories = summarize(sessions, config)
    for name, rows in [('sesiones', details), ('resumen', summaries), ('trayectorias', trajectories)]:
        write_csv(args.out / f'{name}.csv', rows, list(rows[0]))
    (args.out / 'config_utilizada.json').write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding='utf-8')
    if not args.example:
        (args.out / 'manos_utilizadas.csv').write_bytes(source.read_bytes())
    report(args.out / 'informe.html', summaries, trajectories, config)
    print(f'Resultados guardados en {args.out.resolve()}')


if __name__ == '__main__':
    main()
