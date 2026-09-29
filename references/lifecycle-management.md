# 生命周期管理

> 维护整座个人技能库：版本化、优先级、合并、退役与审计。对应主 SKILL.md 的 Maintain 与 Deprecate 阶段。

## 1. 版本化

本工坊治理下的技能在 frontmatter 声明扩展字段 `version`（语义化版本 `x.y.z`）：

- `patch`（0.1.0 → 0.1.1）：修正措辞、补 Gotchas、小修指令；
- `minor`（0.1.0 → 0.2.0）：加能力、改流程、扩展范围；
- `major`（0.1.0 → 1.0.0）：职责边界变化、与旧行为不兼容。

用 `scripts/bump_version.py --skill <path> --part <major|minor|patch> --message "原因"` 升级，它会：
- 更新 frontmatter 的 `version`；
- 在技能目录维护 `CHANGELOG.md`，**保留每次变更的理由**（"为什么"比"改了什么"更有审计价值）。

不治理的第三方技能：只读，不主动改版本。

## 2. 维护优先级（数据驱动）

有使用日志时跑 `scripts/analyze_skill_usage.py`，按以下信号排序：

| 信号 | 动作 |
|---|---|
| 失败率高（fail_rate） | 最高优先——指令可能误导或过时，先修 |
| 纠正率高（每次都要你纠正） | 把纠正写进 Gotchas，重跑验证 |
| 触发偏差（该触发没触发 / 不该触发触发） | 走 trigger-optimization 流程 |
| 长期不用（staleness 超过阈值，默认 90 天） | 降级为退役候选，不要先修 |
| 使用多且稳定 | 保持，不动 |

优先级公式建议：`priority = 0.5×(1-fail_rate) + 0.3×(1-corrected_rate) + 0.2×recency`，按分数排序。

## 3. 使用日志格式

`analyze_skill_usage.py --log usage.log.jsonl`，每行一条：

```json
{"skill": "skill-name", "ts": "2026-09-29T10:00:00+08:00", "outcome": "fail", "note": "脚本在 Windows 上找不到 python"}
```

`outcome` 取值：`success` / `fail` / `corrected`（被用户纠正）。

没有日志时：先让 `skills/atelier-maintain` 建日志骨架，从最近的真实任务开始记录，不要凭记忆估。

## 4. 合并

两个技能职责重叠（`detect_duplicates.py` 输出高相似）时：
1. 确认重叠的**核心能力**与各自**非目标**；
2. 保留更成熟的那个（使用多、验证过的），把另一个的 Gotchas 和边界情况并入；
3. 被并入方按第 5 节退役；
4. 更新所有引用旧技能名的流程/文档。

## 5. 退役（Deprecate）

判定标准（满足其一）：
- 长期不用（超过 staleness 阈值且无恢复迹象）；
- 被完全替代（新技能覆盖全部能力）；
- 不再匹配当前工作流（职责对应的任务已不存在）。

动作：
1. 描述里声明 deprecated（改触发，避免继续被选中）；
2. 迁移依赖流程到替代技能；
3. 合并可合并的重叠；
4. **删除文件**是高风险操作：按 `profile.yml` 的 `require_confirmation_for` 确认后再删；保守做法是移入 `drafts/archived/` 保留证据。

## 6. 定期审计（/atelier audit）

至少每月一次（或技能数明显增长时）：

1. `scripts/detect_duplicates.py --skills-dir <库根>` → 职责重叠清单；
2. `scripts/analyze_skill_usage.py`（有日志时）→ 低价值/失效清单；
3. 逐个过 `references/anti-patterns.md` → 反模式清单；
4. 输出审计报告到 `drafts/`，明确每项的处置：**保持 / 修 / 合并 / 退役**。

## 7. 变更闭环

任何改进都要走：改 → 验证（validate_skill.py 无 Error）→ bump 版本 → 记理由 → 用真实任务重测。跳过验证就发布 = 制造脏数据。
