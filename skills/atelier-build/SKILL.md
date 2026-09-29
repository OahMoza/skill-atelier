---
name: atelier-build
description: "把设计文档变成真实可运行的 Skill：生成规范目录骨架、写入 SKILL.md 与脚本/参考/资源、实际运行验证脚本、安装到个人技能目录。在 /atelier build 流程中，或需要真正创建技能文件而非只给方案时使用。"
version: 0.1.0
---

# atelier-build · 制造

把设计变成**可运行的产物**，不是文本方案。产出物：完整技能目录（SKILL.md + 需要的 scripts/references/assets），安装到 `profile.yml` 的 `directories.skills`。

## 何时使用

- `/atelier build <目标>`；
- 设计文档（atelier-design 产出）已确认，开始制造。

## 流程

1. **读设计文档**（或需求），确认边界、输入输出、资源规划。
2. **生成骨架**：
   ```
   python ../../scripts/scaffold_skill.py --name <name> --type <workflow|tool|governance|knowledge> \
       --description "<做什么 + 何时用>" --out <drafts 或临时目录>
   ```
3. **写入内容**：按类型模板（`../../assets/templates/`）写 SKILL.md 正文；按设计规划写 scripts / references / assets。
4. **脚本必须实际运行验证**：至少跑一遍代表用例，确认输出与退出码符合设计；不验证的脚本不发布。
5. **清理**：删除模板/骨架里用不到的空目录与示例文件（原则 6：不为凑数保留资源）。
6. **安装**：把整个技能目录复制到 `profile.yml` 的 `directories.skills`（保持目录结构与技能名一致）。
7. **交接验证**：跑 `../../scripts/validate_skill.py --skill <安装路径>`，Error 清零后才算交付。

## 验收标准

- [ ] SKILL.md 存在，frontmatter 的 name 与目录名一致；
- [ ] 描述写清"做什么 + 何时用"，≤1024 字符；
- [ ] 引用的每个文件真实存在；
- [ ] 脚本实际运行过并符合输出契约；
- [ ] 无空资源目录、无多余文档；
- [ ] 已安装到技能根目录且 validate 无 Error。

## 非目标

- 不写设计文档（那是 atelier-design）；
- 不做触发测试与查重（那是 atelier-validate）；
- 安装位置不明确时，按 profile.yml；profile 也没有时先问，不擅自装。

## Gotchas

- Windows 上路径用反斜杠/正斜杠统一处理，脚本里别硬编码绝对路径；
- 复制安装后必须在**安装位置**再验证一次，别只在源目录验证；
- 删除用户已有文件前按 profile.yml 的 require_confirmation_for 确认。
