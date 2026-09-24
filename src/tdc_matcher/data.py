"""Loading and serialization of the people pool.

The MVP keeps all people in a single JSON file (``data/people.json``).
No database, no server: the Streamlit app edits an in-session copy of
the pool and can always restore the sample data from this file.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import Person
from .validators import parse_people

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PEOPLE_PATH = DATA_DIR / "people.json"
TEMPLATE_PATH = DATA_DIR / "template.json"


def load_people_from_file(path: str | Path) -> tuple[list[Person], list[str]]:
    """Read a JSON file and validate it.

    Returns ``(people, errors)``. Errors are human-readable strings so the
    UI can display them directly; malformed files never raise.
    """
    file_path = Path(path)
    try:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [], [f"File not found: {file_path}"]
    except json.JSONDecodeError as exc:
        return [], [f"Invalid JSON: {exc}"]
    return parse_people(raw)


def load_sample_people() -> tuple[list[Person], list[str]]:
    """Load the bundled sample pool from ``data/people.json``."""
    return load_people_from_file(PEOPLE_PATH)


def read_template_text() -> str:
    """Read the JSON template file used for downloads."""
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def people_to_json(people: list[Person]) -> str:
    """Serialize people back to the canonical JSON structure."""
    payload = {"people": [person.to_dict() for person in people]}
    return json.dumps(payload, indent=2)
