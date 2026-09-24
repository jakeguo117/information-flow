#!/usr/bin/env python3
"""Readability gate and encrypted restic recovery for one vault tree.

The live DigitalBrain vault is read for backup and compared after an isolated
restore. This tool does not migrate, delete, rewrite notes, or change git
state in the vault. Passwords and B2 keys stay in the macOS keychain and are
passed to restic through the environment.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
KEYCHAIN_SERVICE = "jake.information-flow.vault-recovery"
SF_DATALESS = 0x40000000
SAMPLE_DIRS = {
    "cognition": "📖 Cognition",
    "journal": "📝 Journal",
    "inbox": "📥 Inbox",
}
SAMPLE_LIMITS = {"cognition": None, "journal": 5, "inbox": 5}
SUMMARY_FIELDS = (
    "snapshot_id",
    "data_added",
    "files_changed",
    "files_new",
    "files_unmodified",
    "total_bytes_processed",
    "total_files_processed",
)


class RecoveryError(Exception):
    def __init__(self, message: str, code: int = 2) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class FileStat:
    size: int
    blocks: int
    flags: int
    mode: int
    is_symlink: bool


@dataclass
class SecretBag:
    values: list[str] = field(default_factory=list)

    def add(self, value: str | None) -> None:
        if value and len(value) >= 8:
            self.values.append(value)

    def scrub(self, text: str) -> str:
        redacted = text
        for value in self.values:
            redacted = redacted.replace(value, "[redacted]")
        return redacted


@dataclass
class TreeReport:
    files: int = 0
    markdown: int = 0
    symlinks: int = 0
    directories: int = 0
    empty_directories: int = 0
    dataless: int = 0
    unreadable: int = 0
    unsupported: int = 0
    logical_bytes: int = 0
    bytes_read: int = 0
    by_top: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.dataless == 0 and self.unreadable == 0 and self.unsupported == 0

    def to_json(self) -> dict[str, object]:
        return {
            "bytes_read": self.bytes_read,
            "by_top_level": self.by_top,
            "dataless": self.dataless,
            "directories": self.directories,
            "empty_directories": self.empty_directories,
            "files": self.files,
            "logical_bytes": self.logical_bytes,
            "markdown": self.markdown,
            "ok": self.ok,
            "symlinks": self.symlinks,
            "unreadable": self.unreadable,
            "unsupported": self.unsupported,
        }


def is_dataless(size: int, blocks: int, flags: int) -> bool:
    if flags & SF_DATALESS:
        return True
    return size > 0 and blocks == 0


def file_stat(path: Path) -> FileStat:
    st = path.lstat()
    return FileStat(
        size=st.st_size,
        blocks=getattr(st, "st_blocks", 0) or 0,
        flags=getattr(st, "st_flags", 0) or 0,
        mode=st.st_mode,
        is_symlink=stat.S_ISLNK(st.st_mode),
    )


def assert_backup_root(root: Path) -> Path:
    resolved = root.expanduser().resolve()
    if resolved == Path(resolved.anchor) or resolved == Path.home():
        raise RecoveryError("backup root is too broad")
    if not resolved.is_dir():
        raise RecoveryError("backup root is not a directory")
    return resolved


def assert_outside_repo(path: Path, repo_root: Path = PLUGIN_ROOT) -> Path:
    resolved = path.expanduser().resolve()
    repo = repo_root.resolve()
    if resolved == repo or repo in resolved.parents:
        raise RecoveryError("path is inside the information-flow repository")
    return resolved


def assert_isolated_target(target: Path, vault: Path) -> Path:
    resolved_target = target.expanduser().resolve()
    resolved_vault = vault.expanduser().resolve()
    if resolved_target == Path(resolved_target.anchor):
        raise RecoveryError("restore target is the filesystem root")
    if resolved_target == resolved_vault:
        raise RecoveryError("restore target is the live vault")
    if resolved_vault in resolved_target.parents or resolved_target in resolved_vault.parents:
        raise RecoveryError("restore target overlaps the live vault")
    return resolved_target


def top_level(rel: str) -> str:
    return rel.split("/", 1)[0]


def empty_bucket() -> dict[str, int]:
    return {
        "bytes_read": 0,
        "dataless": 0,
        "files": 0,
        "logical_bytes": 0,
        "markdown": 0,
        "unreadable": 0,
        "unsupported": 0,
    }


def bump(report: TreeReport, rel: str, **deltas: int) -> None:
    bucket = report.by_top.setdefault(top_level(rel), empty_bucket())
    for key, value in deltas.items():
        bucket[key] = bucket.get(key, 0) + value


def iter_names(root: Path) -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        current = Path(dirpath)
        for name in sorted(dirnames):
            path = current / name
            found.append((path.relative_to(root).as_posix(), path))
        for name in sorted(filenames):
            path = current / name
            found.append((path.relative_to(root).as_posix(), path))
    return found


def scan_tree(root: Path, stat_fn=file_stat) -> TreeReport:
    report = TreeReport()
    seen_dirs: set[str] = set()
    child_dirs: set[str] = set()
    for rel, path in iter_names(root):
        if path.parent != root:
            parent_rel = path.parent.relative_to(root).as_posix()
            child_dirs.add(parent_rel)
        try:
            info = stat_fn(path)
        except OSError:
            report.unreadable += 1
            bump(report, rel, unreadable=1)
            continue
        if stat.S_ISDIR(info.mode) and not info.is_symlink:
            report.directories += 1
            seen_dirs.add(rel)
            continue
        if info.is_symlink:
            report.symlinks += 1
            continue
        if not stat.S_ISREG(info.mode):
            report.unsupported += 1
            bump(report, rel, unsupported=1)
            continue
        report.files += 1
        report.logical_bytes += info.size
        markdown = 1 if rel.endswith(".md") else 0
        report.markdown += markdown
        dataless = 1 if is_dataless(info.size, info.blocks, info.flags) else 0
        report.dataless += dataless
        bump(
            report,
            rel,
            files=1,
            logical_bytes=info.size,
            markdown=markdown,
            dataless=dataless,
        )
    report.empty_directories = len(seen_dirs - child_dirs)
    return report


def download_command(path: Path) -> list[str]:
    return ["/usr/bin/brctl", "download", str(path)]


def brctl_download(path: Path) -> None:
    try:
        subprocess.run(
            download_command(path),
            check=False,
            capture_output=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return


def count_bytes(path: Path) -> int:
    total = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                return total
            total += len(chunk)


def sha256_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                return total, digest.hexdigest()
            total += len(chunk)
            digest.update(chunk)


def read_one(
    path: Path,
    stat_fn,
    download_fn,
    read_fn,
    sleep_fn,
    attempts: int,
) -> tuple[str, int, int]:
    last_size = 0
    last_read = 0
    for attempt in range(attempts):
        try:
            info = stat_fn(path)
        except OSError:
            return "unreadable", 0, 0
        last_size = info.size
        if is_dataless(info.size, info.blocks, info.flags):
            download_fn(path)
        try:
            last_read = read_fn(path)
        except OSError:
            last_read = -1
        try:
            after = stat_fn(path)
        except OSError:
            return "unreadable", last_size, 0
        if (
            last_read == after.size
            and not is_dataless(after.size, after.blocks, after.flags)
        ):
            return "ok", after.size, last_read
        if attempt + 1 < attempts:
            sleep_fn(min(2**attempt, 4))
    if last_read < 0:
        return "unreadable", last_size, 0
    try:
        after = stat_fn(path)
    except OSError:
        return "unreadable", last_size, 0
    if is_dataless(after.size, after.blocks, after.flags):
        return "dataless", after.size, max(last_read, 0)
    return "unreadable", after.size, max(last_read, 0)


def read_tree(
    root: Path,
    stat_fn=file_stat,
    download_fn=brctl_download,
    read_fn=count_bytes,
    sleep_fn=time.sleep,
    attempts: int = 3,
    workers: int = 4,
    progress=None,
) -> TreeReport:
    report = TreeReport()
    regular: list[tuple[str, Path]] = []
    seen_dirs: set[str] = set()
    child_dirs: set[str] = set()
    for rel, path in iter_names(root):
        if path.parent != root:
            child_dirs.add(path.parent.relative_to(root).as_posix())
        try:
            info = stat_fn(path)
        except OSError:
            report.unreadable += 1
            bump(report, rel, unreadable=1)
            continue
        if stat.S_ISDIR(info.mode) and not info.is_symlink:
            report.directories += 1
            seen_dirs.add(rel)
            continue
        if info.is_symlink:
            report.symlinks += 1
            continue
        if not stat.S_ISREG(info.mode):
            report.unsupported += 1
            bump(report, rel, unsupported=1)
            continue
        regular.append((rel, path))
    report.empty_directories = len(seen_dirs - child_dirs)

    def task(item: tuple[str, Path]) -> tuple[str, str, int, int]:
        rel, path = item
        status, logical, nbytes = read_one(
            path, stat_fn, download_fn, read_fn, sleep_fn, attempts
        )
        return rel, status, logical, nbytes

    done = 0
    pool_size = max(1, workers)
    with ThreadPoolExecutor(max_workers=pool_size) as pool:
        futures = [pool.submit(task, item) for item in regular]
        for future in as_completed(futures):
            rel, status, logical, nbytes = future.result()
            markdown = 1 if rel.endswith(".md") else 0
            report.files += 1
            report.markdown += markdown
            report.logical_bytes += logical
            dataless = 1 if status == "dataless" else 0
            unreadable = 1 if status == "unreadable" else 0
            if status == "ok":
                report.bytes_read += nbytes
            report.dataless += dataless
            report.unreadable += unreadable
            bump(
                report,
                rel,
                files=1,
                markdown=markdown,
                logical_bytes=logical,
                bytes_read=nbytes if status == "ok" else 0,
                dataless=dataless,
                unreadable=unreadable,
            )
            done += 1
            if progress and done % 100 == 0:
                progress(done, report.files and report.ok)
    return report


def markdown_structure(data: bytes) -> dict[str, object]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return {
            "encoding": "non-utf8",
            "frontmatter_keys": [],
            "wikilink_count": 0,
            "wikilink_digest": "",
        }
    keys: list[str] = []
    body = text
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() != "---":
                continue
            for line in lines[1:index]:
                if not line.strip() or line[0] in " \t#":
                    continue
                if ":" in line:
                    keys.append(line.split(":", 1)[0].strip())
            body = "\n".join(lines[index + 1 :])
            break
    links: list[str] = []
    cursor = 0
    while True:
        start = body.find("[[", cursor)
        if start < 0:
            break
        end = body.find("]]", start + 2)
        if end < 0:
            break
        inner = body[start + 2 : end]
        target = inner.split("|", 1)[0].split("#", 1)[0].strip()
        if target:
            links.append(target)
        cursor = end + 2
    digest = hashlib.sha256("\n".join(links).encode("utf-8")).hexdigest()
    return {
        "encoding": "utf-8",
        "frontmatter_keys": keys,
        "wikilink_count": len(links),
        "wikilink_digest": digest,
    }


def choose_samples(relative_paths: list[str]) -> dict[str, list[str]]:
    selected: dict[str, list[str]] = {}
    for label, dirname in SAMPLE_DIRS.items():
        markdown = sorted(
            rel
            for rel in relative_paths
            if rel.endswith(".md") and (rel == dirname or rel.startswith(dirname + "/"))
        )
        if not markdown:
            raise RecoveryError(f"required sample tree is missing: {label}", code=4)
        limit = SAMPLE_LIMITS[label]
        if limit is None or len(markdown) <= limit:
            selected[label] = markdown
            continue
        step = len(markdown) / limit
        selected[label] = [markdown[int(i * step)] for i in range(limit)]
    return selected


def git_status_counts(root: Path) -> dict[str, object]:
    git_dir = root / ".git"
    index = git_dir / "index"
    if not git_dir.exists() or not index.is_file():
        return {"available": False, "reason": "no-index"}
    with tempfile.TemporaryDirectory(prefix="if-git-index-") as tmp:
        copied = Path(tmp) / "index"
        try:
            shutil.copy2(index, copied)
        except OSError:
            return {"available": False, "reason": "index-unreadable"}
        after_copy = index.stat().st_mtime_ns
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = str(copied)
        env["GIT_OPTIONAL_LOCKS"] = "0"
        proc = subprocess.run(
            [
                "git",
                "--no-optional-locks",
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "core.fsmonitor=",
                "-C",
                str(root),
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
            ],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
    after_status = index.stat().st_mtime_ns
    if after_status != after_copy:
        raise RecoveryError("git status touched the vault index")
    if proc.returncode != 0:
        return {"available": False, "reason": "git-status-failed"}
    counts = {"staged": 0, "modified": 0, "deleted": 0, "untracked": 0, "other": 0}
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            counts["other"] += 1
            continue
        xy = line[:2]
        if xy == "??":
            counts["untracked"] += 1
            continue
        if "D" in xy:
            counts["deleted"] += 1
        elif any(mark in xy for mark in "MATURC"):
            counts["modified"] += 1
        else:
            counts["other"] += 1
        if xy[0] not in " ?":
            counts["staged"] += 1
    counts["available"] = True
    counts["method"] = "porcelain-v1-uall-copied-index"
    return counts


class KeychainStore:
    def __init__(self, service: str = KEYCHAIN_SERVICE, keychain: Path | None = None) -> None:
        self.service = service
        self.keychain = keychain

    def get(self, account: str) -> str | None:
        command = [
            "security",
            "find-generic-password",
            "-s",
            self.service,
            "-a",
            account,
            "-w",
        ]
        if self.keychain is not None:
            command.append(str(self.keychain))
        proc = subprocess.run(command, check=False, capture_output=True, text=True)
        if proc.returncode == 0:
            value = proc.stdout
            if value.endswith("\n"):
                value = value[:-1]
            return value
        err = proc.stderr.lower()
        if "could not be found" in err or "item not found" in err:
            return None
        raise RecoveryError(f"keychain read failed for account {account}")

    def put(self, account: str, secret: str) -> None:
        command = [
            "security",
            "add-generic-password",
            "-U",
            "-s",
            self.service,
            "-a",
            account,
            "-w",
            secret,
        ]
        if self.keychain is not None:
            command.append(str(self.keychain))
        proc = subprocess.run(command, check=False, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RecoveryError(f"keychain write failed for account {account}")


def ensure_restic_password(store: KeychainStore) -> str:
    existing = store.get("restic-password")
    if existing:
        return existing
    generated = secrets.token_urlsafe(32)
    store.put("restic-password", generated)
    stored = store.get("restic-password")
    if stored != generated:
        raise RecoveryError("keychain did not return the restic password")
    return generated


def parse_s3_repo(url: str) -> tuple[str, str, str]:
    if not url.startswith("s3:"):
        raise RecoveryError("restic repository is not an s3 URL")
    rest = url[3:]
    if rest.startswith("//"):
        rest = rest[2:]
    parts = [part for part in rest.split("/") if part != ""]
    if len(parts) < 2:
        raise RecoveryError("restic repository URL is missing a bucket")
    host, bucket = parts[0], parts[1]
    prefix = "/".join(parts[2:])
    return host, bucket, prefix


def s3_host(api_url: str) -> str:
    host = api_url.removeprefix("https://").removeprefix("http://").rstrip("/")
    if not host or "/" in host:
        raise RecoveryError("B2 account did not return an S3 endpoint")
    return host


def b2_authorize(key_id: str, app_key: str, opener) -> dict:
    token = base64.b64encode(f"{key_id}:{app_key}".encode("utf-8")).decode("ascii")
    request = urllib.request.Request(
        "https://api.backblazeb2.com/b2api/v2/b2_authorize_account",
        headers={"Authorization": f"Basic {token}"},
        method="GET",
    )
    try:
        with opener.open(request, timeout=60) as response:
            payload = json.load(response)
    except urllib.error.HTTPError:
        raise RecoveryError("B2 authorization failed") from None
    except (OSError, json.JSONDecodeError):
        raise RecoveryError("B2 authorization failed") from None
    if "authorizationToken" not in payload or "apiUrl" not in payload:
        raise RecoveryError("B2 authorization response was incomplete")
    return payload


def b2_post(auth: dict, api_name: str, payload: dict, opener) -> dict:
    request = urllib.request.Request(
        auth["apiUrl"].rstrip("/") + "/b2api/v2/" + api_name,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": auth["authorizationToken"],
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with opener.open(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            code = json.loads(raw).get("code") or str(exc.code)
        except json.JSONDecodeError:
            code = str(exc.code)
        raise RecoveryError(f"B2 {api_name} failed: {code}") from None
    except (OSError, json.JSONDecodeError):
        raise RecoveryError(f"B2 {api_name} failed") from None


def b2_list_buckets(auth: dict, opener, bucket_name: str | None = None) -> list[dict]:
    body: dict[str, str] = {"accountId": auth["accountId"]}
    if bucket_name:
        body["bucketName"] = bucket_name
    payload = b2_post(auth, "b2_list_buckets", body, opener)
    buckets = payload.get("buckets")
    if not isinstance(buckets, list):
        raise RecoveryError("B2 bucket list was incomplete")
    return buckets


def b2_create_bucket(auth: dict, bucket: str, opener) -> dict:
    return b2_post(
        auth,
        "b2_create_bucket",
        {
            "accountId": auth["accountId"],
            "bucketName": bucket,
            "bucketType": "allPrivate",
        },
        opener,
    )


def ensure_private(listed: dict[str, dict], bucket: str) -> None:
    info = listed.get(bucket)
    if info is None:
        raise RecoveryError("B2 bucket is not visible to this key")
    if info.get("bucketType") != "allPrivate":
        raise RecoveryError("B2 bucket is not private")


def default_bucket_name() -> str:
    return "jdw-recovery-" + secrets.token_hex(8)


def resolve_repository(store: KeychainStore, opener=None, name_fn=default_bucket_name) -> str:
    key_id = store.get("b2-key-id")
    app_key = store.get("b2-application-key")
    if not key_id or not app_key:
        raise RecoveryError(
            "missing keychain accounts b2-key-id and b2-application-key "
            f"in service {KEYCHAIN_SERVICE}"
        )
    client = opener or urllib.request.build_opener()
    auth = b2_authorize(key_id, app_key, client)
    allowed = auth.get("allowed") or {}
    capabilities = set(allowed.get("capabilities") or [])
    if "listBuckets" not in capabilities:
        raise RecoveryError("B2 key cannot list buckets to verify privacy")
    host = s3_host(str(auth.get("s3ApiUrl") or ""))
    current = store.get("restic-repository")
    if current:
        repo_host, bucket, _prefix = parse_s3_repo(current)
        if repo_host != host:
            raise RecoveryError("restic repository host does not match the B2 account")
        listed = {
            item["bucketName"]: item
            for item in b2_list_buckets(auth, client, bucket)
        }
        ensure_private(listed, bucket)
        return current
    listed = {item["bucketName"]: item for item in b2_list_buckets(auth, client)}
    restricted = allowed.get("bucketName") or ""
    if restricted:
        ensure_private(listed, restricted)
        bucket = restricted
    else:
        if "writeBuckets" not in capabilities:
            raise RecoveryError("B2 key cannot create a private bucket")
        bucket = name_fn()
        if bucket in listed:
            raise RecoveryError("generated B2 bucket name already exists")
        created = b2_create_bucket(auth, bucket, client)
        if created.get("bucketType") != "allPrivate":
            raise RecoveryError("B2 bucket was not created private")
        listed = {
            item["bucketName"]: item for item in b2_list_buckets(auth, client, bucket)
        }
        ensure_private(listed, bucket)
    repository = f"s3:{host}/{bucket}/digitalbrain"
    store.put("restic-repository", repository)
    return repository


def restic_bin() -> str:
    found = shutil.which("restic")
    if not found:
        raise RecoveryError("restic is not installed")
    return found


def restic_env(
    repository: str,
    password: str,
    key_id: str | None = None,
    app_key: str | None = None,
) -> dict[str, str]:
    env = os.environ.copy()
    env["RESTIC_REPOSITORY"] = repository
    env["RESTIC_PASSWORD"] = password
    env.pop("RESTIC_PASSWORD_FILE", None)
    env.pop("RESTIC_PASSWORD_COMMAND", None)
    if repository.startswith("s3:"):
        if not key_id or not app_key:
            raise RecoveryError("S3 repository requires B2 keychain accounts")
        env["AWS_ACCESS_KEY_ID"] = key_id
        env["AWS_SECRET_ACCESS_KEY"] = app_key
    else:
        env.pop("AWS_ACCESS_KEY_ID", None)
        env.pop("AWS_SECRET_ACCESS_KEY", None)
    return env


def restic_command(args: list[str], binary: str | None = None) -> list[str]:
    return [binary or restic_bin(), "--no-cache", *args]


@dataclass
class CommandResult:
    returncode: int
    stdout: bytes
    stderr: str


def run_command(cmd: list[str], env: dict[str, str], timeout: int | None = None) -> CommandResult:
    proc = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        env=env,
        timeout=timeout,
    )
    return CommandResult(
        proc.returncode,
        proc.stdout,
        proc.stderr.decode("utf-8", errors="replace"),
    )


def parse_backup_summary(stdout: bytes) -> dict[str, object]:
    summary = None
    for line in stdout.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("message_type") == "summary":
            summary = payload
    if not summary or not summary.get("snapshot_id"):
        raise RecoveryError("restic backup did not report a snapshot id", code=4)
    return {key: summary[key] for key in SUMMARY_FIELDS if key in summary}


def ensure_restic_repo(run, env: dict[str, str], bag: SecretBag) -> None:
    listed = run(["snapshots", "--json"], env)
    if listed.returncode == 0:
        return
    err = bag.scrub(listed.stderr).lower()
    if "wrong password" in err or "ciphertext verification failed" in err:
        raise RecoveryError("restic rejected the keychain password")
    repository = env["RESTIC_REPOSITORY"]
    if not repository.startswith("s3:") and Path(repository).exists():
        raise RecoveryError("existing local path is not a readable restic repository")
    init = run(["init"], env)
    if init.returncode != 0:
        raise RecoveryError("restic init failed: " + bag.scrub(init.stderr)[:400], code=4)


def repo_config_version(run, env: dict[str, str], bag: SecretBag) -> int:
    proc = run(["cat", "config"], env)
    if proc.returncode != 0:
        raise RecoveryError("restic config read failed: " + bag.scrub(proc.stderr)[:300], code=4)
    try:
        payload = json.loads(proc.stdout.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise RecoveryError("restic config was not valid") from exc
    version = payload.get("version")
    if not isinstance(version, int) or version < 1:
        raise RecoveryError("restic repository is not an encrypted restic repo", code=4)
    return version


def snapshot_paths(run, env: dict[str, str], snapshot_id: str, bag: SecretBag) -> list[str]:
    proc = run(["ls", snapshot_id, "--json"], env)
    if proc.returncode != 0:
        raise RecoveryError("restic ls failed: " + bag.scrub(proc.stderr)[:300], code=4)
    paths: list[str] = []
    for line in proc.stdout.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        path = payload.get("path")
        if isinstance(path, str):
            paths.append(path)
    return paths


def match_snapshot_path(root: Path, rel: str, listed: list[str]) -> str:
    expected = root.resolve().as_posix().rstrip("/") + "/" + rel
    if expected in listed:
        return expected
    suffix = "/" + rel
    matches = [path for path in listed if path.endswith(suffix)]
    if len(matches) == 1:
        return matches[0]
    raise RecoveryError("sample path is missing from the snapshot", code=4)


def restored_root(target: Path, source: Path) -> Path:
    files = [
        rel
        for rel, path in iter_names(source)
        if path.is_file() and not path.is_symlink()
    ]
    if not files:
        raise RecoveryError("source tree has no files", code=4)
    marker = sorted(files)[0]
    marker_path = Path(marker)
    for candidate in target.rglob(marker_path.name):
        if not candidate.is_file() or candidate.is_symlink():
            continue
        if not candidate.as_posix().endswith("/" + marker):
            continue
        found = candidate.parents[len(marker_path.parts) - 1]
        if found / marker == candidate:
            return found
    direct = target / source.resolve().relative_to(source.resolve().anchor)
    if direct.is_dir():
        return direct
    raise RecoveryError("isolated restore did not contain the vault tree", code=4)


def hash_tree(root: Path) -> dict[str, tuple[str, int, str]]:
    """Map relative path to (kind, size, digest-or-link)."""
    mapped: dict[str, tuple[str, int, str]] = {}
    for rel, path in iter_names(root):
        if path.is_symlink():
            mapped[rel] = ("symlink", 0, os.readlink(path))
            continue
        if path.is_dir():
            continue
        if not path.is_file():
            mapped[rel] = ("other", 0, "")
            continue
        size, digest = sha256_file(path)
        mapped[rel] = ("file", size, digest)
    return mapped


def compare_trees(source: Path, restored: Path) -> dict[str, object]:
    left = hash_tree(source)
    right = hash_tree(restored)
    missing = sorted(set(left) - set(right))
    extra = sorted(set(right) - set(left))
    mismatched = []
    matched = 0
    for rel in sorted(set(left) & set(right)):
        if left[rel] == right[rel]:
            matched += 1
            continue
        mismatched.append(top_level(rel))
    return {
        "matched": matched,
        "missing": len(missing),
        "extra": len(extra),
        "mismatched": len(mismatched),
        "mismatch_top_levels": sorted(set(mismatched)),
    }


def sample_structure(source: Path, restored: Path, samples: dict[str, list[str]]) -> dict[str, int]:
    checked = 0
    matched = 0
    for rels in samples.values():
        for rel in rels:
            source_path = source / rel
            restored_path = restored / rel
            if not source_path.is_file() or not restored_path.is_file():
                raise RecoveryError("sample file is missing from the isolated restore", code=4)
            source_bytes = source_path.read_bytes()
            restored_bytes = restored_path.read_bytes()
            checked += 1
            if markdown_structure(source_bytes) == markdown_structure(restored_bytes):
                matched += 1
    return {"checked": checked, "matched": matched}


def backup_snapshot(
    root: Path,
    repository: str,
    password: str,
    key_id: str | None,
    app_key: str | None,
    run=None,
    binary: str | None = None,
    preflight: TreeReport | None = None,
) -> dict[str, object]:
    report = preflight if preflight is not None else read_tree(root)
    if not report.ok:
        raise RecoveryError("protected files are still unreadable or dataless", code=3)
    bag = SecretBag()
    bag.add(password)
    bag.add(key_id)
    bag.add(app_key)
    bag.add(repository)
    env = restic_env(repository, password, key_id, app_key)
    command_run = run or (
        lambda args, cmd_env: run_command(restic_command(args, binary), cmd_env)
    )
    ensure_restic_repo(command_run, env, bag)
    version = repo_config_version(command_run, env, bag)
    proc = command_run(
        ["backup", "--json", "--tag", "3b-b1", "--host", "3b-b1", str(root)],
        env,
    )
    if proc.returncode != 0:
        raise RecoveryError("restic backup failed: " + bag.scrub(proc.stderr)[:400], code=4)
    summary = parse_backup_summary(proc.stdout)
    checked = command_run(["check"], env)
    if checked.returncode != 0:
        raise RecoveryError("restic integrity check failed: " + bag.scrub(checked.stderr)[:400], code=4)
    summary["check_ok"] = True
    summary["repo_config_version"] = version
    summary["read"] = report.to_json()
    return summary


def readback_snapshot(
    root: Path,
    snapshot_id: str,
    repository: str,
    password: str,
    key_id: str | None = None,
    app_key: str | None = None,
    run=None,
    binary: str | None = None,
) -> dict[str, object]:
    bag = SecretBag()
    bag.add(password)
    bag.add(key_id)
    bag.add(app_key)
    bag.add(repository)
    env = restic_env(repository, password, key_id, app_key)
    command_run = run or (
        lambda args, cmd_env: run_command(restic_command(args, binary), cmd_env)
    )
    listed = snapshot_paths(command_run, env, snapshot_id, bag)
    files = [rel for rel, path in iter_names(root) if path.is_file() and not path.is_symlink()]
    samples = choose_samples(files)
    checked = 0
    matched = 0
    for rels in samples.values():
        for rel in rels:
            snap_path = match_snapshot_path(root, rel, listed)
            proc = command_run(["dump", snapshot_id, snap_path], env)
            if proc.returncode != 0:
                raise RecoveryError("restic dump failed: " + bag.scrub(proc.stderr)[:300], code=4)
            source_size, source_hash = sha256_file(root / rel)
            dumped = hashlib.sha256(proc.stdout).hexdigest()
            checked += 1
            if len(proc.stdout) == source_size and dumped == source_hash:
                matched += 1
    return {"checked": checked, "byte_matches": matched}


def restore_check(
    root: Path,
    snapshot_id: str,
    repository: str,
    password: str,
    key_id: str | None = None,
    app_key: str | None = None,
    target: Path | None = None,
    run=None,
    binary: str | None = None,
    cleanup: bool = False,
) -> dict[str, object]:
    created = target is None
    destination = target or Path(tempfile.mkdtemp(prefix="if-3b-b1-restore-"))
    assert_isolated_target(destination, root)
    if not created and (destination.exists() or destination.is_symlink()):
        raise RecoveryError("restore target must be a new path")
    destination.mkdir(parents=True, exist_ok=True)
    os.chmod(destination, 0o700)
    bag = SecretBag()
    bag.add(password)
    bag.add(key_id)
    bag.add(app_key)
    bag.add(repository)
    env = restic_env(repository, password, key_id, app_key)
    command_run = run or (
        lambda args, cmd_env: run_command(restic_command(args, binary), cmd_env)
    )
    try:
        proc = command_run(["restore", snapshot_id, "--target", str(destination)], env)
        if proc.returncode != 0:
            raise RecoveryError("restic restore failed: " + bag.scrub(proc.stderr)[:400], code=4)
        restored = restored_root(destination, root)
        if not restored.is_dir():
            raise RecoveryError("isolated restore did not contain the vault tree", code=4)
        for dirname in SAMPLE_DIRS.values():
            if not (root / dirname).is_dir() or not (restored / dirname).is_dir():
                raise RecoveryError("required sample tree is missing from the isolated restore", code=4)
        comparison = compare_trees(root, restored)
        files = [rel for rel, path in iter_names(root) if path.is_file() and not path.is_symlink()]
        samples = choose_samples(files)
        structure = sample_structure(root, restored, samples)
        ok = (
            comparison["missing"] == 0
            and comparison["extra"] == 0
            and comparison["mismatched"] == 0
            and structure["checked"] == structure["matched"]
            and structure["checked"] > 0
        )
        if not ok:
            raise RecoveryError("isolated restore did not match the source tree", code=4)
        return {
            "isolated": True,
            "restore_path": str(destination),
            "comparison": comparison,
            "structure": structure,
            "samples": {label: len(rels) for label, rels in samples.items()},
        }
    finally:
        if cleanup:
            remove_tree(destination, root)


def remove_tree(path: Path, vault: Path) -> None:
    resolved = assert_isolated_target(path, vault)
    if resolved.exists():
        shutil.rmtree(resolved)


def write_evidence(path: Path, payload: dict, repo_root: Path = PLUGIN_ROOT) -> None:
    resolved = assert_outside_repo(path, repo_root)
    resolved.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(resolved, 0o600)


def emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def default_evidence_path() -> Path:
    return (
        Path.home()
        / "Library/Application Support/information-flow/recovery/3b-b1-evidence.json"
    )


def local_repository_path(repository: str, root: Path) -> str:
    candidate = Path(repository).expanduser()
    if not candidate.is_absolute() or candidate.resolve() != candidate.absolute():
        raise RecoveryError("local repository must be an absolute, non-symlink path")
    resolved = assert_outside_repo(candidate)
    assert_isolated_target(resolved, root)
    volumes = Path("/Volumes")
    if volumes not in resolved.parents:
        raise RecoveryError("local repository must be on a mounted volume")
    parts = resolved.relative_to(volumes).parts
    if len(parts) < 3:
        raise RecoveryError("local repository needs a dedicated directory on the volume")
    volume = volumes / parts[0]
    if not os.path.ismount(volume):
        raise RecoveryError("local repository volume is not mounted")
    if resolved == Path(resolved.anchor) or resolved == Path.home():
        raise RecoveryError("local repository path is too broad")
    if resolved.exists() and not resolved.is_dir():
        raise RecoveryError("local repository path is not a directory")
    return str(resolved)


def load_runtime(
    keychain: Path | None, repository_arg: str | None = None, root: Path | None = None
) -> tuple[KeychainStore, str, str, str | None, str | None]:
    store = KeychainStore(keychain=keychain)
    if repository_arg is not None:
        if root is None:
            raise RecoveryError("vault root is required for a local repository")
        repository = local_repository_path(repository_arg, root)
        password = ensure_restic_password(store)
        return store, password, repository, None, None
    key_id = store.get("b2-key-id")
    app_key = store.get("b2-application-key")
    if not key_id or not app_key:
        raise RecoveryError(
            "missing keychain accounts b2-key-id and b2-application-key "
            f"in service {KEYCHAIN_SERVICE}"
        )
    repository = resolve_repository(store)
    password = ensure_restic_password(store)
    return store, password, repository, key_id, app_key


def public_summary(payload: dict) -> dict[str, object]:
    hidden = {"repository", "password", "key_id", "app_key", "authorizationToken"}
    return {key: value for key, value in payload.items() if key not in hidden}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vault_recovery.py")
    parser.add_argument("--keychain", type=Path)
    sub = parser.add_subparsers(dest="cmd", required=True)

    scan = sub.add_parser("scan")
    scan.add_argument("--root", type=Path, required=True)

    read = sub.add_parser("read")
    read.add_argument("--root", type=Path, required=True)
    read.add_argument("--workers", type=int, default=4)

    for name in ("snapshot", "readback", "restore-check"):
        command = sub.add_parser(name)
        command.add_argument("--root", type=Path, required=True)
        command.add_argument("--repository", help="absolute path to a local restic repository")
        command.add_argument("--evidence", type=Path)
        if name != "snapshot":
            command.add_argument("--snapshot", required=True)
        if name == "restore-check":
            command.add_argument("--target", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        keychain = None
        if args.keychain is not None:
            keychain = assert_outside_repo(args.keychain)
        if args.cmd == "scan":
            root = assert_backup_root(args.root)
            report = scan_tree(root)
            payload = report.to_json()
            payload["git"] = git_status_counts(root)
            emit(payload)
            return 0 if report.ok else 3
        if args.cmd == "read":
            root = assert_backup_root(args.root)
            before = git_status_counts(root)

            def progress(done: int, _ok: bool) -> None:
                print(f"read files={done}", file=sys.stderr)

            report = read_tree(root, workers=max(1, args.workers), progress=progress)
            after = git_status_counts(root)
            payload = report.to_json()
            payload["git_before"] = before
            payload["git_after"] = after
            payload["git_status_preserved"] = before == after
            emit(payload)
            if before != after:
                return 3
            return 0 if report.ok else 3
        root = assert_backup_root(args.root)
        evidence = args.evidence or default_evidence_path()
        if args.cmd == "snapshot":
            before = git_status_counts(root)

            def snapshot_progress(done: int, _ok: bool) -> None:
                print(f"read files={done}", file=sys.stderr)

            report = read_tree(root, workers=4, progress=snapshot_progress)
            after_read = git_status_counts(root)
            if not report.ok or before != after_read:
                payload = report.to_json()
                payload["git_before"] = before
                payload["git_after_read"] = after_read
                payload["git_status_preserved"] = before == after_read
                emit(payload)
                return 3
            _store, password, repository, key_id, app_key = load_runtime(
                keychain, args.repository, root
            )
            summary = backup_snapshot(
                root,
                repository,
                password,
                key_id,
                app_key,
                preflight=report,
            )
            after = git_status_counts(root)
            payload = public_summary(summary)
            payload["git_before"] = before
            payload["git_after"] = after
            payload["git_status_preserved"] = before == after
            remote = repository.startswith("s3:")
            if remote:
                payload["bucket_checked_private"] = True
            write_evidence(
                evidence,
                {
                    **payload,
                    "password_in_keychain": True,
                    "repository_recorded_in_keychain": remote,
                },
            )
            emit(payload)
            if before != after:
                return 4
            return 0
        _store, password, repository, key_id, app_key = load_runtime(
            keychain, args.repository, root
        )
        if args.cmd == "readback":
            payload = readback_snapshot(
                root, args.snapshot, repository, password, key_id, app_key
            )
            payload["snapshot_id"] = args.snapshot
            emit(payload)
            write_evidence(evidence, payload)
            if payload["checked"] != payload["byte_matches"] or payload["checked"] == 0:
                return 4
            return 0
        result = restore_check(
            root,
            args.snapshot,
            repository,
            password,
            key_id,
            app_key,
            target=args.target,
        )
        result["snapshot_id"] = args.snapshot
        emit(result)
        write_evidence(evidence, result)
        return 0
    except RecoveryError as exc:
        print(str(exc), file=sys.stderr)
        return exc.code


if __name__ == "__main__":
    sys.exit(main())
