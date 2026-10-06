"""mkmsg.py - build the castle-voice message tables from Kimi's V6 package.

Inputs (Kimi's, read-only): docs/visual/sprites/messages.s and
docs/kimi/V6_MESSAGE_TABLE.md - from the working tree if present, otherwise
from git (default ref kimi/visual-refinement, override with KIMI_REF).

Outputs (generated, committed so the build never needs Kimi's branch):
  gate7_castle/msg_ids.inc    Kimi's MSG_* ids verbatim + MSGX_* gameplay ids
  gate7_castle/messages.inc   strings + msgtab: id -> type, frames, line1, line2

Message type = priority (higher interrupts lower), per the production order:
  MT_EVENT 5   death / win / rebuild screens
  MT_OBSERVE 4 castle observation / memory whisper
  MT_TITLE 3   floor title
  MT_WARN 2    gameplay warning
  MT_PROMPT 1  interaction prompt
Kimi's own priority column is recorded in the table comments, not used.

    python tools/mkmsg.py
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
OUT = os.path.join(ROOT, "gate7_castle")
REF = os.environ.get("KIMI_REF", "kimi/visual-refinement")
ELL = 0x85                                      # Kimi's ellipsis glyph byte

MT = {"event": "MT_EVENT", "observe": "MT_OBSERVE", "title": "MT_TITLE", "warn": "MT_WARN", "prompt": "MT_PROMPT"}

# Gameplay-lane additions: canon hint/death lines from original/index.html that the
# V6 package does not carry yet ("..." becomes Kimi's ellipsis glyph). Answers to
# something the player just did are warnings (they wait behind a title); only
# Kimi's contextual MSG_P_* prompts are prompts (dropped, re-asserted each frame).
EXTRAS = [
    ("MSGX_GATE_SHUT", "warn", 120, "THE GATE IS SHUT. FIND A LEVER."),
    ("MSGX_JAMMED", "warn", 120, "IT IS JAMMED."),
    ("MSGX_GATE_OPEN", "warn", 120, "THE GATE IS ALREADY OPEN."),
    ("MSGX_EMPTY", "warn", 120, "EMPTY."),
    ("MSGX_HEAVY", "warn", 120, "THE HEAVY BRACES. AGAIN!"),
    ("MSGX_HOUND", "warn", 120, "THE HOUND WILL NOT BE PUSHED."),
    ("MSGX_BRICKED", "warn", 150, "BRICKED UP. THE CASTLE CLOSED THIS WAY."),
    ("MSGX_DUD", "warn", 150, "IT TURNS. NOTHING HAPPENS. TRY THE OTHER ONE."),
    ("MSGX_ALARM", "warn", 150, "THE GATE OPENS. THE GUARD HEARD IT."),
    ("MSGX_SLAM", "warn", 150, "THE GATE SLAMS SHUT. THE CASTLE WILL NOT WAIT."),
    ("MSGX_GIFT_SHARD", "warn", 150, "A MEMORY SHARD, LEFT FOR YOU."),
    ("MSGX_SHARD", "warn", 150, "A MEMORY SHARD. THE CASTLE LET YOU HAVE THIS ONE."),
    ("MSGX_TRAP_LEVER", "warn", 120, "...YOUR HAND. RUN."),
    ("MSGX_TRAP_CHEST", "warn", 120, "...GREEDY HANDS. RUN."),
    ("MSGX_CEILING", "warn", 120, "...THE CEILING SHIFTS ABOVE YOU."),
    # death screens: "YOU FELL" + the canon cause line
    ("MSGX_D_GUARD", "event", 90, "A GUARD CAUGHT YOU."),
    ("MSGX_D_ARROW", "event", 90, "AN ARROW."),
    ("MSGX_D_SPIKES", "event", 90, "SPIKES."),
    ("MSGX_D_LEVER", "event", 90, "THE LEVER YOU TRUSTED WAS A TRAP."),
    ("MSGX_D_CHEST", "event", 90, "THE CHEST WAS A TRAP."),
    ("MSGX_D_CEILING", "event", 90, "THE CEILING CAME DOWN."),
    ("MSGX_D_BLADE", "event", 90, "THE BLADE KEPT ITS RHYTHM."),
    ("MSGX_ESCAPE", "event", 180, "THE CASTLE WILL REMEMBER HOW."),
]
EXTRA_LINE1 = {k: "MSG_FELL" for k, *_ in EXTRAS if k.startswith("MSGX_D_")}
EXTRA_LINE1["MSGX_ESCAPE"] = "MSG_ESCAPED"


def kimi_file(rel):
    path = os.path.join(REPO, rel)
    if os.path.exists(path):
        return open(path, "rb").read().decode("utf-8", "replace"), "working tree"
    r = subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (REF, rel)], capture_output=True)
    if r.returncode:
        raise SystemExit("cannot read %s (working tree or %s)" % (rel, REF))
    sha = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", REF], capture_output=True, text=True).stdout.strip()
    return r.stdout.decode("utf-8", "replace"), "%s @ %s" % (REF, sha)


def parse_messages(src):
    ids = [(n, int(v)) for n, v in re.findall(r"^(MSG_\w+)\s+equ\s+(\d+)", src, re.M)]
    strings = {}
    cur = None
    for line in src.splitlines():
        m = re.match(r"^(MSG_\w+?)(_str|_2):", line)
        if m:
            cur = (m.group(1), m.group(2))
            strings[cur] = []
            continue
        if cur and "dc.b" in line:
            strings[cur] += [int(x) for x in re.findall(r"\d+", line.split(";")[0].split("dc.b", 1)[1])]
    return ids, strings


def parse_table(md):
    rows = {}
    for line in md.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 8 and re.match(r"`MSG_\w+`", cells[0]):
            rows[cells[0].strip("`")] = dict(kind=cells[3], pri=cells[5], dur=cells[6])
    return rows


def ascii_bytes(text):
    return [ELL if ch == "\x85" else ord(ch) for ch in text.replace("...", "\x85")]


def main():
    msrc, msrc_from = kimi_file("docs/visual/sprites/messages.s")
    mdsrc, _ = kimi_file("docs/kimi/V6_MESSAGE_TABLE.md")
    ids, strings = parse_messages(msrc)
    table = parse_table(mdsrc)
    assert [v for _, v in ids] == list(range(len(ids))), "MSG ids must be 0..n-1 in order"
    for n, _ in ids:
        assert (n, "_str") in strings, "no string for " + n

    entries = []                       # (id name, type, frames, line1 label, line2 label, note)
    for n, _ in ids:
        row = table.get(n, {})
        kind = row.get("kind", "")
        dur = float(row.get("dur", "0") or 0)
        frames = int(round(dur * 60))
        line1, line2 = n + "_str", ("%s_2" % n) if (n, "_2") in strings else "msg_none"
        if kind in ("screen", "end"):
            ty, frames = "event", frames or 150
        elif kind == "observation":
            ty, frames = "observe", frames or 120
        elif kind == "whisper":            # canon whisper = "THE CASTLE REMEMBERS" + line
            ty, line1, line2 = "observe", "MSG_REMEMBERS_str", n + "_str"
        elif kind == "title":
            ty, frames = "title", frames or 120
        elif kind == "prompt":
            ty, frames = "prompt", 8           # contextual: refreshed while in reach
        else:
            raise SystemExit("unknown type for %s: %r" % (n, kind))
        entries.append([n, ty, frames, line1, line2, "kimi %s pri %s" % (kind, row.get("pri", "?"))])
    # composites the canon screens use
    special = {"MSG_OBSERVED": ("MSG_OBSERVED_str", "MSG_REBUILD_str"),
               "MSG_WATCHED1": ("MSG_REMEMBERS_str", "MSG_WATCHED1_str"),
               "MSG_WATCHEDN": ("MSG_REMEMBERS_str", "MSG_WATCHEDN_str"),
               "MSG_FORGETS": ("MSG_FORGETS_str", "MSG_FORNOW_str"),
               "MSG_FELL": ("MSG_FELL_str", "MSG_RISE_str")}
    for e in entries:
        if e[0] in special:
            e[3], e[4] = special[e[0]]
        if e[0] in ("MSG_WATCHED1", "MSG_WATCHEDN", "MSG_FORGETS"):
            e[1], e[2] = "observe", 156
    base = len(ids)
    for i, (n, ty, frames, text) in enumerate(EXTRAS):
        if n in EXTRA_LINE1:
            entries.append([n, ty, frames, EXTRA_LINE1[n] + "_str", n + "_str", "gameplay lane"])
        else:
            entries.append([n, ty, frames, n + "_str", "msg_none", "gameplay lane"])

    # ---- msg_ids.inc
    o = ["; GENERATED by tools/mkmsg.py from Kimi's V6 package (%s) - do not edit" % msrc_from,
         "; MSG_* ids are Kimi's, verbatim; MSGX_* are gameplay-lane additions."]
    o += ["%-20s equ     %d" % (n, v) for n, v in ids]
    o += ["%-20s equ     %d" % (n, base + i) for i, (n, *_r) in enumerate(EXTRAS)]
    o += ["%-20s equ     %d" % ("MSG_COUNT", base + len(EXTRAS))]
    open(os.path.join(OUT, "msg_ids.inc"), "w", newline="\n").write("\n".join(o) + "\n")

    # ---- messages.inc
    o = ["; GENERATED by tools/mkmsg.py from Kimi's V6 package (%s) - do not edit" % msrc_from,
         "        .even",
         "msgtab:                                 ; id -> type, frames, line1, line2 (12 bytes)"]
    for n, ty, frames, l1, l2, note in entries:
        o.append("        dc.w    %s,%d" % (MT[ty], frames))
        o.append("        dc.l    %s,%s                ; %s (%s)" % (l1, l2, n, note))
    o.append("msgtab_end:")
    o.append("msg_none:       dc.b    0")
    for (n, kind), data in strings.items():
        o.append("%s%s:" % (n, kind))
        o.append("        dc.b    " + ",".join(str(b) for b in data))
    for n, _ty, _f, text in EXTRAS:
        o.append("%s_str:" % n)
        o.append("        dc.b    " + ",".join(str(b) for b in ascii_bytes(text) + [0]))
    o.append("        .even")
    open(os.path.join(OUT, "messages.inc"), "w", newline="\n").write("\n".join(o) + "\n")
    print("messages: %d Kimi + %d gameplay ids from %s" % (len(ids), len(EXTRAS), msrc_from))
    return entries


if __name__ == "__main__":
    main()
