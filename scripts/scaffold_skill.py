#!/usr/bin/env python3
"""Create a validated Skill directory skeleton from templates.

Usage:
  python scaffold_skill.py --name <skill-name> --type <workflow|tool|governance|knowledge> \
      --description "<what it does + when to use>" [--out DIR] [--templates DIR] [--version x.y.z]

Creates: <out>/<name>/SKILL.md (from the matching template) + empty scripts/, references/, assets/.
Refuses to overwrite an existing non-empty directory. Name must follow the Agent Skills spec.

Exit codes: 0 = created, 1 = argument/validation error.
"""

import argparse
import os
import re
import sys

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

TYPE_TEMPLATES = {
    "workflow": "workflow-skill.tmpl",
    "tool": "tool-skill.tmpl",
    "governance": "governance-skill.tmpl",
    "knowledge": "SKILL.md.tmpl",
}


def validate_name(name):
    if not name:
        return "name is required"
    if len(name) > 64:
        return "name must be at most 64 characters"
    if not NAME_RE.fullmatch(name):
        return "name must be lowercase letters/numbers/hyphens, no leading/trailing/consecutive hyphens"
    return None


def substitute(template_text, mapping):
    """Replace {{key}} placeholders. Returns (text, missing_keys)."""
    missing = set()
    def repl(m):
        key = m.group(1)
        if key not in mapping:
            missing.add(key)
            return m.group(0)
        return str(mapping[key])
    out = re.sub(r"\{\{\s*(\w+)\s*\}\}", repl, template_text)
    return out, missing


def main():
    ap = argparse.ArgumentParser(description="Scaffold a Skill directory skeleton")
    ap.add_argument("--name", required=True, help="skill name (kebab-case, lowercase)")
    ap.add_argument("--type", choices=sorted(TYPE_TEMPLATES), default="workflow",
                    help="skill type; picks the template (default: workflow)")
    ap.add_argument("--description", required=True, help="what the skill does + when to use it")
    ap.add_argument("--out", default=".", help="parent directory for the new skill (default: .)")
    ap.add_argument("--templates", default=None,
                    help="templates directory (default: <script_dir>/../assets/templates)")
    ap.add_argument("--version", default="0.1.0", help="initial version (default: 0.1.0)")
    args = ap.parse_args()

    name_err = validate_name(args.name)
    if name_err:
        print(f"error: invalid name '{args.name}': {name_err}", file=sys.stderr)
        return 1

    if len(args.description) > 1024:
        print(f"warning: description is {len(args.description)} chars; spec limit is 1024", file=sys.stderr)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = args.templates or os.path.normpath(os.path.join(script_dir, "..", "assets", "templates"))
    tmpl_name = TYPE_TEMPLATES[args.type]
    tmpl_path = os.path.join(templates_dir, tmpl_name)
    if not os.path.isfile(tmpl_path):
        print(f"error: template not found: {tmpl_path}", file=sys.stderr)
        return 1

    target = os.path.join(args.out, args.name)
    if os.path.exists(target):
        if os.listdir(target):
            print(f"error: target directory already exists and is not empty: {target}", file=sys.stderr)
            return 1
    else:
        os.makedirs(target)

    try:
        with open(tmpl_path, "r", encoding="utf-8") as f:
            template = f.read()
    except OSError as e:
        print(f"error: cannot read template: {e}", file=sys.stderr)
        return 1

    mapping = {
        "name": args.name,
        "description": args.description,
        "version": args.version,
        "year": "2026",
        "type": args.type,
    }
    content, missing = substitute(template, mapping)

    skill_md = os.path.join(target, "SKILL.md")
    with open(skill_md, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    for d in ("scripts", "references", "assets"):
        os.makedirs(os.path.join(target, d), exist_ok=True)

    print(f"created: {target}")
    print("  SKILL.md  (template: {})".format(tmpl_name))
    print("  scripts/ references/ assets/  (empty — remove any you won't use)")
    if missing:
        print("warning: unfilled placeholders kept as-is: {}".format(", ".join(sorted(missing))),
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
