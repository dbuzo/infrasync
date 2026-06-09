"""
engine.py — Core reconciliation engine.

Orchestrates the full cycle:
  1. Load config (desired state)
  2. Load state (recorded state)
  3. Compute plan (diff against real world)
  4. Apply plan (execute actions, update state per resource)
  5. Destroy (remove all managed resources)
"""

from .config import load_config
from .state import load_state, save_state, init_state
from .plan import compute_plan
from .models import Resource, ResourceState, PlanAction, ActionType
from .providers.registry import get_provider
from .graph import topological_sort
from .utils import now_iso, color_action, Colors


def cmd_init():
    """Initialize an empty state file."""
    init_state()


def cmd_plan(config_path: str = "infrasync.yaml", explain: bool = False):
    """Compute and display the plan."""
    resources = load_config(config_path)
    state = load_state()
    actions = compute_plan(resources, state)

    _display_plan(actions)

    if explain:
        from .advisor import explain_plan
        explanation = explain_plan(actions)
        if explanation:
            print(explanation)
            print()

    return actions


def cmd_apply(config_path: str = "infrasync.yaml"):
    """Apply the plan — reconcile real world to desired state."""
    resources = load_config(config_path)
    state = load_state()
    actions = compute_plan(resources, state)

    if not actions:
        print("\nNo changes needed. Infrastructure is in sync.")
        return

    _display_plan(actions)
    print(f"\n{Colors.BOLD}Applying...{Colors.RESET}\n")

    created = 0
    updated = 0
    destroyed = 0
    errors = 0

    for action in actions:
        provider = get_provider(action.resource.type)

        if action.action == ActionType.NOOP:
            if action.resource.address not in state:
                # Adopt an existing resource that already matches desired state.
                real_world = provider.read(action.resource)
                if real_world is not None:
                    state[action.resource.address] = ResourceState(
                        address=action.resource.address,
                        type=action.resource.type,
                        name=action.resource.name,
                        attributes=real_world,
                        checksum=provider.fingerprint(action.resource),
                        last_applied=now_iso(),
                        depends_on=action.resource.depends_on,
                    )
                    save_state(state)
            continue

        try:
            if action.action == ActionType.CREATE:
                result = provider.create(action.resource)
                checksum = provider.fingerprint(action.resource)
                state[action.resource.address] = ResourceState(
                    address=action.resource.address,
                    type=action.resource.type,
                    name=action.resource.name,
                    attributes=result,
                    checksum=checksum,
                    last_applied=now_iso(),
                    depends_on=action.resource.depends_on,
                )
                created += 1
                print(f"  {Colors.GREEN}+ {action.resource.address}{Colors.RESET}")

            elif action.action == ActionType.UPDATE:
                result = provider.update(action.resource)
                checksum = provider.fingerprint(action.resource)
                state[action.resource.address] = ResourceState(
                    address=action.resource.address,
                    type=action.resource.type,
                    name=action.resource.name,
                    attributes=result,
                    checksum=checksum,
                    last_applied=now_iso(),
                    depends_on=action.resource.depends_on,
                )
                updated += 1
                print(f"  {Colors.YELLOW}~ {action.resource.address}{Colors.RESET}")

            elif action.action == ActionType.DESTROY:
                provider.delete(action.resource)
                if action.resource.address in state:
                    del state[action.resource.address]
                destroyed += 1
                print(f"  {Colors.RED}- {action.resource.address}{Colors.RESET}")

            # Save state after EACH successful operation (partial apply safety)
            save_state(state)

        except Exception as e:
            errors += 1
            print(f"  {Colors.RED}ERROR on {action.resource.address}: {e}{Colors.RESET}")
            # State still reflects what succeeded — we don't rollback
            save_state(state)

    print(f"\n{Colors.BOLD}Apply complete.{Colors.RESET} "
          f"{Colors.GREEN}{created} created{Colors.RESET}, "
          f"{Colors.YELLOW}{updated} updated{Colors.RESET}, "
          f"{Colors.RED}{destroyed} destroyed{Colors.RESET}"
          + (f", {errors} errors" if errors else "") + ".")


def cmd_destroy():
    """Destroy all managed resources (reverse dependency order)."""
    state = load_state()

    if not state:
        print("No managed resources to destroy.")
        return

    print(f"\n{Colors.BOLD}Destroying all managed resources...{Colors.RESET}\n")

    destroyed = 0
    destroy_resources = [
        Resource(
            type=rs.type,
            name=rs.name,
            attributes=rs.attributes,
            depends_on=rs.depends_on,
        )
        for rs in state.values()
    ]

    try:
        ordered = list(reversed(topological_sort(destroy_resources, ignore_missing_dependencies=True)))
    except ValueError as e:
        print(f"Warning: could not compute reverse destroy order: {e}")
        ordered = destroy_resources

    for resource in ordered:
        provider = get_provider(resource.type)

        try:
            provider.delete(resource)
            print(f"  {Colors.RED}- {resource.address}{Colors.RESET}")
            destroyed += 1
        except Exception as e:
            print(f"  {Colors.RED}ERROR destroying {resource.address}: {e}{Colors.RESET}")

    # Clear state
    save_state({})
    print(f"\n{Colors.BOLD}Destroy complete.{Colors.RESET} "
          f"{Colors.RED}{destroyed} resources removed.{Colors.RESET}")


def _display_plan(actions: list[PlanAction]):
    """Pretty-print the plan to the terminal."""
    print(f"\n{Colors.BOLD}InfraSync Plan:{Colors.RESET}\n")

    has_changes = False
    for action in actions:
        if action.action == ActionType.NOOP:
            continue

        has_changes = True
        line = f"{action.resource.address}"
        if action.reason:
            line += f" ({action.reason})"
        print(color_action(action.symbol, line))

        # Show attribute details
        if action.action == ActionType.CREATE:
            for key, val in action.resource.attributes.items():
                val_str = _truncate(str(val), 60)
                print(f"      {key}: {val_str}")

        elif action.action == ActionType.UPDATE and action.changes:
            for key, (old, new) in action.changes.items():
                old_str = _truncate(str(old), 30)
                new_str = _truncate(str(new), 30)
                print(f"      {key}: {old_str} => {new_str}")

        print()

    if not has_changes:
        print("  No changes. Infrastructure is in sync.\n")
        return

    creates = sum(1 for a in actions if a.action == ActionType.CREATE)
    updates = sum(1 for a in actions if a.action == ActionType.UPDATE)
    destroys = sum(1 for a in actions if a.action == ActionType.DESTROY)
    print(f"Plan: {creates} to create, {updates} to update, {destroys} to destroy.\n")


def _truncate(s: str, max_len: int) -> str:
    """Truncate long strings for display."""
    s = s.replace("\n", "\\n")
    if len(s) > max_len:
        return s[:max_len] + "..."
    return s
