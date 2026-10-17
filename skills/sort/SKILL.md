---
name: sort
description: Re-sort the Claude Calendar by priority. Use when the user types /sort or asks what to do first, or to reprioritize the calendar.
---

Run every `cal.py` command from `~/.claude/calendar` (or give its full path). Whenever a `cal.py` command changes the calendar and prints a note about republishing, republish `calendar.html` to the same artifact URL, in place, before you reply, so the user never has to ask you to update the calendar.

The user typed /sort. Re-order their calendar by priority, with their say-so before anything is saved.

1. Run `python cal.py sort` (a preview, nothing is saved). It ranks open tasks within each lane using: overdue, how many other tasks it unblocks, security items (revoke, rotate, exposed keys), quick wins, and whether it is waiting on the user. Fixed-time tasks are left alone.
2. Show the top of the list in plain words, best first: what to do first and why, one line each. Give the chat link for any item that has one (`cal.py` prints `-> chat: [title](#session)`; paste it as is). Call out anything the ranking would surprise them with.
3. Ask: **apply this order, or adjust it?** They can say "move X up", "ignore Y", or "that's fine". Adjust by setting `prio` on a task before applying (`python cal.py show ID` then edit via your normal tools, or add a note and re-run).
4. On a yes: `python cal.py sort --apply` (writes the order and recomputes the schedule), then refresh the page the same way `/calendar` does if they have a published one.
5. Finish with the first three things to do now. Do not start any of them unless asked.
