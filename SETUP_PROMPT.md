# Setup prompt

The short version: tell your Claude `Set up https://github.com/Click2x/claude-calendar-kit for me. Read INSTALL.md and follow it.` The prompt below is the longer, self-contained alternative.

Paste this into a new Claude Code session on your machine. It sets up the calendar and the prioritization project from this repo.

```text
Set up the Claude Calendar kit from this repository (https://github.com/Click2x/claude-calendar-kit, or the local copy I give you). Everything stays private to this machine and nothing is sent, posted or published without asking me first.

1. Copy cal.py and render_html.py into ~/.claude/calendar/. Do not copy any tasks.json: start from examples/tasks.example.json, edited to my own projects.
2. Install templates/calendar-runner.SKILL.md as a scheduled task named "calendar-runner" that runs every 30 minutes, replacing <CALENDAR_DIR> with the real path.
3. Render the calendar page with render_html.py and publish it as a private artifact. Update that one artifact in place; never create a second.
4. Copy skills/next/SKILL.md to ~/.claude/skills/next/SKILL.md so /next works.
5. Set up the "Project prioritization" project from docs-project-prioritization.md in a folder I choose.
6. Show me the plan first. Ask before connecting any account or reading messages. Tell me what you could not verify.
7. When done, tell me to open a NEW chat: skills are loaded when a chat starts, so /next will not appear in this one.
```

After setup, open a new chat and type `/next`. If it doesn't appear, restart Claude Code once.
