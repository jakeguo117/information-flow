"""Acceptance tests for the DigitalBrain backup. Uses temp dirs and fakes."""

from __future__ import annotations

import hashlib
import json
import os
import plistlib
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import digitalbrain_backup as db  # noqa: E402

NOW_TUESDAY = "2026-10-13T03:30:00+08:00"
NOW_SUNDAY = "2023-01-01T03:30:00+08:00"


@dataclass
class World:
    work: Path
    vol: Path
    backup: Path
    vault: Path
    bare: Path
    src: Path
    cfg: db.Config
    cfg_path: Path
    hermes_log: Path
    home_log: Path


def write_exec(path: Path, text: str) -> None:
    path.write_text(text)
    path.chmod(0o755)


def diskutil_script(path: Path, mounted: str) -> None:
    script = """#!/bin/bash
if [[ "${1:-}" != "info" ]]; then exit 2; fi
if [[ -n "__MOUNTED__" && "$2" == "__MOUNTED__" ]]; then
  printf 'Volume Name: Disk\\nMount Point: %s\\nMounted: Yes\\n' "$2"
  exit 0
fi
echo "Mounted: No"
echo "Mount Point: Not applicable"
exit 1
"""
    write_exec(path, script.replace("__MOUNTED__", mounted))


def hermes_script(path: Path, log: Path) -> None:
    write_exec(
        path,
        "#!/bin/bash\nprintf '%s\\n' \"$*\" >> \"__LOG__\"\nexit 0\n".replace("__LOG__", str(log)),
    )


def hermes_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line for line in path.read_text().splitlines() if line.strip()]


def init_origin(src: Path, bare: Path) -> None:
    subprocess.check_call(["git", "init", "-b", "main", str(src)])
    subprocess.check_call(["git", "-C", str(src), "config", "user.email", "test@example.com"])
    subprocess.check_call(["git", "-C", str(src), "config", "user.name", "Test"])
    (src / "hello.txt").write_text("v1\n")
    subprocess.check_call(["git", "-C", str(src), "add", "hello.txt"])
    subprocess.check_call(["git", "-C", str(src), "commit", "-m", "init"])
    subprocess.check_call(["git", "clone", "--bare", str(src), str(bare)])


def preseed_old(backup: Path) -> None:
    day = backup / "vault" / "daily" / "1999-01-01"
    day.mkdir(parents=True)
    (day / "keep.txt").write_text("keep-me")
    git_day = backup / "git" / "daily"
    git_day.mkdir(parents=True)
    (git_day / "1999-01-01.bundle").write_text("old-bundle")


def make_world(
    tmp: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    now: str = NOW_TUESDAY,
    timeout: float = 30,
    mounted: bool = True,
    create_root: bool = True,
    with_git: bool = True,
    dataless: bool = False,
    vault_files: dict[str, str] | None = None,
) -> World:
    monkeypatch.setenv("DIGITALBRAIN_BACKUP_NOW", now)
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    monkeypatch.delenv("DIGITALBRAIN_BACKUP_PYTHON", raising=False)
    monkeypatch.delenv("DIGITALBRAIN_BACKUP_STAT_BIN", raising=False)
    monkeypatch.delenv("DIGITALBRAIN_BACKUP_LS_BIN", raising=False)
    work = tmp / "work"
    vol = work / "vol"
    backup = vol / "DigitalBrain-Backups"
    vault = work / "Library" / "Mobile Documents" / "iCloud~md~obsidian" / "Documents" / "DigitalBrain"
    vol.mkdir(parents=True)
    vault.mkdir(parents=True)
    files = {"notes/hello.md": "hello\n"} if vault_files is None else vault_files
    for rel, text in files.items():
        path = vault / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    src = work / "src"
    bare = work / "origin.git"
    if with_git:
        init_origin(src, bare)
        remote = str(bare)
    else:
        remote = "https://github.com/jakeguo117/obsidian-digitalbrain.git"
    if create_root:
        backup.mkdir(parents=True)
        (backup / ".backup-target").write_text("digitalbrain-backup-target\n")
    else:
        (vol / "do-not-touch.txt").write_text("decoy\n")
    diskutil = work / "diskutil"
    diskutil_script(diskutil, str(vol) if mounted else "")
    mounts = work / "mounts"
    if mounted:
        mounts.write_text(f"/dev/disk3s1 {vol} apfs rw\n")
    else:
        mounts.write_text("")
    hermes_log = work / "hermes.log"
    hermes = work / "hermes"
    hermes_script(hermes, hermes_log)
    home_log = work / "home.log"
    data = {
        "volume": str(vol),
        "backup_folder": "DigitalBrain-Backups",
        "github_repo": "jakeguo117/obsidian-digitalbrain",
        "github_remote": remote,
        "git_branch": "main",
        "vault_path": str(vault),
        "retention": {"daily": 14, "weekly": 8, "monthly": 12},
        "discord_channel_id": "123",
        "hermes_command": [
            str(hermes),
            "send",
            "--to",
            "discord:{channel_id}",
            "--quiet",
            "--subject",
            "{subject}",
            "{message}",
        ],
        "disk_log_name": "digitalbrain-backup.log",
        "home_log": str(home_log),
        "timezone": "Asia/Shanghai",
        "read_timeout_seconds": timeout,
        "mount_table": str(mounts),
        "diskutil_bin": str(diskutil),
    }
    if dataless:
        stat_bin = work / "stat"
        write_exec(stat_bin, "#!/bin/bash\necho 1073741824\n")
        data["stat_bin"] = str(stat_bin)
    cfg_path = work / "config.json"
    cfg_path.write_text(json.dumps(data))
    return World(work, vol, backup, vault, bare, src, db.load_config(cfg_path), cfg_path, hermes_log, home_log)


def read_status(backup: Path) -> dict:
    return json.loads((backup / "status.json").read_text())


def assert_old_kept(world: World, rc: int, status: dict, *, day: str = "2026-10-13") -> None:
    assert rc == 1
    assert status["result"] == "failed"
    assert status["prune"]["ran"] is False
    assert status["prune"]["deleted"] == []
    assert (world.backup / "vault" / "daily" / "1999-01-01" / "keep.txt").read_text() == "keep-me"
    assert (world.backup / "git" / "daily" / "1999-01-01.bundle").read_text() == "old-bundle"
    assert not (world.backup / "vault" / "daily" / day).exists()
    lines = hermes_lines(world.hermes_log)
    assert len(lines) == 1
    assert "send" in lines[0] and "discord:" in lines[0]


def test_example_config_and_plist() -> None:
    raw = (ROOT / "config.example.json").read_text()
    assert "/Users/jake/Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain" in raw
    cfg = db.load_config(ROOT / "config.example.json")
    assert cfg.retention_daily == 14
    assert cfg.retention_weekly == 8
    assert cfg.retention_monthly == 12
    assert cfg.github_repo == "jakeguo117/obsidian-digitalbrain"
    assert cfg.volume == Path("/Volumes/Disk")
    assert cfg.backup_folder == "DigitalBrain-Backups"
    text = (ROOT / "launchd" / "com.jake.digitalbrain-backup.plist").read_text()
    assert "__DEDICATED_PYTHON__" in text
    assert "__HOME__" in text
    assert "__DIGITALBRAIN_BACKUP_ROOT__" in text
    plist = plistlib.loads(text.encode())
    assert plist["Label"] == "com.jake.digitalbrain-backup"
    assert plist["StartCalendarInterval"]["Hour"] == 3
    assert plist["StartCalendarInterval"]["Minute"] == 30
    assert "RunAtLoad" not in plist
    assert plist["ProgramArguments"][0] == "__DEDICATED_PYTHON__"
    for path in [ROOT / "digitalbrain_backup.py", * (ROOT / "bin").glob("*"), *(ROOT / "launchd").glob("*")]:
        body = path.read_text()
        assert "launchctl" not in body
        assert "obsidian-vault-sync" not in body


def test_readme_documents_permission_and_schedule() -> None:
    text = (ROOT / "README.md").read_text()
    for needle in (
        "Full Disk Access",
        "python3-digitalbrain-backup",
        "com.jake.obsidian-vault-sync",
        "03:30",
        "demo-unmounted",
        "demo-failure",
        "restore-test",
        "/Volumes/Disk",
        "DigitalBrain-Backups",
        "jakeguo117/obsidian-digitalbrain",
        "14",
        "Operation not permitted",
    ):
        assert needle in text


def test_parse_mount_table() -> None:
    mac = db.parse_mount_table("/dev/disk1s1 on /Volumes/Disk (apfs, local, journaled)\n")
    assert "/Volumes/Disk" in mac
    proc = db.parse_mount_table("/dev/disk3s1 /tmp/foo\\040bar apfs rw\n")
    assert "/tmp/foo bar" in proc


def test_unmounted_volumes_path_refused_even_if_proofs_poisoned() -> None:
    verdict = db.evaluate_mount_point(
        Path("/Volumes/Disk"),
        is_mount=False,
        diskutil_mounted=True,
        mount_points={"/Volumes/Disk"},
    )
    assert verdict.ok is False
    assert "unmounted /Volumes" in verdict.reason


def test_diskutil_false_vetoes_mount_table() -> None:
    verdict = db.evaluate_mount_point(
        Path("/tmp/vol"),
        is_mount=False,
        diskutil_mounted=False,
        mount_points={"/tmp/vol"},
    )
    assert verdict.ok is False
    assert "diskutil" in verdict.reason


def test_unmounted_volume_is_not_written(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    world = make_world(tmp_path, monkeypatch, mounted=False, create_root=False, with_git=False)
    rc = db.cmd_backup(world.cfg)
    assert rc == 1
    assert list(world.vol.iterdir()) == [world.vol / "do-not-touch.txt"]
    assert not (world.vol / "DigitalBrain-Backups").exists()
    assert not (world.vol / "status.json").exists()
    assert "backup target unavailable" in world.home_log.read_text()
    lines = hermes_lines(world.hermes_log)
    assert len(lines) == 1
    assert "send" in lines[0] and "discord:" in lines[0]


def test_home_log_inside_unmounted_volume_is_not_created(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    world = make_world(tmp_path, monkeypatch, mounted=False, create_root=False, with_git=False)
    inside = world.vol / "Library" / "Logs" / "digitalbrain-backup.log"
    data = json.loads(world.cfg_path.read_text())
    data["home_log"] = str(inside)
    world.cfg_path.write_text(json.dumps(data))
    cfg = db.load_config(world.cfg_path)
    rc = db.cmd_backup(cfg)
    assert rc == 1
    assert not (world.vol / "Library").exists()
    assert not inside.exists()
    assert list(world.vol.iterdir()) == [world.vol / "do-not-touch.txt"]
    assert len(hermes_lines(world.hermes_log)) == 1


def test_safe_remove_guards(tmp_path: Path) -> None:
    root = tmp_path / "DigitalBrain-Backups"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("safe")
    link = root / "link"
    link.symlink_to(outside)
    with pytest.raises(db.GuardError):
        db.safe_remove(root, link)
    assert outside.read_text() == "safe"
    assert link.is_symlink()
    evil = tmp_path / "DigitalBrain-Backups-evil"
    evil.mkdir()
    (evil / "x").write_text("no")
    with pytest.raises(db.GuardError):
        db.safe_remove(root, evil / "x")
    assert (evil / "x").read_text() == "no"
    with pytest.raises(db.GuardError):
        db.safe_remove(root, root)
    with pytest.raises(db.GuardError):
        db.safe_remove(root, root / ".." / "outside.txt")
    assert outside.read_text() == "safe"


def test_git_refuses_vault_and_writes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    backup = tmp_path / "backup"
    vault.mkdir()
    backup.mkdir()
    git = db.Git(vault, backup, db.Logger(None))
    with pytest.raises(db.GuardError):
        git.run(["git", "commit", "-m", "x"], cwd=backup)
    with pytest.raises(db.GuardError):
        git.run(["git", "-C", str(vault), "rev-parse", "HEAD"], cwd=backup)
    with pytest.raises(db.GuardError):
        git.run(["git", "rev-parse", "HEAD"], cwd=vault)
    with pytest.raises(db.GuardError):
        git.clone_mirror("https://example.invalid/repo.git", vault / "mirror.git")


def test_worker_does_not_open_git_fifo(tmp_path: Path) -> None:
    fifo = tmp_path / ".git"
    os.mkfifo(fifo)
    payload = "\n".join(
        [
            json.dumps({"op": "LIST", "path": str(fifo)}),
            json.dumps({"op": "STAT", "path": str(fifo)}),
            json.dumps({"op": "COPY", "src": str(fifo), "dst": str(tmp_path / "out")}),
            "EXIT",
        ]
    ) + "\n"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "digitalbrain_backup.py"), "--vault-worker"],
        input=payload,
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    lines = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    assert len(lines) == 3
    for item in lines:
        assert item["ok"] is False
        assert "git" in item["error"]


def test_ls_dataless_parser() -> None:
    assert db.ls_output_has_dataless("-rw-r--r-- 1 user staff dataless 0 file")
    assert not db.ls_output_has_dataless("-rw-r--r-- 1 user staff hidden 0 file")

    class Info:
        st_flags = 0x40000000

    assert db.flags_dataless(Info()) is True


def test_labels(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DIGITALBRAIN_BACKUP_NOW", NOW_SUNDAY)
    labels = db.snapshot_labels()
    assert labels == {
        "daily": "2023-01-01",
        "weekly": "2022-W52",
        "monthly": "2023-01",
        "sunday": True,
        "month_start": True,
    }
    monkeypatch.setenv("DIGITALBRAIN_BACKUP_NOW", NOW_TUESDAY)
    labels = db.snapshot_labels()
    assert labels["daily"] == "2026-10-13"
    assert labels["sunday"] is False
    assert labels["month_start"] is False


def _chmod_vault_readonly(vault: Path) -> tuple[list[Path], list[Path]]:
    files: list[Path] = []
    dirs: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(vault):
        current = Path(dirpath)
        dirs.append(current)
        for name in filenames:
            path = current / name
            if path.is_symlink() or stat.S_ISFIFO(path.lstat().st_mode):
                continue
            path.chmod(0o444)
            files.append(path)
    for path in dirs:
        path.chmod(0o555)
    return files, dirs


def _restore_vault_modes(vault: Path) -> None:
    for dirpath, dirnames, filenames in os.walk(vault):
        os.chmod(dirpath, 0o755)
        for name in filenames:
            path = Path(dirpath) / name
            if path.is_symlink() or stat.S_ISFIFO(path.lstat().st_mode):
                continue
            path.chmod(0o644)
    vault.chmod(0o755)


def test_success_backup_prunes_and_restore(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    world = make_world(
        tmp_path,
        monkeypatch,
        timeout=5,
        vault_files={"notes/hello.md": "hello\n", "notes/nested/b.md": "bee\n"},
    )
    os.mkfifo(world.vault / ".git")
    files, _dirs = _chmod_vault_readonly(world.vault)
    before = []
    for path in [world.vault, *files]:
        info = path.lstat()
        before.append((path, info.st_mtime_ns, stat.S_IMODE(info.st_mode), path.read_bytes() if path.is_file() else None))
    try:
        for day in range(1, 17):
            folder = world.backup / "vault" / "daily" / f"2000-01-{day:02d}"
            folder.mkdir(parents=True)
            (folder / "keep.txt").write_text(f"keep-{day:02d}")
        outside_dir = world.work / "outside-snap"
        outside_dir.mkdir()
        (outside_dir / "secret.txt").write_text("secret-data")
        os.symlink(outside_dir, world.backup / "vault" / "daily" / "1999-01-01")
        secret_file = world.work / "secret-file"
        secret_file.write_text("secret-bundle")
        (world.backup / "git" / "daily").mkdir(parents=True)
        os.symlink(secret_file, world.backup / "git" / "daily" / "1998-01-01.bundle")
        sibling = world.vol / "DigitalBrain-Backups-evil"
        sibling.mkdir()
        (sibling / "stay.txt").write_text("stay")

        rc = db.cmd_backup(world.cfg)
        captured = capsys.readouterr()
        assert rc == 0, captured.err
        assert "--- git fsck ---" not in captured.out
        status = read_status(world.backup)
        assert status["result"] == "ok"
        assert status["errors"] == []
        assert status["alert_sent"] is False
        assert status["prune"]["ran"] is True
        assert status["sizes"]["vault_file_count"] == 2
        assert hermes_lines(world.hermes_log) == []
        for path, mtime_ns, mode, content in before:
            info = path.lstat()
            assert info.st_mtime_ns == mtime_ns
            assert stat.S_IMODE(info.st_mode) == mode
            if content is not None:
                assert path.read_bytes() == content
        assert stat.S_ISFIFO((world.vault / ".git").lstat().st_mode)
        log = (world.backup / "digitalbrain-backup.log").read_text()
        home = world.home_log.read_text()
        assert "backup start" in log and "backup start" in home
        assert "git-fsck rc=0" in log
        assert "git-bundle-verify rc=0" in log
        assert "backup result=ok" in log
        assert "vault-skip-git .git" in log
        for line in log.splitlines():
            if "vault-op " in line:
                assert "/.git" not in line
            if "git-cmd " in line:
                assert str(world.vault) not in line
                sub = line.split("sub=", 1)[1].split()[0]
                assert sub in db.ALLOWED_GIT
        mirror = world.backup / "git" / "mirror.git"
        assert mirror.is_dir()
        assert "Mobile Documents" not in mirror.parts
        proc = subprocess.run(
            ["git", "-c", "safe.directory=*", "-C", str(mirror), "fsck", "--full"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        bundle = world.backup / "git" / "daily" / "2026-10-13.bundle"
        proc = subprocess.run(
            ["git", "-c", "safe.directory=*", "-C", str(mirror), "bundle", "verify", str(bundle)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        head = subprocess.check_output(["git", "-C", str(mirror), "rev-parse", "refs/heads/main"], text=True).strip()
        remote = subprocess.check_output(["git", "ls-remote", str(world.bare), "refs/heads/main"], text=True).split()[0]
        assert status["head_sha"] == status["github_head_sha"] == head == remote
        manifest = json.loads((world.backup / "vault" / "daily" / "2026-10-13.manifest.json").read_text())
        assert manifest["file_count"] == 2
        copied = world.backup / "vault" / "daily" / "2026-10-13"
        for item in manifest["files"]:
            data = (world.vault / item["path"]).read_bytes()
            assert hashlib.sha256(data).hexdigest() == item["sha256"]
            assert db.sha256_file(copied / item["path"]) == item["sha256"]
        assert (world.backup / "vault" / "daily" / "1999-01-01").is_symlink()
        assert (outside_dir / "secret.txt").read_text() == "secret-data"
        assert secret_file.read_text() == "secret-bundle"
        assert (world.backup / "git" / "daily" / "1998-01-01.bundle").is_symlink()
        for gone in ("2000-01-01", "2000-01-02", "2000-01-03"):
            assert not (world.backup / "vault" / "daily" / gone).exists()
        assert (world.backup / "vault" / "daily" / "2000-01-04" / "keep.txt").read_text() == "keep-04"
        assert (sibling / "stay.txt").read_text() == "stay"
        assert not (world.backup / "vault" / "weekly").exists()

        status_bytes = (world.backup / "status.json").read_bytes()
        rc = db.cmd_restore_test(world.cfg)
        restored = capsys.readouterr().out
        assert rc == 0
        assert status_bytes == (world.backup / "status.json").read_bytes()
        assert "--- git fsck ---" in restored
        assert "rc=0" in restored
        assert "manifest ok" in restored
        assert status["head_sha"] in restored

        (world.src / "hello.txt").write_text("v2\n")
        subprocess.check_call(["git", "-C", str(world.src), "add", "hello.txt"])
        subprocess.check_call(["git", "-C", str(world.src), "commit", "-m", "two"])
        subprocess.check_call(["git", "-C", str(world.src), "push", str(world.bare), "HEAD:refs/heads/main"])
        rc = db.cmd_backup(world.cfg)
        assert rc == 0
        second = read_status(world.backup)
        assert second["result"] == "ok"
        assert second["head_sha"] != status["head_sha"]
        remote = subprocess.check_output(["git", "ls-remote", str(world.bare), "refs/heads/main"], text=True).split()[0]
        assert second["head_sha"] == remote
        assert (world.backup / "vault" / "daily" / "2000-01-04" / "keep.txt").read_text() == "keep-04"
        assert hermes_lines(world.hermes_log) == []
    finally:
        _restore_vault_modes(world.vault)


def test_placeholder_fails_without_prune(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    world = make_world(tmp_path, monkeypatch)
    stub = world.vault / "notes" / "stub.md.icloud"
    stub.write_text("stub")
    preseed_old(world.backup)
    rc = db.cmd_backup(world.cfg)
    status = read_status(world.backup)
    assert_old_kept(world, rc, status)
    assert any("placeholder" in item or "stub.md.icloud" in item for item in status["errors"])
    assert stub.read_text() == "stub"
    assert not (world.backup / "vault" / "daily" / "2026-10-13.manifest.json").exists()


def test_unreadable_vault_fails_without_prune(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    world = make_world(tmp_path, monkeypatch)
    preseed_old(world.backup)
    os.chmod(world.vault, 0)
    try:
        rc = db.cmd_backup(world.cfg)
        status = read_status(world.backup)
        assert_old_kept(world, rc, status)
        assert any("Permission" in item for item in status["errors"])
    finally:
        os.chmod(world.vault, 0o755)


def test_timeout_fails_without_prune(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    world = make_world(tmp_path, monkeypatch, timeout=1)
    os.mkfifo(world.vault / "hang.fifo")
    preseed_old(world.backup)
    proc = subprocess.run(
        [sys.executable, str(ROOT / "digitalbrain_backup.py"), "--config", str(world.cfg_path), "backup"],
        timeout=20,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "DIGITALBRAIN_BACKUP_NOW": NOW_TUESDAY, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert proc.returncode != 0, proc.stdout + proc.stderr
    status = read_status(world.backup)
    assert_old_kept(world, proc.returncode, status)
    assert any("timed out" in item for item in status["errors"])


def test_dataless_fails_without_opening(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    world = make_world(tmp_path, monkeypatch, timeout=5, dataless=True)
    os.mkfifo(world.vault / "hang.fifo")
    preseed_old(world.backup)
    import time

    started = time.monotonic()
    rc = db.cmd_backup(world.cfg)
    elapsed = time.monotonic() - started
    status = read_status(world.backup)
    assert_old_kept(world, rc, status)
    assert elapsed < 15
    assert any("dataless" in item or "placeholder" in item for item in status["errors"])
    assert not any("timed out" in item for item in status["errors"])


def test_head_mismatch_does_not_publish(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    world = make_world(tmp_path, monkeypatch)
    preseed_old(world.backup)
    real = shutil.which("git")
    assert real
    bindir = world.work / "bin"
    bindir.mkdir()
    script = """#!/bin/bash
for arg in "$@"; do
  if [[ "$arg" == "ls-remote" ]]; then
    printf 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\\trefs/heads/main\\n'
    exit 0
  fi
done
exec __GIT__ "$@"
"""
    write_exec(bindir / "git", script.replace("__GIT__", real))
    monkeypatch.setenv("PATH", str(bindir) + os.pathsep + os.environ["PATH"])
    rc = db.cmd_backup(world.cfg)
    status = read_status(world.backup)
    assert_old_kept(world, rc, status)
    assert any("does not match" in item for item in status["errors"])


def test_manifest_mismatch_does_not_prune(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    world = make_world(tmp_path, monkeypatch)
    preseed_old(world.backup)
    original = db.sha256_file

    def fake(path: Path) -> str:
        if path.name == "hello.md":
            return "0" * 64
        return original(path)

    monkeypatch.setattr(db, "sha256_file", fake)
    rc = db.cmd_backup(world.cfg)
    status = read_status(world.backup)
    assert_old_kept(world, rc, status)
    assert any("manifest" in item or "sha256" in item for item in status["errors"])


def test_bundle_verify_failure_does_not_prune(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    world = make_world(tmp_path, monkeypatch)
    preseed_old(world.backup)
    real = db.Git.bundle_create

    def wrapped(self: db.Git, mirror: Path, bundle: Path):
        proc = real(self, mirror, bundle)
        bundle.write_bytes(b"not-a-bundle")
        return proc

    monkeypatch.setattr(db.Git, "bundle_create", wrapped)
    rc = db.cmd_backup(world.cfg)
    status = read_status(world.backup)
    assert_old_kept(world, rc, status)
    assert any("bundle" in item for item in status["errors"])


def test_sunday_publish_and_restore_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    world = make_world(tmp_path, monkeypatch, now=NOW_SUNDAY)
    rc = db.cmd_backup(world.cfg)
    out = capsys.readouterr().out
    assert rc == 0
    status = read_status(world.backup)
    assert status["result"] == "ok"
    assert (world.backup / "vault" / "daily" / "2023-01-01").is_dir()
    assert (world.backup / "vault" / "weekly" / "2022-W52").is_dir()
    assert (world.backup / "vault" / "monthly" / "2023-01").is_dir()
    assert (world.backup / "git" / "weekly" / "2022-W52.bundle").is_file()
    assert (world.backup / "git" / "monthly" / "2023-01.bundle").is_file()
    assert "--- git fsck ---" in out
    assert "manifest ok" in out
    assert status["head_sha"] in out


def test_sunday_restore_failure_does_not_prune(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    world = make_world(tmp_path, monkeypatch, now=NOW_SUNDAY)
    for day in range(1, 17):
        folder = world.backup / "vault" / "daily" / f"2000-01-{day:02d}"
        folder.mkdir(parents=True)
        (folder / "keep.txt").write_text(f"2000-01-{day:02d}")

    def fake(_cfg: db.Config, _logger: db.Logger, expected_sha: str | None = None) -> db.RestoreReport:
        return db.RestoreReport(False, "bad", ["fsck failed"])

    monkeypatch.setattr(db, "run_restore", fake)
    rc = db.cmd_backup(world.cfg)
    status = read_status(world.backup)
    assert rc == 1
    assert status["result"] == "failed"
    assert status["prune"]["ran"] is False
    assert any("fsck failed" in item for item in status["errors"])
    assert len(hermes_lines(world.hermes_log)) == 1
    for day in range(1, 17):
        path = world.backup / "vault" / "daily" / f"2000-01-{day:02d}" / "keep.txt"
        assert path.read_text() == f"2000-01-{day:02d}"


def test_install_and_uninstall(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    world = make_world(tmp_path, monkeypatch, with_git=False)
    home = tmp_path / "home"
    agents = tmp_path / "agents"
    template = (ROOT / "launchd" / "com.jake.digitalbrain-backup.plist").read_text()
    rc = db.cmd_install(world.cfg_path, home, agents)
    assert rc == 0
    dedicated = home / "Library" / "Application Support" / "digitalbrain-backup" / "python3-digitalbrain-backup"
    assert dedicated.is_file()
    assert os.access(dedicated, os.X_OK)
    rendered_path = agents / "com.jake.digitalbrain-backup.plist"
    rendered = rendered_path.read_text()
    assert "__DEDICATED_PYTHON__" not in rendered
    assert "__HOME__" not in rendered
    plist = plistlib.loads(rendered.encode())
    assert plist["ProgramArguments"][0] == str(dedicated)
    assert template == (ROOT / "launchd" / "com.jake.digitalbrain-backup.plist").read_text()
    marker = (world.backup / ".backup-target").read_text().splitlines()[0]
    assert marker == "digitalbrain-backup-target"
    sentinel = world.backup / "sentinel.txt"
    sentinel.write_text("stay")
    assert db.cmd_uninstall(agents) == 0
    assert not rendered_path.exists()
    assert sentinel.read_text() == "stay"
    assert (world.backup / ".backup-target").is_file()
    assert dedicated.is_file()


def test_install_unmounted_writes_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    world = make_world(tmp_path, monkeypatch, mounted=False, create_root=False, with_git=False)
    rc = db.cmd_install(world.cfg_path, tmp_path / "home", tmp_path / "agents")
    assert rc == 1
    assert list(world.vol.iterdir()) == [world.vol / "do-not-touch.txt"]
    assert len(hermes_lines(world.hermes_log)) == 1


def test_config_rejects_dotdot(tmp_path: Path) -> None:
    base = json.loads((ROOT / "config.example.json").read_text())
    base["home_log"] = str(tmp_path / "home.log")
    base["volume"] = "/tmp/foo/../../etc"
    path = tmp_path / "config.json"
    path.write_text(json.dumps(base))
    with pytest.raises(db.ConfigError):
        db.load_config(path)
    base["volume"] = str(tmp_path / "vol")
    base["backup_folder"] = "../etc"
    path.write_text(json.dumps(base))
    with pytest.raises(db.ConfigError):
        db.load_config(path)
