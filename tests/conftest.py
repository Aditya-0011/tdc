"""Shared test factory for building people quickly."""

from __future__ import annotations

from typing import Any

from tdc_matcher.models import Person
from tdc_matcher.validators import person_from_dict


def make_person_dict(
    id: str = "p001",
    name: str = "Aarav",
    age: int = 29,
    city: str = "Mumbai",
    state: str = "Maharashtra",
    country: str = "India",
    smoking: bool = False,
    wants_children: str = "yes",
    relationship_goal: str = "marriage",
    lifestyle: str = "moderate",
    pref_age: tuple[int, int, str] = (27, 33, "hard"),
    pref_location: tuple[str, str] = ("Mumbai", "soft"),
    pref_smoking: tuple[bool, str] = (False, "hard"),
    pref_wants_children: tuple[str, str] = ("yes", "soft"),
    pref_relationship_goal: tuple[str, str] = ("marriage", "hard"),
    pref_lifestyle: tuple[str, str] = ("moderate", "soft"),
) -> dict[str, Any]:
    return {
        "id": id,
        "name": name,
        "attributes": {
            "age": age,
            "location": {"city": city, "state": state, "country": country},
            "smoking": smoking,
            "wants_children": wants_children,
            "relationship_goal": relationship_goal,
            "lifestyle": lifestyle,
        },
        "preferences": {
            "age": {"min": pref_age[0], "max": pref_age[1], "strictness": pref_age[2]},
            "location": {"city": pref_location[0], "strictness": pref_location[1]},
            "smoking": {"value": pref_smoking[0], "strictness": pref_smoking[1]},
            "wants_children": {
                "value": pref_wants_children[0],
                "strictness": pref_wants_children[1],
            },
            "relationship_goal": {
                "value": pref_relationship_goal[0],
                "strictness": pref_relationship_goal[1],
            },
            "lifestyle": {"value": pref_lifestyle[0], "strictness": pref_lifestyle[1]},
        },
    }


def make_person(**kwargs: Any) -> Person:
    return person_from_dict(make_person_dict(**kwargs))
