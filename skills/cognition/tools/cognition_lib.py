#!/usr/bin/env python3
"""Shared Cognition parse, ID, fingerprint, relation, and store helpers.

Canonical validation lives here. CLI wrappers must not reimplement it.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.1"
COGNITION_ROOT = "📖 Cognition"
TYPE_DIRS = {
    "evidence": "Evidence",
    "belief": "Beliefs",
    "principle": "Principles",
}
TYPES = ("evidence", "belief", "principle")
ORIGIN_TYPES = ("journal", "direct_reflection", "project_outcome", "external_source")
EVIDENCE_STATUS = ("active", "retired")
BELIEF_PRINCIPLE_STATUS = ("active", "contested", "retired")
VALIDATION_STATES = ("unverified", "checked", "corroborated")
CONFIDENCE = ("low", "medium", "high")
RELIABILITY = ("low", "medium", "high")
FORBIDDEN_RELATION_FIELDS = {
    "supports",
    "contradicts",
    "superseded_by",
    "derived_from",
    "motivates",
    "applies_to",
}
LIST_FIELDS = {
    "domains",
    "related_projects",
    "supporting_evidence",
    "contradicting_evidence",
    "based_on",
    "exceptions",
    "related_to",
    "supersedes",
    "source_journals",
}
COMMON_REQUIRED = (
    "schema_version",
    "id",
    "type",
    "status",
    "domains",
    "related_projects",
    "created",
    "updated",
    "origin_type",
)
EVIDENCE_REQUIRED = (
    "claim",
    "source",
    "source_type",
    "validation",
    "reliability",
    "scope",
    "limitations",
)
BELIEF_REQUIRED = (
    "statement",
    "confidence",
    "supporting_evidence",
    "contradicting_evidence",
)
PRINCIPLE_REQUIRED = (
    "trigger",
    "preferred_action",
    "rationale",
    "based_on",
    "scope",
    "exceptions",
)
ALLOWED_KEYS = (
    set(COMMON_REQUIRED)
    | {"origin_ref", "origin_summary"}
    | set(EVIDENCE_REQUIRED)
    | set(BELIEF_REQUIRED)
    | set(PRINCIPLE_REQUIRED)
    | {"related_to", "supersedes", "source_journals"}
)
ID_RE = re.compile(r"^(evidence|belief|principle)-(\d{8})-([a-z0-9]+(?:-[a-z0-9]+)*)$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TOKEN_RE = re.compile(r"[^\w\u4e00-\u9fff]+")

BELIEF_TRANSITIONS = {
    ("active", "contested"),
    ("contested", "active"),
    ("active", "retired"),
    ("contested", "retired"),
    ("retired", "active"),
}
EVIDENCE_TRANSITIONS = {
    ("active", "retired"),
    ("retired", "active"),
}


class CognitionError(Exception):
    pass


@dataclass
class CognitionDoc:
    path: Path
    meta: dict[str, Any]
    body: str
    raw: str
    parse_error: str | None = None

    @property
    def id(self) -> str:
        return str(self.meta.get("id") or "")

    @property
    def type(self) -> str:
        return str(self.meta.get("type") or "")

    @property
    def status(self) -> str:
        return str(self.meta.get("status") or "")


@dataclass
class Store:
    vault: Path
    root: Path
    available: bool
    docs: list[CognitionDoc] = field(default_factory=list)
    by_id: dict[str, CognitionDoc] = field(default_factory=dict)
    parse_errors: list[str] = field(default_factory=list)
    outside: list[Path] = field(default_factory=list)


def cognition_root(vault: Path) -> Path:
    return vault / COGNITION_ROOT


def type_dir(vault: Path, typ: str) -> Path:
    return cognition_root(vault) / TYPE_DIRS[typ]


def target_path(vault: Path, doc: CognitionDoc) -> Path:
    if doc.path.name:
        parent_ok = doc.path.parent.name == TYPE_DIRS.get(doc.type, "")
        if parent_ok:
            return doc.path
    return type_dir(vault, doc.type) / f"{doc.id}.md"


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def norm_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if value == "":
        return []
    return [str(value)]


def tokenize(text: str) -> list[str]:
    return [part.lower() for part in TOKEN_RE.split(text or "") if part]


def unquote(raw: str) -> str:
    text = raw.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        inner = text[1:-1]
        if text[0] == '"':
            return bytes(inner, "utf-8").decode("unicode_escape") if "\\" in inner else inner
        return inner
    return text


def parse_scalar(raw: str) -> Any:
    text = raw.strip()
    if text == "[]":
        return []
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        parts: list[str] = []
        buf = ""
        in_quote = False
        quote = ""
        for char in inner:
            if in_quote:
                buf += char
                if char == quote:
                    in_quote = False
                continue
            if char in "\"'":
                in_quote = True
                quote = char
                buf += char
                continue
            if char == ",":
                parts.append(unquote(buf))
                buf = ""
                continue
            buf += char
        if buf.strip():
            parts.append(unquote(buf))
        return parts
    return unquote(text)


def parse_frontmatter_block(block: str) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.strip().startswith("#"):
            i += 1
            continue
        if line.startswith(" ") or line.startswith("\t"):
            raise CognitionError(f"unexpected indented line in frontmatter: {line!r}")
        if ":" not in line:
            raise CognitionError(f"invalid frontmatter line: {line!r}")
        key, rest = line.split(":", 1)
        key = key.strip()
        rest = rest.strip()
        if rest == "" or rest in ("|", ">"):
            items: list[str] = []
            scalar_parts: list[str] = []
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if not nxt.strip():
                    j += 1
                    continue
                if nxt.startswith("  - ") or nxt.startswith("\t- "):
                    items.append(unquote(nxt.lstrip()[2:].strip()))
                    j += 1
                    continue
                if nxt.startswith("  ") or nxt.startswith("\t"):
                    scalar_parts.append(nxt.strip())
                    j += 1
                    continue
                break
            if items:
                meta[key] = items
            elif rest in ("|", ">") or scalar_parts:
                meta[key] = "\n".join(scalar_parts)
            else:
                meta[key] = [] if key in LIST_FIELDS else ""
            i = j
            continue
        meta[key] = parse_scalar(rest)
        i += 1
    return meta


def split_markdown(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        raise CognitionError("missing YAML frontmatter")
    rest = text[3:]
    if rest.startswith("\n"):
        rest = rest[1:]
    end = rest.find("\n---")
    if end < 0:
        raise CognitionError("unterminated YAML frontmatter")
    block = rest[:end]
    body = rest[end + len("\n---") :]
    if body.startswith("\n"):
        body = body[1:]
    return parse_frontmatter_block(block), body


def parse_markdown(text: str, path: Path | None = None) -> CognitionDoc:
    loc = path or Path("<memory>")
    try:
        meta, body = split_markdown(text)
    except CognitionError as exc:
        return CognitionDoc(path=loc, meta={}, body="", raw=text, parse_error=str(exc))
    return CognitionDoc(path=loc, meta=meta, body=body, raw=text)


def dump_scalar(value: Any) -> str:
    text = str(value)
    if DATE_RE.match(text) or re.fullmatch(r"[A-Za-z0-9._/-]+", text):
        if text == SCHEMA_VERSION:
            return json.dumps(text)
        return text
    return json.dumps(text, ensure_ascii=False)


def dump_key(key: str, value: Any) -> list[str]:
    if isinstance(value, list):
        if not value:
            return [f"{key}: []"]
        lines = [f"{key}:"]
        for item in value:
            lines.append(f"  - {dump_scalar(item)}")
        return lines
    return [f"{key}: {dump_scalar(value)}"]


def render_markdown(meta: dict[str, Any], body: str) -> str:
    order = (
        "schema_version",
        "id",
        "type",
        "status",
        "domains",
        "related_projects",
        "created",
        "updated",
        "origin_type",
        "origin_ref",
        "origin_summary",
        "claim",
        "source",
        "source_type",
        "validation",
        "reliability",
        "scope",
        "limitations",
        "statement",
        "confidence",
        "supporting_evidence",
        "contradicting_evidence",
        "trigger",
        "preferred_action",
        "rationale",
        "based_on",
        "exceptions",
        "related_to",
        "supersedes",
        "source_journals",
    )
    lines = ["---"]
    seen: set[str] = set()
    for key in order:
        if key in meta:
            lines.extend(dump_key(key, meta[key]))
            seen.add(key)
    for key, value in meta.items():
        if key not in seen:
            lines.extend(dump_key(key, value))
    lines.append("---")
    body_text = body.strip()
    if body_text:
        return "\n".join(lines) + "\n\n" + body_text + "\n"
    return "\n".join(lines) + "\n"


def history_heading(typ: str) -> str:
    if typ == "evidence":
        return "## Validation History"
    return "## Revision History"


def default_history_body(typ: str, created: str, note: str) -> str:
    heading = history_heading(typ)
    return f"{heading}\n- {created}: {note}\n"


def make_id(typ: str, yyyymmdd: str, slug: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
    return f"{typ}-{yyyymmdd}-{cleaned}"


def legal_type_dirs(root: Path) -> set[Path]:
    return {root / name for name in TYPE_DIRS.values()}


def iter_cognition_markdown(root: Path) -> tuple[list[Path], list[Path]]:
    inside: list[Path] = []
    outside: list[Path] = []
    if not root.is_dir():
        return inside, outside
    legal = legal_type_dirs(root)
    for path in sorted(root.rglob("*.md")):
        if path.parent in legal:
            inside.append(path)
        else:
            outside.append(path)
    return inside, outside


def load_store(vault: Path) -> Store:
    root = cognition_root(vault)
    if not vault.is_dir():
        return Store(vault=vault, root=root, available=False)
    if not root.exists():
        return Store(vault=vault, root=root, available=False)
    if not root.is_dir():
        return Store(vault=vault, root=root, available=False)
    inside, outside = iter_cognition_markdown(root)
    docs: list[CognitionDoc] = []
    parse_errors: list[str] = []
    for path in inside:
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            parse_errors.append(f"{path}: unreadable ({exc})")
            docs.append(
                CognitionDoc(path=path, meta={}, body="", raw="", parse_error=f"unreadable ({exc})")
            )
            continue
        doc = parse_markdown(raw, path)
        if doc.parse_error:
            parse_errors.append(f"{path}: {doc.parse_error}")
        docs.append(doc)
    by_id: dict[str, CognitionDoc] = {}
    for doc in docs:
        if doc.parse_error or not doc.id:
            continue
        by_id.setdefault(doc.id, doc)
    return Store(
        vault=vault,
        root=root,
        available=True,
        docs=docs,
        by_id=by_id,
        parse_errors=parse_errors,
        outside=outside,
    )


def _require_str(doc: CognitionDoc, key: str, errors: list[str]) -> str:
    if key not in doc.meta:
        errors.append(f"{doc.path}: missing required field {key}")
        return ""
    value = doc.meta[key]
    if isinstance(value, list) or value is None:
        errors.append(f"{doc.path}: {key} must be a string")
        return ""
    text = str(value).strip()
    if text == "":
        errors.append(f"{doc.path}: {key} must not be empty")
    return text


def _require_list(doc: CognitionDoc, key: str, errors: list[str]) -> list[str]:
    if key not in doc.meta:
        errors.append(f"{doc.path}: missing required field {key}")
        return []
    value = doc.meta[key]
    if not isinstance(value, list):
        errors.append(f"{doc.path}: {key} must be a list")
        return []
    return [str(item) for item in value]


def _check_id(doc: CognitionDoc, errors: list[str]) -> None:
    cid = _require_str(doc, "id", errors)
    if not cid:
        return
    match = ID_RE.fullmatch(cid)
    if not match:
        errors.append(f"{doc.path}: id {cid!r} is not type-YYYYMMDD-slug")
        return
    if match.group(1) != doc.type:
        errors.append(f"{doc.path}: id prefix {match.group(1)} does not match type {doc.type}")


def _check_common(doc: CognitionDoc, errors: list[str]) -> None:
    version = _require_str(doc, "schema_version", errors)
    if version and version != SCHEMA_VERSION:
        errors.append(
            f"{doc.path}: unsupported schema_version {version!r} (supported: {SCHEMA_VERSION})"
        )
    typ = _require_str(doc, "type", errors)
    if typ and typ not in TYPES:
        errors.append(f"{doc.path}: illegal type {typ!r}")
    expected_dir = TYPE_DIRS.get(typ)
    if expected_dir and doc.path.parent.name and doc.path.parent.name != expected_dir:
        if str(doc.path) != "<memory>" and doc.path.suffix == ".md":
            errors.append(
                f"{doc.path}: type {typ} must live in {COGNITION_ROOT}/{expected_dir}/"
            )
    for key in FORBIDDEN_RELATION_FIELDS:
        if key in doc.meta:
            errors.append(f"{doc.path}: illegal persisted relation field {key}")
    for key in doc.meta:
        if key not in ALLOWED_KEYS:
            errors.append(f"{doc.path}: unknown field {key}")
    _require_list(doc, "domains", errors)
    _require_list(doc, "related_projects", errors)
    for date_key in ("created", "updated"):
        value = _require_str(doc, date_key, errors)
        if value and not DATE_RE.fullmatch(value):
            errors.append(f"{doc.path}: {date_key} must be YYYY-MM-DD")
    origin_type = _require_str(doc, "origin_type", errors)
    if origin_type and origin_type not in ORIGIN_TYPES:
        errors.append(f"{doc.path}: illegal origin_type {origin_type!r}")
    origin_ref = str(doc.meta.get("origin_ref") or "").strip()
    origin_summary = str(doc.meta.get("origin_summary") or "").strip()
    if not origin_ref and not origin_summary:
        errors.append(f"{doc.path}: origin_ref or origin_summary is required")
    _check_id(doc, errors)
    heading = history_heading(typ) if typ in TYPES else ""
    if heading and heading not in doc.body:
        errors.append(f"{doc.path}: body must contain append-only {heading}")


def _check_evidence(doc: CognitionDoc, errors: list[str]) -> None:
    status = _require_str(doc, "status", errors)
    if status and status not in EVIDENCE_STATUS:
        errors.append(f"{doc.path}: evidence status must be active|retired")
    for key in EVIDENCE_REQUIRED:
        _require_str(doc, key, errors)
    validation = str(doc.meta.get("validation") or "")
    if validation and validation not in VALIDATION_STATES:
        errors.append(f"{doc.path}: illegal validation {validation!r}")
    reliability = str(doc.meta.get("reliability") or "")
    if reliability and reliability not in RELIABILITY:
        errors.append(f"{doc.path}: illegal reliability {reliability!r}")
    if "supersedes" in doc.meta and as_list(doc.meta.get("supersedes")):
        errors.append(f"{doc.path}: evidence cannot persist supersedes")


def _check_belief(doc: CognitionDoc, errors: list[str]) -> None:
    status = _require_str(doc, "status", errors)
    if status and status not in BELIEF_PRINCIPLE_STATUS:
        errors.append(f"{doc.path}: belief status must be active|contested|retired")
    _require_str(doc, "statement", errors)
    confidence = _require_str(doc, "confidence", errors)
    if confidence and confidence not in CONFIDENCE:
        errors.append(f"{doc.path}: illegal confidence {confidence!r}")
    _require_list(doc, "supporting_evidence", errors)
    _require_list(doc, "contradicting_evidence", errors)


def _check_principle(doc: CognitionDoc, errors: list[str]) -> None:
    status = _require_str(doc, "status", errors)
    if status and status not in BELIEF_PRINCIPLE_STATUS:
        errors.append(f"{doc.path}: principle status must be active|contested|retired")
    for key in ("trigger", "preferred_action", "rationale", "scope"):
        _require_str(doc, key, errors)
    _require_list(doc, "based_on", errors)
    _require_list(doc, "exceptions", errors)


def _target_type(cid: str) -> str | None:
    match = ID_RE.fullmatch(cid)
    return match.group(1) if match else None


def _check_relations(docs: list[CognitionDoc], errors: list[str]) -> None:
    readable = [doc for doc in docs if not doc.parse_error and doc.id]
    by_id: dict[str, list[CognitionDoc]] = {}
    for doc in readable:
        by_id.setdefault(doc.id, []).append(doc)
    for cid, group in by_id.items():
        if len(group) > 1:
            paths = ", ".join(str(doc.path) for doc in group)
            errors.append(f"duplicate id {cid}: {paths}")

    index = {cid: group[0] for cid, group in by_id.items()}
    edges: dict[str, list[str]] = {}

    def resolve(doc: CognitionDoc, field_name: str, expected: str | None) -> list[str]:
        ids = as_list(doc.meta.get(field_name))
        for cid in ids:
            if not ID_RE.fullmatch(cid):
                errors.append(
                    f"{doc.path}: {field_name} must store cognition IDs, got {cid!r}"
                )
                continue
            target = index.get(cid)
            if target is None:
                errors.append(f"{doc.path}: unresolved cognition id {cid}")
                continue
            actual = target.type or _target_type(cid)
            if expected and actual != expected:
                errors.append(
                    f"{doc.path}: {field_name} target {cid} has type {actual}, expected {expected}"
                )
        return ids

    for doc in readable:
        if doc.type == "belief":
            resolve(doc, "supporting_evidence", "evidence")
            resolve(doc, "contradicting_evidence", "evidence")
        elif doc.type == "principle":
            resolve(doc, "based_on", "belief")
        if "related_to" in doc.meta:
            resolve(doc, "related_to", None)
        supersedes = as_list(doc.meta.get("supersedes")) if "supersedes" in doc.meta else []
        if supersedes and doc.type not in ("belief", "principle"):
            errors.append(f"{doc.path}: supersedes is only for belief or principle")
            continue
        for cid in supersedes:
            if cid == doc.id:
                errors.append(f"{doc.path}: supersedes cannot point to self")
                continue
            if not ID_RE.fullmatch(cid):
                errors.append(f"{doc.path}: supersedes must store cognition IDs, got {cid!r}")
                continue
            target = index.get(cid)
            if target is None:
                errors.append(f"{doc.path}: unresolved cognition id {cid}")
                continue
            if target.type != doc.type:
                errors.append(
                    f"{doc.path}: supersedes target {cid} must be the same type ({doc.type})"
                )
            edges.setdefault(doc.id, []).append(cid)

    for src, targets in edges.items():
        seen_path: set[str] = set()

        def visit(node: str, trail: list[str]) -> None:
            if node in trail:
                errors.append(
                    f"supersession cycle involving {src}: {' -> '.join(trail + [node])}"
                )
                return
            if node in seen_path:
                return
            seen_path.add(node)
            for nxt in edges.get(node, []):
                visit(nxt, trail + [node])

        visit(src, [])


def validate_docs(docs: list[CognitionDoc], outside: list[Path] | None = None) -> list[str]:
    errors: list[str] = []
    for path in outside or []:
        errors.append(
            f"{path}: file outside approved {COGNITION_ROOT}/{{Evidence,Beliefs,Principles}}"
        )
    for doc in docs:
        if doc.parse_error:
            errors.append(f"{doc.path}: {doc.parse_error}")
            continue
        _check_common(doc, errors)
        if doc.type == "evidence":
            _check_evidence(doc, errors)
        elif doc.type == "belief":
            _check_belief(doc, errors)
        elif doc.type == "principle":
            _check_principle(doc, errors)
    _check_relations(docs, errors)
    # unique cycle messages
    unique: list[str] = []
    seen: set[str] = set()
    for item in errors:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


def validate_store(store: Store) -> list[str]:
    if not store.available:
        return []
    return validate_docs(store.docs, store.outside)


def merge_proposed(store: Store, proposed: CognitionDoc) -> list[CognitionDoc]:
    docs = [doc for doc in store.docs if doc.id != proposed.id]
    docs.append(proposed)
    return docs


def semantic_key(doc: CognitionDoc) -> str:
    if doc.type == "belief":
        return f"belief:{norm_text(doc.meta.get('statement'))}"
    if doc.type == "evidence":
        return f"evidence:{norm_text(doc.meta.get('claim'))}|{norm_text(doc.meta.get('source'))}"
    if doc.type == "principle":
        return (
            "principle:"
            f"{norm_text(doc.meta.get('trigger'))}|{norm_text(doc.meta.get('preferred_action'))}"
        )
    return f"{doc.type}:{doc.id}"


def find_duplicate(store: Store, proposed: CognitionDoc) -> CognitionDoc | None:
    if proposed.id and proposed.id in store.by_id:
        return store.by_id[proposed.id]
    key = semantic_key(proposed)
    suffix = key.split(":", 1)[-1].strip().strip("|")
    if not suffix:
        return None
    for doc in store.docs:
        if doc.parse_error or doc.id == proposed.id:
            continue
        if doc.type == proposed.type and semantic_key(doc) == key:
            return doc
    return None


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def restore_snapshot(path: Path, snapshot: str | None) -> None:
    if snapshot is None:
        if path.exists():
            path.unlink()
        return
    atomic_write(path, snapshot)


def superseded_ids(docs: list[CognitionDoc]) -> set[str]:
    edges: dict[str, list[str]] = {}
    active: list[str] = []
    for doc in docs:
        if doc.parse_error or not doc.id:
            continue
        edges[doc.id] = as_list(doc.meta.get("supersedes"))
        if doc.status == "active":
            active.append(doc.id)
    marked: set[str] = set()
    stack = list(active)
    seen_src: set[str] = set()
    while stack:
        src = stack.pop()
        if src in seen_src:
            continue
        seen_src.add(src)
        for target in edges.get(src, []):
            if target not in marked:
                marked.add(target)
                stack.append(target)
    return marked


def effective_status(doc: CognitionDoc, superseded: set[str]) -> str:
    if doc.id in superseded:
        return "superseded"
    return doc.status or "unknown"


def haystack(doc: CognitionDoc) -> str:
    parts = [
        doc.id,
        doc.path.name,
        doc.path.stem,
        " ".join(as_list(doc.meta.get("domains"))),
        " ".join(as_list(doc.meta.get("related_projects"))),
        str(doc.meta.get("claim") or ""),
        str(doc.meta.get("statement") or ""),
        str(doc.meta.get("trigger") or ""),
        str(doc.meta.get("preferred_action") or ""),
        str(doc.meta.get("rationale") or ""),
        doc.body,
        doc.raw,
    ]
    return " ".join(parts).lower()


def relevance_score(
    doc: CognitionDoc,
    tokens: list[str],
    project: str,
    domain: str,
) -> int:
    text = haystack(doc)
    score = 0
    for token in tokens:
        if token and token in text:
            score += 2
    projects = " ".join(as_list(doc.meta.get("related_projects"))).lower()
    domains = [item.lower() for item in as_list(doc.meta.get("domains"))]
    if project and project.lower() in projects:
        score += 10
    if domain and domain.lower() in domains:
        score += 8
    return score


def rank_score(
    doc: CognitionDoc,
    tokens: list[str],
    project: str,
    domain: str,
    superseded: set[str],
) -> int:
    score = relevance_score(doc, tokens, project, domain)
    eff = effective_status(doc, superseded)
    if eff == "superseded":
        score -= 20
    elif eff == "retired":
        score -= 15
    elif eff == "contested":
        score -= 3
    return score


def relevant_unreadable(path: Path, raw: str, tokens: list[str], project: str, domain: str) -> bool:
    blob = f"{path.name} {path.stem} {raw} {project} {domain}".lower()
    return any(token and token in blob for token in tokens)


def summarize(doc: CognitionDoc) -> str:
    if doc.type == "evidence":
        return str(doc.meta.get("claim") or "")
    if doc.type == "belief":
        return str(doc.meta.get("statement") or "")
    if doc.type == "principle":
        trigger = doc.meta.get("trigger") or ""
        action = doc.meta.get("preferred_action") or ""
        return f"When {trigger} → prefer {action}"
    return doc.id


def doc_payload(doc: CognitionDoc, superseded: set[str], stale: bool = False) -> dict[str, Any]:
    eff = effective_status(doc, superseded)
    return {
        "id": doc.id,
        "type": doc.type,
        "status": doc.status,
        "effective_status": eff,
        "contested": doc.status == "contested",
        "stale_dependency": stale,
        "summary": summarize(doc),
        "path": str(doc.path),
        "domains": as_list(doc.meta.get("domains")),
        "related_projects": as_list(doc.meta.get("related_projects")),
        "supporting_evidence": as_list(doc.meta.get("supporting_evidence")),
        "contradicting_evidence": as_list(doc.meta.get("contradicting_evidence")),
        "based_on": as_list(doc.meta.get("based_on")),
        "supersedes": as_list(doc.meta.get("supersedes")),
        "validation": doc.meta.get("validation"),
        "confidence": doc.meta.get("confidence"),
    }


def retrieve(
    vault: Path,
    query: str = "",
    project: str = "",
    domain: str = "",
    ids: list[str] | None = None,
    principle_budget: int = 3,
    belief_budget: int = 3,
    evidence_budget: int = 5,
) -> dict[str, Any]:
    store = load_store(vault)
    result: dict[str, Any] = {
        "status": "unavailable",
        "matched_ids": [],
        "principles": [],
        "beliefs": [],
        "evidence": [],
        "historical": [],
        "warnings": [],
        "errors": [],
        "skipped": [],
        "stale_dependencies": [],
        "supersession": [],
        "contested": [],
        "dropped_supporting_evidence": [],
    }
    if not store.available:
        result["errors"].append("cognition store unavailable")
        result["warnings"].append("no cognition store yet")
        return result

    tokens = tokenize(query)
    if project:
        tokens.extend(tokenize(project))
    if domain:
        tokens.extend(tokenize(domain))
    wanted = {item for item in (ids or []) if item}

    skipped_relevant = False
    readable = [doc for doc in store.docs if not doc.parse_error and doc.id]
    for doc in store.docs:
        if doc.parse_error:
            result["skipped"].append({"path": str(doc.path), "reason": doc.parse_error})
            raw = doc.raw or doc.path.name
            if relevant_unreadable(doc.path, raw, tokens, project, domain) or doc.path.stem in wanted:
                skipped_relevant = True
                result["warnings"].append(f"unreadable relevant file: {doc.path}")

    superseded = superseded_ids(readable)
    scored: list[tuple[int, int, CognitionDoc]] = []
    for doc in readable:
        rel = relevance_score(doc, tokens, project, domain)
        sc = rank_score(doc, tokens, project, domain, superseded)
        if wanted and doc.id in wanted:
            rel += 50
            sc += 50
        scored.append((sc, rel, doc))
    scored.sort(key=lambda item: (-item[0], item[2].id))

    def is_match(rel: int, doc: CognitionDoc) -> bool:
        if wanted and doc.id in wanted:
            return True
        return rel > 0 and bool(tokens)

    matching = [doc for sc, rel, doc in scored if is_match(rel, doc)]
    if not matching and not skipped_relevant:
        result["status"] = "no_match"
        return result
    if not matching and skipped_relevant:
        result["status"] = "partial"
        result["warnings"].append("relevant files could not be read; absence claims are unsafe")
        return result

    by_id = {doc.id: doc for doc in readable}
    current_principles: list[CognitionDoc] = []
    for doc in matching:
        if doc.type != "principle":
            continue
        if effective_status(doc, superseded) in {"retired", "superseded"}:
            continue
        current_principles.append(doc)
        if len(current_principles) >= principle_budget:
            break

    beliefs_ordered: list[CognitionDoc] = []
    seen_beliefs: set[str] = set()

    def add_belief(doc: CognitionDoc | None) -> None:
        if doc is None or doc.type != "belief" or doc.id in seen_beliefs:
            return
        seen_beliefs.add(doc.id)
        beliefs_ordered.append(doc)

    for principle in current_principles:
        for cid in as_list(principle.meta.get("based_on")):
            add_belief(by_id.get(cid))
    for doc in matching:
        if doc.type == "belief" and effective_status(doc, superseded) not in {
            "retired",
            "superseded",
        }:
            add_belief(doc)
        if len([b for b in beliefs_ordered if effective_status(b, superseded) not in {"retired", "superseded"}]) >= belief_budget:
            break
    current_beliefs = [
        doc
        for doc in beliefs_ordered
        if effective_status(doc, superseded) not in {"retired", "superseded"}
    ][:belief_budget]
    # keep stale based_on beliefs for dependency warnings even if retired
    for principle in current_principles:
        for cid in as_list(principle.meta.get("based_on")):
            dep = by_id.get(cid)
            if dep and dep not in current_beliefs and dep not in beliefs_ordered:
                beliefs_ordered.append(dep)

    contradicting: list[CognitionDoc] = []
    supporting: list[CognitionDoc] = []
    unresolved_refs = False
    seen_e: set[str] = set()

    def take_evidence(cid: str, bucket: list[CognitionDoc], source_id: str) -> None:
        nonlocal unresolved_refs
        target = by_id.get(cid)
        if target is None:
            unresolved_refs = True
            result["warnings"].append(f"{source_id} references unreadable/missing {cid}")
            return
        if target.id in seen_e:
            return
        seen_e.add(target.id)
        bucket.append(target)

    focus_beliefs = current_beliefs[:]
    for principle in current_principles:
        for cid in as_list(principle.meta.get("based_on")):
            dep = by_id.get(cid)
            if dep and dep not in focus_beliefs:
                focus_beliefs.append(dep)

    for belief in focus_beliefs:
        for cid in as_list(belief.meta.get("contradicting_evidence")):
            take_evidence(cid, contradicting, belief.id)
        for cid in as_list(belief.meta.get("supporting_evidence")):
            take_evidence(cid, supporting, belief.id)

    evidence: list[CognitionDoc] = list(contradicting)
    remain = max(0, evidence_budget - len(evidence))
    dropped: list[str] = []
    for doc in supporting:
        if remain > 0:
            evidence.append(doc)
            remain -= 1
        else:
            dropped.append(doc.id)
    result["dropped_supporting_evidence"] = dropped

    stale_ids: list[str] = []
    for principle in current_principles:
        stale = False
        for cid in as_list(principle.meta.get("based_on")):
            dep = by_id.get(cid)
            if dep is None:
                stale = True
                unresolved_refs = True
                continue
            if effective_status(dep, superseded) in {"retired", "superseded"}:
                stale = True
        if stale:
            stale_ids.append(principle.id)
            result["warnings"].append(
                f"stale_dependency: {principle.id} based_on is retired or superseded"
            )

    historical = [
        doc
        for doc in matching
        if effective_status(doc, superseded) in {"retired", "superseded"}
    ]
    contested_docs = [
        doc
        for doc in current_principles + current_beliefs + evidence
        if doc.status == "contested"
    ]

    result["principles"] = [
        doc_payload(doc, superseded, stale=doc.id in stale_ids) for doc in current_principles
    ]
    result["beliefs"] = [doc_payload(doc, superseded) for doc in current_beliefs]
    result["evidence"] = [doc_payload(doc, superseded) for doc in evidence]
    result["historical"] = [doc_payload(doc, superseded) for doc in historical]
    result["stale_dependencies"] = stale_ids
    result["contested"] = [doc.id for doc in contested_docs]
    result["supersession"] = sorted(superseded)
    matched = [doc.id for doc in current_principles + current_beliefs + evidence]
    result["matched_ids"] = list(dict.fromkeys(matched))

    if skipped_relevant or unresolved_refs:
        result["status"] = "partial"
        result["warnings"].append("retrieval is incomplete; do not claim no relevant cognition")
    else:
        result["status"] = "found"
    return result


def status_transition_allowed(typ: str, before: str, after: str, explicit_reactivate: bool) -> bool:
    if before == after:
        return True
    if typ == "evidence":
        allowed = EVIDENCE_TRANSITIONS
    else:
        allowed = BELIEF_TRANSITIONS
    if (before, after) not in allowed:
        return False
    if before == "retired" and after == "active" and not explicit_reactivate:
        return False
    if typ != "evidence" and before == "retired" and after == "contested":
        return False
    return True
