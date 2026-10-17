#!/usr/bin/env python3
"""Install the Claude Calendar kit. Stdlib only, safe to re-run, never overwrites your tasks.

  python install.py [--home DIR] [--project-dir DIR] [--dry-run]

Does the deterministic part: copies cal.py and render_html.py to <home>/.claude/calendar, installs the /next skill to
<home>/.claude/skills/next, seeds tasks.json from examples/ ONLY if you have none, writes the dispatcher instructions with the
real path filled in, and renders the first page. Optionally creates the prioritization project folder.
Registering the scheduled dispatcher and publishing the page need the Claude app, so INSTALL.md has Claude do those.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--home", default=str(Path.home()), help="home directory to install under (default: your home)")
    ap.add_argument("--project-dir", help="also create the Project prioritization folder here")
    ap.add_argument("--pet", default="waifu", help="pet style to start with, or 'none' to opt out (see pets.json; change any time with cal.py pet)")
    ap.add_argument("--no-pet", action="store_true", help="same as --pet none")
    ap.add_argument("--dry-run", action="store_true", help="show what would happen and change nothing")
    a = ap.parse_args()
    home = Path(a.home).expanduser()
    cal = home / ".claude" / "calendar"
    skill = home / ".claude" / "skills" / "next"
    pet_skill = home / ".claude" / "skills" / "pet"
    log = []

    def do(msg: str, fn=None) -> None:
        log.append(("would: " if a.dry_run else "") + msg)
        if fn and not a.dry_run:
            fn()

    do(f"create {cal}", lambda: cal.mkdir(parents=True, exist_ok=True))
    for f in ("cal.py", "render_html.py"):
        do(f"copy {f} -> {cal / f}", lambda f=f: shutil.copy2(HERE / f, cal / f))
    do(f"install /next skill -> {skill / 'SKILL.md'}", lambda: (skill.mkdir(parents=True, exist_ok=True), shutil.copy2(HERE / "skills" / "next" / "SKILL.md", skill / "SKILL.md")))
    do(f"copy pets.json -> {cal / 'pets.json'}", lambda: shutil.copy2(HERE / "pets.json", cal / "pets.json"))
    do(f"install /pet skill -> {pet_skill / 'SKILL.md'}", lambda: (pet_skill.mkdir(parents=True, exist_ok=True), shutil.copy2(HERE / "skills" / "pet" / "SKILL.md", pet_skill / "SKILL.md")))
    if not (cal / "config.json").exists():
        off = a.no_pet or a.pet.lower() in ("none", "off")
        cfg = json.dumps({"petEnabled": False} if off else {"pet": a.pet, "petEnabled": True}) + chr(10)
        do(f"write {cal / 'config.json'} ({'no pet' if off else 'pet style ' + a.pet})", lambda: (cal / "config.json").write_text(cfg, encoding="utf-8"))
    if not (cal / "tasks.json").exists():
        do(f"seed {cal / 'tasks.json'} from the example (edit it to your projects)", lambda: shutil.copy2(HERE / "examples" / "tasks.example.json", cal / "tasks.json"))
    else:
        log.append(f"kept your existing {cal / 'tasks.json'}")

    def runner() -> None:
        t = (HERE / "templates" / "calendar-runner.SKILL.md").read_text(encoding="utf-8")
        (cal / "calendar-runner.SKILL.md").write_text(t.replace("<CALENDAR_DIR>", cal.as_posix()), encoding="utf-8")

    if not (cal / "dispatcher.json").exists():
        do(f"write {cal / 'dispatcher.json'} (when the dispatcher ticks, for the page's countdown)", lambda: (cal / "dispatcher.json").write_text('{"minutes": [14, 44], "jitterSeconds": 0}\n', encoding="utf-8"))
    do(f"write dispatcher instructions -> {cal / 'calendar-runner.SKILL.md'}", runner)
    if a.project_dir:
        pd = Path(a.project_dir).expanduser()
        do(f"create project folder {pd}", lambda: (pd.mkdir(parents=True, exist_ok=True), shutil.copy2(HERE / "docs-project-prioritization.md", pd / "README.md")))
    if not a.dry_run:
        r = subprocess.run([sys.executable, str(cal / "render_html.py")], capture_output=True, text=True)
        log.append("rendered " + (r.stdout.strip() or r.stderr.strip()))
    print("\n".join(log))
    print("\nNext: register the dispatcher and publish the page (see INSTALL.md), then open a NEW chat and type /next.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
