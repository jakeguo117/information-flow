# Track C continue_project caller

Grok Bot is the only caller. It runs this on request, when someone asks to continue a project. There is no cron, launchd job, GitHub Action, or webhook.

The wrapper serves two adapters with the same code:

- `AI-AGENTS-COOPERATE` requires a repository SHA.
- `AIC-PRJ-0002-HK-INS-FOLLOWUP` has no business repository. The repository step is skipped. It is not marked blocked for that reason.

This does not close R10-14 or R10-16. A synthetic run is not a real Grok Bot session, and it is not an acceptance PASS.

## Call

From the repository root:

```bash
python3 scripts/vnext/continue_caller.py \
  --adapter scripts/vnext/adapters/ai-agents-cooperate.json \
  --board-dir /path/to/local-board \
  < scripts/vnext/fixtures/syn_aic_ready.json
```

The project #2 adapter is `scripts/vnext/adapters/aic-prj-0002-hk-ins-followup.json`. Its synthetic payload is `scripts/vnext/fixtures/syn_prj0002_ready.json`.

Stdin is one JSON object. Stdout is one JSON object. The process exits 0 when the JSON result was produced, including when `status` is `blocked`. It exits 1 when the input is not JSON or the board rejects the event.

Required input fields:

| Field | Meaning |
| --- | --- |
| `project_id` | Must equal the adapter's `project_id`. |
| `request_ref` | Opaque session id. No message text. |
| `occurred_at` | Optional ISO time with `+08:00`. The clock is Asia/Shanghai. |
| `readbacks` | Evidence the caller already read. |

A read-back counts only when `readable` is true and it carries `project_id`, `revision`, and a 64-character `sha256`. Governance, project control, and the manifest also need `drive_file_id`. The manifest is approved only when `revision` and `sha256` equal `expected_revision` and `expected_sha256`, and a separate `approval` read-back is present. A bare `approved: true` or `availability: present` is ignored.

The repository read-back, when the adapter says `repo_step` is `required`, counts only with `readable: true` and a 40-character `sha`. A self-reported `status: verified` without that sha is unverified.

## What Grok Bot does

1. Resolve the project from the name or link the person supplied.
2. Read the pinned documents and, for project #2, the context source. Keep page ids, status codes, and dates. Do not copy client content into this call.
3. Pass that evidence as `readbacks` with the matching adapter.
4. Read `status`, `gaps`, `bounded_next_action`, `consumed_pins`, and `project_id` from stdout.
5. The wrapper appends board events under `--board-dir`. A second call with the same effect key writes nothing and returns `no_op_duplicate`.

Project #2 event names follow `AIC-EVT-PRJ0002-<YYYYMMDD>T<HHMMSS>-<KIND>-<EFF8>.md`. The file body is JSON between `---` fences, using the genesis field names. Corrections are new `CORRECTION` events. Files are not overwritten.

The local directory store is what tests use. `DriveBoardStore` is an unwired stub with no credentials and no network call. Grok Bot supplies whatever store it has already authenticated. This repository does not attach Drive or Notion credentials.

## Result

`blocked` still outranks `unavailable` and `partial`. The result echoes `project_id`. It does not echo context body text. It does not invent a milestone or a SHA. When the repository step is skipped, `verified_sha` is absent and the action uses the adapter template (a due-item count for project #2).

`consumed_pins` lists the revision and sha256 that were actually accepted. `board_readback` is the event parsed back from the store after the write.

## Gaps this wrapper closes

| Gap | Where |
| --- | --- |
| G1 repository step required | Core accepts `repo_verification.required: false`. The project #2 adapter sets `repo_step: skip`. |
| G2 project id | Core echoes `project_id` when passed. The wrapper rejects a missing or mismatched id before any board write. |
| G3 manifest revision | Wrapper compares revision and sha256 with the expected pin and an approval pin. |
| G4 CLI | `scripts/vnext/continue_caller.py`. Core `main()` is still the library stub. |
| G5 board | `scripts/vnext/status_board.py`. |
| G6 effect key | Duplicate key writes nothing. |
| G7 action text | Adapter `success_template` and `unblock`. Core default text is unchanged for direct library calls. |
| G8 self-report | Wrapper marks a step present only after a read-back pin. |

## Decisions

- Plan Q2 is implemented as a skip, not as a fake SHA and not as a renamed parameter. Existing callers that omit `required` still fail closed when the sha is missing.
- New code lives under `scripts/vnext/` and `docs/vnext-port/` because those are the paths this batch is allowed to change. The plan's `scripts/aic_board/` layout was not used.
- Project #2 event bodies are JSON inside fences so the writer does not depend on a YAML parser. Field names and file names follow the genesis note.
- Project #2 success events use the genesis kinds (`SCOPE-SNAPSHOT`, `FOLLOWUP-DUE`, `PENDING-NO-DATE`, `BLOCKED`). `continue_result` is not added for that project.
- Effect keys for follow-up events are `sha256` of `project_id|event_kind|sorted page ids|business date|sorted status codes`, joined by `|`.
- The board whitelist is the schema union narrowed by each adapter's `allowed_event_fields`. Denied keys and contact-shaped strings are rejected. A rejected event is not written.
- Fixtures use tokens such as `crm-fake-0001` and `collection://crm-fake-source`. They are not real records.
- `specs/vnext/requirements.md` still describes the VNext import, which did not add a caller. This wrapper does not rewrite that historical requirement.
