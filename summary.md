# TDC Matcher — Implementation Summary & Work Log

## 1. Purpose

This file is the implementation log for the TDC Product & Tech Generalist Assessment prototype.

The implementation agent must keep this file updated as work progresses.

The log should record **what was actually done**, not what was planned.

Do not fabricate completed work.

---

# 2. Project Goal

Build a small internal web tool for TDC matchmakers that:

1. takes one selected person from the TDC people pool;
2. evaluates every other person as a potential candidate;
3. checks preferences in both directions;
4. rejects pairs with any hard preference mismatch;
5. ranks remaining pairs using simple soft-preference match counts;
6. explains the reasons;
7. keeps the final matchmaking decision with the human matchmaker.

Primary problem being addressed:

> Profiles are sometimes being shared despite conflicting with preferences already known to the client.

Assessment-provided signal:

> Around 35% of rejected profiles were rejected for reasons already mentioned in the client's preferences.

---

# 3. Current Status

**Status:** Ready for submission.

Core engine, validation, data, tests, Streamlit UI, documentation, and a
single-container Docker image are done, reviewed against `product.md`,
and verified.

---

# 4. Fixed MVP Decisions

These decisions were made before implementation and should not be changed casually.

## Data

- One `data/people.json` file.
- Every person is both a TDC client and a potential candidate.
- No separate client/candidate role.
- No SQLite/PostgreSQL for MVP.

## Preference dimensions

The initial MVP uses exactly:

1. `age`
2. `location`
3. `smoking`
4. `wants_children`
5. `relationship_goal`
6. `lifestyle`

## Strictness

Only:

- `hard`
- `soft`

## Result states

- `NOT SUITABLE`
- `STRONG MATCH`
- `POSSIBLE MATCH`

## Matching model

For each pair:

```text
A preferences -> B attributes
B preferences -> A attributes
```

Any hard mismatch in either direction:

`NOT SUITABLE`

No hard mismatch and every soft preference matches:

`STRONG MATCH`

No hard mismatch and at least one soft mismatch:

`POSSIBLE MATCH`

## Soft scoring

Soft score is only a count/ratio of matched soft preferences.

Do not claim it is a scientifically meaningful compatibility score.

## AI

No Jev/LLM in the core MVP.

Document AI/Jev as a future extension for ambiguous qualitative information and free-text feedback.

## UI

Use Streamlit.

## Package management

Use `uv` only.

No pip/Poetry/Pipenv/Conda.

---

# 5. Planned Repository Structure

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

The structure may be simplified if implementation does not need every file.

---

# 6. Implementation Log

Keep entries chronological.

Do not rewrite old entries unless correcting an objective factual error.

## 2026-09-24 — Milestone 1: Project initialization

### Done
- Renamed placeholder package `src/tdc/` to `src/tdc_matcher/` (spec §24 structure).
- Removed the uv-generated `main()` placeholder.
- Added pytest as a dev dependency via `uv add --dev pytest` (recorded as a `[dependency-groups]` dev group in `pyproject.toml`).
- Updated `pyproject.toml` name to `tdc-matcher`.

### Files changed
- `pyproject.toml` — name, dev dependency group, removed placeholder script.
- `src/tdc_matcher/__init__.py` — replaced placeholder with package docstring.

### Verification
- `uv sync` — resolves and builds `tdc-matcher` 0.1.0 successfully.
- `uv run pytest --collect-only -q` — runs (no tests yet at that point).
- `uv run python -c "import streamlit, tdc_matcher"` — streamlit 1.64.0 imports OK.

### Decisions / Notes
- Python 3.11 (per `.python-version`), uv 0.12.18 on Windows.
- No Docker in this build (user decision); the main workflow stays `uv run`.

### Next
- Data model and sample data.

## 2026-09-24 — Milestone 2: Data model + sample data

### Done
- Defined typed dataclasses in `models.py`: `Person`, `Attributes`, `Location`, `Preferences`, `AgePreference`, `LocationPreference`, generic `ValuePreference`, and enums `Strictness`, `WantsChildren` (incl. `maybe_future`), `RelationshipGoal`, `Lifestyle`, `MatchStatus`.
- Created hand-authored sample pool `data/people.json` with 15 people.
- Created `data/template.json` with one valid example person.

### Files changed
- `src/tdc_matcher/models.py` — new.
- `data/people.json` — new.
- `data/template.json` — new.

### Verification
- Covered later by `tests/test_data.py` (all 58 tests pass, including sample/template validity and scenario coverage).

### Decisions / Notes
- All 15 sample people are hand-authored (not generated programmatically). Data is fictional; no claim it represents real TDC clients.
- Intentional edge cases: Aarav↔Priya is a STRONG MATCH; possible matches with different soft ratios for Aarav (Isha 5/6, Rohan 5/6, Neha 4/6, Aditi 3/6, Naina 3/7); hard mismatches via smoking (Kabir), age (Ananya/Vikram), goal (Meera/Tara), location with asymmetric strictness (Dev, Arjun); `maybe_future` attributes (Ananya, Meera, Aditi) and preferences (Naina, Aditi, Vikram).
- Aarav (p001) vs Dev (p011): only Dev's hard location preference fails — demonstrates that a soft preference can never override a hard mismatch and that strictness is per-person.

### Next
- Validators and data loading.

## 2026-09-24 — Milestone 3: Validation + data loading

### Done
- `validators.py`: validates top-level `people` list, unique non-empty `id`, non-empty `name`, attributes (age int 18–99, location city/state/country, smoking bool, enums), preferences (age range with min<=max and bounds, per-dimension value + strictness `hard`/`soft`).
- Validation collects all errors as actionable strings (`people[i] (id='...'): ...`) instead of raising, so the UI can show every problem in an uploaded file at once.
- `parse_people()` builds typed `Person` objects only from validated dicts.
- `data.py`: `load_people_from_file` / `load_sample_people` (JSON + FileNotFoundError + JSONDecodeError handled with messages), `read_template_text`, `people_to_json` round-trip serialization.

### Files changed
- `src/tdc_matcher/validators.py` — new.
- `src/tdc_matcher/data.py` — new.

### Verification
- `uv run pytest -q` — 58 passed (validators: ~25 cases incl. duplicate ids, invalid enums, invalid strictness, min>max, malformed JSON).

### Decisions / Notes
- `bool` is excluded when validating integer fields (Python `bool` is an `int` subclass).
- Person edits made in the UI live in session state only; "reset" restores the sample file. No persistence beyond the bundled JSON (documented as an MVP limitation).

### Next
- Core matcher.

## 2026-09-24 — Milestone 4: Core matcher

### Done
- `evaluate(preferences, candidate)` — directional evaluation returning one `DimensionCheck` per dimension (matched, strictness, human-readable preference/attribute descriptions).
- `evaluate_pair(A, B)` — both directions; classification: any hard mismatch -> `NOT SUITABLE`; all soft match -> `STRONG MATCH`; else `POSSIBLE MATCH`.
- `find_matches(A, people)` — excludes A by id, ranks STRONG -> POSSIBLE (soft ratio desc) -> NOT SUITABLE, name as deterministic tie-break.
- `PairResult.summary_reasons` — explainability: which hard preference failed and whose, or which soft preferences need human review.

### Files changed
- `src/tdc_matcher/matcher.py` — new.

### Verification
- `uv run pytest -q` — 58 passed (hard/soft, bidirectional, asymmetric strictness, age boundaries, classifications, ranking, explanations).

### Decisions / Notes
- Strictness is never combined across people: each direction is evaluated with its own strictness (spec §13).
- Fixed six dimensions, generic evaluator + per-dimension comparison functions (spec §14): age range, city equality, exact equality for the rest.
- Complexity O(N*P) for one selected person; no precomputed NxN matrix.

### Next
- Streamlit UI.

## 2026-09-24 — Milestone 5: Tests

### Done
- `tests/conftest.py` — `make_person`/`make_person_dict` factory.
- `tests/test_matcher.py` — hard match/mismatch, hard-override, soft counting, soft mismatch eligibility, bidirectional (A accepts / B rejects, both pass, asymmetric strictness hard and soft), age boundaries (min/max/below/above), classifications, ranking order, self-exclusion, empty pool, explanation texts.
- `tests/test_validators.py` — top-level structure, ids (missing/duplicate), attributes (missing/age/location/smoking/enums), preferences (age range, bounds, strictness, enums, missing dimension), parse behavior, multi-error collection.
- `tests/test_data.py` — sample file validity + 15 people + all three statuses for Aarav + `maybe_future` presence + asymmetric case assertions, template validity, missing/malformed/invalid files, JSON round-trip.

### Files changed
- `tests/conftest.py`, `tests/test_matcher.py`, `tests/test_validators.py`, `tests/test_data.py` — new.

### Verification
- `uv run pytest -q` — 58 passed.
- `uvx ruff check src tests` — clean; `uvx ty check src` — clean.

### Decisions / Notes
- One initial test failure was a factory keyword typo (`pref_goal` vs `pref_relationship_goal`), fixed immediately.

### Next
- Streamlit UI (app.py).

## 2026-09-24 — Milestone 6: Streamlit UI

### Done
- `app.py` single-file Streamlit app following the Streamlit skill best practices (native widgets only, no custom CSS, `st.form` for the add-person flow, session-state pool, bordered containers, Material Symbols icons, sentence casing).
- Main screen: client selectbox (15 people), summary line ("X of Y candidates clear all hard preferences"), ranked candidate cards with status badge, soft matched X/Y, and bullet reasons.
- Candidate detail expander per card: both directions rendered as `A → B` check lists with icons for match / hard mismatch / soft mismatch, showing the exact preference and attribute values.
- `NOT SUITABLE` results hidden by default behind a "Show not-suitable candidates" checkbox (spec §16 transparency option).
- Sidebar data management: download JSON template, upload JSON (full validation, all errors listed, replaces pool), reset to sample data, download current pool.
- Add-person form: all attributes + preferences with per-preference strictness (segmented controls), auto-generated unique id, server-side validation with messages (widget constraints are not trusted as a boundary).
- Empty/error states: no data, single-person pool, invalid/malformed upload — all via `st.info`/`st.error`, no tracebacks.

### Files changed
- `app.py` — new.

### Verification
- Headless `st.testing.v1.AppTest` smoke tests added in `tests/test_app.py` (app renders, ranked results, rejected shown/hidden, form validation + valid submit).
- Real server smoke: `uv run streamlit run app.py` → `http://localhost:8501/_stcore/health` returned `ok`, then stopped.

### Decisions / Notes
- UI edits (add person, upload) mutate a session-state copy of the pool; the bundled `data/people.json` is never modified at runtime. "Reset to sample data" restores from the file.
- `NOT SUITABLE` candidates still get a card with the failing hard preferences listed when the checkbox is enabled — transparency for the matchmaker.
- Status colors via native colored markdown (`:green[...]` etc.) — no CSS injection.

### Next
- README, docs, final verification.

## 2026-09-24 — Milestone 7: Documentation + final verification

### Done
- README: purpose, problem, matching algorithm, complexity, data model, setup, tests, assumptions, limitations, AI/Jev as future extension only.

### Files changed
- `README.md` — written from scratch.

### Verification
- `uv run pytest` — 69 passed.
- `uvx ruff check src tests app.py` + `uvx ruff format` — clean.
- `uvx ty check src app.py` — clean.
- `uv run streamlit run app.py` — health endpoint ok.

### Decisions / Notes
- Docker intentionally skipped (user decision at planning). README documents this.

### Next
- Assessment-level written answers and submission materials (out of scope for this implementation log).

## 2026-09-24 — Final engineering/product review

### Reviewed
- All sources (`models.py`, `validators.py`, `data.py`, `matcher.py`, `app.py`), all tests, `data/people.json`, `data/template.json`, `README.md` against `product.md` (source of truth).
- Matching semantics: bidirectional evaluation, self-exclusion, hard-override, soft non-disqualification, classification, ranking, explainability, no arbitrary threshold, no partial compatibility scores.
- Edge cases A–H from the review brief against the test suite.
- Architecture for overengineering (JSON -> Python matcher -> Streamlit UI confirmed; no DB/API/AI/extra infra).
- UI requirements §18 of product.md; data management; code quality (dead code, duplication, hard-coded sample logic — none found in the matcher); complexity O(N*P), no precomputed NxN matrix.
- README coverage of the required topics; AI/Jev positioning.

### Problems found
- Dead code: `DimensionCheck.reason` property and `PairResult.selected` field were never read anywhere.
- Two review edge cases had no direct tests: Case F complement (asymmetric strictness where the hard preference passes — each side's strictness evaluated independently), and Case H (`maybe_future` wants_children exact-equality behavior in the matcher).
- Objective factual error in the Milestone 2 log entry (leftover editorial text "wait — see test output") — corrected.
- §12 upload-coverage wording implied AppTest covered the upload handler; AppTest cannot simulate `st.file_uploader` — wording corrected.
- README lacked the "why this problem was selected" rationale.
- One confusing self-questioning comment in `test_asymmetric_strictness_hard_rejects` and one convoluted assertion in the same test.

### Fixes made
- Removed `DimensionCheck.reason` and `PairResult.selected` (matcher.py).
- Added 4 tests in `test_matcher.py`: asymmetric strictness with hard preference passing (per-owner strictness verified via check metadata), maybe_future vs maybe_future match, maybe_future vs yes soft mismatch, hard wants_children mismatch disqualifies.
- Cleaned up the confusing comment/assertion in `test_asymmetric_strictness_hard_rejects` (now asserts `b_to_a.hard_mismatches == []` — the soft side never disqualifies).
- Corrected the Milestone 2 log entry and the §12 upload wording in this file; updated §3/§12/§16 to reflect the reviewed state.
- Added "Why this problem was selected" section to `README.md`.

### Files changed
- `src/tdc_matcher/matcher.py` — dead code removal.
- `tests/test_matcher.py` — 4 new tests, comment/assertion cleanup.
- `README.md` — why-selected rationale section.
- `summary.md` — factual corrections, this review entry, status update.

### Verification
- `uv run pytest` — 69 passed (62 core/data + 7 headless app tests).
- `uvx ruff check src tests app.py` — clean; `uvx ruff format --check` — clean.
- `uvx ty check src app.py` — clean.
- Real server smoke: `uv run streamlit run app.py` → `/_stcore/health` returned `ok`, main page HTTP 200. (The static HTML shell title is "Stream"; `st.set_page_config` applies the browser tab title at runtime.)

### Decisions / Notes
- No product.md inconsistencies found — implementation matches the spec; no scope changes.
- No new features added during review; only dead-code removal, test additions, and documentation corrections.
- File-uploader widget interaction remains un-browser-automated (AppTest limitation, documented in §15); its logic is covered by validator/data tests.

### Next
- Stop — acceptance criteria satisfied.

## 2026-09-24 — Final repository hygiene check

### Checked
- Repository state: untracked file inventory (no temp/debug files, no test artifacts intended for submission; caches are local only and ignored), secrets/credentials/local-path scan of all sources, tests, docs, and config files (none found; only legitimate `localhost:8501` documentation references), file sizes (largest is `uv.lock` at ~280 KB — a normal lockfile; sample data ~11 KB), unused dependencies (`uv tree` shows only `streamlit` + dev `pytest`, both used), dead source files (none — all modules imported and exercised).
- Metadata: package name `tdc-matcher`, module `tdc_matcher` imports cleanly (`uv run python -c "import tdc_matcher..."`), `pyproject.toml` consistent with the actual structure, `uv.lock` present and resolving (`uv sync` clean), README commands match the project, Docker documented as skipped (not required), AI/Jev documented as future-only everywhere.
- `.gitignore`: covered `__pycache__`/build/`.venv` but did not explicitly list standard tool caches or Streamlit secrets.
- README fact-check against the implementation: six fixed dimensions, bidirectional evaluation, hard/soft strictness, no arbitrary threshold, soft counts as preference-match counts (not compatibility predictions), human final decision-maker, session-only JSON behavior, AI/Jev as future work — all accurate.
- Visible demo behavior via `st.testing.v1.AppTest` with Aarav selected: `STRONG MATCH` (Priya, soft 4/4) and `POSSIBLE MATCH` visible; `NOT SUITABLE` hidden by default and visible after the checkbox; detail view renders both directions (`Aarav → Priya` and `Priya → Aarav`).

### Fixes made
- `.gitignore` — added `.pytest_cache/`, `.ruff_cache/`, and `.streamlit/secrets.toml` (these caches were previously only self-ignoring; secrets guard is preventive). No source-code changes.

### Commands and results
- `uv run pytest` — 69 passed.
- `uvx ruff check src tests app.py` — All checks passed.
- `uvx ruff format --check src tests app.py` — 11 files already formatted.
- `uvx ty check src app.py` — All checks passed.
- `uv run streamlit run app.py` — launched; `/_stcore/health` returned `ok`; stopped.
- AppTest demo verification — STRONG/POSSIBLE visible, NOT SUITABLE toggle works, both detail directions rendered.

### Notes
- `opencode.json`, `skills-lock.json`, and `.agents/` are local agent-tooling configuration that predates the implementation; kept as-is (no secrets inside — verified).
- Nothing has been committed to git yet; all project files are staged-untracked and ready for an initial commit by the owner.

### Final submission status
Ready for submission. Acceptance criteria in `product.md` §34 are satisfied; no known issues remain within MVP scope beyond the documented limitations (§15).

## 2026-09-25 — Milestone 8: Docker containerization

### Done
- Added single-container `Dockerfile` (python:3.11-slim + pinned uv 0.12.18; deps from lockfile; headless Streamlit on 0.0.0.0:8501).
- Added `.dockerignore` (excludes .venv, .git, caches, tests, local tooling; keeps runtime `data/`).
- Updated `README.md` with an optional Docker section (build/run commands) and adjusted the Limitations wording.
- Updated §10 Docker Log, §14 change log, and §16 submission readiness in this file.

### Files changed
- `Dockerfile` — new.
- `.dockerignore` — new.
- `README.md` — Docker section + limitation wording.
- `summary.md` — this entry, §10, §14, §16.

### Verification
- `docker build -t tdc-matcher .` — succeeded.
- `docker run -p 8502:8501 tdc-matcher` — `/_stcore/health` returned `ok`; main page HTTP 200.
- In-container app check — 15 people loaded, no validation errors, matching produced all three statuses.
- Container removed after verification; image kept locally as `tdc-matcher:latest` (764 MB).
- `uv run pytest` — 69 passed (unchanged; no source changes).

### Decisions / Notes
- User reversed the earlier "skip Docker" planning decision; everything else stays per plan — no features, no matching changes.
- No commit made (repository owner's decision, unchanged).

### Next
- Stop.

## 2026-09-25 — Sidebar action feedback

### Done
- Added a sidebar status message mechanism: sidebar actions queue a message in session state and it renders (as `st.success`/`st.error` with icons) at the top of the sidebar on the rerun the action triggers, so the user sees confirmation that the action happened. The message is consumed on the next rerun (standard flash-message behavior).
- Applied to: "Reset to sample data" (previously gave no feedback at all — success with people count, or error if sample data fails to load), "Add person" success (now "Added <name> (<id>)." persisting visibly), and JSON upload success (now "Loaded N people from <filename>.").
- Upload validation/JSON errors and add-person form validation errors already rendered immediate `st.error` messages; unchanged.
- Replaced the previous `st.toast` calls (which flash briefly during the rerun) with the persistent status messages.

### Files changed
- `app.py` — `show_status()`/`render_status()` helpers; reset/upload/add-person flows now queue feedback.
- `tests/test_app.py` — 3 new tests (add-person shows status, status clears on next interaction, reset shows status and restores the pool).

### Verification
- `uv run pytest` — 72 passed.
- `uvx ruff check` / `uvx ruff format` — clean; `uvx ty check app.py` — clean.
- `uv run streamlit run app.py` — health `ok` (started and stopped after check).

### Decisions / Notes
- Feedback shows in the sidebar (where the actions live) rather than toasts: toasts were easy to miss because the action triggers an immediate rerun.
- No new features beyond the confirmation messages; no matching/data changes.

### Next
- Stop.

---

# 7. Milestone Checklist

## Milestone 1 — Project initialization

- [x] Initialize Python project with `uv`.
- [x] Add Streamlit with `uv`.
- [x] Add pytest as a development dependency with `uv`.
- [x] Create project structure.
- [x] Confirm application can be launched with `uv run`.
- [x] Confirm tests can be launched with `uv run pytest`.

Python 3.11 (`requires-python >=3.11`), uv 0.12.18, streamlit 1.64.0,
pytest 9.1.1 (dev group). Verified via `uv sync`, `uv run pytest`,
and a real `uv run streamlit run app.py` health check.

---

## Milestone 2 — Data model

- [x] Define person structure.
- [x] Define attributes.
- [x] Define preferences.
- [x] Define strictness.
- [x] Define enum validation.
- [x] Create sample `people.json`.
- [x] Create JSON template.

---

## Milestone 3 — Validation

- [x] Validate top-level `people`.
- [x] Validate required fields.
- [x] Validate unique IDs.
- [x] Validate age.
- [x] Validate age ranges.
- [x] Validate location structure.
- [x] Validate enum values.
- [x] Validate `hard` / `soft`.
- [x] Produce actionable error messages.

Verified with valid and invalid examples in `tests/test_validators.py`.

---

## Milestone 4 — Core matcher

- [x] `evaluate(preferences, attributes)` — hard mismatches, soft match
      count, soft total, per-dimension detail records.
- [x] `evaluate_pair(A, B)` — both directions, aggregated.
- [x] `find_matches(A, people)` — self excluded, every other person
      evaluated, results sorted.

---

## Milestone 5 — Tests

### Hard

- [x] exact match
- [x] mismatch
- [x] hard mismatch wins over all soft matches

### Soft

- [x] match counted
- [x] mismatch counted but does not disqualify

### Bidirectional

- [x] A accepts B, B rejects A hard
- [x] both directions pass hard constraints
- [x] asymmetric strictness behaves correctly

### Age

- [x] minimum boundary
- [x] maximum boundary
- [x] below minimum
- [x] above maximum

### Classification

- [x] strong match
- [x] possible match
- [x] not suitable

### Data

- [x] invalid JSON
- [x] duplicate IDs
- [x] missing data
- [x] invalid enum
- [x] invalid strictness

`uv run pytest` — 65 passed (58 core/data + 7 headless app tests)..

---

# 8. UI Implementation Log

- [x] selected-person flow — sidebar-less main selectbox over all people, session-state pool;
- [x] candidate ranking view — bordered cards in ranked order with summary line;
- [x] candidate details — per-direction check lists in an expander;
- [x] reasons/explanations — hard violations or soft mismatches with exact values;
- [x] add-person form — st.form with strictness controls + server-side validation;
- [x] JSON upload — file_uploader with full validation, replaces pool;
- [x] JSON template download — sidebar download_button;
- [x] sample-data reset — button reloads the bundled file;
- [x] empty/error states — empty pool, single-person pool, upload errors;
- [x] sidebar action feedback — reset/add-person/upload show a persistent status message confirming the action (added 2026-09-25);
- [x] bonus: download current pool as JSON.

The UI remains intentionally simple (native widgets only).

---

# 9. Data Generation Log

- 15 people, all hand-authored (no programmatic generation).
- Indian metro cities; fictional names; not representative of real TDC clients.
- Intentional edge cases:
  - strong match: Aarav ↔ Priya (4/4 soft in both directions);
  - possible matches with different soft ratios: Isha 5/6, Rohan 5/6, Neha 4/6, Aditi 3/6, Naina 3/7 (for Aarav);
  - hard mismatch by smoking: Kabir (Aarav's hard non-smoker preference);
  - hard mismatch by age: Ananya (26 < Aarav's min 27), Vikram (35 > max 33);
  - hard mismatch by relationship goal: Meera (long_term), Tara (open);
  - asymmetric strictness: Dev/Arjun hard on their city while Aarav is soft — Aarav/Dev is NOT SUITABLE purely from Dev's direction;
  - rejected despite everything else matching: Arjun vs Neha fails only on Arjun's hard Delhi preference;
  - non-binary `wants_children`: attributes (Ananya, Meera, Aditi) and preferences (Naina, Aditi, Vikram);
  - boundary ages: Kabir (33) exactly at Aarav's max; Tara (24) at her own pref min.
- Verified by `tests/test_data.py` (all three statuses for Aarav, `maybe_future` presence, asymmetric case).

---

# 10. Docker Log

## 2026-09-24 — Container added (user requested after initially skipping)

- Base image: `python:3.11-slim`, with the uv 0.12.18 binary copied from
  `ghcr.io/astral-sh/uv:0.12.18` (pinned to the version that generated
  `uv.lock`).
- Dependency layers: `uv sync --frozen --no-dev --no-install-project`
  (deps only, cached), then source copy + `uv sync --frozen --no-dev`
  (project install).
- Build command: `docker build -t tdc-matcher .` — succeeded.
- Run command: `docker run -p 8501:8501 tdc-matcher` (tested on host
  port 8502) — container starts Streamlit headless on 0.0.0.0:8501.
- Verification: `/_stcore/health` returned `ok`, main page HTTP 200, and
  an in-container check (`docker exec ... uv run python -c ...`) loaded
  all 15 sample people with no errors and produced all three statuses
  (STRONG MATCH / POSSIBLE MATCH / NOT SUITABLE).
- Single container, Streamlit only — no compose file, no extra services.
- `.dockerignore` excludes `.venv`, `.git`, caches, tests, and local
  tooling files; `data/` (needed at runtime) is included.
- Image size: 764 MB (slim base + Streamlit's numpy/pandas deps; not
  size-optimized).
- The main development workflow remains `uv`; Docker is optional
  reproducibility per `product.md` §29.

---

# 11. Documentation Log

- `README.md` — written from scratch (2026-09-24): purpose, problem,
  algorithm, complexity, data model, uv setup, tests, assumptions,
  limitations, future AI/Jev extension, note that Docker was skipped.
- `product.md` — unchanged; no requirement/design changes during
  implementation.
- `summary.md` — updated after every milestone per §6.

---

# 12. Final Verification Checklist

## Functionality

- [x] App launches. (real server smoke test: health endpoint `ok`)
- [x] Sample data loads.
- [x] Person can be selected.
- [x] Self is excluded. (tested: `find_matches` excludes by id)
- [x] Every other person is evaluated.
- [x] Matching is bidirectional.
- [x] Hard mismatch produces `NOT SUITABLE`.
- [x] All soft matches produce `STRONG MATCH`.
- [x] Some soft mismatch produces `POSSIBLE MATCH`.
- [x] Results are explainable.
- [x] Ranking works. (tested: STRONG → POSSIBLE by ratio → NOT SUITABLE)
- [x] Add-person works. (headless AppTest adds person 16)
- [x] JSON upload works. (the handler's JSON parsing and validation logic is fully covered by validator/data tests, including malformed JSON, invalid content, and error-message quality; the `st.file_uploader` widget interaction itself is not browser-automated because `st.testing.v1.AppTest` cannot simulate it — see §15)
- [x] JSON template download works.
- [x] Reset/load sample data works.

## Engineering

- [x] `uv run streamlit run app.py` works.
- [x] `uv run pytest` passes. (72 passed; 69 at review close + 3 sidebar-feedback tests)
- [x] No unnecessary services.
- [x] No hidden dependency on an external API.
- [x] Error handling is reasonable. (errors surfaced as messages, no tracebacks in normal flows)

## Documentation

- [x] README is accurate.
- [x] `product.md` matches the implementation.
- [x] `summary.md` reflects actual work.
- [x] No unsupported claims about predictive accuracy.
- [x] AI/Jev is described as future/optional, not falsely presented as implemented.

---

# 13. Final Submission Notes

The final assessment submission should include:

1. Written answers.
2. Working prototype link or screenshots/recording.
3. GitHub repository link.
4. Updated resume.
5. Short AI usage note.

The prototype should demonstrate the core idea quickly.

Do not spend remaining time adding unrelated features after the acceptance criteria are satisfied.

---

# 14. Change Log

```text
| Date | Change | Reason |
|------|--------|--------|
| 2026-09-24 | Project initialized; package renamed from `tdc` to `tdc_matcher` | Match spec §24 structure |
| 2026-09-24 | pytest added as dev dependency | Test requirement, uv-managed |
| 2026-09-24 | Added `people_to_json` "download current pool" UI affordance | Convenience; beyond minimum scope but small |
| 2026-09-24 | Docker skipped | User decision at planning; README documents this |
| 2026-09-25 | Docker added (single container, `Dockerfile` + `.dockerignore`) | User reversed the earlier skip decision; spec §29 optional-recommended |
| 2026-09-25 | Sidebar action feedback (persistent status messages) | User request — reset/add/upload gave no visible confirmation |
```

---

# 15. Known Limitations

- fixed six preference dimensions;
- exact matching for categorical fields (e.g. `yes` vs `maybe_future` is a mismatch);
- no historical learning or feedback loop;
- no production data (sample data is fictional, hand-authored);
- soft score is only a preference-match count, not a validated compatibility metric;
- no AI in MVP;
- session-only persistence — the bundled JSON file is never modified at runtime;
- no authentication / multi-user support;
- location matching is exact city equality;
- AppTest does not simulate `st.file_uploader`; the upload handler's parsing/validation logic is covered by validator/data tests, but the widget interaction itself is not automated.

---

# 16. Submission Readiness

```text
Implementation: complete and reviewed against product.md (engine, validation, data, UI)
Tests: 72 passing (uv run pytest)
UI: complete (single app.py, native Streamlit widgets)
Docker: included and verified (single container, Streamlit only)
Documentation: README + product.md + summary.md updated
Known issues: none known beyond documented limitations
```
