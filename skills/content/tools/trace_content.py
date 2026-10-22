#!/usr/bin/env python3
"""Trace a content-0.1 record to Input / Source, and bind approval to one revision.

The caller passes the content record and a graph of Idea, Fact, and Input
nodes. This module does not open a vault and does not use the network.

``source_refs`` stay whole strings, as in content-0.1 / ideas-0.1 / facts-0.1.
Content refs use ``idea:`` and ``fact:``. Those nodes carry ``input:`` /
``source:`` refs (or a bare id the graph already knows). An Input node's
``source_id`` is the Source.

``body_sha256`` is the content-0.1 fingerprint: UTF-8 sha256 of the eleven-key
JSON object, ``sort_keys``, separators ``,`` and ``:``, no ``\\u`` escapes.
An approval covers the draft only when ``by`` is ``jake``, ``phrase`` is
``批``, and both ``revision`` and ``body_sha256`` match this draft. Otherwise
the draft is not publishable and a new approval is required. Tracing does not
depend on that check.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

IDEA_ID_RE = re.compile(r"^idea-[0-9a-f]{12}$")
FACT_ID_RE = re.compile(r"^fact-[0-9a-f]{12}$")
INPUT_ID_RE = re.compile(r"^in-[a-z]+-[0-9a-f]{12}$")
SOURCE_ID_RE = re.compile(r"^src-[a-z]+-\S+$")
PREFIXES = frozenset({"idea", "fact", "input", "source", "journal", "experience"})


class ContentTraceError(Exception):
    """The record or graph is not shaped enough to trace or fingerprint."""


def body_sha256(content: dict[str, Any]) -> str:
    """Recompute the content-0.1 channel fingerprint for this draft."""
    if not isinstance(content, dict):
        raise ContentTraceError("content must be an object")
    revision = content.get("revision")
    if isinstance(revision, bool) or not isinstance(revision, int):
        raise ContentTraceError("revision must be an integer")
    schema_version = content.get("schema_version")
    content_id = content.get("content_id")
    if not isinstance(schema_version, str) or not isinstance(content_id, str):
        raise ContentTraceError("schema_version and content_id must be strings")
    channels = _mapping(content.get("channels"), "channels")
    x = _mapping(channels.get("x"), "channels.x")
    xhs = _mapping(channels.get("xiaohongshu"), "channels.xiaohongshu")
    wechat = _mapping(channels.get("wechat_mp"), "channels.wechat_mp")
    cards = xhs.get("cards", [])
    if cards is None:
        cards = []
    if not isinstance(cards, list) or not all(isinstance(item, str) for item in cards):
        raise ContentTraceError("xiaohongshu cards must be a list of strings")
    payload = {
        "schema_version": schema_version,
        "content_id": content_id,
        "revision": revision,
        "x_body": _text(x.get("body", "")),
        "xhs_caption": _text(xhs.get("caption", "")),
        "xhs_cards": "\n".join(cards),
        "wechat_title": _text(wechat.get("title", "")),
        "wechat_summary": _text(wechat.get("summary", "")),
        "wechat_cover_note": _text(wechat.get("cover_note", "")),
        "wechat_body": _text(wechat.get("body", "")),
        "wechat_sources": _text(wechat.get("sources_note", "")),
    }
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def assess_approval(content: dict[str, Any]) -> dict[str, Any]:
    """Say whether ``approval`` covers this draft's revision and fingerprint."""
    current_revision = content.get("revision")
    if isinstance(current_revision, bool) or not isinstance(current_revision, int):
        raise ContentTraceError("revision must be an integer")
    current_hash = body_sha256(content)
    stored = content.get("body_sha256")
    approval = content.get("approval")
    result: dict[str, Any] = {
        "current_revision": current_revision,
        "current_body_sha256": current_hash,
        "stored_body_sha256": stored,
        "approved_revision": None,
        "approved_body_sha256": None,
        "covers_current": False,
        "publishable": False,
        "new_approval_required": True,
        "reason": "",
    }
    if not isinstance(approval, dict):
        result["reason"] = "no approval on this draft; a new approval is required"
        return result
    approved_revision = approval.get("revision")
    approved_hash = approval.get("body_sha256")
    result["approved_revision"] = approved_revision
    result["approved_body_sha256"] = approved_hash
    problems: list[str] = []
    if approval.get("by") != "jake" or approval.get("phrase") != "批":
        problems.append("approval is not Jake's 批")
    if approved_revision != current_revision:
        problems.append(
            f"approved revision {approved_revision} does not cover draft revision {current_revision}"
        )
    if approved_hash != current_hash:
        problems.append("body_sha256 does not match the approved fingerprint")
    if stored != current_hash:
        problems.append("stored body_sha256 does not match the draft fingerprint")
    if problems:
        problems.append("a new approval is required")
        result["reason"] = "; ".join(problems)
        return result
    result["covers_current"] = True
    result["publishable"] = True
    result["new_approval_required"] = False
    result["reason"] = "approval covers this revision and body_sha256"
    return result


def trace_content(content: dict[str, Any], graph: dict[str, Any] | None = None) -> dict[str, Any]:
    """Walk Idea/Fact refs to Input and Source. Approval mismatch does not stop the walk."""
    if not isinstance(content, dict):
        raise ContentTraceError("content must be an object")
    if graph is None:
        graph = {}
    if not isinstance(graph, dict):
        raise ContentTraceError("graph must be an object")
    content_refs = _string_list(content.get("source_refs"), "content source_refs")
    ideas = _index(_node_list(graph.get("ideas"), "ideas"), "idea_id", "idea")
    facts = _index(_node_list(graph.get("facts"), "facts"), "fact_id", "fact")
    inputs = _index(_node_list(graph.get("inputs"), "inputs"), "input_id", "input")

    idea_ids: list[str] = []
    fact_ids: list[str] = []
    input_ids: list[str] = []
    source_ids: list[str] = []
    unresolved: list[dict[str, str]] = []
    seen_ideas: set[str] = set()
    seen_facts: set[str] = set()
    seen_inputs: set[str] = set()
    seen_sources: set[str] = set()

    for ref in content_refs:
        parsed = _parse_known(ref)
        if parsed is None:
            continue
        prefix, ident = parsed
        if prefix == "idea":
            _take_node(
                ident,
                IDEA_ID_RE,
                ideas,
                "idea",
                "invalid idea id",
                idea_ids,
                seen_ideas,
                inputs,
                input_ids,
                source_ids,
                seen_inputs,
                seen_sources,
                unresolved,
            )
        elif prefix == "fact":
            _take_node(
                ident,
                FACT_ID_RE,
                facts,
                "fact",
                "invalid fact id",
                fact_ids,
                seen_facts,
                inputs,
                input_ids,
                source_ids,
                seen_inputs,
                seen_sources,
                unresolved,
            )

    return {
        "ok": not unresolved,
        "content_id": content.get("content_id"),
        "revision": content.get("revision"),
        "idea_ids": idea_ids,
        "fact_ids": fact_ids,
        "input_ids": input_ids,
        "source_ids": source_ids,
        "unresolved": unresolved,
        "approval": assess_approval(content),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Trace content provenance and whether approval covers this draft"
    )
    parser.add_argument("--content", required=True, help="JSON file with one content record")
    parser.add_argument("--graph", required=True, help="JSON file with ideas, facts, and inputs")
    parser.add_argument(
        "--require-approval",
        action="store_true",
        help="exit 1 when this draft is not the approved revision and fingerprint",
    )
    args = parser.parse_args(argv)
    try:
        content = json.loads(Path(args.content).read_text(encoding="utf-8"))
        graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))
        result = trace_content(content, graph)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 1
    except ContentTraceError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    if not result["ok"]:
        return 1
    if args.require_approval and not result["approval"]["publishable"]:
        return 1
    return 0


def _take_node(
    ident: str,
    id_re: re.Pattern[str],
    nodes: dict[str, dict[str, Any]],
    kind: str,
    invalid_reason: str,
    ids: list[str],
    seen: set[str],
    inputs: dict[str, dict[str, Any]],
    input_ids: list[str],
    source_ids: list[str],
    seen_inputs: set[str],
    seen_sources: set[str],
    unresolved: list[dict[str, str]],
) -> None:
    if id_re.fullmatch(ident) is None:
        unresolved.append({"kind": kind, "id": ident, "reason": invalid_reason})
        return
    if ident in seen:
        return
    seen.add(ident)
    ids.append(ident)
    node = nodes.get(ident)
    if node is None:
        unresolved.append({"kind": kind, "id": ident, "reason": "not in graph"})
        return
    _walk_material_refs(
        _refs_of(node),
        inputs,
        input_ids,
        source_ids,
        seen_inputs,
        seen_sources,
        unresolved,
    )


def _walk_material_refs(
    refs: list[str],
    inputs: dict[str, dict[str, Any]],
    input_ids: list[str],
    source_ids: list[str],
    seen_inputs: set[str],
    seen_sources: set[str],
    unresolved: list[dict[str, str]],
) -> None:
    for ref in refs:
        target = _material_target(ref, inputs)
        if target is None:
            continue
        kind, ident = target
        if kind == "invalid-input":
            unresolved.append({"kind": "input", "id": ident, "reason": "invalid input id"})
            continue
        if kind == "invalid-source":
            unresolved.append({"kind": "source", "id": ident, "reason": "invalid source id"})
            continue
        if kind == "source":
            _add(source_ids, seen_sources, ident)
            continue
        _add(input_ids, seen_inputs, ident)
        node = inputs.get(ident)
        if node is None:
            unresolved.append({"kind": "input", "id": ident, "reason": "not in graph"})
            continue
        source_id = node.get("source_id")
        if isinstance(source_id, str) and SOURCE_ID_RE.fullmatch(source_id):
            _add(source_ids, seen_sources, source_id)
            continue
        unresolved.append({"kind": "source", "id": ident, "reason": "input has no source_id"})


def _material_target(ref: str, inputs: dict[str, dict[str, Any]]) -> tuple[str, str] | None:
    parsed = _parse_known(ref)
    if parsed is not None:
        prefix, ident = parsed
        if prefix == "input":
            if ident in inputs or INPUT_ID_RE.fullmatch(ident):
                return ("input", ident)
            return ("invalid-input", ident)
        if prefix == "source":
            if SOURCE_ID_RE.fullmatch(ident):
                return ("source", ident)
            return ("invalid-source", ident)
        return None
    bare = ref.strip().split("#", 1)[0].strip()
    if bare in inputs or INPUT_ID_RE.fullmatch(bare):
        return ("input", bare)
    if SOURCE_ID_RE.fullmatch(bare):
        return ("source", bare)
    return None


def _parse_known(ref: str) -> tuple[str, str] | None:
    text = ref.strip()
    if ":" not in text:
        return None
    prefix, rest = text.split(":", 1)
    if prefix not in PREFIXES:
        return None
    return prefix, rest.split("#", 1)[0].strip()


def _refs_of(node: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for record in _records(node):
        if "source_refs" not in record or record["source_refs"] is None:
            continue
        refs.extend(_string_list(record["source_refs"], "source_refs"))
    return refs


def _records(node: dict[str, Any]) -> list[dict[str, Any]]:
    records = node.get("records")
    if isinstance(records, list):
        return [item for item in records if isinstance(item, dict)]
    return [node]


def _index(nodes: list[Any], id_field: str, label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if not isinstance(node, dict):
            raise ContentTraceError(f"{label} entries must be objects")
        node_id = node.get(id_field)
        if not isinstance(node_id, str) or node_id.strip() == "":
            raise ContentTraceError(f"{label} entry missing {id_field}")
        if id_field == "fact_id" and node_id in indexed:
            indexed[node_id] = {
                "fact_id": node_id,
                "records": _records(indexed[node_id]) + _records(node),
            }
            continue
        indexed[node_id] = node
    return indexed


def _node_list(value: object, label: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ContentTraceError(f"{label} must be a list")
    return value


def _string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ContentTraceError(f"{label} must be a list of strings")
    return list(value)


def _mapping(value: object, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ContentTraceError(f"{label} must be an object")
    return value


def _text(value: object) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ContentTraceError("channel text must be a string")
    return value


def _add(items: list[str], seen: set[str], value: str) -> None:
    if value in seen:
        return
    seen.add(value)
    items.append(value)


if __name__ == "__main__":
    sys.exit(main())
