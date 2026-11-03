#!/usr/bin/env python3
"""Write one ideas-0.1 node under 💡 Ideas/{topic}/{idea_id}.md.

Field rules live in references/schema.md. write and retry are idempotent:
the same node returns the existing path; a different node at that id is a
conflict and is not overwritten.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

SCHEMA_VERSION = "ideas-0.1"
IDEAS_DIR = "💡 Ideas"
TOPIC_DIRS = ("Content", "Insurance", "Life", "Tech", "Trading")
TOPIC_ALIASES = {
    "content": "Content",
    "内容": "Content",
    "insurance": "Insurance",
    "保险": "Insurance",
    "life": "Life",
    "生活": "Life",
    "tech": "Tech",
    "技术": "Tech",
    "trading": "Trading",
    "交易": "Trading",
}
NATURES = ("question", "hypothesis", "judgment", "method", "business_idea")
CONFIRMATION_STATES = ("candidate", "confirmed", "rejected", "deferred")
VALIDATION_STATES = ("untested", "supported", "disputed", "refuted")
ORIGINS = ("jake", "ai_extension")
VISIBILITIES = ("private-jake", "team", "public-ok")
STATUSES = ("active", "archived")
RELATION_TYPES = (
    "sourced_from",
    "supports",
    "challenges",
    "supplements",
    "applies_to",
    "uses",
    "supersedes",
)
OPS = ("create", "supplement", "support", "challenge", "revise", "supersede")
UPDATE_OPS = ("supplement", "support", "challenge", "revise")
CREATE_OPS = ("create", "supersede")
IMMUTABLE = ("idea_id", "type", "schema_version", "origin", "created_at")
NODE_KEYS = (
    "schema_version",
    "idea_id",
    "type",
    "revision",
    "created_at",
    "updated_at",
    "expression",
    "source_refs",
    "context",
    "topics",
    "nature",
    "confirmation_state",
    "validation_state",
    "applicability",
    "limitations",
    "relations",
    "usage_feedback",
    "origin",
    "visibility",
    "status",
    "history",
)
SNAPSHOT_KEYS = tuple(key for key in NODE_KEYS if key not in ("usage_feedback", "history"))
HISTORY_EXTRA = ("at", "by", "op")
OPTIONAL_TEXT = ("context", "applicability", "limitations")
IDEA_ID_RE = re.compile(r"^idea-[0-9a-f]{12}$")
IDEA_FILE_RE = re.compile(r"^idea-[0-9a-f]{12}\.md$")
OLD_NOTE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-.+\.md$")
STAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00$")
HONG_KONG_OFFSET = timedelta(hours=8)
PROTECTED_NAMES = {"MOC.md", "README.md"}


class IdeaError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def emit(payload: dict[str, Any]) -> None:
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


def finish(payload: dict[str, Any], ok: bool) -> int:
    emit(payload)
    if not ok:
        print(payload.get("error", "error"), file=sys.stderr)
        return 1
    return 0


def fail(message: str, **extra: Any) -> int:
    payload: dict[str, Any] = {"ok": False, "error": message}
    payload.update(extra)
    return finish(payload, False)


def compute_idea_id(source_ref: str, expression: str) -> str:
    digest = hashlib.sha1(f"{source_ref}|{expression}".encode("utf-8")).hexdigest()[:12]
    return f"idea-{digest}"


def first_source_ref(source_refs: list[str]) -> str:
    if not source_refs:
        return ""
    return source_refs[0]


def check_timestamp(value: object, label: str) -> str:
    if not isinstance(value, str) or STAMP_RE.fullmatch(value) is None:
        raise IdeaError(f"invalid {label}")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError as exc:
        raise IdeaError(f"invalid {label}") from exc
    if parsed.utcoffset() != HONG_KONG_OFFSET:
        raise IdeaError(f"invalid {label}")
    return value


def check_revision(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise IdeaError("invalid revision")
    return value


def check_string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list):
        raise IdeaError(f"invalid {label}")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or item.strip() == "":
            raise IdeaError(f"invalid {label}")
        items.append(item)
    return items


def optional_text(data: dict[str, Any], key: str) -> str | None:
    if key not in data or data[key] is None:
        return None
    value = data[key]
    if not isinstance(value, str) or value.strip() == "":
        raise IdeaError(f"invalid {key}")
    return value


def enum_value(value: object, options: tuple[str, ...], label: str) -> str:
    if not isinstance(value, str) or value not in options:
        raise IdeaError(f"invalid {label}")
    return value


def normalize_relation(item: object) -> dict[str, str]:
    if not isinstance(item, dict):
        raise IdeaError("invalid relation")
    extra = set(item) - {"type", "target_id", "note"}
    if extra:
        raise IdeaError(f"unknown relation field: {sorted(extra)[0]}")
    relation_type = enum_value(item.get("type"), RELATION_TYPES, "relation type")
    target = item.get("target_id")
    if not isinstance(target, str) or target.strip() == "":
        raise IdeaError("missing target_id")
    relation = {"type": relation_type, "target_id": target.strip()}
    if "note" in item and item["note"] is not None:
        note = item["note"]
        if not isinstance(note, str):
            raise IdeaError("invalid relation note")
        if note.strip() != "":
            relation["note"] = note
    return relation


def normalize_relations(value: object, idea_id: str | None) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise IdeaError("invalid relations")
    relations = [normalize_relation(item) for item in value]
    seen: set[tuple[str, str]] = set()
    for relation in relations:
        key = (relation["type"], relation["target_id"])
        if key in seen:
            raise IdeaError("duplicate relation")
        seen.add(key)
        if relation["type"] == "supersedes" and idea_id is not None and relation["target_id"] == idea_id:
            raise IdeaError("supersedes self")
    return relations


def normalize_feedback(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise IdeaError("invalid usage_feedback")
    items: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            raise IdeaError("invalid usage_feedback")
        extra = set(item) - {"at", "note", "source_ref"}
        if extra:
            raise IdeaError(f"unknown usage_feedback field: {sorted(extra)[0]}")
        note = item.get("note")
        if not isinstance(note, str) or note.strip() == "":
            raise IdeaError("missing usage feedback note")
        feedback = {"at": check_timestamp(item.get("at"), "usage_feedback at"), "note": note}
        if "source_ref" in item and item["source_ref"] is not None:
            source_ref = item["source_ref"]
            if not isinstance(source_ref, str) or source_ref.strip() == "":
                raise IdeaError("invalid usage_feedback source_ref")
            feedback["source_ref"] = source_ref
        items.append(feedback)
    return items


def project_snapshot(mapping: dict[str, Any]) -> dict[str, Any]:
    projected: dict[str, Any] = {}
    for key in SNAPSHOT_KEYS:
        if key in mapping:
            projected[key] = mapping[key]
    return projected


def supersede_relations(mapping: dict[str, Any]) -> list[dict[str, str]]:
    return [item for item in mapping["relations"] if item["type"] == "supersedes"]


def relation_pairs(mapping: dict[str, Any], relation_type: str) -> set[tuple[str, str]]:
    return {
        (item["type"], item["target_id"])
        for item in mapping["relations"]
        if item["type"] == relation_type
    }


def normalize_history_entry(item: object, *, require_idea_id: bool) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise IdeaError("invalid history")
    allowed = set(HISTORY_EXTRA) | set(SNAPSHOT_KEYS)
    extra = set(item) - allowed
    if extra:
        raise IdeaError(f"unknown history field: {sorted(extra)[0]}")
    entry: dict[str, Any] = {
        "at": check_timestamp(item.get("at"), "history at"),
        "by": enum_value(item.get("by"), ORIGINS, "history by"),
        "op": enum_value(item.get("op"), OPS, "history op"),
    }
    entry.update(read_snapshot(item, require_idea_id=require_idea_id, require_updated_at=True))
    if entry["updated_at"] != entry["at"]:
        raise IdeaError("updated_at does not match history")
    return entry


def read_snapshot(data: dict[str, Any], *, require_idea_id: bool, require_updated_at: bool) -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    schema_version = data.get("schema_version")
    if schema_version != SCHEMA_VERSION:
        raise IdeaError("unknown schema_version")
    snapshot["schema_version"] = SCHEMA_VERSION
    if "idea_id" in data and data["idea_id"] is not None:
        idea_id = data["idea_id"]
        if not isinstance(idea_id, str) or idea_id.strip() == "":
            raise IdeaError("missing idea_id")
        idea_id = idea_id.strip()
        if IDEA_ID_RE.fullmatch(idea_id) is None:
            raise IdeaError("invalid idea_id")
        snapshot["idea_id"] = idea_id
    elif require_idea_id:
        raise IdeaError("missing idea_id")
    node_type = data.get("type")
    if node_type != "idea":
        raise IdeaError("invalid type")
    snapshot["type"] = "idea"
    snapshot["revision"] = check_revision(data.get("revision"))
    snapshot["created_at"] = check_timestamp(data.get("created_at"), "created_at")
    if "updated_at" in data and data["updated_at"] is not None:
        snapshot["updated_at"] = check_timestamp(data["updated_at"], "updated_at")
    elif require_updated_at:
        raise IdeaError("invalid updated_at")
    expression = data.get("expression")
    if not isinstance(expression, str) or expression.strip() == "":
        raise IdeaError("missing expression")
    snapshot["expression"] = expression
    if "source_refs" not in data or data["source_refs"] is None:
        raise IdeaError("invalid source_refs")
    snapshot["source_refs"] = check_string_list(data["source_refs"], "source_refs")
    for key in OPTIONAL_TEXT:
        text = optional_text(data, key)
        if text is not None:
            snapshot[key] = text
    if "topics" not in data or data["topics"] is None:
        raise IdeaError("invalid topics")
    snapshot["topics"] = check_string_list(data["topics"], "topics")
    snapshot["nature"] = enum_value(data.get("nature"), NATURES, "nature")
    if "confirmation_state" not in data or data["confirmation_state"] is None:
        snapshot["confirmation_state"] = "candidate"
    else:
        snapshot["confirmation_state"] = enum_value(
            data["confirmation_state"], CONFIRMATION_STATES, "confirmation_state"
        )
    if "validation_state" not in data or data["validation_state"] is None:
        snapshot["validation_state"] = "untested"
    else:
        snapshot["validation_state"] = enum_value(
            data["validation_state"], VALIDATION_STATES, "validation_state"
        )
    idea_id = snapshot.get("idea_id")
    if "relations" not in data or data["relations"] is None:
        raise IdeaError("invalid relations")
    snapshot["relations"] = normalize_relations(data["relations"], idea_id if isinstance(idea_id, str) else None)
    snapshot["origin"] = enum_value(data.get("origin"), ORIGINS, "origin")
    if "visibility" not in data or data["visibility"] is None:
        snapshot["visibility"] = "private-jake"
    else:
        snapshot["visibility"] = enum_value(data["visibility"], VISIBILITIES, "visibility")
    if "status" not in data or data["status"] is None:
        snapshot["status"] = "active"
    else:
        snapshot["status"] = enum_value(data["status"], STATUSES, "status")
    return snapshot


def check_history_chain(history: list[dict[str, Any]]) -> None:
    if not history:
        raise IdeaError("missing history")
    first = history[0]
    if first["op"] not in CREATE_OPS:
        raise IdeaError("history must start with create or supersede")
    if first["revision"] != 1:
        raise IdeaError("invalid revision")
    if first["op"] == "create" and supersede_relations(first):
        raise IdeaError("create cannot include supersedes")
    if first["op"] == "supersede" and not supersede_relations(first):
        raise IdeaError("missing supersedes relation")
    previous = first
    for entry in history[1:]:
        for key in IMMUTABLE:
            if key in entry and key in previous and entry[key] != previous[key]:
                raise IdeaError(f"{key} changed")
        if entry["created_at"] != previous["created_at"]:
            raise IdeaError("created_at changed")
        if supersede_relations(entry) != supersede_relations(previous):
            raise IdeaError("supersedes relations changed")
        if entry["op"] == "revise":
            if entry["revision"] != previous["revision"] + 1:
                raise IdeaError("revise must increment revision")
        elif entry["op"] in ("supplement", "support", "challenge"):
            if entry["revision"] != previous["revision"]:
                raise IdeaError("revision must stay unchanged")
            if entry["expression"] != previous["expression"]:
                raise IdeaError("expression change requires revise")
        else:
            raise IdeaError("invalid history op")
        previous = entry


def require_jake_record(history: list[dict[str, Any]], state: str, expression: str) -> None:
    if state not in ("confirmed", "rejected", "deferred"):
        return
    wanted = expression.strip()
    for entry in history:
        entry_expression = entry.get("expression")
        if (
            entry.get("by") == "jake"
            and entry.get("confirmation_state") == state
            and isinstance(entry_expression, str)
            and entry_expression.strip() == wanted
        ):
            return
    if state == "confirmed":
        raise IdeaError("missing jake confirmation")
    if state == "rejected":
        raise IdeaError("missing jake rejection")
    raise IdeaError("missing jake deferral")


def fill_idea_id(node: dict[str, Any], op: str) -> None:
    history: list[dict[str, Any]] = node["history"]
    if "idea_id" not in node:
        if op not in CREATE_OPS:
            raise IdeaError("missing idea_id")
        node["idea_id"] = compute_idea_id(first_source_ref(node["source_refs"]), node["expression"])
    for entry in history:
        if "idea_id" not in entry:
            entry["idea_id"] = node["idea_id"]
        elif entry["idea_id"] != node["idea_id"]:
            raise IdeaError("idea_id does not match formula")
    for entry in history:
        entry["relations"] = normalize_relations(entry["relations"], node["idea_id"])
    node["relations"] = normalize_relations(node["relations"], node["idea_id"])
    if project_snapshot(history[-1]) != project_snapshot(node):
        raise IdeaError("history does not match frontmatter")
    if op in UPDATE_OPS:
        born = history[0]
        original = compute_idea_id(first_source_ref(born["source_refs"]), born["expression"])
        current = compute_idea_id(first_source_ref(node["source_refs"]), node["expression"])
        if node["idea_id"] != original:
            if node["idea_id"] == current and current != original:
                raise IdeaError("recomputed idea_id")
            raise IdeaError("idea_id does not match original")


def prepare_payload(data: dict[str, Any], directory_override: str | None) -> tuple[dict[str, Any], str, str | None]:
    if not isinstance(data, dict):
        raise IdeaError("payload must be a JSON object")
    allowed = set(NODE_KEYS) | {"op", "directory"}
    extra = set(data) - allowed
    if extra:
        raise IdeaError(f"unknown field: {sorted(extra)[0]}")
    if "op" not in data or data["op"] is None:
        raise IdeaError("missing op")
    op = enum_value(data["op"], OPS, "op")
    directory = directory_override
    if directory is None and "directory" in data and data["directory"] is not None:
        if not isinstance(data["directory"], str):
            raise IdeaError("invalid directory")
        directory = data["directory"]
    if directory is not None and directory not in TOPIC_DIRS:
        raise IdeaError("invalid directory")
    if "history" not in data or data["history"] is None:
        raise IdeaError("missing history")
    if not isinstance(data["history"], list) or not data["history"]:
        raise IdeaError("missing history")
    node = read_snapshot(data, require_idea_id=False, require_updated_at=True)
    if "usage_feedback" not in data or data["usage_feedback"] is None:
        raise IdeaError("invalid usage_feedback")
    node["usage_feedback"] = normalize_feedback(data["usage_feedback"])
    node["history"] = [
        normalize_history_entry(item, require_idea_id=False) for item in data["history"]
    ]
    check_history_chain(node["history"])
    if node["history"][-1]["op"] != op:
        raise IdeaError("op mismatch")
    if node["updated_at"] != node["history"][-1]["at"]:
        raise IdeaError("updated_at does not match history")
    fill_idea_id(node, op)
    require_jake_record(node["history"], node["confirmation_state"], node["expression"])
    for key in IMMUTABLE:
        for entry in node["history"]:
            if entry.get(key) != node.get(key):
                raise IdeaError(f"{key} changed")
    return node, op, directory


def prepare_disk(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise IdeaError("existing idea is unreadable")
    allowed = set(NODE_KEYS)
    extra = set(data) - allowed
    if extra:
        raise IdeaError("existing idea is unreadable")
    if "history" not in data or not isinstance(data["history"], list) or not data["history"]:
        raise IdeaError("existing idea is unreadable")
    node = read_snapshot(data, require_idea_id=True, require_updated_at=True)
    if "usage_feedback" not in data:
        raise IdeaError("existing idea is unreadable")
    node["usage_feedback"] = normalize_feedback(data["usage_feedback"])
    node["history"] = [
        normalize_history_entry(item, require_idea_id=True) for item in data["history"]
    ]
    check_history_chain(node["history"])
    if project_snapshot(node["history"][-1]) != project_snapshot(node):
        raise IdeaError("existing idea is unreadable")
    if node["updated_at"] != node["history"][-1]["at"]:
        raise IdeaError("existing idea is unreadable")
    require_jake_record(node["history"], node["confirmation_state"], node["expression"])
    return node


def canonical(node: dict[str, Any]) -> dict[str, Any]:
    return {key: node[key] for key in NODE_KEYS if key in node}


def choose_directory(topics: list[str], explicit: str | None) -> str:
    if explicit is not None:
        if explicit not in TOPIC_DIRS:
            raise IdeaError("invalid directory")
        return explicit
    matched: list[str] = []
    for topic in topics:
        if not isinstance(topic, str):
            continue
        dest = TOPIC_ALIASES.get(topic.strip().casefold())
        if dest and dest not in matched:
            matched.append(dest)
    if len(matched) == 1:
        return matched[0]
    return "Life"


def ideas_root(vault: Path) -> Path:
    return (vault / IDEAS_DIR).resolve()


def assert_idea_path(vault: Path, path: Path) -> Path:
    root = ideas_root(vault)
    resolved = path.resolve()
    if resolved.parent.parent != root or resolved.parent.name not in TOPIC_DIRS:
        raise IdeaError("protected path")
    if resolved.name in PROTECTED_NAMES or OLD_NOTE_RE.match(resolved.name):
        raise IdeaError("protected path")
    if IDEA_FILE_RE.match(resolved.name) is None:
        raise IdeaError("protected path")
    return resolved


def target_path(vault: Path, directory: str, idea_id: str) -> Path:
    if directory not in TOPIC_DIRS:
        raise IdeaError("invalid directory")
    path = vault / IDEAS_DIR / directory / f"{idea_id}.md"
    return assert_idea_path(vault, path)


def find_ideas(vault: Path, idea_id: str) -> list[Path]:
    found: list[Path] = []
    root = vault / IDEAS_DIR
    for directory in TOPIC_DIRS:
        folder = root / directory
        if not folder.is_dir():
            continue
        path = folder / f"{idea_id}.md"
        if path.is_file() and IDEA_FILE_RE.match(path.name):
            found.append(path)
    return found


def dump_scalar(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise IdeaError("invalid scalar")
    if isinstance(value, int):
        return str(value)
    return json.dumps(value, ensure_ascii=False)


def emit_keyed(key: str, value: object, indent: int) -> list[str]:
    pad = " " * indent
    if isinstance(value, dict):
        lines = [f"{pad}{key}:"]
        for child_key, child_value in value.items():
            lines.extend(emit_keyed(str(child_key), child_value, indent + 2))
        return lines
    if isinstance(value, list):
        if not value:
            return [f"{pad}{key}: []"]
        lines = [f"{pad}{key}:"]
        for item in value:
            lines.extend(emit_list_item(item, indent))
        return lines
    return [f"{pad}{key}: {dump_scalar(value)}"]


def emit_list_item(item: object, indent: int) -> list[str]:
    pad = " " * indent
    if not isinstance(item, dict):
        return [f"{pad}  - {dump_scalar(item)}"]
    pairs = list(item.items())
    if not pairs:
        return [f"{pad}  - {{}}"]
    first_key, first_value = pairs[0]
    if isinstance(first_value, (dict, list)):
        raise IdeaError("invalid scalar")
    lines = [f"{pad}  - {first_key}: {dump_scalar(first_value)}"]
    for key, value in pairs[1:]:
        lines.extend(emit_keyed(str(key), value, indent + 4))
    return lines


def render(node: dict[str, Any]) -> str:
    lines = ["---"]
    for key in NODE_KEYS:
        if key in node:
            lines.extend(emit_keyed(key, node[key], 0))
    lines.append("---")
    body = node["expression"].strip()
    return "\n".join(lines) + "\n\n" + body + "\n"


def split_frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---\n"):
        raise IdeaError("existing idea is unreadable")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise IdeaError("existing idea is unreadable")
    loaded = yaml.safe_load(text[4:end])
    if not isinstance(loaded, dict):
        raise IdeaError("existing idea is unreadable")
    return loaded


def load_idea_text(text: str) -> dict[str, Any]:
    return prepare_disk(split_frontmatter(text))


def node_diff(existing: dict[str, Any] | None, proposed: dict[str, Any]) -> str:
    if existing is None:
        left = ["<unreadable>"]
    else:
        left = json.dumps(canonical(existing), ensure_ascii=False, indent=2, sort_keys=True).splitlines()
    right = json.dumps(canonical(proposed), ensure_ascii=False, indent=2, sort_keys=True).splitlines()
    return "\n".join(
        difflib.unified_diff(left, right, fromfile="existing", tofile="proposed", lineterm="")
    )


def conflict(message: str, path: Path, idea_id: str, existing: dict[str, Any] | None, proposed: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": False,
        "error": f"conflict: {message}",
        "path": str(path),
        "idea_id": idea_id,
        "diff": node_diff(existing, proposed),
    }


def without_history_clock(node: dict[str, Any]) -> dict[str, Any]:
    data = canonical(node)
    data.pop("updated_at", None)
    data.pop("history", None)
    return data


def is_prefix(older: list[Any], newer: list[Any]) -> bool:
    return len(newer) >= len(older) and newer[: len(older)] == older


def successor_problem(existing: dict[str, Any], proposed: dict[str, Any], op: str) -> str | None:
    if op not in UPDATE_OPS:
        return "create cannot replace an existing idea"
    for key in IMMUTABLE:
        if existing.get(key) != proposed.get(key):
            return f"{key} changed"
    if not is_prefix(existing["history"], proposed["history"]):
        return "history modified"
    if len(proposed["history"]) != len(existing["history"]) + 1:
        return "history modified"
    if proposed["history"][-1]["op"] != op:
        return "op mismatch"
    if not is_prefix(existing["usage_feedback"], proposed["usage_feedback"]):
        return "usage_feedback modified"
    if supersede_relations(existing) != supersede_relations(proposed):
        return "supersedes relations changed"
    if op == "revise":
        if proposed["revision"] != existing["revision"] + 1:
            return "revise must increment revision"
    else:
        if proposed["revision"] != existing["revision"]:
            return "revision must stay unchanged"
        if proposed["expression"] != existing["expression"]:
            return "expression change requires revise"
    if op == "support" and not (relation_pairs(proposed, "supports") - relation_pairs(existing, "supports")):
        return "support requires a new supports relation"
    if op == "challenge" and not (
        relation_pairs(proposed, "challenges") - relation_pairs(existing, "challenges")
    ):
        return "challenge requires a new challenges relation"
    if op == "supplement" and without_history_clock(existing) == without_history_clock(proposed):
        return "supplement changes nothing"
    return None


def check_new_node(node: dict[str, Any], op: str) -> None:
    if op not in CREATE_OPS:
        raise IdeaError("idea not found")
    if node["revision"] != 1 or len(node["history"]) != 1:
        raise IdeaError("create history must contain one snapshot")
    if node["history"][0]["op"] != op:
        raise IdeaError("op mismatch")
    expected = compute_idea_id(first_source_ref(node["source_refs"]), node["expression"])
    if node["idea_id"] != expected:
        raise IdeaError("idea_id does not match formula")
    if op == "create" and supersede_relations(node):
        raise IdeaError("create cannot include supersedes")
    if op == "supersede" and not supersede_relations(node):
        raise IdeaError("missing supersedes relation")


def commit_text(path: Path, text: str, previous: bytes | None) -> None:
    encoded = text.encode("utf-8")
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    replaced = False
    try:
        with tmp.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp, path)
        replaced = True
        if path.read_bytes() != encoded:
            raise OSError("readback mismatch")
    except OSError:
        if replaced:
            if previous is None:
                if path.is_file():
                    path.unlink()
            else:
                path.write_bytes(previous)
        raise
    finally:
        if tmp.exists():
            tmp.unlink()


def success(path: Path, idea_id: str, op: str, *, dry_run: bool, already: bool) -> dict[str, Any]:
    return {
        "ok": True,
        "dry_run": dry_run,
        "path": str(path),
        "idea_id": idea_id,
        "op": op,
        "already_persisted": already,
    }


_GUARD = None
_GUARD_MISSING = "写入只许进 obsidian-digitalbrain，vault guard 缺失，拒绝并停下"


def _rejection(vault: Path) -> tuple[str, str] | None:
    global _GUARD
    if _GUARD is None:
        path = Path(__file__).resolve().parents[2] / "journal" / "tools" / "vault_guard.py"
        spec = importlib.util.spec_from_file_location("infoflow_vault_guard", path)
        if spec is None or spec.loader is None or not path.is_file():
            return "refused", _GUARD_MISSING
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _GUARD = module
    return _GUARD.rejection(vault)


def perform(
    vault: Path,
    action: str,
    payload_text: str,
    *,
    dry_run: bool,
    directory_override: str | None,
) -> dict[str, Any]:
    if action not in ("write", "retry"):
        return {"ok": False, "error": "action must be write or retry"}
    if not vault.is_dir():
        return {"ok": False, "error": "vault missing"}
    rejected = _rejection(vault)
    if rejected is not None:
        _status, message = rejected
        return {"ok": False, "error": message}
    if not (vault / IDEAS_DIR).is_dir():
        return {"ok": False, "error": "ideas directory missing"}
    try:
        data = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"invalid payload: {exc}"}
    try:
        node, op, directory = prepare_payload(data, directory_override)
    except IdeaError as exc:
        return {"ok": False, "error": exc.message}

    idea_id = node["idea_id"]
    try:
        matches = find_ideas(vault, idea_id)
    except OSError as exc:
        return {"ok": False, "error": f"unavailable: {exc}", "idea_id": idea_id}
    if len(matches) > 1:
        return {
            "ok": False,
            "error": "conflict: idea_id stored in more than one topic directory",
            "idea_id": idea_id,
            "diff": "",
        }

    if len(matches) == 1:
        path = matches[0]
        try:
            assert_idea_path(vault, path)
            previous = path.read_bytes()
            existing = load_idea_text(previous.decode("utf-8"))
        except (OSError, UnicodeError, IdeaError) as exc:
            message = exc.message if isinstance(exc, IdeaError) else "existing idea is unreadable"
            return conflict(message, path, idea_id, None, node)
        if canonical(existing) == canonical(node):
            return success(path, idea_id, op, dry_run=dry_run, already=True)
        reason = successor_problem(existing, node, op)
        if reason is not None:
            return conflict(reason, path, idea_id, existing, node)
        if directory is not None and directory != path.parent.name:
            return {
                "ok": False,
                "error": f"idea is already stored in {path.parent.name}",
                "path": str(path),
                "idea_id": idea_id,
            }
        try:
            rendered = render(node)
            if canonical(load_idea_text(rendered)) != canonical(node):
                return {"ok": False, "error": "render is not stable", "idea_id": idea_id, "diff": node_diff(existing, node)}
        except IdeaError as exc:
            return {"ok": False, "error": exc.message, "idea_id": idea_id}
        if dry_run:
            return success(path, idea_id, op, dry_run=True, already=False)
        try:
            commit_text(path, rendered, previous)
        except OSError as exc:
            return {"ok": False, "error": f"write failed: {exc}", "path": str(path), "idea_id": idea_id}
        return success(path, idea_id, op, dry_run=False, already=False)

    try:
        check_new_node(node, op)
        directory = choose_directory(node["topics"], directory)
        path = target_path(vault, directory, idea_id)
        if not path.parent.is_dir():
            raise IdeaError("topic directory does not exist")
        if path.exists():
            return conflict("target path exists", path, idea_id, None, node)
        rendered = render(node)
        if canonical(load_idea_text(rendered)) != canonical(node):
            return {"ok": False, "error": "render is not stable", "idea_id": idea_id}
    except IdeaError as exc:
        return {"ok": False, "error": exc.message, "idea_id": idea_id}
    if dry_run:
        return success(path, idea_id, op, dry_run=True, already=False)
    try:
        commit_text(path, rendered, None)
    except OSError as exc:
        return {"ok": False, "error": f"write failed: {exc}", "path": str(path), "idea_id": idea_id}
    return success(path, idea_id, op, dry_run=False, already=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write one ideas-0.1 markdown node.")
    parser.add_argument("action", choices=["write", "retry"])
    parser.add_argument("--vault", required=True)
    parser.add_argument("--payload", required=True)
    parser.add_argument("--directory", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    vault = Path(args.vault).expanduser()
    payload_path = Path(args.payload).expanduser()
    if not payload_path.is_file():
        return fail(f"payload missing: {payload_path}")
    try:
        payload_text = payload_path.read_text(encoding="utf-8")
    except OSError as exc:
        return fail(f"payload unreadable: {exc}")
    result = perform(
        vault,
        args.action,
        payload_text,
        dry_run=bool(args.dry_run),
        directory_override=args.directory,
    )
    return finish(result, bool(result.get("ok")))


if __name__ == "__main__":
    sys.exit(main())
