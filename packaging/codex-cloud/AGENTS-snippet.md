<!-- information-flow:codex-cloud-journal:start -->
## Codex Cloud 写周记

这个环境的工作区是私有仓 `jakeguo117/obsidian-digitalbrain`。工作区根上有 `📝 Journal/` 时，vault 就是工作区根。不要猜别的路径。

技能不在 vault 里。读 `$HOME/.infoflow-codex-home` 的那一行绝对路径，记作 `INFOFLOW_HOME`（常见是 `/opt/information-flow`，写不进 `/opt` 时是 `$HOME/.codex/information-flow`）。先读 `$INFOFLOW_HOME/skills/journal/SKILL.md`，再跑那里的脚本。不要用工作区相对路径 `skills/journal/`，vault 里没有这份代码。也不要改 `/opt` 或 `INFOFLOW_HOME` 里的文件。

跑脚本之前确认环境变量 `INFOFLOW_RUNTIME=codex-cloud`。setup 写进 `~/.bashrc` 的 export 不一定进非交互 shell。没有这个变量就先导出再跑。

写周记、周记、`/journal`：

- 确认短语仍然只认 `可以写`、`写吧`、`OK 写`。`写周记` 不是确认。
- 落盘只跑：

```bash
python3 "$INFOFLOW_HOME/skills/journal/tools/write_journal.py" save --vault "$PWD" --approval FILE
```

- 有本周周四快照时照 SKILL 加 `--digest-snapshot`。同一 `event_id` 的去重由这个脚本做，不要手写第二份。
- 不要 `git commit` 到 `main`，不要 `git push`。文件留在工作区，交给这次 Codex Cloud 任务的 PR。PR 的仓库必须是 `jakeguo117/obsidian-digitalbrain`。

记一下、想法、`/thought`：

- 原话原样。落盘只跑 `capture_thought.py`。可以带 `--publish`。在 `INFOFLOW_RUNTIME=codex-cloud` 下，`--publish` 只写文件，不执行推 main。退出码 0 且 `runtime` 为 `codex-cloud` 表示文件在工作区，还没进 main。
- 不要自己补 `git push origin HEAD:main`。提交交给 Codex 的 PR。

写入只许进 obsidian-digitalbrain，发现是公开仓就拒绝并停下。脚本若拒绝（远端是 information-flow，或工作区是 information-flow 代码仓，或远端不在允许列表），停。不要换编辑器、不要改写到别的目录、不要推到 information-flow。

Cognition / Ideas 的落盘同样只跑 `$INFOFLOW_HOME` 里对应的 `write_cognition.py` / `write_idea.py`，`--vault` 仍是工作区根。它们走同一条远端检查。不要 push main。
<!-- information-flow:codex-cloud-journal:end -->
