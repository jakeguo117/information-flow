#!/usr/bin/env python3
"""Deterministic Cognition retrieval. Prints a JSON result contract to stdout."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cognition_lib import retrieve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Retrieve DigitalBrain Cognition")
    parser.add_argument("--vault", required=True)
    parser.add_argument("--query", default="")
    parser.add_argument("--project", default="")
    parser.add_argument("--domain", default="")
    parser.add_argument("--id", action="append", dest="ids", default=[])
    parser.add_argument("--principle-budget", type=int, default=3)
    parser.add_argument("--belief-budget", type=int, default=3)
    parser.add_argument("--evidence-budget", type=int, default=5)
    args = parser.parse_args(argv)

    vault = Path(args.vault).expanduser()
    if not args.query and not args.ids:
        print("retrieve_cognition.py: --query or --id is required", file=sys.stderr)
        payload = retrieve(vault, query="", ids=[])
        payload["status"] = "unavailable" if payload["status"] == "unavailable" else payload["status"]
        if payload["status"] != "unavailable":
            payload["status"] = "no_match"
            payload["errors"].append("empty query")
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 1

    payload = retrieve(
        vault,
        query=args.query,
        project=args.project,
        domain=args.domain,
        ids=args.ids,
        principle_budget=args.principle_budget,
        belief_budget=args.belief_budget,
        evidence_budget=args.evidence_budget,
    )
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if payload["status"] != "unavailable" else 2


if __name__ == "__main__":
    raise SystemExit(main())
