"""Tests for sample data files and JSON round-tripping."""

from __future__ import annotations

import json
from pathlib import Path

from tdc_matcher.data import (
    PEOPLE_PATH,
    TEMPLATE_PATH,
    load_people_from_file,
    load_sample_people,
    people_to_json,
    read_template_text,
)
from tdc_matcher.matcher import find_matches
from tdc_matcher.models import MatchStatus
from tdc_matcher.validators import parse_people, validate_people


class TestSampleData:
    def test_sample_file_is_valid(self):
        raw = json.loads(PEOPLE_PATH.read_text(encoding="utf-8"))
        assert validate_people(raw) == []

    def test_sample_file_has_15_people(self):
        people, errors = load_sample_people()
        assert errors == []
        assert len(people) == 15

    def test_template_file_is_valid(self):
        raw = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
        assert validate_people(raw) == []

    def test_sample_data_covers_all_three_statuses(self):
        """Aarav must have at least one STRONG, one POSSIBLE and one NOT SUITABLE result."""
        people, _ = load_sample_people()
        aarav = next(p for p in people if p.name == "Aarav")
        statuses = {r.status for r in find_matches(aarav, people)}
        assert statuses == {
            MatchStatus.STRONG_MATCH,
            MatchStatus.POSSIBLE_MATCH,
            MatchStatus.NOT_SUITABLE,
        }

    def test_sample_data_contains_maybe_future(self):
        raw = json.loads(PEOPLE_PATH.read_text(encoding="utf-8"))
        values = {p["attributes"]["wants_children"] for p in raw["people"]}
        assert "maybe_future" in values

    def test_sample_data_has_asymmetric_strictness_case(self):
        """Dev (p011) is hard on location while Aarav is soft — Aarav/Dev must be NOT SUITABLE
        with the mismatch coming from Dev's direction only."""
        people, _ = load_sample_people()
        aarav = next(p for p in people if p.id == "p001")
        dev = next(p for p in people if p.id == "p011")
        results = find_matches(aarav, people)
        dev_result = next(r for r in results if r.candidate.id == dev.id)
        assert dev_result.status is MatchStatus.NOT_SUITABLE
        assert all(c.dimension == "location" for c in dev_result.b_to_a.hard_mismatches)
        assert dev_result.a_to_b.hard_mismatches == []


class TestFileLoading:
    def test_missing_file_reports_error(self, tmp_path: Path):
        people, errors = load_people_from_file(tmp_path / "nope.json")
        assert people == []
        assert any("File not found" in e for e in errors)

    def test_malformed_json_reports_error(self, tmp_path: Path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        people, errors = load_people_from_file(bad)
        assert people == []
        assert any("Invalid JSON" in e for e in errors)

    def test_invalid_content_reports_errors(self, tmp_path: Path):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"people": [{"id": "p001"}]}), encoding="utf-8")
        people, errors = load_people_from_file(bad)
        assert people == []
        assert errors != []


class TestRoundTrip:
    def test_people_to_json_round_trips(self):
        people, _ = load_sample_people()
        text = people_to_json(people)
        reparsed, errors = parse_people(json.loads(text))
        assert errors == []
        assert [p.id for p in reparsed] == [p.id for p in people]

    def test_template_text_is_valid_json(self):
        raw = json.loads(read_template_text())
        assert validate_people(raw) == []
