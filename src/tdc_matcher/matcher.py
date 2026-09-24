"""Core matching engine.

Matching is bidirectional: for a pair A/B we evaluate
``A.preferences -> B.attributes`` and ``B.preferences -> A.attributes``.
Each person's preference is evaluated according to that person's own
strictness — strictness is never combined across people.

Classification:
- any hard mismatch in either direction  -> NOT SUITABLE
- no hard mismatch, all soft match       -> STRONG MATCH
- no hard mismatch, any soft mismatch    -> POSSIBLE MATCH
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import (
    Lifestyle,
    MatchStatus,
    Person,
    Preferences,
    RelationshipGoal,
    Strictness,
    ValuePreference,
    WantsChildren,
)

STATUS_SORT_ORDER = {
    MatchStatus.STRONG_MATCH: 0,
    MatchStatus.POSSIBLE_MATCH: 1,
    MatchStatus.NOT_SUITABLE: 2,
}


@dataclass(frozen=True)
class DimensionCheck:
    """Result of one preference dimension in one direction."""

    dimension: str
    strictness: Strictness
    matched: bool
    preference: str
    attribute: str


@dataclass(frozen=True)
class DirectionEvaluation:
    """All dimension checks for one direction, e.g. A.preferences -> B.attributes."""

    from_name: str
    to_name: str
    checks: list[DimensionCheck] = field(default_factory=list)

    @property
    def hard_mismatches(self) -> list[DimensionCheck]:
        return [
            c for c in self.checks if not c.matched and c.strictness is Strictness.HARD
        ]

    @property
    def soft_checks(self) -> list[DimensionCheck]:
        return [c for c in self.checks if c.strictness is Strictness.SOFT]

    @property
    def soft_match_count(self) -> int:
        return sum(1 for c in self.soft_checks if c.matched)

    @property
    def soft_total(self) -> int:
        return len(self.soft_checks)


@dataclass(frozen=True)
class PairResult:
    """Bidirectional evaluation of one pair."""

    candidate: Person
    a_to_b: DirectionEvaluation
    b_to_a: DirectionEvaluation
    status: MatchStatus

    @property
    def hard_mismatches(self) -> list[DimensionCheck]:
        return self.a_to_b.hard_mismatches + self.b_to_a.hard_mismatches

    @property
    def soft_match_count(self) -> int:
        return self.a_to_b.soft_match_count + self.b_to_a.soft_match_count

    @property
    def soft_total(self) -> int:
        return self.a_to_b.soft_total + self.b_to_a.soft_total

    @property
    def soft_mismatches(self) -> list[DimensionCheck]:
        return [
            c
            for c in self.a_to_b.soft_checks + self.b_to_a.soft_checks
            if not c.matched
        ]

    @property
    def summary_reasons(self) -> list[str]:
        """Short reasons for the result card."""
        if self.status is MatchStatus.NOT_SUITABLE:
            reasons = []
            for direction in (self.a_to_b, self.b_to_a):
                for check in direction.hard_mismatches:
                    reasons.append(
                        f"{direction.from_name}'s hard preference is violated: "
                        f"{check.preference}, but {check.attribute}."
                    )
            return reasons
        if self.status is MatchStatus.STRONG_MATCH:
            return ["All hard and soft preferences match in both directions."]
        reasons = [
            f"Human review required — {len(self.soft_mismatches)} soft mismatch(es):"
        ]
        reasons.extend(
            f"{c.preference}, but {c.attribute}." for c in self.soft_mismatches
        )
        return reasons

    @property
    def soft_ratio(self) -> float:
        if self.soft_total == 0:
            return 1.0
        return self.soft_match_count / self.soft_total


def evaluate(preferences: Preferences, candidate: Person) -> list[DimensionCheck]:
    """Evaluate one person's preferences against a candidate's attributes.

    Returns one check per preference dimension, in fixed order.
    """
    attrs = candidate.attributes
    age_pref = preferences.age
    location_pref = preferences.location
    smoking_pref: ValuePreference[bool] = preferences.smoking
    wants_pref: ValuePreference[WantsChildren] = preferences.wants_children
    goal_pref: ValuePreference[RelationshipGoal] = preferences.relationship_goal
    lifestyle_pref: ValuePreference[Lifestyle] = preferences.lifestyle

    return [
        DimensionCheck(
            dimension="age",
            strictness=age_pref.strictness,
            matched=age_pref.min <= attrs.age <= age_pref.max,
            preference=f"prefers age {age_pref.min}–{age_pref.max}",
            attribute=f"{candidate.name} is {attrs.age}",
        ),
        DimensionCheck(
            dimension="location",
            strictness=location_pref.strictness,
            matched=attrs.location.city == location_pref.city,
            preference=f"prefers someone in {location_pref.city}",
            attribute=f"{candidate.name} lives in {attrs.location.city}",
        ),
        DimensionCheck(
            dimension="smoking",
            strictness=smoking_pref.strictness,
            matched=attrs.smoking == smoking_pref.value,
            preference="prefers a non-smoker"
            if not smoking_pref.value
            else "prefers a smoker",
            attribute=f"{candidate.name} is a smoker"
            if attrs.smoking
            else f"{candidate.name} is a non-smoker",
        ),
        DimensionCheck(
            dimension="wants_children",
            strictness=wants_pref.strictness,
            matched=attrs.wants_children is wants_pref.value,
            preference=f"prefers someone who {_wants_children_text(wants_pref.value)}",
            attribute=f"{candidate.name} {_wants_children_text(attrs.wants_children)}",
        ),
        DimensionCheck(
            dimension="relationship_goal",
            strictness=goal_pref.strictness,
            matched=attrs.relationship_goal is goal_pref.value,
            preference=f"prefers goal '{goal_pref.value.value}'",
            attribute=f"{candidate.name} wants '{attrs.relationship_goal.value}'",
        ),
        DimensionCheck(
            dimension="lifestyle",
            strictness=lifestyle_pref.strictness,
            matched=attrs.lifestyle is lifestyle_pref.value,
            preference=f"prefers lifestyle '{lifestyle_pref.value.value}'",
            attribute=f"{candidate.name} has lifestyle '{attrs.lifestyle.value}'",
        ),
    ]


def evaluate_pair(selected: Person, candidate: Person) -> PairResult:
    """Evaluate a pair in both directions and classify it."""
    a_to_b = DirectionEvaluation(
        from_name=selected.name,
        to_name=candidate.name,
        checks=evaluate(selected.preferences, candidate),
    )
    b_to_a = DirectionEvaluation(
        from_name=candidate.name,
        to_name=selected.name,
        checks=evaluate(candidate.preferences, selected),
    )

    hard_mismatch = bool(a_to_b.hard_mismatches or b_to_a.hard_mismatches)
    if hard_mismatch:
        status = MatchStatus.NOT_SUITABLE
    elif (
        a_to_b.soft_match_count == a_to_b.soft_total
        and b_to_a.soft_match_count == b_to_a.soft_total
    ):
        status = MatchStatus.STRONG_MATCH
    else:
        status = MatchStatus.POSSIBLE_MATCH

    return PairResult(
        candidate=candidate,
        a_to_b=a_to_b,
        b_to_a=b_to_a,
        status=status,
    )


def find_matches(selected: Person, people: list[Person]) -> list[PairResult]:
    """Evaluate the selected person against everyone else and rank results.

    The selected person is excluded by id. Ranking order:
    STRONG MATCH, then POSSIBLE MATCH by soft-match ratio (descending),
    then NOT SUITABLE.
    """
    results = [
        evaluate_pair(selected, candidate)
        for candidate in people
        if candidate.id != selected.id
    ]
    results.sort(
        key=lambda r: (
            STATUS_SORT_ORDER[r.status],
            -r.soft_ratio,
            r.candidate.name,
        )
    )
    return results


def _wants_children_text(value: WantsChildren) -> str:
    if value is WantsChildren.YES:
        return "wants children"
    if value is WantsChildren.NO:
        return "does not want children"
    return "may want children in the future"
