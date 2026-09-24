"""Validation for raw people JSON data.

The MVP has no database: people arrive as JSON (file upload, sample data,
or the add-person form) and must be validated before use. Validation
collects actionable error messages instead of raising, so the UI can
show every problem with an uploaded file at once.
"""

from __future__ import annotations

from typing import Any, TypeGuard

from .models import (
    AgePreference,
    Attributes,
    Lifestyle,
    Location,
    LocationPreference,
    Person,
    Preferences,
    RelationshipGoal,
    Strictness,
    ValuePreference,
    WantsChildren,
)

MIN_AGE = 18
MAX_AGE = 99

STRICTNESS_VALUES = ("hard", "soft")
WANTS_CHILDREN_VALUES = tuple(v.value for v in WantsChildren)
RELATIONSHIP_GOAL_VALUES = tuple(v.value for v in RelationshipGoal)
LIFESTYLE_VALUES = tuple(v.value for v in Lifestyle)


def validate_people(raw: Any) -> list[str]:
    """Validate the canonical top-level structure ``{"people": [...]}``.

    Returns a list of human-readable error messages; empty means valid.
    """
    errors: list[str] = []
    if not isinstance(raw, dict):
        return ["Top-level JSON must be an object with a 'people' list."]
    people = raw.get("people")
    if not isinstance(people, list):
        return ["Top-level JSON must contain a 'people' list."]
    if not people:
        return ["The 'people' list is empty — add at least one person."]

    seen_ids: set[str] = set()
    for index, entry in enumerate(people):
        errors.extend(_validate_person(entry, index, seen_ids))
    return errors


def parse_people(raw: Any) -> tuple[list[Person], list[str]]:
    """Validate raw JSON and build Person objects.

    Returns ``(people, errors)``. If validation fails, people is empty and
    errors contains every problem found.
    """
    errors = validate_people(raw)
    if errors:
        return [], errors
    people = [person_from_dict(entry) for entry in raw["people"]]
    return people, []


def person_from_dict(data: dict[str, Any]) -> Person:
    """Build a Person from an already-validated dict."""
    attrs = data["attributes"]
    loc = attrs["location"]
    prefs = data["preferences"]
    return Person(
        id=data["id"],
        name=data["name"],
        attributes=Attributes(
            age=attrs["age"],
            location=Location(
                city=loc["city"], state=loc["state"], country=loc["country"]
            ),
            smoking=attrs["smoking"],
            wants_children=WantsChildren(attrs["wants_children"]),
            relationship_goal=RelationshipGoal(attrs["relationship_goal"]),
            lifestyle=Lifestyle(attrs["lifestyle"]),
        ),
        preferences=Preferences(
            age=AgePreference(
                min=prefs["age"]["min"],
                max=prefs["age"]["max"],
                strictness=Strictness(prefs["age"]["strictness"]),
            ),
            location=LocationPreference(
                city=prefs["location"]["city"],
                strictness=Strictness(prefs["location"]["strictness"]),
            ),
            smoking=ValuePreference(
                value=prefs["smoking"]["value"],
                strictness=Strictness(prefs["smoking"]["strictness"]),
            ),
            wants_children=ValuePreference(
                value=WantsChildren(prefs["wants_children"]["value"]),
                strictness=Strictness(prefs["wants_children"]["strictness"]),
            ),
            relationship_goal=ValuePreference(
                value=RelationshipGoal(prefs["relationship_goal"]["value"]),
                strictness=Strictness(prefs["relationship_goal"]["strictness"]),
            ),
            lifestyle=ValuePreference(
                value=Lifestyle(prefs["lifestyle"]["value"]),
                strictness=Strictness(prefs["lifestyle"]["strictness"]),
            ),
        ),
    )


def _validate_person(entry: Any, index: int, seen_ids: set[str]) -> list[str]:
    label = f"people[{index}]"
    if not isinstance(entry, dict):
        return [f"{label}: each person must be an object."]

    person_id = entry.get("id")
    if not _is_nonempty_str(person_id):
        errors = [f"{label}: 'id' is required and must be a non-empty string."]
        person_id = None
    else:
        label = f"{label} (id='{person_id}')"
        if person_id in seen_ids:
            errors = [f"{label}: duplicate id '{person_id}' — ids must be unique."]
        else:
            seen_ids.add(person_id)
            errors = []

    if not _is_nonempty_str(entry.get("name")):
        errors.append(f"{label}: 'name' is required and must be a non-empty string.")

    attributes = entry.get("attributes")
    if not isinstance(attributes, dict):
        errors.append(f"{label}: 'attributes' must be an object.")
    else:
        errors.extend(_validate_attributes(attributes, label))

    preferences = entry.get("preferences")
    if not isinstance(preferences, dict):
        errors.append(f"{label}: 'preferences' must be an object.")
    else:
        errors.extend(_validate_preferences(preferences, label))

    return errors


def _validate_attributes(attrs: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []

    age = attrs.get("age")
    if not _is_int(age):
        errors.append(f"{label}.attributes.age must be an integer (got {age!r}).")
    elif not MIN_AGE <= age <= MAX_AGE:
        errors.append(
            f"{label}.attributes.age must be between {MIN_AGE} and {MAX_AGE} (got {age})."
        )

    location = attrs.get("location")
    if not isinstance(location, dict):
        errors.append(f"{label}.attributes.location must be an object.")
    else:
        for field in ("city", "state", "country"):
            if not _is_nonempty_str(location.get(field)):
                errors.append(
                    f"{label}.attributes.location.{field} is required and must be a non-empty string."
                )

    smoking = attrs.get("smoking")
    if not isinstance(smoking, bool):
        errors.append(
            f"{label}.attributes.smoking must be true or false (got {smoking!r})."
        )

    errors.extend(
        _validate_enum(
            attrs.get("wants_children"),
            WANTS_CHILDREN_VALUES,
            f"{label}.attributes.wants_children",
        )
    )
    errors.extend(
        _validate_enum(
            attrs.get("relationship_goal"),
            RELATIONSHIP_GOAL_VALUES,
            f"{label}.attributes.relationship_goal",
        )
    )
    errors.extend(
        _validate_enum(
            attrs.get("lifestyle"), LIFESTYLE_VALUES, f"{label}.attributes.lifestyle"
        )
    )
    return errors


def _validate_preferences(prefs: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []

    age_pref = prefs.get("age")
    if not isinstance(age_pref, dict):
        errors.append(
            f"{label}.preferences.age must be an object with 'min', 'max', 'strictness'."
        )
    else:
        for bound in ("min", "max"):
            value = age_pref.get(bound)
            if not _is_int(value):
                errors.append(
                    f"{label}.preferences.age.{bound} must be an integer (got {value!r})."
                )
            elif not MIN_AGE <= value <= MAX_AGE:
                errors.append(
                    f"{label}.preferences.age.{bound} must be between {MIN_AGE} and {MAX_AGE} (got {value})."
                )
        min_value, max_value = age_pref.get("min"), age_pref.get("max")
        if _is_int(min_value) and _is_int(max_value) and min_value > max_value:
            errors.append(
                f"{label}.preferences.age: 'min' ({min_value}) must not be greater than 'max' ({max_value})."
            )
        errors.extend(_validate_strictness(age_pref, f"{label}.preferences.age"))

    location_pref = prefs.get("location")
    if not isinstance(location_pref, dict):
        errors.append(
            f"{label}.preferences.location must be an object with 'city', 'strictness'."
        )
    else:
        if not _is_nonempty_str(location_pref.get("city")):
            errors.append(
                f"{label}.preferences.location.city is required and must be a non-empty string."
            )
        errors.extend(
            _validate_strictness(location_pref, f"{label}.preferences.location")
        )

    smoking_pref = prefs.get("smoking")
    if not isinstance(smoking_pref, dict):
        errors.append(
            f"{label}.preferences.smoking must be an object with 'value', 'strictness'."
        )
    else:
        if not isinstance(smoking_pref.get("value"), bool):
            errors.append(
                f"{label}.preferences.smoking.value must be true or false (got {smoking_pref.get('value')!r})."
            )
        errors.extend(
            _validate_strictness(smoking_pref, f"{label}.preferences.smoking")
        )

    for dimension, allowed in (
        ("wants_children", WANTS_CHILDREN_VALUES),
        ("relationship_goal", RELATIONSHIP_GOAL_VALUES),
        ("lifestyle", LIFESTYLE_VALUES),
    ):
        pref = prefs.get(dimension)
        if not isinstance(pref, dict):
            errors.append(
                f"{label}.preferences.{dimension} must be an object with 'value', 'strictness'."
            )
        else:
            errors.extend(
                _validate_enum(
                    pref.get("value"), allowed, f"{label}.preferences.{dimension}.value"
                )
            )
            errors.extend(
                _validate_strictness(pref, f"{label}.preferences.{dimension}")
            )

    return errors


def _validate_strictness(pref: dict[str, Any], label: str) -> list[str]:
    strictness = pref.get("strictness")
    if strictness not in STRICTNESS_VALUES:
        return [
            f"{label}.strictness must be one of: {', '.join(STRICTNESS_VALUES)} (got {strictness!r})."
        ]
    return []


def _validate_enum(value: Any, allowed: tuple[str, ...], label: str) -> list[str]:
    if value not in allowed:
        return [f"{label} must be one of: {', '.join(allowed)} (got {value!r})."]
    return []


def _is_int(value: Any) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""
