"""Tests for the core matching engine."""

from __future__ import annotations

from conftest import make_person

from tdc_matcher.matcher import evaluate_pair, find_matches
from tdc_matcher.models import MatchStatus


class TestHardPreferences:
    def test_hard_exact_match(self):
        a = make_person(name="A")
        b = make_person(name="B", id="p002")
        result = evaluate_pair(a, b)
        assert result.a_to_b.hard_mismatches == []

    def test_hard_mismatch_detected(self):
        a = make_person(name="A", pref_smoking=(False, "hard"))
        b = make_person(name="B", id="p002", smoking=True)
        result = evaluate_pair(a, b)
        assert any(c.dimension == "smoking" for c in result.a_to_b.hard_mismatches)

    def test_hard_mismatch_overrides_all_soft_matches(self):
        # B matches every soft preference but fails the hard smoking preference.
        a = make_person(name="A", pref_smoking=(False, "hard"))
        b = make_person(
            name="B",
            id="p002",
            age=29,
            city="Mumbai",
            smoking=True,
            wants_children="yes",
            relationship_goal="marriage",
            lifestyle="moderate",
        )
        result = evaluate_pair(a, b)
        # Every one of A's soft preferences matches, yet the hard
        # smoking mismatch still disqualifies the pair.
        assert result.a_to_b.soft_match_count == result.a_to_b.soft_total
        assert result.status is MatchStatus.NOT_SUITABLE


class TestSoftPreferences:
    def test_soft_match_counted(self):
        a = make_person(name="A", pref_lifestyle=("moderate", "soft"))
        b = make_person(name="B", id="p002", lifestyle="moderate")
        result = evaluate_pair(a, b)
        lifestyle = next(c for c in result.a_to_b.checks if c.dimension == "lifestyle")
        assert lifestyle.matched
        assert lifestyle.strictness.value == "soft"
        assert result.a_to_b.soft_match_count >= 1

    def test_soft_mismatch_does_not_disqualify(self):
        a = make_person(name="A", pref_lifestyle=("moderate", "soft"))
        b = make_person(name="B", id="p002", lifestyle="social")
        result = evaluate_pair(a, b)
        assert result.status is MatchStatus.POSSIBLE_MATCH


class TestBidirectional:
    def test_a_accepts_but_b_hard_rejects(self):
        # A has no problem with B, but B's hard age preference excludes A.
        a = make_person(name="A", age=40)
        b = make_person(name="B", id="p002", pref_age=(25, 33, "hard"))
        result = evaluate_pair(a, b)
        assert result.a_to_b.hard_mismatches == []
        assert result.b_to_a.hard_mismatches != []
        assert result.status is MatchStatus.NOT_SUITABLE

    def test_both_directions_pass(self):
        a = make_person(name="A")
        b = make_person(name="B", id="p002")
        result = evaluate_pair(a, b)
        assert result.status is MatchStatus.STRONG_MATCH

    def test_asymmetric_strictness_hard_rejects(self):
        # A: non-smoker, hard. B: doesn't care about smoking (soft), but smokes.
        # Only A's hard mismatch disqualifies the pair — B's soft preference
        # for a smoker also fails, but a soft mismatch alone never does.
        a = make_person(name="A", pref_smoking=(False, "hard"))
        b = make_person(name="B", id="p002", smoking=True, pref_smoking=(True, "soft"))
        result = evaluate_pair(a, b)
        assert result.status is MatchStatus.NOT_SUITABLE
        assert any(c.dimension == "smoking" for c in result.a_to_b.hard_mismatches)
        assert result.b_to_a.hard_mismatches == []

    def test_asymmetric_strictness_hard_passes_stays_eligible(self):
        # Same dimension, opposite strictness: A hard non-smoker, B soft
        # non-smoker, and both are non-smokers. Each preference is evaluated
        # with its own owner's strictness — A's check stays hard, B's stays
        # soft — and the pair is not disqualified.
        a = make_person(name="A", pref_smoking=(False, "hard"))
        b = make_person(name="B", id="p002", pref_smoking=(False, "soft"))
        result = evaluate_pair(a, b)
        a_smoking = next(c for c in result.a_to_b.checks if c.dimension == "smoking")
        b_smoking = next(c for c in result.b_to_a.checks if c.dimension == "smoking")
        assert a_smoking.strictness.value == "hard" and a_smoking.matched
        assert b_smoking.strictness.value == "soft" and b_smoking.matched
        assert result.status is not MatchStatus.NOT_SUITABLE

    def test_asymmetric_strictness_both_soft_stays_eligible(self):
        # Same smoking values but both soft: eligible, counted as soft mismatch.
        a = make_person(name="A", pref_smoking=(False, "soft"))
        b = make_person(name="B", id="p002", smoking=True, pref_smoking=(True, "soft"))
        result = evaluate_pair(a, b)
        assert result.status is MatchStatus.POSSIBLE_MATCH


class TestWantsChildren:
    def test_maybe_future_matches_maybe_future(self):
        a = make_person(name="A", pref_wants_children=("maybe_future", "hard"))
        b = make_person(name="B", id="p002", wants_children="maybe_future")
        result = evaluate_pair(a, b)
        check = next(c for c in result.a_to_b.checks if c.dimension == "wants_children")
        assert check.matched
        assert result.status is not MatchStatus.NOT_SUITABLE

    def test_maybe_future_mismatches_yes_as_soft(self):
        # Comparison is exact equality: yes vs maybe_future is a soft
        # mismatch here — no partial numeric compatibility is invented.
        a = make_person(name="A", pref_wants_children=("maybe_future", "soft"))
        b = make_person(name="B", id="p002", wants_children="yes")
        result = evaluate_pair(a, b)
        check = next(c for c in result.a_to_b.checks if c.dimension == "wants_children")
        assert not check.matched
        assert result.status is MatchStatus.POSSIBLE_MATCH

    def test_hard_wants_children_mismatch_disqualifies(self):
        a = make_person(name="A", pref_wants_children=("no", "hard"))
        b = make_person(name="B", id="p002", wants_children="yes")
        result = evaluate_pair(a, b)
        assert result.status is MatchStatus.NOT_SUITABLE


class TestAgeRange:
    def _single_pair(self, candidate_age: int):
        a = make_person(name="A", pref_age=(27, 33, "hard"))
        b = make_person(name="B", id="p002", age=candidate_age)
        return evaluate_pair(a, b)

    def test_age_exactly_min(self):
        assert self._single_pair(27).a_to_b.hard_mismatches == []

    def test_age_exactly_max(self):
        assert self._single_pair(33).a_to_b.hard_mismatches == []

    def test_age_below_min(self):
        assert any(
            c.dimension == "age" for c in self._single_pair(26).a_to_b.hard_mismatches
        )

    def test_age_above_max(self):
        assert any(
            c.dimension == "age" for c in self._single_pair(34).a_to_b.hard_mismatches
        )


class TestClassification:
    def test_strong_match(self):
        a = make_person(name="A")
        b = make_person(name="B", id="p002")
        result = evaluate_pair(a, b)
        assert result.status is MatchStatus.STRONG_MATCH
        assert result.soft_match_count == result.soft_total

    def test_possible_match(self):
        a = make_person(name="A")
        b = make_person(name="B", id="p002", lifestyle="social")
        result = evaluate_pair(a, b)
        assert result.status is MatchStatus.POSSIBLE_MATCH
        assert result.soft_match_count < result.soft_total

    def test_not_suitable(self):
        a = make_person(name="A", pref_relationship_goal=("marriage", "hard"))
        b = make_person(name="B", id="p002", relationship_goal="open")
        result = evaluate_pair(a, b)
        assert result.status is MatchStatus.NOT_SUITABLE


class TestFindMatches:
    def test_excludes_self(self):
        a = make_person(name="A", id="p001")
        pool = [a, make_person(name="B", id="p002")]
        results = find_matches(a, pool)
        assert all(r.candidate.id != a.id for r in results)
        assert len(results) == 1

    def test_ranking_order(self):
        a = make_person(name="A", id="p001")
        strong = make_person(name="Strong", id="p002")
        possible_low = make_person(
            name="LowRatio", id="p003", lifestyle="social", wants_children="no"
        )
        possible_high = make_person(name="HighRatio", id="p004", lifestyle="social")
        not_suitable = make_person(name="Rejected", id="p005", smoking=True)
        pool = [a, possible_low, not_suitable, possible_high, strong]
        results = find_matches(a, pool)
        statuses = [r.status for r in results]
        assert statuses[0] is MatchStatus.STRONG_MATCH
        assert statuses[1] is MatchStatus.POSSIBLE_MATCH
        assert results[1].candidate.name == "HighRatio"
        assert statuses[2] is MatchStatus.POSSIBLE_MATCH
        assert results[2].candidate.name == "LowRatio"
        assert statuses[-1] is MatchStatus.NOT_SUITABLE

    def test_empty_pool(self):
        a = make_person(name="A")
        assert find_matches(a, [a]) == []


class TestExplanations:
    def test_not_suitable_reasons_mention_hard_preference(self):
        a = make_person(name="A", pref_smoking=(False, "hard"))
        b = make_person(name="B", id="p002", smoking=True)
        result = evaluate_pair(a, b)
        reasons = " ".join(result.summary_reasons)
        assert "hard preference is violated" in reasons
        assert "smoker" in reasons

    def test_possible_match_reasons_mention_review(self):
        a = make_person(name="A")
        b = make_person(name="B", id="p002", lifestyle="social")
        result = evaluate_pair(a, b)
        assert any("Human review" in r for r in result.summary_reasons)

    def test_strong_match_reason(self):
        a = make_person(name="A")
        b = make_person(name="B", id="p002")
        result = evaluate_pair(a, b)
        assert result.summary_reasons == [
            "All hard and soft preferences match in both directions."
        ]
