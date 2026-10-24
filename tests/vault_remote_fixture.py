"""Give synthetic vaults a passing remote check without adding a second remote.

Vaults with no origin get origin set to the real data-vault URL. Vaults whose
origin is a local path (publish tests) keep that origin; the guard is patched
in-process for that directory only. information-flow remotes are not patched.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

_ORIG = None
_PATCHED_VAULTS: set[str] = set()
_SITE: Path | None = None

_SITE_CODE = '''import builtins
import os
from pathlib import Path

_VAULTS = {item for item in os.environ.get("INFOFLOW_FIXTURE_VAULTS", "").split("\\n") if item}
_real_import = builtins.__import__


def _patch(module):
    current = module.rejection
    if getattr(current, "_infoflow_fixture", False):
        return

    def rejection(vault):
        try:
            key = str(Path(vault).expanduser().resolve())
        except OSError:
            key = str(vault)
        if key in _VAULTS:
            return None
        return current(vault)

    rejection._infoflow_fixture = True
    module.rejection = rejection


def _import(name, globals=None, locals=None, fromlist=(), level=0):
    module = _real_import(name, globals, locals, fromlist, level)
    if name == "vault_guard":
        _patch(module)
    return module


builtins.__import__ = _import
'''


def _run():
    return _ORIG or subprocess.run


def _key(vault: Path) -> str:
    try:
        return str(Path(vault).expanduser().resolve())
    except OSError:
        return str(vault)


def _site_dir() -> str:
    global _SITE
    if _SITE is None:
        path = Path(tempfile.mkdtemp(prefix="infoflow-fixture-site-"))
        (path / "sitecustomize.py").write_text(_SITE_CODE, encoding="utf-8")
        _SITE = path
    return str(_SITE)


def _patch_inprocess() -> None:
    tools = Path(__file__).resolve().parents[1] / "skills" / "journal" / "tools"
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    import vault_guard

    current = vault_guard.rejection
    if getattr(current, "_infoflow_fixture", False):
        return

    def rejection(vault):
        try:
            key = str(Path(vault).expanduser().resolve())
        except OSError:
            key = str(vault)
        if key in _PATCHED_VAULTS:
            return None
        return current(vault)

    rejection._infoflow_fixture = True
    vault_guard.rejection = rejection


def stamp(vault: Path) -> None:
    vault = Path(vault).expanduser()
    if not vault.is_dir():
        return
    tools = Path(__file__).resolve().parents[1] / "skills" / "journal" / "tools"
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    import vault_guard

    if vault_guard.is_code_repo(vault):
        return
    run = _run()

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return run(
            ["git", "-C", str(vault), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    inside = git("rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        if git("init", "-b", "main").returncode != 0:
            return
    url = f"https://github.com/{vault_guard.DEFAULT_VAULT_REMOTE}.git"
    names = git("remote").stdout.split()
    if "origin" not in names:
        git("remote", "add", "origin", url)
        return
    current = git("remote", "get-url", "origin")
    if vault_guard.slug_of(current.stdout.strip()) == vault_guard.DEFAULT_VAULT_REMOTE:
        return
    if vault_guard.slug_of(current.stdout.strip()) is not None:
        return
    _PATCHED_VAULTS.add(_key(vault))
    _patch_inprocess()


def _vault_from_command(args: object) -> Path | None:
    if not isinstance(args, (list, tuple)):
        return None
    tokens = [str(item) for item in args]
    if "--vault" not in tokens:
        return None
    index = tokens.index("--vault")
    if index + 1 >= len(tokens):
        return None
    return Path(tokens[index + 1])


def _stamp_from_command(args: object) -> None:
    vault = _vault_from_command(args)
    if vault is not None:
        stamp(vault)


def install(*, writers: bool = False) -> None:
    global _ORIG
    if _ORIG is None:
        _ORIG = subprocess.run

        def run(args, *a, **kwargs):
            _stamp_from_command(args)
            vault = _vault_from_command(args)
            if vault is not None and _key(vault) in _PATCHED_VAULTS:
                kwargs = dict(kwargs)
                env = dict(kwargs["env"] if kwargs.get("env") is not None else os.environ)
                env["INFOFLOW_FIXTURE_VAULTS"] = "\n".join(sorted(_PATCHED_VAULTS))
                root = _site_dir()
                prior = env.get("PYTHONPATH", "")
                env["PYTHONPATH"] = root if not prior else root + os.pathsep + prior
                kwargs["env"] = env
            return _ORIG(args, *a, **kwargs)

        subprocess.run = run
    if not writers:
        return
    import thought_lib

    if getattr(thought_lib.add_thought, "_vault_stamped", False):
        return

    def wrap(fn):
        def wrapped(vault, *args, **kwargs):
            stamp(Path(vault))
            return fn(vault, *args, **kwargs)

        wrapped._vault_stamped = True
        return wrapped

    thought_lib.add_thought = wrap(thought_lib.add_thought)
    thought_lib.record_digest = wrap(thought_lib.record_digest)
    thought_lib.publish_exact = wrap(thought_lib.publish_exact)
