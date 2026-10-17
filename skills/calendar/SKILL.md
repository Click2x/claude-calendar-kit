---
name: calendar
description: Bring up the user's Claude Calendar page. Use when the user types /calendar or asks to see, open or pin their calendar.
---

Run every `cal.py` command from `~/.claude/calendar` (or give its full path).

The user typed /calendar. Show them their calendar page (default folder ~/.claude/calendar).

1. Read where it lives: `python cal.py config get artifactUrl`.
   - **A published page exists** (the URL is set): refresh it first so it is current (`python render_html.py`, then republish the same file to that same artifact URL, in place; never create a second one), then open it with the Artifact tool (`action: "open"`) and give them the link.
   - **No published page yet:** run `python render_html.py`, then offer once to publish `~/.claude/calendar/calendar.html` as a **private** artifact. If they say yes, publish it, save the URL with `python cal.py config set artifactUrl <url>`, and open it. If they say no, tell them the file path to open locally.
2. If they asked to **pin** it, pin the artifact (Artifact tool, `action: "pin"`). Only pin when they ask, and tell them you did. Never pin as a side effect.
3. Finish with one line: what is on the page that needs them (`python cal.py reviews`, with chat links as printed), and that the commands are listed on the page itself.
