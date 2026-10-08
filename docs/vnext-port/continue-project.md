# continue_project mapping

This file is the VNext port mapping. It does not add a webhook or a GPT event endpoint.

Track C adds a separate on-request wrapper for Grok Bot. See `continue-project-trackc.md`. That wrapper is not a webhook, and it does not close R10-14 or R10-16. The library `main()` still refuses a CLI call. The wrapper is `scripts/vnext/continue_caller.py`.

Settled entry points (owner decision 2026-10-08):

- Journal formal entry is GPT Cloud Work.
- Project resume is a new GPT conversation given the project name or link only, plus Grok reading the same approved version.

VNext rules that relate to resume are mapped in `docs/vnext-port/RULE-MAP.md` (WI-REQ-014, 032, 035, 037, 038). The durable fields a reader must be able to recover are in `specs/vnext/requirements.md`. They are not a product surface.

The existing local chain in `scripts/continue_project.py` remains Global Governance, PROJECT_CONTROL, PROJECT_MILESTONE_MAP, frozen authority or approved Manifest, verified repo SHA, and minimum DigitalBrain context. Callers inject those inputs. An explicit `repo_verification.required: false` records the repository step as skipped and does not invent a SHA. The default remains required. This port does not wire VNext events into that function.
