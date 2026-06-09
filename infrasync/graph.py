"""
graph.py — Dependency graph and topological sort.

Ensures resources are created in the right order (dependencies first)
and destroyed in reverse order.
"""

from .models import Resource
from typing import List


def topological_sort(resources: List[Resource], ignore_missing_dependencies: bool = False) -> List[Resource]:
    """
    Sort resources so dependencies come before dependents.
    Raises ValueError if a cycle is detected.

    If ignore_missing_dependencies is True, any dependency that is not part of
    the provided resource set is ignored. This is useful when ordering destroy
    operations for resources that may depend on resources being retained.
    """
    # Build adjacency: address -> list of addresses that depend on it
    address_map = {r.address: r for r in resources}
    in_degree = {r.address: 0 for r in resources}
    dependents = {r.address: [] for r in resources}

    for r in resources:
        for dep in r.depends_on:
            if dep not in address_map:
                if ignore_missing_dependencies:
                    continue
                raise ValueError(
                    f"Resource '{r.address}' depends on '{dep}', "
                    f"which is not defined in config."
                )
            dependents[dep].append(r.address)
            in_degree[r.address] += 1

    # Kahn's algorithm
    queue = [addr for addr, deg in in_degree.items() if deg == 0]
    sorted_order = []

    while queue:
        # Sort for deterministic output
        queue.sort()
        current = queue.pop(0)
        sorted_order.append(current)

        for dependent in dependents[current]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(sorted_order) != len(resources):
        # Cycle detected
        remaining = [r.address for r in resources if r.address not in sorted_order]
        raise ValueError(
            f"Dependency cycle detected involving: {remaining}"
        )

    return [address_map[addr] for addr in sorted_order]
