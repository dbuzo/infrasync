"""
plan.py — Compute the diff between desired state and real-world state.

This is the core reconciliation logic:
  - Config vs State vs Real World = three-way diff
  - Output: a list of PlanActions (create, update, destroy, noop)
"""

from .models import Resource, ResourceState, PlanAction, ActionType
from .providers.registry import get_provider
from .graph import topological_sort
from typing import Dict, List


def compute_plan(
    resources: List[Resource],
    state: Dict[str, ResourceState],
) -> List[PlanAction]:
    """
    Compute what needs to happen to reconcile desired state with reality.

    Three-way comparison for each resource:
      1. In config + not in state → CREATE (new resource)
      2. In config + in state + world matches desired → NOOP
      3. In config + in state + world differs → UPDATE (drift or config change)
      4. In config + in state + not in world → CREATE (disappeared)
      5. In state + not in config → DESTROY (removed from config)
    """
    actions = []

    # Sort resources by dependency order for creates/updates
    sorted_resources = topological_sort(resources)
    config_addresses = {r.address for r in resources}

    # Check each resource in config
    for resource in sorted_resources:
        provider = get_provider(resource.type)
        real_world = provider.read(resource)
        desired_checksum = provider.fingerprint(resource)

        if resource.address not in state:
            # Never been applied before
            if real_world is None:
                # Doesn't exist anywhere — create it
                actions.append(PlanAction(
                    action=ActionType.CREATE,
                    resource=resource,
                    reason="new resource",
                ))
            else:
                # Exists in world but not in state (maybe created manually)
                real_checksum = real_world.get("checksum", "")
                if real_checksum == desired_checksum:
                    # World matches config — just adopt into state (noop)
                    actions.append(PlanAction(
                        action=ActionType.NOOP,
                        resource=resource,
                        reason="already matches desired state",
                    ))
                else:
                    # World exists but differs from config — update
                    actions.append(PlanAction(
                        action=ActionType.UPDATE,
                        resource=resource,
                        reason="exists but content differs from config",
                        changes=_compute_changes(real_world, resource),
                    ))
        else:
            # Has been applied before (in state)
            recorded = state[resource.address]

            if real_world is None:
                # State says it exists, but it's gone from the world — recreate
                actions.append(PlanAction(
                    action=ActionType.CREATE,
                    resource=resource,
                    reason="resource was deleted externally",
                ))
            else:
                real_checksum = real_world.get("checksum", "")

                if real_checksum == desired_checksum:
                    # Everything matches — nothing to do
                    actions.append(PlanAction(
                        action=ActionType.NOOP,
                        resource=resource,
                        reason="up to date",
                    ))
                elif real_checksum != recorded.checksum:
                    # Real world differs from state — drift
                    actions.append(PlanAction(
                        action=ActionType.UPDATE,
                        resource=resource,
                        reason="drift detected — changed outside infrasync",
                        changes=_compute_changes(real_world, resource),
                    ))
                else:
                    # Real world matches state but config changed — config update
                    actions.append(PlanAction(
                        action=ActionType.UPDATE,
                        resource=resource,
                        reason="config changed",
                        changes=_compute_changes(real_world, resource),
                    ))

    # Check for resources in state but not in config (need to destroy)
    for address, recorded in state.items():
        if address not in config_addresses:
            # Build a minimal Resource for the destroy action
            resource = Resource(
                type=recorded.type,
                name=recorded.name,
                attributes=recorded.attributes,
            )
            actions.append(PlanAction(
                action=ActionType.DESTROY,
                resource=resource,
                reason="removed from config",
            ))

    return actions


def _compute_changes(real_world: dict, resource: Resource) -> dict:
    """Compute attribute-level changes between real world and desired."""
    changes = {}
    for key, desired_val in resource.attributes.items():
        real_val = real_world.get(key)
        if real_val is not None and real_val != desired_val:
            changes[key] = (real_val, desired_val)
    return changes
