"""TDC Matcher — Streamlit entry point.

A small internal tool for TDC matchmakers: pick a client, screen every
other person in the pool against explicit preferences (in both
directions), and keep the final matchmaking decision with the human.

Hard preference mismatches are disqualifying; soft preferences only
rank and flag candidates for human review.
"""

import json

import streamlit as st

from tdc_matcher.data import load_sample_people, people_to_json, read_template_text
from tdc_matcher.matcher import find_matches
from tdc_matcher.models import MatchStatus, Strictness
from tdc_matcher.validators import parse_people, person_from_dict, validate_people

WANTS_CHILDREN_OPTIONS = ("yes", "no", "maybe_future")
RELATIONSHIP_GOAL_OPTIONS = ("marriage", "long_term", "open")
LIFESTYLE_OPTIONS = ("quiet", "moderate", "social")
STRICTNESS_OPTIONS = ("hard", "soft")
NO_YES_OPTIONS = ("No", "Yes")

st.set_page_config(
    page_title="TDC Matcher", page_icon=":material/favorite:", layout="centered"
)


def load_sample_pool() -> None:
    """(Re)load the bundled sample pool into session state."""
    people, errors = load_sample_people()
    st.session_state.people = people
    st.session_state.data_errors = errors


if "people" not in st.session_state:
    load_sample_pool()


def status_badge(status: MatchStatus) -> str:
    if status is MatchStatus.STRONG_MATCH:
        return ":green[STRONG MATCH]"
    if status is MatchStatus.POSSIBLE_MATCH:
        return ":orange[POSSIBLE MATCH]"
    return ":red[NOT SUITABLE]"


def check_icon(matched: bool, strictness: Strictness) -> str:
    if matched:
        return ":material/check:"
    if strictness is Strictness.HARD:
        return ":material/block:"
    return ":material/warning:"


def render_direction(title: str, direction) -> None:
    """Render one directional evaluation, e.g. 'Aarav → Isha'."""
    st.markdown(f"**{title}**")
    for check in direction.checks:
        st.markdown(
            f"{check_icon(check.matched, check.strictness)} "
            f"{check.preference} — {check.attribute} "
            f"({check.strictness.value})"
        )


def render_result(result) -> None:
    """Render one candidate card with reasons and a detail expander."""
    candidate = result.candidate
    with st.container(border=True):
        st.markdown(
            f"**{candidate.name}** ({candidate.id}) — {status_badge(result.status)}"
        )
        if result.status is not MatchStatus.NOT_SUITABLE:
            st.caption(
                f"Soft preferences matched: {result.soft_match_count} / {result.soft_total}"
            )
        for reason in result.summary_reasons:
            st.markdown(f"- {reason}")
        with st.expander("Details"):
            render_direction(
                f"{result.a_to_b.from_name} → {result.a_to_b.to_name}", result.a_to_b
            )
            st.divider()
            render_direction(
                f"{result.b_to_a.from_name} → {result.b_to_a.to_name}", result.b_to_a
            )


def render_sidebar() -> None:
    """Data management: add person, upload JSON, download template, reset."""
    with st.sidebar:
        st.header("Data")
        st.download_button(
            "Download JSON template",
            data=read_template_text(),
            file_name="tdc_people_template.json",
            mime="application/json",
            icon=":material/download:",
        )

        uploaded = st.file_uploader("Upload people JSON", type="json")
        if uploaded is not None:
            fingerprint = f"{uploaded.name}:{uploaded.size}"
            if st.session_state.get("last_upload") != fingerprint:
                try:
                    raw = json.loads(uploaded.getvalue().decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    st.error(f"Invalid JSON: {exc}")
                else:
                    people, errors = parse_people(raw)
                    if errors:
                        st.error("Upload rejected — fix these problems and try again:")
                        for error in errors:
                            st.markdown(f"- {error}")
                    else:
                        st.session_state.people = people
                        st.session_state.data_errors = []
                        st.session_state.last_upload = fingerprint
                        st.toast(
                            f"Loaded {len(people)} people.", icon=":material/check:"
                        )
                        st.rerun()

        if st.button("Reset to sample data", icon=":material/restart_alt:"):
            load_sample_pool()
            st.rerun()

        st.download_button(
            "Download current pool",
            data=people_to_json(st.session_state.people),
            file_name="tdc_people.json",
            mime="application/json",
            icon=":material/save:",
        )

        st.divider()
        render_add_person_form()


def next_id(people) -> str:
    """Generate a unique person id like 'p016'."""
    existing = {p.id for p in people}
    n = len(people) + 1
    while f"p{n:03d}" in existing:
        n += 1
    return f"p{n:03d}"


def render_add_person_form() -> None:
    with st.expander("Add person"):
        with st.form("add_person", border=False):
            st.markdown("##### Attributes")
            name = st.text_input("Name")
            age = st.number_input("Age", min_value=18, max_value=99, value=29)
            city = st.text_input("City")
            state = st.text_input("State")
            country = st.text_input("Country", value="India")
            smoking = st.selectbox("Smoking", NO_YES_OPTIONS) == "Yes"
            wants_children = st.selectbox("Wants children", WANTS_CHILDREN_OPTIONS)
            goal = st.selectbox("Relationship goal", RELATIONSHIP_GOAL_OPTIONS)
            lifestyle = st.selectbox("Lifestyle", LIFESTYLE_OPTIONS)

            st.markdown("##### Preferences")
            age_min = st.number_input(
                "Preferred age — min", min_value=18, max_value=99, value=25
            )
            age_max = st.number_input(
                "Preferred age — max", min_value=18, max_value=99, value=35
            )
            pref_city = st.text_input("Preferred city")
            age_strictness = st.segmented_control(
                "Age strictness", STRICTNESS_OPTIONS, default="hard"
            )
            location_strictness = st.segmented_control(
                "Location strictness", STRICTNESS_OPTIONS, default="soft"
            )
            pref_smoking = st.selectbox("Smoking preference", NO_YES_OPTIONS) == "Yes"
            smoking_strictness = st.segmented_control(
                "Smoking strictness", STRICTNESS_OPTIONS, default="hard"
            )
            pref_wants_children = st.selectbox(
                "Wants children preference", WANTS_CHILDREN_OPTIONS
            )
            wants_strictness = st.segmented_control(
                "Wants children strictness", STRICTNESS_OPTIONS, default="soft"
            )
            pref_goal = st.selectbox(
                "Relationship goal preference", RELATIONSHIP_GOAL_OPTIONS
            )
            goal_strictness = st.segmented_control(
                "Relationship goal strictness", STRICTNESS_OPTIONS, default="hard"
            )
            pref_lifestyle = st.selectbox("Lifestyle preference", LIFESTYLE_OPTIONS)
            lifestyle_strictness = st.segmented_control(
                "Lifestyle strictness", STRICTNESS_OPTIONS, default="soft"
            )
            submitted = st.form_submit_button(
                "Add person", icon=":material/person_add:", type="primary"
            )

        if submitted:
            person_id = next_id(st.session_state.people)
            candidate_dict = {
                "id": person_id,
                "name": name,
                "attributes": {
                    "age": int(age),
                    "location": {"city": city, "state": state, "country": country},
                    "smoking": smoking,
                    "wants_children": wants_children,
                    "relationship_goal": goal,
                    "lifestyle": lifestyle,
                },
                "preferences": {
                    "age": {
                        "min": int(age_min),
                        "max": int(age_max),
                        "strictness": age_strictness,
                    },
                    "location": {"city": pref_city, "strictness": location_strictness},
                    "smoking": {
                        "value": pref_smoking,
                        "strictness": smoking_strictness,
                    },
                    "wants_children": {
                        "value": pref_wants_children,
                        "strictness": wants_strictness,
                    },
                    "relationship_goal": {
                        "value": pref_goal,
                        "strictness": goal_strictness,
                    },
                    "lifestyle": {
                        "value": pref_lifestyle,
                        "strictness": lifestyle_strictness,
                    },
                },
            }
            prefix = f"people[0] (id='{person_id}'): "
            errors = [
                e.removeprefix(prefix)
                for e in validate_people({"people": [candidate_dict]})
            ]
            if errors:
                for error in errors:
                    st.error(error)
            else:
                st.session_state.people.append(person_from_dict(candidate_dict))
                st.toast(f"Added {name}.", icon=":material/check:")
                st.rerun()


render_sidebar()

st.title("TDC Matcher")
st.caption(
    "Screen and rank candidates against explicit preferences — the final decision stays with the matchmaker."
)

people = st.session_state.people

if st.session_state.data_errors:
    st.error("Sample data could not be loaded:")
    for error in st.session_state.data_errors:
        st.markdown(f"- {error}")
    st.info("Try 'Reset to sample data' in the sidebar, or upload a valid JSON file.")
    st.stop()

if not people:
    st.info("The pool is empty. Add a person in the sidebar to begin.")
    st.stop()

labels = {f"{p.name} ({p.id})": p for p in people}
selected = labels[st.selectbox("Client", options=list(labels))]

st.divider()

if len(people) < 2:
    st.warning(
        "The pool has only one person — add more people to see candidate matches."
    )
    st.stop()

results = find_matches(selected, people)
eligible = [r for r in results if r.status is not MatchStatus.NOT_SUITABLE]

if eligible:
    strong = sum(1 for r in eligible if r.status is MatchStatus.STRONG_MATCH)
    st.markdown(
        f"**{len(eligible)} of {len(results)} candidates** clear all hard preferences in both "
        f"directions ({strong} strong, {len(eligible) - strong} possible)."
    )
else:
    st.warning("No candidate clears the hard preferences in both directions.")

show_rejected = st.checkbox("Show not-suitable candidates", value=False)
for result in results:
    if result.status is MatchStatus.NOT_SUITABLE and not show_rejected:
        continue
    render_result(result)
