"""
base.py — Abstract provider interface.

Every provider (filesystem, cloud, database, HTTP) implements this.
The engine never knows the details — only this interface.
"""

from abc import ABC, abstractmethod
from typing import Optional
from ..models import Resource


class Provider(ABC):
    """Abstract base for all resource providers."""

    @abstractmethod
    def read(self, resource: Resource) -> Optional[dict]:
        """
        Read the current real-world state of a resource.
        Returns a dict of attributes if it exists, or None if it doesn't.
        """
        pass

    @abstractmethod
    def create(self, resource: Resource) -> dict:
        """
        Create the resource in the real world.
        Returns the resulting attributes (for state storage).
        """
        pass

    @abstractmethod
    def update(self, resource: Resource) -> dict:
        """
        Update the resource to match desired state.
        Returns the updated attributes.
        """
        pass

    @abstractmethod
    def delete(self, resource: Resource) -> None:
        """Remove the resource from the real world."""
        pass

    @abstractmethod
    def fingerprint(self, resource: Resource) -> str:
        """
        Generate a content hash representing the desired state.
        Used for drift detection: if real-world fingerprint != desired fingerprint,
        the resource has drifted.
        """
        pass
