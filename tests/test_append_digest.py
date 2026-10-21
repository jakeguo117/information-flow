"""--append-digest no longer copies a digest onto the journal (J06-A)."""
import json, subprocess, sys, tempfile, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
TOOLS = HERE / "skills/journal/tools"
sys.path.insert(0, str(TOOLS))
from journal_lib import render_journal, read_digest, fingerprint

def run(vault, approval, *extra):
    ap = vault.parent / "approval.json"
    ap.write_text(json.dumps(approval, ensure_ascii=False), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(TOOLS / "write_journal.py"), "save", "--vault", str(vault), "--approval", str(ap), *extra],
        capture_output=True,
        text=True,
    )
    return proc.returncode, json.loads(proc.stdout)

tmp = Path(tempfile.mkdtemp())
vault = tmp / "vault"
try:
    vault.mkdir()
    (vault / "📋 Digests/2026-W42").mkdir(parents=True)
    dg = vault / "📋 Digests/2026-W42/digest.md"
    dg.write_text(
        "---\nweek: 2026-W42\n---\n\n# 本周 digest（2026-W42）\n\n- **T-2026W42-1**\n",
        encoding="utf-8",
    )
    base = dict(
        confirmed=True,
        phrase="可以写",
        date="2026-10-16",
        journal_number=42,
        title="合成测试",
        event_id="journal-test-42",
        body="合成正文。",
        topics=[],
        previous="",
    )
    base["payload_sha256"] = fingerprint(render_journal(base))
    rel = "📋 Digests/2026-W42/digest.md"
    before = dg.read_bytes()

    rc, out = run(vault, base, "--append-digest", rel)
    assert rc == 2 and out["status"] == "unavailable" and out["files_written"] == 0, out
    assert "--digest-snapshot" in out["message"], out
    assert "本周 digest" not in out["message"]
    assert not (vault / "📝 Journal").exists()
    assert dg.read_bytes() == before

    stale = dict(base, payload_sha256="0" * 64)
    rc, out = run(vault, stale, "--append-digest", rel)
    assert rc == 2 and out["status"] == "unavailable" and out["files_written"] == 0, out
    assert "--digest-snapshot" in out["message"], out
    assert not (vault / "📝 Journal").exists()

    rc, out = run(vault, base, "--append-digest", str(tmp / "outside.md"))
    assert rc == 2 and out["status"] == "unavailable" and "--digest-snapshot" in out["message"], out
    assert not (vault / "📝 Journal").exists()

    rc, out = run(vault, base)
    assert rc == 0 and out["status"] == "success" and out["files_written"] == 1, out
    text = Path(out["path"]).read_text(encoding="utf-8")
    assert "本周 digest" not in text and "T-2026W42-1" not in text and "digest_id:" not in text, text
    rc, out = run(vault, base)
    assert rc == 0 and out["already_persisted"] is True and out["files_written"] == 0, out

    marked = dg.read_text(encoding="utf-8").rstrip("\n") + "\n<!-- information-flow-weekly-digest generator=1 sha256=" + ("ab" * 32) + " -->\n"
    dg.write_text(marked, encoding="utf-8")
    assert "information-flow-weekly-digest" not in read_digest(vault, Path(rel))
    assert "information-flow-weekly-digest" in dg.read_text(encoding="utf-8")
    try:
        read_digest(vault, Path(tmp / "outside.md"))
        raise AssertionError("outside digest was readable")
    except OSError:
        pass
    print("ALL PASS")
finally:
    shutil.rmtree(tmp)
