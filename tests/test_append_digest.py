"""最小测试：write_journal.py --append-digest 一次写入周记 + digest（临时目录）。"""
import json, subprocess, sys, tempfile, shutil
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
TOOLS = Path(__file__).resolve().parents[1] / "skills/journal/tools"
sys.path.insert(0, str(TOOLS))
from journal_lib import render_journal, read_digest, fingerprint

def run(vault, approval, *extra):
    ap = vault.parent / "approval.json"; ap.write_text(json.dumps(approval, ensure_ascii=False), encoding="utf-8")
    p = subprocess.run([sys.executable, str(TOOLS / "write_journal.py"), "save", "--vault", str(vault), "--approval", str(ap), *extra], capture_output=True, text=True)
    return p.returncode, json.loads(p.stdout)

tmp = Path(tempfile.mkdtemp()); vault = tmp / "vault"
try:
    (vault / "📋 Digests/2026-W42").mkdir(parents=True)
    dg = vault / "📋 Digests/2026-W42/digest.md"
    dg.write_text("---\nweek: 2026-W42\n---\n\n# 本周 digest（2026-W42）\n\n## 值得讨论的（thesis）\n\n- **T-2026W42-a**｜合成一句话｜[原文](https://example.com/a)\n  - 我的看法：\n", encoding="utf-8")
    base = dict(confirmed=True, phrase="可以写", date="2026-10-16", journal_number=42, title="合成测试", event_id="journal-test-42", body="合成正文。", topics=[], previous="2026-10-11 终于有一条线开始出结果了", digest_week="2026-W42")
    rel = "📋 Digests/2026-W42/digest.md"
    a = dict(base, payload_sha256=fingerprint(render_journal(base, read_digest(vault, Path(rel)))))
    rc, out = run(vault, a, "--append-digest", rel)
    assert rc == 0 and out["status"] == "success" and out["files_written"] == 1, out
    text = Path(out["path"]).read_text(encoding="utf-8")
    assert text.index("**Previous / 上一篇:**") < text.index("## 本周 digest（2026-W42）") < text.index("T-2026W42-a"), "digest 不在末尾"
    assert "week: 2026-W42" not in text, "digest frontmatter 不应写入"
    assert text.count("event_id:") == 1
    rc, out = run(vault, a, "--append-digest", rel)                      # 重放：幂等
    assert rc == 0 and out["already_persisted"] is True and out["files_written"] == 0, out
    rc, out = run(vault, a)                                             # 不带 digest：哈希对不上
    assert rc == 2 and out["status"] == "stale_approval", out
    rc, out = run(vault, a, "--append-digest", str(tmp / "outside.md"))  # 库外路径
    assert rc == 2 and out["status"] == "unavailable", out
    b = dict(base, event_id="journal-test-legacy", title="旧用法"); b["payload_sha256"] = fingerprint(render_journal(b))
    rc, out = run(vault, b)                                             # 旧用法不受影响
    assert rc == 0 and "本周 digest" not in Path(out["path"]).read_text(encoding="utf-8"), out
    print("ALL PASS (5 cases)")
finally:
    shutil.rmtree(tmp)
