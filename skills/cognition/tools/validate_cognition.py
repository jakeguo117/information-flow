#!/usr/bin/env python3
"""Canonical Cognition validator. Exit 0 if valid, non-zero on schema/structure errors."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cognition_lib import load_store, parse_markdown, validate_docs, validate_store


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate DigitalBrain Cognition Markdown")
    parser.add_argument("--vault", required=True)
    parser.add_argument("--file", help="validate one proposed Markdown file against the store")
    args = parser.parse_args(argv)

    vault = Path(args.vault).expanduser()
    store = load_store(vault)
    if args.file:
        path = Path(args.file).expanduser()
        if not path.is_file():
            print(f"{path}: missing file", file=sys.stderr)
            return 1
        proposed = parse_markdown(path.read_text(encoding="utf-8"), path)
        docs = [doc for doc in store.docs if doc.id != proposed.id]
        docs.append(proposed)
        errors = validate_docs(docs, store.outside)
    else:
        errors = validate_store(store)

    if errors:
        for item in errors:
            print(item, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
