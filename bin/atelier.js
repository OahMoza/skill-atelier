#!/usr/bin/env node
'use strict';

/*
 * atelier — Skill Atelier 的命令行入口（npx github:owner/skill-atelier 可直接执行）
 *
 * 零依赖：只负责把子命令转发给 scripts/ 下的 Python 实现（仅标准库）。
 * discover / design / improve / deprecate 是智能体驱动的判断流程，
 * 请交给 Skill Atelier 元技能本体（SKILL.md 的 /atelier 命令），本 CLI 不伪造。
 */

const { spawnSync } = require('child_process');
const path = require('path');
const pkg = require('../package.json');

const SCRIPTS_DIR = path.join(__dirname, '..', 'scripts');
const PY = process.platform === 'win32' ? 'python' : 'python3';

function runPython(scriptName, args) {
  const script = path.join(SCRIPTS_DIR, scriptName);
  if (!require('fs').existsSync(script)) {
    console.error(`atelier: script not found: ${script}`);
    process.exit(1);
  }
  const res = spawnSync(PY, [script].concat(args), { stdio: 'inherit' });
  process.exit(res.status === null ? 1 : res.status);
}

const HELP = `Skill Atelier · 匠心技能工坊 v${pkg.version}

用法: atelier <command> [args]

命令（均直接调度 scripts/ 下的实现）:
  build     生成技能骨架     atelier build --name <skill> --type <workflow|tool|governance|knowledge> --description "<做什么 + 何时用>"
  validate  校验技能合规     atelier validate --skill <path>          （支持 --skills-dir 扫描整个库）
  audit     技能库查重       atelier audit --skills-dir <dir>
  usage     使用日志分析     atelier usage --log <usage.log.jsonl>    （维护紧迫度/退役候选）
  bump      版本升级         atelier bump --skill <path> --part <patch|minor|major> --message "<原因>"
  help      显示本帮助       atelier help
  version   显示版本         atelier version

智能体驱动流程（无脚本实现，由 SKILL.md 的 /atelier 命令处理）:
  discover / design / improve / deprecate

示例:
  npx --yes github:OahMoza/skill-atelier build --name my-skill --type workflow --description "把周报整理固化为流程"
  npx --yes github:OahMoza/skill-atelier validate --skill ./my-skill
`;

function main() {
  const cmd = process.argv[2] || 'help';
  const args = process.argv.slice(3);

  switch (cmd) {
    case 'build':
      runPython('scaffold_skill.py', args);
      break;
    case 'validate':
    case 'check':
      runPython('validate_skill.py', args);
      break;
    case 'audit':
    case 'dup':
      runPython('detect_duplicates.py', args);
      break;
    case 'usage':
    case 'analyze':
      runPython('analyze_skill_usage.py', args);
      break;
    case 'bump':
      runPython('bump_version.py', args);
      break;
    case 'version':
    case '-v':
    case '--version':
      console.log(pkg.version);
      break;
    case 'help':
    case '-h':
    case '--help':
    default:
      console.log(HELP);
      break;
  }
}

main();
