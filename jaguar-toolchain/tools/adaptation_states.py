# adaptation_states.py — Castle Remembers "the castle remembers" dressing
# (kimi/visual-refinement)
#
# Design assets only (no OP slots yet — Bob Checkpoint B if adopted).
# Transparent overlay decals that Claude can composite or that get baked into
# per-tier backdrop variants, making behavioural adaptation visible:
#   decal_crack_16    16x8   crack cluster (corridor damage tiers)
#   decal_grate       16x16  iron grate (fortified corridor / door tier 2+)
#   decal_chain       8x16   hanging chain + warning tag (altered dressing)
#   decal_bones       16x8   bone debris at trap sites
# Plus a composite preview (v2_adaptation.png) showing an F1 corridor crop
# escalating: pristine -> +spikes slot plate -> +cracks/bones -> +grate.
# Palette VJ-verified via kpalette.py. NOT linked into the game.

import os
from PIL import Image, ImageDraw

from kpalette import PAL, cry_to_rgb

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_OUT = os.path.join(HERE, "..", "..", "docs", "visual", "previews")
SPR_OUT = os.path.join(HERE, "..", "..", "docs", "visual", "sprites")
os.makedirs(IMG_OUT, exist_ok=True)
os.makedirs(SPR_OUT, exist_ok=True)

CH = {
    ".": 0x0000,
    "O": PAL["BLACK"],
    "k": PAL["SHADOW"],
    "i": PAL["IRON_D"],
    "I": PAL["IRON_L"],
    "B": PAL["BONE"],
    "R": PAL["WARN_D"],
}

SPRITES = {
    "decal_crack_16": [
        "................",
        "..k.............",
        ".kk.k...........",
        ".k..kk....k.....",
        "k....k.k..kk....",
        ".....k..kk.k.k..",
        "......k....k.kk.",
        ".......k......k.",
    ],
    "decal_grate": [
        "iiiiiiiiiiiiiiii",
        "iI.iI..iI..iI.iI",
        "iI.iI..iI..iI.iI",
        "iiiiiiiiiiiiiiii",
        "iI.iI..iI..iI.iI",
        "iI.iI..iI..iI.iI",
        "iI.iI..iI..iI.iI",
        "iiiiiiiiiiiiiiii",
        "iI.iI..iI..iI.iI",
        "iI.iI..iI..iI.iI",
        "iiiiiiiiiiiiiiii",
        "iI.iI..iI..iI.iI",
        "iI.iI..iI..iI.iI",
        "iI.iI..iI..iI.iI",
        "iI.iI..iI..iI.iI",
        "iiiiiiiiiiiiiiii",
    ],
    "decal_chain": [
        "...ii...",
        "...iI...",
        "...ii...",
        "...iI...",
        "...ii...",
        "...iI...",
        "...ii...",
        "..OiIO..",
        "..ORRO..",
        "..ORRO..",
        "..OiIO..",
        "...OO...",
        "........",
        "........",
        "........",
        "........",
    ],
    "decal_bones": [
        "................",
        "................",
        "................",
        "................",
        "....B...........",
        "..B.BB..B...B...",
        ".BB.BB.BBB.BB.B.",
        ".B..B...B...BB..",
    ],
}

for name, rows in SPRITES.items():
    w = len(rows[0])
    for r in rows:
        assert len(r) == w, f"{name}: ragged '{r}'"
        for c in r:
            assert c in CH, f"{name}: bad char '{c}'"

# ---- composite escalation preview over the F1 backdrop crop -----------------
import backdrop_family as bf

f1 = bf.floor1()
CROP = (32, 120, 128, 180)     # left corridor: door arch + torch area
x0, y0, x1, y1 = CROP

def crop(rows):
    return [r[x0:x1] for r in rows[y0:y1]]

def paste(dst, decal, dx, dy):
    for y, row in enumerate(decal):
        for x, c in enumerate(row):
            if c != ".":
                dst[y0 + dy + y][x0 + dx + x] = CH[c]

stage_pristine = [r[:] for r in f1]
stage_spikes = [r[:] for r in f1]
spike_plate = [list(r) for r in __import__("trap_family").IMG_SPIKE16[6:]]
for y in range(2):
    for x in range(16):
        stage_spikes[y1 - 8 + y][x0 + 24 + x] = __import__("trap_family").CH[
            spike_plate[y][x]]
stage_damage = [r[:] for r in stage_spikes]
paste(stage_damage, SPRITES["decal_crack_16"], 20, 48)
paste(stage_damage, SPRITES["decal_bones"], 22, 52)
stage_fort = [r[:] for r in stage_damage]
paste(stage_fort, SPRITES["decal_grate"], 4, 8)
paste(stage_fort, SPRITES["decal_chain"], 60, 8)

STAGES = [
    ("F1 pristine", crop(stage_pristine)),
    ("tier1: spike slots", crop(stage_spikes)),
    ("tier2: cracks+bones", crop(stage_damage)),
    ("tier3: grate+chain", crop(stage_fort)),
]

SCALE = 3
cw, chh = (x1 - x0) * SCALE, (y1 - y0) * SCALE
LABEL_H = 18
sheet = Image.new("RGB", (4 * (cw + 16) + 16, chh + LABEL_H + 40), (14, 14, 20))
d = ImageDraw.Draw(sheet)
d.text((12, sheet.height - 18),
       "Escalation dressing over the SAME corridor — the castle remembers.",
       fill=(220, 210, 180))
for i, (label, rows) in enumerate(STAGES):
    x = 16 + i * (cw + 16)
    d.text((x, 2), label, fill=(220, 210, 180))
    for y, row in enumerate(rows):
        for xx, w in enumerate(row):
            d.rectangle([x + xx * SCALE, LABEL_H + y * SCALE,
                         x + (xx + 1) * SCALE - 1, LABEL_H + (y + 1) * SCALE - 1],
                        fill=cry_to_rgb(w))
sheet.save(os.path.join(IMG_OUT, "v2_adaptation.png"))

# ---- fragments ----------------------------------------------------------------
def write_frag(name, rows):
    w, h = len(rows[0]), len(rows)
    lines = [
        f"; {name} — {w}x{h} CRY16 adaptation decal (kimi/visual-refinement)",
        f"; Transparent overlay ($0000). Design asset — new OP slot would be Bob Checkpoint B.",
        f"{name}:",
    ]
    vals = [CH[c] for row in rows for c in row]
    for i in range(0, len(vals), 8):
        lines.append("        dc.w    " + ",".join(f"${v:04X}" for v in vals[i:i + 8]))
    with open(os.path.join(SPR_OUT, f"{name}.s"), "w") as fh:
        fh.write("\n".join(lines) + "\n")

for name, rows in SPRITES.items():
    write_frag(name, rows)

print("sheet:", os.path.join(IMG_OUT, "v2_adaptation.png"))
print("decals:", list(SPRITES))
