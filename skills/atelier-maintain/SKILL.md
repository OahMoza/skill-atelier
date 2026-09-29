---
name: atelier-maintain
description: "根据真实使用反馈迭代既有 Skill：用使用日志定位失败率与纠正率、把用户纠正写进 Gotchas、修订指令与触发描述、升级版本并保留变更理由。在 /atelier improve、/atelier maintain 流程中，或需要根据反馈优化技能时使用。"
version: 0.1.0
---

# atelier-maintain · 维护

让技能跟着你的真实工作方式生长。**维护的依据是使用证据，不是感觉**。

## 何时使用

- `/atelier improve <skill 路径>`；
- 收到使用失败、用户纠正、触发偏差反馈；
- 定期巡检（配合 /atelier audit）。

## 流程

1. **收集证据**：
   - 有使用日志：`python ../../scripts/analyze_skill_usage.py --log <usage.log.jsonl>`；
   - 无日志：从最近真实任务补记（outcome: success / fail / corrected），不凭记忆。
2. **定位问题**：
   - 失败率高 → 指令过时/误导，重写相关步骤；
   - 纠正率高 → 把每次纠正写进 **Gotchas**（最高价值的迭代输入）；
   - 触发偏差 → 走 `../../references/trigger-optimization.md` 的评估循环；
   - 无问题 → 不动，别为改而改。
3. **修改**：编辑 SKILL.md 或资源，保持边界与非目标不变（边界变化 = minor/major，见下）。
4. **验证**：`python ../../scripts/validate_skill.py --skill <路径>`，Error 清零。
5. **升级版本**（保留"为什么"）：
   ```
   python ../../scripts/bump_version.py --skill <路径> --part <patch|minor|major> --message "原因"
   ```
   - patch：措辞、Gotchas、小修；
   - minor：加能力、改流程；
   - major：职责边界变化、不兼容。
6. **重测**：用一个真实任务跑一遍，确认修复生效。

## 变更记录要求

- 每次 bump 的 message 写**原因**（"脚本在 Windows 找不到 python → 补兼容路径"），不写"更新了脚本"；
- CHANGELOG.md 由 bump_version.py 维护，不要手改。

## 非目标

- 不做一次性的临时修正（用临时提示词解决，不进技能）；
- 不重写设计（职责漂移 → 回 atelier-design）；
- 反复修不好的技能 → 交给 atelier-deprecate 评估。

## Gotchas

- 用户纠正你一次就记一次，别攒着；
- 修完必须跑过真实任务再 bump，先 bump 后修 = 版本号撒谎；
- 别用具体失败查询的关键词硬塞进描述——那是过拟合（见 trigger-optimization）。
