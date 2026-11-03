"""Templates + deploy.example.env must reproduce the plists running on the iMac.

The sha256 values are the fingerprints recorded when the jobs were installed on
2026-11-01 (EXECUTION cards 5-7; build/sha256.txt). If a template changes on
purpose, update the fingerprint here in the same change and redeploy.
"""
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "bin"))
import render_launchd as r  # noqa: E402

RUNNING = {
    "com.jake.digitalbrain-imac-push.plist":
        "8c500cc1f6ebf8c2366756e362efc08447731e1759b0ee187dfa93b0381045b0",
    "com.jake.digitalbrain-imac-push.dryrun.plist":
        "6bc8071a96986c658d70822298faeec2b36cb7a96045e2ab8cbaf7eba5e06c2f",
    "com.jake.digitalbrain-imac-push.cutover.plist":
        "7ab711bf81856bd1a414627ec9a9e9c4ae590f7718c1c8b9fd4261babff68c50",
}
SCRIPT_SHA = "c12a6af32bc1fc8518d544d0712ed5ee99ee73c2ac6d7cb0f1ad1da738d74b49"


class RenderTests(unittest.TestCase):
    def test_example_env_reproduces_running_plists(self):
        rendered = r.render_all(r.read_env(ROOT / "deploy.example.env"))
        self.assertEqual(set(rendered), set(RUNNING))
        for name, text in rendered.items():
            self.assertEqual(hashlib.sha256(text.encode("utf-8")).hexdigest(), RUNNING[name], name)

    def test_script_is_the_running_version(self):
        data = (ROOT / "bin" / "push_from_icloud.py").read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), SCRIPT_SHA)

    def test_templates_have_no_personal_paths(self):
        for tpl in (ROOT / "launchd").glob("*.plist"):
            text = tpl.read_text(encoding="utf-8")
            self.assertNotIn("/Users/", text, tpl.name)
            self.assertNotIn("hermes", text, tpl.name)
            self.assertTrue(r.PLACEHOLDER.search(text), tpl.name)

    def test_missing_value_fails(self):
        values = r.read_env(ROOT / "deploy.example.env")
        values.pop("__VAULT__")
        with self.assertRaises(SystemExit):
            r.render_all(values)

    def test_unknown_key_fails(self):
        values = r.read_env(ROOT / "deploy.example.env")
        values["__NOT_USED__"] = "x"
        with self.assertRaises(SystemExit):
            r.render_all(values)

    def test_cli_writes_files_and_prints_sha(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "rendered"
            cp = subprocess.run(
                [sys.executable, str(ROOT / "bin" / "render_launchd.py"),
                 "--env", str(ROOT / "deploy.example.env"), "--out", str(out)],
                capture_output=True, text=True, check=True)
            lines = dict(reversed(l.split("  ", 1)) for l in cp.stdout.splitlines())
            self.assertEqual(lines, {k: v for k, v in RUNNING.items()})
            self.assertEqual(sorted(p.name for p in out.iterdir()), sorted(RUNNING))


if __name__ == "__main__":
    unittest.main()
