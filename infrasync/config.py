"""
config.py — Parse and validate the YAML config file.

Turns a YAML file into a list of Resource objects.
"""

import yaml
import sys
from pathlib import Path
from .models import Resource


def load_config(config_path: str = "infrasync.yaml") -> list[Resource]:
    """Load and validate the config file, returning a list of Resources."""
    path = Path(config_path)

    if not path.exists():
        print(f"Error: Config file '{config_path}' not found.")
        sys.exit(1)

    try:
        with open(path, "r") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in '{config_path}': {e}")
        sys.exit(1)

    if not raw or "resources" not in raw:
        print(f"Error: Config file must contain a 'resources' list.")
        sys.exit(1)

    resources = []
    seen_addresses = set()

    for i, entry in enumerate(raw["resources"]):
        resource = _parse_resource(entry, i)
        if resource.address in seen_addresses:
            print(f"Error: Duplicate resource address '{resource.address}'.")
            sys.exit(1)
        seen_addresses.add(resource.address)
        resources.append(resource)

    return resources


def _parse_resource(entry: dict, index: int) -> Resource:
    """Parse a single resource entry from config."""
    required = ["type", "name"]
    for field in required:
        if field not in entry:
            print(f"Error: Resource at index {index} missing required field '{field}'.")
            sys.exit(1)

    rtype = entry["type"]
    name = entry["name"]
    depends_on = entry.get("depends_on", [])

    # Everything except type, name, depends_on goes into attributes
    attributes = {
        k: v for k, v in entry.items()
        if k not in ("type", "name", "depends_on")
    }

    # Validate known resource types have required attributes
    _validate_attributes(rtype, name, attributes)

    return Resource(
        type=rtype,
        name=name,
        attributes=attributes,
        depends_on=depends_on,
    )


def _validate_attributes(rtype: str, name: str, attributes: dict):
    """Check that resource attributes make sense for the given type."""
    if rtype == "fs_file":
        if "path" not in attributes:
            print(f"Error: fs_file.{name} requires 'path' attribute.")
            sys.exit(1)
        if "content" not in attributes:
            print(f"Error: fs_file.{name} requires 'content' attribute.")
            sys.exit(1)

    elif rtype == "fs_directory":
        if "path" not in attributes:
            print(f"Error: fs_directory.{name} requires 'path' attribute.")
            sys.exit(1)

    else:
        print(f"Warning: Unknown resource type '{rtype}'. No validation applied.")
