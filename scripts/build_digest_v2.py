#!/usr/bin/env python3
"""Write one cycle digest snapshot from the Thursday batch and the index.

Reads ``{vault}/📋 Digests/cycles/{cycle_id}/batch.json`` and the inbox index.
Writes ``{vault}/📋 Digests/cycles/{cycle_id}/r{n}.md``. Does not select inputs,
does not append state, and does not rewrite ``batch.json``.

``input_ids`` are ``selected_input_ids`` in batch order. ``counts`` has every
``process_state`` plus ``total``. The state keys sum to ``total``, and
``total`` is ``len(input_ids)``. ``completed`` is the AC06 "ready" bucket.

An id is in ``late_or_cross_week`` when its ``received_at`` is after
``cutoff_at``, or its ``source_week`` is set and is not the ISO week of the
cycle date. Ids that missed this batch stay in ``late_input_ids`` and are not
listed.

``D-{cycle_id}-{nn}`` follows selected order and stays fixed for the cycle.
Items with no topic are listed under 「待归类」. A later run writes ``r{n+1}``
only when the snapshot changed. Existing ``r{n}.md`` bytes are left as they
are (AC07).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import inbox_lib
from inbox_index import PROCESS_STATES, read_index
from process_batch import batch_path

SCHEMA_VERSION = "digest-2.0"
DIGEST_TYPE = "cycle-digest"
GENERATOR = "build_digest_v2"
UNTAGGED = "待归类"
FAILED_SECTION = "失败和不完整"
HISTORY_SECTION = "历史关联（只放链接）"
SOURCE_SECTION = "本批来源统计（哪个来源是 0）"
CYCLE_RE = re.compile(r"^cy-(?P<y>\d{4})(?P<m>\d{2})(?P<d>\d{2})$")
REVISION_NAME = re.compile(r"^r(\d+)\.md$")
_REVISION_LINE = re.compile(r"(?m)^snapshot_revision:.*$")
_GENERATED_LINE = re.compile(r"(?m)^generated_at:.*$")


def build_digest(
    vault: Path,
    index_dir: Path,
    cycle_id: str,
    *,
    at: str | None = None,
) -> dict:
    """Write the next digest revision for ``cycle_id`` when the snapshot changed."""

    cycle_id = _cycle_id(cycle_id)
    batch = _load_batch(vault, cycle_id)
    stamp = _stamp(at) if at else inbox_lib.format_hk(datetime.now(inbox_lib.HK))
    sources, inputs = read_index(index_dir)
    rows = _rows(vault, batch, sources, inputs, cycle_id)
    fields = _fields(batch, rows, cycle_id, stamp, revision=1)
    directory = batch_path(vault, cycle_id).parent
    existing = _existing_revisions(directory)
    revision = 1 if not existing else existing[-1][0] + 1
    fields["snapshot_revision"] = revision
    text = _render(fields, rows)
    if existing and _material(existing[-1][1].read_text(encoding="utf-8")) == _material(text):
        return _payload(existing[-1][1], written=False)
    path = digest_path(vault, cycle_id, revision)
    _write_new(path, text)
    return _payload(path, written=True)


def digest_path(vault: Path, cycle_id: str, revision: int) -> Path:
    if revision < 1:
        raise ValueError(f"snapshot_revision must be >= 1: {revision}")
    return batch_path(vault, _cycle_id(cycle_id)).parent / f"r{revision}.md"


def _rows(
    vault: Path,
    batch: dict,
    sources: list[dict],
    inputs: list[dict],
    cycle_id: str,
) -> list[dict]:
    by_id = {item["input_id"]: item for item in inputs if isinstance(item.get("input_id"), str)}
    by_source = {
        item["source_id"]: item for item in sources if isinstance(item.get("source_id"), str)
    }
    cutoff = _moment(batch["cutoff_at"], "cutoff_at")
    cycle_week = _cycle_week(cycle_id)
    rows: list[dict] = []
    for index, input_id in enumerate(batch["selected_input_ids"], start=1):
        item = by_id.get(input_id)
        if item is None:
            raise ValueError(f"unknown input_id: {input_id}")
        state = item.get("process_state")
        if state not in PROCESS_STATES:
            raise ValueError(f"input {input_id} process_state must be one of {PROCESS_STATES}")
        source = by_source.get(item.get("source_id"))
        received = _moment(item.get("received_at"), f"input {input_id} received_at")
        week = item.get("source_week")
        cross_week = isinstance(week, str) and bool(week) and week != cycle_week
        url = _url(source)
        origin = item.get("origin")
        rows.append(
            {
                "input_id": input_id,
                "d_id": f"D-{cycle_id}-{index:02d}",
                "summary": _summary(vault, item.get("summary_ref")),
                "url": url,
                "state": state,
                "flagged": received > cutoff or cross_week,
                "topics": _topics(item.get("topics"), input_id),
                "failed_or_incomplete": state == "failed" or _incomplete(item.get("completeness")),
                "history_url": url if origin == "historical_import" else "",
                "platform": _platform(item, source),
                "source_week": week if isinstance(week, str) and week else None,
            }
        )
    return rows


def _fields(batch: dict, rows: list[dict], cycle_id: str, generated_at: str, *, revision: int) -> dict:
    counts = {state: 0 for state in PROCESS_STATES}
    weeks: dict[str, int] = {}
    for row in rows:
        counts[row["state"]] += 1
        week = row["source_week"]
        if week is not None:
            weeks[week] = weeks.get(week, 0) + 1
    counts["total"] = len(rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "type": DIGEST_TYPE,
        "digest_id": f"dg-{cycle_id}",
        "cycle_id": cycle_id,
        "coverage_start": batch["coverage_start"],
        "cutoff_at": batch["cutoff_at"],
        "snapshot_revision": revision,
        "input_ids": [row["input_id"] for row in rows],
        "source_weeks": {week: weeks[week] for week in sorted(weeks)},
        "counts": counts,
        "late_or_cross_week": [row["input_id"] for row in rows if row["flagged"]],
        "generated_at": generated_at,
        "generator": GENERATOR,
    }


def _render(fields: dict, rows: list[dict]) -> str:
    sections: list[str] = ["---", _frontmatter(fields), "---", ""]
    grouped: dict[str, list[str]] = {}
    untagged: list[str] = []
    for row in rows:
        line = _line(row)
        if not row["topics"]:
            untagged.append(line)
            continue
        for topic in row["topics"]:
            grouped.setdefault(topic, []).append(line)
    for topic, lines in grouped.items():
        sections.append(f"## {topic}")
        sections.append("")
        sections.extend(lines)
        sections.append("")
    sections.append(f"## {UNTAGGED}")
    sections.append("")
    sections.extend(untagged)
    sections.append("")
    sections.append(f"## {FAILED_SECTION}")
    sections.append("")
    sections.extend(_line(row) for row in rows if row["failed_or_incomplete"])
    sections.append("")
    sections.append(f"## {HISTORY_SECTION}")
    sections.append("")
    sections.extend(_history_links(rows))
    sections.append("")
    sections.append(f"## {SOURCE_SECTION}")
    sections.append("")
    sections.extend(_source_lines(rows))
    sections.append("")
    return "\n".join(sections)


def _line(row: dict) -> str:
    link = f"`{row['url']}`" if row["url"] else ""
    flag = "是" if row["flagged"] else "否"
    return f"{row['d_id']}｜{row['summary']}｜{link}｜{row['state']}｜{flag}"


def _history_links(rows: list[dict]) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()
    for row in rows:
        url = row["history_url"]
        if not url or url in seen:
            continue
        seen.add(url)
        links.append(url)
    return links


def _source_lines(rows: list[dict]) -> list[str]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["platform"]] = counts.get(row["platform"], 0) + 1
    lines = [f"{name}: {counts.get(name, 0)}" for name in inbox_lib.PLATFORMS]
    extra = sorted(set(counts) - set(inbox_lib.PLATFORMS))
    lines.extend(f"{name}: {counts[name]}" for name in extra)
    return lines


def _frontmatter(fields: dict) -> str:
    lines = [
        f"schema_version: {_quote(fields['schema_version'])}",
        f"type: {_quote(fields['type'])}",
        f"digest_id: {_quote(fields['digest_id'])}",
        f"cycle_id: {_quote(fields['cycle_id'])}",
        f"coverage_start: {_quote(fields['coverage_start'])}",
        f"cutoff_at: {_quote(fields['cutoff_at'])}",
        f"snapshot_revision: {fields['snapshot_revision']}",
    ]
    lines.extend(_yaml_list("input_ids", fields["input_ids"]))
    lines.extend(_yaml_map("source_weeks", fields["source_weeks"]))
    lines.extend(_yaml_map("counts", fields["counts"]))
    lines.extend(_yaml_list("late_or_cross_week", fields["late_or_cross_week"]))
    lines.append(f"generated_at: {_quote(fields['generated_at'])}")
    lines.append(f"generator: {_quote(fields['generator'])}")
    return "\n".join(lines)


def _yaml_list(key: str, values: list[str]) -> list[str]:
    if not values:
        return [f"{key}: []"]
    return [f"{key}:"] + [f"  - {_quote(item)}" for item in values]


def _yaml_map(key: str, values: dict) -> list[str]:
    if not values:
        return [f"{key}: {{}}"]
    lines = [f"{key}:"]
    for name, value in values.items():
        rendered = value if isinstance(value, int) else _quote(value)
        lines.append(f"  {_quote(str(name))}: {rendered}")
    return lines


def _quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _summary(vault: Path, summary_ref: object) -> str:
    if not isinstance(summary_ref, str) or not summary_ref.strip():
        return ""
    text = summary_ref.strip()
    if _looks_like_ref(text):
        return _excerpt(vault, text)
    return re.sub(r"\s+", " ", text.splitlines()[0].strip())


def _looks_like_ref(text: str) -> bool:
    head = text.split("#", 1)[0]
    return head.endswith(".md") or head.startswith("📥") or "/" in head


def _excerpt(vault: Path, ref: str) -> str:
    relative = ref.split("#", 1)[0]
    path = vault / relative
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            body = text[end + 4 :]
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return re.sub(r"\s+", " ", stripped)
    return ""


def _topics(raw: object, input_id: str) -> list[str]:
    if raw is None:
        return []
    values = [raw] if isinstance(raw, str) else raw
    if not isinstance(values, list):
        raise ValueError(f"input {input_id} topics must be a list of strings")
    names: list[str] = []
    for topic in values:
        if topic is None:
            continue
        if not isinstance(topic, str):
            raise ValueError(f"input {input_id} topics must be a list of strings")
        cleaned = topic.strip()
        if cleaned:
            names.append(cleaned)
    return names


def _incomplete(completeness: object) -> bool:
    return isinstance(completeness, str) and completeness != "" and completeness != "full"


def _url(source: dict | None) -> str:
    if source is None:
        return ""
    url = source.get("canonical_url")
    if not isinstance(url, str):
        return ""
    return url.strip()


def _platform(item: dict, source: dict | None) -> str:
    if source is not None and isinstance(source.get("platform"), str) and source["platform"]:
        return source["platform"]
    for key in ("source_id", "input_id"):
        raw = item.get(key)
        if isinstance(raw, str) and "-" in raw:
            prefix, platform, *_rest = raw.split("-")
            if prefix in {"src", "in"} and platform:
                return platform
    return "unknown"


def _load_batch(vault: Path, cycle_id: str) -> dict:
    path = batch_path(vault, cycle_id)
    if not path.is_file():
        raise ValueError(f"batch.json is missing: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path.name} is not json") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} is not an object")
    if data.get("cycle_id") != cycle_id:
        raise ValueError("batch.json cycle_id conflicts with this run")
    for key in ("cutoff_at", "coverage_start"):
        if not isinstance(data.get(key), str):
            raise ValueError(f"batch.json {key} must be a timestamp")
    selected = data.get("selected_input_ids")
    if not isinstance(selected, list) or not all(isinstance(item, str) and item for item in selected):
        raise ValueError("batch.json selected_input_ids must be a list of ids")
    return data


def _existing_revisions(directory: Path) -> list[tuple[int, Path]]:
    if not directory.is_dir():
        return []
    found: list[tuple[int, Path]] = []
    for path in directory.iterdir():
        match = REVISION_NAME.match(path.name)
        if match and path.is_file():
            found.append((int(match.group(1)), path))
    found.sort(key=lambda item: item[0])
    return found


def _material(text: str) -> str:
    text = _REVISION_LINE.sub("snapshot_revision: 0", text, count=1)
    return _GENERATED_LINE.sub('generated_at: ""', text, count=1)


def _payload(path: Path, *, written: bool) -> dict:
    text = path.read_text(encoding="utf-8")
    fields = _parse_frontmatter(text)
    fields["written"] = written
    fields["path"] = str(path)
    return fields


def _parse_frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        raise ValueError("digest is missing frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("digest is missing frontmatter")
    raw = text[4:end]
    data: dict = {}
    key: str | None = None
    mode: str | None = None
    for line in raw.splitlines():
        if line.startswith("  - ") and mode in {"list", "block"} and key is not None:
            if mode == "block":
                data[key] = []
                mode = "list"
            data[key].append(json.loads(line[4:]))
            continue
        if line.startswith("  ") and mode in {"map", "block"} and key is not None and ":" in line:
            if mode == "block":
                data[key] = {}
                mode = "map"
            name, value = line.strip().split(":", 1)
            data[key][json.loads(name.strip())] = _yaml_value(value.strip())
            continue
        if ":" not in line:
            raise ValueError("digest frontmatter is not readable")
        name, value = line.split(":", 1)
        key = name.strip()
        value = value.strip()
        if value == "":
            data[key] = None
            mode = "block"
            continue
        if value == "{}":
            data[key] = {}
            mode = "map"
            continue
        if value == "[]":
            data[key] = []
            mode = None
            continue
        if value.startswith("{") or value.startswith("["):
            raise ValueError("digest frontmatter is not readable")
        data[key] = _yaml_value(value)
        mode = None
    for name in ("input_ids", "late_or_cross_week"):
        if not isinstance(data.get(name), list):
            raise ValueError(f"digest {name} must be a list")
    if not isinstance(data.get("counts"), dict) or not isinstance(data.get("source_weeks"), dict):
        raise ValueError("digest counts must be a map")
    return data


def _yaml_value(raw: str):
    if raw[:1] == '"':
        return json.loads(raw)
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    raise ValueError(f"digest frontmatter value is not readable: {raw}")


def _write_new(path: Path, text: str) -> None:
    if path.exists():
        raise ValueError(f"{path.name} already exists; not rewriting")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".md.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _cycle_id(cycle_id: str) -> str:
    _cycle_day(cycle_id)
    return cycle_id


def _cycle_day(cycle_id: str) -> datetime:
    match = CYCLE_RE.match(cycle_id)
    if match is None:
        raise ValueError(f"cycle_id must look like cy-YYYYMMDD: {cycle_id}")
    try:
        return datetime(int(match.group("y")), int(match.group("m")), int(match.group("d")))
    except ValueError as exc:
        raise ValueError(f"cycle_id must look like cy-YYYYMMDD: {cycle_id}") from exc


def _cycle_week(cycle_id: str) -> str:
    day = _cycle_day(cycle_id)
    week = inbox_lib.source_week_for(day.strftime("%Y-%m-%dT00:00:00+08:00"), "platform")
    if week is None:
        raise ValueError(f"cycle_id must look like cy-YYYYMMDD: {cycle_id}")
    return week


def _moment(raw: object, label: str) -> datetime:
    moment = inbox_lib.parse_time(raw) if isinstance(raw, str) else None
    if moment is None:
        raise ValueError(f"{label} must include a date")
    return moment


def _stamp(raw: str) -> str:
    return inbox_lib.format_hk(_moment(raw, "timestamp"))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write a cycle digest snapshot from batch.json.")
    parser.add_argument("--vault", required=True, help="Vault root for 📋 Digests/cycles")
    parser.add_argument("--index", required=True, help="Directory with inputs.jsonl")
    parser.add_argument("--cycle-id", required=True, help="cy-YYYYMMDD Thursday")
    parser.add_argument("--at", default=None, help="Clock for generated_at. Default: now in Hong Kong")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        digest = build_digest(Path(args.vault), Path(args.index), args.cycle_id, at=args.at)
    except ValueError as exc:
        json.dump({"ok": False, "error": str(exc)}, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
        return 1
    json.dump({"ok": True, "digest": digest}, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
