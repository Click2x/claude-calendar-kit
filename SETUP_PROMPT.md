# Setup prompt

Paste this into a new Claude Code chat:

```text
Set up https://github.com/Click2x/claude-calendar-kit for me. Read INSTALL.md and follow it.
```

That is all. Claude follows [`INSTALL.md`](INSTALL.md): it installs everything quietly, then walks you through a short welcome (scan your projects or tell it about yourself, an optional pet, pinning the calendar, links to chats that need attention) and ends with your commands: `/scan`, `/next`, `/pet`, `/calendar`, `/sort`. It asks before connecting any account, publishing anything, or marking a task to run on its own. Skills load when a chat starts, so open a new chat afterwards and type `/next`.

Installing by hand instead: `python install.py` (see the README).
