---
name: skill-atelier
description: >
  个人元技能制造与治理系统。基于用户真实任务、工作记录、项目文件、团队规范和使用反馈，持续设计、生成、测试、审查、版本化和淘汰 Agent Skills。当用户想要创建新 Skill、把 SOP/项目工作流/个人习惯固化为 Skill、改进某个 SKILL.md 的触发描述或指令、检查技能库重复、评估某个任务是否值得做成 Skill、或维护个人技能组合时使用。支持 /atelier discover、design、build、validate、improve、deprecate、audit 全套操作。
version: 0.1.0
---

# Skill Atelier · 匠心技能工坊

个人元技能（meta-skill）制造与治理系统。它不只是"批量生成 SKILL.md 文本"，而是围绕你**真实的工作方式**：从你的任务、记录、纠正和反馈中**发现**能力，**设计**责任边界，**制造**可运行产物，**验证**后再安装，并在使用证据驱动下持续**迭代**，必要时**退役**。

核心区别：通用工具生成"一份 SKILL.md"；Skill Atelier 维护"你的整座技能库"。

## 八条操作原则

1. **从证据出发，不从想象出发** —— 先读任务记录、项目文件、使用日志，再判断该做什么。
2. **一个技能一个窄职责** —— 宁可拆，不可堆；职责过宽会破坏触发精度。
3. **制造可执行、可测试的产物** —— 脚本要真能跑，验收要有证据，不是"看起来对"。
4. **保留你的个人风格与约束** —— 语言、格式、风险偏好、目录习惯都是规格的一部分。
5. **每个技能必须声明触发场景与非目标** —— 描述写"做什么 + 何时用"，正文写"不做什么"。
6. **不为凑数保留 references / scripts / assets** —— 用不到的资源一律不建。
7. **验证通过才算完成** —— 先跑 `scripts/validate_skill.py`，再宣布完成。
8. **用退役代替堆积** —— 弱技能合并或标记 deprecated，而不是留着制造重复。

## 生命周期

### 1 发现（Discover）→ `skills/atelier-discover`
从以下来源识别候选能力：
- 反复出现的请求与纠正模式；
- 反复执行的项目工作流与 SOP；
- 高频命令行序列、固定输出格式；
- 已有代码、提示词、模板、文档里可沉淀的重复逻辑；
- 使用日志（`scripts/analyze_skill_usage.py` 的输出）。

产出：候选评估报告（候选名称 / 类型 / 触发场景 / 非目标 / 当前替代方案 / 证据 / 建议：新建 | 并入 | 暂不创建）。

### 2 设计（Design）→ `skills/atelier-design`
写设计文档（**不建文件**），定义：
- 精确能力边界与非目标；
- 输入契约、输出契约；
- 权限与运行时依赖；
- 触发条件；
- 失败行为；
- 验收标准。

参考 `references/skill-design-principles.md`。

### 3 制造（Build）→ `skills/atelier-build`
- 用 `scripts/scaffold_skill.py` 生成规范骨架；
- 按 `assets/templates/` 中的类型模板（workflow / tool / governance）写内容；
- 真正创建目录、脚本与文件，**不是只输出文本**；
- 安装位置按 `profile.yml` 的 `directories.skills`。

### 4 验证（Validate）→ `skills/atelier-validate`
- 跑 `scripts/validate_skill.py` 检查 frontmatter、结构、文件引用、权限、脚本可执行性与安全风险；
- 触发描述优化参考 `references/trigger-optimization.md`；
- 新建前先跑 `scripts/detect_duplicates.py` 查重；
- 全绿才算完成；警告也要处理或记录理由。

### 5 维护（Maintain）→ `skills/atelier-maintain`
- 基于使用反馈与 `scripts/analyze_skill_usage.py` 的失败/纠正率决定改什么；
- 修改后记录变更理由，用 `scripts/bump_version.py` 升级版本；
- 把用户的纠正写进 Gotchas —— 这是迭代最直接的输入。

### 6 退役（Deprecate）→ `skills/atelier-deprecate`
当技能长期不用、被完全替代、或不再匹配你的工作流时：
- 标记 deprecated 并在描述里声明；
- 迁移依赖它的流程到替代技能；
- 合并重叠技能，删除死技能（删除前按 `profile.yml` 的 `require_confirmation_for` 确认）。

### 横向治理 · 审计（Audit）→ `skills/atelier-audit`
`/atelier audit` 是**全库层面**的体检（查重、批量校验、触发冲突、使用健康度、反模式），不属于单个阶段。至少每月一次或技能数明显增长时执行；方法论见 `references/lifecycle-management.md` §6，产出处置清单落到 `drafts/`。

## 交互命令

| 命令 | 作用 |
|---|---|
| `/atelier discover` | 从当前任务、项目文件或工作记录发现 Skill 候选 |
| `/atelier design <目标>` | 输出 Skill 设计文档，不创建文件 |
| `/atelier build <目标>` | 创建完整 Skill 目录及可运行产物 |
| `/atelier validate <skill 路径>` | 检查规范、路由、文件、脚本与安全风险 |
| `/atelier improve <skill 路径>` | 根据使用反馈优化既有 Skill |
| `/atelier deprecate <skill 路径>` | 判断并安全移除或合并 Skill |
| `/atelier audit` | 审计整库：查重、批量校验、触发冲突、健康度（→ skills/atelier-audit） |

## 个人化

动手前先读 `profile.yml`（或 `~/.skill-atelier/profile.yml`，若存在则优先）。它决定生成的技能长什么样：语言、输出风格、风险容忍度、需确认的操作、偏好工具、技能安装目录与草稿目录。字段说明见 `references/personal-context-template.md`。

隐私边界：不推断敏感信息，不访问授权路径之外的文件。

## 与官方规范的关系

- 规范快照（只读）：`references/agentskills-spec.md`，来源 agentskills/agentskills，快照日期 2026-09-29，commit `69ef37e`。
- 兼容策略：**不修改官方核心字段**（name、description）；扩展信息（version、permissions、dependencies、platforms）单独声明，官方字段缺失时忽略扩展。
- 检测到官方规范更新时：更新快照文件并记录 commit，再批量校验存量技能，而不是逐个猜测。

## 资源路由

| 场景 | 读这个 |
|---|---|
| 需要官方格式细节（字段约束、目录结构、渐进式披露） | `references/agentskills-spec.md` |
| 设计新技能的边界与结构 | `references/skill-design-principles.md` |
| 描述互相抢触发、触发不准 | `references/trigger-optimization.md` |
| 维护/审计整个技能组合 | `references/lifecycle-management.md` |
| 全库审计（/atelier audit） | `skills/atelier-audit`（方法论见 `references/lifecycle-management.md` §6） |
| 决定个人化配置字段 | `references/personal-context-template.md` |
| 判断什么不该做 | `references/anti-patterns.md` |
| 生成骨架 | `scripts/scaffold_skill.py` |
| 新建前查重 | `scripts/detect_duplicates.py` |
| 校验 | `scripts/validate_skill.py` |
| 维护优先级 | `scripts/analyze_skill_usage.py` |
| 版本升级 | `scripts/bump_version.py` |

## 定稿验证要求

宣布"创建/改进完成"之前，必须：
- [ ] `scripts/validate_skill.py` 无 Error；
- [ ] 触发描述写清了"做什么 + 何时用"，且 ≤1024 字符；
- [ ] 脚本已实际运行过（或写明未运行原因）；
- [ ] 无凑数的空资源目录；
- [ ] 新增前已跑过 `detect_duplicates.py`；
- [ ] 版本号与变更记录已更新（若属于本工坊治理的技能）。

## 与既有技能的关系

- `skill-builder`：单次"从需求到 SKILL.md"的制造方法论。Skill Atelier 把它作为 **Build 阶段**的底层方法之一引用，并增加"发现 → 治理 → 迭代 → 退役"的元层闭环。
- `skill-creator-for-work` 等生成类技能：它们产单份文件；本技能管整座库。职责不重叠。
