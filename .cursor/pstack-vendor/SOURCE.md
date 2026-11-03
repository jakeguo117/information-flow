# pstack 技能来源（7 个，原样收录）

## 上游

- **插件**: pstack 0.15.36（作者 Lauren Tan）
- **仓库**: https://github.com/cursor/plugins （目录 `pstack/skills/<名>/`）
- **Commit SHA**: `1ba91fc25c0977741dd0e267849e6234b037ed0a`（2026-10-29T01:25:55Z）
- **raw 基址**: https://raw.githubusercontent.com/cursor/plugins/1ba91fc25c0977741dd0e267849e6234b037ed0a/pstack/skills/
- **许可证**: MIT（`.cursor/pstack-vendor/LICENSE-pstack`，Copyright (c) 2026 Lauren Tan）
- **收录日期**: 2026-11-01

## 收录了什么

blast-radius、interrogate、figure-it-out、principle-fix-root-causes、principle-prove-it-works、create-verification-skill（含 `references/feature-map-example/` 三份）、maintain-verification-skill。

每个文件与上面 SHA 的上游逐字节一致，未改。sha256 见 `.cursor/pstack-vendor/SHA256SUMS.txt`。

## 没收录什么

这几个技能正文里点到的其它 pstack 技能（arena、architect、how、why、unslop、poteto-mode、show-me-your-work、in-your-own-words 和其余 principle-*）不收。Cloud Agent 碰到这些名字就跳过，不去找；按 `.cursor/rules/cloud-agent-thrift.mdc` 第 4 条，不开 arena 多代理。

## 为什么放 `.cursor/skills/` 而不是 `skills/`

- `.cursor/skills/` 是 Cursor（含 Cloud Agent）自动发现项目技能的目录。
- `skills/` 会被 `.codex-plugin/plugin.json` 打进 Information Flow 插件，也会按白名单同步到 DigitalBrain。这 7 个是工程用的，不该进去。
