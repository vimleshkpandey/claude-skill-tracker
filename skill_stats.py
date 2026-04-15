#!/usr/bin/env python3
# skill-tracker/skill_stats.py
# View your skill usage stats
# Usage: python3 skill_stats.py [--json] [--since YYYY-MM-DD] [--sort count|name|recent]

import json
import os
import sys
import argparse
from datetime import datetime, date, timedelta

STATS_FILE = os.path.expanduser("~/.claude/skill-stats.json")
LOG_FILE   = os.path.expanduser("~/.claude/skill-usage.jsonl")
SKILLS_DIR = os.path.expanduser("~/.claude/skills")

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    with open(STATS_FILE) as f:
        return json.load(f)

def get_all_skills():
    if not os.path.isdir(SKILLS_DIR):
        return []
    return [d for d in os.listdir(SKILLS_DIR)
            if os.path.isdir(os.path.join(SKILLS_DIR, d))]

def skill_size_mb(name):
    path = os.path.join(SKILLS_DIR, name)
    total = 0
    for dirpath, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(dirpath, f))
            except:
                pass
    return round(total / 1024 / 1024, 1)

def format_date(iso):
    if not iso:
        return "never"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%b %d")
    except:
        return iso[:10]

def main():
    parser = argparse.ArgumentParser(description="Claude Code skill usage stats")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--since", help="Filter to date YYYY-MM-DD onwards")
    parser.add_argument("--sort", choices=["count", "name", "recent", "size"], default="count")
    parser.add_argument("--unused", action="store_true", help="Show only never-used skills")
    parser.add_argument("--top", type=int, default=None, help="Show top N skills")
    args = parser.parse_args()

    stats  = load_stats()
    all_skills = get_all_skills()

    # Build unified list including zero-use skills
    rows = []
    for skill in all_skills:
        s = stats.get(skill, {})
        total = s.get("total", 0)

        # Apply --since filter to counts
        if args.since and total > 0:
            by_date = s.get("by_date", {})
            total = sum(v for k, v in by_date.items() if k >= args.since)

        rows.append({
            "skill":      skill,
            "total":      total,
            "last_used":  s.get("last_used"),
            "first_used": s.get("first_used"),
            "by_date":    s.get("by_date", {}),
            "size_mb":    skill_size_mb(skill),
        })

    if args.unused:
        rows = [r for r in rows if r["total"] == 0]

    # Sort
    if args.sort == "count":
        rows.sort(key=lambda r: -r["total"])
    elif args.sort == "name":
        rows.sort(key=lambda r: r["skill"])
    elif args.sort == "recent":
        rows.sort(key=lambda r: r["last_used"] or "", reverse=True)
    elif args.sort == "size":
        rows.sort(key=lambda r: -r["size_mb"])

    if args.top:
        rows = rows[:args.top]

    if args.json:
        print(json.dumps(rows, indent=2))
        return

    # Pretty print
    total_skills = len(all_skills)
    used_skills  = sum(1 for r in rows if r["total"] > 0)
    total_size   = sum(r["size_mb"] for r in rows)
    total_uses   = sum(r["total"]   for r in rows)

    print(f"\n{'─'*62}")
    print(f"  Claude Code — skill usage report")
    if args.since:
        print(f"  Since {args.since}")
    print(f"{'─'*62}")
    print(f"  {total_skills} skills  |  {used_skills} ever used  |  {total_size:.0f} MB total")
    print(f"{'─'*62}")
    print(f"  {'Skill':<38} {'Uses':>5}  {'Size':>6}  {'Last used'}")
    print(f"  {'─'*38} {'─'*5}  {'─'*6}  {'─'*9}")

    for r in rows:
        bar = "●" * min(r["total"], 10) if r["total"] > 0 else "○"
        flag = " !" if r["size_mb"] >= 5 else "  "
        print(f"{flag} {r['skill']:<38} {r['total']:>5}  {r['size_mb']:>5.1f}M  {format_date(r['last_used'])}")

    print(f"{'─'*62}")
    print(f"  Total invocations tracked: {total_uses}")

    if not args.unused:
        never = [r["skill"] for r in rows if r["total"] == 0]
        if never:
            print(f"\n  Never used ({len(never)} skills):")
            for s in sorted(never)[:20]:
                mb = skill_size_mb(s)
                print(f"    - {s} ({mb}MB)")
            if len(never) > 20:
                print(f"    ... and {len(never)-20} more (run --unused to see all)")

    print()

if __name__ == "__main__":
    main()
