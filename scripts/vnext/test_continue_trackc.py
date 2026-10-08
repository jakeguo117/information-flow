#!/usr/bin/env python3
"""Synthetic tests for the Track C continue_project wrapper and status board.

No live vault, Drive, Notion, or client content. Page ids are fake tokens.
"""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
VNEXT = SCRIPTS / "vnext"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(VNEXT))

import continue_caller as caller  # noqa: E402
import continue_project as cp  # noqa: E402
import package_journal_pack  # noqa: E402
import status_board as board  # noqa: E402

AIC_ID = "AI-AGENTS-COOPERATE"
P2_ID = "AIC-PRJ-0002-HK-INS-FOLLOWUP"
WHEN = datetime(2026, 10, 8, 15, 15, tzinfo=ZoneInfo("Asia/Shanghai"))
BANNED_LITERALS = ("insurance", "CRM", "保险", "AIC-")
SOURCE_FILES = (
    SCRIPTS / "continue_project.py",
    VNEXT / "status_board.py",
    VNEXT / "continue_caller.py",
)


def _load(name: str) -> dict:
    return json.loads((VNEXT / name).read_text(encoding="utf-8"))


def _run(adapter: dict, payload: dict, store: board.LocalDirectoryBoardStore) -> dict:
    moment = datetime.fromisoformat(payload["occurred_at"])
    return caller.continue_for_project(
        project_id=payload["project_id"],
        adapter=adapter,
        readbacks=payload["readbacks"],
        request_ref=payload["request_ref"],
        board_store=store,
        now=moment,
    )


def _ok_core(**overrides):
    base = {
        "governance": {"availability": "present"},
        "project_control": {"availability": "present"},
        "milestone_map": {"availability": "present"},
        "frozen_authority_or_manifest": {"availability": "present", "approved": True},
        "repo_verification": {
            "status": "verified",
            "sha": "b069358b879c1d70af565fe0dd65939d73de43f7",
        },
        "vault_access": {
            "availability": "available",
            "minimum_context": {"relevant_ids": ["cog-fake-0001"]},
        },
    }
    base.update(overrides)
    return base


class CoreCompatibilityTests(unittest.TestCase):
    def test_repo_skip_is_not_blocked_and_invents_no_sha(self) -> None:
        result = cp.continue_project(
            **_ok_core(repo_verification={"required": False})
        )
        self.assertEqual(result["status"], "found")
        self.assertNotIn("verified_sha", result)
        states = {step["step"]: step["state"] for step in result["steps_checked"]}
        self.assertEqual(states["repo_verification"], "skipped")
        self.assertNotIn("SHA", result["bounded_next_action"])
        self.assertNotIn("None", result["bounded_next_action"])

    def test_project_id_is_echoed_only_when_supplied(self) -> None:
        echoed = cp.continue_project(**_ok_core(), project_id=AIC_ID)
        self.assertEqual(echoed["project_id"], AIC_ID)
        omitted = cp.continue_project(**_ok_core())
        self.assertNotIn("project_id", omitted)

    def test_blocked_still_outranks_a_skipped_repo(self) -> None:
        result = cp.continue_project(
            **_ok_core(
                repo_verification={"required": False},
                frozen_authority_or_manifest={"availability": "absent", "approved": False},
                governance={"availability": "absent"},
            )
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("Manifest", result["bounded_next_action"])

    def test_library_main_stays_a_library(self) -> None:
        with self.assertRaises(SystemExit) as raised:
            cp.main()
        self.assertIn("library entrypoint", str(raised.exception))


class EndToEndTests(unittest.TestCase):
    def setUp(self) -> None:
        self.aic_adapter = caller.load_adapter(VNEXT / "adapters" / "ai-agents-cooperate.json")
        self.p2_adapter = caller.load_adapter(
            VNEXT / "adapters" / "aic-prj-0002-hk-ins-followup.json"
        )
        self.aic_payload = _load("fixtures/syn_aic_ready.json")
        self.p2_payload = _load("fixtures/syn_prj0002_ready.json")

    def test_both_projects_and_cross_project_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aic_store = board.LocalDirectoryBoardStore(root / "aic")
            p2_store = board.LocalDirectoryBoardStore(root / "p2")
            aic = _run(self.aic_adapter, self.aic_payload, aic_store)
            p2 = _run(self.p2_adapter, self.p2_payload, p2_store)

            self.assertEqual(aic["status"], "found")
            self.assertEqual(aic["project_id"], AIC_ID)
            self.assertEqual(aic["verified_sha"], "b069358b879c1d70af565fe0dd65939d73de43f7")
            self.assertIn(aic["verified_sha"], aic["bounded_next_action"])
            self.assertEqual(p2["status"], "found")
            self.assertEqual(p2["project_id"], P2_ID)
            self.assertNotIn("verified_sha", p2)
            states = {step["step"]: step["state"] for step in p2["steps_checked"]}
            self.assertEqual(states["repo_verification"], "skipped")
            self.assertEqual(p2["bounded_next_action"], "Continue project: 1 due item(s).")
            self.assertNotIn("DigitalBrain", p2["bounded_next_action"])
            self.assertNotIn("SHA", p2["bounded_next_action"])
            self.assertNotIn("crm-fake-0001", p2["bounded_next_action"])
            self.assertEqual(p2["counts"]["due_count"], 1)
            self.assertEqual(p2["counts"]["no_date_count"], 1)
            self.assertIs(cp.continue_project, caller.cp.continue_project)

            aic_text = "\n".join(aic_store.read_text(name) for name in aic_store.list_names())
            p2_text = "\n".join(p2_store.read_text(name) for name in p2_store.list_names())
            self.assertIn(AIC_ID, aic_text)
            self.assertNotIn(P2_ID, aic_text)
            self.assertIn(P2_ID, p2_text)
            self.assertNotIn(AIC_ID, p2_text)
            self.assertNotIn("prose", aic_text.lower())

            before = p2_store.list_names()
            mixed = caller.continue_for_project(
                project_id=P2_ID,
                adapter=self.aic_adapter,
                readbacks=self.p2_payload["readbacks"],
                request_ref="session-fake-0002",
                board_store=p2_store,
                now=WHEN,
            )
            self.assertEqual(mixed["status"], "blocked")
            self.assertEqual(p2_store.list_names(), before)
            self.assertNotIn(AIC_ID, json.dumps(mixed))

            foreign = copy.deepcopy(self.p2_payload)
            foreign["readbacks"]["governance"]["project_id"] = AIC_ID
            foreign_result = _run(self.p2_adapter, foreign, p2_store)
            self.assertEqual(foreign_result["status"], "blocked")
            self.assertEqual(p2_store.list_names(), before)
            self.assertNotIn(AIC_ID, "\n".join(p2_store.read_text(name) for name in p2_store.list_names()))

    def test_manifest_mismatch_blocks_without_trusting_approved_flag(self) -> None:
        payload = copy.deepcopy(self.aic_payload)
        manifest = payload["readbacks"]["frozen_authority_or_manifest"]
        manifest["approved"] = True
        manifest["expected_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as tmp:
            result = _run(self.aic_adapter, payload, board.LocalDirectoryBoardStore(tmp))
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any(pin["step"] == "frozen_authority_or_manifest" and pin["match"] is False for pin in result["consumed_pins"]))
        self.assertIn("manifest", result["bounded_next_action"].lower())

    def test_self_reported_present_is_not_evidence(self) -> None:
        payload = copy.deepcopy(self.aic_payload)
        payload["readbacks"]["governance"] = {
            "readable": True,
            "availability": "present",
            "status": "present",
            "approved": True,
            "project_id": AIC_ID,
        }
        with tempfile.TemporaryDirectory() as tmp:
            result = _run(self.aic_adapter, payload, board.LocalDirectoryBoardStore(tmp))
        self.assertEqual(result["status"], "unavailable")
        self.assertFalse(any(pin["step"] == "governance" for pin in result["consumed_pins"]))
        joined = json.dumps(result["board_readback"])
        self.assertIn("8b18cf8d7571775e7ac5f2207e28daadbec9babd0588518f064d29ee6e2f8f69", json.dumps(self.aic_payload))
        self.assertNotIn("availability", joined)

    def test_idempotent_effect_key_writes_nothing_the_second_time(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = board.LocalDirectoryBoardStore(tmp)
            first = _run(self.p2_adapter, self.p2_payload, store)
            names = store.list_names()
            blobs = {name: store.read_text(name) for name in names}
            self.assertGreaterEqual(len(names), 1)
            self.assertTrue(all(item["wrote"] for item in first["board_writes"]))
            second = _run(self.p2_adapter, self.p2_payload, store)
            self.assertEqual(store.list_names(), names)
            for name in names:
                self.assertEqual(store.read_text(name), blobs[name])
            self.assertTrue(all(item["result"] == "no_op_duplicate" for item in second["board_writes"]))
            self.assertTrue(all(item["wrote"] is False for item in second["board_writes"]))

    def test_readback_matches_consumed_pin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = board.LocalDirectoryBoardStore(tmp)
            result = _run(self.aic_adapter, self.aic_payload, store)
        pin = next(item for item in result["consumed_pins"] if item["step"] == "governance")
        self.assertEqual(pin["sha256"], self.aic_payload["readbacks"]["governance"]["sha256"])
        self.assertEqual(pin["revision"], "rev-fake-gov-aic")
        self.assertTrue(pin["match"])
        reread = result["board_readback"][0]
        self.assertEqual(reread["effect_key"], result["board_writes"][0]["effect_key"])
        self.assertEqual(reread["consumed_pins"][0]["sha256"], pin["sha256"])
        self.assertEqual(reread["code_ref"], result["verified_sha"])

    def test_cli_json_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [
                    sys.executable,
                    str(VNEXT / "continue_caller.py"),
                    "--adapter",
                    str(VNEXT / "adapters" / "aic-prj-0002-hk-ins-followup.json"),
                    "--board-dir",
                    tmp,
                ],
                input=json.dumps(self.p2_payload),
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        body = json.loads(proc.stdout)
        self.assertEqual(body["status"], "found")
        self.assertEqual(body["project_id"], P2_ID)
        self.assertNotIn("verified_sha", body)
        self.assertEqual(body["bounded_next_action"], "Continue project: 1 due item(s).")


class BoardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = caller.load_adapter(
            VNEXT / "adapters" / "aic-prj-0002-hk-ins-followup.json"
        )

    def _event(self, *, kind: str = "FOLLOWUP-DUE", effect_key: str | None = None, supersedes: str | None = None) -> dict:
        key = effect_key or board.effect_key_followup(
            project_id=P2_ID,
            event_kind=kind,
            page_ids=["crm-fake-0001"],
            business_date="2026-10-08",
            status_codes=[self.adapter["status_codes"]["due"]],
        )
        event = {
            "event_id": f"AIC-EVT-PRJ0002-20261008T151500-{kind}-{key[:8]}",
            "project_id": P2_ID,
            "event_kind": kind,
            "occurred_at": "2026-10-08T15:15:00+08:00",
            "writer": "Grok Bot",
            "invocation": "on_request",
            "request_ref": "session-fake-0002",
            "effect_key": key,
            "supersedes": supersedes,
            "result": "ok",
            "crm_source": "collection://crm-fake-source",
            "crm_read_at": "2026-10-08T15:15:00+08:00",
            "crm_page_ids": ["crm-fake-0001"],
            "followup_status": {"crm-fake-0001": self.adapter["status_codes"]["due"]},
            "dates": {"crm-fake-0001": {"next_followup": "2026-10-08", "last_contact": None}},
        }
        return event

    def test_whitelist_rejects_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = board.LocalDirectoryBoardStore(tmp)
            event = self._event()
            event["姓名"] = "redacted-token"
            with self.assertRaises(board.BoardReject) as raised:
                board.write_event(store, event, self.adapter, stamp="20261008T151500")
            self.assertEqual(raised.exception.reason_code, "field_rule")
            self.assertEqual(store.list_names(), [])

            nested = self._event()
            nested["dates"]["crm-fake-0001"]["备注"] = "redacted-token"
            with self.assertRaises(board.BoardReject):
                board.write_event(store, nested, self.adapter, stamp="20261008T151500")
            self.assertEqual(store.list_names(), [])

    def test_contact_shaped_value_is_rejected(self) -> None:
        event = self._event()
        event["crm_source"] = "prefix-" + ("+" + ("1" * 11))
        with self.assertRaises(board.BoardReject):
            board.validate_event(event, self.adapter)

    def test_duplicate_effect_key_and_append_only_correction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = board.LocalDirectoryBoardStore(tmp)
            original = self._event()
            first = board.write_event(store, original, self.adapter, stamp="20261008T151500")
            self.assertTrue(first["wrote"])
            saved = store.read_text(first["name"])
            second = board.write_event(store, original, self.adapter, stamp="20261008T151501")
            self.assertEqual(second["result"], "no_op_duplicate")
            self.assertFalse(second["wrote"])
            self.assertEqual(store.read_text(first["name"]), saved)
            with self.assertRaises(FileExistsError):
                store.write_new(first["name"], saved + "\nchanged\n")
            self.assertEqual(store.read_text(first["name"]), saved)

            correction_key = board.effect_key_followup(
                project_id=P2_ID,
                event_kind="CORRECTION",
                page_ids=["crm-fake-0001"],
                business_date="2026-10-08",
                status_codes=[self.adapter["status_codes"]["due"]],
            )
            correction = self._event(kind="CORRECTION", effect_key=correction_key, supersedes=original["event_id"])
            correction["event_id"] = f"AIC-EVT-PRJ0002-20261008T161500-CORRECTION-{correction_key[:8]}"
            correction["occurred_at"] = "2026-10-08T16:15:00+08:00"
            written = board.write_event(store, correction, self.adapter, stamp="20261008T161500")
            self.assertTrue(written["wrote"])
            self.assertEqual(store.read_text(first["name"]), saved)
            self.assertEqual(len(store.list_names()), 2)
            snapshot = board.replay(board.load_events(store), self.adapter)
            self.assertEqual([item["event_id"] for item in snapshot["current"]], [correction["event_id"]])
            self.assertIn(original["event_id"], snapshot["superseded"])

    def test_replay_drops_other_writers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = board.LocalDirectoryBoardStore(tmp)
            kept = board.write_event(store, self._event(), self.adapter, stamp="20261008T151500")
            planted = {
                "event_id": "AIC-EVT-PRJ0002-20261008T151501-FOLLOWUP-DUE-aaaaaaaa",
                "project_id": P2_ID,
                "event_kind": "FOLLOWUP-DUE",
                "occurred_at": "2026-10-08T15:15:01+08:00",
                "writer": "Other Agent",
                "invocation": "on_request",
                "request_ref": "session-fake-0009",
                "effect_key": "ab" * 32,
                "supersedes": kept["event"]["event_id"],
                "result": "ok",
            }
            store.write_new("AIC-EVT-PRJ0002-20261008T151501-FOLLOWUP-DUE-aaaaaaaa.md", json.dumps(planted))
            snapshot = board.replay(board.load_events(store), self.adapter)
            self.assertEqual(snapshot["current"][0]["event_id"], kept["event"]["event_id"])
            self.assertEqual(snapshot["violations"][0]["reason_code"], "ownership_violation")

    def test_header_revision_is_a_new_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = board.LocalDirectoryBoardStore(tmp)
            first_key = hashlib.sha256(b"header-fake-1").hexdigest()
            second_key = hashlib.sha256(b"header-fake-2").hexdigest()
            header = {
                "board_schema_version": "aic-board/0.1",
                "project_id": P2_ID,
                "writer": "Grok Bot",
                "invocation": "on_request",
                "written_at": "2026-10-08T15:15:00+08:00",
                "effect_key": first_key,
                "code_ref": None,
                "authority_pins": [
                    {
                        "doc_id": "doc-fake-0001",
                        "version": "0.0.0",
                        "drive_file_id": "file-fake-doc",
                        "revision": "rev-fake-doc",
                        "sha256": hashlib.sha256(b"doc-fake-0001").hexdigest(),
                    }
                ],
            }
            board.write_header(store, header, self.adapter, stamp="20261008T151500")
            revised = dict(header)
            revised["effect_key"] = second_key
            revised["written_at"] = "2026-10-08T16:15:00+08:00"
            board.write_header(store, revised, self.adapter, stamp="20261008T161500")
            names = store.list_names()
            self.assertEqual(len(names), 2)
            self.assertTrue(all(name.startswith("BOARD-HEADER-") for name in names))

    def test_drive_stub_is_unwired(self) -> None:
        stub = board.DriveBoardStore("folder-fake-0001")
        with self.assertRaises(board.BoardBackendError):
            stub.list_names()
        with self.assertRaises(board.BoardBackendError):
            stub.write_new("EVT-x.json", "{}")


class GuardTests(unittest.TestCase):
    def test_journal_pack_still_excludes_continue_project(self) -> None:
        self.assertIn("continue_project", package_journal_pack.FORBIDDEN_PARTS)

    def test_core_and_board_have_no_project_literals(self) -> None:
        for path in SOURCE_FILES:
            text = path.read_text(encoding="utf-8")
            for token in BANNED_LITERALS:
                self.assertNotIn(token, text, msg=f"{token} in {path.name}")

    def test_no_network_client_in_source(self) -> None:
        banned = ("urllib", "requests", "http.client", "socket", "googleapiclient")
        for path in SOURCE_FILES:
            text = path.read_text(encoding="utf-8")
            for token in banned:
                self.assertNotIn(token, text, msg=f"{token} in {path.name}")

    def test_no_project_branch_in_core_or_board(self) -> None:
        for path in SOURCE_FILES:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("if project ==", text)
            self.assertNotIn("if project_id ==", text)


class ApprovalGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = caller.load_adapter(
            VNEXT / "adapters" / "aic-prj-0002-hk-ins-followup.json"
        )
        self.payload = _load("fixtures/syn_prj0002_ready.json")

    def _approval(self, payload: dict) -> dict:
        return payload["readbacks"]["frozen_authority_or_manifest"]["approval"]

    def _kinds(self, result: dict) -> list[str]:
        return [event["event_kind"] for event in result["board_readback"]]

    def test_approved_status_is_found_and_writes_events(self) -> None:
        self.assertEqual(self._approval(self.payload)["status"], "APPROVED")
        with tempfile.TemporaryDirectory() as tmp:
            store = board.LocalDirectoryBoardStore(tmp)
            result = _run(self.adapter, self.payload, store)
        self.assertEqual(result["status"], "found")
        self.assertTrue(result["board_writes"])
        self.assertTrue(all(item["wrote"] for item in result["board_writes"]))
        self.assertIn("SCOPE-SNAPSHOT", self._kinds(result))
        approval = next(pin for pin in result["consumed_pins"] if pin["step"] == "approval")
        self.assertTrue(approval["match"])

    def test_non_approved_status_blocks_without_scope_snapshot(self) -> None:
        cases: list[dict] = [
            {"status": "PENDING_PM_READBACK"},
            {"status": "PENDING"},
            {"status": "DRAFT"},
            {"status": "REJECTED"},
            {"status": ""},
            {"status": "approved"},
            {"drop": True},
        ]
        for case in cases:
            payload = copy.deepcopy(self.payload)
            approval = self._approval(payload)
            if case.get("drop"):
                approval.pop("status", None)
            else:
                approval["status"] = case["status"]
            with tempfile.TemporaryDirectory() as tmp:
                store = board.LocalDirectoryBoardStore(tmp)
                result = _run(self.adapter, payload, store)
                names = store.list_names()
            with self.subTest(case=case):
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(
                    [event["reason_code"] for event in result["board_readback"]],
                    ["not_approved"],
                )
                self.assertEqual(self._kinds(result), ["BLOCKED"])
                self.assertTrue(names)
                self.assertTrue(all("SCOPE-SNAPSHOT" not in name for name in names))
                approval_pin = next(
                    pin for pin in result["consumed_pins"] if pin["step"] == "approval"
                )
                self.assertFalse(approval_pin["match"])

    def test_placeholder_revision_blocks_each_slot(self) -> None:
        slots = (
            ("governance", ("governance", "revision")),
            ("project_control", ("project_control", "revision")),
            ("milestone_map", ("milestone_map", "revision")),
            ("manifest", ("frozen_authority_or_manifest", "revision")),
            ("expected_revision", ("frozen_authority_or_manifest", "expected_revision")),
            ("approval", ("frozen_authority_or_manifest", "approval", "revision")),
            ("context", ("context", "revision")),
        )
        for label, path in slots:
            payload = copy.deepcopy(self.payload)
            cursor = payload["readbacks"]
            for key in path[:-1]:
                cursor = cursor[key]
            cursor[path[-1]] = "REVISION_ID_UNAVAILABLE"
            with tempfile.TemporaryDirectory() as tmp:
                store = board.LocalDirectoryBoardStore(tmp)
                result = _run(self.adapter, payload, store)
                blob = "\n".join(store.read_text(name) for name in store.list_names())
            with self.subTest(slot=label):
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "revision_placeholder")
                self.assertEqual(
                    [event["reason_code"] for event in result["board_readback"]],
                    ["revision_placeholder"],
                )
                self.assertEqual(self._kinds(result), ["BLOCKED"])
                self.assertNotIn("SCOPE-SNAPSHOT", blob)
                self.assertNotIn("REVISION_ID_UNAVAILABLE", blob)

    def test_placeholder_token_shapes_block(self) -> None:
        tokens = (
            "",
            "   ",
            "unavailable",
            "UNKNOWN",
            "tbd",
            "Todo",
            "PlAcEhOlDeR",
            "N/A",
            "none",
            "NULL",
            "<revision>",
            "<>",
            "  <id>  ",
        )
        for token in tokens:
            payload = copy.deepcopy(self.payload)
            payload["readbacks"]["governance"]["revision"] = token
            with tempfile.TemporaryDirectory() as tmp:
                result = _run(self.adapter, payload, board.LocalDirectoryBoardStore(tmp))
            with self.subTest(token=token):
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason_code"], "revision_placeholder")
                self.assertNotIn("SCOPE-SNAPSHOT", self._kinds(result))

    def test_modified_time_and_opaque_revisions_are_accepted(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["readbacks"]["governance"]["revision"] = "2026-10-08T07:41:14Z"
        manifest = payload["readbacks"]["frozen_authority_or_manifest"]
        manifest["revision"] = "2026-10-08T07:41:14.123Z"
        manifest["expected_revision"] = "2026-10-08T07:41:14.123Z"
        manifest["approval"]["revision"] = "rev-opaque_1.2:abc"
        payload["readbacks"]["project_control"]["revision"] = "rev-unavailable-1"
        with tempfile.TemporaryDirectory() as tmp:
            result = _run(self.adapter, payload, board.LocalDirectoryBoardStore(tmp))
        self.assertEqual(result["status"], "found")
        self.assertIn("SCOPE-SNAPSHOT", self._kinds(result))
        pins = {pin["step"]: pin for pin in result["consumed_pins"]}
        self.assertEqual(pins["governance"]["revision"], "2026-10-08T07:41:14Z")
        self.assertTrue(pins["governance"]["match"])
        self.assertEqual(pins["frozen_authority_or_manifest"]["revision"], "2026-10-08T07:41:14.123Z")
        self.assertTrue(pins["frozen_authority_or_manifest"]["match"])
        self.assertEqual(pins["approval"]["revision"], "rev-opaque_1.2:abc")
        self.assertEqual(pins["project_control"]["revision"], "rev-unavailable-1")

    def test_replay_of_approved_run_is_no_op_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = board.LocalDirectoryBoardStore(tmp)
            first = _run(self.adapter, self.payload, store)
            names = store.list_names()
            blobs = {name: store.read_text(name) for name in names}
            second = _run(self.adapter, self.payload, store)
            self.assertEqual(first["status"], "found")
            self.assertIn("SCOPE-SNAPSHOT", self._kinds(first))
            self.assertTrue(all(item["wrote"] for item in first["board_writes"]))
            self.assertEqual(
                [item["effect_key"] for item in first["board_writes"]],
                [item["effect_key"] for item in second["board_writes"]],
            )
            self.assertTrue(all(item["result"] == "no_op_duplicate" for item in second["board_writes"]))
            self.assertTrue(all(item["wrote"] is False for item in second["board_writes"]))
            self.assertEqual(store.list_names(), names)
            for name in names:
                self.assertEqual(store.read_text(name), blobs[name])

    def test_cli_omitted_approval_status_is_not_approved(self) -> None:
        payload = copy.deepcopy(self.payload)
        self._approval(payload).pop("status")
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [
                    sys.executable,
                    str(VNEXT / "continue_caller.py"),
                    "--adapter",
                    str(VNEXT / "adapters" / "aic-prj-0002-hk-ins-followup.json"),
                    "--board-dir",
                    tmp,
                ],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        body = json.loads(proc.stdout)
        self.assertEqual(body["status"], "blocked")
        self.assertEqual(
            [event["reason_code"] for event in body["board_readback"]],
            ["not_approved"],
        )
        self.assertEqual([event["event_kind"] for event in body["board_readback"]], ["BLOCKED"])


if __name__ == "__main__":
    unittest.main()
