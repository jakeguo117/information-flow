# continue_project mapping

`scripts/continue_project.py` is unchanged. This port does not add a caller, a webhook, or a GPT event endpoint.

Settled entry points (owner decision 2026-10-08):

- Journal formal entry is GPT Cloud Work.
- Project resume is a new GPT conversation given the project name or link only, plus Grok reading the same approved version.

VNext rules that relate to resume are mapped in `docs/vnext-port/RULE-MAP.md` (WI-REQ-014, 032, 035, 037, 038). The durable fields a reader must be able to recover are in `specs/vnext/requirements.md`. They are not a product surface.

The existing local chain in `scripts/continue_project.py` remains Global Governance, PROJECT_CONTROL, PROJECT_MILESTONE_MAP, frozen authority or approved Manifest, verified repo SHA, and minimum DigitalBrain context. Callers inject those inputs. This port does not wire VNext events into that function.
