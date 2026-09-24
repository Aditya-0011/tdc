# TDC Matcher

A small internal web tool for The Date Crew (TDC) matchmakers. It screens
and ranks candidate profiles against a client's explicitly stated
preferences **before** profiles are shared, so that candidates with known
hard-preference conflicts are caught up front. It is decision support —
the final matchmaking decision always stays with the human matchmaker.

## Problem being addressed

> Profiles are sometimes shared despite conflicting with preferences
> already known to the client. Around 35% of rejected profiles were
> rejected for reasons already mentioned in the client's preferences.

## Why this problem was selected

Of the issues in the assessment scenario, explicit-preference mismatch is
the one a small, deterministic tool can fix outright: the preferences are
already structured, already recorded, and a violation is a matter of
fact rather than judgment. Screening against them is pure rule-checking —
no compatibility modelling, no AI, no behavioural data required — yet it
directly attacks the ~35% avoidable-rejection baseline while making the
matchmaker faster (less manual profile screening) and leaving every
final decision with the human.

Given one selected person and the rest of the people pool, the tool:

1. Compares the selected person's preferences against each candidate's attributes.
2. Compares each candidate's preferences against the selected person's attributes.
3. Disqualifies any pair with a **hard** preference mismatch in either direction.
4. Ranks the remaining candidates using **soft** preference match counts.
5. Classifies each pair as `STRONG MATCH`, `POSSIBLE MATCH`, or `NOT SUITABLE`.
6. Explains every decision so the matchmaker can review and decide.

## How matching works

Matching is **bidirectional**. For a pair A/B the tool evaluates
`A.preferences -> B.attributes` and `B.preferences -> A.attributes`.
Each person's preference is evaluated using **that person's own
strictness** — strictness is never combined across people.

Classification per pair:

| Condition | Result |
|---|---|
| Any hard preference mismatch in either direction | `NOT SUITABLE` |
| No hard mismatch, every soft preference matches | `STRONG MATCH` |
| No hard mismatch, at least one soft mismatch | `POSSIBLE MATCH` |

- `hard` strictness is a dealbreaker: a mismatch disqualifies the pair.
- `soft` strictness never disqualifies; soft matches are counted only to
  rank candidates and flag where human judgment is needed.
- Soft scores are **preference-match counts, not compatibility scores**.
  `5 / 7 soft preferences matched` says nothing validated about long-term
  relationship success.
- There is deliberately **no arbitrary compatibility threshold**
  (e.g. "70% = match"). Hard constraints decide eligibility; soft matches
  rank; the matchmaker decides.

### Preference dimensions (fixed MVP set)

`age` (min/max range), `location` (city equality), `smoking` (exact),
`wants_children` (exact: `yes` / `no` / `maybe_future`), `relationship_goal`
(exact: `marriage` / `long_term` / `open`), `lifestyle` (exact: `quiet` /
`moderate` / `social`). Comparisons are intentionally simple: age is a
range check, location compares city, everything else is exact equality.

### Complexity

For one selected person the tool evaluates every other person once per
direction: `O(N * P)` where `N` is the pool size and `P` (6) is the number
of preference dimensions — effectively linear in the pool. No precomputed
`N x N` matrix is used.

## Data model

Everything lives in one file: `data/people.json`
(`{"people": [...]}`). Every person is both a TDC client and a potential
candidate — there is no separate role. Each person has `id`, `name`,
`attributes`, and `preferences`; every preference carries a value and a
`strictness` of `hard` or `soft`. See `data/template.json` for a
downloadable example (also available from the app's sidebar) and
`product.md` for the full specification.

In the UI, added or uploaded people live in the session only;
"Reset to sample data" restores the bundled file. There is no database
and no server-side persistence by design.

## Setup

Requires [uv](https://docs.astral.sh/uv/) (Python 3.11+).

```bash
uv sync
uv run streamlit run app.py
```

Then open http://localhost:8501.

## Tests

```bash
uv run pytest
```

The suite covers hard/soft behavior (match, mismatch, hard-override),
bidirectional evaluation (including asymmetric strictness), age range
boundaries, all three classifications, ranking order, data validation
(duplicate ids, missing fields, invalid enums/strictness, invalid age
ranges, malformed JSON), sample/template data integrity, JSON
round-tripping, and headless Streamlit app smoke tests via
`st.testing.v1.AppTest`.

Lint/type checks (run via `uvx`, not project dependencies):

```bash
uvx ruff check src tests app.py
uvx ty check src app.py
```

## Docker (optional)

A single-container `Dockerfile` is included for reproducibility. It runs
only the Streamlit app; there are no other services. The main development
workflow remains `uv`.

```bash
docker build -t tdc-matcher .
docker run -p 8501:8501 tdc-matcher
```

Then open http://localhost:8501. The image uses `python:3.11-slim` plus a
pinned uv binary, installs dependencies from the lockfile
(`uv sync --frozen`), and launches `streamlit run app.py` headless.

## Assumptions

- Preference data is complete for the six MVP dimensions; unknown or
  ambiguous preferences are out of scope (see future AI extension).
- Location matching is exact city equality — no radius, commute, or
  relocation willingness.
- All comparisons are deterministic; there is no randomness and no AI
  in the core matching logic.
- The 15-person sample dataset is fictional and hand-authored to
  demonstrate every result class; it does not represent real TDC clients.

## Limitations

- Fixed six preference dimensions; no custom preferences.
- Exact matching for categorical fields; no partial compatibility
  (e.g. `wants_children: yes` vs `maybe_future` is a mismatch).
- No historical learning, feedback loop, or production data.
- Soft match count is not a validated compatibility metric.
- Session-only persistence; no multi-user support; no authentication.
- The Docker image is single-purpose (Streamlit only) and not optimized
  for size.

## Future AI/Jev extension (not implemented)

Explicit hard constraints are handled deterministically because they are
structured, explainable, and should not depend on probabilistic output.
AI could later assist with ambiguous or qualitative inputs — extracting
structured rejection reasons from free-text feedback, interpreting
statements like "I can adjust a little", or summarizing soft-compatibility
trade-offs for the matchmaker. Its output would be a recommendation input
to the human, never an autonomous matchmaking decision. See `product.md`
§30 for details.
