"""
__main__.py — CLI entry point for infrasync.

Usage:
    python -m infrasync init
    python -m infrasync plan
    python -m infrasync apply
    python -m infrasync destroy
"""

import argparse
import sys
from .engine import cmd_init, cmd_plan, cmd_apply, cmd_destroy


def main():
    parser = argparse.ArgumentParser(
        prog="infrasync",
        description="Declarative infrastructure provisioning with state reconciliation.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init
    subparsers.add_parser("init", help="Initialize a new state file")

    # plan
    plan_parser = subparsers.add_parser("plan", help="Show what changes would be made")
    plan_parser.add_argument(
        "-c", "--config", default="infrasync.yaml",
        help="Path to config file (default: infrasync.yaml)"
    )
    plan_parser.add_argument(
        "--explain", action="store_true",
        help="Use AI advisor to explain detected drift"
    )

    # apply
    apply_parser = subparsers.add_parser("apply", help="Apply changes to match desired state")
    apply_parser.add_argument(
        "-c", "--config", default="infrasync.yaml",
        help="Path to config file (default: infrasync.yaml)"
    )

    # destroy
    subparsers.add_parser("destroy", help="Destroy all managed resources")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    if args.command == "init":
        cmd_init()
    elif args.command == "plan":
        cmd_plan(args.config, explain=args.explain)
    elif args.command == "apply":
        cmd_apply(args.config)
    elif args.command == "destroy":
        cmd_destroy()


if __name__ == "__main__":
    main()
