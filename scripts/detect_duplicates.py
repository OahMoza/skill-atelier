#!/usr/bin/env python3
"""Detect overlapping skills in a skills directory by description similarity.

Computes Jaccard similarity between each pair of skills' description keyword
sets (latin words + CJK bigrams) and reports pairs at or above --threshold.
Run before creating a new skill (atelier-discover) or during /atelier audit.

Usage:
  python detect_duplicates.py --skills-dir ./library [--threshold 0.45] [--top 25] [--md report.md] [--json report.json]

Exit codes: 0 = ok (pairs may still be found; check output).
"""

import argparse
import json
import os
import re
import sys


def parse_frontmatter(text):
    """Minimal frontmatter parser; returns (data, body) or (None, None)."""
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
    data = {}
    i = 1
    while i < end:
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if raw[:1] in (" ", "\t"):
            if data:
                key = next(reversed(data))
                prev = data[key]
                if isinstance(prev, str):
                    data[key] = prev + "\n" + stripped
            i += 1
            continue
        m = re.match(r"^([\w.\-]+):(?:\s*(.*))?$", raw)
        if not m:
            i += 1
            continue
        key, val = m.group(1), (m.group(2) or "").strip()
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
        else:
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            data[key] = val
        i += 1
    return data, "\n".join(lines[end + 1:])


def keyword_tokens(text):
    toks = set()
    for w in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9_\-]{1,}", text.lower()):
        toks.add(w)
    cjk = re.findall(r"[\u4e00-\u9fff]", text)
    for a, b in zip(cjk, cjk[1:]):
        toks.add(a + b)
    return toks


def jaccard(a, b):
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return inter / len(a | b)


def containment(a, b):
    """How much of the smaller set is inside the larger one (direction-agnostic)."""
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def find_skills(directory):
    found = []
    for dirpath, dirnames, filenames in os.walk(directory):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        if "SKILL.md" in filenames:
            found.append(dirpath)
    return sorted(found)


def main():
    ap = argparse.ArgumentParser(description="Detect overlapping skills by description similarity")
    ap.add_argument("--skills-dir", default=".", help="directory tree to scan (default: .)")
    ap.add_argument("--threshold", type=float, default=0.45, help="minimum Jaccard score to report (default: 0.45)")
    ap.add_argument("--top", type=int, default=25, help="max pairs to print (default: 25)")
    ap.add_argument("--md", default=None, help="write a markdown report to this path")
    ap.add_argument("--json", default=None, help="write all pair data as JSON to this path")
    args = ap.parse_args()

    skills = []
    for d in find_skills(args.skills_dir):
        with open(os.path.join(d, "SKILL.md"), "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        data, _ = parse_frontmatter(text)
        name = (data or {}).get("name") or os.path.basename(d)
        desc = (data or {}).get("description")
        if not desc:
            continue
        skills.append({"dir": os.path.abspath(d), "name": name, "desc": desc,
                       "tokens": keyword_tokens(desc)})

    pairs = []
    for i in range(len(skills)):
        for j in range(i + 1, len(skills)):
            a, b = skills[i], skills[j]
            score = jaccard(a["tokens"], b["tokens"])
            if score < args.threshold:
                continue
            shared = sorted(a["tokens"] & b["tokens"])[:8]
            pairs.append({
                "skill_a": a["name"], "dir_a": a["dir"],
                "skill_b": b["name"], "dir_b": b["dir"],
                "jaccard": round(score, 3),
                "containment": round(containment(a["tokens"], b["tokens"]), 3),
                "shared_keywords": shared,
            })
    pairs.sort(key=lambda p: (-p["jaccard"], p["skill_a"]))

    rows = pairs[:args.top]
    print(f"scanned {len(skills)} skills; {len(pairs)} pair(s) >= {args.threshold}")
    if not rows:
        print("no overlapping pairs found.")
    for p in rows:
        subset = "  <可能互为子集>" if p["containment"] >= 0.8 else ""
        print(f"  {p['jaccard']:.3f}  {p['skill_a']}  <->  {p['skill_b']}{subset}")
        print(f"      shared keywords: {', '.join(p['shared_keywords']) or '-'}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(pairs, f, ensure_ascii=False, indent=2)
        print(f"json report: {args.json}")

    if args.md:
        lines = ["# 技能库查重报告", "",
                 f"扫描技能数：{len(skills)}；Jaccard 阈值：{args.threshold}；命中 {len(pairs)} 对。", "",
                 "| 相似度 | 技能 A | 技能 B | 包含度 | 共享关键词 |", "|---|---|---|---|---|"]
        for p in pairs:
            lines.append(f"| {p['jaccard']:.3f} | {p['skill_a']} | {p['skill_b']} | {p['containment']:.2f} | {', '.join(p['shared_keywords']) or '-'} |")
        with open(args.md, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"markdown report: {args.md}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
