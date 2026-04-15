# Skill Usage Tracker for Claude Code

Tracks which of your  skills actually get used, so you can make an informed cleanup after a month.

## Setup

### 1. Copy files

```bash
mkdir -p ~/claude-skill-tracker
cp track_skills.sh ~/claude-skill-tracker/
cp skill_stats.py ~/claude-skill-tracker/
chmod +x ~/claude-skill-tracker/track_skills.sh
```

### 2. Add the hook to ~/.claude/settings.json

Add this inside the `"hooks"` section alongside your existing `UserPromptSubmit` hook:

```json
"PostToolUse": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "bash ~/claude-skill-tracker/track_skills.sh",
        "statusMessage": ""
      }
    ]
  }
]
```

Your full hooks section will look like:

```json
"hooks": {
  "UserPromptSubmit": [ ...your existing finance hook... ],
  "PostToolUse": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "bash ~/claude-skill-tracker/track_skills.sh",
          "statusMessage": ""
        }
      ]
    }
  ]
}
```

### 3. Verify it's working

Start a new Claude Code session, ask it to do something that would use a skill (e.g. "create a Word document"), then check:

```bash
cat ~/.claude/skill-usage.jsonl   # raw event log
cat ~/.claude/skill-stats.json    # aggregated counts
```

---

## Viewing stats

```bash
# All skills sorted by usage count (default)
python3 ~/claude-skill-tracker/skill_stats.py

# See only skills you've never used (candidates for archiving)
python3 ~/claude-skill-tracker/skill_stats.py --unused

# Top 20 most used
python3 ~/claude-skill-tracker/skill_stats.py --top 20

# Usage since a specific date
python3 ~/claude-skill-tracker/skill_stats.py --since 2026-04-01

# Sorted by size (biggest space hogs)
python3 ~/claude-skill-tracker/skill_stats.py --sort size

# Raw JSON for your own analysis
python3 ~/claude-skill-tracker/skill_stats.py --json
```

## After a month

Run this to get your cleanup list:

```bash
# Skills taking up space that you never used
python3 ~/claude-skill-tracker/skill_stats.py --unused --sort size
```

Then archive them:

```bash
mkdir -p ~/claude-skills-archive
# Move each unused skill out
python3 ~/claude-skill-tracker/skill_stats.py --unused --json \
  | jq -r '.[].skill' \
  | xargs -I{} mv ~/.claude/skills/{} ~/claude-skills-archive/
```

## Files created

| File | Purpose |
|---|---|
| `~/.claude/skill-usage.jsonl` | Raw event log, one JSON line per skill invocation |
| `~/.claude/skill-stats.json` | Aggregated stats per skill (total, by date, first/last used) |
