#!/usr/bin/env python3
"""ideas-0.1 write rules. Synthetic vaults only."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

TOOL = Path(__file__).resolve().parent / "write_idea.py"
EXAMPLE_REF = "journal:synthetic#p1"
EXAMPLE_EXPRESSION = "合成想法，离开原周记也能懂。"
EXAMPLE_ID = "idea-e7029224ac83"
TOPIC_DIRS = ("Content", "Insurance", "Life", "Tech", "Trading")
SNAPSHOT_KEYS = (
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
    "origin",
    "visibility",
    "status",
)


def stamp(hour: int, minute: int = 0) -> str:
    return f"2026-10-21T{hour:02d}:{minute:02d}:00+08:00"


def formula_id(source_ref: str, expression: str) -> str:
    digest = hashlib.sha1(f"{source_ref}|{expression}".encode("utf-8")).hexdigest()[:12]
    return f"idea-{digest}"


def snapshot_entry(state: dict, at: str, by: str, op: str) -> dict:
    entry = {"at": at, "by": by, "op": op}
    for key in SNAPSHOT_KEYS:
        if key == "updated_at":
            continue
        if key in state:
            entry[key] = copy.deepcopy(state[key])
    entry["updated_at"] = at
    return entry


def pack(state: dict, op: str, history: list[dict], directory: str | None = None) -> dict:
    payload = copy.deepcopy(state)
    payload["op"] = op
    payload["history"] = copy.deepcopy(history)
    payload["updated_at"] = history[-1]["at"]
    if directory is not None:
        payload["directory"] = directory
    return payload


def make_create(
    expression: str,
    source_refs: list[str] | None = None,
    topics: list[str] | None = None,
    *,
    at: str | None = None,
    by: str = "ai_extension",
    op: str = "create",
    origin: str = "ai_extension",
    confirmation: str = "candidate",
    validation: str = "untested",
    nature: str = "judgment",
    relations: list[dict] | None = None,
    idea_id: str | None = None,
    directory: str | None = None,
    limitations: str | None = None,
    applicability: str | None = None,
    context: str | None = None,
    feedback: list[dict] | None = None,
    visibility: str = "private-jake",
    status: str = "active",
) -> tuple[dict, dict, list[dict]]:
    at = at or stamp(9)
    state: dict = {
        "schema_version": "ideas-0.1",
        "type": "idea",
        "revision": 1,
        "created_at": at,
        "updated_at": at,
        "expression": expression,
        "source_refs": [] if source_refs is None else source_refs,
        "topics": [] if topics is None else topics,
        "nature": nature,
        "confirmation_state": confirmation,
        "validation_state": validation,
        "relations": [] if relations is None else relations,
        "usage_feedback": [] if feedback is None else feedback,
        "origin": origin,
        "visibility": visibility,
        "status": status,
    }
    if idea_id is not None:
        state["idea_id"] = idea_id
    if limitations is not None:
        state["limitations"] = limitations
    if applicability is not None:
        state["applicability"] = applicability
    if context is not None:
        state["context"] = context
    history = [snapshot_entry(state, at, by, op)]
    return pack(state, op, history, directory), state, history


def build_update(
    prev_state: dict,
    prev_history: list[dict],
    op: str,
    at: str,
    by: str,
    **changes: object,
) -> tuple[dict, dict, list[dict]]:
    state = copy.deepcopy(prev_state)
    state.update(changes)
    state["updated_at"] = at
    history = copy.deepcopy(prev_history) + [snapshot_entry(state, at, by, op)]
    return pack(state, op, history), state, history


def remember(state: dict, history: list[dict], idea_id: str) -> None:
    state["idea_id"] = idea_id
    for entry in history:
        entry["idea_id"] = idea_id


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---", 2)[1])


class IdeaWriteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name)
        self.root = self.vault / "💡 Ideas"
        self.protected: dict[Path, bytes] = {}
        for name in TOPIC_DIRS:
            (self.root / name).mkdir(parents=True)
        samples = {
            self.root / "MOC.md": "moc\n",
            self.root / "README.md": "readme\n",
            self.root / "Life" / "MOC.md": "topic moc\n",
            self.root / "Life" / "2020-01-01-life.md": "old life\n",
            self.root / "Tech" / "2024-05-06-tech.md": "old tech\n",
            self.root / "2020-01-02-root.md": "old root\n",
        }
        for path, text in samples.items():
            path.write_text(text, encoding="utf-8")
            self.protected[path] = path.read_bytes()
        self.seq = 0

    def tearDown(self) -> None:
        try:
            for path, data in self.protected.items():
                self.assertEqual(path.read_bytes(), data, str(path))
        finally:
            self.tmp.cleanup()

    def invoke(
        self,
        action: str,
        payload: dict,
        *,
        dry_run: bool = False,
        directory: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        self.seq += 1
        path = self.vault / f"payload-{self.seq}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        args = [sys.executable, str(TOOL), action, "--vault", str(self.vault), "--payload", str(path)]
        if dry_run:
            args.append("--dry-run")
        if directory is not None:
            args.extend(["--directory", directory])
        return subprocess.run(args, capture_output=True, text=True, check=False)

    def load(self, proc: subprocess.CompletedProcess[str]) -> dict:
        return json.loads(proc.stdout)

    def idea_files(self) -> list[Path]:
        return sorted(path for path in self.root.rglob("idea-*.md") if path.is_file())

    def test_formula_example_and_dry_run(self) -> None:
        payload, _state, _history = make_create(EXAMPLE_EXPRESSION, [EXAMPLE_REF], [])
        dry = self.invoke("write", payload, dry_run=True)
        self.assertEqual(dry.returncode, 0, dry.stderr)
        dry_body = self.load(dry)
        self.assertTrue(dry_body["ok"])
        self.assertTrue(dry_body["dry_run"])
        self.assertFalse(dry_body["already_persisted"])
        self.assertEqual(dry_body["idea_id"], EXAMPLE_ID)
        self.assertEqual(self.idea_files(), [])

        proc = self.invoke("write", payload)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        body = self.load(proc)
        self.assertEqual(body["idea_id"], EXAMPLE_ID)
        path = Path(body["path"])
        self.assertEqual(path.parent.name, "Life")
        self.assertEqual(path.name, f"{EXAMPLE_ID}.md")
        text = path.read_text(encoding="utf-8")
        self.assertIn(EXAMPLE_EXPRESSION, text)
        meta = frontmatter(path)
        self.assertEqual(meta["schema_version"], "ideas-0.1")
        self.assertEqual(meta["type"], "idea")
        self.assertEqual(meta["origin"], "ai_extension")
        self.assertEqual(meta["confirmation_state"], "candidate")
        self.assertEqual(meta["validation_state"], "untested")
        self.assertEqual(meta["history"][0]["expression"], EXAMPLE_EXPRESSION)
        self.assertEqual(meta["history"][0]["op"], "create")
        self.assertNotIn("usage_feedback", meta["history"][0])

        empty_expression = "没有来源引用的合成想法。"
        empty_payload, _, _ = make_create(empty_expression, [])
        empty = self.invoke("write", empty_payload)
        self.assertEqual(empty.returncode, 0, empty.stderr)
        self.assertEqual(self.load(empty)["idea_id"], formula_id("", empty_expression))

    def test_ac10_rejects_confirmed_without_jake_history(self) -> None:
        payload, state, history = make_create(
            "延伸候选，离开原周记也能懂。",
            [EXAMPLE_REF],
            ["生活"],
        )
        created = self.invoke("write", payload)
        self.assertEqual(created.returncode, 0, created.stderr)
        path = Path(self.load(created)["path"])
        before = path.read_bytes()
        stamp_ns = path.stat().st_mtime_ns
        remember(state, history, self.load(created)["idea_id"])

        rejected, _, _ = build_update(
            state,
            history,
            "supplement",
            stamp(10),
            "ai_extension",
            confirmation_state="confirmed",
            limitations="这条不该被确认。",
        )
        proc = self.invoke("write", rejected)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("missing jake confirmation", self.load(proc)["error"])
        self.assertFalse(self.load(proc)["ok"])
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(path.stat().st_mtime_ns, stamp_ns)

        fresh, _, _ = make_create(
            "未确认就标已确认，离开原周记也能懂。",
            ["journal:synthetic#ac10"],
            confirmation="confirmed",
            by="ai_extension",
            origin="ai_extension",
        )
        alone = self.invoke("write", fresh)
        self.assertNotEqual(alone.returncode, 0)
        self.assertIn("missing jake confirmation", self.load(alone)["error"])
        self.assertEqual(len(self.idea_files()), 1)

        jake_origin, _, _ = make_create(
            "origin 是 jake 但记录不是，离开原周记也能懂。",
            ["journal:synthetic#ac10b"],
            confirmation="confirmed",
            by="ai_extension",
            origin="jake",
        )
        still = self.invoke("write", jake_origin)
        self.assertNotEqual(still.returncode, 0)
        self.assertIn("missing jake confirmation", self.load(still)["error"])
        self.assertEqual(len(self.idea_files()), 1)

    def test_ac10_allows_confirmed_after_jake_history(self) -> None:
        payload, _, _ = make_create(
            "Jake 确认过的延伸，离开原周记也能懂。",
            [EXAMPLE_REF],
            ["tech"],
            confirmation="confirmed",
            by="jake",
            origin="ai_extension",
        )
        proc = self.invoke("write", payload)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        body = self.load(proc)
        path = Path(body["path"])
        self.assertEqual(path.parent.name, "Tech")
        meta = frontmatter(path)
        self.assertEqual(meta["origin"], "ai_extension")
        self.assertEqual(meta["confirmation_state"], "confirmed")
        self.assertEqual(meta["history"][0]["by"], "jake")
        self.assertEqual(meta["history"][0]["confirmation_state"], "confirmed")
        self.assertEqual(meta["history"][0]["expression"], meta["expression"])

    def test_rejected_and_deferred_require_jake_history(self) -> None:
        cases = (
            ("rejected", "missing jake rejection", "舍弃这句合成想法。"),
            ("deferred", "missing jake deferral", "暂存这句合成想法。"),
        )
        for state_name, message, expression in cases:
            with self.subTest(state=state_name, allowed=False):
                payload, _, _ = make_create(
                    expression,
                    [f"journal:synthetic#{state_name}"],
                    confirmation=state_name,
                    by="ai_extension",
                    origin="jake",
                )
                before = [path.read_bytes() for path in self.idea_files()]
                proc = self.invoke("write", payload)
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn(message, self.load(proc)["error"])
                self.assertEqual([path.read_bytes() for path in self.idea_files()], before)
            with self.subTest(state=state_name, allowed=True):
                payload, _, _ = make_create(
                    expression + "Jake 记下了。",
                    [f"journal:synthetic#{state_name}-ok"],
                    confirmation=state_name,
                    by="jake",
                    origin="ai_extension",
                )
                proc = self.invoke("write", payload)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                meta = frontmatter(Path(self.load(proc)["path"]))
                self.assertEqual(meta["confirmation_state"], state_name)
                self.assertEqual(meta["origin"], "ai_extension")
                self.assertEqual(meta["history"][0]["by"], "jake")

    def test_retry_idempotent(self) -> None:
        payload, state, history = make_create(
            "幂等合成想法，离开原周记也能懂。",
            [EXAMPLE_REF],
            ["生活"],
            relations=[{"type": "sourced_from", "target_id": EXAMPLE_REF}],
        )
        first = self.invoke("write", payload)
        self.assertEqual(first.returncode, 0, first.stderr)
        first_body = self.load(first)
        self.assertFalse(first_body["already_persisted"])
        path = Path(first_body["path"])
        before = path.read_bytes()
        stamp_ns = path.stat().st_mtime_ns
        idea_id = first_body["idea_id"]
        remember(state, history, idea_id)
        self.assertEqual(len(self.idea_files()), 1)

        retried = self.invoke("retry", payload)
        self.assertEqual(retried.returncode, 0, retried.stderr)
        retry_body = self.load(retried)
        self.assertTrue(retry_body["ok"])
        self.assertTrue(retry_body["already_persisted"])
        self.assertEqual(retry_body["idea_id"], idea_id)
        self.assertEqual(Path(retry_body["path"]).resolve(), path.resolve())
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(path.stat().st_mtime_ns, stamp_ns)

        again = self.invoke("write", pack(state, "create", history))
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertTrue(self.load(again)["already_persisted"])
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(path.stat().st_mtime_ns, stamp_ns)
        self.assertEqual(len(self.idea_files()), 1)

        conflict_payload = pack(state, "create", history)
        conflict_payload["expression"] = "另一句幂等合成想法，离开原周记也能懂。"
        conflict_payload["history"][0]["expression"] = conflict_payload["expression"]
        conflicted = self.invoke("write", conflict_payload)
        self.assertNotEqual(conflicted.returncode, 0)
        conflict_body = self.load(conflicted)
        self.assertFalse(conflict_body["ok"])
        self.assertIn("conflict", conflict_body["error"])
        self.assertIn(conflict_payload["expression"], conflict_body["diff"])
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(path.stat().st_mtime_ns, stamp_ns)
        self.assertEqual(self.idea_files(), [path])

        fresh, _, _ = make_create("重跑才落盘的合成想法。", ["journal:synthetic#retry"])
        missed = self.invoke("retry", fresh)
        self.assertEqual(missed.returncode, 0, missed.stderr)
        self.assertFalse(self.load(missed)["already_persisted"])
        self.assertTrue(Path(self.load(missed)["path"]).is_file())

    def test_ops_smoke(self) -> None:
        payload, state, history = make_create(
            '创建时他说 "keep"，离开原周记也能懂。',
            [EXAMPLE_REF],
            ["生活"],
            relations=[{"type": "sourced_from", "target_id": EXAMPLE_REF}],
            context="合成周记收束之后。",
        )
        created = self.invoke("write", payload)
        self.assertEqual(created.returncode, 0, created.stderr)
        created_body = self.load(created)
        created_path = Path(created_body["path"])
        remember(state, history, created_body["idea_id"])
        self.assertEqual(frontmatter(created_path)["validation_state"], "untested")

        supplemented, state, history = build_update(
            state,
            history,
            "supplement",
            stamp(10),
            "ai_extension",
            limitations="范围：合成数据。",
            usage_feedback=[{"at": stamp(10), "note": "合成反馈。", "source_ref": EXAMPLE_REF}],
            source_refs=[EXAMPLE_REF, "journal:synthetic#extra"],
        )
        supplement = self.invoke("write", supplemented)
        self.assertEqual(supplement.returncode, 0, supplement.stderr)
        supplement_meta = frontmatter(created_path)
        self.assertEqual(supplement_meta["revision"], 1)
        self.assertEqual(supplement_meta["idea_id"], created_body["idea_id"])
        self.assertEqual(supplement_meta["limitations"], "范围：合成数据。")
        self.assertEqual([item["op"] for item in supplement_meta["history"]], ["create", "supplement"])
        self.assertEqual(supplement_meta["history"][0]["expression"], payload["expression"])
        self.assertEqual(supplement_meta["validation_state"], "untested")

        relations = copy.deepcopy(state["relations"]) + [
            {"type": "supports", "target_id": "fact-synthetic0001"}
        ]
        supported, state, history = build_update(
            state,
            history,
            "support",
            stamp(11),
            "jake",
            relations=relations,
        )
        support = self.invoke("write", supported)
        self.assertEqual(support.returncode, 0, support.stderr)
        support_meta = frontmatter(created_path)
        self.assertEqual(support_meta["revision"], 1)
        self.assertEqual(support_meta["validation_state"], "untested")
        self.assertIn(
            {"type": "supports", "target_id": "fact-synthetic0001"},
            support_meta["relations"],
        )

        relations = copy.deepcopy(state["relations"]) + [
            {"type": "challenges", "target_id": "fact-synthetic0002", "note": "合成异议"}
        ]
        challenged, state, history = build_update(
            state,
            history,
            "challenge",
            stamp(12),
            "jake",
            relations=relations,
        )
        challenge = self.invoke("write", challenged)
        self.assertEqual(challenge.returncode, 0, challenge.stderr)
        challenge_meta = frontmatter(created_path)
        self.assertEqual(challenge_meta["revision"], 1)
        self.assertTrue(any(item["type"] == "challenges" for item in challenge_meta["relations"]))

        revised_expression = "修订后的合成想法，离开原周记也能懂。"
        revised, state, history = build_update(
            state,
            history,
            "revise",
            stamp(13),
            "jake",
            expression=revised_expression,
            revision=2,
            confirmation_state="confirmed",
        )
        before_revise_names = {path.name for path in self.idea_files()}
        revise = self.invoke("write", revised)
        self.assertEqual(revise.returncode, 0, revise.stderr)
        revise_body = self.load(revise)
        self.assertEqual(revise_body["idea_id"], created_body["idea_id"])
        self.assertEqual(Path(revise_body["path"]).resolve(), created_path.resolve())
        revise_meta = frontmatter(created_path)
        self.assertEqual(revise_meta["revision"], 2)
        self.assertEqual(revise_meta["expression"], revised_expression)
        self.assertEqual(revise_meta["history"][0]["expression"], payload["expression"])
        self.assertEqual(revise_meta["history"][-1]["op"], "revise")
        self.assertEqual(revise_meta["confirmation_state"], "confirmed")
        new_formula = formula_id(EXAMPLE_REF, revised_expression)
        self.assertNotEqual(new_formula, created_body["idea_id"])
        self.assertNotIn(f"{new_formula}.md", {path.name for path in self.idea_files()})
        self.assertEqual({path.name for path in self.idea_files()}, before_revise_names)

        revised_bytes = created_path.read_bytes()
        replay = self.invoke("retry", revised)
        self.assertEqual(replay.returncode, 0, replay.stderr)
        self.assertTrue(self.load(replay)["already_persisted"])
        self.assertEqual(created_path.read_bytes(), revised_bytes)

        old_bytes = created_path.read_bytes()
        superseded_expression = "替代后的合成想法，离开原周记也能懂。"
        supersede_payload, _, _ = make_create(
            superseded_expression,
            ["journal:synthetic#supersede"],
            ["交易"],
            op="supersede",
            relations=[{"type": "supersedes", "target_id": created_body["idea_id"]}],
            at=stamp(14),
        )
        supersede = self.invoke("write", supersede_payload)
        self.assertEqual(supersede.returncode, 0, supersede.stderr)
        supersede_body = self.load(supersede)
        supersede_path = Path(supersede_body["path"])
        self.assertEqual(supersede_path.parent.name, "Trading")
        self.assertNotEqual(supersede_body["idea_id"], created_body["idea_id"])
        self.assertEqual(
            supersede_body["idea_id"],
            formula_id("journal:synthetic#supersede", superseded_expression),
        )
        supersede_meta = frontmatter(supersede_path)
        self.assertEqual(supersede_meta["revision"], 1)
        self.assertEqual(supersede_meta["history"][0]["op"], "supersede")
        self.assertEqual(
            supersede_meta["relations"],
            [{"type": "supersedes", "target_id": created_body["idea_id"]}],
        )
        self.assertEqual(created_path.read_bytes(), old_bytes)
        old_meta = frontmatter(created_path)
        self.assertFalse(any(item["type"] == "supersedes" for item in old_meta["relations"]))

    def test_directory_rules_and_protected_files(self) -> None:
        routed = (
            (["技术"], None, "Tech"),
            (["技术", "交易"], None, "Life"),
            (["内容", "content"], None, "Content"),
            (["杂项"], None, "Life"),
            (["技术"], "Content", "Content"),
        )
        for index, (topics, directory, expected) in enumerate(routed):
            expression = f"目录样例{index}，离开原周记也能懂。"
            payload, _, _ = make_create(
                expression,
                [f"journal:synthetic#dir{index}"],
                topics,
                directory=directory,
            )
            proc = self.invoke("write", payload)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(Path(self.load(proc)["path"]).parent.name, expected)

        payload, _, _ = make_create("命令行目录覆盖，离开原周记也能懂。", ["journal:synthetic#cli"])
        proc = self.invoke("write", payload, directory="Insurance")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(Path(self.load(proc)["path"]).parent.name, "Insurance")

        illegal, _, _ = make_create("非法目录，离开原周记也能懂。", ["journal:synthetic#bad-dir"])
        illegal["directory"] = "Secret"
        before = sorted(path.name for path in self.idea_files())
        rejected = self.invoke("write", illegal)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("invalid directory", self.load(rejected)["error"])
        self.assertFalse((self.root / "Secret").exists())
        self.assertEqual(sorted(path.name for path in self.idea_files()), before)

        escaped = self.invoke(
            "write",
            make_create("路径逃逸，离开原周记也能懂。", ["journal:synthetic#escape"])[0],
            directory="Life/../../etc",
        )
        self.assertNotEqual(escaped.returncode, 0)
        self.assertIn("invalid directory", self.load(escaped)["error"])
        self.assertEqual(sorted(path.name for path in self.idea_files()), before)

        duplicate_expression = "重复公式标识，离开原周记也能懂。"
        first, _, _ = make_create(duplicate_expression, [EXAMPLE_REF], ["生活"])
        wrote = self.invoke("write", first)
        self.assertEqual(wrote.returncode, 0, wrote.stderr)
        original = Path(self.load(wrote)["path"])
        original_bytes = original.read_bytes()
        same = copy.deepcopy(first)
        same["directory"] = "Tech"
        replay = self.invoke("write", same)
        self.assertEqual(replay.returncode, 0, replay.stderr)
        self.assertTrue(self.load(replay)["already_persisted"])
        self.assertEqual(Path(self.load(replay)["path"]).resolve(), original.resolve())
        self.assertEqual(original.read_bytes(), original_bytes)
        self.assertEqual(original.parent.name, "Life")
        self.assertFalse((self.root / "Tech" / original.name).exists())

        changed = copy.deepcopy(first)
        changed["idea_id"] = self.load(wrote)["idea_id"]
        changed["history"][0]["idea_id"] = changed["idea_id"]
        changed["topics"] = ["技术"]
        changed["history"][0]["topics"] = ["技术"]
        conflicted = self.invoke("write", changed)
        self.assertNotEqual(conflicted.returncode, 0)
        self.assertIn("conflict", self.load(conflicted)["error"])
        self.assertEqual(original.read_bytes(), original_bytes)
        self.assertFalse((self.root / "Tech" / original.name).exists())

    def test_rejections_leave_zero_bytes(self) -> None:
        self.assertEqual(self.idea_files(), [])
        cases = []

        missing, _, _ = make_create("   ", [EXAMPLE_REF])
        cases.append(missing)

        bad_schema, _, _ = make_create("版本不对，离开原周记也能懂。", [EXAMPLE_REF])
        bad_schema["schema_version"] = "ideas-9.9"
        bad_schema["history"][0]["schema_version"] = "ideas-9.9"
        cases.append(bad_schema)

        bad_type, _, _ = make_create("类型不对，离开原周记也能懂。", [EXAMPLE_REF])
        bad_type["type"] = "viewpoint"
        bad_type["history"][0]["type"] = "viewpoint"
        cases.append(bad_type)

        mismatch, _, _ = make_create("前后不一致，离开原周记也能懂。", [EXAMPLE_REF])
        mismatch["expression"] = "正文改了，历史没改。"
        cases.append(mismatch)

        bad_status, _, _ = make_create("状态用了确认词，离开原周记也能懂。", [EXAMPLE_REF])
        bad_status["status"] = "confirmed"
        bad_status["history"][0]["status"] = "confirmed"
        cases.append(bad_status)

        duplicate, _, _ = make_create(
            "关系重复，离开原周记也能懂。",
            [EXAMPLE_REF],
            relations=[
                {"type": "supports", "target_id": "fact-synthetic0001"},
                {"type": "supports", "target_id": " fact-synthetic0001 "},
            ],
        )
        cases.append(duplicate)

        self_expression = "替代自己，离开原周记也能懂。"
        self_id = formula_id(EXAMPLE_REF, self_expression)
        supersede_self, _, _ = make_create(
            self_expression,
            [EXAMPLE_REF],
            op="supersede",
            idea_id=self_id,
            relations=[{"type": "supersedes", "target_id": self_id}],
        )
        cases.append(supersede_self)

        wrong_id, _, _ = make_create(
            EXAMPLE_EXPRESSION,
            [EXAMPLE_REF],
            idea_id="idea-000000000000",
        )
        cases.append(wrong_id)

        for payload in cases:
            with self.subTest(expression=payload.get("expression")):
                proc = self.invoke("write", payload)
                self.assertNotEqual(proc.returncode, 0)
                self.assertFalse(self.load(proc)["ok"])
                self.assertEqual(self.idea_files(), [])


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tests"))
    import vault_remote_fixture

    vault_remote_fixture.install()
    unittest.main()
