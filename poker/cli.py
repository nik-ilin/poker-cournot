import argparse
from pathlib import Path

from .game import Config
from .simulation import export, session


def main():
    p = argparse.ArgumentParser(description="Laboratorio de póker finito")
    p.add_argument("command", choices=["session", "experiment"])
    p.add_argument("--out", type=Path, default=Path("run"))
    p.add_argument("--seed", type=int, default=10000)
    p.add_argument("--sessions", type=int, default=200)
    p.add_argument("--scenarios", type=int, default=Config().scenarios)
    p.add_argument(
        "--strategy", choices=["fixed", "profit", "risk", "minrisk"], default="risk"
    )
    p.add_argument(
        "--opponent",
        choices=["stable", "loose", "tight", "changing", "minrisk"],
        default="stable",
    )
    p.add_argument("--limit", type=float, default=10)
    p.add_argument("--minimum", type=float, default=5)
    p.add_argument("--capital", type=int, default=455)
    p.add_argument("--hands", type=int, default=50)
    a = p.parse_args()
    if a.sessions < 1:
        p.error("sessions debe ser positivo")
    if a.command == "experiment":
        from .experiments import run

        run(a.out, a.sessions, a.scenarios, a.seed)
    else:
        a.out.mkdir(parents=True, exist_ok=False)
        export(
            a.out / "hands.csv",
            session(
                Config(a.capital, a.hands, scenarios=a.scenarios),
                a.strategy,
                a.opponent,
                a.seed,
                a.limit,
                a.minimum,
            ),
        )
        from .evaluation import evaluate

        evaluate(a.out / "hands.csv", Config(a.capital, a.hands), a.out)
    print(a.out.resolve())


if __name__ == "__main__":
    main()
