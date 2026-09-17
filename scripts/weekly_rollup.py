#!/usr/bin/env python3
"""Rewrite Briefing on this week's intake.md and sink checked items. No Hermes."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from weekly_intake import iso_week, refresh_intake  # noqa: E402

SHANGHAI = ZoneInfo("Asia/Shanghai")
DEFAULT_VAULT = (
    Path.home()
    / "Library/Mobile Documents/iCloud~md~obsidian/Documents/DigitalBrain"
)
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = PLUGIN_ROOT / "state"


def vault_path(raw: str | None) -> Path:
    return Path(raw).expanduser() if raw else DEFAULT_VAULT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh Briefing and sink [x] on weekly intake.md")
    parser.add_argument("--date", help="YYYY-MM-DD in the target ISO week (default: today Asia/Shanghai)")
    parser.add_argument("--vault")
    parser.add_argument("--force", action="store_true", help="ignored; never overwrites a non-generated file")
    args = parser.parse_args(argv)

    vault = vault_path(args.vault)
    today = dt.datetime.now(SHANGHAI).date()
    day = dt.date.fromisoformat(args.date) if args.date else today
    week = iso_week(day)

    if not vault.is_dir():
        print(f"vault missing: {vault}", file=sys.stderr)
        return 1

    result = refresh_intake(vault, week)
    if not result["wrote"]:
        print(f"skip {week} (no intake.md)")
        return 0

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with (STATE_DIR / "weekly-rollup.log").open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "ran_at": dt.datetime.now(SHANGHAI).isoformat(),
                    "week": week,
                    "path": result["path"],
                    "item_count": result.get("item_count"),
                    "open_count": result.get("open_count"),
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    print(
        f"wrote {result['path']} items={result.get('item_count')} open={result.get('open_count')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
