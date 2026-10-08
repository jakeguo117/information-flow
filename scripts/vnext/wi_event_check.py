#!/usr/bin/env python3
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

"""Admit a normalized Strategy event against a durable handoff.

The system derives the canonical effect identity from the scope tuple.
A caller-supplied idempotency key is delivery metadata, not that identity.
"""

import hashlib
import json
import os
import re
import sys
import time

ALLOWED = {
    "schema_version",
    "event_kind",
    "repository",
    "project_id",
    "change_id",
    "decision_id",
    "escalation_id",
    "authority_ref",
    "record_path",
    "idempotency_key",
}
KINDS = {
    "capture_request",
    "strategy_approved",
    "material_escalation",
    "strategy_resolved",
}
TERMINAL = {"closed", "converged", "new baseline"}
STOPS = (
    "STOP — JAKE DECISION REQUIRED",
    "STOP — JAKE COST APPROVAL REQUIRED",
)


def field(text, key):
    prefix = key + ": "
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):]
    return ""


def reject(reason):
    print(f"event: reject reason={reason}")
    return 1


def canonical(event):
    parts = [
        event["repository"],
        event["project_id"],
        event["change_id"],
        event["authority_ref"],
        event["decision_id"],
        event["event_kind"],
    ]
    escalation = event.get("escalation_id") or ""
    if escalation:
        parts.append(escalation)
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def is_terminal(workflow):
    normalized = workflow.strip().lower()
    if normalized in TERMINAL:
        return True
    tokens = [token for token in re.split(r"[^a-z0-9]+", normalized) if token]
    joined = " ".join(tokens)
    if joined in TERMINAL or "new baseline" in joined:
        return True
    if "closed" in tokens or "converged" in tokens:
        return True
    return False


def is_stopped(handoff):
    action = field(handoff, "next_bounded_action").strip()
    return any(action == stop or action.startswith(stop) for stop in STOPS)


def predecessors(handoff):
    return {
        item.strip()
        for item in field(handoff, "predecessor_decision_id").split(",")
        if item.strip() and item.strip() != "none"
    }


def parse_effects(lines):
    records = []
    for line in lines:
        parts = line.split()
        if len(parts) < 4:
            continue
        records.append(
            {
                "state": parts[0],
                "key": parts[1],
                "kind": parts[2],
                "decision": parts[3],
                "caller": parts[4] if len(parts) > 4 else "",
                "raw": line,
            }
        )
    return records


def main(argv):
    if len(argv) != 5 or argv[1] != "--check":
        print(
            "Usage: wi_event_check.py --check <event.json> <handoff.md> <effects>",
            file=sys.stderr,
        )
        return 2
    event_path, handoff_path, effects_path = argv[2:]
    try:
        event = json.loads(open(event_path, encoding="utf-8").read())
    except (OSError, json.JSONDecodeError):
        return reject("payload-authority")
    if not isinstance(event, dict):
        return reject("payload-authority")
    if set(event) - ALLOWED:
        return reject("payload-authority")
    if event.get("schema_version") != 1 or event.get("event_kind") not in KINDS:
        return reject("payload-authority")
    for key in (
        "repository",
        "project_id",
        "change_id",
        "decision_id",
        "record_path",
        "idempotency_key",
    ):
        value = event.get(key)
        if not isinstance(value, str) or not value.strip() or any(ch.isspace() for ch in value):
            return reject("payload-authority")
    escalation = event.get("escalation_id", "")
    if not isinstance(escalation, str):
        return reject("payload-authority")
    if not re.fullmatch(r"[0-9a-f]{40}", event.get("authority_ref", "")):
        return reject("payload-authority")

    handoff = open(handoff_path, encoding="utf-8").read()
    if (
        event["repository"] != field(handoff, "repository")
        or event["project_id"] != field(handoff, "project_id")
        or event["change_id"] != field(handoff, "change_id")
    ):
        return reject("repository")
    if event["record_path"] != field(handoff, "record_path"):
        return reject("authority")
    if is_terminal(field(handoff, "workflow_state")):
        return reject("closed")
    if field(handoff, "conflict_decision_id") not in ("", "none"):
        return reject("conflict")
    if is_stopped(handoff):
        return reject("stop")

    current = field(handoff, "decision_id")
    if event["decision_id"] != current:
        if event["decision_id"] in predecessors(handoff):
            print("event: noop reason=superseded")
            return 0
        return reject("unknown-decision")

    approved = field(handoff, "approved_content")
    if event["event_kind"] == "capture_request":
        base = field(handoff, "expected_remote_sha")
        if event["authority_ref"] not in {approved, base}:
            return reject("authority")
    elif event["authority_ref"] != approved:
        return reject("authority")

    key = canonical(event)
    caller = event["idempotency_key"]
    lock = effects_path + ".lock"
    acquired = False
    for _ in range(40):
        try:
            os.mkdir(lock)
            acquired = True
            break
        except FileExistsError:
            time.sleep(0.05)
    if not acquired:
        return reject("lock")
    try:
        lines = []
        if os.path.exists(effects_path):
            lines = [
                line
                for line in open(effects_path, encoding="utf-8").read().splitlines()
                if line.strip()
            ]
        records = parse_effects(lines)
        for record in records:
            if record["key"] != key:
                continue
            if record["kind"] != event["event_kind"] or record["decision"] != event["decision_id"]:
                print("event: reject reason=conflict")
                return 1
            if record["state"] == "pending":
                updated = [
                    (
                        f"acknowledged {key} {event['event_kind']} {event['decision_id']} {caller}"
                        if item == record["raw"]
                        else item
                    )
                    for item in lines
                ]
                with open(effects_path, "w", encoding="utf-8") as handle:
                    handle.write("\n".join(updated) + "\n")
            print(f"event: ack key={key} state={record['state']}")
            return 0
        record = f"pending {key} {event['event_kind']} {event['decision_id']} {caller}"
        with open(effects_path, "a", encoding="utf-8") as handle:
            handle.write(record + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        print(f"event: admit key={key} kind={event['event_kind']}")
        return 0
    finally:
        os.rmdir(lock)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
