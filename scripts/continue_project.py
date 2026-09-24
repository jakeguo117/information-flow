#!/usr/bin/env python3
"""Minimal local「继续项目」continuation route.

Deterministic chain (Manifest cut D):
  Global Governance → PROJECT_CONTROL → PROJECT_MILESTONE_MAP →
  Frozen authority / approved Manifest → verified repo state →
  minimum relevant DigitalBrain context → bounded next action.

Callers inject availability and results. This module does not fetch Drive,
read a live vault, or invent project state.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

STEP_ORDER = (
    "governance",
    "project_control",
    "milestone_map",
    "frozen_authority_or_manifest",
    "repo_verification",
    "digitalbrain_context",
)

# Higher wins when multiple gaps apply.
_SEVERITY_RANK = {
    "found": 0,
    "partial": 1,
    "unavailable": 2,
    "blocked": 3,
}

_UNBLOCK = {
    "governance": "Restore Global Governance (present and readable).",
    "project_control": "Provide PROJECT_CONTROL via the project router.",
    "milestone_map": "Provide PROJECT_MILESTONE_MAP.",
    "frozen_authority_or_manifest": (
        "Provide an approved Manifest (frozen authority)."
    ),
    "repo_verification": "Verify repository state and supply the verified SHA.",
    "digitalbrain_context": (
        "Restore DigitalBrain vault access with minimum context "
        "(ids/statuses only)."
    ),
}


def _avail(value: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        if key in value and value[key] is not None:
            return str(value[key]).strip().lower()
    return ""


def continue_project(
    *,
    governance: Mapping[str, Any],
    project_control: Mapping[str, Any],
    milestone_map: Mapping[str, Any],
    frozen_authority_or_manifest: Mapping[str, Any],
    repo_verification: Mapping[str, Any],
    vault_access: Mapping[str, Any],
    digitalbrain_minimum_context: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Evaluate the continuation chain from injected structured inputs.

    Returns a structured result with:
      - status: found | partial | unavailable | blocked
      - steps_checked: ordered present/missing marks
      - gaps: list of {step, reason, severity} when not found
      - bounded_next_action: success action or unblock step
      - verified_sha: echoed only when repo_verification supplied a SHA
        and status is found (never invented)

    Never invents milestone status, SHA, or vault facts.
    """
    steps_checked: list[dict[str, str]] = []
    gaps: list[dict[str, str]] = []
    verified_sha: Optional[str] = None

    # --- 1. Global Governance ---
    gov = _avail(governance, "availability", "status")
    if gov == "present":
        steps_checked.append({"step": "governance", "state": "present"})
    else:
        steps_checked.append({"step": "governance", "state": "missing"})
        reason = (
            "governance unreadable"
            if gov == "unreadable"
            else "governance missing"
        )
        gaps.append(
            {
                "step": "governance",
                "reason": reason,
                "severity": "unavailable",
            }
        )

    # --- 2. PROJECT_CONTROL ---
    pc = _avail(project_control, "availability", "status")
    if pc == "present":
        steps_checked.append({"step": "project_control", "state": "present"})
    else:
        steps_checked.append({"step": "project_control", "state": "missing"})
        gaps.append(
            {
                "step": "project_control",
                "reason": "PROJECT_CONTROL missing",
                "severity": "partial",
            }
        )

    # --- 3. PROJECT_MILESTONE_MAP ---
    mm = _avail(milestone_map, "availability", "status")
    if mm == "present":
        steps_checked.append({"step": "milestone_map", "state": "present"})
    else:
        steps_checked.append({"step": "milestone_map", "state": "missing"})
        gaps.append(
            {
                "step": "milestone_map",
                "reason": "PROJECT_MILESTONE_MAP missing",
                "severity": "partial",
            }
        )

    # --- 4. Frozen authority / approved Manifest ---
    fa = _avail(frozen_authority_or_manifest, "availability", "status")
    approved = bool(frozen_authority_or_manifest.get("approved"))
    if fa == "present" and approved:
        steps_checked.append(
            {"step": "frozen_authority_or_manifest", "state": "present"}
        )
    else:
        steps_checked.append(
            {"step": "frozen_authority_or_manifest", "state": "missing"}
        )
        if fa != "present":
            reason = "approved Manifest missing"
        else:
            reason = "Manifest present but not approved"
        gaps.append(
            {
                "step": "frozen_authority_or_manifest",
                "reason": reason,
                "severity": "blocked",
            }
        )

    # --- 5. verified repo state ---
    repo_status = _avail(repo_verification, "status", "availability")
    sha_raw = repo_verification.get("sha") or repo_verification.get("verified_sha")
    sha = str(sha_raw).strip() if sha_raw else ""
    if repo_status == "verified" and sha:
        verified_sha = sha
        steps_checked.append({"step": "repo_verification", "state": "present"})
    else:
        steps_checked.append({"step": "repo_verification", "state": "missing"})
        if repo_status == "verified" and not sha:
            reason = "repo marked verified but SHA not supplied"
        elif repo_status in {"unverified", "error", ""}:
            reason = f"repo verification {repo_status or 'missing'}"
        else:
            reason = "repo verification failed"
        gaps.append(
            {
                "step": "repo_verification",
                "reason": reason,
                "severity": "blocked",
            }
        )

    # --- 6. minimum relevant DigitalBrain context ---
    vault = _avail(vault_access, "availability", "status")
    context: Optional[Mapping[str, Any]] = None
    if digitalbrain_minimum_context is not None:
        context = digitalbrain_minimum_context
    elif isinstance(vault_access.get("minimum_context"), Mapping):
        context = vault_access["minimum_context"]  # type: ignore[assignment]

    if vault == "available" and context is not None:
        steps_checked.append({"step": "digitalbrain_context", "state": "present"})
    else:
        steps_checked.append({"step": "digitalbrain_context", "state": "missing"})
        if vault != "available":
            gaps.append(
                {
                    "step": "digitalbrain_context",
                    "reason": "vault access unavailable",
                    "severity": "unavailable",
                }
            )
        else:
            gaps.append(
                {
                    "step": "digitalbrain_context",
                    "reason": "minimum DigitalBrain context missing",
                    "severity": "partial",
                }
            )

    status = _resolve_status(gaps)
    bounded_next_action = _bounded_next_action(
        status=status,
        gaps=gaps,
        verified_sha=verified_sha,
        context=context if status == "found" else None,
    )

    result: dict[str, Any] = {
        "status": status,
        "steps_checked": steps_checked,
        "gaps": gaps,
        "bounded_next_action": bounded_next_action,
    }
    if status == "found" and verified_sha:
        result["verified_sha"] = verified_sha
    # Explicitly do not attach invented milestone / vault body fields.
    return result


def _resolve_status(gaps: list[dict[str, str]]) -> str:
    if not gaps:
        return "found"
    worst = "partial"
    for gap in gaps:
        sev = gap["severity"]
        if _SEVERITY_RANK[sev] > _SEVERITY_RANK[worst]:
            worst = sev
    return worst


def _bounded_next_action(
    *,
    status: str,
    gaps: list[dict[str, str]],
    verified_sha: Optional[str],
    context: Optional[Mapping[str, Any]],
) -> str:
    if status == "found":
        # Short success action: cite verified SHA only; never dump context bodies.
        ids = []
        if isinstance(context, Mapping):
            raw_ids = context.get("relevant_ids")
            if isinstance(raw_ids, (list, tuple)):
                ids = [str(x) for x in raw_ids if x is not None]
        id_note = f" ({len(ids)} context id(s))" if ids else ""
        return (
            f"Continue project at verified SHA {verified_sha}{id_note}."
        )

    # Unblock: most severe gap; ties break by STEP_ORDER.
    worst_rank = max(_SEVERITY_RANK[g["severity"]] for g in gaps)
    candidates = [g for g in gaps if _SEVERITY_RANK[g["severity"]] == worst_rank]
    order = {name: i for i, name in enumerate(STEP_ORDER)}
    candidates.sort(key=lambda g: order.get(g["step"], 999))
    step = candidates[0]["step"]
    return _UNBLOCK[step]


def main() -> None:
    """CLI stub for local dry-run with explicit JSON-like kwargs is out of scope.

    This module is meant to be imported by tests and callers that already hold
    injected governance / router / manifest / repo / vault results.
    """
    raise SystemExit(
        "continue_project is a library entrypoint; call continue_project(...) "
        "with injected structured inputs."
    )


if __name__ == "__main__":
    main()
