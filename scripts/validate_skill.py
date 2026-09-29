#!/usr/bin/env python3
"""Validate Skill directories against the Agent Skills spec + atelier extensions.

Checks (E = error, W = warning):
  E  SKILL.md exists; frontmatter present and closed
  E  name: present, kebab-case, <=64 chars, matches parent directory name
  E  description: present, non-empty, <=1024 chars
  E  every referenced file (scripts/references/assets path in links, code
     spans or command-style lines) exists
  W  description lacks trigger phrasing (what + when)
  W  unknown frontmatter keys (spec fields + atelier extensions only)
  W  non-semver version; metadata not a mapping
  W  body > 500 lines
  W  resource directories that exist but are never referenced by SKILL.md
  W  scripts/ files without a recognized executable extension
  W  README.md / INSTALLATION_GUIDE.md at skill root (CHANGELOG.md allowed when version is declared)
  W  references/ files that link deeper into references/ (one-level-deep rule)

Usage:
  python validate_skill.py --skill ./my-skill [--skill ./other ...]
  python validate_skill.py --skills-dir ./library

Exit codes: 0 = clean, 1 = errors found, 2 = warnings only (no errors).
"""

import argparse
import os
import re
import sys

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SPEC_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
EXT_KEYS = {"version", "permissions", "dependencies", "platforms"}
ALLOWED_KEYS = SPEC_KEYS | EXT_KEYS
REF_DIRS = ("scripts", "references", "assets")
TRIGGER_WORDS = ("使用", "用于", "适用", "触发", "需要", "当", "Use", "when", "if", "handle",
                 "work with", "mention")
EXEC_EXT = {".py", ".ps1", ".sh", ".js", ".mjs", ".ts", ".bat", ".cmd", ".rb", ".pl"}
MARKDOWN_LINK_RE = re.compile(r"\]\((references|scripts|assets)/[^)#\s]+\)")
MARKDOWN_LINK_PARENT_RE = re.compile(r"\]\((?:\.\./)+(references|scripts|assets)/[^)#\s]+\)")
CODE_SPAN_RE = re.compile(r"`(references|scripts|assets)/[\w./\-]+`")
CODE_SPAN_PARENT_RE = re.compile(r"`(?:\.\./)+(references|scripts|assets)/[\w./\-]+`")
CMD_LINE_RE = re.compile(r"^\s*(references|scripts|assets)/[\w./\-]+", re.MULTILINE)
CMD_LINE_PARENT_RE = re.compile(r"^\s*(?:\.\./)+(references|scripts|assets)/[\w./\-]+", re.MULTILINE)


class Issue:
    __slots__ = ("level", "msg")

    def __init__(self, level, msg):
        self.level = level  # "E" or "W"
        self.msg = msg

    def render(self):
        tag = "ERROR" if self.level == "E" else "WARN "
        return f"[{tag}] {self.msg}"


def parse_frontmatter(text):
    """Minimal YAML frontmatter parser covering the spec's field shapes.

    Handles plain scalars, quoted scalars, '>' folded, '|' literal, and
    indented block maps (metadata). Not a full YAML parser.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, None
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, None
    body = "\n".join(lines[end + 1:])
    data = {}
    i = 1
    while i < end:
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if raw[:1] in (" ", "\t"):
            # continuation line: fold into the previous value
            if data:
                key = next(reversed(data))
                prev = data[key]
                if isinstance(prev, str):
                    data[key] = prev + "\n" + stripped
                elif isinstance(prev, dict):
                    m = re.match(r"^[\- ]*([\w.\-]+):\s*(.*)$", stripped)
                    if m:
                        prev[m.group(1)] = m.group(2).strip().strip("\"'")
                elif isinstance(prev, list):
                    data[key] = prev + [stripped]
            i += 1
            continue
        m = re.match(r"^([\w.\-]+):(?:\s*(.*))?$", raw)
        if not m:
            i += 1
            continue
        key = m.group(1)
        val = (m.group(2) or "").strip()
        if val.startswith(">") or val.startswith("|"):
            block = []
            j = i + 1
            while j < end and lines[j][:1] in (" ", "\t"):
                block.append(lines[j].strip())
                j += 1
            data[key] = (" " if val.startswith(">") else "\n").join(block)
            i = j
            continue
        if val == "":
            j = i + 1
            if j < end and lines[j][:1] in (" ", "\t"):
                inner = {}
                while j < end and lines[j][:1] in (" ", "\t"):
                    m2 = re.match(r"^[\- ]*([\w.\-]+):\s*(.*)$", lines[j])
                    if m2:
                        inner[m2.group(1)] = m2.group(2).strip().strip("\"'")
                    j += 1
                data[key] = inner
                i = j
                continue
            data[key] = ""
            i += 1
            continue
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        data[key] = val
        i += 1
    return data, body


def collect_referenced_paths(skill_md_text):
    """Extract file paths referenced by a SKILL.md (links, code spans, command lines).

    Returns a set of path tokens as written; leading '../' is kept so the
    caller can resolve against the package root (parent of the skill dir).
    """
    found = set()
    for pattern in (MARKDOWN_LINK_RE, MARKDOWN_LINK_PARENT_RE, CODE_SPAN_RE,
                    CODE_SPAN_PARENT_RE, CMD_LINE_RE, CMD_LINE_PARENT_RE):
        for m in pattern.finditer(skill_md_text):
            token = m.group(0)
            start = token.find("(") + 1 if "(" in token else token.find("`") + 1
            end = token.rfind(")") if ")" in token else token.rfind("`")
            if start > 0 and end > start:
                found.add(token[start:end])
    return found


def validate_skill(skill_dir, issues):
    root = os.path.abspath(skill_dir)
    md_path = os.path.join(root, "SKILL.md")
    if not os.path.isfile(md_path):
        issues.append(Issue("E", f"SKILL.md missing in {root}"))
        return
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()

    data, body = parse_frontmatter(text)
    if data is None:
        issues.append(Issue("E", "frontmatter missing or not closed with ---"))
        return

    # --- name ---
    name = data.get("name")
    dir_name = os.path.basename(root)
    if not isinstance(name, str) or not name:
        issues.append(Issue("E", "frontmatter field 'name' is required"))
    else:
        if len(name) > 64:
            issues.append(Issue("E", f"name '{name}' exceeds 64 characters"))
        if not NAME_RE.fullmatch(name):
            issues.append(Issue("E", f"name '{name}' violates kebab-case rule (lowercase letters/numbers/hyphens, no leading/trailing/consecutive hyphens)"))
        if name != dir_name:
            issues.append(Issue("E", f"name '{name}' does not match parent directory name '{dir_name}'"))

    # --- description ---
    desc = data.get("description")
    if not isinstance(desc, str) or not desc.strip():
        issues.append(Issue("E", "frontmatter field 'description' is required and non-empty"))
    else:
        if len(desc) > 1024:
            issues.append(Issue("E", f"description is {len(desc)} chars; spec limit is 1024"))
        if len(desc) < 40:
            issues.append(Issue("W", "description is very short; add what the skill does and when to use it"))
        if not any(w in desc for w in TRIGGER_WORDS):
            issues.append(Issue("W", "description lacks trigger phrasing; add 'when to use' cues (使用/用于/适用/Use/when...)"))

    # --- allowed keys ---
    for key in data:
        if key not in ALLOWED_KEYS:
            issues.append(Issue("W", f"unknown frontmatter key '{key}' (spec fields: {', '.join(sorted(SPEC_KEYS))}; atelier extensions: {', '.join(sorted(EXT_KEYS))})"))

    # --- extension field sanity ---
    version = data.get("version")
    if version is not None and not re.fullmatch(r"\d+\.\d+(\.\d+)?", str(version)):
        issues.append(Issue("W", f"version '{version}' is not a semver-like x.y.z value"))
    metadata = data.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        issues.append(Issue("W", "metadata must be a key-value mapping"))

    # --- body ---
    if body is None:
        body = ""
    n_lines = len(body.splitlines())
    if n_lines > 500:
        issues.append(Issue("W", f"SKILL.md body is {n_lines} lines; spec recommends keeping it under 500 (split to references)"))

    # --- file references ---
    # Refs are resolved verbatim as relative paths from the skill root, so
    # package-internal skills may point upward with ../ or ../../ chains.
    refs = collect_referenced_paths(text)
    used_dirs = set()
    for ref in sorted(refs):
        rel = ref
        probe = rel
        while probe.startswith("../"):
            probe = probe[3:]
        top = probe.split("/", 1)[0]
        if top not in REF_DIRS:
            continue
        used_dirs.add(top)
        target = os.path.normpath(os.path.join(root, rel))
        if not os.path.exists(target):
            issues.append(Issue("E", f"referenced file not found: {ref}"))

    # --- resource dirs used? ---
    for d in REF_DIRS:
        dpath = os.path.join(root, d)
        if os.path.isdir(dpath) and os.listdir(dpath):
            if d not in used_dirs:
                issues.append(Issue("W", f"{d}/ contains files but SKILL.md never references them (anti-pattern: decoration assets)"))

    # --- script executability ---
    scripts_dir = os.path.join(root, "scripts")
    if os.path.isdir(scripts_dir):
        for entry in sorted(os.listdir(scripts_dir)):
            if entry.startswith("."):
                continue
            full = os.path.join(scripts_dir, entry)
            if os.path.isfile(full):
                ext = os.path.splitext(entry)[1].lower()
                if ext not in EXEC_EXT and not entry.lower().endswith(("makefile", "dockerfile", "requirements.txt", ".txt")):
                    issues.append(Issue("W", f"scripts/{entry} has no recognized executable extension ({', '.join(sorted(EXEC_EXT))})"))

    # --- extra docs ---
    for extra in ("README.md", "INSTALLATION_GUIDE.md"):
        if os.path.isfile(os.path.join(root, extra)):
            issues.append(Issue("W", f"{extra} at skill root adds clutter; put project docs outside the skill or remove"))
    if os.path.isfile(os.path.join(root, "CHANGELOG.md")) and version is None:
        issues.append(Issue("W", "CHANGELOG.md present but no version declared in frontmatter"))

    # --- deep reference chains (references/ docs linking into other references/) ---
    refs_dir = os.path.join(root, "references")
    if os.path.isdir(refs_dir):
        for entry in sorted(os.listdir(refs_dir)):
            full = os.path.join(refs_dir, entry)
            if not os.path.isfile(full):
                continue
            with open(full, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            # ignore code-fence content (e.g. quoted spec examples) and
            # code-span mentions (intentional 'go read this' pointers);
            # only markdown links into references/ indicate a doc chain.
            content = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
            if re.search(r"\]\(references/", content):
                issues.append(Issue("W", f"references/{entry} links deeper into references/; keep references one level deep from SKILL.md"))


def find_skills(directory):
    found = []
    for dirpath, dirnames, filenames in os.walk(directory):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        if "SKILL.md" in filenames:
            found.append(dirpath)
    return sorted(found)


def main():
    ap = argparse.ArgumentParser(description="Validate Skill directories")
    ap.add_argument("--skill", action="append", default=[], help="skill directory to validate (repeatable)")
    ap.add_argument("--skills-dir", default=None, help="scan a directory tree for skills (each dir with SKILL.md)")
    args = ap.parse_args()

    targets = list(args.skill)
    if args.skills_dir:
        targets += find_skills(args.skills_dir)
    targets = sorted(set(os.path.abspath(t) for t in targets))
    if not targets:
        print("error: nothing to validate; pass --skill PATH or --skills-dir DIR", file=sys.stderr)
        return 3

    all_issues = []
    for t in targets:
        issues = []
        validate_skill(t, issues)
        print(f"\n== {os.path.basename(t)} ({t}) ==")
        for iss in issues:
            print("  " + iss.render())
        all_issues.append((os.path.basename(t), issues))

    n_errors = sum(1 for _, iss in all_issues for i in iss if i.level == "E")
    n_warns = sum(1 for _, iss in all_issues for i in iss if i.level == "W")
    print(f"\nsummary: {len(targets)} skill(s), {n_errors} error(s), {n_warns} warning(s)")
    if n_errors:
        return 1
    if n_warns:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
