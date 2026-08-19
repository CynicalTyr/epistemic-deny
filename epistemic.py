"""Epistemic discipline helpers for allowlist blocks and admin status replies.

A deny that looks like a normal tool error is how models invent config:
they treat 'permission denied' as 'the flag is unset' and report success.
These packets make STATUS/WHY/USE_INSTEAD first-class in the tool result.
"""

from __future__ import annotations

import hashlib
from typing import Any, Literal

AllowlistVerdictLabel = Literal[
    "blocked",
    "restricted",
    "unknown",
    "denied",
]

_DEFAULT_USE_INSTEAD = (
    "inspect_runtime_config, memory_query_readonly, inspect_system_health, "
    "read_file on RUNBOOK_MD/TOPOLOGY_MD, python_agent_playbook, or propose_allowlist_rule"
)

_VERSION_CHECK_DOCTRINE = (
    "NEXT_LEGAL_MOVES: Use `.venv/bin/python3 -m pip show <package>` for installed "
    "versions; read_file on the requirements pin file; inspect_system_health or "
    "a connectivity probe for /api/health."
)

_STATUS_BY_VERDICT: dict[str, str] = {
    "blocked": "BLOCKED",
    "restricted": "RESTRICTED",
    "unknown": "UNKNOWN",
    "denied": "DENIED",
}


def format_allowlist_block_result(
    cmd: str,
    *,
    reason: str | None,
    alternative_tool: str | None = None,
    alternative_hint: str | None = None,
    hard_block: bool = False,
    identical_retry_count: int = 1,
    verdict: AllowlistVerdictLabel | str | None = None,
) -> str:
    """Structured tool result the agent must read as deny + next legal move.

    Always includes STATUS, WHY, USE_INSTEAD, and HINT so the agent can tell
    blocked vs restricted vs unknown and what to try instead of inventing state.
    """
    resolved_verdict = (
        "blocked"
        if hard_block
        else (str(verdict).strip().lower() if verdict else "blocked")
    )
    if resolved_verdict not in _STATUS_BY_VERDICT:
        resolved_verdict = "blocked"

    status = "HARD-BLOCKED" if hard_block else _STATUS_BY_VERDICT[resolved_verdict]
    why = (reason or "").strip() or "Denied by allowlist policy."
    use_instead = (alternative_tool or "").strip() or _DEFAULT_USE_INSTEAD
    hint = (alternative_hint or "").strip() or why

    lines = [
        f"STATUS: {status}",
        f"VERDICT: {resolved_verdict}",
        f"COMMAND: {(cmd or '')[:200]}",
        f"WHY: {why}",
        f"USE_INSTEAD: {use_instead}",
        f"HINT: {hint}",
    ]
    if hard_block or resolved_verdict == "blocked":
        lines.append(
            "RETRY_RULE: Do NOT retry the same command or a minor variant "
            "(e.g. python -c, path-prefixed interpreters, or chaining)."
        )
    elif resolved_verdict == "restricted":
        lines.append(
            "RETRY_RULE: Restricted — needs operator admin_override on the "
            "console/messenger, or propose_allowlist_rule. Do not invent a SAFE bypass."
        )
    elif resolved_verdict == "unknown":
        lines.append(
            "RETRY_RULE: Command is not on safe_prefixes. Do not invent execution "
            "results. Use USE_INSTEAD/HINT or propose_allowlist_rule."
        )
    else:
        lines.append(
            "RETRY_RULE: Execution denied. Follow USE_INSTEAD/HINT; do not retry "
            "the same shell payload."
        )

    hint_lower = hint.lower()
    cmd_lower = (cmd or "").lower()
    if (
        hard_block
        or "pip show" in hint_lower
        or "python -c" in cmd_lower
        or "/python3 -c" in cmd_lower
        or "/python -c" in cmd_lower
    ):
        lines.append(_VERSION_CHECK_DOCTRINE)

    lines.append(
        "AGENT_RULE: You were denied this shell/config action. Do not state "
        "configuration or file contents as fact. Say STATUS/VERDICT plainly, "
        "follow USE_INSTEAD and HINT, or ask the operator."
    )
    lines.append(
        "EPISTEMIC_RULE: Do not invent blocked state as success. Prefer the "
        "HINT command/tool over retrying variants."
    )
    if hard_block and identical_retry_count >= 2:
        lines.append(
            "STOP_RETRY: This identical command was HARD-BLOCKED "
            f"{identical_retry_count} times in this tool loop. Stop retrying shell "
            "variants; answer in text using NEXT_LEGAL_MOVES / HINT only."
        )
    return "\n".join(lines)


def increment_identical_allowlist_block(brain: Any, cmd: str) -> int:
    """Count identical hard-blocked commands within the current brain session."""
    key = hashlib.sha256((cmd or "").strip().encode()).hexdigest()[:16]
    counts: dict[str, int] = getattr(brain, "_allowlist_identical_block_counts", None) or {}
    counts[key] = counts.get(key, 0) + 1
    brain._allowlist_identical_block_counts = counts
    return counts[key]


def finalize_hard_allowlist_block(
    brain: Any,
    cmd: str,
    *,
    guidance: dict[str, str | None],
) -> tuple[str, bool]:
    """Format a hard-block tool result and return whether to force text-only recovery."""
    retry_count = increment_identical_allowlist_block(brain, cmd)
    result = format_allowlist_block_result(
        cmd,
        reason=guidance.get("reason"),
        alternative_tool=guidance.get("alternative_tool"),
        alternative_hint=guidance.get("alternative_hint"),
        hard_block=True,
        identical_retry_count=retry_count,
        verdict="blocked",
    )
    return result, retry_count >= 2


def block_guidance_from_actions(actions: Any) -> dict[str, str | None]:
    return {
        "reason": getattr(actions, "_last_block_reason", None),
        "alternative_tool": getattr(actions, "_last_block_alternative_tool", None),
        "alternative_hint": getattr(actions, "_last_block_alternative_hint", None),
    }
