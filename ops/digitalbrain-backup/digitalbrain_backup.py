#!/usr/bin/env python3
"""Nightly DigitalBrain backup onto an external disk.

The GitHub repository is cloned and fetched into a mirror on the backup
volume. Nothing in this program runs git against the iCloud vault, and the
vault's ``.git`` entry is never stated or read (it may be an undownloaded
gitdir pointer that hangs on read).

Vault names come from ``listdir``. File bytes are read only in a child
process. If that child does not answer within the configured timeout it is
killed. An unreadable vault, an iCloud placeholder, a dataless file, or a
timed-out read fails the run. Failure writes ``status.json`` and alerts.
It does not publish a new daily/weekly/monthly snapshot and does not delete
older ones.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import select
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

SHANGHAI = timezone(timedelta(hours=8))
SF_DATALESS = 0x40000000
MARKER_NAME = ".backup-target"
MARKER_TOKEN = "digitalbrain-backup-target"
PLIST_NAME = "com.jake.digitalbrain-backup.plist"
DEDICATED_NAME = "python3-digitalbrain-backup"
PACKAGE_ROOT = Path(__file__).resolve().parent
GIT_TIMEOUT = int(os.environ.get("DIGITALBRAIN_BACKUP_GIT_TIMEOUT", "3600"))
HERMES_TIMEOUT = 30
DISKUTIL_TIMEOUT = 30
ALLOWED_GIT = {"clone", "fetch", "fsck", "bundle", "ls-remote", "rev-parse"}
VOLUMES = Path("/Volumes")

DAILY_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}$")
WEEKLY_NAME = re.compile(r"^\d{4}-W\d{2}$")
MONTHLY_NAME = re.compile(r"^\d{4}-\d{2}$")
DAILY_BUNDLE = re.compile(r"^\d{4}-\d{2}-\d{2}\.bundle$")
WEEKLY_BUNDLE = re.compile(r"^\d{4}-W\d{2}\.bundle$")
MONTHLY_BUNDLE = re.compile(r"^\d{4}-\d{2}\.bundle$")
DAILY_MANIFEST = re.compile(r"^(\d{4}-\d{2}-\d{2})\.manifest\.json$")
WEEKLY_MANIFEST = re.compile(r"^(\d{4}-W\d{2})\.manifest\.json$")
MONTHLY_MANIFEST = re.compile(r"^(\d{4}-\d{2})\.manifest\.json$")


class BackupError(Exception):
    pass


class GuardError(BackupError):
    pass


class ConfigError(BackupError):
    pass


class VaultProblem(BackupError):
    def __init__(
        self,
        message: str,
        *,
        kind: str = "vault",
        placeholders: list | None = None,
        skipped_git: list | None = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.placeholders = placeholders or []
        self.skipped_git = skipped_git or []


class ReadTimeout(VaultProblem):
    def __init__(self, path: str) -> None:
        super().__init__(f"vault read timed out: {path}", kind="timeout")
        self.path = path


@dataclass
class Config:
    volume: Path
    backup_folder: str
    github_repo: str
    github_remote: str
    git_branch: str
    vault_path: Path
    retention_daily: int
    retention_weekly: int
    retention_monthly: int
    discord_channel_id: str
    hermes_command: list[str]
    disk_log_name: str
    home_log: Path
    read_timeout_seconds: float
    mount_table: Path | None
    diskutil_bin: Path | None
    stat_bin: Path | None
    ls_bin: Path | None
    config_path: Path

    @property
    def backup_root(self) -> Path:
        return self.volume / self.backup_folder


@dataclass
class GitSync:
    head_sha: str | None = None
    github_head_sha: str | None = None
    bundle_bytes: int = 0
    fsck_output: str = ""
    verify_output: str = ""


@dataclass
class Scan:
    files: list[str]
    fingerprint: tuple
    symlinks: list[str]
    skipped_git: list[str]
    placeholders: list[dict]


@dataclass
class MountVerdict:
    ok: bool
    reason: str


@dataclass
class RestoreReport:
    ok: bool
    output: str
    errors: list[str] = field(default_factory=list)


def shanghai_now() -> datetime:
    raw = os.environ.get("DIGITALBRAIN_BACKUP_NOW")
    if raw:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=SHANGHAI)
        return parsed.astimezone(SHANGHAI)
    return datetime.now(SHANGHAI)


def snapshot_labels(now: datetime | None = None) -> dict:
    current = now or shanghai_now()
    iso = current.isocalendar()
    return {
        "daily": current.strftime("%Y-%m-%d"),
        "weekly": f"{iso.year}-W{iso.week:02d}",
        "monthly": current.strftime("%Y-%m"),
        "sunday": current.weekday() == 6,
        "month_start": current.day == 1,
    }


def is_within(child: Path, parent: Path) -> bool:
    child_r = child.expanduser().resolve(strict=False)
    parent_r = parent.expanduser().resolve(strict=False)
    return child_r == parent_r or parent_r in child_r.parents


def path_is_icloud(path: Path) -> bool:
    return "Mobile Documents" in path.parts


def require_inside(root: Path, path: Path) -> None:
    if ".." in path.parts or ".." in root.parts:
        raise GuardError("refusing path with ..")
    try:
        relative = path.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError as exc:
        raise GuardError("path is outside backup root") from exc
    if ".." in relative.parts:
        raise GuardError("refusing path with ..")


def require_abs(value: object, key: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{key} must be a path")
    path = Path(value).expanduser()
    if ".." in path.parts:
        raise ConfigError(f"{key} must not contain ..")
    if not path.is_absolute():
        raise ConfigError(f"{key} must be absolute")
    return path


def optional_abs(data: dict, key: str) -> Path | None:
    if key not in data or data[key] in (None, ""):
        return None
    return require_abs(data[key], key)


def positive_int(value: object, key: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ConfigError(f"{key} must be a positive integer")
    return value


def load_config(path: Path) -> Config:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot read config: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("config must be a JSON object")
    timezone_name = data.get("timezone", "Asia/Shanghai")
    if timezone_name != "Asia/Shanghai":
        raise ConfigError("timezone must be Asia/Shanghai")
    folder = data.get("backup_folder")
    if not isinstance(folder, str) or not folder or folder.startswith("/") or ".." in Path(folder).parts:
        raise ConfigError("backup_folder must be a relative path under the volume")
    retention = data.get("retention") or {}
    if not isinstance(retention, dict):
        raise ConfigError("retention must be an object")
    command = data.get("hermes_command")
    if not isinstance(command, list) or not command or not all(isinstance(part, str) and part for part in command):
        raise ConfigError("hermes_command must be a list of strings")
    joined = " ".join(command)
    if "hermes" not in joined or "send" not in joined:
        raise ConfigError("hermes_command must invoke hermes send")
    if "{channel_id}" not in joined or "{message}" not in joined:
        raise ConfigError("hermes_command must include {channel_id} and {message}")
    branch = data.get("git_branch")
    if not isinstance(branch, str) or not re.fullmatch(r"[A-Za-z0-9._/-]+", branch):
        raise ConfigError("git_branch is not a plain ref name")
    if branch.startswith("/") or ".." in branch.split("/"):
        raise ConfigError("git_branch is not a plain ref name")
    timeout = data.get("read_timeout_seconds", 120)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ConfigError("read_timeout_seconds must be a positive number")
    remote = data.get("github_remote")
    repo = data.get("github_repo")
    if not isinstance(remote, str) or not remote:
        raise ConfigError("github_remote is required")
    if not isinstance(repo, str) or not repo:
        raise ConfigError("github_repo is required")
    channel = data.get("discord_channel_id")
    if not isinstance(channel, str):
        raise ConfigError("discord_channel_id is required")
    return Config(
        volume=require_abs(data.get("volume"), "volume"),
        backup_folder=folder,
        github_repo=repo,
        github_remote=remote,
        git_branch=branch,
        vault_path=require_abs(data.get("vault_path"), "vault_path"),
        retention_daily=positive_int(retention.get("daily"), "retention.daily"),
        retention_weekly=positive_int(retention.get("weekly"), "retention.weekly"),
        retention_monthly=positive_int(retention.get("monthly"), "retention.monthly"),
        discord_channel_id=channel,
        hermes_command=list(command),
        disk_log_name=str(data.get("disk_log_name") or "digitalbrain-backup.log"),
        home_log=require_abs(data.get("home_log"), "home_log"),
        read_timeout_seconds=float(timeout),
        mount_table=optional_abs(data, "mount_table"),
        diskutil_bin=optional_abs(data, "diskutil_bin"),
        stat_bin=optional_abs(data, "stat_bin"),
        ls_bin=optional_abs(data, "ls_bin"),
        config_path=path,
    )


class Logger:
    def __init__(
        self,
        home_log: Path | None,
        disk_log: Path | None = None,
        *,
        blocked_roots: list[Path] | None = None,
    ) -> None:
        self.home_log = home_log
        self.disk_log = disk_log
        self.blocked_roots = blocked_roots or []

    def write(self, message: str) -> None:
        line = f"{shanghai_now().isoformat()} {message}\n"
        for path in (self.home_log, self.disk_log):
            if path is None or self._blocked(path) or path.is_symlink():
                if path is not None and path.is_symlink():
                    print(f"refusing symlink log {path}", file=sys.stderr)
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(line)

    def _blocked(self, path: Path) -> bool:
        for root in self.blocked_roots:
            try:
                if path.resolve(strict=False) == root.resolve(strict=False) or is_within(path, root):
                    return True
            except OSError:
                return True
        return False


def render_template(part: str, channel_id: str, subject: str, message: str) -> str:
    return (
        part.replace("{channel_id}", channel_id)
        .replace("{subject}", subject)
        .replace("{message}", message)
    )


def send_alert(cfg: Config, status: dict, logger: Logger) -> None:
    channel = cfg.discord_channel_id
    if not channel.strip() or "REPLACE_" in channel:
        status["alert_sent"] = False
        logger.write("alert skipped: discord_channel_id not set")
        return
    subject = f"digitalbrain-backup {status['result']}"
    errs = "; ".join(str(item) for item in status.get("errors") or [])[:1500]
    message = (
        f"result={status['result']} time={status['time']} "
        f"head={status.get('head_sha')} errors={errs or 'none'}"
    )[:1800]
    argv = [render_template(part, channel, subject, message) for part in cfg.hermes_command]
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            check=False,
            timeout=HERMES_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        status["errors"].append("hermes alert failed: timed out")
        status["alert_sent"] = False
        logger.write("alert sent=False timed out")
        return
    except OSError as exc:
        status["errors"].append(f"hermes alert failed: {exc}")
        status["alert_sent"] = False
        logger.write(f"alert sent=False {exc}")
        return
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        status["errors"].append(f"hermes alert failed: {detail}")
        status["alert_sent"] = False
    else:
        status["alert_sent"] = True
    logger.write(f"alert sent={status['alert_sent']}")


def failure_status(
    errors: list[str],
    *,
    head: str | None = None,
    github: str | None = None,
    placeholders: list | None = None,
    skipped_git: list | None = None,
) -> dict:
    return {
        "alert_sent": False,
        "errors": list(errors),
        "github_head_sha": github,
        "head_sha": head,
        "placeholders": placeholders or [],
        "prune": {
            "deleted": [],
            "ran": False,
            "reason": "backup did not succeed",
            "skipped": [],
        },
        "result": "failed",
        "sizes": {"git_bundle_bytes": 0, "vault_bytes": 0, "vault_file_count": 0},
        "skipped_git": skipped_git or [],
        "time": shanghai_now().isoformat(),
        "timezone": "Asia/Shanghai",
    }


def write_status(cfg: Config, status: dict) -> None:
    path = cfg.backup_root / "status.json"
    require_inside(cfg.backup_root, path)
    if path.is_symlink():
        raise GuardError("refusing symlink status.json")
    temporary = path.with_name("status.json.tmp")
    require_inside(cfg.backup_root, temporary)
    temporary.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def ls_output_has_dataless(text: str) -> bool:
    return bool(re.search(r"(^|\s)dataless(\s|,|$)", text or ""))


def parse_diskutil_mounted(stdout: str, volume: Path) -> bool:
    # diskutil info indents every field ("   Mounted:                   Yes").
    # Mounted only when both the Yes line and a matching Mount Point are present.
    mounted = re.search(r"^\s*Mounted:\s*(Yes|No)\b", stdout, re.IGNORECASE | re.MULTILINE)
    if not mounted or mounted.group(1).lower() != "yes":
        return False
    if re.search(r"not mounted", stdout, re.IGNORECASE):
        return False
    match = re.search(r"^\s*Mount Point:\s*(.+)$", stdout, re.MULTILINE)
    if not match:
        return False
    point = match.group(1).strip()
    if point in {"", "Not applicable"}:
        return False
    return Path(point) == volume


def parse_mount_table(text: str) -> set[str]:
    points: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if " on " in line and "(" in line:
            match = re.search(r" on (.+) \(", line)
            if match:
                points.add(match.group(1).strip())
                continue
        parts = [unescape_mount(part) for part in line.split()]
        if len(parts) >= 2 and parts[1].startswith("/"):
            points.add(parts[1])
        elif len(parts) == 1 and parts[0].startswith("/"):
            points.add(parts[0])
    return points


def unescape_mount(value: str) -> str:
    return re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), value)


def system_mount_text() -> str:
    proc_mounts = Path("/proc/mounts")
    if proc_mounts.is_file():
        return proc_mounts.read_text(encoding="utf-8", errors="replace")
    result = subprocess.run(["mount"], capture_output=True, text=True, check=False)
    return result.stdout or ""


def load_mount_points(cfg: Config) -> set[str]:
    if cfg.mount_table is not None:
        if not cfg.mount_table.is_file():
            return set()
        return parse_mount_table(cfg.mount_table.read_text(encoding="utf-8", errors="replace"))
    return parse_mount_table(system_mount_text())


def find_system_diskutil() -> Path | None:
    for candidate in (Path("/usr/sbin/diskutil"), Path("/usr/bin/diskutil")):
        if candidate.is_file():
            return candidate
    found = shutil.which("diskutil")
    return Path(found) if found else None


def probe_diskutil(configured: Path | None, volume: Path) -> bool | None:
    if configured is not None:
        binary = configured
        if not binary.is_file():
            return False
    else:
        binary = find_system_diskutil()
        if binary is None:
            return None
    try:
        proc = subprocess.run(
            [str(binary), "info", str(volume)],
            capture_output=True,
            text=True,
            check=False,
            timeout=DISKUTIL_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return False
    if proc.returncode != 0:
        return False
    return parse_diskutil_mounted(proc.stdout + "\n" + proc.stderr, volume)


def evaluate_mount_point(
    volume: Path,
    *,
    is_mount: bool,
    diskutil_mounted: bool | None,
    mount_points: set[str],
) -> MountVerdict:
    if ".." in volume.parts:
        return MountVerdict(False, "volume path contains ..")
    if volume.parent == VOLUMES and not is_mount:
        return MountVerdict(False, "refusing to write into an unmounted /Volumes path")
    normalized = {point.rstrip("/") if point != "/" else point for point in mount_points}
    vol = str(volume)
    if vol != "/" and vol.endswith("/"):
        vol = vol.rstrip("/")
    in_table = vol in normalized
    if diskutil_mounted is False:
        return MountVerdict(False, "diskutil reports volume is not mounted")
    if diskutil_mounted is not True and not in_table:
        return MountVerdict(False, "volume is not a proven mount point")
    return MountVerdict(True, "mounted")


def collect_mount_facts(cfg: Config) -> MountVerdict:
    volume = cfg.volume
    if ".." in volume.parts:
        return MountVerdict(False, "volume path contains ..")
    try:
        if volume.is_symlink():
            return MountVerdict(False, "volume path is a symlink")
        if not volume.exists():
            return MountVerdict(False, "volume path does not exist")
        if not volume.is_dir():
            return MountVerdict(False, "volume path is not a directory")
        is_mount = os.path.ismount(volume)
    except OSError as exc:
        return MountVerdict(False, f"volume path is not readable: {exc}")
    return evaluate_mount_point(
        volume,
        is_mount=is_mount,
        diskutil_mounted=probe_diskutil(cfg.diskutil_bin, volume),
        mount_points=load_mount_points(cfg),
    )


def marker_status(path: Path) -> tuple[bool, str]:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False, "missing"
    except OSError as exc:
        return False, f"unreadable: {exc}"
    if stat.S_ISLNK(info.st_mode):
        return False, "symlink"
    if not stat.S_ISREG(info.st_mode):
        return False, "not a regular file"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return False, f"unreadable: {exc}"
    first = text.splitlines()[0].strip() if text.splitlines() else ""
    if first != MARKER_TOKEN:
        return False, "bad token"
    return True, "ok"


def target_ready(cfg: Config) -> MountVerdict:
    point = collect_mount_facts(cfg)
    if not point.ok:
        return point
    ok, detail = marker_status(cfg.backup_root / MARKER_NAME)
    if not ok:
        return MountVerdict(False, f"backup target marker is missing or invalid: {detail}")
    if cfg.backup_root.is_symlink():
        return MountVerdict(False, "backup root is a symlink")
    return MountVerdict(True, "mounted")


def safe_remove(backup_root: Path, target: Path) -> None:
    if not backup_root.is_absolute() or not target.is_absolute():
        raise GuardError("paths must be absolute")
    if target == backup_root:
        raise GuardError("refusing to delete backup root")
    if ".." in target.parts or ".." in backup_root.parts:
        raise GuardError("refusing path with ..")
    try:
        relative = target.relative_to(backup_root)
    except ValueError as exc:
        raise GuardError("refusing path outside backup root") from exc
    if any(part in {".", ".."} for part in relative.parts):
        raise GuardError("refusing path with ..")
    current = backup_root
    for part in relative.parts:
        current = current / part
        try:
            if current.is_symlink():
                raise GuardError(f"refusing symlink: {current}")
        except OSError as exc:
            raise GuardError(f"refusing unreadable path: {current}: {exc}") from exc
    if not current.exists():
        return
    real_root = os.path.realpath(backup_root)
    real_target = os.path.realpath(current)
    try:
        common = os.path.commonpath([real_root, real_target])
    except ValueError as exc:
        raise GuardError("refusing path outside backup root") from exc
    if common != real_root:
        raise GuardError("refusing path outside backup root")
    if current.is_dir():
        for dirpath, dirnames, filenames in os.walk(current, followlinks=False):
            for name in list(dirnames) + list(filenames):
                candidate = Path(dirpath) / name
                if candidate.is_symlink():
                    raise GuardError(f"refusing tree containing symlink: {candidate}")
        shutil.rmtree(current)
        return
    if current.is_file():
        current.unlink()
        return
    raise GuardError("refusing special file")


def discard_incoming(backup_root: Path) -> None:
    incoming = backup_root / "incoming"
    if incoming.is_symlink():
        raise GuardError("refusing symlink incoming directory")
    if incoming.exists():
        safe_remove(backup_root, incoming)


def remote_path(remote: str) -> Path | None:
    if remote.startswith("file://"):
        parsed = urlparse(remote)
        raw = unquote(parsed.path)
        return Path(raw) if raw.startswith("/") else None
    if "://" in remote:
        return None
    path = Path(remote)
    return path if path.is_absolute() else None


def remote_is_forbidden(remote: str, cfg: Config) -> bool:
    path = remote_path(remote)
    if path is None:
        return False
    if path_is_icloud(path) or is_within(path, cfg.vault_path):
        return True
    return False


def assert_layout(cfg: Config) -> None:
    vault = cfg.vault_path
    if vault.is_symlink():
        raise VaultProblem("refusing symlink vault path", kind="unreadable")
    if not vault.exists() or not vault.is_dir():
        raise VaultProblem(f"vault unreadable: {vault}: not a directory", kind="unreadable")
    if cfg.backup_root.is_symlink():
        raise BackupError("backup root is a symlink")
    if path_is_icloud(cfg.volume) or path_is_icloud(cfg.backup_root):
        raise BackupError("backup volume must be outside iCloud")
    if is_within(cfg.backup_root, vault) or is_within(vault, cfg.backup_root):
        raise BackupError("vault and backup root overlap")
    if remote_is_forbidden(cfg.github_remote, cfg):
        raise BackupError("refusing to read git data from the iCloud vault")


def git_subcommand(args: list[str]) -> str:
    if not args or Path(args[0]).name != "git":
        raise GuardError("not a git command")
    index = 1
    while index < len(args):
        arg = args[index]
        if arg in {"-C", "-c", "--git-dir", "--work-tree"}:
            index += 2
            continue
        if arg.startswith("-"):
            index += 1
            continue
        return arg
    raise GuardError("missing git subcommand")


def git_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def git_fail(action: str, proc: subprocess.CompletedProcess) -> str:
    detail = ((proc.stderr or "") + (proc.stdout or "")).strip()
    if len(detail) > 500:
        detail = detail[:500]
    return f"git {action} failed: {detail or 'no output'}"


def parse_ls_remote(text: str, branch: str) -> str | None:
    want = f"refs/heads/{branch}"
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] == want:
            return parts[0]
    return None


class Git:
    def __init__(self, vault: Path, backup_root: Path, logger: Logger) -> None:
        self.vault = vault
        self.backup_root = backup_root
        self.logger = logger

    def run(
        self,
        args: list[str],
        *,
        cwd: Path,
        write_dest: Path | None = None,
        write_roots: list[Path] | None = None,
    ) -> subprocess.CompletedProcess:
        sub = git_subcommand(args)
        if sub not in ALLOWED_GIT:
            raise GuardError(f"refusing git {sub}")
        if self._in_vault(cwd):
            raise GuardError("refusing to run git inside the vault")
        for arg in args[1:]:
            if arg.startswith("-") or arg.startswith("refs/"):
                continue
            candidate = Path(arg)
            if candidate.is_absolute() and self._in_vault(candidate):
                raise GuardError(f"refusing git path inside vault: {arg}")
        if write_dest is not None:
            if self._in_vault(write_dest):
                raise GuardError("refusing git write inside the vault")
            roots = write_roots if write_roots is not None else [self.backup_root]
            if not any(is_within(write_dest, root) for root in roots):
                raise GuardError("git write destination is outside the allowed root")
        self.logger.write(f"git-cmd sub={sub} cwd={cwd} {shlex.join(args)}")
        try:
            return subprocess.run(
                args,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                check=False,
                timeout=GIT_TIMEOUT,
                env=git_env(),
            )
        except subprocess.TimeoutExpired as exc:
            raise BackupError(f"git {sub} timed out") from exc

    def _in_vault(self, path: Path) -> bool:
        return is_within(path, self.vault)

    def clone_mirror(self, url: str, dest: Path) -> subprocess.CompletedProcess:
        return self.run(
            ["git", "-c", "safe.directory=*", "clone", "--mirror", url, str(dest)],
            cwd=self.backup_root,
            write_dest=dest,
        )

    def fetch(self, mirror: Path) -> subprocess.CompletedProcess:
        return self.run(
            ["git", "-c", "safe.directory=*", "-C", str(mirror), "fetch", "origin"],
            cwd=mirror,
            write_dest=mirror,
        )

    def fsck(self, repo: Path) -> subprocess.CompletedProcess:
        return self.run(
            ["git", "-c", "safe.directory=*", "-C", str(repo), "fsck", "--full"],
            cwd=repo,
        )

    def rev_parse(self, repo: Path, ref: str) -> subprocess.CompletedProcess:
        return self.run(
            ["git", "-c", "safe.directory=*", "-C", str(repo), "rev-parse", ref],
            cwd=repo,
        )

    def ls_remote(self, url: str, branch: str) -> subprocess.CompletedProcess:
        return self.run(
            ["git", "-c", "safe.directory=*", "ls-remote", url, f"refs/heads/{branch}"],
            cwd=self.backup_root,
        )

    def bundle_create(self, mirror: Path, bundle: Path) -> subprocess.CompletedProcess:
        return self.run(
            ["git", "-c", "safe.directory=*", "-C", str(mirror), "bundle", "create", str(bundle), "--all"],
            cwd=mirror,
            write_dest=bundle,
        )

    def bundle_verify(self, repo: Path, bundle: Path) -> subprocess.CompletedProcess:
        return self.run(
            ["git", "-c", "safe.directory=*", "-C", str(repo), "bundle", "verify", str(bundle)],
            cwd=repo,
        )

    def clone_working(self, bundle: Path, dest: Path, write_root: Path) -> subprocess.CompletedProcess:
        return self.run(
            ["git", "-c", "safe.directory=*", "clone", str(bundle), str(dest)],
            cwd=write_root,
            write_dest=dest,
            write_roots=[write_root],
        )


def refuse_git(path: Path) -> dict | None:
    if ".git" in path.parts:
        return {"ok": False, "error": "refusing vault .git"}
    return None


def kind_of(info: os.stat_result) -> str:
    if stat.S_ISLNK(info.st_mode):
        return "symlink"
    if stat.S_ISDIR(info.st_mode):
        return "dir"
    if stat.S_ISREG(info.st_mode):
        return "file"
    return "other"


def flags_dataless(info: os.stat_result) -> bool:
    flags = getattr(info, "st_flags", 0) or 0
    return bool(flags & SF_DATALESS)


def external_dataless(path: Path) -> bool:
    stat_bin = os.environ.get("DIGITALBRAIN_BACKUP_STAT_BIN")
    if stat_bin:
        proc = subprocess.run([stat_bin, "-f", "%Sf", str(path)], capture_output=True, text=True, check=False)
        text = (proc.stdout or "").strip()
        if text.isdigit() and int(text) & SF_DATALESS:
            return True
        if "dataless" in text.lower():
            return True
    elif sys.platform == "darwin":
        proc = subprocess.run(["/usr/bin/stat", "-f", "%Sf", str(path)], capture_output=True, text=True, check=False)
        text = (proc.stdout or "").strip()
        if text.isdigit() and int(text) & SF_DATALESS:
            return True
    ls_bin = os.environ.get("DIGITALBRAIN_BACKUP_LS_BIN")
    if ls_bin:
        proc = subprocess.run([ls_bin, "-lO", str(path)], capture_output=True, text=True, check=False)
        if ls_output_has_dataless((proc.stdout or "") + (proc.stderr or "")):
            return True
    elif sys.platform == "darwin":
        proc = subprocess.run(["/bin/ls", "-lO", str(path)], capture_output=True, text=True, check=False)
        if ls_output_has_dataless((proc.stdout or "") + (proc.stderr or "")):
            return True
    return False


def worker_dispatch(req: dict, vault_root: Path | None = None) -> dict:
    op = req.get("op")
    if op == "LIST":
        path = Path(req["path"])
        refused = refuse_git(path)
        if refused:
            return refused
        try:
            names = os.listdir(path)
        except OSError as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "names": names}
    if op == "STAT":
        path = Path(req["path"])
        refused = refuse_git(path)
        if refused:
            return refused
        try:
            info = os.lstat(path)
        except OSError as exc:
            return {"ok": False, "error": str(exc)}
        dataless = path.name.endswith(".icloud") or flags_dataless(info)
        if not dataless and not stat.S_ISLNK(info.st_mode) and not stat.S_ISDIR(info.st_mode):
            dataless = external_dataless(path)
        return {
            "dataless": dataless,
            "flags": getattr(info, "st_flags", 0) or 0,
            "kind": kind_of(info),
            "mode": info.st_mode,
            "mtime_ns": info.st_mtime_ns,
            "ok": True,
            "size": info.st_size,
        }
    if op == "COPY":
        src = Path(req["src"])
        dst = Path(req["dst"])
        refused = refuse_git(src)
        if refused:
            return refused
        if vault_root is not None and is_within(dst, vault_root):
            return {"ok": False, "error": "refusing to write inside the vault"}
        try:
            info = os.lstat(src)
        except OSError as exc:
            return {"ok": False, "error": str(exc)}
        if stat.S_ISLNK(info.st_mode):
            return {"ok": False, "error": "refusing to copy symlink"}
        if name_dataless(src, info):
            return {"dataless": True, "error": "dataless", "ok": False}
        dst.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_RDONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(src, flags)
        except OSError as exc:
            return {"ok": False, "error": str(exc)}
        try:
            inp = os.fdopen(fd, "rb")
        except Exception:
            os.close(fd)
            raise
        try:
            hasher = hashlib.sha256()
            total = 0
            with inp, dst.open("wb") as out:
                while True:
                    chunk = inp.read(1024 * 1024)
                    if not chunk:
                        break
                    hasher.update(chunk)
                    out.write(chunk)
                    total += len(chunk)
        except OSError as exc:
            return {"ok": False, "error": str(exc)}
        return {"bytes": total, "ok": True, "sha256": hasher.hexdigest()}
    return {"error": f"unknown op {op}", "ok": False}


def name_dataless(path: Path, info: os.stat_result) -> bool:
    if path.name.endswith(".icloud") or flags_dataless(info):
        return True
    if stat.S_ISLNK(info.st_mode) or stat.S_ISDIR(info.st_mode):
        return False
    return external_dataless(path)


def vault_worker_main() -> int:
    raw_root = os.environ.get("DIGITALBRAIN_BACKUP_VAULT", "")
    vault_root = Path(raw_root) if raw_root else None
    for line in sys.stdin:
        text = line.strip()
        if not text:
            continue
        if text == "EXIT":
            break
        try:
            req = json.loads(text)
            resp = worker_dispatch(req, vault_root)
        except Exception as exc:  # worker must answer instead of dying on one file
            resp = {"error": str(exc), "ok": False}
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()
    return 0


class VaultWorker:
    def __init__(self, cfg: Config, logger: Logger) -> None:
        self.timeout = cfg.read_timeout_seconds
        self.logger = logger
        self._buf = b""
        self.err = tempfile.TemporaryFile()
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["DIGITALBRAIN_BACKUP_VAULT"] = str(cfg.vault_path)
        if cfg.stat_bin is not None:
            env["DIGITALBRAIN_BACKUP_STAT_BIN"] = str(cfg.stat_bin)
        if cfg.ls_bin is not None:
            env["DIGITALBRAIN_BACKUP_LS_BIN"] = str(cfg.ls_bin)
        self.proc: subprocess.Popen | None = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--vault-worker"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.err,
            env=env,
        )

    def request(self, payload: dict) -> dict:
        proc = self.proc
        if proc is None or proc.poll() is not None or proc.stdin is None or proc.stdout is None:
            raise VaultProblem("vault reader is not running", kind="unreadable")
        path = str(payload.get("path") or payload.get("src") or "")
        proc.stdin.write((json.dumps(payload) + "\n").encode())
        proc.stdin.flush()
        try:
            raw = self._readline()
        except ReadTimeout:
            raise ReadTimeout(path) from None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise VaultProblem(f"vault reader returned invalid data: {exc}", kind="vault") from exc

    def _readline(self) -> str:
        proc = self.proc
        if proc is None or proc.stdout is None:
            raise VaultProblem("vault reader is not running", kind="unreadable")
        deadline = time.monotonic() + self.timeout
        while b"\n" not in self._buf:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self.kill()
                raise ReadTimeout("")
            ready, _, _ = select.select([proc.stdout], [], [], remaining)
            if not ready:
                self.kill()
                raise ReadTimeout("")
            chunk = os.read(proc.stdout.fileno(), 65536)
            if not chunk:
                self.kill()
                raise VaultProblem("vault reader exited", kind="unreadable")
            self._buf += chunk
        line, self._buf = self._buf.split(b"\n", 1)
        return line.decode(errors="replace")

    def list_dir(self, path: Path) -> list[str]:
        self.logger.write(f"vault-op LIST {path}")
        resp = self.request({"op": "LIST", "path": str(path)})
        if not resp.get("ok"):
            raise VaultProblem(f"vault unreadable: {path}: {resp.get('error')}", kind="unreadable")
        return list(resp.get("names") or [])

    def stat(self, path: Path) -> dict:
        self.logger.write(f"vault-op STAT {path}")
        resp = self.request({"op": "STAT", "path": str(path)})
        if not resp.get("ok"):
            raise VaultProblem(f"vault unreadable: {path}: {resp.get('error')}", kind="unreadable")
        return resp

    def copy(self, src: Path, dst: Path) -> dict:
        self.logger.write(f"vault-op COPY {src}")
        resp = self.request({"op": "COPY", "src": str(src), "dst": str(dst)})
        if not resp.get("ok"):
            if resp.get("dataless"):
                raise VaultProblem(f"dataless file: {src}", kind="placeholder")
            raise VaultProblem(f"vault unreadable: {src}: {resp.get('error')}", kind="unreadable")
        return resp

    def kill(self) -> None:
        proc = self.proc
        if proc is None:
            return
        if proc.poll() is None:
            proc.kill()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        self.proc = None
        self.err.close()

    def close(self) -> None:
        proc = self.proc
        if proc is None:
            return
        try:
            if proc.stdin:
                proc.stdin.close()
        except Exception:
            pass
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.kill()
            return
        self.proc = None
        self.err.close()


def collect_tree(worker: VaultWorker, vault: Path, logger: Logger) -> Scan:
    files: list[str] = []
    fingerprint: list[tuple] = []
    symlinks: list[str] = []
    skipped_git: list[str] = []
    placeholders: list[dict] = []

    def walk(rel: str) -> None:
        current = vault if rel == "" else vault / rel
        for name in sorted(worker.list_dir(current)):
            rel_path = name if rel == "" else f"{rel}/{name}"
            if name == ".git":
                skipped_git.append(rel_path)
                logger.write(f"vault-skip-git {rel_path}")
                continue
            if name.endswith(".icloud"):
                placeholders.append({"path": rel_path, "reason": "icloud-stub"})
                continue
            info = worker.stat(vault / rel_path)
            if info.get("dataless"):
                placeholders.append({"path": rel_path, "reason": "dataless"})
                continue
            kind = info["kind"]
            fingerprint.append((rel_path, kind, info.get("mode"), info.get("mtime_ns"), info.get("size")))
            if kind == "dir":
                walk(rel_path)
            elif kind == "symlink":
                symlinks.append(rel_path)
            else:
                files.append(rel_path)

    walk("")
    return Scan(files, tuple(fingerprint), symlinks, skipped_git, placeholders)


def scan_vault(worker: VaultWorker, vault: Path, logger: Logger) -> Scan:
    scan = collect_tree(worker, vault, logger)
    if scan.placeholders:
        listed = ", ".join(item["path"] for item in scan.placeholders)
        raise VaultProblem(
            f"icloud placeholder or dataless file: {listed}",
            kind="placeholder",
            placeholders=scan.placeholders,
            skipped_git=scan.skipped_git,
        )
    return scan


def walk_regular_files(root: Path) -> list[str]:
    found: list[str] = []
    if not root.exists():
        return found
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        dirnames[:] = [name for name in dirnames if not (current / name).is_symlink()]
        for name in filenames:
            path = current / name
            if path.is_symlink() or not path.is_file():
                continue
            found.append(path.relative_to(root).as_posix())
    return found


def verify_manifest(root: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    files = manifest.get("files") or []
    if len(files) != manifest.get("file_count"):
        errors.append("manifest file_count does not match file list")
    seen: set[str] = set()
    total = 0
    for item in files:
        rel = item["path"]
        relative = Path(rel)
        if relative.is_absolute() or ".." in relative.parts or ".git" in relative.parts:
            errors.append(f"bad manifest path: {rel}")
            continue
        path = root / rel
        if path.is_symlink() or not path.is_file():
            errors.append(f"missing file: {rel}")
            continue
        digest = sha256_file(path)
        if digest != item["sha256"]:
            errors.append(f"sha256 mismatch: {rel}")
        size = path.stat().st_size
        if size != item["bytes"]:
            errors.append(f"size mismatch: {rel}")
        seen.add(rel)
        total += size
    for rel in walk_regular_files(root):
        if rel not in seen:
            errors.append(f"extra file: {rel}")
    if total != manifest.get("total_bytes") and not any(err.startswith("sha256") or err.startswith("size") for err in errors):
        if total != manifest.get("total_bytes"):
            errors.append("total bytes mismatch")
    return errors


def sync_git(cfg: Config, logger: Logger, git_sync: GitSync) -> None:
    git = Git(cfg.vault_path, cfg.backup_root, logger)
    mirror = cfg.backup_root / "git" / "mirror.git"
    require_inside(cfg.backup_root, mirror)
    if path_is_icloud(mirror) or is_within(mirror, cfg.vault_path):
        raise BackupError("git mirror must be outside iCloud and outside the vault")
    mirror.parent.mkdir(parents=True, exist_ok=True)
    if mirror.is_symlink():
        raise BackupError("refusing symlink git mirror")
    if not mirror.exists():
        proc = git.clone_mirror(cfg.github_remote, mirror)
        if proc.returncode != 0:
            if mirror.exists() and not mirror.is_symlink():
                safe_remove(cfg.backup_root, mirror)
            raise BackupError(git_fail("clone", proc))
    else:
        proc = git.fetch(mirror)
        if proc.returncode != 0:
            raise BackupError(git_fail("fetch", proc))
    proc = git.rev_parse(mirror, f"refs/heads/{cfg.git_branch}")
    if proc.returncode != 0:
        raise BackupError(git_fail("rev-parse", proc))
    git_sync.head_sha = proc.stdout.strip()
    proc = git.ls_remote(cfg.github_remote, cfg.git_branch)
    if proc.returncode != 0:
        raise BackupError(git_fail("ls-remote", proc))
    git_sync.github_head_sha = parse_ls_remote(proc.stdout, cfg.git_branch)
    if not git_sync.github_head_sha or git_sync.github_head_sha != git_sync.head_sha:
        raise BackupError(
            f"backed-up HEAD does not match GitHub {cfg.git_branch}: "
            f"mirror={git_sync.head_sha} github={git_sync.github_head_sha}"
        )
    proc = git.fsck(mirror)
    git_sync.fsck_output = (proc.stdout or "") + (proc.stderr or "")
    logger.write(f"git-fsck rc={proc.returncode}\n{git_sync.fsck_output.rstrip()}")
    if proc.returncode != 0:
        raise BackupError(git_fail("fsck", proc))
    incoming = cfg.backup_root / "incoming"
    if incoming.exists() or incoming.is_symlink():
        if incoming.is_symlink():
            raise GuardError("refusing symlink incoming directory")
    else:
        incoming.mkdir()
    bundle = incoming / "repo.bundle"
    proc = git.bundle_create(mirror, bundle)
    if proc.returncode != 0:
        raise BackupError(git_fail("bundle create", proc))
    proc = git.bundle_verify(mirror, bundle)
    git_sync.verify_output = (proc.stdout or "") + (proc.stderr or "")
    logger.write(f"git-bundle-verify rc={proc.returncode}\n{git_sync.verify_output.rstrip()}")
    if proc.returncode != 0:
        raise BackupError(git_fail("bundle verify", proc))
    git_sync.bundle_bytes = bundle.stat().st_size


def copy_vault(cfg: Config, worker: VaultWorker, scan: Scan, logger: Logger) -> dict:
    incoming_vault = cfg.backup_root / "incoming" / "vault"
    require_inside(cfg.backup_root, incoming_vault)
    if incoming_vault.exists() or incoming_vault.is_symlink():
        if incoming_vault.is_symlink():
            raise GuardError("refusing symlink incoming vault")
        safe_remove(cfg.backup_root, incoming_vault)
    incoming_vault.mkdir(parents=True)
    files = []
    total = 0
    for rel in scan.files:
        src = cfg.vault_path / rel
        dst = incoming_vault / rel
        require_inside(cfg.backup_root, dst)
        if is_within(dst, cfg.vault_path):
            raise BackupError("refusing to write inside the vault")
        info = worker.copy(src, dst)
        files.append({"bytes": info["bytes"], "path": rel, "sha256": info["sha256"]})
        total += int(info["bytes"])
    manifest = {
        "algorithm": "sha256",
        "file_count": len(files),
        "files": files,
        "total_bytes": total,
    }
    manifest_path = cfg.backup_root / "incoming" / "manifest.json"
    require_inside(cfg.backup_root, manifest_path)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    errors = verify_manifest(incoming_vault, manifest)
    if errors:
        raise BackupError("manifest verification failed: " + "; ".join(errors))
    again = collect_tree(worker, cfg.vault_path, logger)
    if again.placeholders:
        listed = ", ".join(item["path"] for item in again.placeholders)
        raise VaultProblem(f"icloud placeholder or dataless file: {listed}", kind="placeholder", placeholders=again.placeholders)
    if again.fingerprint != scan.fingerprint:
        raise VaultProblem("source vault changed during backup", kind="vault")
    return manifest


def move_into_place(src: Path, dst: Path, backup_root: Path) -> None:
    require_inside(backup_root, src)
    require_inside(backup_root, dst)
    if src.is_symlink() or dst.is_symlink():
        raise BackupError(f"refusing symlink snapshot: {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    aside = dst.with_name(dst.name + ".previous")
    require_inside(backup_root, aside)
    if aside.is_symlink():
        raise BackupError(f"refusing symlink: {aside}")
    if aside.exists():
        safe_remove(backup_root, aside)
    if dst.is_symlink():
        raise BackupError(f"refusing symlink snapshot: {dst}")
    if dst.exists():
        os.rename(dst, aside)
    try:
        os.rename(src, dst)
    except Exception:
        if aside.exists() and not dst.exists():
            os.rename(aside, dst)
        raise
    if aside.exists() and not aside.is_symlink():
        safe_remove(backup_root, aside)


def link_or_copy_file(src: Path, dst: Path) -> None:
    if src.is_symlink() or dst.is_symlink():
        raise BackupError("refusing symlink while linking snapshot")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copyfile(src, dst)


def replicate_tree(src: Path, dst: Path) -> None:
    if dst.exists() or dst.is_symlink():
        raise BackupError(f"snapshot destination exists: {dst}")
    dst.mkdir(parents=True)
    for dirpath, dirnames, filenames in os.walk(src, followlinks=False):
        current = Path(dirpath)
        for name in list(dirnames):
            path = current / name
            if path.is_symlink():
                raise BackupError(f"refusing to replicate symlink: {path}")
        target_dir = dst / current.relative_to(src)
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in filenames:
            source = current / name
            if source.is_symlink():
                raise BackupError(f"refusing to replicate symlink: {source}")
            link_or_copy_file(source, target_dir / name)


def link_period(cfg: Config, period: str, label: str, daily_vault: Path, daily_manifest: Path, daily_bundle: Path) -> None:
    stage_tree = cfg.backup_root / "incoming" / f"{period}-tree"
    replicate_tree(daily_vault, stage_tree)
    move_into_place(stage_tree, cfg.backup_root / "vault" / period / label, cfg.backup_root)
    stage_manifest = cfg.backup_root / "incoming" / f"{period}.manifest.json"
    link_or_copy_file(daily_manifest, stage_manifest)
    move_into_place(stage_manifest, cfg.backup_root / "vault" / period / f"{label}.manifest.json", cfg.backup_root)
    stage_bundle = cfg.backup_root / "incoming" / f"{period}.bundle"
    link_or_copy_file(daily_bundle, stage_bundle)
    move_into_place(stage_bundle, cfg.backup_root / "git" / period / f"{label}.bundle", cfg.backup_root)


def publish_snapshots(cfg: Config, labels: dict) -> tuple[Path, Path, Path]:
    daily_vault = cfg.backup_root / "vault" / "daily" / labels["daily"]
    daily_manifest = cfg.backup_root / "vault" / "daily" / f"{labels['daily']}.manifest.json"
    daily_bundle = cfg.backup_root / "git" / "daily" / f"{labels['daily']}.bundle"
    move_into_place(cfg.backup_root / "incoming" / "vault", daily_vault, cfg.backup_root)
    move_into_place(cfg.backup_root / "incoming" / "manifest.json", daily_manifest, cfg.backup_root)
    move_into_place(cfg.backup_root / "incoming" / "repo.bundle", daily_bundle, cfg.backup_root)
    if labels["sunday"]:
        link_period(cfg, "weekly", labels["weekly"], daily_vault, daily_manifest, daily_bundle)
    if labels["month_start"]:
        link_period(cfg, "monthly", labels["monthly"], daily_vault, daily_manifest, daily_bundle)
    return daily_vault, daily_manifest, daily_bundle


def matching_names(directory: Path, pattern: re.Pattern) -> list[str]:
    if not directory.exists() or directory.is_symlink() or not directory.is_dir():
        return []
    return sorted(path.name for path in directory.iterdir() if pattern.fullmatch(path.name))


def remove_entry(backup_root: Path, path: Path, deleted: list[str], skipped: list[dict]) -> None:
    if path.is_symlink():
        skipped.append({"path": str(path), "reason": "symlink"})
        return
    try:
        relative = str(path.relative_to(backup_root))
        safe_remove(backup_root, path)
        deleted.append(relative)
    except GuardError as exc:
        skipped.append({"path": str(path), "reason": str(exc)})


def apply_retention(backup_root: Path, cfg: Config) -> dict:
    deleted: list[str] = []
    skipped: list[dict] = []
    specs = [
        ("daily", cfg.retention_daily, DAILY_NAME, DAILY_BUNDLE, DAILY_MANIFEST),
        ("weekly", cfg.retention_weekly, WEEKLY_NAME, WEEKLY_BUNDLE, WEEKLY_MANIFEST),
        ("monthly", cfg.retention_monthly, MONTHLY_NAME, MONTHLY_BUNDLE, MONTHLY_MANIFEST),
    ]
    for period, keep, name_re, bundle_re, manifest_re in specs:
        vault_dir = backup_root / "vault" / period
        git_dir = backup_root / "git" / period
        names = matching_names(vault_dir, name_re)
        kept = set(names[-keep:])
        for name in names:
            if name not in kept:
                remove_entry(backup_root, vault_dir / name, deleted, skipped)
        if vault_dir.is_dir() and not vault_dir.is_symlink():
            for path in list(vault_dir.iterdir()):
                match = manifest_re.fullmatch(path.name)
                if match and match.group(1) not in kept:
                    remove_entry(backup_root, path, deleted, skipped)
        bundles = matching_names(git_dir, bundle_re)
        kept_bundles = set(bundles[-keep:])
        for name in bundles:
            if name not in kept_bundles:
                remove_entry(backup_root, git_dir / name, deleted, skipped)
    return {"deleted": deleted, "ran": True, "reason": "", "skipped": skipped}


def copy_snapshot(src: Path, dst: Path) -> None:
    if src.is_symlink():
        raise BackupError("refusing to restore a symlink snapshot")
    dst.mkdir(parents=True, exist_ok=True)
    for dirpath, dirnames, filenames in os.walk(src, followlinks=False):
        current = Path(dirpath)
        dirnames[:] = [name for name in dirnames if not (current / name).is_symlink()]
        target_dir = dst / current.relative_to(src)
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in filenames:
            source = current / name
            if source.is_symlink() or not source.is_file():
                continue
            target = target_dir / name
            with source.open("rb") as inp, target.open("wb") as out:
                shutil.copyfileobj(inp, out)


def make_restore_dir(cfg: Config) -> Path:
    path = Path(tempfile.mkdtemp(prefix="digitalbrain-restore-"))
    if is_within(path, cfg.vault_path) or is_within(path, cfg.backup_root):
        shutil.rmtree(path, ignore_errors=True)
        raise BackupError("restore temp dir overlaps vault or backup")
    return path


def run_restore(cfg: Config, logger: Logger, expected_sha: str | None = None) -> RestoreReport:
    chunks: list[str] = []

    def emit(title: str, text: str) -> None:
        block = f"--- {title} ---\n{text}"
        if not block.endswith("\n"):
            block += "\n"
        chunks.append(block)
        print(block, end="", flush=True)
        logger.write(block.rstrip("\n"))

    names = matching_names(cfg.backup_root / "vault" / "daily", DAILY_NAME)
    chosen = None
    for name in reversed(names):
        path = cfg.backup_root / "vault" / "daily" / name
        if not path.is_symlink():
            chosen = name
            break
    if chosen is None:
        raise BackupError("no daily vault snapshot to restore")
    bundle = cfg.backup_root / "git" / "daily" / f"{chosen}.bundle"
    manifest_path = cfg.backup_root / "vault" / "daily" / f"{chosen}.manifest.json"
    vault_snap = cfg.backup_root / "vault" / "daily" / chosen
    if bundle.is_symlink() or not bundle.is_file():
        raise BackupError("daily bundle missing")
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise BackupError("manifest missing")
    if expected_sha is None:
        status_path = cfg.backup_root / "status.json"
        if status_path.is_file() and not status_path.is_symlink():
            expected_sha = json.loads(status_path.read_text(encoding="utf-8")).get("head_sha")
    tmp = make_restore_dir(cfg)
    errors: list[str] = []
    try:
        git = Git(cfg.vault_path, cfg.backup_root, logger)
        dest = tmp / "repo"
        proc = git.clone_working(bundle, dest, tmp)
        emit("git clone", f"rc={proc.returncode}\n{proc.stdout}{proc.stderr}")
        if proc.returncode != 0:
            errors.append("git clone of bundle failed")
        else:
            proc = git.fsck(dest)
            emit("git fsck", f"rc={proc.returncode}\n{proc.stdout}{proc.stderr}")
            if proc.returncode != 0:
                errors.append("git fsck failed")
            proc = git.bundle_verify(dest, bundle)
            emit("git bundle verify", f"rc={proc.returncode}\n{proc.stdout}{proc.stderr}")
            if proc.returncode != 0:
                errors.append("git bundle verify failed")
            proc = git.rev_parse(dest, "HEAD")
            head = (proc.stdout or "").strip()
            emit("HEAD", f"rc={proc.returncode}\n{head}\n")
            if proc.returncode != 0:
                errors.append("rev-parse failed")
            elif expected_sha and head != expected_sha:
                errors.append(f"HEAD {head} != expected {expected_sha}")
        restored_vault = tmp / "vault"
        copy_snapshot(vault_snap, restored_vault)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_errors = verify_manifest(restored_vault, manifest)
        if manifest_errors:
            errors.extend(manifest_errors)
            emit(
                "manifest",
                f"file_count={manifest['file_count']}\n" + "\n".join(manifest_errors) + "\nmanifest ok=false\n",
            )
        else:
            emit(
                "manifest",
                f"file_count={manifest['file_count']}\nverified={manifest['file_count']}\nmanifest ok\n",
            )
    finally:
        if not errors:
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            emit("restore_dir", f"{tmp}\n")
    output = "".join(chunks)
    return RestoreReport(not errors, output, errors)


def acquire_lock(backup_root: Path) -> int | None:
    path = backup_root / ".backup.lock"
    if path.is_symlink():
        raise BackupError("refusing symlink lock file")
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        return None
    return fd


def perform_backup(cfg: Config, logger: Logger) -> dict:
    git_sync = GitSync()
    worker: VaultWorker | None = None
    try:
        assert_layout(cfg)
        discard_incoming(cfg.backup_root)
        worker = VaultWorker(cfg, logger)
        scan = None
        vault_exc: VaultProblem | None = None
        try:
            scan = scan_vault(worker, cfg.vault_path, logger)
        except VaultProblem as exc:
            vault_exc = exc
        git_exc: BackupError | None = None
        try:
            sync_git(cfg, logger, git_sync)
        except (BackupError, GuardError) as exc:
            git_exc = exc
        if vault_exc or git_exc or scan is None:
            discard_incoming(cfg.backup_root)
            errors = [str(item) for item in (vault_exc, git_exc) if item]
            return failure_status(
                errors or ["backup failed"],
                head=git_sync.head_sha,
                github=git_sync.github_head_sha,
                placeholders=list(getattr(vault_exc, "placeholders", []) or []),
                skipped_git=list(getattr(vault_exc, "skipped_git", []) or []),
            )
        manifest = copy_vault(cfg, worker, scan, logger)
        labels = snapshot_labels()
        publish_snapshots(cfg, labels)
        if labels["sunday"]:
            report = run_restore(cfg, logger, expected_sha=git_sync.head_sha)
            if not report.ok:
                raise BackupError("restore test failed: " + "; ".join(report.errors))
        try:
            discard_incoming(cfg.backup_root)
        except GuardError:
            pass
        prune = apply_retention(cfg.backup_root, cfg)
        bundle = cfg.backup_root / "git" / "daily" / f"{labels['daily']}.bundle"
        bundle_bytes = bundle.stat().st_size if bundle.is_file() else git_sync.bundle_bytes
        return {
            "alert_sent": False,
            "errors": [],
            "github_head_sha": git_sync.github_head_sha,
            "head_sha": git_sync.head_sha,
            "placeholders": [],
            "prune": prune,
            "result": "ok",
            "sizes": {
                "git_bundle_bytes": bundle_bytes,
                "vault_bytes": manifest["total_bytes"],
                "vault_file_count": manifest["file_count"],
            },
            "skipped_git": scan.skipped_git,
            "time": shanghai_now().isoformat(),
            "timezone": "Asia/Shanghai",
        }
    except (BackupError, VaultProblem, GuardError) as exc:
        try:
            discard_incoming(cfg.backup_root)
        except GuardError:
            pass
        placeholders = list(getattr(exc, "placeholders", []) or [])
        skipped = list(getattr(exc, "skipped_git", []) or [])
        return failure_status(
            [str(exc)],
            head=git_sync.head_sha,
            github=git_sync.github_head_sha,
            placeholders=placeholders,
            skipped_git=skipped,
        )
    finally:
        if worker is not None:
            worker.close()


def cmd_backup(cfg: Config) -> int:
    home_logger = Logger(cfg.home_log, None, blocked_roots=[cfg.volume])
    verdict = target_ready(cfg)
    if not verdict.ok:
        home_logger.write(f"backup target unavailable: {verdict.reason}")
        home_logger.write(f"interpreter sys.executable={sys.executable}")
        print(f"digitalbrain-backup result=failed reason={verdict.reason}", file=sys.stderr)
        status = failure_status([verdict.reason])
        send_alert(cfg, status, home_logger)
        return 1
    logger = Logger(cfg.home_log, cfg.backup_root / cfg.disk_log_name)
    logger.write("backup start")
    logger.write(f"interpreter sys.executable={sys.executable}")
    lock_fd = acquire_lock(cfg.backup_root)
    if lock_fd is None:
        status = failure_status(["another backup is already running"])
        write_status(cfg, status)
        send_alert(cfg, status, logger)
        write_status(cfg, status)
        print("digitalbrain-backup result=failed head=None")
        return 1
    try:
        status = perform_backup(cfg, logger)
    except Exception as exc:
        logger.write(traceback.format_exc())
        try:
            discard_incoming(cfg.backup_root)
        except GuardError:
            pass
        status = failure_status([str(exc)])
    finally:
        os.close(lock_fd)
    write_status(cfg, status)
    if status["result"] != "ok":
        send_alert(cfg, status, logger)
        write_status(cfg, status)
    else:
        logger.write("backup result=ok")
    print(f"digitalbrain-backup result={status['result']} head={status.get('head_sha')}")
    return 0 if status["result"] == "ok" else 1


def cmd_restore_test(cfg: Config) -> int:
    verdict = target_ready(cfg)
    home_logger = Logger(cfg.home_log, None, blocked_roots=[cfg.volume])
    if not verdict.ok:
        home_logger.write(f"backup target unavailable: {verdict.reason}")
        home_logger.write(f"interpreter sys.executable={sys.executable}")
        status = failure_status([verdict.reason])
        send_alert(cfg, status, home_logger)
        print(f"digitalbrain-backup result=failed reason={verdict.reason}", file=sys.stderr)
        return 1
    logger = Logger(cfg.home_log, cfg.backup_root / cfg.disk_log_name)
    logger.write(f"interpreter sys.executable={sys.executable}")
    try:
        report = run_restore(cfg, logger)
    except (BackupError, GuardError) as exc:
        print(str(exc), file=sys.stderr)
        report = RestoreReport(False, str(exc), [str(exc)])
    if report.ok:
        return 0
    status = failure_status(report.errors or ["restore test failed"])
    send_alert(cfg, status, logger)
    return 1


def ensure_backup_root(cfg: Config) -> Path:
    if not cfg.volume.is_dir() or cfg.volume.is_symlink():
        raise BackupError("volume is not a directory")
    root = cfg.volume
    for part in Path(cfg.backup_folder).parts:
        if part in {"", ".", ".."}:
            raise BackupError("bad backup folder")
        root = root / part
        if root.is_symlink():
            raise BackupError("refusing symlink in backup path")
        if not root.exists():
            root.mkdir(exist_ok=False)
        elif not root.is_dir():
            raise BackupError("backup folder is not a directory")
    return root


def write_marker(path: Path, volume: Path) -> None:
    if path.is_symlink():
        raise BackupError("refusing symlink marker")
    path.write_text(f"{MARKER_TOKEN}\nvolume={volume}\n", encoding="utf-8")


def is_usr_bin_python3(path: Path) -> bool:
    current = Path(os.path.normpath(str(path.expanduser())))
    seen: set[str] = set()
    while len(seen) < 8:
        text = os.path.normpath(str(current))
        if text in seen:
            break
        seen.add(text)
        if text == "/usr/bin/python3":
            return True
        if not current.is_symlink():
            break
        try:
            link = os.readlink(current)
        except OSError:
            break
        nxt = Path(link)
        if not nxt.is_absolute():
            nxt = current.parent / nxt
        current = Path(os.path.normpath(str(nxt)))
    return False


def python_stdout(binary: Path, code: str) -> str:
    try:
        proc = subprocess.run(
            [str(binary), "-c", code],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
    except OSError as exc:
        raise BackupError(f"python interpreter failed to start: {exc}") from exc
    if proc.returncode != 0:
        detail = ((proc.stderr or "") + (proc.stdout or "")).strip()
        raise BackupError(f"python interpreter failed to start: {detail or 'no output'}")
    return (proc.stdout or "").strip()


def require_standalone_python() -> Path:
    raw = os.environ.get("DIGITALBRAIN_BACKUP_PYTHON", "").strip()
    if not raw:
        raise BackupError(
            "DIGITALBRAIN_BACKUP_PYTHON is required and must point to a standalone Python; "
            "/usr/bin/python3 is a macOS launcher shim and is refused"
        )
    source = Path(raw).expanduser()
    if not source.is_absolute():
        raise BackupError("DIGITALBRAIN_BACKUP_PYTHON must be an absolute path")
    if is_usr_bin_python3(source):
        raise BackupError("refusing /usr/bin/python3; it is a launcher shim, not a standalone Python")
    if not source.is_file():
        raise BackupError(f"python interpreter not found: {source}")
    reported = python_stdout(source, "import os,sys; print(os.path.realpath(sys.executable))")
    if not reported or os.path.realpath(reported) != os.path.realpath(source):
        raise BackupError(
            "refusing launcher shim: sys.executable "
            f"{reported or 'empty'} does not match DIGITALBRAIN_BACKUP_PYTHON {source}"
        )
    return source


def install_dedicated_python(home: Path) -> Path:
    source = require_standalone_python()
    dest_dir = home / "Library/Application Support/digitalbrain-backup"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / DEDICATED_NAME
    if dest.is_symlink():
        raise BackupError("refusing symlink dedicated interpreter")
    temporary = dest.with_name(DEDICATED_NAME + ".tmp")
    if temporary.is_symlink():
        raise BackupError("refusing symlink dedicated interpreter")
    if temporary.exists():
        temporary.unlink()
    shutil.copyfile(source, temporary)
    os.chmod(temporary, 0o755)
    if sys.platform == "darwin":
        subprocess.run(
            [
                "codesign",
                "--force",
                "--sign",
                "-",
                "--identifier",
                "com.jake.digitalbrain-backup.python",
                str(temporary),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    try:
        reported = python_stdout(temporary, "import hashlib,sys; print(sys.executable)")
    except BackupError:
        temporary.unlink(missing_ok=True)
        raise
    if reported != str(temporary):
        temporary.unlink(missing_ok=True)
        raise BackupError(
            f"dedicated interpreter sys.executable is {reported or 'empty'}, not the copied path {temporary}"
        )
    os.replace(temporary, dest)
    return dest


def render_plist(dedicated: Path, home: Path) -> str:
    template = (PACKAGE_ROOT / "launchd" / PLIST_NAME).read_text(encoding="utf-8")
    rendered = (
        template.replace("__DEDICATED_PYTHON__", str(dedicated))
        .replace("__DIGITALBRAIN_BACKUP_ROOT__", str(PACKAGE_ROOT))
        .replace("__HOME__", str(home))
    )
    for token in ("__DEDICATED_PYTHON__", "__DIGITALBRAIN_BACKUP_ROOT__", "__HOME__"):
        if token in rendered:
            raise BackupError("plist placeholders were not filled")
    return rendered


def cmd_install(config_path: Path, home: Path, launch_agents: Path) -> int:
    if not config_path.exists():
        example = PACKAGE_ROOT / "config.example.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(example, config_path)
        print(
            "Wrote config from config.example.json. Edit vault_path and discord_channel_id, then re-run install.",
            file=sys.stderr,
        )
        return 1
    cfg = load_config(config_path)
    logger = Logger(cfg.home_log, None, blocked_roots=[cfg.volume])
    verdict = collect_mount_facts(cfg)
    if not verdict.ok:
        logger.write(f"install target unavailable: {verdict.reason}")
        status = failure_status([verdict.reason])
        send_alert(cfg, status, logger)
        print(f"digitalbrain-backup install failed: {verdict.reason}", file=sys.stderr)
        return 1
    try:
        dedicated = install_dedicated_python(home)
        root = ensure_backup_root(cfg)
        marker = root / MARKER_NAME
        ok, detail = marker_status(marker)
        if marker.is_symlink() or detail == "symlink":
            raise BackupError("refusing symlink marker")
        if not ok:
            write_marker(marker, cfg.volume)
        text = render_plist(dedicated, home)
        launch_agents.mkdir(parents=True, exist_ok=True)
        dest = launch_agents / PLIST_NAME
        if dest.is_symlink():
            raise BackupError("refusing symlink LaunchAgent path")
        dest.write_text(text, encoding="utf-8")
    except (BackupError, ConfigError, GuardError) as exc:
        status = failure_status([str(exc)])
        send_alert(cfg, status, logger)
        print(f"digitalbrain-backup install failed: {exc}", file=sys.stderr)
        return 1
    print(f"Dedicated interpreter: {dedicated}")
    print(f"LaunchAgent plist written to {dest}")
    print("The agent is not loaded. Grant Full Disk Access only to that interpreter, then load the agent yourself. See README.")
    if not cfg.vault_path.exists():
        print(f"warning: vault path does not exist yet: {cfg.vault_path}", file=sys.stderr)
    if "REPLACE_" in cfg.discord_channel_id or not cfg.discord_channel_id.strip():
        print("warning: discord_channel_id is not set", file=sys.stderr)
    return 0


def cmd_uninstall(launch_agents: Path) -> int:
    dest = launch_agents / PLIST_NAME
    if dest.is_symlink() or dest.exists():
        dest.unlink()
        print(f"Removed {dest}")
    else:
        print(f"No plist at {dest}")
    print("Backup files and the dedicated interpreter were left in place.")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    if len(argv) > 1 and argv[1] == "--vault-worker":
        return vault_worker_main()
    parser = argparse.ArgumentParser(description="DigitalBrain nightly backup")
    parser.add_argument("--config", type=Path)
    parser.add_argument("command", choices=["backup", "restore-test", "install", "uninstall"])
    parser.add_argument("--home", type=Path)
    parser.add_argument("--launch-agents-dir", type=Path)
    args = parser.parse_args(argv[1:])
    home = args.home.expanduser() if args.home else Path.home()
    launch_agents = args.launch_agents_dir or (home / "Library/LaunchAgents")
    if args.command == "uninstall":
        return cmd_uninstall(launch_agents)
    if args.config is None:
        print("config is required", file=sys.stderr)
        return 2
    if args.command == "install":
        return cmd_install(args.config, home, launch_agents)
    if not args.config.is_file():
        print(f"config not found: {args.config}", file=sys.stderr)
        return 2
    try:
        cfg = load_config(args.config)
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.command == "backup":
        return cmd_backup(cfg)
    return cmd_restore_test(cfg)


if __name__ == "__main__":
    sys.exit(main())
