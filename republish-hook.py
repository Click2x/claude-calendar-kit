#!/usr/bin/env python3
"""Claude Code PostToolUse hook: after a command that changes the calendar, remind Claude to republish the page.

cal.py already re-renders calendar.html locally after every change, but only Claude can publish the artifact, so this hook
adds a short instruction to the conversation (only when you have a published page: config.json has "artifactUrl").
It reads the hook event from stdin and prints JSON. It never changes anything itself and always exits 0.

Wire it up in ~/.claude/settings.json (INSTALL.md offers to do this, and asks first):
  "hooks": {"PostToolUse": [{"matcher": "Bash|PowerShell", "hooks": [{"type": "command", "command": "python ~/.claude/calendar/republish-hook.py"}]}]}
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CHANGES = re.compile(
    r"cal\.py\s+(add|done|skip|block|review|reviewed|force|start|attach|followup|replan|note"
    r"|pet\s+(set|on|off)|config\s+set|sort\s+--apply)\b"
)


def main() -> int:
    try:
        event = json.load(sys.stdin)
        command = (event.get("tool_input") or {}).get("command", "") or ""
    except (ValueError, AttributeError):
        return 0
    if "cal.py" not in command or not CHANGES.search(command) or re.search(r"\s(-h|--help)\b", command):
        return 0
    try:
        cfg = json.loads((Path(__file__).resolve().parent / "config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0
    url = cfg.get("artifactUrl")
    if not url:
        return 0
    note = (
        "The calendar just changed (the local calendar.html is already re-rendered). Before your final reply, republish "
        f"{Path(__file__).resolve().parent / 'calendar.html'} to the same artifact in place: {url} (Artifact tool, publish with "
        "that url; if it is refused with a newer live version, read it and publish again; never create a second artifact). "
        "If you are making several calendar changes in a row, publish once after the last one."
    )
    sys.stdout.write(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": note}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
