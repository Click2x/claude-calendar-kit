# Claude Calendar kit

One task calendar for all of your projects, built for use with Claude Code. Plain JSON, Python standard library only, private to your machine.

- `cal.py` is the command line. `tasks.json` (not in this repo) is the source of truth.
- `render_html.py` renders a self-contained interactive calendar page (month view, day outline, up-next list, and a small mascot that reacts to your task state).
- `templates/calendar-runner.SKILL.md` is a dispatcher you run as a scheduled task: it replans, starts ready tasks (one per lane) and tells you when something needs your review.
- `docs-project-prioritization.md` describes a companion project that surfaces received messages, cleans up the calendar and suggests projects.
- `skills/next/SKILL.md` is a `/next` skill: copy it to `~/.claude/skills/next/`. Type `/next` in any chat to see what is waiting on you, running and ready, with links to the chats, then it asks what you actually want (or whether to build something new).
- `SETUP_PROMPT.md` is a prompt that sets all of this up for you.

## Ideas

- **Lanes.** A lane is a resource that can run one task at a time (for example `gpu`, `cpu`, `owner`). Lane `owner` is for work only you can do.
- **Dependencies.** A task can list `after` ids. `cal.py replan` starts each task as soon as its dependencies and lane are free.
- **Review.** Work that needs you ends in status `review`, not `done`, and does not block its dependents. `cal.py reviewed ID` replans so nothing waits.
- **Follow-ups.** When a task completes, `--followup "TITLE|PROMPT|auto|LANE"` (or `cal.py followup`) creates the next step.
- **Auto tasks.** `auto: true` means you pre-authorized exactly what the prompt describes. Anything needing money, accounts, credentials or irreversible steps is blocked for you, never run.

## Quick start

```bash
python cal.py add --title "Write tests" --when tomorrow --project my-app --auto --lane cpu --prompt "..."
python cal.py list
python cal.py replan
python cal.py ready
python cal.py reviews
python render_html.py
```

Run `python cal.py -h` for every command. License: MIT.
