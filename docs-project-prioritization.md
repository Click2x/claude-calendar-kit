# Project prioritization project

A companion "project" for the calendar. Create a folder for it (for example `~/projects/prioritization`), put this file in it as `README.md`, and open it in Claude Code. It turns the calendar into a place that notices what you are neglecting and suggests what to do next. It is generic: nothing here is specific to one person.

## Jobs

1. **Received messages.** With your permission, read recent mail and messages (any connectors you have granted) and turn anything that needs action or a reply into a calendar task with a due date and a one-line summary. Never reply, send, delete or archive anything. Drafts only, and only when asked.
2. **Calendar cleanup.** Find overdue, duplicate, stale and conflicting tasks. Propose merges, skips and reschedules as a short list. Apply nothing until you say yes.
3. **Neglected projects.** For each project on the calendar and each folder you work in, track last activity (a task done, a session, a file change). Flag the ones that have had little attention, and when you open the chat, ask about the two or three most neglected ones and what is blocking them.
4. **New project ideas.** Using your shared context (projects, notes, memory), suggest new projects that build on what you already do or know. Each idea gets a one-paragraph pitch, a first step and what it connects to. Offer three at a time and add one to the calendar only if you pick it.
5. **Weekly summary.** A short briefing: what got done, what is waiting on you, what is neglected, and the top three priorities for the next week.

## Rules

- Ask before connecting any account or reading messages, and say which connector you want to use.
- Never send, post, publish, buy or delete anything on your behalf.
- When a task finishes, create its follow-up step on the calendar (`cal.py followup` or `--followup`).
- Keep a short notes file with your priorities and preferences so suggestions improve over time.
