#!/usr/bin/env python3
"""Fill the launchd templates in ../launchd with values from an env file.

Usage: render_launchd.py --env deploy.env --out rendered/

The env file has one KEY=VALUE per line; KEY is a placeholder such as __HOME__.
Lines starting with # and blank lines are ignored. Values are used verbatim
(spaces allowed, no quoting). Rendering fails if a template keeps a placeholder
or the env file names a placeholder no template uses. Nothing is installed or
loaded; copying into ~/Library/LaunchAgents is a separate, manual step.

Stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE.parent / "launchd"
PLACEHOLDER = re.compile(r"__[A-Z][A-Z0-9_]*__")


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = raw.partition("=")
        key = key.strip()
        if not sep or not PLACEHOLDER.fullmatch(key):
            raise SystemExit(f"{path}:{n}: expected __NAME__=value")
        if not value:
            raise SystemExit(f"{path}:{n}: empty value for {key}")
        values[key] = value
    return values


def render(text: str, values: dict[str, str]) -> str:
    out = PLACEHOLDER.sub(lambda m: values.get(m.group(0), m.group(0)), text)
    left = sorted(set(PLACEHOLDER.findall(out)))
    if left:
        raise SystemExit(f"unfilled placeholders: {', '.join(left)}")
    return out


def render_all(values: dict[str, str]) -> dict[str, str]:
    rendered: dict[str, str] = {}
    used: set[str] = set()
    for tpl in sorted(TEMPLATES.glob("*.plist")):
        text = tpl.read_text(encoding="utf-8")
        used.update(PLACEHOLDER.findall(text))
        rendered[tpl.name] = render(text, values)
    unused = sorted(set(values) - used)
    if unused:
        raise SystemExit(f"env names placeholders no template uses: {', '.join(unused)}")
    return rendered


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--env", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)
    rendered = render_all(read_env(args.env))
    args.out.mkdir(parents=True, exist_ok=True)
    for name, text in rendered.items():
        data = text.encode("utf-8")
        (args.out / name).write_bytes(data)
        print(f"{hashlib.sha256(data).hexdigest()}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
