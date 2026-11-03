import fcntl, hashlib, json, os, subprocess, sys, tempfile, time, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "bin"))
import push_from_icloud as m  # noqa: E402

GENV = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "Other", "GIT_AUTHOR_EMAIL": "o@x", "GIT_COMMITTER_NAME": "Other",
        "GIT_COMMITTER_EMAIL": "o@x"}
SN = "📥 Inbox/Snipd"
WR = "📥 Inbox/WeRead"
BK = "📚 Books/哲学宗教"


def git(*a, cwd=None):
    cp = subprocess.run(["git", "-c", "core.quotepath=false", *a], cwd=cwd, env=GENV, capture_output=True)
    if cp.returncode:
        raise RuntimeError(f"git {a}: {cp.stderr.decode()}")
    return cp.stdout.decode().strip()


def old(p: Path, age=3600):
    t = time.time() - age
    os.utime(p, (t, t))


class Base(unittest.TestCase):
    def setUp(self):
        m.release_guard()
        self.cwd0 = os.getcwd()
        self.t = Path(tempfile.mkdtemp())
        t = self.t
        self.remote = t / "remote.git"
        git("init", "-q", "--bare", "-b", "main", str(self.remote))
        self.other = t / "other"
        git("clone", "-q", str(self.remote), str(self.other))
        files = {
            f"{SN}/a.md": "# A\nold a\n", f"{SN}/c.md": "c\n", f"{WR}/w.md": "w\n",
            f"{BK}/洞见.md": "# 洞见\n第一章\n", "📝 Journal/j.md": "j\n", ".obsidian/app.json": "{}\n",
        }
        for k, v in files.items():
            p = self.other / k
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(v)
        git("add", "-A", cwd=self.other)
        git("commit", "-qm", "seed", cwd=self.other)
        git("push", "-q", "origin", "HEAD:main", cwd=self.other)
        self.vault = t / "Mobile Documents" / "DigitalBrain"
        self.vault.mkdir(parents=True)
        self.gdir = t / "gitdir-imac"
        tmpc = t / "tmpc"
        git("clone", "-q", "--no-checkout", str(self.remote), str(tmpc))
        os.rename(tmpc / ".git", self.gdir)
        git(f"--git-dir={self.gdir}", "config", "core.bare", "false")
        git(f"--git-dir={self.gdir}", "config", "core.worktree", str(self.vault))
        git(f"--git-dir={self.gdir}", f"--work-tree={self.vault}", "checkout", "-q", "-f", "main")
        for p in self.vault.rglob("*"):
            if p.is_file():
                old(p)
        self.repo = t / "pusher" / "repo"
        git("clone", "-q", str(self.remote), str(self.repo))
        self.state = t / "pusher" / "state"

    def tearDown(self):
        m.release_guard()
        m._between_reads_hook = m._before_push_hook = m._before_bookkeeping_hook = None
        os.chdir(self.cwd0)

    def run_main(self, *extra):
        before = self.snapshot()
        try:
            rc = m.main(["--vault", str(self.vault), "--repo", str(self.repo), "--pull-gitdir", str(self.gdir),
                         "--state", str(self.state), "--ignore-quiet", "--recheck-seconds", "0", *extra])
        finally:
            m.release_guard()
            os.chdir(self.cwd0)
        self.assertEqual(before, self.snapshot(), "vault changed by pusher")
        name = "status-dryrun.json" if "--dry-run" in extra else "status.json"
        return rc, json.loads((self.state / name).read_text())

    def snapshot(self):
        out = {}
        for p in sorted(self.vault.rglob("*")):
            if p.is_file():
                out[str(p)] = (hashlib.sha1(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            else:
                out[str(p)] = "dir"
        return out

    def vwrite(self, rel, text, age=3600):
        p = self.vault / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        if age is not None:
            old(p, age)
        return p

    def remote_head(self):
        return git(f"--git-dir={self.remote}", "rev-parse", "main")

    def remote_files(self, rev="main"):
        return set(git(f"--git-dir={self.remote}", "ls-tree", "-r", "--name-only", rev).splitlines())

    def remote_show(self, path, rev="main"):
        return git(f"--git-dir={self.remote}", "show", f"{rev}:{path}")

    def other_push(self, rel, text):
        git("pull", "-q", "--ff-only", cwd=self.other)
        p = self.other / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        git("add", "--", rel, cwd=self.other)
        git("commit", "-qm", f"other: {rel}", cwd=self.other)
        git("push", "-q", "origin", "HEAD:main", cwd=self.other)

    def g_head(self):
        return git(f"--git-dir={self.gdir}", "rev-parse", "HEAD")

    def g_index_tree(self):
        return git(f"--git-dir={self.gdir}", f"--work-tree={self.t}", "write-tree")


class TestPush(Base):
    def test_local_change_pushed_exact_path_and_bookkeeping(self):
        self.vwrite(f"{SN}/a.md", "# A\nnew a\n## 新标题\n")
        (self.repo / "junk.txt").write_text("untracked junk")
        h0 = self.remote_head()
        rc, st = self.run_main()
        self.assertEqual(rc, 0, st)
        self.assertEqual(st["result"], "pushed", st)
        h1 = self.remote_head()
        self.assertNotEqual(h0, h1)
        changed = git(f"--git-dir={self.remote}", "diff", "--name-only", h0, h1).splitlines()
        self.assertEqual(changed, [f"{SN}/a.md"])
        self.assertIn("## 新标题", st["headings_added"][f"{SN}/a.md"])
        self.assertTrue(git(f"--git-dir={self.remote}", "log", "-1", "--format=%s").startswith("imac: sync"))
        self.assertNotIn("junk.txt", self.remote_files())
        self.assertEqual(self.g_head(), h1)
        self.assertEqual(self.g_index_tree(), git(f"--git-dir={self.remote}", "rev-parse", "main^{tree}"))
        rc, st = self.run_main()
        self.assertEqual(st["result"], "noop", st)

    def test_out_of_scope_never_pushed(self):
        self.vwrite("📝 Journal/j.md", "changed\n")
        self.vwrite(".obsidian/app.json", '{"x":1}\n')
        self.vwrite(f"{SN}/.hidden.md", "x\n")
        h0 = self.remote_head()
        rc, st = self.run_main()
        self.assertEqual(st["result"], "noop", st)
        self.assertEqual(self.remote_head(), h0)
        lst = self.t / "only.txt"
        lst.write_text("📝 Journal/j.md\n")
        rc, st = self.run_main("--only-paths", str(lst))
        self.assertEqual(rc, 2)
        self.assertIn("outside the three folders", " ".join(st["errors"]))
        self.assertEqual(self.remote_head(), h0)

    def test_placeholders_and_dataless_skipped(self):
        self.vwrite(f"{SN}/.new.md.icloud", "stub")
        self.vwrite(f"{SN}/data.md", "would be dataless\n")
        orig = m.is_dataless
        m.is_dataless = lambda st: st.st_size == len("would be dataless\n")
        try:
            os.remove(self.vault / SN / "c.md")
            self.vwrite(f"{SN}/.c.md.icloud", "stub")
            rc, st = self.run_main()
        finally:
            m.is_dataless = orig
        self.assertEqual(st["result"], "noop", st)
        self.assertIn(f"{SN}/data.md", st["skipped"]["placeholder"])
        self.assertIn(f"{SN}/c.md", st["skipped"]["placeholder"])
        self.assertNotIn(f"{SN}/c.md", st["skipped"]["missing_in_vault_not_pushed"])
        self.assertIn(f"{SN}/c.md", self.remote_files())

    def test_icloud_copies_skipped_but_tech_euphoria_kept(self):
        self.vwrite(f"{SN}/a 2.md", "copy\n")
        self.vwrite(f"{SN}/GPT-6 Hits AGI_ Tech Euphoria 2.0 ep.md", "real\n")
        self.vwrite(f"{SN}/Episode 2.md", "no sibling, real\n")
        rc, st = self.run_main()
        self.assertEqual(st["result"], "pushed", st)
        files = self.remote_files()
        self.assertNotIn(f"{SN}/a 2.md", files)
        self.assertIn(f"{SN}/GPT-6 Hits AGI_ Tech Euphoria 2.0 ep.md", files)
        self.assertIn(f"{SN}/Episode 2.md", files)
        self.assertIn(f"{SN}/a 2.md", st["skipped"]["icloud_copy"])

    def test_recent_and_changing_files_skipped(self):
        self.vwrite(f"{SN}/a.md", "fresh\n", age=10)
        h0 = self.remote_head()
        rc, st = self.run_main()
        self.assertEqual(st["result"], "noop", st)
        self.assertIn(f"{SN}/a.md", st["skipped"]["still_writing"])
        self.vwrite(f"{SN}/a.md", "settled\n")

        def change():
            m.release_guard()
            self.vwrite(f"{SN}/a.md", "changed between reads\n")
            m.install_guard(self.vault, self.gdir, self.state / "empty-worktree", self.repo)
        m._between_reads_hook = change
        before = self.snapshot()
        try:
            m.main(["--vault", str(self.vault), "--repo", str(self.repo), "--pull-gitdir", str(self.gdir),
                    "--state", str(self.state), "--ignore-quiet", "--recheck-seconds", "0"])
        finally:
            m.release_guard()
            os.chdir(self.cwd0)
        st = json.loads((self.state / "status.json").read_text())
        self.assertEqual(st["result"], "noop", st)
        self.assertEqual(self.remote_head(), h0)
        self.assertNotEqual(before, self.snapshot())  # only our test hook changed it

    def test_both_sides_changed_skipped(self):
        self.other_push(f"{SN}/a.md", "# A\ngithub edit\n")
        self.vwrite(f"{SN}/a.md", "# A\nlocal edit\n")
        self.vwrite(f"{WR}/w.md", "w local only\n")
        h0 = self.remote_head()
        rc, st = self.run_main("--pull-behind-alert-seconds", "0")
        self.assertEqual(st["result"], "skip_pull_behind", st)
        self.assertEqual(self.remote_head(), h0)
        self.assertEqual(st["skipped"]["both_changed"], [f"{SN}/a.md"])
        self.assertTrue(any("两边都改了" in a for a in st["needs_attention"]))
        self.assertEqual(self.remote_show(f"{SN}/a.md"), "# A\ngithub edit")

    def test_synced_base_both_changed_per_file(self):
        # gate passes (pull current) but our own record says GitHub moved since last sync
        self.vwrite(f"{SN}/a.md", "# A\nlocal edit\n")
        self.state.mkdir(parents=True, exist_ok=True)
        (self.state / "synced.json").write_text(json.dumps({f"{SN}/a.md": "0" * 40}))
        orig = m.Git.tree

        def fake_tree(self_, commit, paths=()):
            res = orig(self_, commit, paths)
            if self_.base[0].startswith("--git-dir"):
                k = f"{SN}/a.md"
                res[k] = (res[k][0], "0" * 40, res[k][2])
            return res
        m.Git.tree = fake_tree
        try:
            rc, st = self.run_main()
        finally:
            m.Git.tree = orig
        self.assertIn(f"{SN}/a.md", st["skipped"]["both_changed"], st)
        self.assertEqual(st["result"], "noop")

    def test_deletions_never_pushed(self):
        os.remove(self.vault / SN / "c.md")
        os.remove(self.vault / BK / "洞见.md")
        h0 = self.remote_head()
        rc, st = self.run_main()
        self.assertEqual(st["result"], "noop", st)
        self.assertEqual(self.remote_head(), h0)
        self.assertIn(f"{SN}/c.md", st["skipped"]["missing_in_vault_not_pushed"])
        self.assertIn(f"{SN}/c.md", self.remote_files())

    def test_push_rejected_drops_local_commit(self):
        self.vwrite(f"{SN}/a.md", "# A\nlocal\n")
        h0 = self.remote_head()
        m._before_push_hook = lambda: self.other_push(f"{WR}/w.md", "foreign\n")
        rc, st = self.run_main()
        self.assertEqual(st["result"], "push_rejected", st)
        foreign = self.remote_head()
        self.assertNotEqual(foreign, h0)
        self.assertEqual(git("log", "-1", "--format=%s", foreign, cwd=self.other), f"other: {WR}/w.md")
        self.assertEqual(git("rev-parse", "HEAD", cwd=self.repo), h0)  # dropped, not merged/rebased
        self.assertEqual(git("status", "--porcelain", "--untracked-files=no", cwd=self.repo), "")
        self.assertEqual(self.g_head(), h0)
        self.assertEqual(self.remote_show(f"{SN}/a.md"), "# A\nold a")
        reflog = git("reflog", "--format=%gs", cwd=self.repo)
        self.assertNotIn("rebase", reflog)
        self.assertNotIn("merge", reflog)

    def test_pull_behind_skips_round(self):
        self.other_push(f"{WR}/w.md", "upstream\n")
        self.vwrite(f"{SN}/a.md", "# A\nlocal\n")
        h0 = self.remote_head()
        rc, st = self.run_main()
        self.assertEqual(st["result"], "skip_pull_behind")
        self.assertEqual(st["needs_attention"], [])
        rc, st = self.run_main("--pull-behind-alert-seconds", "0")
        self.assertTrue(any("拉取卡住" in a for a in st["needs_attention"]), st)
        self.assertEqual(self.remote_head(), h0)

    def test_bookkeeping_only_when_vault_matches(self):
        self.vwrite(f"{SN}/a.md", "# A\nv1\n")
        g0 = self.g_head()

        def touch():
            m.release_guard()
            self.vwrite(f"{SN}/a.md", "# A\nv2 after push\n")
            m.install_guard(self.vault, self.gdir, self.state / "empty-worktree", self.repo)
        m._before_bookkeeping_hook = touch
        try:
            m.main(["--vault", str(self.vault), "--repo", str(self.repo), "--pull-gitdir", str(self.gdir),
                    "--state", str(self.state), "--ignore-quiet", "--recheck-seconds", "0"])
        finally:
            m.release_guard()
            os.chdir(self.cwd0)
        st = json.loads((self.state / "status.json").read_text())
        self.assertEqual(st["result"], "pushed_bookkeeping_pending", st)
        self.assertEqual(self.g_head(), g0)
        self.assertTrue((self.state / "pending_bookkeeping.json").exists())
        m._before_bookkeeping_hook = None
        rc, st = self.run_main()
        self.assertEqual(st["result"], "pushed", st)
        self.assertEqual(self.remote_show(f"{SN}/a.md"), "# A\nv2 after push")
        self.assertEqual(self.g_head(), self.remote_head())
        self.assertFalse((self.state / "pending_bookkeeping.json").exists())
        authors = git(f"--git-dir={self.remote}", "log", "--format=%an", "-2").splitlines()
        self.assertEqual(authors, [m.COMMIT_NAME, m.COMMIT_NAME])

    def test_lock(self):
        self.state.mkdir(parents=True)
        with open(self.state / "push.lock", "a+") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            rc, st = self.run_main()
        self.assertEqual(st["result"], "locked")

    def test_dry_run_and_only_paths(self):
        self.vwrite(f"{SN}/a.md", "# A\nnew\n## H2\n")
        self.vwrite(f"{BK}/洞见.md", "# 洞见\n第一章\n## 第十一章\n")
        self.vwrite(f"{WR}/w.md", "not in list\n")
        lst = self.t / "only.txt"
        lst.write_text(f"{SN}/a.md\n{BK}/洞见.md\n")
        h0 = self.remote_head()
        rc, st = self.run_main("--dry-run", "--probe-push", "--only-paths", str(lst))
        self.assertEqual(st["result"], "dry_run_ok", st)
        self.assertEqual(self.remote_head(), h0)
        self.assertEqual(self.g_head(), h0)
        self.assertEqual(sorted(st["paths"]), sorted([f"{SN}/a.md", f"{BK}/洞见.md"]))
        self.assertEqual(st["probe_push"]["rc"], 0, st)
        self.assertEqual(git("rev-parse", "HEAD", cwd=self.repo), st["commit"])
        self.assertIn("## 第十一章", st["headings_added"][f"{BK}/洞见.md"])
        self.assertFalse((self.state / "status.json").exists())

    def test_quiet_window(self):
        before = self.snapshot()
        try:
            m.main(["--vault", str(self.vault), "--repo", str(self.repo), "--pull-gitdir", str(self.gdir),
                    "--state", str(self.state), "--now", "2026-11-02T00:10:00+00:00"])  # Mon 08:10 Shanghai
        finally:
            m.release_guard()
            os.chdir(self.cwd0)
        st = json.loads((self.state / "status.json").read_text())
        self.assertEqual(st["result"], "quiet")
        self.assertEqual(before, self.snapshot())


class TestGuard(Base):
    def test_write_guard_blocks_everything(self):
        dummy = self.t / "dummy"
        dummy.mkdir()
        m.install_guard(self.vault, self.gdir, dummy, self.repo)
        target = self.vault / SN / "x.md"
        with self.assertRaises(m.GuardViolation):
            open(target, "w")
        with self.assertRaises(m.GuardViolation):
            os.open(str(target), os.O_WRONLY | os.O_CREAT)
        with self.assertRaises(m.GuardViolation):
            os.remove(self.vault / SN / "c.md")
        with self.assertRaises(m.GuardViolation):
            os.rename(self.vault / SN / "c.md", self.vault / SN / "d.md")
        with self.assertRaises(m.GuardViolation):
            os.mkdir(self.vault / "newdir")
        with self.assertRaises(m.GuardViolation):
            subprocess.run(["true"], cwd=str(self.vault))
        with self.assertRaises(m.GuardViolation):
            subprocess.run(["git", f"--git-dir={self.gdir}", "status"])
        with self.assertRaises(m.GuardViolation):
            subprocess.run(["git", f"--git-dir={self.gdir}", f"--work-tree={dummy}", "checkout", "main"])
        with self.assertRaises(m.GuardViolation):
            subprocess.run(["git", f"--git-dir={self.gdir}", f"--work-tree={dummy}", "read-tree", "-u", "-m", "HEAD"])
        with self.assertRaises(m.GuardViolation):
            subprocess.run(["git", "-C", str(self.repo), f"--work-tree={self.vault}", "status"])
        open(self.vault / SN / "c.md", "rb").close()  # reading is fine
        m.release_guard()
        self.assertFalse(target.exists())
        self.assertTrue((self.vault / SN / "c.md").exists())
        self.assertFalse((self.vault / "newdir").exists())

    def test_guard_abort_in_main(self):
        self.vwrite(f"{SN}/a.md", "# A\nlocal\n")
        h0 = self.remote_head()
        m._before_push_hook = lambda: open(self.vault / SN / "evil.md", "w")
        rc, st = self.run_main()
        self.assertEqual(rc, 3)
        self.assertEqual(st["result"], "guard_abort")
        self.assertFalse((self.vault / SN / "evil.md").exists())
        self.assertEqual(self.remote_head(), h0)


class TestUnits(unittest.TestCase):
    def test_scope(self):
        self.assertTrue(m.in_scope("📥 Inbox/Snipd/x.md"))
        self.assertTrue(m.in_scope("📚 Books/📖 读后感/x.md"))
        for bad in ("📥 Inbox/X-Bookmarks/x.md", "📥 Inbox/Snipd", "📥 Inbox/Snipd/../j.md",
                    ".obsidian/app.json", "📥 Inbox/Snipd/.x.md", "📝 Journal/x.md", "/abs"):
            self.assertFalse(m.in_scope(bad), bad)

    def test_copy_regex(self):
        sib = {"a.md", "dir"}
        self.assertTrue(m.is_icloud_copy("a 2.md", sib))
        self.assertTrue(m.is_icloud_copy("dir 2", sib))
        self.assertFalse(m.is_icloud_copy("b 2.md", sib))
        self.assertFalse(m.is_icloud_copy("GPT-6 Hits AGI_ Tech Euphoria 2.0 ep.md",
                                          {"GPT-6 Hits AGI_ Tech Euphoria.md", "GPT-6 Hits AGI_ Tech Euphoria 2.0 ep.md"}))

    def test_classify(self):
        self.assertTrue(m.classify_rejected(" ! [rejected]        HEAD -> main (fetch first)"))
        self.assertTrue(m.classify_auth("remote: Permission to x denied to y. 403"))


if __name__ == "__main__":
    unittest.main()
