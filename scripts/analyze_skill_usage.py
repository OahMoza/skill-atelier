#!/usr/bin/env python3
"""Aggregate a usage log into maintenance priorities and deprecation candidates.

Log format: a JSON array or JSONL (one JSON object per line):
  {"skill": "skill-name", "ts": "2026-09-29T10:00:00+08:00", "outcome": "success", "note": "optional"}
outcome: "success" | "fail" | "corrected"  (corrected = the user had to steer the run)

Output sections: maintenance priority (lower score = more urgent), high-failure
skills to fix first, stale/deprecation candidates, and a full table.

Usage:
  python analyze_skill_usage.py --log usage.log.jsonl [--staleness-days 90] [--md report.md] [--json report.json]

Exit codes: 0 = ok, 3 = log file missing/empty (guidance printed).
"""

import argparse
import datetime
import json
import os
import sys


def parse_ts(value):
    s = str(value).strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.datetime.fromisoformat(s)
    except ValueError:
        return None


def load_log(path):
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        text = f.read().strip()
    if not text:
        return []
    if text.startswith("["):
        data = json.loads(text)
        return data if isinstance(data, list) else []
    # JSONL
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            rows.append(json.loads(line))
    return rows


def main():
    ap = argparse.ArgumentParser(description="Analyze skill usage log into maintenance priorities")
    ap.add_argument("--log", required=True, help="path to usage log (JSON array or JSONL)")
    ap.add_argument("--staleness-days", type=int, default=90, help="days without use -> deprecation candidate (default: 90)")
    ap.add_argument("--now", default=None, help="reference time ISO8601 (default: system now)")
    ap.add_argument("--md", default=None, help="write a markdown report to this path")
    ap.add_argument("--json", default=None, help="write aggregated data as JSON to this path")
    args = ap.parse_args()

    if not os.path.isfile(args.log):
        print("error: log file not found", file=sys.stderr)
        print("log schema (JSONL):", file=sys.stderr)
        print('  {"skill": "skill-name", "ts": "2026-09-29T10:00:00+08:00", "outcome": "success|fail|corrected", "note": "..."}', file=sys.stderr)
        return 3

    rows = load_log(args.log)
    if not rows:
        print("error: log is empty; record real usage first", file=sys.stderr)
        return 3

    now = datetime.datetime.fromisoformat(args.now) if args.now else datetime.datetime.now()
    records = []
    bad = 0
    for r in rows:
        if not isinstance(r, dict):
            bad += 1
            continue
        skill = r.get("skill")
        outcome = r.get("outcome")
        ts = parse_ts(r.get("ts", ""))
        if not skill or outcome not in ("success", "fail", "corrected"):
            bad += 1
            continue
        records.append({"skill": skill, "ts": ts, "outcome": outcome, "note": r.get("note", "")})
    if bad:
        print(f"warning: skipped {bad} malformed log entries", file=sys.stderr)

    by_skill = {}
    for r in records:
        key = r["skill"]
        d = by_skill.setdefault(key, {"skill": key, "count": 0, "fail": 0, "corrected": 0,
                                      "success": 0, "ts_list": []})
        d["count"] += 1
        d[r["outcome"]] += 1
        if r["ts"]:
            d["ts_list"].append(r["ts"])

    table = []
    for key, d in by_skill.items():
        d["fail_rate"] = d["fail"] / d["count"]
        d["corrected_rate"] = d["corrected"] / d["count"]
        if d["ts_list"]:
            last = max(d["ts_list"])
            d["last_use"] = last.isoformat(timespec="minutes")
            d["days_since_last"] = max(0, (now - last).days)
        else:
            d["last_use"] = "-"
            d["days_since_last"] = None
        recency = 1.0 / (1.0 + (d["days_since_last"] or 0) / 30.0)
        d["priority"] = round(0.5 * (1 - d["fail_rate"]) + 0.3 * (1 - d["corrected_rate"]) + 0.2 * recency, 3)
        table.append(d)

    # maintenance priority: lower score = more urgent
    table.sort(key=lambda d: d["priority"])
    stale_threshold = args.staleness_days
    deprecate = [d for d in table if d["days_since_last"] is not None and d["days_since_last"] > stale_threshold
                 and (d["count"] < 3 or d["fail_rate"] < 0.3)]
    high_fail = [d for d in table if d["fail_rate"] >= 0.4]

    def fmt(d):
        days = d["days_since_last"] if d["days_since_last"] is not None else "-"
        return (f"{d['skill']:<28} uses={d['count']:<4} fail={d['fail_rate']:.0%} "
                f"corrected={d['corrected_rate']:.0%} last={d['last_use']} ({days}d) score={d['priority']}")

    print(f"\n== 维护紧迫度（分值越低越需优先处理）==")
    for d in table:
        print("  " + fmt(d))

    print(f"\n== 高失败率（先修）: fail_rate >= 0.4 ==")
    for d in high_fail:
        print("  " + fmt(d))
    if not high_fail:
        print("  (无)")

    print(f"\n== 退役候选（> {stale_threshold} 天未用且无活跃使用）==")
    for d in deprecate:
        print("  " + fmt(d))
    if not deprecate:
        print("  (无)")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(table, f, ensure_ascii=False, indent=2)
        print(f"\njson report: {args.json}")

    if args.md:
        lines = ["# 技能使用分析报告", "",
                 f"日志：{args.log}；记录数：{len(records)}；退役阈值：{stale_threshold} 天。", "",
                 "| 技能 | 次数 | 失败率 | 纠正率 | 最后使用 | 距今天数 | 紧迫度分 |",
                 "|---|---|---|---|---|---|---|"]
        for d in table:
            days = d["days_since_last"] if d["days_since_last"] is not None else "-"
            lines.append(f"| {d['skill']} | {d['count']} | {d['fail_rate']:.0%} | {d['corrected_rate']:.0%} "
                         f"| {d['last_use']} | {days} | {d['priority']} |")
        lines += ["", "## 退役候选", ""]
        for d in deprecate:
            lines.append(f"- {d['skill']}（{d['days_since_last']} 天未用）")
        with open(args.md, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"\nmarkdown report: {args.md}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
