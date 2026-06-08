"""
advisor — Optional AI-assisted drift analysis.

When drift is detected, this module can explain what happened
and recommend whether to correct or accept the change.

This is a thin, optional layer. The core engine works without it.
Set ANTHROPIC_API_KEY environment variable to enable.
"""

import os
from typing import List
from ..models import PlanAction, ActionType


def explain_plan(actions: List[PlanAction]) -> str:
    """
    Generate a plain-English explanation of the plan using an LLM.
    Falls back to a simple summary if no API key is configured.
    """
    drift_actions = [a for a in actions if a.action == ActionType.UPDATE and "drift" in a.reason]

    if not drift_actions:
        return ""

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return _local_explanation(drift_actions)

    try:
        return _llm_explanation(drift_actions, api_key)
    except Exception as e:
        return f"  (AI advisor unavailable: {e})\n" + _local_explanation(drift_actions)


def _local_explanation(actions: List[PlanAction]) -> str:
    """Simple rule-based explanation when no LLM is available."""
    lines = ["\n  Drift Advisor:"]
    for action in actions:
        resource = action.resource
        lines.append(f"    • {resource.address} was modified outside infrasync.")
        if action.changes:
            for attr, (old, new) in action.changes.items():
                lines.append(f"      {attr} changed externally.")
        lines.append(f"      Recommendation: run 'apply' to restore, or update config if the change was intentional.")
    return "\n".join(lines)


def _llm_explanation(actions: List[PlanAction], api_key: str) -> str:
    """Use Claude API to explain drift in plain English."""
    try:
        import httpx
    except ImportError:
        return _local_explanation(actions)

    # Build a concise description of what drifted
    drift_summary = []
    for action in actions:
        desc = f"Resource: {action.resource.address} (type: {action.resource.type})"
        if action.changes:
            for attr, (old, new) in action.changes.items():
                desc += f"\n  {attr}: was '{_truncate(str(old), 50)}' → should be '{_truncate(str(new), 50)}'"
        drift_summary.append(desc)

    prompt = (
        "You are an infrastructure operations advisor. "
        "The following managed resources have drifted from their desired state "
        "(they were changed outside of the provisioning tool). "
        "For each, briefly explain the likely cause and recommend whether to "
        "correct (apply) or accept (update config). Keep it concise — 2-3 sentences per resource.\n\n"
        + "\n\n".join(drift_summary)
    )

    response = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=10.0,
    )

    if response.status_code == 200:
        data = response.json()
        text = data["content"][0]["text"]
        return "\n  AI Drift Advisor:\n    " + text.replace("\n", "\n    ")
    else:
        return _local_explanation(actions)


def _truncate(s: str, max_len: int) -> str:
    s = s.replace("\n", "\\n")
    return s[:max_len] + "..." if len(s) > max_len else s
