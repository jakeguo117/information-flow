#!/usr/bin/env python3
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

"""Reusable VNext enrollment detector and bootstrap.

The project is --repo (default: current directory). The protocol checkout is
--protocol-root. Repository names come from arguments and PROJECT_STATE.md.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SUPPORTED_PROTOCOL = "v0.3.0"
SUPPORTED_CONTRACT = "1"
SHA_RE = re.compile(r"[0-9a-f]{40}")
REPO_RE = re.compile(r"^[^/\s]+/[^/\s]+$")
CHANGE_RE = re.compile(r"^WI-CHG-[0-9]{4}$")

REQUIRED_KEYS = (
    "Project ID",
    "Project",
    "Repository",
    "Target Branch",
    "VNext Protocol Version",
    "VNext Protocol Commit",
    "VNext Contract Version",
    "Current Approved Spec",
    "Current Project Baseline",
    "Active Change ID",
    "Active Change",
    "Workflow State",
    "Next Action",
    "Blockers",
    "Jake Decision Needed",
    "Handoff",
    "Review",
    "Verification",
)


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def origin_slug(root: Path) -> str | None:
    found = run_git(root, "remote", "get-url", "origin")
    if found.returncode != 0:
        return None
    url = found.stdout.strip()
    if not url:
        return None
    url = url[:-4] if url.endswith(".git") else url
    if url.startswith("git@github.com:"):
        url = url[len("git@github.com:") :]
    elif "github.com/" in url:
        url = url.split("github.com/", 1)[1]
    return url or None


def parse_state(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        fields.setdefault(key, value.strip())
    return fields


def sha40(value: str) -> str:
    found = SHA_RE.findall(value or "")
    return found[-1] if found else ""


def pin_has_contract(protocol_root: Path, pin: str) -> bool:
    if not SHA_RE.fullmatch(pin):
        return False
    found = run_git(protocol_root, "cat-file", "-e", f"{pin}:scripts/wi_bootstrap.sh")
    sibling = run_git(protocol_root, "cat-file", "-e", f"{pin}:scripts/wi_bootstrap.py")
    return found.returncode == 0 and sibling.returncode == 0


def empty_report(result: str, reason: str) -> dict[str, str]:
    return {
        "result": result,
        "reason": reason,
        "project_id": "",
        "project": "",
        "repository": "",
        "target_branch": "",
        "protocol_version": "",
        "protocol_commit": "",
        "contract_version": "",
        "current_approved_spec": "",
        "baseline": "",
        "implementation_sha": "",
        "active_change_id": "",
        "active_change": "",
        "workflow_state": "",
        "blockers": "",
        "jake_decision_needed": "",
        "next_action": "",
        "handoff": "",
        "review": "",
        "verification": "",
        "idempotency_key": "",
    }


def fill_report(report: dict[str, str], fields: dict[str, str]) -> None:
    report["project_id"] = fields.get("Project ID", "")
    report["project"] = fields.get("Project", "")
    report["repository"] = fields.get("Repository", "")
    report["target_branch"] = fields.get("Target Branch", "")
    report["protocol_version"] = fields.get("VNext Protocol Version", "")
    report["protocol_commit"] = sha40(fields.get("VNext Protocol Commit", ""))
    report["contract_version"] = fields.get("VNext Contract Version", "")
    report["current_approved_spec"] = fields.get("Current Approved Spec", "")
    report["baseline"] = fields.get("Current Project Baseline", "")
    report["implementation_sha"] = sha40(fields.get("Implementation Baseline / Git SHA", ""))
    report["active_change_id"] = fields.get("Active Change ID", "")
    report["active_change"] = fields.get("Active Change", "")
    report["workflow_state"] = fields.get("Workflow State", "")
    report["blockers"] = fields.get("Blockers", "")
    report["jake_decision_needed"] = fields.get("Jake Decision Needed", "")
    report["next_action"] = fields.get("Next Action", "")
    report["handoff"] = fields.get("Handoff", "")
    report["review"] = fields.get("Review", "")
    report["verification"] = fields.get("Verification", "")
    base = sha40(fields.get("Current Approved Spec", "")) or "none"
    report["idempotency_key"] = f"{report['repository']} {report['active_change_id'] or 'none'} {base}"


def spec_path(value: str) -> str:
    if not value or value == "none" or value.startswith("none "):
        return "none"
    return value.split()[0]


def path_inside(root: Path, relative: str) -> bool:
    if relative == "none":
        return True
    if relative.startswith("/") or relative.startswith("\\"):
        return False
    parts = Path(relative).parts
    if ".." in parts:
        return False
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return False
    return candidate.is_file()


def detect(project: Path, protocol_root: Path) -> tuple[dict[str, str], int]:
    if not project.exists() or not project.is_dir() or not os.access(project, os.R_OK | os.X_OK):
        return empty_report("NOT_VERIFIED", "UNREADABLE"), 14
    state_path = project / "PROJECT_STATE.md"
    if state_path.exists() and not os.access(state_path, os.R_OK):
        return empty_report("NOT_VERIFIED", "UNREADABLE"), 14
    if not state_path.exists():
        return empty_report("VNEXT_NOT_INITIALIZED", "ABSENT"), 0
    try:
        fields = parse_state(state_path.read_text(encoding="utf-8"))
    except OSError:
        return empty_report("NOT_VERIFIED", "UNREADABLE"), 14

    report = empty_report("VNEXT_NOT_INITIALIZED", "PARTIAL")
    fill_report(report, fields)
    if fields.get("Jake Opt Out", "").lower() == "yes":
        report["result"] = "VNEXT_NOT_INITIALIZED"
        report["reason"] = "JAKE_OPT_OUT"
        return report, 0
    missing = [key for key in REQUIRED_KEYS if not fields.get(key, "").strip()]
    if missing:
        report["reason"] = "PARTIAL"
        return report, 0
    if (
        fields["VNext Protocol Version"] != SUPPORTED_PROTOCOL
        or fields["VNext Contract Version"] != SUPPORTED_CONTRACT
        or not pin_has_contract(protocol_root, sha40(fields["VNext Protocol Commit"]))
    ):
        report["reason"] = "UNSUPPORTED"
        return report, 0

    change_id = fields["Active Change ID"]
    change_path = fields["Active Change"]
    both_none = change_id == "none" and change_path == "none"
    both_set = CHANGE_RE.fullmatch(change_id) and change_path not in ("", "none")
    spec = spec_path(fields["Current Approved Spec"])
    origin = origin_slug(project)
    change_conflict = (not both_none) and (not both_set)
    invalid = (
        not REPO_RE.fullmatch(fields["Repository"])
        or change_conflict
        or not path_inside(project, spec)
        or (origin is not None and origin != fields["Repository"])
        or (spec == "none" and fields["Workflow State"] == "Implement")
    )
    if invalid:
        report["reason"] = "INVALID"
        return report, 0
    report["result"] = "VNEXT_INITIALIZED"
    report["reason"] = "NONE"
    return report, 0


def project_name(repository: str) -> str:
    return repository.split("/", 1)[1]


def contract_text(repository: str, branch: str, pin: str) -> str:
    name = project_name(repository)
    return "\n".join(
        [
            f"Project: {name}",
            f"Project ID: {name}",
            "Project Phase: Phase 0",
            f"Repository: {repository}",
            f"Target Branch: {branch}",
            f"VNext Protocol Version: {SUPPORTED_PROTOCOL}",
            f"VNext Protocol Commit: {pin}",
            f"VNext Contract Version: {SUPPORTED_CONTRACT}",
            "Current Approved Spec: none",
            "Current Project Baseline: none",
            "Implementation Baseline / Git SHA: none",
            "Active Change ID: none",
            "Active Change: none",
            "Workflow State: Draft",
            "Blockers: none",
            "Jake Decision Needed: none",
            "Next Action: Capture requirements. Implementation is not authorized.",
            "Handoff: none",
            "Review: none",
            "Verification: none",
            "CI: none",
            "Authority graph: none",
            "",
        ]
    )


def write_enrollment(project: Path, protocol_root: Path, repository: str, branch: str, pin: str) -> None:
    text = contract_text(repository, branch, pin)
    (project / "PROJECT_STATE.md").write_text(text, encoding="utf-8")
    template_dir = project / "templates"
    template_dir.mkdir(exist_ok=True)
    source = protocol_root / ".specify" / "templates" / "overrides" / "handoff-template.md"
    if not source.is_file():
        source = protocol_root / "templates" / "handoff.md"
    if source.is_file():
        (template_dir / "handoff.md").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    agents = project / "AGENTS.md"
    if not agents.exists():
        agents.write_text(
            "# Project entry\n\nRead PROJECT_STATE.md before acting. That file is the project index. It grants no extra authority and duplicates no requirements.\n",
            encoding="utf-8",
        )


def same_enrollment(report: dict[str, str], repository: str, branch: str, pin: str) -> bool:
    return (
        report["result"] == "VNEXT_INITIALIZED"
        and report["repository"] == repository
        and report["target_branch"] == branch
        and report["protocol_commit"] == pin
    )


def bootstrap(args: argparse.Namespace) -> int:
    if args.apply:
        print(
            "bootstrap: --apply is not migrated; it would write a VNext PROJECT_STATE enrollment",
            file=sys.stderr,
        )
        return 2
    project = Path(args.repo).resolve()
    protocol_root = Path(args.protocol_root).resolve()
    if not REPO_RE.fullmatch(args.repository):
        print("bootstrap: repository must be owner/name", file=sys.stderr)
        return 2
    if not args.branch.strip():
        print("bootstrap: branch is empty", file=sys.stderr)
        return 2
    if not pin_has_contract(protocol_root, args.protocol_commit):
        print("bootstrap: protocol commit does not contain the contract", file=sys.stderr)
        return 2
    report, code = detect(project, protocol_root)
    if code == 14:
        print(json.dumps(report))
        return 14
    if same_enrollment(report, args.repository, args.branch, args.protocol_commit):
        print(json.dumps(report))
        return 0
    if report["reason"] != "ABSENT":
        print(json.dumps(report))
        print(f"bootstrap: refused reason={report['reason']}", file=sys.stderr)
        return 4
    if args.preview:
        print("BOOTSTRAP_PREVIEW")
        print(contract_text(args.repository, args.branch, args.protocol_commit), end="")
        return 0
    if not args.apply:
        print("bootstrap: refusing to write without --apply", file=sys.stderr)
        return 2
    write_enrollment(project, protocol_root, args.repository, args.branch, args.protocol_commit)
    confirmed, confirmed_code = detect(project, protocol_root)
    print(json.dumps(confirmed))
    if confirmed_code != 0 or confirmed["result"] != "VNEXT_INITIALIZED":
        return confirmed_code or 4
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=os.getcwd())
    parser.add_argument("--protocol-root", required=True)
    parser.add_argument("--detect", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--bootstrap", action="store_true")
    parser.add_argument("--repository", default="")
    parser.add_argument("--branch", default="")
    parser.add_argument("--protocol-commit", default="")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    project = Path(args.repo).resolve()
    protocol_root = Path(args.protocol_root).resolve()
    if args.detect:
        report, code = detect(project, protocol_root)
        if args.json or True:
            print(json.dumps(report))
        return code
    if args.bootstrap:
        return bootstrap(args)
    parser.error("choose --detect or --bootstrap")
    return 2


if __name__ == "__main__":
    sys.exit(main())
