"""Interfaz de estudio: predicciones registradas y resultados separados."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from poker.game import Config
from poker.simulation import session

st.set_page_config(page_title="Laboratorio de póker", layout="wide")
st.title("Póker finito · beneficio y riesgo")
st.caption(
    "Una ronda preflop; no es no-limit Hold’em completo. Riesgo local ≠ riesgo de sesión."
)
strategy = st.sidebar.selectbox("Estrategia J1", ["risk", "profit", "fixed", "minrisk"])
opponent = st.sidebar.selectbox(
    "Rival J2", ["stable", "loose", "tight", "changing", "minrisk"]
)
model = st.sidebar.selectbox(
    "Rival estimado / continuación", ["stable", "loose", "tight"]
)
capital = st.sidebar.number_input("Capital por jugador", min_value=1, value=455, step=1)
hands = st.sidebar.number_input(
    "Máximo de manos", min_value=1, max_value=50, value=50, step=1
)
seed = st.sidebar.number_input("Semilla", min_value=0, value=10000, step=1)
scenarios = st.sidebar.number_input(
    "Escenarios por decisión",
    min_value=1,
    max_value=512,
    value=Config().scenarios,
    step=1,
)
alpha = st.sidebar.slider("Alpha CVaR", 0.0, 0.99, 0.9)
limit = st.sidebar.number_input("Límite CVaR local J1", value=10.0)
minimum = st.sidebar.number_input("Beneficio mínimo para minrisk", value=5.0)
if st.button("Ejecutar sesión"):
    st.session_state.rows = session(
        Config(int(capital), int(hands), alpha, int(scenarios)),
        strategy,
        opponent,
        int(seed),
        limit,
        minimum,
        model,
    )
if "rows" in st.session_state:
    rows = st.session_state.rows
    st.write(
        "Configuración ejecutada (los controles nuevos requieren ejecutar de nuevo):",
        rows[0]["config"],
    )
    st.write({k: rows[0][k] for k in ("strategy", "opponent", "condition")})
    st.line_chart(
        pd.DataFrame(
            [
                {
                    "hand": 0,
                    "J1": rows[0]["config"]["capital"],
                    "J2": rows[0]["config"]["capital"],
                }
            ]
            + [
                {"hand": r["hand"], "J1": r["bankroll_1"], "J2": r["bankroll_2"]}
                for r in rows
            ]
        ).set_index("hand")
    )
    hand = st.select_slider("Mano registrada", options=list(range(1, len(rows) + 1)))
    row = rows[hand - 1]
    view = st.radio("Vista", ["Jugador 1", "Jugador 2", "Observador"], horizontal=True)
    player = 0 if view == "Jugador 1" else 1
    st.write(
        "Cartas (rango 2–14; palo 0–3):",
        row["holes"] if view == "Observador" else row["holes"][player],
    )
    st.write("Posición de ciega pequeña:", row["small"])
    st.write("Predicciones antes de actuar")
    for event in row["events"]:
        if view == "Observador" or event["player"] == player + 1:
            st.write({k: v for k, v in event.items() if k != "candidates"})
            if event["candidates"]:
                st.dataframe(pd.DataFrame(event["candidates"]))
            if event["status"] == "infeasible_emergency":
                st.warning(
                    "INVIABLE en las acciones y escenarios considerados. Se aplicó alternativa de emergencia."
                )
        else:
            st.write(
                {k: event[k] for k in ("player", "action", "paid_before", "pot_before")}
            )
    st.write("Resultado observado después de cerrar la mano")
    if row["folded"] is None or view == "Observador":
        st.write("Mesa:", row["board"])
    else:
        st.caption("Sin showdown: no se revelan comunitarias ni cartas rivales.")
    st.write(
        {
            k: row[k]
            for k in ("pot", "refund", "folded", "bankroll_1", "bankroll_2", "profit_1")
        }
    )
    # Exportación respeta la vista, incluso para escenarios/semillas reproducibles.
    if view == "Observador":
        payload = rows
    else:
        payload = [
            {
                k: r[k]
                for k in (
                    "hand",
                    "bankroll_1",
                    "bankroll_2",
                    "profit_1",
                    "pot",
                    "folded",
                )
            }
            | {
                "own_cards": r["holes"][player],
                "public_actions": [(e["player"], e["action"]) for e in r["events"]],
            }
            for r in rows
        ]
    st.download_button(
        "Exportar vista JSON", json.dumps(payload, indent=2), file_name="sesion.json"
    )
path = Path("results/study/summary.csv")
if path.exists():
    st.subheader("Experimento publicado · resultados observados")
    data = pd.read_csv(path)
    st.dataframe(data)
    st.scatter_chart(data, x="mean_profit", y="cvar_session_loss", color="opponent")
    st.download_button(
        "Exportar resumen CSV", path.read_bytes(), file_name="summary.csv"
    )
    diagnostics = Path("results/study/diagnostics.csv")
    if diagnostics.exists():
        st.dataframe(pd.read_csv(diagnostics))

    for filename, title in [
        ("uncertainty.csv", "Intervalos bootstrap"),
        ("paired.csv", "Diferencias emparejadas frente a fija"),
    ]:
        source = path.parent / filename
        if source.exists():
            with st.expander(title):
                st.dataframe(pd.read_csv(source))
