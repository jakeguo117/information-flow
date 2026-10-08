#!/usr/bin/env python3
# AIC port of a VNext guard.
# Source: workspace-infrastructure-vnext @c99355daf488
# This script does not grant standing merge, push, or write permission.
# It does not adopt the VNext baseline and it does not record an AIC acceptance PASS.
# PROJECT_STATE.md is intentionally not part of this port; checks that require it fail closed.

"""Check the canonical Workspace Infrastructure VNext authority graph.

This script does not fetch the network. External verification uses an
observation file supplied by a reader that already reached the source.
Without that observation, external authorities stay NOT_VERIFIED.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

GRAPH_RELATIVE = "docs/authority-graph.json"
DISCOVERY_LINE = "Authority graph: docs/authority-graph.json"
MODIFIED_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
OUTCOMES = {"FAIL", "NOT_VERIFIED", "RECONCILE"}
ENTRY_KEYS = (
    "role",
    "purpose",
    "source_type",
    "locator",
    "identifier",
    "revision",
    "status",
    "normative",
    "validation",
    "on_unavailable",
    "on_identity_mismatch",
    "on_revision_mismatch",
)
REQUIRED_ROLES = {
    "engineering-requirements": {
        "source_type": "git-path",
        "normative": True,
        "status": "current",
    },
    "workflow-lifecycle": {
        "source_type": "google-drive-folder",
        "normative": True,
        "status": "current",
    },
    "architecture": {
        "source_type": "google-drive-file",
        "normative": True,
        "status": "current",
    },
    "implementation": {
        "source_type": "github-repository",
        "normative": True,
        "status": "current",
    },
    "projection": {
        "source_type": "linear-project",
        "normative": False,
        "status": "current",
    },
}
CONSUMER_PATHS = (
    ".cursor/agents/reviewer.md",
    ".cursor/agents/verifier.md",
    ".specify/workflows/change-lifecycle/workflow.yml",
    "scripts/wi_preflight.sh",
    "README.md",
    "docs/reconciliation.md",
)
SEVERITY = {0: 0, 10: 1, 14: 2, 12: 3, 11: 4}


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.code = 0

    def add(self, line: str) -> None:
        self.lines.append(line)

    def raise_code(self, code: int) -> None:
        if SEVERITY.get(code, 0) > SEVERITY.get(self.code, 0):
            self.code = code


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        text=True,
        capture_output=True,
    )


def detect_repo(root: Path) -> str:
    override = os.environ.get("WI_PREFLIGHT_REPOSITORY_DETECTED")
    if override:
        return override
    proc = git(root, "remote", "get-url", "origin")
    url = proc.stdout.strip()
    if url.endswith(".git"):
        url = url[:-4]
    if url.startswith("git@github.com:"):
        return url[len("git@github.com:") :]
    marker = "github.com/"
    if marker in url:
        return url.split(marker, 1)[1]
    if url:
        return url
    return os.environ.get("GITHUB_REPOSITORY", "")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_schema(graph: dict) -> list[str]:
    errors: list[str] = []
    if graph.get("schema_version") != 1:
        errors.append("schema_version")
    authorities = graph.get("authorities")
    if not isinstance(authorities, list):
        return errors + ["authorities"]
    roles: list[str] = []
    for entry in authorities:
        if not isinstance(entry, dict):
            errors.append("entry")
            continue
        role = entry.get("role")
        roles.append(role if isinstance(role, str) else "")
        for key in ENTRY_KEYS:
            if key not in entry or entry[key] in ("", None):
                errors.append(f"{role} missing {key}")
        if not isinstance(entry.get("normative"), bool):
            errors.append(f"{role} normative")
        for outcome_key in (
            "on_unavailable",
            "on_identity_mismatch",
            "on_revision_mismatch",
        ):
            if entry.get(outcome_key) not in OUTCOMES:
                errors.append(f"{role} {outcome_key}")
        revision = entry.get("revision")
        if not isinstance(revision, dict) or "kind" not in revision or not isinstance(
            revision.get("pinned"), bool
        ):
            errors.append(f"{role} revision")
            continue
        if revision["pinned"]:
            errors.extend(validate_pin(str(role), revision))
        if entry.get("source_type") == "git-path":
            locator = Path(str(entry.get("locator")))
            if locator.is_absolute() or ".." in locator.parts:
                errors.append(f"{role} locator")
    for role, expected in REQUIRED_ROLES.items():
        matches = [entry for entry in authorities if isinstance(entry, dict) and entry.get("role") == role]
        if len(matches) != 1:
            errors.append(f"role {role}")
            continue
        entry = matches[0]
        if entry.get("source_type") != expected["source_type"]:
            errors.append(f"{role} source_type")
        if entry.get("normative") is not expected["normative"]:
            errors.append(f"{role} normative flag")
        if entry.get("status") != expected["status"]:
            errors.append(f"{role} status")
    if len(roles) != len(set(roles)):
        errors.append("duplicate role")
    return errors


def validate_pin(role: str, revision: dict) -> list[str]:
    errors: list[str] = []
    kind = revision.get("kind")
    if kind == "drive-metadata":
        if not isinstance(revision.get("size"), int) or revision["size"] <= 0:
            errors.append(f"{role} size")
        if not isinstance(revision.get("modified"), str) or not MODIFIED_RE.match(
            revision["modified"]
        ):
            errors.append(f"{role} modified")
        if not revision.get("document_version"):
            errors.append(f"{role} document_version")
    elif kind == "drive-member-metadata":
        if not revision.get("document_version"):
            errors.append(f"{role} document_version")
        members = revision.get("members")
        if not isinstance(members, list) or not members:
            errors.append(f"{role} members")
            return errors
        seen: set[str] = set()
        for member in members:
            if not isinstance(member, dict):
                errors.append(f"{role} member")
                continue
            identifier = member.get("identifier")
            if not identifier or identifier in seen:
                errors.append(f"{role} member identifier")
            else:
                seen.add(identifier)
            if not member.get("name"):
                errors.append(f"{role} member name")
            if not isinstance(member.get("size"), int) or member["size"] <= 0:
                errors.append(f"{role} member size")
            if not isinstance(member.get("modified"), str) or not MODIFIED_RE.match(
                member["modified"]
            ):
                errors.append(f"{role} member modified")
    else:
        errors.append(f"{role} pinned kind")
    if "sha256" in revision and (
        not isinstance(revision["sha256"], str) or len(revision["sha256"]) != 64
    ):
        errors.append(f"{role} sha256")
    return errors


def line_for(
    entry: dict,
    identity: str,
    revision_state: str,
    revision_value: str = "",
) -> str:
    suffix = f" revision_value={revision_value}" if revision_value else ""
    return (
        "authority"
        f" role={entry['role']}"
        f" source_type={entry['source_type']}"
        f" normative={'true' if entry['normative'] else 'false'}"
        f" identity={identity}"
        f" revision={revision_state}"
        f" identifier={entry['identifier']}"
        f"{suffix}"
    )


def observation_for(observation: dict | None, role: str) -> dict | None:
    if not observation:
        return None
    authorities = observation.get("authorities")
    if not isinstance(authorities, dict):
        return None
    found = authorities.get(role)
    if found is None:
        return None
    if not isinstance(found, dict):
        return {"available": False}
    return found


def check_requirements(root: Path, entry: dict, observed: dict | None, report: Report) -> None:
    path = root / str(entry["locator"])
    if not path.is_file():
        report.add(line_for(entry, "FAIL", "NOT_VERIFIED"))
        report.raise_code(11)
        return
    text = path.read_text(encoding="utf-8")
    locator = str(entry["locator"])
    # 008 is the converged v0.3.0 requirements source. Its status line is
    # "Status: APPROVED". Do not require the 001 phrase "CURRENT / APPROVED".
    status_ok = "Status: CURRENT / APPROVED" in text or (
        locator == "specs/008-project-bootstrap/spec.md"
        and "Status: APPROVED" in text
        and "Change: WI-CHG-0008" in text
        and "WI-REQ-034" in text
    )
    if not status_ok or "WI-REQ-001" not in text or "WI-REQ-030" not in text:
        report.add(line_for(entry, "FAIL", "NOT_VERIFIED"))
        report.raise_code(11)
        return
    proc = git(root, "hash-object", str(path))
    blob = proc.stdout.strip()
    if proc.returncode != 0 or not SHA_RE.match(blob):
        report.add(line_for(entry, "VERIFIED", "NOT_VERIFIED"))
        return
    if observed and observed.get("available") is False:
        report.add(line_for(entry, "VERIFIED", "VERIFIED", blob))
        return
    if observed and observed.get("identifier") not in (None, entry["identifier"]):
        report.add(line_for(entry, "FAIL", "NOT_VERIFIED"))
        report.raise_code(11)
        return
    if observed and observed.get("blob") not in (None, blob):
        report.add(line_for(entry, "VERIFIED", "RECONCILE", blob))
        report.raise_code(12)
        return
    report.add(line_for(entry, "VERIFIED", "VERIFIED", blob))


def check_implementation(root: Path, entry: dict, observed: dict | None, report: Report) -> None:
    actual = detect_repo(root)
    if actual != entry["identifier"]:
        report.add(line_for(entry, "FAIL", "NOT_VERIFIED"))
        report.raise_code(11)
        return
    if not observed or observed.get("available") is False:
        report.add(line_for(entry, "VERIFIED", "NOT_VERIFIED"))
        return
    if observed.get("identifier") not in (None, entry["identifier"]):
        report.add(line_for(entry, "FAIL", "NOT_VERIFIED"))
        report.raise_code(11)
        return
    remote_sha = observed.get("remote_sha")
    if not isinstance(remote_sha, str) or not SHA_RE.match(remote_sha):
        report.add(line_for(entry, "VERIFIED", "NOT_VERIFIED"))
        return
    report.add(line_for(entry, "VERIFIED", "VERIFIED", remote_sha))


def metadata_mismatch(pinned: dict, observed: dict) -> bool:
    if "size" in observed and observed["size"] != pinned["size"]:
        return True
    if "modified" in observed and observed["modified"] != pinned["modified"]:
        return True
    if "sha256" in pinned and "sha256" in observed and observed["sha256"] != pinned["sha256"]:
        return True
    if "name" in observed and observed["name"] != pinned.get("name"):
        return True
    return False


def metadata_complete(pinned: dict, observed: dict) -> bool:
    if "size" not in observed or "modified" not in observed:
        return False
    if "sha256" in pinned and "sha256" not in observed:
        return False
    return True


def check_drive_file(entry: dict, observed: dict | None, report: Report) -> None:
    if not observed or observed.get("available") is False:
        report.add(line_for(entry, "NOT_VERIFIED", "NOT_VERIFIED"))
        return
    if observed.get("identifier") != entry["identifier"]:
        report.add(line_for(entry, "FAIL", "NOT_VERIFIED"))
        report.raise_code(11)
        return
    revision = entry["revision"]
    if not revision["pinned"]:
        report.add(line_for(entry, "VERIFIED", "NOT_VERIFIED"))
        return
    if metadata_mismatch(revision, observed):
        report.add(line_for(entry, "VERIFIED", "RECONCILE"))
        report.raise_code(12)
        return
    if not metadata_complete(revision, observed):
        report.add(line_for(entry, "VERIFIED", "NOT_VERIFIED"))
        return
    report.add(line_for(entry, "VERIFIED", "VERIFIED"))


def check_drive_folder(entry: dict, observed: dict | None, report: Report) -> None:
    if not observed or observed.get("available") is False:
        report.add(line_for(entry, "NOT_VERIFIED", "NOT_VERIFIED"))
        return
    if observed.get("identifier") != entry["identifier"]:
        report.add(line_for(entry, "FAIL", "NOT_VERIFIED"))
        report.raise_code(11)
        return
    members = observed.get("members")
    if members is None:
        report.add(line_for(entry, "VERIFIED", "NOT_VERIFIED"))
        return
    if not isinstance(members, list):
        report.add(line_for(entry, "VERIFIED", "RECONCILE"))
        report.raise_code(12)
        return
    observed_members = {}
    for member in members:
        if not isinstance(member, dict) or "identifier" not in member:
            report.add(line_for(entry, "VERIFIED", "RECONCILE"))
            report.raise_code(12)
            return
        observed_members[member["identifier"]] = member
    pinned_members = {member["identifier"]: member for member in entry["revision"]["members"]}
    if set(observed_members) != set(pinned_members):
        report.add(line_for(entry, "VERIFIED", "RECONCILE"))
        report.raise_code(12)
        return
    incomplete = False
    for identifier, pinned in pinned_members.items():
        observed_member = observed_members[identifier]
        if metadata_mismatch(pinned, observed_member):
            report.add(line_for(entry, "VERIFIED", "RECONCILE"))
            report.raise_code(12)
            return
        if not metadata_complete(pinned, observed_member):
            incomplete = True
    if incomplete:
        report.add(line_for(entry, "VERIFIED", "NOT_VERIFIED"))
        return
    report.add(line_for(entry, "VERIFIED", "VERIFIED"))


def check_projection(entry: dict, observed: dict | None, report: Report) -> None:
    if not observed or observed.get("available") is False:
        report.add(line_for(entry, "NOT_VERIFIED", "NOT_VERIFIED"))
        return
    if observed.get("identifier") != entry["identifier"]:
        report.add(line_for(entry, "FAIL", "NOT_VERIFIED"))
        report.raise_code(11)
        return
    report.add(line_for(entry, "VERIFIED", "NOT_VERIFIED"))


def apply_require_verified(report: Report, require_verified: set[str]) -> None:
    if not require_verified:
        return
    by_role = {}
    for line in report.lines:
        if not line.startswith("authority "):
            continue
        fields = dict(part.split("=", 1) for part in line.split() if "=" in part)
        by_role[fields.get("role")] = fields
    for role in require_verified:
        fields = by_role.get(role)
        if not fields or fields.get("identity") != "VERIFIED" or fields.get("revision") != "VERIFIED":
            report.raise_code(14)


def summary(code: int) -> str:
    if code == 0:
        return "authority-graph: ok"
    if code == 12:
        return "authority-graph: RECONCILE"
    if code == 14:
        return "authority-graph: NOT_VERIFIED"
    return "authority-graph: FAIL"


def run_check(
    root: Path,
    graph_path: Path,
    observation: dict | None,
    require_verified: set[str],
    enforce_discovery: bool,
) -> Report:
    report = Report()
    if enforce_discovery:
        state_path = root / "PROJECT_STATE.md"
        if not state_path.is_file() or DISCOVERY_LINE not in state_path.read_text(
            encoding="utf-8"
        ).splitlines():
            report.add("authority-graph: FAIL discovery")
            report.raise_code(10)
            report.add(summary(report.code))
            return report
        reconciliation = root / "docs/reconciliation.md"
        if not reconciliation.is_file() or GRAPH_RELATIVE not in reconciliation.read_text(
            encoding="utf-8"
        ):
            report.add("authority-graph: FAIL discovery")
            report.raise_code(10)
            report.add(summary(report.code))
            return report
    if not graph_path.is_file():
        report.add("authority-graph: FAIL missing binding")
        report.raise_code(10)
        report.add(summary(report.code))
        return report
    try:
        graph = load_json(graph_path)
    except (OSError, json.JSONDecodeError):
        report.add("authority-graph: FAIL missing binding")
        report.raise_code(10)
        report.add(summary(report.code))
        return report
    errors = validate_schema(graph)
    if errors:
        report.add("authority-graph: FAIL missing binding")
        report.raise_code(10)
        report.add(summary(report.code))
        return report
    for entry in graph["authorities"]:
        observed = observation_for(observation, entry["role"])
        source_type = entry["source_type"]
        if source_type == "git-path":
            check_requirements(root, entry, observed, report)
        elif source_type == "github-repository":
            check_implementation(root, entry, observed, report)
        elif source_type == "google-drive-file":
            check_drive_file(entry, observed, report)
        elif source_type == "google-drive-folder":
            check_drive_folder(entry, observed, report)
        elif source_type == "linear-project":
            check_projection(entry, observed, report)
        else:
            report.add(line_for(entry, "NOT_VERIFIED", "NOT_VERIFIED"))
    apply_require_verified(report, require_verified)
    report.add(summary(report.code))
    return report


def external_identifiers(graph: dict) -> set[str]:
    found: set[str] = set()
    for entry in graph["authorities"]:
        if entry["source_type"] in {"google-drive-file", "google-drive-folder", "linear-project"}:
            found.add(entry["identifier"])
        for member in entry["revision"].get("members", []):
            found.add(member["identifier"])
    return found


def write_graph(path: Path, graph: dict) -> None:
    path.write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")


def matching_observation(graph: dict, role: str) -> dict:
    entry = next(item for item in graph["authorities"] if item["role"] == role)
    revision = entry["revision"]
    if revision["kind"] == "drive-metadata":
        body = {
            "available": True,
            "identifier": entry["identifier"],
            "size": revision["size"],
            "modified": revision["modified"],
        }
    elif revision["kind"] == "drive-member-metadata":
        body = {
            "available": True,
            "identifier": entry["identifier"],
            "members": [
                {
                    "identifier": member["identifier"],
                    "name": member["name"],
                    "size": member["size"],
                    "modified": member["modified"],
                }
                for member in revision["members"]
            ],
        }
    else:
        body = {"available": True, "identifier": entry["identifier"]}
    return {"authorities": {role: body}}


def expect(name: str, report: Report, code: int, needle: str) -> bool:
    text = "\n".join(report.lines)
    ok = report.code == code and needle in text
    print(f"self-test {name}: {'PASS' if ok else 'FAIL'}")
    if not ok:
        print(text, file=sys.stderr)
        print(f"expected code {code}", file=sys.stderr)
    return ok


def self_test(root: Path) -> int:
    graph_path = root / GRAPH_RELATIVE
    real = run_check(root, graph_path, None, set(), True)
    graph = load_json(graph_path)
    reconstruction_ok = real.code == 0
    text = "\n".join(real.lines)
    for role, expected_role in REQUIRED_ROLES.items():
        marker = (
            f"role={role} source_type={expected_role['source_type']} "
            f"normative={'true' if expected_role['normative'] else 'false'}"
        )
        if marker not in text:
            reconstruction_ok = False
    if "identity=NOT_VERIFIED" not in text or "role=engineering-requirements" not in text:
        reconstruction_ok = False
    identifiers = external_identifiers(graph)
    for relative in CONSUMER_PATHS:
        consumer = (root / relative).read_text(encoding="utf-8")
        if any(identifier in consumer for identifier in identifiers):
            reconstruction_ok = False
    if DISCOVERY_LINE not in (root / "PROJECT_STATE.md").read_text(encoding="utf-8"):
        reconstruction_ok = False
    print(f"self-test reconstruction: {'PASS' if reconstruction_ok else 'FAIL'}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        missing_graph = copy.deepcopy(graph)
        missing_graph["authorities"] = [
            entry for entry in missing_graph["authorities"] if entry["role"] != "architecture"
        ]
        missing_path = tmp_path / "missing.json"
        write_graph(missing_path, missing_graph)
        missing = run_check(root, missing_path, None, set(), False)

        wrong_observation = matching_observation(graph, "architecture")
        wrong_observation["authorities"]["architecture"]["identifier"] = "not-the-authority"
        wrong = run_check(root, graph_path, wrong_observation, set(), False)

        unavailable = run_check(
            root,
            graph_path,
            {"authorities": {"architecture": {"available": False}}},
            set(),
            False,
        )
        required = run_check(
            root,
            graph_path,
            {"authorities": {"architecture": {"available": False}}},
            {"architecture"},
            False,
        )

        stale_observation = matching_observation(graph, "architecture")
        stale_observation["authorities"]["architecture"]["modified"] = "2000-01-01T00:00:00.000Z"
        stale = run_check(root, graph_path, stale_observation, set(), False)

        fresh = matching_observation(graph, "workflow-lifecycle")
        fresh["authorities"].update(matching_observation(graph, "architecture")["authorities"])
        confirmed = run_check(root, graph_path, fresh, set(), False)

    results = [
        reconstruction_ok,
        expect("missing-binding", missing, 10, "authority-graph: FAIL"),
        expect("wrong-identity", wrong, 11, "identity=FAIL"),
        expect("unavailable", unavailable, 0, "role=architecture source_type=google-drive-file normative=true identity=NOT_VERIFIED revision=NOT_VERIFIED"),
        expect("require-verified", required, 14, "authority-graph: NOT_VERIFIED"),
        expect("stale-revision", stale, 12, "revision=RECONCILE"),
        expect("matching-observation", confirmed, 0, "role=architecture source_type=google-drive-file normative=true identity=VERIFIED revision=VERIFIED"),
    ]
    if all(results):
        print("authority self-test: ok")
        return 0
    print("authority self-test: FAIL", file=sys.stderr)
    return 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    parser.add_argument("--graph")
    parser.add_argument("--observation")
    parser.add_argument("--root")
    parser.add_argument("--require-verified", default="")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    root = Path(args.root) if args.root else Path(git(Path("."), "rev-parse", "--show-toplevel").stdout.strip())
    if not root.is_dir():
        print("authority-graph: FAIL missing binding", file=sys.stderr)
        return 10
    if args.self_test:
        return self_test(root)
    graph_path = Path(args.graph) if args.graph else root / GRAPH_RELATIVE
    observation_path = args.observation or os.environ.get("WI_AUTHORITY_OBSERVATION")
    observation = None
    if observation_path:
        try:
            observation = load_json(Path(observation_path))
        except (OSError, json.JSONDecodeError):
            print("authority-graph: NOT_VERIFIED", file=sys.stderr)
            return 14
    require_verified = {item for item in args.require_verified.split(",") if item}
    report = run_check(
        root,
        graph_path,
        observation,
        require_verified,
        enforce_discovery=args.graph is None,
    )
    print("\n".join(report.lines))
    return report.code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
