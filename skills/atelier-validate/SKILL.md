---
name: atelier-validate
description: "校验既有或新建 Skill 的合规与质量：frontmatter 字段、目录结构、文件引用、权限与安全、脚本可执行性、技能库查重、触发描述质量。在 /atelier validate、/atelier audit 流程中，或需要确认技能达到发布标准时使用。"
version: 0.1.0
---

# atelier-validate · 验证

发布/改进前把关。**Error 必须清零**；Warning 要么处理，要么记录理由。

## 何时使用

- `/atelier validate <skill 路径>`；
- `/atelier audit`；
- 任何技能创建/修改后、宣布完成前。

## 执行

1. **结构合规**（必跑）：
   ```
   python ../../scripts/validate_skill.py --skill <路径>
   ```
   覆盖：frontmatter 存在与字段合法、name 与目录一致、description ≤1024、文件引用存在、资源目录非空即被引用、脚本可执行后缀、深层引用链、多余文档。
2. **权限与安全**（人工核对）：
   - 脚本/指令里有无删除、网络写、数据库写、付费调用等高风险操作；
   - 有则确认已按 profile.yml 的 `require_confirmation_for` 写进技能守则；
   - 检查命令注入/路径穿越类隐患（脚本参数是否被当作命令拼接）。
3. **查重**（新建前必跑）：
   ```
   python ../../scripts/detect_duplicates.py --skills-dir <技能库根>
   ```
   与既有技能 Jaccard ≥ 阈值 → 走合并评估，不直接放行。
4. **触发描述质量**（有偏差记录时）：
   - 对照 `../../references/trigger-optimization.md`：写没写"何时用"、有没有触发短语；
   - 有 eval_queries.json 就跑触发率评估；没有就先人工审描述。

## 输出

```
== <skill> 校验报告 ==
[ERROR] …   ← 必须修复，清零才能发布
[WARN] …    ← 处理或记录理由
结论：通过 / 不通过
```

## 验收标准

- [ ] validate_skill.py 无 Error；
- [ ] 高风险操作有确认机制；
- [ ] 与库内技能无显著重叠（或已记录合并计划）；
- [ ] 描述 ≤1024 且含触发表述。

## 非目标

- 不修改技能内容（那是 atelier-maintain 的事），只报告问题；
- 不做触发优化本身的迭代（那是 maintain + trigger-optimization 闭环）。

## Gotchas

- 只跑 validate 不看安全 = 漏掉一半把关；
- 警告别悄悄忽略：每个 W 要么改、要么在报告里写"为何可接受"；
- 校验要在**安装后的位置**跑，源目录通过 ≠ 安装位置通过。
