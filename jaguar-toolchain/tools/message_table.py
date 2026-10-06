# message_table.py — Castle Remembers V6 canon message package
# (kimi/visual-refinement)
#
# Complete canonical string table for the Jaguar edition, paired with the V6
# font (font_family.py contract: cell 6x8, advance 6, pitch 10, 320x240).
# Canon source: original/index.html (whispers, observations, end screens).
# Content/assets only — Claude owns the message/state system and any
# rendering; Bob approves buffers (Checkpoint B). No OP objects, no DRAM
# allocation, no gameplay logic.
#
# Emits:
#   docs/kimi/V6_MESSAGE_TABLE.md     full handoff table
#   docs/visual/sprites/messages.s    MSG_* equates + ASCII string data
#   docs/visual/previews/v6m_*.png    mockups at true 320x240 (shown 2x)

import os

from font_family import G, CELL_W, LINE_PITCH, draw_text, center_x, text_width, render_png
import backdrop_family as bf

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_OUT = os.path.join(HERE, "..", "..", "docs", "visual", "previews")
SPR_OUT = os.path.join(HERE, "..", "..", "docs", "visual", "sprites")
DOC_OUT = os.path.join(HERE, "..", "..", "docs", "kimi")
os.makedirs(IMG_OUT, exist_ok=True)
os.makedirs(SPR_OUT, exist_ok=True)
os.makedirs(DOC_OUT, exist_ok=True)

ELL = "\u2026"   # … glyph (font index supports it)

# type: whisper | observation | title | prompt | end | screen
# pos: top (y=14), crown (y=8), center block, above-object, bottom (y=226)
# dur: seconds (0 = until dismissed / contextual)
M = []
def msg(mid, text, mtype, pos, pri, dur, canon=None, wrap=None):
    M.append(dict(id=mid, text=text, type=mtype, pos=pos, pri=pri, dur=dur,
                  canon=canon, wrap=wrap))

# ---------------------------------------------------------------- global
msg("MSG_TITLE_A", "THE CASTLE", "screen", "center y=88", 5, 0)
msg("MSG_TITLE_B", "REMEMBERS", "screen", "center y=102", 5, 0)
msg("MSG_TITLE_SUB", "CLIMB. LEARN. ADAPT. ESCAPE.", "screen", "center y=120", 4, 0)
msg("MSG_TITLE_GO", "PRESS PAUSE TO BEGIN", "screen", "center y=200", 4, 0,
    canon="TAP OR PRESS ENTER (binding is Claude's; PAUSE suggested)")
msg("MSG_OBSERVED", "THE CASTLE OBSERVED YOU", "screen", "center y=96", 5, 1.6)
msg("MSG_REBUILD", f"RECONSTRUCTING{ELL}", "screen", "center y=140", 5, 0,
    canon="RECONSTRUCTING + animated dots")
msg("MSG_REMEMBERS", "THE CASTLE REMEMBERS", "end", "center y=88", 5, 0)
msg("MSG_WATCHED1", f"{ELL}IT HAS WATCHED YOU 1 TIME.", "end", "center y=104", 4, 0,
    canon="…it has watched you 1 time.")
msg("MSG_WATCHEDN", f"{ELL}IT HAS WATCHED YOU # TIMES.", "end", "center y=104", 4, 0,
    canon="…it has watched you N times. — # = runtime digit substitution")
msg("MSG_FORGETS", "THE CASTLE FORGETS", "end", "center y=88", 5, 0)
msg("MSG_FORNOW", f"{ELL}FOR NOW.", "end", "center y=104", 5, 0,
    canon="…for now.")
msg("MSG_ESCAPED", "YOU ESCAPED", "end", "center y=88", 5, 0)
msg("MSG_FELL", "YOU FELL", "end", "center y=88", 5, 0)
msg("MSG_RISE", "RISE AGAIN", "end", "center y=210", 3, 0,
    canon="TAP TO RISE AGAIN")
msg("MSG_ENTERAGAIN", "ENTER AGAIN", "end", "center y=210", 3, 0,
    canon="TAP TO ENTER AGAIN")

# ---------------------------------------------------------------- whispers (canon verbatim, dur 2.6s per original)
W = 2.6
msg("MSG_W_DOOR_L", f"{ELL}YOU ALWAYS GO LEFT.", "whisper", "top", 3, W,
    canon="…you always go left.")
msg("MSG_W_DOOR_R", f"{ELL}YOU ALWAYS GO RIGHT.", "whisper", "top", 3, W,
    canon="…you always go right.")
msg("MSG_W_DOOR_GONE_L", f"{ELL}THE LEFT WAY IS GONE.", "whisper", "top", 3, W,
    canon="…the left way is gone. (door tier 3: bricked)")
msg("MSG_W_DOOR_GONE_R", f"{ELL}THE RIGHT WAY IS GONE.", "whisper", "top", 3, W,
    canon="…the right way is gone.")
msg("MSG_W_DOOR_GIFT_L", f"{ELL}THE LEFT DOOR WAS LEFT OPEN FOR YOU.", "whisper", "top", 3, W,
    canon="…the left door was left open for you. (door tier 1-2 gift)")
msg("MSG_W_DOOR_GIFT_R", f"{ELL}THE RIGHT DOOR WAS LEFT OPEN FOR YOU.", "whisper", "top", 3, W,
    canon="…the right door was left open for you.")
msg("MSG_W_LEVER_TRUST", f"{ELL}IT KNOWS WHICH LEVER YOU TRUST.", "whisper", "top", 3, W,
    canon="…it knows which lever you trust.")
msg("MSG_W_LEVER_HERE", f"{ELL}THE LEVER YOU TRUST IS HERE TOO.", "whisper", "top", 3, W,
    canon="…the lever you trust is here too.")
msg("MSG_W_RUSH", f"{ELL}YOU NEVER STOP TO LOOK.", "whisper", "top", 3, W,
    canon="…you never stop to look.")
msg("MSG_W_WAIT", f"{ELL}YOU LIKE TO WAIT.", "whisper", "top", 3, W,
    canon="…you like to wait.")
msg("MSG_W_BRACE", f"{ELL}THE GUARDS HAVE FELT YOUR HANDS.", "whisper", "top", 3, W,
    canon="…the guards have felt your hands.")
msg("MSG_W_WATCH", f"{ELL}THE GUARDS KNOW YOU SLIP PAST.", "whisper", "top", 3, W,
    canon="…the guards know you slip past.")
msg("MSG_W_TRAP", f"{ELL}THE SPIKES GREW FOR YOU.", "whisper", "top", 3, W,
    canon="…the spikes grew for you.")
msg("MSG_W_CHEST", f"{ELL}IT SAW YOU OPEN EVERY BOX.", "whisper", "top", 3, W,
    canon="…it saw you open every box.")
msg("MSG_W_EXIT_MOVED", f"{ELL}THE WAY OUT HAS MOVED.", "whisper", "top", 4, W,
    canon="…the way out has moved.")
msg("MSG_W_EXIT_GUARD", f"{ELL}IT WILL NOT LET YOU LEAVE SO EASILY.", "whisper", "top", 4, W,
    canon="…it will not let you leave so easily.")

# ---------------------------------------------------------------- observations (rebuild screen)
# Canon carries dynamic counts/times; Jaguar text drops them, meaning preserved.
msg("MSG_O_FIRST", "IT HAS NOT SEEN YOU YET.", "observation", "center y=118", 4, 2.0,
    canon="IT HAS NOT SEEN YOU YET.")
msg("MSG_O_DOOR_L", "YOU WENT LEFT AGAIN.", "observation", "center y=118", 4, 2.0,
    canon="YOU WENT LEFT AGAIN (N OF M DOORS). THE LEFT SIDE STAYS ARMED.",
    wrap="THE LEFT SIDE STAYS ARMED.")
msg("MSG_O_DOOR_R", "YOU WENT RIGHT AGAIN.", "observation", "center y=118", 4, 2.0,
    canon="YOU WENT RIGHT AGAIN (N OF M DOORS). THE RIGHT SIDE STAYS ARMED.",
    wrap="THE RIGHT SIDE STAYS ARMED.")
msg("MSG_O_LEVER_L", "YOU PULLED THE LEFT LEVER AGAIN.", "observation", "center y=118", 4, 2.0,
    canon="YOU PULLED THE LEFT LEVER AGAIN. IT STAYS ARMED.",
    wrap="IT STAYS ARMED.")
msg("MSG_O_LEVER_R", "YOU PULLED THE RIGHT LEVER AGAIN.", "observation", "center y=118", 4, 2.0,
    canon="YOU PULLED THE RIGHT LEVER AGAIN. IT STAYS ARMED.",
    wrap="IT STAYS ARMED.")
msg("MSG_O_RUSH", "YOU RUSHED. THE AMBUSH STAYS.", "observation", "center y=118", 4, 2.0,
    canon="YOU RUSHED (N% STANDING STILL). THE AMBUSH STAYS.")
msg("MSG_O_WAIT", "YOU WAITED. THE GATES KEEP CLOSING.", "observation", "center y=118", 4, 2.0,
    canon="YOU WAITED (N% STANDING STILL). THE GATES KEEP CLOSING.")
msg("MSG_O_TRAP", "YOU SPRANG THE TRAPS. THE SPIKES STAY.", "observation", "center y=118", 4, 2.0,
    canon="YOU SPRANG N TRAPS AND FELL ON FLOOR F. THE SPIKES STAY.")
msg("MSG_O_CHEST", "YOU OPENED EVERY CHEST. IT STAYS PACKED.", "observation", "center y=118", 4, 2.0,
    canon="YOU OPENED N CHESTS. THE CASTLE PACKED ONE FOR YOU. IT STAYS PACKED.")
msg("MSG_O_GUARD", "A GUARD CAUGHT YOU ON FLOOR #.", "observation", "center y=118", 4, 2.0,
    canon="A GUARD CAUGHT YOU ON FLOOR F. SHOVED X, SLIPPED PAST Y.",
    wrap=None)
msg("MSG_O_ARROW", "AN ARROW FOUND YOU ON FLOOR #.", "observation", "center y=118", 4, 2.0,
    canon="AN ARROW FOUND YOU ON FLOOR F. SHOVED X, SLIPPED PAST Y.")
msg("MSG_O_WIN_DOOR_L", "YOU ESCAPED THROUGH LEFT DOORS.", "observation", "center y=118", 4, 2.0,
    canon="YOU ESCAPED THROUGH LEFT DOORS (N OF M).")
msg("MSG_O_WIN_DOOR_R", "YOU ESCAPED THROUGH RIGHT DOORS.", "observation", "center y=118", 4, 2.0,
    canon="YOU ESCAPED THROUGH RIGHT DOORS (N OF M).")
msg("MSG_O_WIN_LEVER_L", "YOU ESCAPED PULLING THE LEFT LEVER.", "observation", "center y=118", 4, 2.0,
    canon="YOU ESCAPED PULLING THE LEFT LEVER (N OF M).")
msg("MSG_O_WIN_LEVER_R", "YOU ESCAPED PULLING THE RIGHT LEVER.", "observation", "center y=118", 4, 2.0,
    canon="YOU ESCAPED PULLING THE RIGHT LEVER (N OF M).")
msg("MSG_O_WIN_RUSH", "YOU ESCAPED WITHOUT STOPPING.", "observation", "center y=118", 4, 2.0,
    canon="YOU ESCAPED IN T.Ts WITHOUT STOPPING (N% STILL).")
msg("MSG_O_WIN_WAIT", "YOU ESCAPED BY WAITING.", "observation", "center y=118", 4, 2.0,
    canon="YOU ESCAPED IN T.Ts BY WAITING (N% STILL).")
msg("MSG_O_WIN_BRACE", "YOU ESCAPED BY SHOVING GUARDS.", "observation", "center y=118", 4, 2.0,
    canon="YOU ESCAPED BY SHOVING N GUARDS.")
msg("MSG_O_WIN_WATCH", "YOU ESCAPED BY SLIPPING PAST.", "observation", "center y=118", 4, 2.0,
    canon="YOU ESCAPED BY SLIPPING PAST N GUARDS.")
msg("MSG_O_WIN_TRAP", "YOU SPRANG TRAPS AND STILL ESCAPED.", "observation", "center y=118", 4, 2.0,
    canon="YOU SPRANG N TRAPS AND STILL ESCAPED.")
msg("MSG_O_WIN_CHEST", "YOU ESCAPED AFTER OPENING EVERY CHEST.", "observation", "center y=118", 4, 2.0,
    canon="YOU ESCAPED AFTER OPENING N OF M CHESTS.")

# ---------------------------------------------------------------- floor titles
msg("MSG_F1", "FLOOR 1 - GATEHOUSE", "title", "crown", 4, 2.0)
msg("MSG_F2", "FLOOR 2 - GALLERY", "title", "crown", 4, 2.0)
msg("MSG_F3", "FLOOR 3 - HALL OF ECHOES", "title", "crown", 4, 2.0)
msg("MSG_F4", "FLOOR 4 - VAULT", "title", "crown", 4, 2.0)
msg("MSG_F5", "FLOOR 5 - JUDGMENT", "title", "crown", 4, 2.0)

# ---------------------------------------------------------------- prompts (Gate 7 controls: S up, X down, L act)
msg("MSG_P_OPEN", "L - OPEN", "prompt", "above-object", 2, 0)
msg("MSG_P_PULL", "L - PULL", "prompt", "above-object", 2, 0)
msg("MSG_P_SHOVE", "L - SHOVE", "prompt", "above-object", 2, 0)
msg("MSG_P_CLIMB", "S - CLIMB", "prompt", "above-object", 2, 0)
msg("MSG_P_DOWN", "X - DOWN", "prompt", "above-object", 2, 0)
msg("MSG_P_SEALED", "SEALED", "prompt", "above-object", 2, 0,
    canon="(bricked door: canon flavour, no canon string)")
msg("MSG_P_EXIT", "EXIT", "prompt", "above-object", 2, 0)

# ---------------------------------------------------------------- validation
for m in M:
    for ch in m["text"]:
        assert ch in G or ch == "#", f"{m['id']}: char {ch!r} not in font"
    w = text_width(m["text"])
    m["width"] = w
    if m["type"] != "screen":
        assert w <= 318, f"{m['id']}: {w}px too wide"
    if m["wrap"]:
        for ch in m["wrap"]:
            assert ch in G, f"{m['id']} wrap: char {ch!r} not in font"
        m["wrap_width"] = text_width(m["wrap"])

# ---------------------------------------------------------------- markdown table
md = [
    "# V6 Canon Message Table — Castle Remembers (Jaguar)",
    "",
    "Branch `kimi/visual-refinement`. Font contract: cell 6×8, advance 6 px,",
    "line pitch 10 px, face `$98BD`, relief `$3601` (see `font_data.s`).",
    "Canon source: `original/index.html`. `#` marks a runtime digit substitution.",
    "Content only — Claude owns the message/state system; Bob Checkpoint B for",
    "the render path. No OP objects or buffers are allocated here.",
    "",
    "Positions: `top` = y 14, centered · `crown` = y 8, centered · `center` =",
    "centered block · `above-object` = 10 px above the interaction object,",
    "clamped to screen · `bottom` = y 226, centered.",
    "",
    "| ID | Text | px | Type | Position | Pri | Dur s | Wrap line 2 |",
    "|---|---|---|---|---|---|---|---|",
]
for m in M:
    shown = m["text"].replace(ELL, "…").replace("|", "\\|")
    wrap = (m["wrap"] or "").replace("|", "\\|")
    md.append(f"| `{m['id']}` | {shown} | {m['width']} | {m['type']} | "
              f"{m['pos']} | {m['pri']} | {m['dur']} | {wrap} |")
md += [
    "",
    "## Canon originals (where Jaguar text was shortened)",
    "",
    "Meanings preserved; dynamic counts/times dropped or reduced to `#`.",
    "",
    "| ID | Canon original (original/index.html) |",
    "|---|---|",
]
for m in M:
    if m["canon"]:
        md.append(f"| `{m['id']}` | {m['canon'].replace('|', '\\|')} |")
md += [
    "",
    "## Whisper queue behaviour (canon)",
    "",
    "- Whispers are title `THE CASTLE REMEMBERS` + sub-line, 2.6 s each, queued",
    "  on run start (death merge) and on floor entry for that floor's tier notes.",
    "- On escape: `THE CASTLE FORGETS` + `…for now.`, double-weight memory merge.",
    "- Priority 4 whispers (exit moved / exit guarded) jump the queue.",
    "",
    "## String data",
    "",
    "`docs/visual/sprites/messages.s` — `MSG_*` index equates in table order,",
    "then `msg_strings:` as 0-terminated ASCII (`$85` = ellipsis glyph, `#` kept",
    "literal for Claude's digit substitution). Optional second line for wrapped",
    "observations follows its parent as `<ID>_2`.",
]
with open(os.path.join(DOC_OUT, "V6_MESSAGE_TABLE.md"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(md) + "\n")

# ---------------------------------------------------------------- messages.s
def encode(text):
    return [0x85 if ch == ELL else ord(ch) for ch in text]

lines = [
    "; messages.s - V6 canon message strings (kimi/visual-refinement)",
    "; Index equates in table order; strings are 0-terminated ASCII.",
    "; $85 = ellipsis glyph (font order index 49). '#' = runtime digit slot.",
    "; <ID>_2 labels hold optional wrap second lines. Font contract: font_data.s.",
    "; NOT linked - Claude owns the message system; Bob Checkpoint B on buffers.",
    "",
]
for i, m in enumerate(M):
    lines.append(f"{m['id']:<20} equ     {i}")
lines.append("")
lines.append("msg_strings:")
for m in M:
    lines.append(f"{m['id']}_str:")
    lines.append("        dc.b    " + ",".join(str(b) for b in encode(m["text"])) + ",0")
    if m["wrap"]:
        lines.append(f"{m['id']}_2:")
        lines.append("        dc.b    " + ",".join(str(b) for b in encode(m["wrap"])) + ",0")
with open(os.path.join(SPR_OUT, "messages.s"), "w", encoding="ascii") as fh:
    fh.write("\n".join(lines) + "\n")

# ---------------------------------------------------------------- mockups
def scene(floor_rows):
    img = [r[:] for r in floor_rows]
    for y in range(180, 240):
        img.append([PAL_BLACK] * 320)
    for y in range(180, 194):
        img[y] = [PAL_WARMD if y % 8 else PAL_MORTAR for _ in range(320)]
    for y in range(194, 202):
        img[y] = [PAL_WARMM if y % 4 else PAL_MORTAR for _ in range(320)]
    return img[:240]

from kpalette import PAL
PAL_BLACK = PAL["BLACK"]; PAL_WARMD = PAL["WARM_D"]
PAL_WARMM = PAL["WARM_M"]; PAL_MORTAR = PAL["MORTAR"]

def m_whisper():                                  # F3, door tier-3 whisper
    img = scene(bf.floor3())
    t = next(m for m in M if m["id"] == "MSG_W_DOOR_GONE_L")["text"]
    draw_text(img, center_x(t), 14, t)
    return img

def m_rebuild():                                  # observation screen
    img = [[PAL_BLACK] * 320 for _ in range(240)]
    draw_text(img, center_x("THE CASTLE OBSERVED YOU"), 96, "THE CASTLE OBSERVED YOU")
    o = next(m for m in M if m["id"] == "MSG_O_LEVER_L")
    draw_text(img, center_x(o["text"]), 118, o["text"])
    draw_text(img, center_x(o["wrap"]), 118 + LINE_PITCH, o["wrap"])
    r = f"RECONSTRUCTING{ELL}"
    draw_text(img, center_x(r), 160, r)
    return img

def m_death():                                    # death: remember + watched + whisper
    img = [[PAL_BLACK] * 320 for _ in range(240)]
    draw_text(img, center_x("THE CASTLE REMEMBERS"), 88, "THE CASTLE REMEMBERS")
    w = f"{ELL}IT HAS WATCHED YOU 3 TIMES."
    draw_text(img, center_x(w), 104, w)
    s = f"{ELL}THE SPIKES GREW FOR YOU."
    draw_text(img, center_x(s), 130, s)
    draw_text(img, center_x("RISE AGAIN"), 210, "RISE AGAIN")
    return img

def m_prompt():                                   # F2, PULL above left lever
    img = scene(bf.floor2())
    t = "FLOOR 2 - GALLERY"
    draw_text(img, center_x(t), 8, t)
    p = "L - PULL"
    draw_text(img, 84 - text_width(p) // 2, 150, p)   # over lever niche x=80
    return img

def m_floortitle():                               # F4 entry
    img = scene(bf.floor4())
    t = "FLOOR 4 - VAULT"
    draw_text(img, center_x(t), 8, t)
    return img

MOCKS = {
    "v6m_whisper.png": m_whisper,
    "v6m_rebuild_obs.png": m_rebuild,
    "v6m_death.png": m_death,
    "v6m_prompt.png": m_prompt,
    "v6m_floortitle.png": m_floortitle,
}
for name, fn in MOCKS.items():
    rows = fn()
    assert len(rows) == 240 and all(len(r) == 320 for r in rows)
    render_png(rows, os.path.join(IMG_OUT, name), scale=2)

print("messages:", len(M))
print("table:", os.path.join(DOC_OUT, "V6_MESSAGE_TABLE.md"))
print("strings:", os.path.join(SPR_OUT, "messages.s"))
print("mockups:", list(MOCKS))
print("widest:", max((m["width"], m["id"]) for m in M))
