#!/bin/bash
# skill-tracker/track_skills.sh
# Claude Code hook — reads PostToolUse events and logs skill usage
# Install: add to ~/.claude/settings.json hooks (see README below)

SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
LOG_FILE="${SKILL_TRACKER_LOG:-$HOME/.claude/skill-usage.jsonl}"
STATS_FILE="${SKILL_TRACKER_STATS:-$HOME/.claude/skill-stats.json}"

# Read the hook event from stdin (Claude Code sends JSON)
INPUT=$(cat)

# Extract tool name and any file paths referenced
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""' 2>/dev/null)
TOOL_INPUT=$(echo "$INPUT" | jq -r '.tool_input // {}' 2>/dev/null)

# Detect skill usage by checking if any file path references ~/.claude/skills/
# Claude Code reads SKILL.md files via Read/View tool calls
SKILL_USED=""

if [[ "$TOOL_NAME" == "Read" || "$TOOL_NAME" == "View" || "$TOOL_NAME" == "read_file" ]]; then
  FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.path // .file_path // ""' 2>/dev/null)
  if [[ "$FILE_PATH" == *"/.claude/skills/"* ]]; then
    # Extract skill name from path: ~/.claude/skills/SKILLNAME/...
    SKILL_USED=$(echo "$FILE_PATH" | sed "s|.*/.claude/skills/||" | cut -d'/' -f1)
  fi
fi

# Also catch when skill names appear in prompts (PostToolUse on Bash that mentions a skill)
if [[ -z "$SKILL_USED" && "$TOOL_NAME" == "Bash" ]]; then
  CMD=$(echo "$TOOL_INPUT" | jq -r '.command // ""' 2>/dev/null)
  if [[ "$CMD" == *"/.claude/skills/"* ]]; then
    SKILL_USED=$(echo "$CMD" | grep -o '/.claude/skills/[^/]*' | head -1 | sed 's|/.claude/skills/||')
  fi
fi

if [[ -z "$SKILL_USED" ]]; then
  echo "{}"
  exit 0
fi

# Verify it's an actual skill directory
if [[ ! -d "$SKILLS_DIR/$SKILL_USED" ]]; then
  echo "{}"
  exit 0
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DATE=$(date +"%Y-%m-%d")
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // ""' 2>/dev/null)

# Append to log
echo "{\"skill\":\"$SKILL_USED\",\"timestamp\":\"$TIMESTAMP\",\"date\":\"$DATE\",\"session\":\"$SESSION_ID\",\"tool\":\"$TOOL_NAME\"}" >> "$LOG_FILE"

# Update stats JSON
python3 - <<PYEOF
import json, os, sys
from datetime import datetime

stats_file = "$STATS_FILE"
log_file = "$LOG_FILE"
skill = "$SKILL_USED"
today = "$DATE"

# Load existing stats
stats = {}
if os.path.exists(stats_file):
    try:
        with open(stats_file) as f:
            stats = json.load(f)
    except:
        stats = {}

if skill not in stats:
    stats[skill] = {"total": 0, "by_date": {}, "last_used": None, "first_used": None}

stats[skill]["total"] += 1
stats[skill]["by_date"][today] = stats[skill]["by_date"].get(today, 0) + 1
stats[skill]["last_used"] = "$TIMESTAMP"
if not stats[skill]["first_used"]:
    stats[skill]["first_used"] = "$TIMESTAMP"

with open(stats_file, "w") as f:
    json.dump(stats, f, indent=2)
PYEOF

echo "{}"
