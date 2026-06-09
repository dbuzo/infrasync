"""
state.py — Read and write the state file.

The state file records what was last applied:
which resources exist, their checksums, and when they were last touched.
"""

import json
from pathlib import Path
from typing import Dict
from .models import ResourceState


STATE_FILE = "infrasync.state.json"
STATE_VERSION = 1


def load_state(state_path: str = STATE_FILE) -> Dict[str, ResourceState]:
    """Load existing state from disk. Returns empty dict if no state file."""
    path = Path(state_path)

    if not path.exists():
        return {}

    try:
        with open(path, "r") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not read state file: {e}. Starting fresh.")
        return {}

    if raw.get("version") != STATE_VERSION:
        print(f"Warning: State file version mismatch. Starting fresh.")
        return {}

    resources = {}
    for address, data in raw.get("resources", {}).items():
        resources[address] = ResourceState(
            address=address,
            type=data["type"],
            name=data["name"],
            attributes=data["attributes"],
            checksum=data["checksum"],
            last_applied=data["last_applied"],
            depends_on=data.get("depends_on", []),
        )

    return resources


def save_state(resources: Dict[str, ResourceState], state_path: str = STATE_FILE):
    """Write the full state to disk."""
    data = {
        "version": STATE_VERSION,
        "resources": {}
    }

    for address, rs in resources.items():
        data["resources"][address] = {
            "type": rs.type,
            "name": rs.name,
            "attributes": rs.attributes,
            "checksum": rs.checksum,
            "last_applied": rs.last_applied,
            "depends_on": rs.depends_on,
        }

    with open(state_path, "w") as f:
        json.dump(data, f, indent=2)


def init_state(state_path: str = STATE_FILE):
    """Create an empty state file."""
    path = Path(state_path)
    if path.exists():
        print(f"State file '{state_path}' already exists. Nothing to do.")
        return

    save_state({}, state_path)
    print(f"Initialized empty state file: {state_path}")
