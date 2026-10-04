# Changelog

## 未发版（下次 bump 时并入正式版本）

- 新增 `skills/atelier-audit` 子技能：`/atelier audit` 从"命令表承诺 + 散落在 lifecycle-management §6"落实为可执行子技能（全库查重 / 批量校验 / 触发冲突 / 使用健康度 / 反模式 → 处置清单），方法论引用 `references/lifecycle-management.md` §6。
- SKILL.md：命令表 audit 行指向 atelier-audit；生命周期新增"横向治理 · 审计"小节；资源路由新增 audit 行。
- README 目录结构补 atelier-audit。
- 版本号暂不 bump：与"正式发版打 tag"一起处理，避免 npx #v0.1.0 引用断裂。

## 0.1.0 — 2026-09-29

- 首个可运行版本：主 SKILL.md、六个子技能（discover/design/build/validate/maintain/deprecate）。
- 五个脚本：scaffold_skill / validate_skill / detect_duplicates / analyze_skill_usage / bump_version。
- 官方规范快照 `references/agentskills-spec.md`（agentskills/agentskills commit `69ef37e`）。
- 个人配置 `profile.yml` 与模板。
