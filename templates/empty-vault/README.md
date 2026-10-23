# Information-flow vault

This folder is a data vault from the official empty-vault template.
The information-flow code repository is a different folder. Keep this vault outside that repository.

`.infoflow/vault.json` records the template id, template version, storage mode, and creation time. The scaffold fills storage mode and creation time when it creates the vault.

| Directory | Purpose | Who writes | Who does not |
| --- | --- | --- | --- |
| `📥 Inbox/` | Source drops | Sync tools and you, per source | Cognition tools |
| `📝 Journal/` | Notes you keep | Journal tools after you approve a save | Intake sync |
| `💡 Ideas/` | Ideas under themes you create | You and the ideas skill, after you confirm | This template (no theme folders) |
| `📋 Digests/` | Cycle digests | Digest tools | This template (no sample digests) |
| `📖 Cognition/` | Evidence, Beliefs, Principles | Cognition tools on an approved write | This template (no type folders yet) |

`📖 Resources/` and `🚀 Projects/` are not created here.

Plugin documentation lives in the information-flow package (skills and scripts), not in this vault.
