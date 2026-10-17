---
name: scan
description: Scan the user's project folders (read-only), summarize what is there and how recently each was touched, and offer to put the ones they care about on the calendar. Use when the user types /scan or asks Claude to find their projects.
---

Run every `cal.py` command from `~/.claude/calendar` (or give its full path).

The user typed /scan. Find their projects and offer to track them on the shared Claude Calendar. This is read-only until they say yes to adding something.

1. **Where to look.** If you do not already know, ask once which folders to scan (suggest `~/Documents`, `~/projects`, `~/code`, `~/dev`; skip anything they exclude). Scan only those, one or two levels deep.
2. **What counts as a project.** Any folder one or two levels inside the folders they chose, including plain ones (notes, documents, writing, no code). Mark the ones with a `.git`, `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `*.sln`, `project.godot`, or a README as "code/project" and list the rest as "plain folder". Skip `node_modules`, `.venv`, build output, caches and hidden system folders.
3. **What to read per project** (cheap, read-only): the last-modified date, (where there is a git repo) the current branch and the date of the last commit, the number of uncommitted changes, and a count of `TODO` / `FIXME` lines. Never open `.env`, key files, credentials, or anything that looks like a secret, and never run a project's own code or scripts.
4. **Show it** as a short table sorted by most recently touched: name, last activity, state (clean, uncommitted work, open TODOs). Mark the ones untouched for 30 days or more as **neglected**. Give a one-line guess at what each is, only if the README makes it obvious.
5. **Ask which to track.** Offer: all active ones, a chosen few, or none. For each tracked project, propose one or two concrete next steps (from TODOs, uncommitted work, or open branches). Add them only on a yes:
   `python cal.py add --title "..." --when "+1d" --project NAME --cwd DIR [--lane owner]`
   Anything only the user can do goes in lane `owner`. Never mark a task `auto` unless they say it may run unattended.
6. **Close** with what you added, what you skipped, and a one-line pointer to `/next`. If `cal.py pet say` prints a line, you may open with it.
