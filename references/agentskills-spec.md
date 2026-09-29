# Agent Skills 官方规范快照（只读）

> **规范来源**：https://github.com/agentskills/agentskills（官方 Agent Skills 规范）
> **快照 commit**：`69ef37e9424c0a7ea9dd2293b559e43ec8176379`（2026-08-09，docs: add OpenClaw to client showcase）
> **快照日期**：2026-09-29
> **版权**：规范文档 CC-BY-4.0；仓库代码 Apache-2.0
>
> 本文件是**只读资料**。检测到上游更新时，用新 commit 替换快照并记录到 CHANGELOG，不要逐条修改正文。校验器 `scripts/validate_skill.py` 与制造流程都以本快照为准。

## 1. 目录结构

一个 Skill 是**一个包含 `SKILL.md` 的目录**，最小结构：

```
skill-name/
├── SKILL.md        # 必需：元数据 + 指令
├── scripts/        # 可选：可执行代码
├── references/     # 可选：文档
├── assets/         # 可选：模板、资源
└── ...             # 其他任意文件/目录
```

## 2. SKILL.md 格式

`SKILL.md` = YAML frontmatter + Markdown 正文。

### 2.1 Frontmatter 字段

| 字段 | 必需 | 约束 |
|---|---|---|
| `name` | 是 | ≤64 字符；仅小写字母、数字、连字符；不能以连字符开头/结尾 |
| `description` | 是 | 1–1024 字符；描述"做什么 + 何时用" |
| `license` | 否 | 许可证名或指向打包许可证文件的引用 |
| `compatibility` | 否 | ≤500 字符；环境要求（目标产品、系统包、网络等） |
| `metadata` | 否 | 字符串键值映射，用于自定义元数据 |
| `allowed-tools` | 否 | 空格分隔的预批准工具列表（实验性） |

**本工坊扩展字段**（官方无此字段，单独声明，官方缺失时忽略）：`version`、`permissions`、`dependencies`、`platforms`。

最小示例：

```markdown
---
name: skill-name
description: A description of what this skill does and when to use it.
---
```

### 2.2 name 字段

- 1–64 字符；
- 仅小写字母（`a-z`）、数字（`0-9`）、连字符（`-`）；
- 不能以 `-` 开头或结尾；
- 不能含连续 `--`；
- **必须与父目录名一致**。

合法：`pdf-processing`、`data-analysis`、`code-review`
非法：`PDF-Processing`（大写）、`-pdf`（开头连字符）、`pdf--processing`（连续连字符）

### 2.3 description 字段

- 1–1024 字符；
- 同时描述"技能做什么"和"何时使用"；
- 包含能帮智能体识别相关任务的具体关键词。

好例子：`Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction.`
坏例子：`Helps with PDFs.`

### 2.4 可选字段要点

- `license`：建议简短（许可证名或文件名）。
- `compatibility`：大多数技能不需要；只写真实环境要求（如 `Requires Python 3.14+ and uv`）。
- `metadata`：字符串→字符串映射；键名建议带唯一前缀避免冲突（官方示例：`author`、`version`）。
- `allowed-tools`：空格分隔，如 `Bash(git:*) Bash(jq:*) Read`；实验性，兼容性因实现而异。

## 3. 正文（Body）

frontmatter 之后的 Markdown 是技能指令，**无格式限制**。建议包含：分步指令、输入输出示例、常见边界情况。

注意：技能被激活时**整份 SKILL.md 会载入上下文**。过长内容拆到 references，按需加载。

## 4. 渐进式披露（Progressive Disclosure）

1. **元数据**（约 100 token）：启动时加载所有技能的 name + description，仅用于判断相关性；
2. **指令**（建议 <5000 token）：技能激活时加载完整 SKILL.md 正文；
3. **资源**（按需）：scripts / references / assets 仅在需要时加载。

主 SKILL.md 控制在 **500 行以内**；详细资料放独立文件。

## 5. 文件引用规则

- 从技能根目录使用**相对路径**引用：
  ```markdown
  See [the reference guide](references/REFERENCE.md) for details.
  Run the extraction script:
  scripts/extract.py
  ```
- 引用保持**一层深**（`references/xxx.md`），避免深层引用链。

## 6. 官方校验

官方提供参考实现 [skills-ref](https://github.com/agentskills/agentskills/tree/main/skills-ref)（Python 包）：

```bash
skills-ref validate ./my-skill
```

检查 frontmatter 合法性与命名约定。本工坊的 `scripts/validate_skill.py` 在此基础上增加：文件引用存在性、触发描述质量、权限/安全、重复与范围检查。

## 7. 官方创作指南（快照摘要）

本仓库 `docs/skill-creation/` 下四篇指南，要点已提炼到：

- `references/skill-design-principles.md` ← best-practices.mdx
- `references/trigger-optimization.md` ← optimizing-descriptions.mdx
- （evaluating-skills.mdx / using-scripts.mdx 为后续版本预留的扩展点）
