"""
registry.py — Provider registry.

Maps resource types to their provider implementation.
This is where you'd register new providers (cloud, database, HTTP).
"""

from typing import Dict, List
from .base import Provider
from .filesystem import FilesystemProvider


# Singleton instances
_filesystem_provider = FilesystemProvider()

# Registry: resource_type -> provider
_PROVIDERS: Dict[str, Provider] = {
    "fs_file": _filesystem_provider,
    "fs_directory": _filesystem_provider,
}


def get_provider(resource_type: str) -> Provider:
    """Look up the provider for a given resource type."""
    if resource_type not in _PROVIDERS:
        raise ValueError(
            f"No provider registered for resource type '{resource_type}'. "
            f"Known types: {list(_PROVIDERS.keys())}"
        )
    return _PROVIDERS[resource_type]


def registered_types() -> List[str]:
    """List all registered resource types."""
    return list(_PROVIDERS.keys())
