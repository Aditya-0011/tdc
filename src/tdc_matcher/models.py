"""Typed data structures for the TDC Matcher prototype.

Every person in the pool is both a TDC client and a potential candidate.
There is no separate client/candidate role.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

PREF_VALUE = TypeVar("PREF_VALUE")


class Strictness(str, Enum):
    """Mismatch handling for a preference."""

    HARD = "hard"
    SOFT = "soft"


class WantsChildren(str, Enum):
    YES = "yes"
    NO = "no"
    MAYBE_FUTURE = "maybe_future"


class RelationshipGoal(str, Enum):
    MARRIAGE = "marriage"
    LONG_TERM = "long_term"
    OPEN = "open"


class Lifestyle(str, Enum):
    QUIET = "quiet"
    MODERATE = "moderate"
    SOCIAL = "social"


class MatchStatus(str, Enum):
    STRONG_MATCH = "STRONG MATCH"
    POSSIBLE_MATCH = "POSSIBLE MATCH"
    NOT_SUITABLE = "NOT SUITABLE"


@dataclass(frozen=True)
class Location:
    city: str
    state: str
    country: str

    def to_dict(self) -> dict[str, str]:
        return {"city": self.city, "state": self.state, "country": self.country}


@dataclass(frozen=True)
class Attributes:
    age: int
    location: Location
    smoking: bool
    wants_children: WantsChildren
    relationship_goal: RelationshipGoal
    lifestyle: Lifestyle

    def to_dict(self) -> dict[str, object]:
        return {
            "age": self.age,
            "location": self.location.to_dict(),
            "smoking": self.smoking,
            "wants_children": self.wants_children.value,
            "relationship_goal": self.relationship_goal.value,
            "lifestyle": self.lifestyle.value,
        }


@dataclass(frozen=True)
class AgePreference:
    min: int
    max: int
    strictness: Strictness


@dataclass(frozen=True)
class LocationPreference:
    city: str
    strictness: Strictness


@dataclass(frozen=True)
class ValuePreference(Generic[PREF_VALUE]):
    value: PREF_VALUE
    strictness: Strictness


@dataclass(frozen=True)
class Preferences:
    age: AgePreference
    location: LocationPreference
    smoking: ValuePreference[bool]
    wants_children: ValuePreference[WantsChildren]
    relationship_goal: ValuePreference[RelationshipGoal]
    lifestyle: ValuePreference[Lifestyle]

    def to_dict(self) -> dict[str, object]:
        return {
            "age": {
                "min": self.age.min,
                "max": self.age.max,
                "strictness": self.age.strictness.value,
            },
            "location": {
                "city": self.location.city,
                "strictness": self.location.strictness.value,
            },
            "smoking": {
                "value": self.smoking.value,
                "strictness": self.smoking.strictness.value,
            },
            "wants_children": {
                "value": self.wants_children.value.value,
                "strictness": self.wants_children.strictness.value,
            },
            "relationship_goal": {
                "value": self.relationship_goal.value.value,
                "strictness": self.relationship_goal.strictness.value,
            },
            "lifestyle": {
                "value": self.lifestyle.value.value,
                "strictness": self.lifestyle.strictness.value,
            },
        }


@dataclass(frozen=True)
class Person:
    id: str
    name: str
    attributes: Attributes
    preferences: Preferences

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "attributes": self.attributes.to_dict(),
            "preferences": self.preferences.to_dict(),
        }
