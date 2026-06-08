"""
filesystem.py — Filesystem provider.

Manages two resource types:
  - fs_file: a file with specific content
  - fs_directory: a directory that should exist
"""

import os
from pathlib import Path
from typing import Optional
from .base import Provider
from ..models import Resource
from ..utils import sha256


class FilesystemProvider(Provider):
    """Provider that manages files and directories on the local filesystem."""

    def read(self, resource: Resource) -> Optional[dict]:
        """Check if the file/directory exists and read its current state."""
        path = Path(resource.attributes["path"])

        if resource.type == "fs_file":
            if not path.exists() or not path.is_file():
                return None
            content = path.read_text()
            return {
                "path": resource.attributes["path"],
                "content": content,
                "checksum": sha256(content),
            }

        elif resource.type == "fs_directory":
            if not path.exists() or not path.is_dir():
                return None
            return {
                "path": resource.attributes["path"],
                "checksum": sha256(resource.attributes["path"]),  # dirs fingerprinted by path identity
            }

        return None

    def create(self, resource: Resource) -> dict:
        """Create a file or directory."""
        path = Path(resource.attributes["path"])

        if resource.type == "fs_file":
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            content = resource.attributes["content"]
            path.write_text(content)
            return {
                "path": resource.attributes["path"],
                "content": content,
                "checksum": sha256(content),
            }

        elif resource.type == "fs_directory":
            path.mkdir(parents=True, exist_ok=True)
            return {
                "path": resource.attributes["path"],
                "checksum": sha256(resource.attributes["path"]),
            }

        raise ValueError(f"Unknown resource type: {resource.type}")

    def update(self, resource: Resource) -> dict:
        """Update a file's content (directories don't really update)."""
        path = Path(resource.attributes["path"])

        if resource.type == "fs_file":
            content = resource.attributes["content"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            return {
                "path": resource.attributes["path"],
                "content": content,
                "checksum": sha256(content),
            }

        elif resource.type == "fs_directory":
            path.mkdir(parents=True, exist_ok=True)
            return {
                "path": resource.attributes["path"],
                "checksum": sha256(resource.attributes["path"]),
            }

        raise ValueError(f"Unknown resource type: {resource.type}")

    def delete(self, resource: Resource) -> None:
        """Delete a file or directory."""
        path = Path(resource.attributes["path"])

        if resource.type == "fs_file":
            if path.exists():
                path.unlink()

        elif resource.type == "fs_directory":
            if path.exists():
                # Remove directory (only if empty, to be safe)
                try:
                    path.rmdir()
                except OSError:
                    # Directory not empty — remove contents too
                    import shutil
                    shutil.rmtree(path)

    def fingerprint(self, resource: Resource) -> str:
        """Compute the desired-state fingerprint for a resource."""
        if resource.type == "fs_file":
            return sha256(resource.attributes["content"])
        elif resource.type == "fs_directory":
            return sha256(resource.attributes["path"])
        return ""
