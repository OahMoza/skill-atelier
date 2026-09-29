#!/usr/bin/env python3
"""Bump the version extension field in a skill's SKILL.md and record a changelog entry.

Bumps the frontmatter 'version' (x.y.z, or x.y treated as x.y.0) and maintains
CHANGELOG.md in the skill directory with the reason for the change. If the
skill has no version field, it is created at 0.1.0.

Usage:
  python bump_version.py --skill ./my-skill [--part patch|minor|major] --message "what changed and why" [--dry-run]

Exit codes: 0 = done, 1 = error (missing SKILL.md, bad args).
"""

import argparse
import datetime
import os
import re
import sys

VERSION_LINE_RE = re.compile(r"^version:\s*\"?([0-9.]+)\"?\s*$")


def parse_version(raw):
    parts = raw.strip().strip("\"'").split(".")
    nums = []
    for p in parts:
        if not p.isdigit():
            return None
        nums.append(int(p))
    if len(nums) == 1:
        nums += [0, 0]
    if len(nums) == 2:
        nums += [0]
    if len(nums) > 3:
        return None
    return nums


def bump(parts, part):
    major, minor, patch = parts
    if part == "major":
        return [major + 1, 0, 0]
    if part == "minor":
        return [major, minor + 1, 0]
    return [major, minor, patch + 1]


def main():
    ap = argparse.ArgumentParser(description="Bump a skill's version and record a changelog entry")
    ap.add_argument("--skill", required=True, help="skill directory containing SKILL.md")
    ap.add_argument("--part", choices=["patch", "minor", "major"], default="patch",
                    help="version part to bump (default: patch)")
    ap.add_argument("--message", default="", help="reason for the change (written to CHANGELOG.md)")
    ap.add_argument("--dry-run", action="store_true", help="print the plan without writing")
    args = ap.parse_args()

    skill_dir = os.path.abspath(args.skill)
    md_path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(md_path):
        print(f"error: SKILL.md not found in {skill_dir}", file=sys.stderr)
        return 1

    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        print(f"error: {md_path} has no frontmatter", file=sys.stderr)
        return 1
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        print(f"error: {md_path} frontmatter not closed", file=sys.stderr)
        return 1

    version_idx = None
    old_raw = None
    quoted = False
    for i in range(1, end):
        m = VERSION_LINE_RE.match(lines[i].strip())
        if m:
            version_idx = i
            old_raw = m.group(1)
            quoted = '"' in lines[i]
            break

    if old_raw is None:
        parts = [0, 1, 0]
        created = True
    else:
        parts = parse_version(old_raw)
        if parts is None:
            print(f"error: cannot parse version '{old_raw}' in {md_path}", file=sys.stderr)
            return 1
        created = False

    new_parts = parts if created else bump(parts, args.part)
    new_raw = ".".join(str(p) for p in new_parts)
    new_line = f"version: \"{new_raw}\"" if quoted else f"version: {new_raw}"

    print(f"skill: {os.path.basename(skill_dir)}")
    if created:
        print(f"  version field absent -> creating at {new_raw}")
    else:
        print(f"  {args.part} bump: {'.'.join(str(p) for p in parts)} -> {new_raw}")

    if args.dry_run:
        print("  dry-run: no files written")
        return 0

    new_lines = list(lines)
    if version_idx is None:
        new_lines.insert(1, new_line)
    else:
        new_lines[version_idx] = new_line
    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(new_lines) + "\n")
    print(f"  updated {md_path}")

    # --- CHANGELOG.md ---
    today = datetime.date.today().isoformat()
    entry = f"\n## {new_raw} — {today}\n- {args.message or '(no message)'}\n"
    changelog_path = os.path.join(skill_dir, "CHANGELOG.md")
    if os.path.isfile(changelog_path):
        with open(changelog_path, "r", encoding="utf-8") as f:
            cl = f.read()
        lines_cl = cl.splitlines()
        header_idx = 0
        for i, line in enumerate(lines_cl):
            if line.startswith("# "):
                header_idx = i
                break
        # insert entry right after the top-level header
        new_cl = lines_cl[:header_idx + 1] + [entry.strip()] + lines_cl[header_idx + 1:]
        with open(changelog_path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(new_cl) + "\n")
        print(f"  updated {changelog_path}")
    else:
        with open(changelog_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"# Changelog\n\n{entry.strip()}\n")
        print(f"  created {changelog_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
