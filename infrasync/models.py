"""
models.py — Data models for resources and plan actions.

A Resource is what the user declares in config.
A ResourceState is what we persist in the state file.
A PlanAction is what the engine decides to do.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Dict, Tuple


class ActionType(Enum):
    CREATE = "create"
    UPDATE = "update"
    DESTROY = "destroy"
    NOOP = "noop"


@dataclass
class Resource:
    """A resource declared in the config file."""
    type: str          # e.g. "fs_file", "fs_directory"
    name: str          # user-given name
    attributes: dict   # type-specific properties (path, content, etc.)
    depends_on: List[str] = field(default_factory=list)

    @property
    def address(self) -> str:
        """Unique identifier: type.name (e.g. fs_file.readme)"""
        return f"{self.type}.{self.name}"


@dataclass
class ResourceState:
    """Persisted state for a single resource after apply."""
    address: str
    type: str
    name: str
    attributes: dict
    checksum: str
    last_applied: str  # ISO timestamp


@dataclass
class PlanAction:
    """A single action the engine will take during apply."""
    action: ActionType
    resource: Resource
    reason: str = ""
    changes: dict = field(default_factory=dict)  # {attr: (old_value, new_value)}

    @property
    def symbol(self) -> str:
        symbols = {
            ActionType.CREATE: "+",
            ActionType.UPDATE: "~",
            ActionType.DESTROY: "-",
            ActionType.NOOP: " ",
        }
        return symbols[self.action]
