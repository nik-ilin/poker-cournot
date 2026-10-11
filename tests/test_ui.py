from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_ui_session():
    app = AppTest.from_file(
        Path(__file__).resolve().parents[1] / "app.py", default_timeout=60
    ).run()
    assert not app.exception
    # Short but real session through the interface.
    for number in app.sidebar.number_input:
        if number.label == "Máximo de manos":
            number.set_value(2)
        if number.label == "Escenarios por decisión":
            number.set_value(2)
    app.button[0].click().run()
    assert not app.exception
    assert len(app.session_state["rows"]) == 2
    app.radio[0].set_value("Observador").run()
    assert not app.exception
