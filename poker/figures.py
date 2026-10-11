"""Figuras exportables desde resultados compactos, sin repetir simulación."""

import csv
import json
import os
import tempfile
from pathlib import Path


def render(directory):
    # Caché local temporal; no escribe en el perfil global del usuario.
    os.environ.setdefault(
        "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "poker-matplotlib")
    )
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    root = Path(directory)

    def read(name):
        with (root / name).open() as f:
            return list(csv.DictReader(f))

    summary = read("summary.csv")
    uncertainty = {(r["strategy"], r["opponent"]): r for r in read("uncertainty.csv")}
    titles = {
        "stable": "Rival estable",
        "loose": "Rival distinto (loose)",
        "changing": "Rival cambia en mano 26",
    }
    colors = {
        "fixed": "#666666",
        "profit": "#0072B2",
        "risk2": "#D55E00",
        "risk10": "#009E73",
    }

    def label(strategy):
        if strategy.startswith("fixed"):
            return "Fija", "fixed"
        if strategy.startswith("profit"):
            return "Beneficio / R=30", "profit"
        if ":R=2:" in strategy:
            return "R=2", "risk2"
        return "R=10", "risk10"

    fig, axes = plt.subplots(
        1, 3, figsize=(14, 4.8), layout="constrained", sharex=True, sharey=True
    )
    for ax, opponent in zip(axes, titles):
        for row in summary:
            if row["opponent"] != opponent or ":R=30:" in row["strategy"]:
                continue
            name, key = label(row["strategy"])
            u = uncertainty[row["strategy"], opponent]
            x = float(row["mean_profit"])
            y = float(row["cvar_session_loss"])
            # Intervalos marginales, no región de confianza conjunta.
            ax.plot(
                [float(u["mean_low"]), float(u["mean_high"])],
                [y, y],
                color=colors[key],
                alpha=0.6,
            )
            ax.plot(
                [x, x],
                [float(u["cvar_low"]), float(u["cvar_high"])],
                color=colors[key],
                alpha=0.6,
            )
            ax.scatter([x], [y], color=colors[key], label=name, zorder=3)
        ax.set_title(titles[opponent])
        ax.set_xlabel("Ganancia media por sesión (fichas)")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("CVaR .90 de pérdida por sesión (fichas)")
    axes[-1].legend(fontsize=8)
    fig.suptitle("Beneficio y riesgo · intervalos bootstrap marginales del 95 %")
    fig.savefig(root / "risk-return.svg")
    fig.savefig(root / "risk-return.png", dpi=150)
    plt.close(fig)
    trajectories = read("trajectories.csv")
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5), layout="constrained", sharey=True)
    for ax, opponent in zip(axes, titles):
        for strategy in sorted({r["strategy"] for r in trajectories}):
            if ":R=30:" in strategy:
                continue
            rows = [
                r
                for r in trajectories
                if r["opponent"] == opponent and r["strategy"] == strategy
            ]
            name, key = label(strategy)
            ax.plot(
                [int(r["hand"]) for r in rows],
                [float(r["mean_bankroll"]) for r in rows],
                label=name,
                color=colors[key],
            )
        ax.set_title(titles[opponent])
        ax.set_xlabel("Mano")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("Capital medio J1 (fichas)")
    axes[-1].legend(fontsize=8)
    fig.suptitle("Trayectorias medias · saldo terminal conservado hasta mano 50")
    fig.savefig(root / "trajectories.svg")
    fig.savefig(root / "trajectories.png", dpi=150)
    plt.close(fig)
    data = json.loads((root / "exposure.json").read_text())
    fig, ax = plt.subplots(figsize=(6, 5), layout="constrained")
    for name, color in [("br1", "#0072B2"), ("br2", "#D55E00")]:
        pairs = [
            (own, int(other)) if name == "br1" else (int(other), own)
            for other, values in data[name].items()
            for own in values
        ]
        if pairs:
            ax.scatter(*zip(*pairs), s=12, label=name.upper(), color=color)
    ax.set(
        xlabel="q1 (fichas adicionales)",
        ylabel="q2 (fichas adicionales)",
        title="Exposición: mejores respuestas en coordenadas comunes",
    )
    ax.legend()
    ax.grid(alpha=0.2)
    fig.savefig(root / "best-responses.svg")
    plt.close(fig)

    for svg in root.glob("*.svg"):
        svg.write_text(
            "\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n"
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("directory")
    render(parser.parse_args().directory)
