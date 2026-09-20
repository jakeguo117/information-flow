#!/usr/bin/env python3
"""Sole Agent-controlled entry point for persistent Cognition mutation.

Create, update, and retry inspect disk. Success is allowed only after readback
and canonical validation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from cognition_lib import (
    SCHEMA_VERSION,
    TYPE_DIRS,
    CognitionDoc,
    atomic_write,
    cognition_root,
    find_duplicate,
    fingerprint,
    load_store,
    merge_proposed,
    parse_markdown,
    restore_snapshot,
    status_transition_allowed,
    target_path,
    type_dir,
    validate_docs,
)


def emit(payload: dict[str, Any], ok: bool) -> int:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if ok else 2


def load_approval(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("approval must be a JSON object")
    return data


def proposed_target(vault: Path, doc: CognitionDoc) -> Path:
    if doc.path.suffix == ".md" and doc.path.parent.name == TYPE_DIRS.get(doc.type, ""):
        try:
            doc.path.relative_to(cognition_root(vault))
            return doc.path
        except ValueError:
            pass
    return type_dir(vault, doc.type) / f"{doc.id}.md"


def semantic_equal(left: str, right: str) -> bool:
    if left == right:
        return True
    a = parse_markdown(left)
    b = parse_markdown(right)
    if a.parse_error or b.parse_error:
        return False
    return a.meta == b.meta and a.body.strip() == b.body.strip()


def perform(
    vault: Path,
    action: str,
    payload_text: str,
    approval: dict[str, Any],
    direct_instruction: bool,
) -> tuple[dict[str, Any], bool]:
    proposed = parse_markdown(payload_text)
    if proposed.parse_error:
        return {
            "status": "validation_error",
            "errors": [proposed.parse_error],
            "schema_version": SCHEMA_VERSION,
        }, False

    proposed.path = proposed_target(vault, proposed)
    approval_kind = str(approval.get("kind") or "")
    approval_id = str(approval.get("id") or "")
    approval_type = str(approval.get("type") or "")
    approval_fp = approval.get("target_fingerprint")
    payload_sha = approval.get("payload_sha256")

    if approval_id != proposed.id or approval_type != proposed.type:
        return {
            "status": "unauthorized",
            "message": "approval does not bind to this type/id payload",
            "id": proposed.id,
        }, False
    if payload_sha and payload_sha != fingerprint(payload_text):
        return {
            "status": "stale_approval",
            "message": "approved payload changed before write",
            "id": proposed.id,
        }, False

    store = load_store(vault)
    if not vault.is_dir():
        return {
            "status": "unavailable",
            "message": "vault missing; will not write cognition elsewhere",
            "id": proposed.id,
        }, False

    merged = merge_proposed(store, proposed) if store.available else [proposed]
    outside = store.outside if store.available else []
    errors = validate_docs(merged, outside)
    if errors:
        return {
            "status": "validation_error",
            "errors": errors,
            "id": proposed.id,
        }, False

    target = proposed.path
    existing_raw = target.read_text(encoding="utf-8") if target.is_file() else None
    existing_fp = fingerprint(existing_raw) if existing_raw is not None else None

    if action == "retry":
        if existing_raw is not None:
            if semantic_equal(existing_raw, payload_text):
                post = validate_docs(load_store(vault).docs, load_store(vault).outside)
                if post:
                    return {
                        "status": "validation_error",
                        "errors": post,
                        "id": proposed.id,
                        "path": str(target),
                    }, False
                return {
                    "status": "success",
                    "already_persisted": True,
                    "id": proposed.id,
                    "path": str(target),
                    "fingerprint": existing_fp,
                    "schema_version": SCHEMA_VERSION,
                }, True
            return {
                "status": "conflict",
                "message": "persisted content differs from proposed payload",
                "id": proposed.id,
                "path": str(target),
                "fingerprint": existing_fp,
            }, False

    if approval_kind == "create" and action != "update":
        duplicate = find_duplicate(store, proposed) if store.available else None
        if existing_raw is not None and not semantic_equal(existing_raw, payload_text):
            duplicate = parse_markdown(existing_raw, target)
        if duplicate is not None and (
            existing_raw is None or not semantic_equal(existing_raw, payload_text)
        ):
            return {
                "status": "needs_update_authorization",
                "message": "create approval cannot mutate an existing cognition object",
                "id": proposed.id,
                "existing_id": duplicate.id,
                "existing_path": str(duplicate.path),
            }, False
        if existing_raw is not None and semantic_equal(existing_raw, payload_text):
            if action == "retry":
                return {
                    "status": "success",
                    "already_persisted": True,
                    "id": proposed.id,
                    "path": str(target),
                    "fingerprint": existing_fp,
                    "schema_version": SCHEMA_VERSION,
                }, True
            return {
                "status": "needs_update_authorization",
                "message": "create approval cannot mutate an existing cognition object",
                "id": proposed.id,
                "existing_id": proposed.id,
                "existing_path": str(target),
            }, False

    if approval_kind == "update" or action == "update":
        if existing_raw is None:
            return {
                "status": "conflict",
                "message": "update target is missing",
                "id": proposed.id,
                "path": str(target),
            }, False
        if not direct_instruction and approval_fp != existing_fp:
            return {
                "status": "stale_approval",
                "message": "target fingerprint changed since approval; reload and re-authorize",
                "id": proposed.id,
                "path": str(target),
                "observed_fingerprint": existing_fp,
            }, False
        previous = parse_markdown(existing_raw, target)
        if previous.parse_error is None and previous.status != proposed.status:
            if not status_transition_allowed(
                proposed.type,
                previous.status,
                proposed.status,
                explicit_reactivate=direct_instruction,
            ):
                return {
                    "status": "unauthorized",
                    "message": (
                        f"status {previous.status} → {proposed.status} is not allowed"
                        " without the matching authorization"
                    ),
                    "id": proposed.id,
                }, False

    snapshot = existing_raw
    try:
        atomic_write(target, payload_text)
        readback = target.read_text(encoding="utf-8")
        if readback != payload_text:
            restore_snapshot(target, snapshot)
            return {
                "status": "conflict",
                "message": "readback did not match proposed payload",
                "id": proposed.id,
                "path": str(target),
            }, False
        post_store = load_store(vault)
        post_errors = validate_docs(post_store.docs, post_store.outside)
        if post_errors:
            restore_snapshot(target, snapshot)
            return {
                "status": "validation_error",
                "errors": post_errors,
                "id": proposed.id,
                "path": str(target),
                "restored": True,
            }, False
    except OSError as exc:
        restore_snapshot(target, snapshot)
        return {
            "status": "unavailable",
            "message": f"write failed: {exc}",
            "id": proposed.id,
            "path": str(target),
        }, False

    return {
        "status": "success",
        "already_persisted": False,
        "id": proposed.id,
        "path": str(target),
        "fingerprint": fingerprint(readback),
        "schema_version": SCHEMA_VERSION,
    }, True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write DigitalBrain Cognition Markdown")
    parser.add_argument("action", choices=["create", "update", "retry"])
    parser.add_argument("--vault", required=True)
    parser.add_argument("--payload", required=True)
    parser.add_argument("--approval", required=True)
    parser.add_argument(
        "--direct-instruction",
        action="store_true",
        help="Jake's current instruction already covers this exact mutation",
    )
    args = parser.parse_args(argv)

    vault = Path(args.vault).expanduser()
    payload_path = Path(args.payload).expanduser()
    approval_path = Path(args.approval).expanduser()
    if not payload_path.is_file():
        return emit({"status": "unavailable", "message": f"payload missing: {payload_path}"}, False)
    if not approval_path.is_file():
        return emit({"status": "unauthorized", "message": f"approval missing: {approval_path}"}, False)
    try:
        approval = load_approval(approval_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return emit({"status": "unauthorized", "message": f"invalid approval: {exc}"}, False)

    payload_text = payload_path.read_text(encoding="utf-8")
    if not payload_text.endswith("\n"):
        payload_text += "\n"
    result, ok = perform(
        vault,
        args.action,
        payload_text,
        approval,
        direct_instruction=args.direct_instruction,
    )
    return emit(result, ok)


if __name__ == "__main__":
    raise SystemExit(main())
