#!/usr/bin/env python3
"""Vault writes only proceed for an allowlisted git remote."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = ROOT / "skills" / "journal" / "tools"
COGNITION = ROOT / "skills" / "cognition" / "tools"
IDEAS = ROOT / "skills" / "ideas" / "tools"
sys.path.insert(0, str(JOURNAL))
sys.path.insert(0, str(COGNITION))

import cognition_lib  # noqa: E402
import journal_lib  # noqa: E402
import vault_guard  # noqa: E402

ALLOW = f"https://github.com/{vault_guard.DEFAULT_VAULT_REMOTE}.git"
PUBLIC = "https://github.com/jakeguo117/information-flow.git"
OTHER = "https://github.com/example/notes.git"
BRANCH = "cursor/codex-cloud-journal-guard-e437"


def git(vault: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(vault), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def init_remote(vault: Path, url: str | None) -> None:
    vault.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(["git", "init", "-b", "main", str(vault)], stdout=subprocess.DEVNULL)
    if url:
        subprocess.check_call(["git", "-C", str(vault), "remote", "add", "origin", url])


def journal_approval(**overrides: object) -> dict:
    data: dict = {
        "event_id": "vault-guard-event",
        "confirmed": True,
        "phrase": "可以写",
        "date": "2026-10-23",
        "journal_number": 3,
        "title": "通路测试",
        "body": "合成正文。\n",
        "topics": [],
        "previous": "",
    }
    data.update(overrides)
    if data.get("confirmed") is True and data.get("phrase") in journal_lib.CONFIRM_PHRASES:
        data["payload_sha256"] = journal_lib.fingerprint(journal_lib.render_journal(data))
    return data


def run_tool(cmd: list[str], env_extra: dict[str, str] | None = None, drop: tuple[str, ...] = ()) -> tuple[int, dict]:
    env = os.environ.copy()
    for key in ("INFOFLOW_VAULT_REMOTE", "INFOFLOW_RUNTIME", "INFOFLOW_CONFIG", *drop):
        env.pop(key, None)
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    body = proc.stdout.strip() or "{}"
    return proc.returncode, json.loads(body)


def save_journal(vault: Path, approval: dict, env_extra: dict[str, str] | None = None) -> tuple[int, dict]:
    with tempfile.TemporaryDirectory() as raw:
        path = Path(raw) / "approval.json"
        path.write_text(json.dumps(approval), encoding="utf-8")
        return run_tool(
            [
                sys.executable,
                str(JOURNAL / "write_journal.py"),
                "save",
                "--vault",
                str(vault),
                "--approval",
                str(path),
            ],
            env_extra,
        )


class SlugTests(unittest.TestCase):
    def test_github_urls_and_local_paths(self) -> None:
        self.assertEqual(
            vault_guard.slug_of("https://github.com/Jakeguo117/obsidian-digitalbrain.git"),
            "jakeguo117/obsidian-digitalbrain",
        )
        self.assertEqual(
            vault_guard.slug_of("git@github.com:jakeguo117/obsidian-digitalbrain.git"),
            "jakeguo117/obsidian-digitalbrain",
        )
        self.assertEqual(
            vault_guard.slug_of("https://x-access-token:secret@github.com/jakeguo117/information-flow"),
            "jakeguo117/information-flow",
        )
        self.assertIsNone(vault_guard.slug_of("/tmp/remote.git"))

    def test_default_allowlist_without_env(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"INFOFLOW_CONFIG": str(ROOT / "no-such-infoflow-config.json")},
            clear=False,
        ):
            os.environ.pop("INFOFLOW_VAULT_REMOTE", None)
            self.assertEqual(vault_guard.allowlist(), [vault_guard.DEFAULT_VAULT_REMOTE])


class JournalRemoteTests(unittest.TestCase):
    def test_allowed_remote_writes_once_and_keeps_confirmation_and_event_id(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw) / "vault"
            init_remote(vault, ALLOW)
            refused, data = save_journal(vault, journal_approval(confirmed=False, phrase="写周记"))
            self.assertEqual(refused, 2, data)
            self.assertEqual(data["status"], "refused")
            self.assertIn("可以写", data["message"])
            self.assertEqual(data["files_written"], 0)
            self.assertFalse((vault / "📝 Journal").exists())

            code, data = save_journal(vault, journal_approval())
            self.assertEqual(code, 0, data)
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["files_written"], 1)
            self.assertTrue(Path(data["path"]).is_file())

            again, data = save_journal(vault, journal_approval())
            self.assertEqual(again, 0, data)
            self.assertTrue(data["already_persisted"])
            self.assertEqual(data["files_written"], 0)

    def test_information_flow_remote_is_refused_even_if_allowlisted(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw) / "vault"
            init_remote(vault, PUBLIC)
            subprocess.check_call(
                ["git", "-C", str(vault), "remote", "add", "also", ALLOW]
            )
            code, data = save_journal(
                vault,
                journal_approval(),
                {"INFOFLOW_VAULT_REMOTE": "jakeguo117/information-flow,jakeguo117/obsidian-digitalbrain"},
            )
            self.assertEqual(code, 2, data)
            self.assertEqual(data["message"], vault_guard.PUBLIC_REPO_REFUSAL)
            self.assertEqual(data["files_written"], 0)
            self.assertFalse((vault / "📝 Journal").exists())

    def test_other_remote_and_missing_remote_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            other = Path(raw) / "other"
            init_remote(other, OTHER)
            code, data = save_journal(other, journal_approval())
            self.assertEqual(data["message"], vault_guard.OTHER_REFUSAL, data)
            self.assertEqual(data["files_written"], 0)
            self.assertEqual(code, 2)

            bare = Path(raw) / "bare"
            init_remote(bare, None)
            code, data = save_journal(bare, journal_approval())
            self.assertEqual(data["message"], vault_guard.OTHER_REFUSAL, data)
            self.assertEqual(data["files_written"], 0)

    def test_env_replaces_the_default_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw) / "vault"
            init_remote(vault, OTHER)
            code, data = save_journal(vault, journal_approval(), {"INFOFLOW_VAULT_REMOTE": "example/notes"})
            self.assertEqual(code, 0, data)
            self.assertEqual(data["files_written"], 1)

            blocked = Path(raw) / "default"
            init_remote(blocked, ALLOW)
            code, data = save_journal(
                blocked,
                journal_approval(event_id="vault-guard-other"),
                {"INFOFLOW_VAULT_REMOTE": "example/notes"},
            )
            self.assertEqual(data["message"], vault_guard.OTHER_REFUSAL, data)
            self.assertEqual(data["files_written"], 0)

    def test_config_vault_remote_allows_a_non_default_slug(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            vault = Path(raw) / "vault"
            init_remote(vault, OTHER)
            config = Path(raw) / "config.json"
            config.write_text(json.dumps({"vault_remote": "example/notes"}), encoding="utf-8")
            code, data = save_journal(vault, journal_approval(), {"INFOFLOW_CONFIG": str(config)})
            self.assertEqual(code, 0, data)
            self.assertEqual(data["files_written"], 1)

            placeholder = Path(raw) / "placeholder.json"
            placeholder.write_text(
                json.dumps({"vault_remote": "REPLACE_WITH_VAULT_REMOTE"}),
                encoding="utf-8",
            )
            default_vault = Path(raw) / "default"
            init_remote(default_vault, ALLOW)
            code, data = save_journal(
                default_vault,
                journal_approval(event_id="vault-guard-placeholder"),
                {"INFOFLOW_CONFIG": str(placeholder)},
            )
            self.assertEqual(code, 0, data)
            self.assertEqual(data["files_written"], 1)

    def test_code_checkout_is_refused(self) -> None:
        before = {path.relative_to(ROOT) for path in (ROOT / "📝 Journal").rglob("*") if path.is_file()}
        code, data = save_journal(ROOT, journal_approval(event_id="do-not-write-the-code-repo"))
        after = {path.relative_to(ROOT) for path in (ROOT / "📝 Journal").rglob("*") if path.is_file()}
        self.assertEqual(code, 2, data)
        self.assertEqual(data["files_written"], 0)
        self.assertEqual(data["message"], vault_guard.PUBLIC_REPO_REFUSAL)
        self.assertEqual(before, after)

        with tempfile.TemporaryDirectory() as raw:
            fake = Path(raw) / "repo"
            (fake / "scripts").mkdir(parents=True)
            (fake / "scripts" / "package_journal_pack.py").write_text("# synthetic\n", encoding="utf-8")
            skill = fake / "skills" / "journal"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# synthetic\n", encoding="utf-8")
            init_remote(fake, ALLOW)
            code, data = save_journal(fake, journal_approval(event_id="fake-code-repo"))
            self.assertEqual(data["message"], vault_guard.CODE_REPO_REFUSAL, data)
            self.assertEqual(data["files_written"], 0)
            self.assertFalse((fake / "📝 Journal").exists())


class ThoughtAndOtherWriterTests(unittest.TestCase):
    def test_capture_refuses_public_repo_without_creating_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault = root / "vault"
            init_remote(vault, PUBLIC)
            words = root / "words.txt"
            words.write_text("合成原话\n", encoding="utf-8")
            code, data = run_tool(
                [
                    sys.executable,
                    str(JOURNAL / "capture_thought.py"),
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(words),
                    "--at",
                    "2026-10-23T09:00:00+08:00",
                    "--publish",
                ]
            )
            self.assertEqual(code, 2, data)
            self.assertEqual(data["status"], "not_saved")
            self.assertEqual(data["reason"], vault_guard.PUBLIC_REPO_REFUSAL)
            self.assertEqual(data["verbatim"], "合成原话\n")
            self.assertFalse((vault / "📝 Journal").exists())

    def test_codex_cloud_publish_does_not_push(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            vault = root / "vault"
            remote = root / "remote.git"
            subprocess.check_call(["git", "init", "--bare", "-b", "main", str(remote)], stdout=subprocess.DEVNULL)
            subprocess.check_call(["git", "init", "-b", "main", str(vault)], stdout=subprocess.DEVNULL)
            for args in (
                ["config", "user.email", "synthetic@example.com"],
                ["config", "user.name", "Synthetic"],
                ["config", "commit.gpgsign", "false"],
            ):
                subprocess.check_call(["git", "-C", str(vault), *args])
            (vault / "README.md").write_text("synthetic\n", encoding="utf-8")
            subprocess.check_call(["git", "-C", str(vault), "add", "README.md"])
            subprocess.check_call(["git", "-C", str(vault), "commit", "-m", "init"])
            subprocess.check_call(["git", "-C", str(vault), "remote", "add", "origin", str(remote)])
            subprocess.check_call(["git", "-C", str(vault), "remote", "add", "infoflow-allow", ALLOW])
            subprocess.check_call(["git", "-C", str(vault), "push", "-u", "origin", "main"])
            before = git(remote, "rev-parse", "main").stdout.strip()

            real_git = shutil.which("git")
            self.assertTrue(real_git)
            shim = root / "shim"
            shim.mkdir()
            (shim / "git").write_text(
                "#!/bin/sh\n"
                "if [ \"$1\" = \"push\" ]; then\n"
                "  echo 'push was called' >&2\n"
                "  exit 99\n"
                "fi\n"
                f"exec {real_git} \"$@\"\n",
                encoding="utf-8",
            )
            (shim / "git").chmod(0o755)
            words = root / "words.txt"
            words.write_text("Codex Cloud 通路测试\n", encoding="utf-8")
            env = os.environ.copy()
            env["PATH"] = f"{shim}{os.pathsep}{env.get('PATH', '')}"
            env["INFOFLOW_RUNTIME"] = "codex-cloud"
            env.pop("INFOFLOW_VAULT_REMOTE", None)
            env.pop("INFOFLOW_CONFIG", None)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(JOURNAL / "capture_thought.py"),
                    "add",
                    "--vault",
                    str(vault),
                    "--text-file",
                    str(words),
                    "--at",
                    "2026-10-23T09:05:00+08:00",
                    "--publish",
                ],
                capture_output=True,
                text=True,
                env=env,
            )
            data = json.loads(proc.stdout or "{}")
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            self.assertEqual(data["status"], "success", data)
            self.assertEqual(data["runtime"], "codex-cloud")
            self.assertFalse(data["pushed"])
            self.assertEqual(git(remote, "rev-parse", "main").stdout.strip(), before)
            written = list(vault.rglob("thought-20261023-0905.md"))
            self.assertEqual(len(written), 1)
            status = git(vault, "status", "--porcelain")
            self.assertIn("??", status.stdout)
            self.assertNotIn("push was called", proc.stderr)

    def test_cognition_and_ideas_refuse_and_allow(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            denied = root / "denied"
            init_remote(denied, PUBLIC)
            (root / "payload.md").write_text("nope\n", encoding="utf-8")
            (root / "approval.json").write_text("{}", encoding="utf-8")
            code, data = run_tool(
                [
                    sys.executable,
                    str(COGNITION / "write_cognition.py"),
                    "create",
                    "--vault",
                    str(denied),
                    "--payload",
                    str(root / "payload.md"),
                    "--approval",
                    str(root / "approval.json"),
                ]
            )
            self.assertNotEqual(code, 0)
            self.assertEqual(data["message"], vault_guard.PUBLIC_REPO_REFUSAL)
            self.assertEqual(data["files_written"], 0)

            allowed = root / "allowed"
            init_remote(allowed, ALLOW)
            payload = cognition_lib.render_markdown(
                {
                    "schema_version": "1.1",
                    "id": "evidence-20261023-vault-guard",
                    "type": "evidence",
                    "status": "active",
                    "domains": ["synthetic-widgets"],
                    "related_projects": ["[[Synthetic Widget Project]]"],
                    "created": "2026-10-23",
                    "updated": "2026-10-23",
                    "origin_type": "external_source",
                    "origin_summary": "synthetic vault guard allow",
                    "claim": "Synthetic claim for the vault remote allow test.",
                    "source": "[[source-synthetic-vault-guard]]",
                    "source_type": "interview",
                    "validation": "unverified",
                    "reliability": "low",
                    "scope": "unknown",
                    "limitations": "not established",
                },
                "# evidence-20261023-vault-guard\n\nSynthetic.\n\n## Validation History\n- 2026-10-23: created unverified\n",
            )
            payload_path = root / "payload.md"
            payload_path.write_text(payload, encoding="utf-8")
            approval = {
                "kind": "create",
                "id": "evidence-20261023-vault-guard",
                "type": "evidence",
                "payload_sha256": cognition_lib.fingerprint(payload),
            }
            approval_path = root / "approval.json"
            approval_path.write_text(json.dumps(approval), encoding="utf-8")
            code, data = run_tool(
                [
                    sys.executable,
                    str(COGNITION / "write_cognition.py"),
                    "create",
                    "--vault",
                    str(allowed),
                    "--payload",
                    str(payload_path),
                    "--approval",
                    str(approval_path),
                ]
            )
            self.assertEqual(code, 0, data)
            self.assertEqual(data["status"], "success")
            self.assertTrue(Path(data["path"]).is_file())

            idea_denied = root / "idea-denied"
            init_remote(idea_denied, PUBLIC)
            (idea_denied / "💡 Ideas").mkdir()
            idea_payload = root / "idea.json"
            idea_payload.write_text("{}", encoding="utf-8")
            code, data = run_tool(
                [
                    sys.executable,
                    str(IDEAS / "write_idea.py"),
                    "write",
                    "--vault",
                    str(idea_denied),
                    "--payload",
                    str(idea_payload),
                ]
            )
            self.assertNotEqual(code, 0)
            self.assertEqual(data["error"], vault_guard.PUBLIC_REPO_REFUSAL)
            self.assertEqual(list((idea_denied / "💡 Ideas").glob("idea-*.md")), [])

            sys.path.insert(0, str(IDEAS))
            import test_ideas  # noqa: E402

            packed, _state, _history = test_ideas.make_create(
                test_ideas.EXAMPLE_EXPRESSION,
                [test_ideas.EXAMPLE_REF],
                ["生活"],
                directory="Life",
            )
            idea_ok = root / "idea-ok"
            init_remote(idea_ok, ALLOW)
            (idea_ok / "💡 Ideas" / "Life").mkdir(parents=True)
            ok_path = root / "idea-ok.json"
            ok_path.write_text(json.dumps(packed, ensure_ascii=False), encoding="utf-8")
            code, data = run_tool(
                [
                    sys.executable,
                    str(IDEAS / "write_idea.py"),
                    "write",
                    "--vault",
                    str(idea_ok),
                    "--payload",
                    str(ok_path),
                ]
            )
            self.assertEqual(code, 0, data)
            self.assertTrue(data["ok"], data)
            self.assertTrue(Path(data["path"]).is_file())


class PackagingTests(unittest.TestCase):
    def test_setup_script_pins_ref_and_checks(self) -> None:
        script = ROOT / "packaging" / "codex-cloud" / "setup.sh"
        text = script.read_text(encoding="utf-8")
        self.assertIn(f'INFOFLOW_REF:-{BRANCH}', text)
        self.assertIn("github.com/jakeguo117/information-flow.git", text)
        self.assertNotIn("/Users/", text)
        self.assertNotIn("iCloud", text)
        proc = subprocess.run(["sh", "-n", str(script)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for name in ("AGENTS-snippet.md", "JAKE-STEPS.txt"):
            body = (ROOT / "packaging" / "codex-cloud" / name).read_text(encoding="utf-8")
            self.assertIn("obsidian-digitalbrain", body)
            self.assertIn("INFOFLOW_RUNTIME", body)
            self.assertNotIn("/Users/", body)

    def test_skill_states_the_public_repo_refusal(self) -> None:
        skill = (ROOT / "skills" / "journal" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(vault_guard.PUBLIC_REPO_REFUSAL, skill)
        self.assertIn("INFOFLOW_RUNTIME=codex-cloud", skill)
        self.assertIn("event_id", skill)


if __name__ == "__main__":
    unittest.main()
