#!/usr/bin/env python3
"""
Claude Calendar - one shared task calendar for ALL of your projects. Plain JSON, stdlib only, private to this machine.

  python cal.py list   [--project NAME] [--all]        open tasks (soonest first); --all adds done/skipped
  python cal.py due    [--project NAME] [--json]       open tasks that are due now or overdue
  python cal.py add --title T --when WHEN [--project NAME] [--cwd DIR] [--prompt TEXT] [--auto] [--repeat daily|weekly|monthly]
                       [--lane L] [--est HOURS] [--prio N] [--after ID ...] [--review] [--scheduled-task ID]
                       --auto needs --cwd (existing folder) and --prompt; --after ids look like t-YYYYMMDD-NN (see `cal.py list`)
                       WHEN = 2026-11-01 | 2026-11-01T09:00 | tomorrow | +3d | +6h | mon..sun
  python cal.py show ID
  python cal.py done ID [--result TEXT] [--followup "TITLE|PROMPT|auto|LANE"]   marks done and can create the next step; a repeating task schedules its next occurrence
  python cal.py skip ID [--result TEXT]
  python cal.py note ID TEXT                            append a note
  python cal.py ready  [--json]                         auto tasks that can start NOW (deps met, due passed, lane free)
  python cal.py attach ID SESSION_ID                    link the task to the chat session working on it (the page then shows an Open chat link)
  python cal.py start ID [--session SESSION_ID]                                mark running (the dispatcher calls this before launching a session)
  python cal.py followup ID --title T [--prompt P] [--auto] [--cwd DIR] [--lane L] [--est H] [--review]   add the next step after task ID (inherits project/cwd/lane, waits on ID; --auto needs a prompt and a folder)
  done/review/reviewed also take --followup "TITLE|PROMPT|auto|LANE" (repeatable) and create declared `followups` templates
  python cal.py review ID --result TEXT                 auto work finished but needs the owner: status review (does not block dependents)
  python cal.py reviewed ID [--result TEXT]             owner finished reviewing / doing it: done, then replan (pulls dependents forward)
  python cal.py pet [list|say|on|off|set STYLE [--name NAME]]   your calendar pet: pick a style, rename it, or hear what it has to say
  python cal.py sort [--apply]                          re-sort by priority (overdue, unblocks others, waiting on you, quick wins); preview unless --apply
  python cal.py config [get|set KEY VALUE]              settings in config.json (pet, petEnabled, artifactUrl)
  python cal.py reviews                                 everything waiting on the owner (review + due owner tasks)
  python cal.py force ID                                run this task NOW: ignore its due time, dependencies and notBefore (set by the page's Run now button)
  python cal.py replan [--from WHEN]                    recompute due times: every task starts as soon as its deps and lane are free
Task extras: after (list of ids), lane (owner = only you can do it | main | any resource name you choose, e.g. cpu, gpu | fixed), prio (lower first), est (hours), notBefore (iso), fixed (never moved).

Tasks live in tasks.json beside this file. `auto` tasks are executed unattended by the scheduled task "calendar-runner"
(it runs the task's prompt in the task's cwd, then marks it done with a result). A task with --scheduled-task is run by that
scheduled task itself; the runner only mirrors its done state.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

FILE = Path(__file__).resolve().parent / "tasks.json"
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def now() -> datetime:
    return datetime.now().astimezone()


def load() -> dict:
    if not FILE.exists():
        return {"version": 1, "tasks": []}
    return json.loads(FILE.read_text(encoding="utf-8"))


_SAVED = False


def save(db: dict) -> None:
    global _SAVED
    _SAVED = True
    fd, tmp = tempfile.mkstemp(dir=FILE.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    os.replace(tmp, FILE)


def parse_when(s: str) -> str:
    s = s.strip().lower()
    n = now()
    if s in ("today", "now"):
        return n.replace(microsecond=0).isoformat()
    if s == "tomorrow":
        return (n + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0).isoformat()
    if s[:1] == "+" and s[-1:] in "dhw" and s[1:-1].isdigit():
        k, unit = int(s[1:-1]), s[-1]
        return (n + (timedelta(days=k) if unit == "d" else timedelta(hours=k) if unit == "h" else timedelta(weeks=k))).replace(microsecond=0).isoformat()
    if s[:3] in DAYS and len(s) <= 9:
        ahead = (DAYS.index(s[:3]) - n.weekday()) % 7 or 7
        return (n + timedelta(days=ahead)).replace(hour=9, minute=0, second=0, microsecond=0).isoformat()
    try:
        d = datetime.fromisoformat(s.replace("z", "+00:00"))
    except ValueError:
        sys.exit(f"can't read --when '{s}'. Use 2026-11-01, 2026-11-01T09:00, tomorrow, today, +3d, +6h, +2w or mon..sun")
    if d.tzinfo is None:
        d = d.astimezone() if "t" in s else d.replace(hour=9, minute=0).astimezone()
    return d.replace(microsecond=0).isoformat()


GRACE = timedelta(minutes=15)  # a task is only "overdue" once it is this far past its time, so a task made a moment ago never is


def is_overdue(t: dict) -> bool:
    return t["status"] == "open" and due_dt(t) < now() - GRACE


def due_dt(t: dict) -> datetime:
    return datetime.fromisoformat(t["due"])


def next_id(db: dict) -> str:
    stamp = now().strftime("%Y%m%d")
    n = 1 + sum(1 for t in db["tasks"] if t["id"].startswith("t-" + stamp))
    return f"t-{stamp}-{n:02d}"


def find(db: dict, tid: str) -> dict:
    for t in db["tasks"]:
        if t["id"] == tid:
            return t
    sys.exit(f"no task {tid}")


def fmt(t: dict) -> str:
    d = due_dt(t)
    flag = {"open": " ", "done": "x", "skipped": "-", "blocked": "!", "running": ">", "review": "?"}.get(t["status"], "?")
    over = " OVERDUE" if is_overdue(t) else ""
    mode = "auto" if t.get("auto") else ("sched" if t.get("scheduledTaskId") else "manual")
    return f"[{flag}] {t['id']}  {d:%Y-%m-%d %H:%M}  {t.get('project', '-'):<12} {mode:<6} {t['title']}{over}{chat_link(t)}"


def chat_link(t: dict) -> str:
    """Markdown link to the chat working on a task. Paste it as-is into a reply: in the Claude app it opens with one click.
    (A bare claude:// URL is not clickable, so we print the in-app form.) Empty when the task has no chat yet."""
    sid = t.get("session")
    if not sid:
        return ""
    return f"  -> chat: [{t.get('sessionTitle') or t['title']}](#{sid})"


def advance(t: dict) -> str | None:
    d = due_dt(t)
    step = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1), "monthly": timedelta(days=30)}.get(t.get("repeat") or "")
    if not step:
        return None
    nd = d + step
    while nd < now():
        nd += step
    return nd.isoformat()


PETS_FILE = FILE.parent / "pets.json"
CONFIG_FILE = FILE.parent / "config.json"


def load_pets() -> dict:
    return json.loads(PETS_FILE.read_text(encoding="utf-8")) if PETS_FILE.exists() else {"default": "plain", "styles": {"plain": {"label": "Plain", "blurb": "", "name": "Status", "faces": {}, "lines": {"idle": ["Nothing pending."]}}}}


def load_cfg() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def pet_state(db: dict) -> tuple[str, int]:
    """Mood by priority: review > blocked > late > running > sleepy (night, nothing else) > idle."""
    ts = db["tasks"]
    review = sum(1 for t in ts if t["status"] == "review")
    blocked = sum(1 for t in ts if t["status"] == "blocked")
    late = sum(1 for t in ts if is_overdue(t))
    running = sum(1 for t in ts if t["status"] == "running")
    for mood, n in (("review", review), ("blocked", blocked), ("late", late), ("running", running)):
        if n:
            return mood, n
    return ("sleepy" if now().hour >= 23 or now().hour < 6 else "idle"), 0


def pet_say(db: dict) -> str:
    pets, cfg = load_pets(), load_cfg()
    if cfg.get("petEnabled") is False:
        return ""
    key = cfg.get("pet") if cfg.get("pet") in pets["styles"] else pets["default"]
    st = pets["styles"][key]
    mood, n = pet_state(db)
    lines = st["lines"].get(mood) or st["lines"].get("idle") or [""]
    line = lines[(now().timetuple().tm_yday + now().hour) % len(lines)]
    name = cfg.get("petName") or st.get("name", "")
    line = line.replace("{n}", str(n)).replace("{s}", "" if n == 1 else "s").replace("{name}", name)
    return (st["faces"].get(mood, "") + " " + line).strip()


SATISFIED = ("done", "review", "skipped")
EST_DEFAULT = {"owner": 0.25}


def est_h(t: dict) -> float:
    return float(t.get("est") or EST_DEFAULT.get(t.get("lane"), 1.5 if t.get("lane") == "gpu" else 1.0))


def deps_met(db: dict, t: dict) -> bool:
    by = {x["id"]: x for x in db["tasks"]}
    return all(by.get(d, {"status": "done"})["status"] in SATISFIED for d in t.get("after") or [])


def replan(db: dict, start: datetime) -> None:
    """Greedy schedule: per lane in prio order, each open task starts at max(lane free, deps end, notBefore, start)."""
    by = {x["id"]: x for x in db["tasks"]}
    end: dict[str, datetime] = {}
    cursor: dict[str, datetime] = {}
    for t in db["tasks"]:
        if t["status"] in ("done", "skipped", "review"):
            end[t["id"]] = datetime.fromisoformat(t["doneAt"]) if t.get("doneAt") else start
        elif t["status"] == "running":
            lane = t.get("lane") or "fixed"
            e = datetime.fromisoformat(t.get("startedAt") or start.isoformat()) + timedelta(hours=est_h(t))
            end[t["id"]] = max(e, start)
            cursor[lane] = max(cursor.get(lane, start), end[t["id"]])
    todo = [t for t in db["tasks"] if t["status"] in ("open", "blocked") and not t.get("forced")]
    todo.sort(key=lambda t: (t.get("prio", 50), due_dt(t)))
    pending = list(todo)
    guard = 0
    while pending and guard < 10000:
        guard += 1
        progressed = False
        for t in list(pending):
            deps = t.get("after") or []
            if any(d in by and by[d]["status"] in ("open", "blocked") and d not in end for d in deps):
                continue
            lane = t.get("lane") or "fixed"
            if t.get("fixed") or lane == "fixed":
                st = due_dt(t)
            else:
                ready_at = max(start, cursor.get(lane, start), *[end[d] for d in deps if d in end])
                floor = datetime.fromisoformat(t["notBefore"]) if t.get("notBefore") else start
                st = max(ready_at, floor)
                # A task waiting for a date far ahead must not hold the lane: only advance the lane if it really starts soon.
                if st - ready_at <= timedelta(hours=12):
                    cursor[lane] = st + timedelta(hours=est_h(t))
            t["due"] = st.replace(microsecond=0).isoformat()
            end[t["id"]] = st + timedelta(hours=est_h(t))
            pending.remove(t)
            progressed = True
        if not progressed:
            break


def make_followup(db: dict, parent: dict, f: dict) -> dict:
    """Create the next step after `parent`: inherits project/cwd/lane, waits on parent, replan schedules it."""
    if f.get("auto"):
        fcwd = f.get("cwd") or parent.get("cwd", "")
        if not (f.get("prompt") and fcwd and Path(fcwd).is_dir()):
            sys.exit(f"follow-up '{f['title']}': an auto task runs unattended, so it needs a prompt (exactly what it may do) and an existing folder (--cwd, or one inherited from the task it follows). Nothing was saved.")
    t = {"id": next_id(db), "title": f["title"], "project": f.get("project") or parent.get("project", "general"),
         "cwd": f.get("cwd") or parent.get("cwd", ""), "due": now().replace(microsecond=0).isoformat(), "repeat": None,
         "prompt": f.get("prompt", ""), "auto": bool(f.get("auto", False)), "status": "open",
         "createdAt": now().replace(microsecond=0).isoformat(), "scheduledTaskId": None, "notes": [], "result": None, "doneAt": None,
         "lane": f.get("lane") or ("owner" if not f.get("auto") else parent.get("lane")), "prio": f.get("prio", parent.get("prio", 50)),
         "est": f.get("est"), "after": [parent["id"]] + [x for x in f.get("after", []) if x != parent["id"]], "followupOf": parent["id"]}
    if parent.get("session"):
        t["session"] = parent["session"]
        t["sessionTitle"] = parent.get("sessionTitle", "")
    if f.get("reviewOnDone"):
        t["reviewOnDone"] = True
    db["tasks"].append(t)
    return t


def spawn_followups(db: dict, parent: dict, extra: list[dict]) -> list[dict]:
    """Declared templates (parent['followups']) plus any passed on the command line; each created once."""
    made = []
    for f in list(parent.get("followups") or []) + extra:
        if any(x.get("followupOf") == parent["id"] and x["title"] == f["title"] for x in db["tasks"]):
            continue
        made.append(make_followup(db, parent, f))
    parent["followups"] = []
    return made


def sort_plan(db: dict) -> list[tuple[dict, float, list[str]]]:
    """Score open tasks by priority. Higher score = sooner. Returns [(task, score, reasons)] best first.
    Reasons: overdue, waiting on you (review), unblocks other tasks, quick win. Fixed-time tasks are left alone."""
    open_ids = {t["id"] for t in db["tasks"] if t["status"] in ("open", "blocked", "review", "running")}
    blocks: dict[str, int] = {}
    for t in db["tasks"]:
        if t["status"] in ("open", "blocked"):
            for d in t.get("after") or []:
                blocks[d] = blocks.get(d, 0) + 1
    out = []
    for t in db["tasks"]:
        if t["status"] not in ("open", "blocked") or t.get("fixed") or (t.get("lane") or "") == "fixed":
            continue
        score, why = 0.0, []
        late_days = (now() - GRACE - due_dt(t)).total_seconds() / 86400
        if late_days > 0:
            score += min(10.0, 3.0 + late_days * 2)
            why.append("overdue")
        n = blocks.get(t["id"], 0)
        if n:
            score += 4.0 * n
            why.append(f"unblocks {n} task{'s' if n != 1 else ''}")
        if (t.get("lane") or "") == "owner":
            score += 1.0
        if est_h(t) <= 0.5:
            score += 1.5
            why.append("quick win")
        if any(w in t["title"].lower() for w in ("revoke", "rotate", "security", "credential", "exposed", "leak")):
            score += 4.0
            why.append("security")
        if t.get("status") == "blocked":
            score -= 5.0
            why.append("blocked")
        out.append((t, score, why))
    out.sort(key=lambda x: (-x[1], due_dt(x[0])))
    return out


def lane_busy(db: dict, lane: str) -> bool:
    return any(t["status"] == "running" and t.get("lane") == lane for t in db["tasks"])


def parse_fu(items: list[str]) -> list[dict]:
    out = []
    for it in items:
        parts = [x.strip() for x in it.split("|")]
        f = {"title": parts[0]}
        if len(parts) > 1 and parts[1]:
            f["prompt"] = parts[1]
        if len(parts) > 2:
            f["auto"] = parts[2].lower() == "auto"
        if len(parts) > 3 and parts[3]:
            f["lane"] = parts[3]
        out.append(f)
    return out


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("--project"); p.add_argument("--all", action="store_true")
    p = sub.add_parser("due"); p.add_argument("--project"); p.add_argument("--json", action="store_true")
    p = sub.add_parser("add")
    p.add_argument("--title", required=True); p.add_argument("--when", required=True); p.add_argument("--project", default="general")
    p.add_argument("--cwd", default=""); p.add_argument("--prompt", default=""); p.add_argument("--auto", action="store_true")
    p.add_argument("--repeat", choices=["daily", "weekly", "monthly"]); p.add_argument("--scheduled-task", dest="sched")
    p.add_argument("--lane", help="owner (only you can do it) or a resource lane such as cpu/gpu; default: owner, or main for --auto")
    p.add_argument("--est", type=float, help="estimated hours"); p.add_argument("--prio", type=int, help="lower runs first")
    p.add_argument("--after", action="append", default=[], metavar="ID", help="task id this one waits for (repeatable)")
    p.add_argument("--review", action="store_true", help="when it finishes, mark it for your review instead of done")
    for name in ("show", "done", "skip", "block"):
        p = sub.add_parser(name); p.add_argument("id")
        if name != "show":
            p.add_argument("--result", default="")
    for name in ("review", "reviewed"):
        p = sub.add_parser(name); p.add_argument("id"); p.add_argument("--result", default="")
    for name in ("done", "review", "reviewed"):
        sub.choices[name].add_argument("--followup", action="append", default=[], metavar="TITLE[|PROMPT[|auto|manual[|LANE]]]",
                                       help="create the next step on the calendar when this completes (repeatable)")
    p = sub.add_parser("followup"); p.add_argument("id"); p.add_argument("--title", required=True); p.add_argument("--prompt", default="")
    p.add_argument("--auto", action="store_true"); p.add_argument("--cwd", default=""); p.add_argument("--lane"); p.add_argument("--est", type=float); p.add_argument("--review", action="store_true")
    p = sub.add_parser("start"); p.add_argument("id"); p.add_argument("--session")
    p = sub.add_parser("attach"); p.add_argument("id"); p.add_argument("session"); p.add_argument("--title", default="")
    p = sub.add_parser("force"); p.add_argument("id")
    p = sub.add_parser("ready"); p.add_argument("--json", action="store_true")
    sub.add_parser("reviews")
    p = sub.add_parser("sort"); p.add_argument("--apply", action="store_true", help="write the new priority order (otherwise just show it)")
    p = sub.add_parser("config"); p.add_argument("action", nargs="?", default="get", choices=["get", "set"]); p.add_argument("key", nargs="?"); p.add_argument("value", nargs="?")
    p = sub.add_parser("pet"); p.add_argument("action", nargs="?", default="list", choices=["list", "set", "say", "off", "on"]); p.add_argument("style", nargs="?"); p.add_argument("--name")
    p = sub.add_parser("replan"); p.add_argument("--from", dest="frm")
    p = sub.add_parser("note"); p.add_argument("id"); p.add_argument("text")
    a = ap.parse_args()
    db = load()

    if a.cmd in ("list", "due"):
        ts = [t for t in db["tasks"] if (not a.project or t.get("project") == a.project)]
        if a.cmd == "due":
            ts = [t for t in ts if t["status"] == "open" and due_dt(t) <= now()]
        elif not a.all:
            ts = [t for t in ts if t["status"] in ("open", "blocked", "running", "review")]
        ts.sort(key=due_dt)
        if getattr(a, "json", False):
            print(json.dumps(ts, indent=2))
        else:
            print("\n".join(fmt(t) for t in ts) or "(none)")
    elif a.cmd == "add":
        if a.auto and not (a.cwd and a.prompt):
            sys.exit("an --auto task runs unattended, so it needs --cwd (the folder to work in) and --prompt (exactly what it may do)")
        known = {x["id"] for x in db["tasks"]}
        bad = [i for i in a.after if i not in known]
        if bad:
            sys.exit("unknown task id(s) in --after: " + ", ".join(bad) + "  (ids look like t-YYYYMMDD-NN; see `cal.py list`)")
        cwd = str(Path(a.cwd).expanduser()) if a.cwd else ""
        if a.auto and not Path(cwd).is_dir():
            sys.exit(f"--cwd {cwd} is not an existing folder")
        due = parse_when(a.when)
        t = {"id": next_id(db), "title": a.title, "project": a.project, "cwd": cwd, "due": due, "repeat": a.repeat,
             "prompt": a.prompt, "auto": bool(a.auto), "status": "open", "createdAt": now().replace(microsecond=0).isoformat(),
             "scheduledTaskId": a.sched, "notes": [], "result": None, "doneAt": None,
             "lane": a.lane or ("main" if a.auto else "owner")}
        if a.est:
            t["est"] = a.est
        if a.prio is not None:
            t["prio"] = a.prio
        if a.after:
            t["after"] = a.after
        if a.review:
            t["reviewOnDone"] = True
        if datetime.fromisoformat(due) > now() + timedelta(hours=1):
            t["notBefore"] = due  # a date you chose in the future is a floor: replan never pulls it earlier
        db["tasks"].append(t)
        replan(db, now())
        save(db)
        print(fmt(t))
    elif a.cmd == "show":
        print(json.dumps(find(db, a.id), indent=2, ensure_ascii=False))
    elif a.cmd == "block":
        t = find(db, a.id)
        t["status"] = "blocked"
        t["result"] = a.result or t.get("result")
        save(db)
        print(fmt(t))
    elif a.cmd in ("done", "skip"):
        t = find(db, a.id)
        t["status"] = "done" if a.cmd == "done" else "skipped"
        t["result"] = a.result or t.get("result")
        t["doneAt"] = now().replace(microsecond=0).isoformat()
        if a.cmd == "done":
            for c in spawn_followups(db, t, parse_fu(getattr(a, "followup", []))):
                print("followup:", fmt(c))
            replan(db, now())
        nxt = advance(t)
        if nxt:
            c = dict(t, id=next_id(db), due=nxt, status="open", result=None, doneAt=None, notes=[], createdAt=now().replace(microsecond=0).isoformat())
            db["tasks"].append(c)
            print("next occurrence:", fmt(c))
        save(db)
        print(fmt(t))
    elif a.cmd == "start":
        t = find(db, a.id); t["status"] = "running"; t["forced"] = False; t["startedAt"] = now().replace(microsecond=0).isoformat()
        if a.session:
            t["session"] = a.session
        save(db); print(fmt(t))
    elif a.cmd == "attach":
        t = find(db, a.id); t["session"] = a.session
        if a.title:
            t["sessionTitle"] = a.title
        save(db); print(fmt(t))
    elif a.cmd == "followup":
        t = find(db, a.id)
        c = make_followup(db, t, {"title": a.title, "prompt": a.prompt, "cwd": a.cwd, "auto": a.auto, "lane": a.lane, "est": a.est, "reviewOnDone": a.review})
        replan(db, now()); save(db); print(fmt(c))
    elif a.cmd == "force":
        t = find(db, a.id)
        if t["status"] not in ("open", "blocked"):
            sys.exit(f"{a.id} is {t['status']}, nothing to run")
        t["status"] = "open"; t["forced"] = True; t["due"] = now().replace(microsecond=0).isoformat()
        t["notes"] = t.get("notes", []) + [{"at": t["due"], "text": "run now requested from the calendar page"}]
        save(db); print(fmt(t))
    elif a.cmd == "review":
        t = find(db, a.id); t["status"] = "review"; t["result"] = a.result or t.get("result")
        t["doneAt"] = now().replace(microsecond=0).isoformat()
        for c in spawn_followups(db, t, parse_fu(a.followup)):
            print("followup:", fmt(c))
        replan(db, now()); save(db); print(fmt(t))
    elif a.cmd == "reviewed":
        t = find(db, a.id); t["status"] = "done"; t["result"] = a.result or t.get("result")
        t["doneAt"] = now().replace(microsecond=0).isoformat()
        for c in spawn_followups(db, t, parse_fu(a.followup)):
            print("followup:", fmt(c))
        replan(db, now()); save(db); print(fmt(t))
        for x in db["tasks"]:
            if x["status"] == "open" and a.id in (x.get("after") or []) and due_dt(x) <= now():
                print("now ready:", fmt(x))
    elif a.cmd == "ready":
        ts = [t for t in db["tasks"] if t["status"] == "open" and (t.get("auto") or t.get("forced")) and (t.get("forced") or (due_dt(t) <= now() and deps_met(db, t))) and not lane_busy(db, t.get("lane") or "fixed")]
        seen, out = set(), []
        for t in sorted(ts, key=lambda t: (not t.get("forced"), t.get("prio", 50), due_dt(t))):
            ln = t.get("lane") or "fixed"
            if ln in seen:
                continue
            seen.add(ln); out.append(t)
        print(json.dumps(out, indent=2) if a.json else ("\n".join(fmt(t) for t in out) or "(none ready)"))
    elif a.cmd == "pet":
        pets, cfg = load_pets(), load_cfg()
        cur = cfg.get("pet") if cfg.get("pet") in pets["styles"] else pets["default"]
        if a.action == "say":
            print(pet_say(db))
        elif a.action in ("off", "on"):
            cfg["petEnabled"] = a.action == "on"
            CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
            print("pet is " + ("on" if cfg["petEnabled"] else "off (no pet on the page or in /next; turn it back on with: cal.py pet on)"))
        elif a.action == "set":
            if a.style not in pets["styles"]:
                sys.exit("unknown style; choose one of: " + ", ".join(pets["styles"]))
            cfg["pet"] = a.style
            cfg["petEnabled"] = True
            if a.name:
                cfg["petName"] = a.name
            elif "petName" in cfg:
                del cfg["petName"]
            CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
            print("pet set to " + a.style + ": " + pet_say(db))
        else:
            for k, v in pets["styles"].items():
                print(("* " if (k == cur and cfg.get("petEnabled") is not False) else "  ") + f"{k:<8} {v['faces'].get('idle', ''):<10} {v['label']} - {v['blurb']}")
            print("(faces shown are the calm 'idle' face; the pet's face changes with your tasks)")
            print("\nchoose with: cal.py pet set STYLE [--name NAME]    opt out with: cal.py pet off" + ("    [pet is currently OFF]" if cfg.get("petEnabled") is False else "") + "    (the page also has a Change pet picker)")
    elif a.cmd == "sort":
        plan = sort_plan(db)
        if not plan:
            print("(nothing to sort)")
        else:
            print("lane        rank  score  task  [why it ranks here]   (higher score = do sooner; ranks are within a lane)")
        rank: dict[str, int] = {}
        for t, score, why in plan:
            ln = t.get("lane") or "fixed"
            rank[ln] = rank.get(ln, 0) + 1
            print(f"{ln:<11} #{rank[ln]:<2} {score:5.1f}  {t['title'][:70]}  [{', '.join(why) or 'by due date'}]{chat_link(t)}")
            if a.apply:
                t["prio"] = rank[ln]
        if a.apply and plan:
            replan(db, now()); save(db)
            print("\nsorted: priorities written and the schedule recomputed")
        elif plan:
            print("\n(preview only: run with --apply to save this order)")
    elif a.cmd == "config":
        cfg = load_cfg()
        if a.action == "set":
            if not a.key or a.value is None:
                sys.exit("usage: cal.py config set KEY VALUE")
            cfg[a.key] = a.value if a.value not in ("true", "false") else (a.value == "true")
            CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(cfg, indent=2, ensure_ascii=False) if not a.key or a.action == "set" else json.dumps(cfg.get(a.key)))
    elif a.cmd == "reviews":
        rv = [t for t in db["tasks"] if t["status"] == "review"]
        mine = [t for t in db["tasks"] if t["status"] == "open" and t.get("lane") == "owner" and due_dt(t) <= now() and deps_met(db, t)]
        print("WAITING FOR REVIEW:")
        for t in rv:
            print(fmt(t)); print("     -> " + (t.get("result") or ""))
        if not rv:
            print("(none)")
        print("YOUR TASKS READY NOW:")
        mine.sort(key=lambda t: (t.get("prio", 50), due_dt(t)))
        for t in mine:
            print(fmt(t))
        if not mine:
            print("(none)")
    elif a.cmd == "replan":
        replan(db, datetime.fromisoformat(a.frm).astimezone() if a.frm else now()); save(db)
        print("\n".join(fmt(t) for t in sorted((t for t in db["tasks"] if t["status"] in ("open", "running", "blocked")), key=due_dt)))
    elif a.cmd == "note":
        t = find(db, a.id)
        t.setdefault("notes", []).append({"at": now().replace(microsecond=0).isoformat(), "text": a.text})
        save(db)
        print(fmt(t))
    return 0


def refresh_page() -> None:
    """After any change to the tasks: re-render the local calendar.html, and say so if a published copy needs republishing."""
    import subprocess
    r = FILE.parent / "render_html.py"
    if r.exists():
        subprocess.run([sys.executable, str(r)], capture_output=True, text=True)
    url = load_cfg().get("artifactUrl")
    if url:
        print(f"(calendar.html is refreshed. The published page does not update itself: republish {FILE.parent / 'calendar.html'} to {url} in place.)")


if __name__ == "__main__":
    rc = main()
    if _SAVED and rc == 0:
        refresh_page()
    sys.exit(rc)
