# Weekly brief builder

`scripts/wj_weekly_brief.py` builds one discussion draft per ISO week. Callers pass the week label, the current inbox rows, and optionally the previous brief's markdown. The function returns the new brief as a string.

## What it does

- `iso_week_label(date)` returns `YYYY-Www` using ISO 8601 (`date.isocalendar`), Monday through Sunday. A `datetime.date` is the calendar date. Aware datetimes are converted to Asia/Shanghai first; naive datetimes are Shanghai wall time. This is the same week label as `scripts/weekly_intake.py`.
  - `2026-01-01` → `2026-W01`
  - `2026-10-05` → `2026-W41`
  - `2026-10-12` → `2026-W42`
  - `2027-01-01` → `2026-W53`
- `brief_rel_path(week_label)` returns the path string `📋 Digests/weekly-briefs/{week_label}.md`. It does not create directories or files.
- `STATUSES` is exactly `待讨论`, `已讨论`, `暂缓`, `来源缺失/失败`.
- `build_brief` groups the current week's rows by topic under `## 本周索引`. Each row shows its id, source week, source link, an empty `讨论线索` slot, and the status literal. Order is topic, then id.
- Rows from the previous brief that are not `已讨论` are listed under `## 遗留候选`. `待讨论`, `暂缓`, and `来源缺失/失败` all carry forward. The original source week, source link, and status are copied. They are not dropped, not marked `已讨论`, and not repeated in the current-week index. The same rule keeps an undiscussed row whose `source_week` is an earlier week. A later week still shows the earliest source week.
- `来源缺失/失败` is rendered as id, source week, source link, and status only. The builder has no source text, so it writes no summary.

The printed brief starts with: 讨论草稿。外部作者观点不是 Jake 的信念.

## What it does not do

- It does not write the vault, this repo, or any other file. It does not read Inbox, Digests, or source notes. Stdin JSON is optional and is only a way to print the same string.
- It does not open network connections and does not call a model.
- It does not invent a summary when a source is missing or failed, and it does not fill `讨论线索` from source content.
- The brief is a discussion draft. Views that later get quoted from external authors are not Jake's beliefs.
- Saving or pushing a journal, and confirming anything into Cognition, stay behind their own gates. This script does not call `write_journal.py` or the cognition tools.
