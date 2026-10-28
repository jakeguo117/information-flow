# Information-flow vault

This folder is a data vault from the official empty-vault template.
The information-flow code repository is a different folder. Keep this vault outside that repository.

`.infoflow/vault.json` records the template id, template version, storage mode, and creation time. The scaffold fills storage mode and creation time when it creates the vault.

| Directory | Purpose | Who writes | Who does not |
| --- | --- | --- | --- |
| `📥 Inbox/` | Source drops | Sync tools and you, per source | Cognition tools |
| `📝 Journal/` | Notes you keep | Journal tools after you approve a save | Intake sync |
| `💡 Ideas/` | Ideas under themes you create | You and the ideas skill, after you confirm | This template (no theme folders) |
| `📋 Digests/` | Thursday `cycles/` archive, plus weekday 归堆 in `cluster/` | 想法梳理 writes `📋 Digests/cluster/YYYY-MM-DD.md`. A Cloud Agent pushes the private vault. Emergency digest dispatch may still write `cycles/`. | This template (no sample digests). It does not create or edit `📋 Digests/daily/`. takeaway 已 offline，本 PR 不另挂停排程 |
| `📖 Cognition/` | Evidence, Beliefs, Principles | Cognition tools on an approved write | This template (no type folders yet) |

`📖 Resources/` and `🚀 Projects/` are not created here.

Plugin documentation lives in the information-flow package (skills and scripts), not in this vault.
