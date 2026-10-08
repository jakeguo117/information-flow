#!/usr/bin/env python3
"""On-request caller for continue_project.

Grok Bot invokes this when a person or an agent asks to continue a project.
There is no scheduler, webhook, or network client here. The caller reads
only the structured read-back evidence it is given, calls continue_project,
and appends a board event through the injected store.

Project differences live in the adapter JSON. This module does not branch
on a project id literal.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Mapping, Optional
from zoneinfo import ZoneInfo

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import continue_project as cp  # noqa: E402
import status_board as board  # noqa: E402

_FILE_ID = re.compile(r"[A-Za-z0-9_-]{1,128}")
_REVISION = re.compile(r"[A-Za-z0-9._:-]{1,128}")
_REQUEST = re.compile(r"[A-Za-z0-9:_-]{1,80}")
_PAGE = re.compile(r"[A-Za-z0-9:_-]{1,80}")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_SOURCE = re.compile(r"[A-Za-z0-9:./_-]{1,120}")
_SHA256 = board._SHA256
_GIT_SHA = board._GIT_SHA

_PIN_STEPS = (
    "governance",
    "project_control",
    "milestone_map",
    "frozen_authority_or_manifest",
)
_PAGE_FIELD_KEYS = {"page_id", "next_followup", "last_contact"}


def load_adapter(path: Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise board.BoardReject("field_rule")
    _validate_adapter(data)
    return data


def _validate_adapter(adapter: Mapping[str, Any]) -> None:
    required = (
        "project_id",
        "repo_step",
        "effect_key_style",
        "event_format",
        "event_prefix",
        "writer",
        "event_kinds",
        "continue_event_kind",
        "blocked_event_kind",
        "success_template",
        "unblock",
        "allowed_event_fields",
        "status_codes",
        "context_kind",
        "timezone",
        "board_schema_version",
    )
    for key in required:
        if key not in adapter:
            raise board.BoardReject("field_rule")
    if adapter["repo_step"] not in {"required", "skip"}:
        raise board.BoardReject("field_rule")
    if adapter["effect_key_style"] not in {"continue", "followup"}:
        raise board.BoardReject("field_rule")
    if adapter["event_format"] not in {"json", "markdown"}:
        raise board.BoardReject("field_rule")
    if adapter["context_kind"] not in {"ids", "pages"}:
        raise board.BoardReject("field_rule")
    if adapter["board_schema_version"] != board.SCHEMA["board_schema_version"]:
        raise board.BoardReject("field_rule")
    unblock = adapter["unblock"]
    if not isinstance(unblock, Mapping):
        raise board.BoardReject("field_rule")
    for step in (*cp.STEP_ORDER, "project_id"):
        if not isinstance(unblock.get(step), str) or not unblock[step]:
            raise board.BoardReject("field_rule")
    if adapter["continue_event_kind"] not in adapter["event_kinds"]:
        raise board.BoardReject("field_rule")
    if adapter["blocked_event_kind"] not in adapter["event_kinds"]:
        raise board.BoardReject("field_rule")
    if adapter["context_kind"] == "pages":
        codes = adapter["status_codes"]
        for key in ("no_date", "due", "overdue", "future"):
            if key not in codes:
                raise board.BoardReject("field_rule")
        for kind in ("SCOPE-SNAPSHOT", "FOLLOWUP-DUE"):
            if kind not in adapter["event_kinds"]:
                raise board.BoardReject("field_rule")
        no_date_kind = adapter.get("no_date_event_kind") or "PENDING-NO-DATE"
        if no_date_kind not in adapter["event_kinds"]:
            raise board.BoardReject("field_rule")
    identity = {
        "event_id",
        "project_id",
        "event_kind",
        "occurred_at",
        "writer",
        "invocation",
        "request_ref",
        "effect_key",
        "supersedes",
        "result",
    }
    if not identity <= set(adapter["allowed_event_fields"]):
        raise board.BoardReject("field_rule")


def continue_for_project(
    *,
    project_id: str,
    adapter: Mapping[str, Any],
    readbacks: Mapping[str, Any],
    request_ref: str,
    board_store: Optional[board.BoardStore] = None,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    """Run one on-request continuation and optionally append board events."""
    _validate_adapter(adapter)
    if not isinstance(project_id, str) or not project_id.strip():
        return _identity_block(adapter, project_id if isinstance(project_id, str) else "")
    project_id = project_id.strip()
    if project_id != adapter["project_id"]:
        return _identity_block(adapter, project_id)
    if not isinstance(request_ref, str) or _REQUEST.fullmatch(request_ref) is None:
        return _blocked_result(
            adapter,
            project_id,
            reason_code="field_rule",
            step="project_id",
        )
    if not isinstance(readbacks, Mapping) or board.contains_forbidden(readbacks):
        return _finish_blocked(
            adapter,
            project_id,
            request_ref,
            reason_code="field_rule",
            step="digitalbrain_context",
            board_store=board_store,
            now=now,
            pins=[],
            pages=[],
        )
    if _foreign_project_id(readbacks, project_id):
        return _identity_block(adapter, project_id)

    moment = _shanghai(now, str(adapter["timezone"]))
    assembled = _assemble(project_id, adapter, readbacks)
    if assembled["tainted"]:
        return _finish_blocked(
            adapter,
            project_id,
            request_ref,
            reason_code="field_rule",
            step="digitalbrain_context",
            board_store=board_store,
            now=moment,
            pins=[],
            pages=[],
        )
    core = cp.continue_project(project_id=project_id, **assembled["core"])
    gaps = _caller_gaps(core["gaps"], adapter)
    status = core["status"]
    counts = assembled["counts"]
    if status == "found":
        action = _success_action(adapter, core, counts, assembled["page_ids"])
    else:
        action = _unblock_action(adapter, gaps)

    result: dict[str, Any] = {
        "project_id": project_id,
        "status": status,
        "steps_checked": core["steps_checked"],
        "gaps": gaps,
        "bounded_next_action": action,
        "consumed_pins": assembled["pins"],
        "counts": counts,
        "board_writes": [],
        "board_readback": [],
    }
    if "verified_sha" in core:
        result["verified_sha"] = core["verified_sha"]
    if assembled["code_ref"]:
        result["code_ref"] = assembled["code_ref"]

    if board_store is not None:
        _append_events(
            result,
            adapter=adapter,
            request_ref=request_ref,
            moment=moment,
            pins=assembled["pins"],
            pages=assembled["pages"],
            groups=assembled["groups"],
            authority_ref=assembled["authority_ref"],
            code_ref=assembled["code_ref"],
            reason_code=_reason_code(status, assembled, gaps),
            store=board_store,
        )
    return result


def _identity_block(adapter: Mapping[str, Any], project_id: str) -> dict[str, Any]:
    reason = str(adapter["unblock"]["project_id"])
    return {
        "project_id": project_id,
        "status": "blocked",
        "steps_checked": [],
        "gaps": [{"step": "project_id", "reason": reason, "severity": "blocked"}],
        "bounded_next_action": reason,
        "consumed_pins": [],
        "counts": {"context_count": 0, "due_count": 0, "no_date_count": 0},
        "board_writes": [],
        "board_readback": [],
    }


def _blocked_result(
    adapter: Mapping[str, Any],
    project_id: str,
    *,
    reason_code: str,
    step: str,
) -> dict[str, Any]:
    reason = str(adapter["unblock"].get(step) or adapter["unblock"]["project_id"])
    return {
        "project_id": project_id,
        "status": "blocked",
        "steps_checked": [],
        "gaps": [{"step": step, "reason": reason, "severity": "blocked"}],
        "bounded_next_action": reason,
        "consumed_pins": [],
        "counts": {"context_count": 0, "due_count": 0, "no_date_count": 0},
        "reason_code": reason_code,
        "board_writes": [],
        "board_readback": [],
    }


def _finish_blocked(
    adapter: Mapping[str, Any],
    project_id: str,
    request_ref: str,
    *,
    reason_code: str,
    step: str,
    board_store: Optional[board.BoardStore],
    now: Optional[datetime],
    pins: list[dict[str, Any]],
    pages: list[dict[str, Any]],
) -> dict[str, Any]:
    result = _blocked_result(adapter, project_id, reason_code=reason_code, step=step)
    if board_store is not None and isinstance(request_ref, str) and _REQUEST.fullmatch(request_ref):
        moment = _shanghai(now, str(adapter["timezone"]))
        _append_events(
            result,
            adapter=adapter,
            request_ref=request_ref,
            moment=moment,
            pins=pins,
            pages=[],
            groups={},
            authority_ref=None,
            code_ref=None,
            reason_code=reason_code,
            store=board_store,
            force_blocked=True,
        )
    return result


def _shanghai(now: Optional[datetime], timezone_name: str) -> datetime:
    zone = ZoneInfo(timezone_name)
    if now is None:
        current = datetime.now(zone)
    elif now.utcoffset() is None:
        current = now.replace(tzinfo=zone)
    else:
        current = now.astimezone(zone)
    if current.utcoffset() != timedelta(hours=8):
        raise board.BoardReject("field_rule")
    return current.replace(microsecond=0)


def _foreign_project_id(value: Any, project_id: str) -> bool:
    found: list[str] = []
    _collect_project_ids(value, found)
    return any(item != project_id for item in found)


def _collect_project_ids(value: Any, found: list[str]) -> None:
    if isinstance(value, Mapping):
        marker = value.get("project_id")
        if isinstance(marker, str):
            found.append(marker)
        for item in value.values():
            _collect_project_ids(item, found)
    elif isinstance(value, list):
        for item in value:
            _collect_project_ids(item, found)


def _assemble(
    project_id: str,
    adapter: Mapping[str, Any],
    readbacks: Mapping[str, Any],
) -> dict[str, Any]:
    pins: list[dict[str, Any]] = []
    core: dict[str, Any] = {}
    for step in ("governance", "project_control", "milestone_map"):
        pin = _document_pin(readbacks.get(step), project_id, step)
        if pin is None:
            core[step] = {"availability": "absent"}
        else:
            pin["match"] = True
            pins.append(pin)
            core[step] = {"availability": "present"}

    manifest_state, manifest_sha, manifest_code = _manifest(
        readbacks.get("frozen_authority_or_manifest"),
        project_id,
        pins,
    )
    core["frozen_authority_or_manifest"] = manifest_state

    code_ref = None
    if adapter["repo_step"] == "skip":
        core["repo_verification"] = {"required": False}
        code_ref = _optional_git_sha(readbacks.get("code_ref"), project_id)
    else:
        sha = _optional_git_sha(readbacks.get("repo_verification"), project_id)
        if sha:
            core["repo_verification"] = {"status": "verified", "sha": sha}
            code_ref = sha
        else:
            core["repo_verification"] = {"status": "unverified"}

    context_pin = _document_pin(readbacks.get("context"), project_id, "digitalbrain_context")
    pages: list[dict[str, Any]] = []
    groups: dict[str, list[dict[str, Any]]] = {}
    relevant_ids: list[str] = []
    counts = {"context_count": 0, "due_count": 0, "no_date_count": 0}
    context_mapping: Optional[dict[str, Any]] = None
    context_body = readbacks.get("context")
    tainted = False
    if context_pin is None or not isinstance(context_body, Mapping):
        core["vault_access"] = {"availability": "unavailable"}
    else:
        context_pin["match"] = True
        pins.append(context_pin)
        if adapter["context_kind"] == "pages":
            pages, tainted = _pages(context_body, adapter)
            relevant_ids = [item["page_id"] for item in pages]
            groups = _groups(pages)
            counts["due_count"] = len(groups.get("due", []))
            counts["no_date_count"] = len(groups.get("no_date", []))
        else:
            raw_ids = context_body.get("relevant_ids")
            if isinstance(raw_ids, list):
                relevant_ids = [
                    item
                    for item in raw_ids
                    if isinstance(item, str) and _PAGE.fullmatch(item)
                ]
                if len(relevant_ids) != len(raw_ids):
                    tainted = True
                    relevant_ids = []
        counts["context_count"] = len(relevant_ids)
        if relevant_ids and not tainted:
            context_mapping = {"relevant_ids": relevant_ids}
            core["vault_access"] = {"availability": "available"}
        elif tainted:
            core["vault_access"] = {"availability": "unavailable"}
        else:
            core["vault_access"] = {"availability": "available"}

    if context_mapping is not None:
        core["digitalbrain_minimum_context"] = context_mapping

    return {
        "core": core,
        "pins": pins,
        "pages": pages,
        "groups": groups,
        "counts": counts,
        "authority_ref": manifest_sha,
        "code_ref": code_ref,
        "manifest_matched": manifest_state.get("approved") is True,
        "manifest_present": manifest_state.get("availability") == "present",
        "manifest_code": manifest_code,
        "page_ids": relevant_ids,
        "tainted": tainted,
    }


def _document_pin(readback: Any, project_id: str, step: str) -> Optional[dict[str, Any]]:
    """A self-reported present/approved flag is not evidence."""
    if not isinstance(readback, Mapping):
        return None
    if readback.get("readable") is not True:
        return None
    if readback.get("project_id") != project_id:
        return None
    revision = readback.get("revision")
    sha = readback.get("sha256")
    if not isinstance(revision, str) or _REVISION.fullmatch(revision) is None:
        return None
    if not isinstance(sha, str) or _SHA256.fullmatch(sha) is None:
        return None
    file_id = readback.get("drive_file_id")
    source_ref = readback.get("source_ref")
    if step in {"governance", "project_control", "frozen_authority_or_manifest"}:
        if not isinstance(file_id, str) or _FILE_ID.fullmatch(file_id) is None:
            return None
    elif file_id is None and source_ref is None:
        return None
    pin: dict[str, Any] = {
        "step": step,
        "project_id": project_id,
        "revision": revision,
        "sha256": sha,
        "match": False,
    }
    if isinstance(file_id, str):
        pin["drive_file_id"] = file_id
    if isinstance(source_ref, str) and _SOURCE.fullmatch(source_ref):
        pin["source_ref"] = source_ref
    return pin


def _manifest(
    readback: Any,
    project_id: str,
    pins: list[dict[str, Any]],
) -> tuple[dict[str, Any], Optional[str], str]:
    pin = _document_pin(readback, project_id, "frozen_authority_or_manifest")
    if pin is None or not isinstance(readback, Mapping):
        return {"availability": "absent", "approved": False}, None, "absent"
    approval = readback.get("approval")
    approval_pin = (
        _document_pin(approval, project_id, "approval")
        if isinstance(approval, Mapping)
        else None
    )
    hashes_match = (
        readback.get("expected_revision") == readback.get("revision")
        and readback.get("expected_sha256") == readback.get("sha256")
    )
    matched = hashes_match and approval_pin is not None
    pin["match"] = matched
    pins.append(pin)
    if approval_pin is not None:
        approval_pin["match"] = matched
        pins.append(approval_pin)
    sha = str(readback.get("sha256"))
    if matched:
        return {"availability": "present", "approved": True}, sha, "matched"
    if hashes_match:
        return {"availability": "present", "approved": False}, sha, "not_approved"
    return {"availability": "present", "approved": False}, sha, "mismatch"


def _optional_git_sha(readback: Any, project_id: str) -> Optional[str]:
    if not isinstance(readback, Mapping):
        return None
    if readback.get("readable") is not True or readback.get("project_id") != project_id:
        return None
    sha = readback.get("sha")
    if isinstance(sha, str) and _GIT_SHA.fullmatch(sha):
        return sha
    return None


def _pages(
    readback: Mapping[str, Any],
    adapter: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], bool]:
    as_of = readback.get("as_of")
    raw_pages = readback.get("pages")
    source_ref = readback.get("source_ref")
    if not isinstance(source_ref, str) or _SOURCE.fullmatch(source_ref) is None:
        return [], False
    if not isinstance(as_of, str) or _DATE.fullmatch(as_of) is None:
        return [], False
    if not isinstance(raw_pages, list):
        return [], False
    codes = adapter["status_codes"]
    pages: list[dict[str, Any]] = []
    for item in raw_pages:
        if not isinstance(item, Mapping) or set(item) - _PAGE_FIELD_KEYS:
            return [], True
        page_id = item.get("page_id")
        if not isinstance(page_id, str) or _PAGE.fullmatch(page_id) is None:
            return [], True
        nxt = item.get("next_followup")
        last = item.get("last_contact")
        if not _date_or_null(nxt) or not _date_or_null(last):
            return [], True
        status = _status_code(nxt, as_of, codes)
        pages.append(
            {
                "page_id": page_id,
                "next_followup": nxt,
                "last_contact": last,
                "followup_status": status,
                "bucket": _bucket(nxt, as_of),
                "source_ref": source_ref,
            }
        )
    return pages, False


def _date_or_null(value: Any) -> bool:
    return value is None or (isinstance(value, str) and _DATE.fullmatch(value) is not None)


def _bucket(next_followup: Any, as_of: str) -> str:
    if next_followup is None:
        return "no_date"
    if not isinstance(next_followup, str):
        return "no_date"
    if next_followup < as_of:
        return "overdue"
    if next_followup == as_of:
        return "due"
    return "future"


def _status_code(next_followup: Any, as_of: str, codes: Mapping[str, str]) -> str:
    return str(codes[_bucket(next_followup, as_of)])


def _groups(pages: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {
        "due": [],
        "no_date": [],
        "future": [],
    }
    for page in pages:
        bucket = page["bucket"]
        if bucket == "overdue":
            grouped["due"].append(page)
        elif bucket in grouped:
            grouped[bucket].append(page)
    return grouped


def _caller_gaps(gaps: list[dict[str, str]], adapter: Mapping[str, Any]) -> list[dict[str, str]]:
    rendered = []
    for gap in gaps:
        step = gap["step"]
        rendered.append(
            {
                "step": step,
                "reason": str(adapter["unblock"].get(step, "Step is not ready.")),
                "severity": gap["severity"],
            }
        )
    return rendered


def _success_action(
    adapter: Mapping[str, Any],
    core: Mapping[str, Any],
    counts: Mapping[str, int],
    page_ids: list[str],
) -> str:
    action = str(adapter["success_template"]).format(
        verified_sha=str(core.get("verified_sha") or ""),
        context_count=counts["context_count"],
        due_count=counts["due_count"],
    )
    if board.contains_forbidden(action) or any(page_id and page_id in action for page_id in page_ids):
        return "Continue project."
    if len(action) > 200:
        return "Continue project."
    return action


def _unblock_action(adapter: Mapping[str, Any], gaps: list[dict[str, str]]) -> str:
    if not gaps:
        return "Continue project."
    worst = max(cp._SEVERITY_RANK[gap["severity"]] for gap in gaps)
    candidates = [gap for gap in gaps if cp._SEVERITY_RANK[gap["severity"]] == worst]
    order = {name: index for index, name in enumerate(cp.STEP_ORDER)}
    candidates.sort(key=lambda gap: order.get(gap["step"], 999))
    return candidates[0]["reason"]


def _reason_code(
    status: str,
    assembled: Mapping[str, Any],
    gaps: list[dict[str, str]],
) -> Optional[str]:
    if status == "found":
        return None
    steps = {gap["step"] for gap in gaps}
    if "frozen_authority_or_manifest" in steps:
        if assembled["manifest_present"] and not assembled["manifest_matched"]:
            approval_missing = assembled.get("manifest_code") == "not_approved"
            if approval_missing:
                return "not_approved"
            return "manifest_mismatch"
        return "missing_evidence"
    if "repo_verification" in steps:
        return "repo_unverified"
    if "digitalbrain_context" in steps and any(
        gap["step"] == "digitalbrain_context" and gap["severity"] == "unavailable" for gap in gaps
    ):
        return "source_unreadable"
    return "missing_evidence"


def _append_events(
    result: dict[str, Any],
    *,
    adapter: Mapping[str, Any],
    request_ref: str,
    moment: datetime,
    pins: list[dict[str, Any]],
    pages: list[dict[str, Any]],
    groups: Mapping[str, list[dict[str, Any]]],
    authority_ref: Optional[str],
    code_ref: Optional[str],
    reason_code: Optional[str],
    store: board.BoardStore,
    force_blocked: bool = False,
) -> None:
    stamp = moment.strftime("%Y%m%dT%H%M%S")
    occurred = moment.isoformat(timespec="seconds")
    business_date = moment.date().isoformat()
    drafts = _drafts(
        result=result,
        adapter=adapter,
        request_ref=request_ref,
        occurred=occurred,
        business_date=business_date,
        pins=pins,
        pages=pages,
        groups=groups,
        authority_ref=authority_ref,
        code_ref=code_ref,
        reason_code=reason_code,
        force_blocked=force_blocked,
    )
    for draft in drafts:
        written = board.write_event(store, draft, adapter, stamp=stamp)
        result["board_writes"].append(
            {
                "result": written["result"],
                "wrote": written["wrote"],
                "event_id": written["event"]["event_id"],
                "effect_key": written["event"]["effect_key"],
                "name": written["name"],
            }
        )
        if written["name"]:
            result["board_readback"].append(board.parse_event(store.read_text(written["name"])))


def _drafts(
    *,
    result: Mapping[str, Any],
    adapter: Mapping[str, Any],
    request_ref: str,
    occurred: str,
    business_date: str,
    pins: list[dict[str, Any]],
    pages: list[dict[str, Any]],
    groups: Mapping[str, list[dict[str, Any]]],
    authority_ref: Optional[str],
    code_ref: Optional[str],
    reason_code: Optional[str],
    force_blocked: bool,
) -> list[dict[str, Any]]:
    if force_blocked or result["status"] != "found":
        return [
            _shell(
                adapter=adapter,
                kind=str(adapter["blocked_event_kind"]),
                request_ref=request_ref,
                occurred=occurred,
                business_date=business_date,
                pins=pins,
                authority_ref=authority_ref,
                code_ref=code_ref,
                result_code="blocked",
                reason_code=reason_code or "missing_evidence",
                status=str(result["status"]),
                gaps=list(result["gaps"]),
                page_rows=[],
            )
        ]
    if adapter["context_kind"] != "pages":
        return [
            _shell(
                adapter=adapter,
                kind=str(adapter["continue_event_kind"]),
                request_ref=request_ref,
                occurred=occurred,
                business_date=business_date,
                pins=pins,
                authority_ref=authority_ref,
                code_ref=code_ref,
                result_code="ok",
                reason_code=None,
                status=str(result["status"]),
                gaps=[],
                page_rows=[],
            )
        ]
    drafts: list[dict[str, Any]] = []
    if pages:
        drafts.append(
            _shell(
                adapter=adapter,
                kind="SCOPE-SNAPSHOT",
                request_ref=request_ref,
                occurred=occurred,
                business_date=business_date,
                pins=pins,
                authority_ref=authority_ref,
                code_ref=code_ref,
                result_code="ok",
                reason_code=None,
                status="found",
                gaps=[],
                page_rows=pages,
            )
        )
    due_rows = list(groups.get("due") or [])
    if due_rows:
        drafts.append(
            _shell(
                adapter=adapter,
                kind="FOLLOWUP-DUE",
                request_ref=request_ref,
                occurred=occurred,
                business_date=business_date,
                pins=pins,
                authority_ref=authority_ref,
                code_ref=code_ref,
                result_code="ok",
                reason_code=None,
                status="found",
                gaps=[],
                page_rows=due_rows,
            )
        )
    missing_rows = list(groups.get("no_date") or [])
    if missing_rows:
        drafts.append(
            _shell(
                adapter=adapter,
                kind=str(adapter.get("no_date_event_kind") or "PENDING-NO-DATE"),
                request_ref=request_ref,
                occurred=occurred,
                business_date=business_date,
                pins=pins,
                authority_ref=authority_ref,
                code_ref=code_ref,
                result_code="ok",
                reason_code=None,
                status="found",
                gaps=[],
                page_rows=missing_rows,
            )
        )
    return drafts


def _shell(
    *,
    adapter: Mapping[str, Any],
    kind: str,
    request_ref: str,
    occurred: str,
    business_date: str,
    pins: list[dict[str, Any]],
    authority_ref: Optional[str],
    code_ref: Optional[str],
    result_code: str,
    reason_code: Optional[str],
    status: str,
    gaps: list[dict[str, str]],
    page_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    project_id = str(adapter["project_id"])
    page_ids = [row["page_id"] for row in page_rows]
    status_codes = [row["followup_status"] for row in page_rows]
    if adapter["effect_key_style"] == "followup":
        effect_key = board.effect_key_followup(
            project_id=project_id,
            event_kind=kind,
            page_ids=page_ids,
            business_date=business_date,
            status_codes=status_codes,
        )
    else:
        effect_key = board.effect_key_continue(
            project_id=project_id,
            authority_ref=authority_ref or "none",
            event_kind=kind,
            session_id=request_ref,
        )
    compact = _compact_stamp(occurred)
    event_id = f"{adapter['event_prefix']}-{compact}-{kind}-{effect_key[:8]}"
    event: dict[str, Any] = {
        "event_id": event_id,
        "project_id": project_id,
        "event_kind": kind,
        "occurred_at": occurred,
        "writer": adapter["writer"],
        "invocation": "on_request",
        "request_ref": request_ref,
        "effect_key": effect_key,
        "supersedes": None,
        "result": result_code,
    }
    allowed = set(adapter["allowed_event_fields"])
    if "reason_code" in allowed and reason_code:
        event["reason_code"] = reason_code
    if "consumed_pins" in allowed:
        event["consumed_pins"] = pins
    if "code_ref" in allowed and code_ref:
        event["code_ref"] = code_ref
    if "authority_ref" in allowed and authority_ref:
        event["authority_ref"] = authority_ref
    if "status" in allowed:
        event["status"] = status
    if "gap_steps" in allowed and gaps:
        event["gap_steps"] = [
            {"step": gap["step"], "severity": gap["severity"]} for gap in gaps if gap["step"] in board.GAP_STEPS
        ]
    if page_rows and result_code != "blocked":
        event["crm_source"] = page_rows[0]["source_ref"]
        event["crm_read_at"] = occurred
        event["crm_page_ids"] = page_ids
        event["followup_status"] = {
            row["page_id"]: row["followup_status"] for row in page_rows
        }
        event["dates"] = {
            row["page_id"]: {
                "next_followup": row["next_followup"],
                "last_contact": row["last_contact"],
            }
            for row in page_rows
        }
    return {key: value for key, value in event.items() if key in allowed}


def _compact_stamp(occurred: str) -> str:
    # 2026-10-08T15:15:00+08:00 -> 20261008T151500
    day = occurred[:10].replace("-", "")
    clock = occurred[11:19].replace(":", "")
    return f"{day}T{clock}"


def main(argv: Optional[list[str]] = None) -> int:
    """JSON on stdin, JSON on stdout. Local board directory only."""
    parser = argparse.ArgumentParser(description="On-request continue_project caller")
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--board-dir", required=True)
    args = parser.parse_args(argv)
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        sys.stdout.write(json.dumps({"status": "blocked", "error": "invalid_json"}) + "\n")
        return 1
    if not isinstance(payload, dict):
        sys.stdout.write(json.dumps({"status": "blocked", "error": "invalid_json"}) + "\n")
        return 1
    try:
        adapter = load_adapter(Path(args.adapter))
        store = board.LocalDirectoryBoardStore(Path(args.board_dir))
        moment = None
        if payload.get("occurred_at"):
            moment = datetime.fromisoformat(str(payload["occurred_at"]))
        result = continue_for_project(
            project_id=str(payload.get("project_id") or ""),
            adapter=adapter,
            readbacks=payload.get("readbacks") if isinstance(payload.get("readbacks"), dict) else {},
            request_ref=str(payload.get("request_ref") or ""),
            board_store=store,
            now=moment,
        )
    except board.BoardError as exc:
        sys.stdout.write(json.dumps({"status": "blocked", "reason_code": exc.reason_code}) + "\n")
        return 1
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
