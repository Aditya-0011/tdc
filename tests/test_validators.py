"""Tests for raw JSON validation."""

from __future__ import annotations

from conftest import make_person_dict

from tdc_matcher.validators import parse_people, validate_people


def valid_file() -> dict:
    return {"people": [make_person_dict()]}


def errors_of(raw) -> list[str]:
    return validate_people(raw)


class TestTopLevel:
    def test_not_an_object(self):
        assert errors_of([1, 2]) != []

    def test_missing_people_key(self):
        assert errors_of({}) != []

    def test_people_not_a_list(self):
        assert errors_of({"people": {"id": "p001"}}) != []

    def test_empty_people_list(self):
        assert errors_of({"people": []}) != []

    def test_valid_file_passes(self):
        assert errors_of(valid_file()) == []

    def test_error_messages_are_actionable(self):
        message = errors_of({"people": {}})[0]
        assert "people" in message


class TestIds:
    def test_missing_id(self):
        raw = valid_file()
        del raw["people"][0]["id"]
        assert any("'id' is required" in e for e in errors_of(raw))

    def test_duplicate_ids(self):
        raw = {
            "people": [
                make_person_dict(id="p001"),
                make_person_dict(id="p001", name="B"),
            ]
        }
        errors = errors_of(raw)
        assert any("duplicate id" in e for e in errors)

    def test_missing_name(self):
        raw = valid_file()
        del raw["people"][0]["name"]
        assert any("'name' is required" in e for e in errors_of(raw))


class TestAttributes:
    def test_missing_attributes(self):
        raw = valid_file()
        del raw["people"][0]["attributes"]
        assert any("'attributes' must be an object" in e for e in errors_of(raw))

    def test_invalid_age_not_integer(self):
        raw = valid_file()
        raw["people"][0]["attributes"]["age"] = "twenty"
        assert any("attributes.age must be an integer" in e for e in errors_of(raw))

    def test_invalid_age_out_of_range(self):
        raw = valid_file()
        raw["people"][0]["attributes"]["age"] = 12
        assert any("must be between" in e for e in errors_of(raw))

    def test_missing_location_city(self):
        raw = valid_file()
        del raw["people"][0]["attributes"]["location"]["city"]
        assert any("location.city" in e for e in errors_of(raw))

    def test_invalid_smoking(self):
        raw = valid_file()
        raw["people"][0]["attributes"]["smoking"] = "no"
        assert any("smoking must be true or false" in e for e in errors_of(raw))

    def test_invalid_wants_children_enum(self):
        raw = valid_file()
        raw["people"][0]["attributes"]["wants_children"] = "someday"
        assert any(
            "wants_children must be one of: yes, no, maybe_future" in e
            for e in errors_of(raw)
        )

    def test_invalid_relationship_goal_enum(self):
        raw = valid_file()
        raw["people"][0]["attributes"]["relationship_goal"] = "casual"
        assert any("relationship_goal must be one of" in e for e in errors_of(raw))

    def test_invalid_lifestyle_enum(self):
        raw = valid_file()
        raw["people"][0]["attributes"]["lifestyle"] = "wild"
        assert any("lifestyle must be one of" in e for e in errors_of(raw))


class TestPreferences:
    def test_invalid_age_range_min_greater_than_max(self):
        raw = valid_file()
        raw["people"][0]["preferences"]["age"] = {
            "min": 35,
            "max": 25,
            "strictness": "hard",
        }
        assert any("must not be greater than" in e for e in errors_of(raw))

    def test_invalid_age_preference_bound(self):
        raw = valid_file()
        raw["people"][0]["preferences"]["age"]["min"] = 10
        assert any("preferences.age.min must be between" in e for e in errors_of(raw))

    def test_invalid_strictness(self):
        raw = valid_file()
        raw["people"][0]["preferences"]["smoking"]["strictness"] = "strict"
        assert any("strictness must be one of: hard, soft" in e for e in errors_of(raw))

    def test_invalid_enum_in_preference(self):
        raw = valid_file()
        raw["people"][0]["preferences"]["lifestyle"]["value"] = "chaotic"
        assert any(
            "preferences.lifestyle.value must be one of: quiet, moderate, social" in e
            for e in errors_of(raw)
        )

    def test_missing_preference_dimension(self):
        raw = valid_file()
        del raw["people"][0]["preferences"]["location"]
        assert any(
            "preferences.location must be an object" in e for e in errors_of(raw)
        )


class TestParsePeople:
    def test_parse_valid_returns_people(self):
        raw = {
            "people": [
                make_person_dict(id="p001"),
                make_person_dict(id="p002", name="B"),
            ]
        }
        people, errors = parse_people(raw)
        assert errors == []
        assert len(people) == 2
        assert people[0].name == "Aarav"

    def test_parse_invalid_returns_errors_only(self):
        raw = {"people": [make_person_dict(), make_person_dict()]}
        people, errors = parse_people(raw)
        assert people == []
        assert any("duplicate id" in e for e in errors)

    def test_collects_multiple_errors_across_people(self):
        raw = {
            "people": [
                make_person_dict(id="p001", age="bad"),
                make_person_dict(id="p002", wants_children="someday"),
            ]
        }
        _, errors = parse_people(raw)
        assert len(errors) == 2
