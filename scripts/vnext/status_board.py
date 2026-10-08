#!/usr/bin/env python3
"""Append-only status board.

Pure validation, replay, and serialization. I/O goes through a store.
The local directory store is for tests and for a caller that already holds
files. The Drive store is an unwired stub: it has no credentials and it
does not open a network connection.

This module does not name a project. Adapters supply the project id, the
allowed event kinds, the writer, and which event fields are in use.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping, Optional, Protocol

SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "board-0.1.json"
SCHEMA: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

EVENT_KEYS = set(SCHEMA["event_keys"])
HEADER_KEYS = set(SCHEMA["header_keys"])
PIN_KEYS = set(SCHEMA["pin_keys"])
AUTHORITY_PIN_KEYS = set(SCHEMA["authority_pin_keys"])
DATE_KEYS = set(SCHEMA["date_keys"])
GAP_KEYS = set(SCHEMA["gap_keys"])
DENY_KEYS = set(SCHEMA["deny_keys"])
RESULTS = set(SCHEMA["results"])
INVOCATIONS = set(SCHEMA["invocations"])
REASON_CODES = set(SCHEMA["reason_codes"])
CONTINUE_STATUSES = set(SCHEMA["continue_statuses"])
GAP_STEPS = set(SCHEMA["gap_steps"])
SEVERITIES = set(SCHEMA["severities"])

_SHA256 = re.compile(r"[0-9a-f]{64}")
_GIT_SHA = re.compile(r"[0-9a-f]{40}")
_PAGE_ID = re.compile(r"[A-Za-z0-9:_-]{1,80}")
_ITEM_REF = re.compile(r"check-[0-9]+|track:[A-Z]")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_SAFE_NAME = re.compile(r"[A-Za-z0-9._-]{1,180}")
_HEX_ONLY = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")


class BoardError(Exception):
    """Base error. Messages stay on reason codes, not on caller values."""

    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


class BoardReject(BoardError):
    """The event is not on the whitelist. Nothing was written."""


class BoardBackendError(BoardError):
    """The store cannot be used. The Drive stub always raises this."""

    def __init__(self, reason_code: str = "backend_unwired") -> None:
        super().__init__(reason_code)


class BoardStore(Protocol):
    def list_names(self) -> list[str]:
        ...

    def read_text(self, name: str) -> str:
        ...

    def write_new(self, name: str, text: str) -> None:
        ...


def effect_key_continue(
    *,
    project_id: str,
    authority_ref: str,
    event_kind: str,
    session_id: str,
    item_ref: Optional[str] = None,
) -> str:
    """SHA-256 of project, authority, kind, optional item, and session."""
    parts = [project_id, authority_ref, event_kind]
    if item_ref:
        parts.append(item_ref)
    parts.append(session_id)
    return _sha256_text("|".join(parts))


def effect_key_followup(
    *,
    project_id: str,
    event_kind: str,
    page_ids: list[str],
    business_date: str,
    status_codes: list[str],
) -> str:
    """SHA-256 of project, kind, sorted page ids, business date, status set.

    business_date is the Asia/Shanghai calendar date (YYYY-MM-DD).
    Status codes are sorted unique values. Page ids are sorted.
    """
    pages = ",".join(sorted(page_ids))
    statuses = ",".join(sorted(set(status_codes)))
    material = "|".join(
        [project_id, event_kind, pages, business_date, statuses]
    )
    return _sha256_text(material)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def contains_forbidden(value: Any) -> bool:
    """True when a tree holds a denied key or a contact-shaped string."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in DENY_KEYS or contains_forbidden(item):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(contains_forbidden(item) for item in value)
    if isinstance(value, str):
        return _contact_shaped(value)
    return False


def _contact_shaped(value: str) -> bool:
    if _HEX_ONLY.fullmatch(value):
        return False
    if "@" in value:
        return True
    if re.search(r"\+\d{8,15}", value):
        return True
    if re.search(r"(?<![A-Za-z0-9])\d{11,}(?![A-Za-z0-9])", value):
        return True
    return False


def _reject_unknown(keys: set[str], allowed: set[str]) -> None:
    if keys - allowed:
        raise BoardReject("field_rule")


def _require_str(event: Mapping[str, Any], key: str, pattern: re.Pattern[str]) -> str:
    value = event.get(key)
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise BoardReject("field_rule")
    return value


def validate_event(event: Mapping[str, Any], adapter: Mapping[str, Any]) -> None:
    """Reject anything outside the adapter field whitelist and the schema."""
    if not isinstance(event, Mapping):
        raise BoardReject("field_rule")
    if contains_forbidden(event):
        raise BoardReject("field_rule")
    allowed = set(adapter.get("allowed_event_fields") or [])
    if not allowed or not allowed <= EVENT_KEYS:
        raise BoardReject("field_rule")
    _reject_unknown(set(event), allowed)

    project_id = _require_str(event, "project_id", re.compile(r"[A-Za-z0-9-]{1,80}"))
    if project_id != adapter.get("project_id"):
        raise BoardReject("project_mismatch")
    kind = event.get("event_kind")
    if kind not in set(adapter.get("event_kinds") or []):
        raise BoardReject("field_rule")
    if event.get("writer") != adapter.get("writer"):
        raise BoardReject("ownership_violation")
    if event.get("invocation") not in INVOCATIONS:
        raise BoardReject("field_rule")
    _require_str(event, "event_id", _SAFE_NAME)
    _require_str(event, "effect_key", _SHA256)
    _require_str(event, "request_ref", re.compile(r"[A-Za-z0-9:_-]{1,80}"))
    occurred = event.get("occurred_at")
    if not isinstance(occurred, str) or not occurred.endswith("+08:00"):
        raise BoardReject("field_rule")
    result = event.get("result")
    if result not in RESULTS:
        raise BoardReject("field_rule")
    if "reason_code" in event and event["reason_code"] is not None:
        if event["reason_code"] not in REASON_CODES:
            raise BoardReject("field_rule")
    supersedes = event.get("supersedes")
    if kind == "CORRECTION":
        if not isinstance(supersedes, str) or not supersedes:
            raise BoardReject("field_rule")
    elif supersedes not in (None,):
        if "supersedes" in event and supersedes is not None:
            raise BoardReject("field_rule")

    if "consumed_pins" in event:
        _validate_pins(event["consumed_pins"], project_id)
    if "crm_page_ids" in event or "followup_status" in event or "dates" in event:
        _validate_pages(event, adapter)
    if "item_refs" in event:
        _validate_item_refs(event["item_refs"])
    if "status" in event and event["status"] not in CONTINUE_STATUSES:
        raise BoardReject("field_rule")
    if "gap_steps" in event:
        _validate_gaps(event["gap_steps"])
    if "code_ref" in event and event["code_ref"] is not None:
        if not isinstance(event["code_ref"], str) or _GIT_SHA.fullmatch(event["code_ref"]) is None:
            raise BoardReject("field_rule")
    if "authority_ref" in event and event["authority_ref"] is not None:
        if not isinstance(event["authority_ref"], str) or _SHA256.fullmatch(event["authority_ref"]) is None:
            raise BoardReject("field_rule")
    if "crm_source" in event:
        if not isinstance(event["crm_source"], str) or re.fullmatch(r"[A-Za-z0-9:./_-]{1,120}", event["crm_source"]) is None:
            raise BoardReject("field_rule")
    if "crm_read_at" in event:
        if not isinstance(event["crm_read_at"], str) or not event["crm_read_at"].endswith("+08:00"):
            raise BoardReject("field_rule")
    if result == "blocked":
        for key in ("crm_page_ids", "followup_status", "dates", "crm_source"):
            if key in event:
                raise BoardReject("field_rule")


def _validate_pins(pins: Any, project_id: str) -> None:
    if not isinstance(pins, list):
        raise BoardReject("field_rule")
    for pin in pins:
        if not isinstance(pin, Mapping):
            raise BoardReject("field_rule")
        _reject_unknown(set(pin), PIN_KEYS)
        if pin.get("project_id") != project_id:
            raise BoardReject("project_mismatch")
        if pin.get("step") not in GAP_STEPS and pin.get("step") != "approval":
            raise BoardReject("field_rule")
        if not isinstance(pin.get("match"), bool):
            raise BoardReject("field_rule")
        for key in ("revision", "sha256"):
            if key not in pin:
                raise BoardReject("field_rule")
        if not isinstance(pin["sha256"], str) or _SHA256.fullmatch(pin["sha256"]) is None:
            raise BoardReject("field_rule")
        if not isinstance(pin["revision"], str) or not pin["revision"]:
            raise BoardReject("field_rule")


def _validate_pages(event: Mapping[str, Any], adapter: Mapping[str, Any]) -> None:
    page_ids = event.get("crm_page_ids")
    if not isinstance(page_ids, list) or not page_ids:
        raise BoardReject("field_rule")
    if any(not isinstance(item, str) or _PAGE_ID.fullmatch(item) is None for item in page_ids):
        raise BoardReject("field_rule")
    allowed_codes = set((adapter.get("status_codes") or {}).values())
    status_map = event.get("followup_status")
    if not isinstance(status_map, Mapping):
        raise BoardReject("field_rule")
    _reject_unknown(set(status_map), set(page_ids))
    for key, code in status_map.items():
        if code not in allowed_codes:
            raise BoardReject("field_rule")
    dates = event.get("dates")
    if not isinstance(dates, Mapping):
        raise BoardReject("field_rule")
    _reject_unknown(set(dates), set(page_ids))
    for page_id, fields in dates.items():
        if not isinstance(fields, Mapping):
            raise BoardReject("field_rule")
        _reject_unknown(set(fields), DATE_KEYS)
        for key in DATE_KEYS:
            if key not in fields:
                raise BoardReject("field_rule")
            value = fields[key]
            if value is None:
                continue
            if not isinstance(value, str) or _DATE.fullmatch(value) is None:
                raise BoardReject("field_rule")


def _validate_item_refs(value: Any) -> None:
    if not isinstance(value, list):
        raise BoardReject("field_rule")
    for item in value:
        if not isinstance(item, str) or _ITEM_REF.fullmatch(item) is None:
            raise BoardReject("field_rule")


def _validate_gaps(value: Any) -> None:
    if not isinstance(value, list):
        raise BoardReject("field_rule")
    for item in value:
        if not isinstance(item, Mapping):
            raise BoardReject("field_rule")
        _reject_unknown(set(item), GAP_KEYS)
        if item.get("step") not in GAP_STEPS or item.get("severity") not in SEVERITIES:
            raise BoardReject("field_rule")


def validate_header(header: Mapping[str, Any], adapter: Mapping[str, Any]) -> None:
    if not isinstance(header, Mapping) or contains_forbidden(header):
        raise BoardReject("field_rule")
    _reject_unknown(set(header), HEADER_KEYS)
    if header.get("project_id") != adapter.get("project_id"):
        raise BoardReject("project_mismatch")
    if header.get("board_schema_version") != SCHEMA["board_schema_version"]:
        raise BoardReject("field_rule")
    if header.get("writer") != adapter.get("writer"):
        raise BoardReject("ownership_violation")
    if header.get("invocation") not in INVOCATIONS:
        raise BoardReject("field_rule")
    _require_str(header, "effect_key", _SHA256)
    written = header.get("written_at")
    if not isinstance(written, str) or not written.endswith("+08:00"):
        raise BoardReject("field_rule")
    pins = header.get("authority_pins")
    if not isinstance(pins, list):
        raise BoardReject("field_rule")
    for pin in pins:
        if not isinstance(pin, Mapping):
            raise BoardReject("field_rule")
        _reject_unknown(set(pin), AUTHORITY_PIN_KEYS)
        if not isinstance(pin.get("sha256"), str) or _SHA256.fullmatch(pin["sha256"]) is None:
            raise BoardReject("field_rule")
    if "code_ref" in header and header["code_ref"] is not None:
        if not isinstance(header["code_ref"], str) or _GIT_SHA.fullmatch(header["code_ref"]) is None:
            raise BoardReject("field_rule")


def event_filename(adapter: Mapping[str, Any], stamp: str, kind: str, effect_key: str) -> str:
    ext = "md" if adapter.get("event_format") == "markdown" else "json"
    name = f"{adapter['event_prefix']}-{stamp}-{kind}-{effect_key[:8]}.{ext}"
    if _SAFE_NAME.fullmatch(name) is None or "/" in name or ".." in name:
        raise BoardReject("field_rule")
    return name


def header_filename(stamp: str, effect_key: str) -> str:
    name = f"BOARD-HEADER-{stamp}-{effect_key[:8]}.json"
    if _SAFE_NAME.fullmatch(name) is None:
        raise BoardReject("field_rule")
    return name


def serialize_event(event: Mapping[str, Any], event_format: str) -> str:
    payload = json.dumps(event, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if event_format == "json":
        return payload
    if event_format == "markdown":
        return f"---\n{payload}---\n"
    raise BoardReject("field_rule")


def parse_event(text: str) -> dict[str, Any]:
    body = text
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end == -1:
            raise BoardReject("field_rule")
        body = text[4:end]
    value = json.loads(body)
    if not isinstance(value, dict):
        raise BoardReject("field_rule")
    return value


class LocalDirectoryBoardStore:
    """Files in one directory. Writes use exclusive create. No overwrite API."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def list_names(self) -> list[str]:
        names = []
        for path in self.root.iterdir():
            if path.is_file() and _SAFE_NAME.fullmatch(path.name):
                names.append(path.name)
        return sorted(names)

    def read_text(self, name: str) -> str:
        path = self._path(name)
        return path.read_text(encoding="utf-8")

    def write_new(self, name: str, text: str) -> None:
        path = self._path(name)
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        fd = os.open(path, flags, 0o644)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)

    def _path(self, name: str) -> Path:
        if _SAFE_NAME.fullmatch(name) is None or name.startswith("."):
            raise BoardReject("field_rule")
        path = self.root / name
        if path.parent != self.root:
            raise BoardReject("field_rule")
        return path


class DriveBoardStore:
    """Unwired Drive interface. No credentials. No network calls."""

    def __init__(self, folder_id: str) -> None:
        if not isinstance(folder_id, str) or not folder_id:
            raise BoardReject("field_rule")
        self.folder_id = folder_id

    def list_names(self) -> list[str]:
        raise BoardBackendError("backend_unwired")

    def read_text(self, name: str) -> str:
        raise BoardBackendError("backend_unwired")

    def write_new(self, name: str, text: str) -> None:
        raise BoardBackendError("backend_unwired")


def load_named_events(store: BoardStore) -> list[tuple[str, dict[str, Any]]]:
    rows: list[tuple[str, dict[str, Any]]] = []
    for name in store.list_names():
        if name.startswith("BOARD-HEADER-"):
            continue
        try:
            parsed = parse_event(store.read_text(name))
        except (BoardReject, json.JSONDecodeError) as exc:
            raise BoardReject("field_rule") from exc
        rows.append((name, parsed))
    rows.sort(key=lambda item: (item[1].get("occurred_at", ""), item[1].get("event_id", "")))
    return rows


def load_events(store: BoardStore) -> list[dict[str, Any]]:
    return [event for _name, event in load_named_events(store)]


def find_effect(events: list[Mapping[str, Any]], effect_key: str) -> Optional[dict[str, Any]]:
    """Earliest event with this effect_key wins."""
    matches = [dict(item) for item in events if item.get("effect_key") == effect_key]
    if not matches:
        return None
    matches.sort(key=lambda item: (item.get("occurred_at", ""), item.get("event_id", "")))
    return matches[0]


def write_event(
    store: BoardStore,
    event: Mapping[str, Any],
    adapter: Mapping[str, Any],
    *,
    stamp: str,
) -> dict[str, Any]:
    """Append one event, or write nothing when effect_key already exists."""
    validate_event(event, adapter)
    named = load_named_events(store)
    prior_name = None
    prior_event = None
    for name, existing in named:
        if existing.get("effect_key") == event["effect_key"]:
            if prior_event is None:
                prior_name = name
                prior_event = existing
    if prior_event is not None:
        return {
            "result": "no_op_duplicate",
            "wrote": False,
            "event": prior_event,
            "name": prior_name,
        }
    name = event_filename(adapter, stamp, str(event["event_kind"]), str(event["effect_key"]))
    text = serialize_event(event, str(adapter["event_format"]))
    store.write_new(name, text)
    return {
        "result": "ok",
        "wrote": True,
        "event": parse_event(store.read_text(name)),
        "name": name,
    }


def write_header(
    store: BoardStore,
    header: Mapping[str, Any],
    adapter: Mapping[str, Any],
    *,
    stamp: str,
) -> dict[str, Any]:
    """Append a header revision. A second write is a new file, never an overwrite."""
    validate_header(header, adapter)
    name = header_filename(stamp, str(header["effect_key"]))
    text = json.dumps(header, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    store.write_new(name, text)
    return {"result": "ok", "wrote": True, "name": name}


def replay(events: list[Mapping[str, Any]], adapter: Mapping[str, Any]) -> dict[str, Any]:
    """Drop other writers and apply supersedes. Earliest duplicate effect_key wins."""
    ordered = sorted(
        events,
        key=lambda item: (str(item.get("occurred_at", "")), str(item.get("event_id", ""))),
    )
    seen_keys: set[str] = set()
    usable: list[dict[str, Any]] = []
    violations: list[dict[str, str]] = []
    for raw in ordered:
        event = dict(raw)
        key = str(event.get("effect_key", ""))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        if event.get("writer") != adapter.get("writer") or event.get("project_id") != adapter.get("project_id"):
            violations.append(
                {
                    "event_id": str(event.get("event_id", "")),
                    "reason_code": "ownership_violation",
                }
            )
            continue
        usable.append(event)

    by_id = {item["event_id"]: item for item in usable}
    superseded: set[str] = set()
    for event in usable:
        target = event.get("supersedes")
        seen: set[str] = set()
        while isinstance(target, str) and target:
            if target in seen:
                violations.append(
                    {
                        "event_id": str(event.get("event_id", "")),
                        "reason_code": "field_rule",
                    }
                )
                break
            seen.add(target)
            if target not in by_id:
                break
            superseded.add(target)
            target = by_id[target].get("supersedes")

    current = [item for item in usable if item["event_id"] not in superseded]
    return {
        "current": current,
        "violations": violations,
        "superseded": sorted(superseded),
    }
