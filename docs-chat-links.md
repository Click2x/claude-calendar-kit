# Chat links: make every mention of another chat clickable

When Claude mentions work that is waiting on you (your go, your approval, your review), it should hand you a link to the chat that work belongs to, so you can get there in one click.

## The rule

> Whenever you mention a task or chat that is waiting on the user's go, approval or review, include a clickable link to its chat, written as `[chat title](#local_<session id>)`. A bare `claude://...` URL is not clickable, and links inside a published calendar page are blocked by the page's sandbox, so use this in-app form in your replies. If the item has no chat yet, say so plainly instead of leaving it out.

## How the kit supports it

- `cal.py attach ID SESSION_ID --title "Chat name"` links a task to its chat. The dispatcher does this when it starts a session.
- A follow-up created with `--followup` or `cal.py followup` inherits its parent's chat, so a hand-test points at the chat that built the thing.
- `cal.py list`, `cal.py reviews` and `cal.py ready` print `-> chat: [title](#session)` on any task that has one. Paste those links as they are.
- The `/next` skill follows the rule and says so when a task has no chat yet.

## Make it permanent (optional)

Ask your Claude to remember the rule as a preference ("always include clickable chat links for anything waiting on me"). In Claude Code that is a memory entry or a line in `~/.claude/CLAUDE.md`. Do it only if you want it everywhere, not just in calendar chats.
