---
name: pet
description: Choose, rename, or turn off the calendar pet. Use when the user types /pet or asks to change the pet's style, name, or to turn the pet on or off.
---

Run every `cal.py` command from `~/.claude/calendar` (or give its full path).

The user typed /pet. Their calendar has an optional pet that reacts to their tasks and speaks in the calendar page and at the top of /next. Use the calendar CLI (default folder ~/.claude/calendar).

1. Run `python cal.py pet` to list the styles (the current one is marked, and it says if the pet is off).
2. If they gave a style, a name, or "off" / "on", do it directly:
   - `python cal.py pet set STYLE [--name NAME]`
   - `python cal.py pet off` (opt out: no pet on the page or in /next) or `python cal.py pet on`
   Then show `python cal.py pet say` so they hear it in its new voice.
3. If they gave nothing, show the styles as a short list with each style's face and one-line personality, say which is current, and ask which they want, or whether they would rather have no pet. Keep it light. The page also has a Change pet picker, and that choice is remembered per browser.
4. Never pick for them. Opting out is always fine and needs no explanation.
