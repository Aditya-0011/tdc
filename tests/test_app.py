"""Headless smoke tests for the Streamlit app."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
EXPECTED_ELIGIBLE = "**6 of 14 candidates**"


def run_app(client: str | None = None) -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception
    if client is not None:
        at.selectbox[0].select(client).run()
        assert not at.exception
    return at


class TestMainFlow:
    def test_app_renders_with_sample_data(self):
        at = run_app()
        assert at.title[0].value == "TDC Matcher"
        assert len(at.selectbox[0].options) == 15

    def test_selected_person_shows_ranked_candidates(self):
        at = run_app("Aarav (p001)")
        markdown = [m.value for m in at.markdown]
        assert any("STRONG MATCH" in m for m in markdown)
        assert any(EXPECTED_ELIGIBLE in m for m in markdown)
        # Priya is the strong match and must be ranked first.
        assert (
            "Priya"
            in markdown[
                markdown.index(next(m for m in markdown if "STRONG MATCH" in m))
            ]
        )

    def test_not_suitable_hidden_by_default(self):
        at = run_app("Aarav (p001)")
        markdown = [m.value for m in at.markdown]
        assert not any("Kabir" in m for m in markdown)

    def test_not_suitable_shown_when_enabled(self):
        at = run_app("Aarav (p001)")
        at.checkbox[0].check().run()
        assert not at.exception
        markdown = [m.value for m in at.markdown]
        assert any("Kabir" in m for m in markdown)
        assert any("NOT SUITABLE" in m for m in markdown)


def fill_valid_person(form) -> None:
    """Fill the add-person form with valid values (name, cities, state)."""
    text_inputs = form.get("text_input")
    text_inputs[0].set_value("Test Person")
    text_inputs[1].set_value("Mumbai")
    text_inputs[2].set_value("Maharashtra")
    text_inputs[4].set_value("Mumbai")


class TestAddPersonForm:
    def test_form_rejects_missing_fields(self):
        at = run_app()
        form = at.sidebar.get("form")[0]
        # Submit with an empty name and city.
        form.button[0].click().run()
        assert not at.exception
        assert len(at.sidebar.error) > 0

    def test_form_adds_valid_person(self):
        at = run_app()
        form = at.sidebar.get("form")[0]
        fill_valid_person(form)
        form.button[0].click().run()
        assert not at.exception
        assert not at.sidebar.error
        assert len(at.selectbox[0].options) == 16
        assert "Test Person (p016)" in at.selectbox[0].options

    def test_form_rejects_invalid_age_range(self):
        at = run_app()
        form = at.sidebar.get("form")[0]
        fill_valid_person(form)
        number_inputs = form.get("number_input")
        number_inputs[1].set_value(35)
        number_inputs[2].set_value(25)
        form.button[0].click().run()
        assert not at.exception
        assert any("must not be greater than" in e.value for e in at.sidebar.error)
