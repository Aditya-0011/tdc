# TDC Product & Tech Generalist Assessment — Product Specification

## 1. Project Overview

Build a small internal web tool for The Date Crew (TDC) matchmakers.

The tool addresses one specific problem from the assessment scenario:

> Some profiles are being shared even though they conflict with preferences that the client has already explicitly stated.

The assessment states that around **35% of rejected profiles were rejected for reasons already mentioned in the client's preferences**. The prototype should therefore demonstrate a simple way for a matchmaker to screen and rank people before sharing profiles.

### Core product idea

Given one selected TDC client and the rest of the people in the TDC pool:

1. Compare the selected person's preferences against each candidate's attributes.
2. Compare each candidate's preferences against the selected person's attributes.
3. Treat **hard preference mismatches as disqualifying**.
4. Keep candidates with no hard mismatch.
5. Use **soft preference matches** only as a ranking/review signal.
6. Return one of three statuses:
   - `NOT SUITABLE`
   - `STRONG MATCH`
   - `POSSIBLE MATCH`
7. Explain the reasons behind the result so the human matchmaker can make the final decision.

The prototype is **decision support**, not an autonomous matchmaking system.

---

# 2. Assessment Context

The supplied scenario contains the following last-30-day funnel:

| Stage | Number |
|---|---:|
| Profiles shared | 1,000 |
| Profiles accepted | 310 |
| Contact details shared | 210 |
| Conversations started | 150 |
| Meetings fixed | 75 |
| Meetings completed | 42 |

Additional observations:

- Matchmaker A has a 44% profile acceptance rate.
- Matchmaker B has a 21% profile acceptance rate.
- Around 35% of rejected profiles were rejected for reasons already mentioned in client preferences.
- Matchmakers spend around 2 hours per client per week searching for profiles.
- Rejection feedback is mostly unstructured free-text.
- Some clients reject profiles initially but later accept profiles with very similar characteristics.

The prototype does **not** need to reproduce the entire matchmaking system. It should demonstrate one small, testable intervention against the explicit-preference mismatch problem.

---

# 3. Product Goal

## Primary goal

Reduce the number of profiles shared with clients that violate their explicitly stated preferences, while keeping the human matchmaker in control.

## Primary success metric

**Avoidable preference rejection rate**

Definition:

`rejected profiles caused by a mismatch with an already-known explicit preference / total rejected profiles`

Baseline supplied by the assessment: approximately **35%**.

The prototype should not claim a target improvement that is not supported by data. The assessment can state that the objective is to meaningfully reduce this baseline.

## Secondary metrics

1. **Profile acceptance rate**
   - Current aggregate baseline: `310 / 1000 = 31%`

2. **Matchmaker search time per client per week**
   - Current baseline: approximately 2 hours.

These metrics should be discussed in the written submission, but the prototype does not need real production measurement.

---

# 4. MVP Scope

## In scope

- One `people.json` file containing the entire TDC matching pool.
- Every person is a TDC client/member.
- When Person A is selected, every other person is a candidate.
- Fixed preference/attribute schema.
- Hard and soft preference strictness.
- Bidirectional preference evaluation.
- Deterministic matching logic.
- Human-readable explanations.
- Soft preference match count / percentage.
- Ranked results.
- Candidate detail view.
- Small sample dataset.
- Ability to add/edit a person through a simple web form.
- Ability to upload a JSON file using the documented schema.
- Ability to download the JSON schema/template.
- Ability to reset/load sample data.
- Basic automated tests for matching logic.
- Optional Docker container for easy reproducibility.

## Explicitly out of scope for MVP

Do not build:

- A production authentication system.
- A real CRM integration.
- Email sending.
- Email parsing.
- Real user accounts.
- PostgreSQL.
- Redis.
- Message queues.
- Microservices.
- gRPC.
- Kubernetes.
- Cloud infrastructure.
- Vector databases.
- Embedding search.
- Fine-tuning.
- An LLM-based autonomous matching agent.
- Gale-Shapley / Stable Marriage as the core algorithm.
- A scientifically validated psychological compatibility score.
- A claim that the numeric score predicts relationship success.
- Jev integration in the core MVP.

AI/Jev may be documented as a future extension, but should not be required for the deterministic MVP.

---

# 5. Product Principles

## 5.1 Human in the loop

The tool recommends and explains; the matchmaker decides.

`NOT SUITABLE` is used only for explicit hard conflicts.

`STRONG MATCH` and `POSSIBLE MATCH` are recommendations for review, not an autonomous final matchmaking decision.

## 5.2 Hard constraints are eligibility rules

A hard preference is effectively a dealbreaker.

If either person violates a hard preference of the other person, the pair is `NOT SUITABLE`.

A soft preference can never override a hard mismatch.

## 5.3 Soft preferences are ranking signals

A soft mismatch does not make a person ineligible.

Soft preferences are counted to help rank candidates and indicate where human judgment may be needed.

The prototype should not invent a scientifically meaningful compatibility percentage.

Prefer wording such as:

> `Soft preferences matched: 5 / 7`

or:

> `Soft preference match: 71%`

rather than:

> `Compatibility: 71%`

## 5.4 Explainability

Every decision should be explainable:

- Which hard preference failed?
- Which soft preferences matched?
- Which soft preferences did not match?
- Which direction produced the mismatch?

---

# 6. User

## Primary user

**TDC matchmaker**

The matchmaker uses the tool to quickly screen and review potential candidates for a selected client.

## Typical flow

1. Matchmaker selects a person.
2. Tool evaluates that person against everyone else in the pool.
3. Tool removes candidates with hard preference conflicts.
4. Tool ranks remaining people by soft preference matches.
5. Matchmaker opens candidate details.
6. Matchmaker makes the final human decision.

---

# 7. Data Model

Use a **single file**:

`data/people.json`

Do not split clients and candidates into separate files.

Every person has:

- `id`
- `name`
- `attributes`
- `preferences`

There is no `role` field in the MVP.

---

# 8. Fixed Preference Dimensions

Use exactly these six preference dimensions for the initial MVP:

1. `age`
2. `location`
3. `smoking`
4. `wants_children`
5. `relationship_goal`
6. `lifestyle`

This is intentionally small.

The purpose is to demonstrate the matching model, not to build a full matrimonial profile schema.

---

# 9. Attribute Definitions

Each person has the following attributes.

## Age

Type: integer

Example:

```json
"age": 29
```

## Location

Type: object

```json
"location": {
  "city": "Mumbai",
  "state": "Maharashtra",
  "country": "India"
}
```

## Smoking

Type: boolean

Allowed values:

- `true`
- `false`

## Wants children

Type: enum

Allowed values:

- `yes`
- `no`
- `maybe_future`

Meaning:

- `yes`: wants children.
- `no`: does not want children.
- `maybe_future`: could want children later / open to the possibility.

## Relationship goal

Type: enum

Allowed values:

- `marriage`
- `long_term`
- `open`

## Lifestyle

Type: enum

Allowed values:

- `quiet`
- `moderate`
- `social`

---

# 10. Preference Definitions

Every preference has a value and strictness.

Allowed strictness values:

- `hard`
- `soft`

`hard` means mismatch is disqualifying.

`soft` means mismatch is retained as a possible match and affects the soft-preference match count.

## Age preference

Age is a range:

```json
"age": {
  "min": 27,
  "max": 33,
  "strictness": "hard"
}
```

A candidate matches if:

`min <= candidate.age <= max`

## Location preference

MVP preference:

```json
"location": {
  "city": "Mumbai",
  "strictness": "soft"
}
```

For MVP, location matches when the candidate's city equals the preferred city.

Potential future enhancements such as radius, commute time, or relocation willingness are out of scope.

## Smoking preference

Example:

```json
"smoking": {
  "value": false,
  "strictness": "hard"
}
```

The candidate matches when:

`candidate.attributes.smoking == preference.value`

## Wants children preference

Example:

```json
"wants_children": {
  "value": "yes",
  "strictness": "soft"
}
```

For the MVP, comparison is exact equality:

`candidate.attributes.wants_children == preference.value`

A mismatch is a soft mismatch when the preference is soft.

Do not create hand-written partial compatibility scores in the core MVP.

## Relationship goal preference

Example:

```json
"relationship_goal": {
  "value": "marriage",
  "strictness": "hard"
}
```

Exact equality for MVP.

## Lifestyle preference

Example:

```json
"lifestyle": {
  "value": "moderate",
  "strictness": "soft"
}
```

Exact equality for MVP.

Future versions may introduce richer compatibility rules.

---

# 11. Canonical Person JSON Schema

Example:

```json
{
  "id": "p001",
  "name": "Aarav",
  "attributes": {
    "age": 29,
    "location": {
      "city": "Mumbai",
      "state": "Maharashtra",
      "country": "India"
    },
    "smoking": false,
    "wants_children": "yes",
    "relationship_goal": "marriage",
    "lifestyle": "moderate"
  },
  "preferences": {
    "age": {
      "min": 27,
      "max": 33,
      "strictness": "hard"
    },
    "location": {
      "city": "Mumbai",
      "strictness": "soft"
    },
    "smoking": {
      "value": false,
      "strictness": "hard"
    },
    "wants_children": {
      "value": "yes",
      "strictness": "soft"
    },
    "relationship_goal": {
      "value": "marriage",
      "strictness": "hard"
    },
    "lifestyle": {
      "value": "moderate",
      "strictness": "soft"
    }
  }
}
```

Top-level file:

```json
{
  "people": [
    {
      "...": "..."
    }
  ]
}
```

---

# 12. Matching Algorithm

## 12.1 High-level algorithm

For selected person `A`:

```text
for every person B where B.id != A.id:

    evaluate A's preferences against B's attributes
    evaluate B's preferences against A's attributes

    if any hard mismatch exists:
        status = NOT SUITABLE

    else:
        calculate soft preference match ratio

        if every soft preference matches:
            status = STRONG MATCH
        else:
            status = POSSIBLE MATCH
```

This is a pairwise evaluation.

For one selected person:

- `N` = number of people in the pool
- `P` = number of preference dimensions

Time complexity is:

`O(N * P)`

Since `P` is fixed and very small, this is effectively linear in the size of the candidate pool.

Do not precompute a global `N x N` score matrix for the MVP.

---

# 13. Directional Evaluation

Matching is bidirectional.

For a pair `A` and `B`, evaluate:

```text
A.preferences -> B.attributes
B.preferences -> A.attributes
```

Do not combine strictness values across people.

Each person's preference is evaluated according to **that person's own strictness**.

Example:

- A says smoking must be false and marks it `hard`.
- B smokes.

A's preference fails as a hard mismatch.

The fact that B may have a soft smoking preference is irrelevant to whether A's hard constraint is violated.

---

# 14. Preference Comparison Rules

Use a small generic evaluator plus attribute-specific comparison functions.

## Age

```text
match = min <= candidate_age <= max
```

## Location

```text
match = candidate.city == preferred.city
```

## Other enumerated/boolean fields

```text
match = preferred_value == candidate_attribute_value
```

This means the MVP does not attempt to infer nuanced human compatibility.

---

# 15. Result Aggregation

Each directional evaluation should return:

- `hard_mismatches`
- `soft_match_count`
- `soft_total`
- detailed explanations

Then combine both directions.

## NOT SUITABLE

If:

`A -> B` has at least one hard mismatch

OR

`B -> A` has at least one hard mismatch

then:

```text
NOT SUITABLE
```

Do not calculate or display a soft score as a reason to keep the pair.

## STRONG MATCH

If:

- no hard mismatches in either direction
- every soft preference checked in both directions matches

then:

```text
STRONG MATCH
```

Display:

`Soft preferences matched: X / X`

## POSSIBLE MATCH

If:

- no hard mismatch
- one or more soft preferences do not match

then:

```text
POSSIBLE MATCH
```

Display:

`Soft preferences matched: X / Y`

and:

`Human review required`

---

# 16. Ranking

For the selected person, sort results in this order:

1. `STRONG MATCH`
2. `POSSIBLE MATCH` with the highest soft-match ratio
3. lower-scoring `POSSIBLE MATCH`
4. `NOT SUITABLE`

Within the same status, higher soft-match ratio comes first.

`NOT SUITABLE` results may be shown in a separate section for transparency, or hidden by default with an option to inspect rejected candidates.

---

# 17. No Arbitrary Compatibility Threshold

Do not implement rules such as:

`70% = match`

or:

`below 70% = reject`

The supplied assessment data does not provide evidence for a scientifically or operationally validated threshold.

Instead:

- hard constraints determine eligibility;
- soft matches provide ranking;
- human matchmakers make the final decision.

A possible future version could learn/calibrate ranking thresholds from historical acceptance and meeting outcomes.

---

# 18. UI Requirements

Use a simple **web UI**.

Recommended framework:

**Streamlit**

Do not build a frontend/backend split.

## Main screen

The screen should contain:

### A. Selected person

Dropdown/selectbox populated from `people.json`.

Example:

`Client: [Aarav ▼]`

### B. Candidate results

Display cards or a table containing:

- candidate name
- status
- soft preferences matched
- key reason(s)

Example:

```text
Isha
POSSIBLE MATCH
5 / 7 soft preferences matched
Human review required
```

### C. Candidate details

When a candidate is selected, show:

```text
Aarav ↔ Isha

Result: POSSIBLE MATCH

Aarav → Isha
✓ Age
✓ Smoking
✓ Relationship goal
✓ Lifestyle
⚠ Wants children
...

Isha → Aarav
✓ Age
✓ Smoking
...
```

Each mismatch should explain the exact preference and candidate attribute where possible.

### D. Data management

Provide:

- `Load sample data`
- `Download JSON template`
- `Upload JSON`
- `Add person`
- `Reset to sample data`

Do not require manual editing of raw JSON just to demo the product.

---

# 19. Add Person Form

Provide a simple form with:

## Basic attributes

- Name
- Age
- City
- State
- Country
- Smoking
- Wants children
- Relationship goal
- Lifestyle

## Preferences

- Age minimum
- Age maximum
- Preferred city
- Smoking preference
- Wants children preference
- Relationship goal preference
- Lifestyle preference

For each preference:

- value
- strictness (`hard` / `soft`)

Validation should reject unsupported enum values and invalid age ranges.

---

# 20. JSON Upload

Allow upload of a single JSON file in the canonical structure:

```json
{
  "people": [...]
}
```

The upload can contain multiple people.

Do not require separate files for clients and candidates.

Validate:

- top-level `people` exists
- each person has an `id`
- IDs are unique
- `name` is present
- required attributes exist
- required preferences exist
- enum values are valid
- age is valid
- preference age range is valid
- strictness is `hard` or `soft`

Show useful validation errors rather than crashing.

---

# 21. JSON Template Download

Provide a downloadable template containing one example person and clear structure.

The template should be valid JSON.

Do not include comments inside JSON.

A human-readable README can explain the fields.

---

# 22. Sample Dataset Requirements

Provide enough mock data to make the prototype visibly useful.

Recommended:

- 5–10 people for the first demo.
- Ideally 15–25 people if generating data is easy.

The sample data should intentionally contain:

- at least one strong match
- multiple possible matches
- at least one hard mismatch
- candidates with different soft-match counts
- a non-binary `wants_children` example
- at least one pair where the mismatch is caused by the other person's preference
- at least one candidate rejected because of a hard preference even though many other attributes match

Do not claim the generated data represents real TDC behaviour.

---

# 23. Example Match Scenarios

## Scenario A — Strong Match

A's hard preferences all match B.

B's hard preferences all match A.

All soft preferences match in both directions.

Result:

`STRONG MATCH`

## Scenario B — Possible Match

No hard mismatch.

Some soft preferences differ.

Result:

`POSSIBLE MATCH`

Example:

```text
Soft preferences matched: 4 / 6
```

## Scenario C — Not Suitable

A has:

```text
smoking = false
strictness = hard
```

B has:

```text
smoking = true
```

Result:

`NOT SUITABLE`

Reason:

`A's hard smoking preference is violated.`

## Scenario D — Asymmetric preference

A has:

```text
location = Mumbai
strictness = hard
```

B lives in Pune.

Even if B is flexible about location, the pair is still:

`NOT SUITABLE`

because A's hard preference is violated.

---

# 24. Code Organization

Keep the code small and modular.

Suggested structure:

```text
tdc-matcher/
├── app.py
├── pyproject.toml
├── README.md
├── Dockerfile
├── data/
│   ├── people.json
│   └── template.json
├── src/
│   └── tdc_matcher/
│       ├── __init__.py
│       ├── models.py
│       ├── matcher.py
│       ├── validators.py
│       └── data.py
├── tests/
│   ├── test_matcher.py
│   ├── test_validators.py
│   └── test_data.py
├── product.md
└── summary.md
```

Do not create a package hierarchy larger than necessary.

---

# 25. Technical Requirements

## Python

Use a modern supported Python version compatible with the project dependencies.

## Package management

**Use `uv` only.**

Do not use:

- `pip`
- `pip3`
- Poetry
- Pipenv
- Conda
- manually managed virtual environments

Preferred workflow:

```bash
uv init
uv add streamlit
uv add --dev pytest
uv run streamlit run app.py
uv run pytest
```

Use `uv sync` as appropriate for reproducibility.

All dependency changes should be reflected in `pyproject.toml` and the `uv.lock` file.

Do not install packages globally.

---

# 26. Testing Requirements

At minimum, cover:

## Hard preference

- hard exact match
- hard exact mismatch
- hard mismatch overrides all soft matches

## Soft preference

- soft exact match
- soft mismatch remains eligible

## Bidirectional matching

- A accepts B but B hard-rejects A
- both directions pass
- different strictness between A and B

## Age range

- exactly minimum
- exactly maximum
- below minimum
- above maximum

## Result classification

- all hard + all soft match → `STRONG MATCH`
- no hard mismatch + soft mismatch → `POSSIBLE MATCH`
- any hard mismatch → `NOT SUITABLE`

## Data validation

- duplicate IDs
- missing attribute
- invalid enum
- invalid strictness
- invalid age range
- malformed JSON

---

# 27. Error Handling

The app should:

- show a clear validation error when JSON is invalid;
- refuse malformed data gracefully;
- never silently skip required preferences;
- avoid Python tracebacks in normal user-facing flows;
- handle empty candidate pools;
- handle a person with no other people in the pool.

---

# 28. Accessibility / UX

Do not optimize for visual polish.

Prioritize:

- readable result labels
- clear mismatch reasons
- simple navigation
- low cognitive load
- obvious distinction between hard and soft
- clear `Human review required` messaging

Do not spend significant time on animations, branding, or decorative design.

---

# 29. Docker

Containerization is optional but recommended as a small finishing step.

Use a **single container**.

The container only needs to run Streamlit.

Do not add multiple services or compose files unless genuinely necessary.

The README should include the commands to build and run the container.

The main development workflow must still use `uv`.

---

# 30. AI / Jev Position

Do not integrate Jev into the core MVP.

The written submission may describe a future extension:

> Explicit hard constraints are handled deterministically because they are structured, explainable, and should not depend on probabilistic model output. AI could later assist with ambiguous or qualitative inputs such as free-text rejection feedback, lifestyle descriptions, or nuanced preferences. The output should be treated as a recommendation/input to the matchmaker rather than an autonomous decision.

Potential future use cases:

- extract structured rejection reasons from free-text;
- identify latent preference signals;
- interpret nuanced statements such as "I can adjust a little";
- help the matchmaker review soft compatibility.

The current prototype should not pretend that AI can objectively determine romantic compatibility.

---

# 31. Stable Marriage / Matching Algorithms

The classic Stable Marriage / Gale-Shapley algorithm should not be used in the MVP.

Reason:

- the prototype does not have complete ranked preference lists;
- preferences are incomplete and partially qualitative;
- the system is human-assisted;
- the immediate problem is avoidable preference mismatch, not globally stable allocation.

A future system could investigate two-sided matching algorithms after reliable preference and behavioural data exists.

This can be mentioned in the design document as a future direction.

---

# 32. Product Boundaries

The system is not intended to answer:

> "Are these two people actually compatible?"

It answers:

> "Based on the structured preferences we currently have, should this candidate be excluded, surfaced as a strong match, or surfaced for human review?"

This distinction must remain clear in the UI, README, and written submission.

---

# 33. Implementation Plan

## Phase 1 — Data and core matching

1. Initialize project with `uv`.
2. Define typed models.
3. Create `people.json`.
4. Implement validators.
5. Implement individual preference comparisons.
6. Implement directional evaluation.
7. Implement pair evaluation.
8. Implement selected-person candidate search.
9. Add tests.

## Phase 2 — UI

1. Build Streamlit app.
2. Load sample data.
3. Add person selector.
4. Display candidate ranking.
5. Display candidate detail/reasons.
6. Add data upload.
7. Add JSON template download.
8. Add person creation form.

## Phase 3 — Polish

1. Improve error messages.
2. Add sample-data reset.
3. Add README.
4. Add Dockerfile.
5. Run full test suite.
6. Manually verify all three result classes.

## Phase 4 — Assessment documentation

Update:

- `product.md` only when requirements/design materially change.
- `summary.md` after each implementation milestone.

---

# 34. Acceptance Criteria

The MVP is complete when all of the following are true:

### Data

- [ ] One `data/people.json` contains the whole matching pool.
- [ ] Every person uses the same schema.
- [ ] Sample data covers strong/possible/not-suitable cases.

### Matching

- [ ] A selected person is never matched with themselves.
- [ ] Matching is bidirectional.
- [ ] Hard mismatch in either direction produces `NOT SUITABLE`.
- [ ] No hard mismatch + all soft matches produces `STRONG MATCH`.
- [ ] No hard mismatch + any soft mismatch produces `POSSIBLE MATCH`.
- [ ] Soft match counts/ratio are displayed for eligible results.
- [ ] Decisions are explainable.

### UI

- [ ] User can select a person.
- [ ] User can see ranked candidates.
- [ ] User can inspect reasons.
- [ ] User can add a person.
- [ ] User can upload valid JSON.
- [ ] User can download the JSON template.
- [ ] User can restore sample data.

### Engineering

- [ ] Dependencies managed with `uv`.
- [ ] App runs with `uv run`.
- [ ] Tests run with `uv run pytest`.
- [ ] Core matcher tests pass.
- [ ] Invalid data is handled gracefully.
- [ ] No unnecessary external services.

### Documentation

- [ ] README explains purpose and local setup.
- [ ] README explains the matching logic.
- [ ] README explains assumptions and limitations.
- [ ] README mentions that soft scoring is only a preference-match signal.
- [ ] README explains future AI/Jev use without making it part of the MVP.
- [ ] `summary.md` accurately records implementation work.

---

# 35. Important Implementation Guardrails

The implementation agent must follow these constraints:

1. **Do not add features that are not needed for the assessment.**
2. **Do not introduce a database when JSON is sufficient.**
3. **Do not introduce an API/backend service when Streamlit can directly run the logic.**
4. **Do not introduce AI merely to claim AI usage.**
5. **Do not create a compatibility score that looks scientifically validated.**
6. **Do not turn soft mismatch into automatic rejection.**
7. **Do not let a soft preference override a hard mismatch.**
8. **Do not treat the matchmaker as replaceable.**
9. **Prefer transparent deterministic code over clever abstractions.**
10. **Use `uv` for all Python environment/dependency operations.**

The desired implementation should be easy to understand in one sitting by another engineer.
