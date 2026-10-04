---
name: atelier-audit
description: "对整座个人技能库做定期体检：全库查重、批量校验、触发描述冲突、使用日志健康度（失败率/纠正率/staleness）与反模式检查，产出带证据与处置建议的审计报告。在 /atelier audit 流程中，或需要盘点技能库、找出职责重叠/失效/低价值技能、判断库的整体健康度时使用。"
version: 0.1.0
---

# atelier-audit · 审计

把"定期盘点整座库"变成可执行流程：只产出处置清单，不越权改动。方法论与口径以 `../../references/lifecycle-management.md` §6 为准，冲突以该文档为准。

## 何时使用

- `/atelier audit`；
- 至少每月一次，或技能数明显增长时；
- 怀疑触发互相抢、职责重叠，或想判断哪些技能该修、该合并、该退役。

## 流程

1. **全库查重**：`python ../../scripts/detect_duplicates.py --skills-dir <库根>` → 重叠对清单；
2. **批量校验**：`python ../../scripts/validate_skill.py --skills-dir <库根>` → Error / Warning 汇总；
3. **触发冲突**：过一遍各 SKILL.md 的 description，找抢触发与表述含糊（参考 `../../references/trigger-optimization.md`）；
4. **健康度**（有日志时）：`python ../../scripts/analyze_skill_usage.py --log usage.log.jsonl` → 失败率 / 纠正率 / staleness；
5. **反模式**：逐个过 `../../references/anti-patterns.md`；
6. **出报告**：落到 `drafts/`，每条问题给证据 + 处置建议（保持 / 修 / 合并 / 退役），按影响度排序。

## 交接

- 退役候选 → `skills/atelier-deprecate`；
- 改进候选 → `skills/atelier-maintain`；
- 新建候选 → `skills/atelier-discover`。

## 验收标准

- [ ] 覆盖查重 / 校验 / 触发 / 健康度 / 反模式五类检查（无日志时健康度标注"无日志"）；
- [ ] 每条问题有证据（脚本输出 / 文件路径 / 触发文本）与处置建议；
- [ ] 无问题的类别明说"未发现"并注明检查范围；
- [ ] 报告落在 `drafts/`，可在下次审计对比；
- [ ] 本技能不直接修改或删除任何技能。

## 非目标

- 不直接改 / 删技能（那是 atelier-maintain / atelier-deprecate）；
- 不做单个候选的新建判断（那是 atelier-discover）；
- 不给技能库打分排行——只做问题清单与建议。

## Gotchas

- 审计跑在**安装副本**上（别只在源目录），清单才有意义；
- "未发现" ≠ "检查了所有"：报告里记录库根、脚本与快照日期；
- 删除类处置一律走 deprecate + `profile.yml` 的 `require_confirmation_for`，审计不越权。
