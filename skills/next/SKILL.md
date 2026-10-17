---
name: next
description: Show what is open on the shared Claude Calendar (what is waiting for the user, what is running, what is ready next), with clickable links to the chats involved, then ask whether that is what they meant or whether they have something else in mind, including building something new. Use when the user types /next or asks "what's next", "what's waiting on me", or "where did I leave off".
---

Run every `cal.py` command from `~/.claude/calendar` (or give its full path).

The user typed /next. Give them the open items from their shared Claude Calendar, with a way to jump to each chat, and then check what they actually want.

1. Gather, with the calendar CLI (default folder ~/.claude/calendar):
   - `python cal.py replan` first, so the due times are current.
   - `python cal.py reviews` for work waiting on the user and the user's own tasks that are ready now.
   - `python cal.py list` for what is running and what is coming next.
   - For a task that has a chat, read its "session" and "sessionTitle" with `python cal.py show ID`. A task without a session has no chat yet.
1b. Run `python cal.py pet say`. If it prints something, that is the user's calendar pet speaking: open your answer with that line on its own (the face and the words, exactly as printed), then continue in your own voice. If it prints nothing, the user has no pet or turned it off: skip this and never mention it.
2. Present it in this order, newest and most important first, and keep it short:
   - **Waiting on you** (status review, or the user's own tasks that are ready): one line each, what it is and what you need from them. Give each chat as a clickable link: `[chat title](#local_<session id>)`. Never paste a bare `claude://` link, since that needs copy and paste. `cal.py list` and `cal.py reviews` already print `-> chat: [title](#session)`: use those as they are. Apply this to every mention of a waiting item in this reply, including any "waiting for your go" line, and say plainly when something has no chat yet.
   - **Running now**: one line each, with the chat link.
   - **Ready next**: the top three, so they can see the queue.
   - If something has no chat yet, say so and offer to start one.
3. Then ask, in your own words and not as a fixed script: is this what they meant, or did they have something else in mind? Offer concrete options: pick one item to do now; start the next ready task; clean up the calendar (stale, duplicate or overdue items); or build something new. If they want something new, ask what it connects to, using their projects and what you remember about them, and offer two or three starting ideas.
4. Voice: sound like a person who knows them. Use what the user's memory says about how they like to be talked to (tone, length, how much detail, how they work), and mirror their energy: short and quick if they are, more careful if they are. Do not recite their memory back to them. If you know nothing about them, stay warm, plain and brief.
5. Do not start tasks, send messages, change the calendar or open anything until they answer. When they pick an item, do it or start its session, and create the follow-up step when it finishes (`cal.py followup`).
