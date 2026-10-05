# trap_family.py — Castle Remembers trap sprites, V2 runtime-compatible
# (kimi/visual-refinement)
#
# V2 = palette repair pass: all words VJ-verified via kpalette.py.
# $F001 (black) and $CE7B (olive) are gone; warning red is $E26E/$E2DD.
#
# Runtime drop-ins (same-size replacements for Gate 7 slots, Bob Checkpoint A):
#   img_spike16  16x8   raised; rows 6-7 alone = retracted slot plate
#   img_spike24  24x8   same, 6 teeth
#   img_flame    64x16  eruption, 4 jets; rows 14-15 alone = ember warning
# Design assets (new OP slots later, Bob Checkpoint B):
#   falling_block 16x16, swinging_blade 16x16 (polished), flame_hazard 16x16
#
# Fragments are dc.w word lists matching castle_art.inc format.
# Not linked into the game — Claude integrates, Bob confirms checkpoints.

import os
from PIL import Image, ImageDraw

from kpalette import PAL, cry_to_rgb

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_OUT = os.path.join(HERE, "..", "..", "docs", "visual", "previews")
SPR_OUT = os.path.join(HERE, "..", "..", "docs", "visual", "sprites")
os.makedirs(IMG_OUT, exist_ok=True)
os.makedirs(SPR_OUT, exist_ok=True)

CH = {
    ".": PAL["TRANS"] if "TRANS" in PAL else 0x0000,
    "O": PAL["BLACK"],
    "k": PAL["SHADOW"],
    "m": PAL["MORTAR"],
    "w": PAL["WARM_M"],
    "W": PAL["WARM_L"],
    "i": PAL["IRON_D"],
    "I": PAL["IRON_L"],
    "R": PAL["WARN_D"],
    "Y": PAL["FLAME_Y"],
    "F": PAL["FLAME_O"],
    "e": PAL["EMBER"],
    "B": PAL["BONE"],
}
CH["."] = 0x0000

# ---------------------------------------------------------------- spikes (8-row runtime slots)
# Teeth = pale stone (WARM_L tip / WARM_M body) on a mortar slot plate.
# Rows 6-7 must read as "flush dark slots" when drawn alone (retracted state).

def spike_rows(width, teeth):
    rows = []
    tooth = [width // teeth * t + 1 for t in range(teeth)]  # left edge of each tooth
    body = [[x, x + 1, x + 2] for x in tooth]
    for r in range(8):
        line = ["."] * width
        if r <= 1:
            for b in body:
                line[b[0] + 1] = "W"
        elif r <= 3:
            for b in body:
                line[b[0]] = "W"; line[b[0] + 1] = "W"; line[b[0] + 2] = "w"
        elif r <= 5:
            for b in body:
                line[b[0]] = "w"; line[b[0] + 1] = "w"; line[b[0] + 2] = "w"
        elif r == 6:
            line = ["m"] * width
        else:
            line = ["m"] * width
            for b in body:
                line[b[0]] = "k"; line[b[0] + 1] = "k"
        rows.append("".join(line))
    return rows

IMG_SPIKE16 = spike_rows(16, 4)
IMG_SPIKE24 = spike_rows(24, 6)

# ---------------------------------------------------------------- flame (64x16 runtime slot)
# Four jets across, varying heights; rows 14-15 = ember bed (warning state).

JET_H = [13, 11, 14, 12]          # jet height per 16-px tile (max row 13)
PROFILE = {0: "YY", 1: "YY"}      # rel row -> core pattern (widened below)

def flame_rows():
    rows = [["."] * 64 for _ in range(16)]
    for t, h in enumerate(JET_H):
        cx = t * 16 + 8
        top = 14 - h
        for r in range(top, 14):
            rel = r - top
            if rel <= 1:
                span, pat = 2, ("Y", "Y")
            elif rel <= 4:
                span, pat = 5, ("F", "Y", "Y", "Y", "F")
            elif rel <= 8:
                span, pat = 7, ("F", "F", "Y", "Y", "Y", "F", "F")
            else:
                span, pat = 9, ("F", "F", "Y", "Y", "Y", "Y", "Y", "F", "F")
            x0 = cx - span // 2
            for i, c in enumerate(pat):
                rows[r][x0 + i] = c
        # flicker: a couple of ember sparks above the tip
        rows[max(0, top - 1)][cx + (1 if t % 2 else -1)] = "e"
    # ember bed (warning state when drawn alone)
    ember_x = [2, 7, 12, 19, 24, 30, 35, 41, 46, 52, 57, 62]
    for x in ember_x:
        rows[14][x] = "e"
    for x in (x + 3 for x in ember_x[::2]):
        if x < 64:
            rows[15][x] = "e"
    for x in (0, 15, 16, 31, 32, 47, 48, 63):
        rows[15][x] = "k"   # scorched ground line
    return ["".join(r) for r in rows]

IMG_FLAME = flame_rows()

# ---------------------------------------------------------------- design assets (16x16, Checkpoint B)

FALLING_BLOCK = [
    "......OOOO......",
    "......OiiO......",
    "OOOOOOOOOOOOOOOO",
    "OwwwwwwwwwwwwwwO",
    "OwWWwwwWwwwWWwwO",
    "OwwwwwwOwwwwwwwO",
    "OwwwwwwwOwwwwwwO",
    "OwwwwwwOwwwwwwwO",
    "OwwwwwOOOwwwwwwO",
    "OwwwwwwOwwwwwwwO",
    "OwwwwwwWwwwwwwwO",
    "OwwwwwwwwwwwwwwO",
    "ORRRRRRRRRRRRRRO",
    "OOOOOOOOOOOOOOOO",
    "................",
    "................",
]

SWINGING_BLADE = [
    ".......OO.......",
    ".......iO.......",
    ".......Oi.......",
    ".......iO.......",
    ".......Oi.......",
    "......OOO.......",
    ".....OIIiO......",
    "....OIIIiiO.....",
    "...OBIIiiiO.....",
    "..OBIIiiiO......",
    "..OBIIiiO.......",
    "..OBIiiO........",
    "..OBiO..........",
    "..OBO...........",
    "...O............",
    "................",
]

FLAME_HAZARD = [
    ".......e........",
    "......eFe.......",
    "......FYF.......",
    ".....eFYFe......",
    ".....FYFYF......",
    ".....FYFYF......",
    "....eFYFYFe.....",
    "....FYYYYF......",
    "....FYFFYF......",
    "...eFYYYYFe.....",
    "...FYYFFYYF.....",
    "...FYYYYYYF.....",
    "..OFFYYYYYYFFO..",
    "..OiiiiiiiiiO...",
    "...OiiiiiiO.....",
    "....OOOOOO......",
]

RUNTIME = {
    "img_spike16": IMG_SPIKE16,
    "img_spike24": IMG_SPIKE24,
    "img_flame": IMG_FLAME,
}
ASSETS = {
    "falling_block": FALLING_BLOCK,
    "swinging_blade": SWINGING_BLADE,
    "flame_hazard": FLAME_HAZARD,
}

# ---------------------------------------------------------------- validation
for name, rows in {**RUNTIME, **ASSETS}.items():
    w = len(rows[0])
    for r in rows:
        assert len(r) == w, f"{name}: ragged row '{r}'"
        for c in r:
            assert c in CH, f"{name}: bad char '{c}'"
assert len(IMG_SPIKE16) == 8 and len(IMG_SPIKE16[0]) == 16
assert len(IMG_SPIKE24) == 8 and len(IMG_SPIKE24[0]) == 24
assert len(IMG_FLAME) == 16 and len(IMG_FLAME[0]) == 64
for rows in ASSETS.values():
    assert len(rows) == 16 and len(rows[0]) == 16

# ---------------------------------------------------------------- preview sheet
SCALE = 6
LABEL_H = 22
BG = (14, 14, 20)

def blit(d, rows, x0, y0, scale):
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c == ".":
                continue
            col = cry_to_rgb(CH[c])
            d.rectangle([x0 + x * scale, y0 + y * scale,
                         x0 + (x + 1) * scale - 1, y0 + (y + 1) * scale - 1],
                        fill=col)

items = [
    ("img_spike16 (16x8)", IMG_SPIKE16, 8),
    ("retracted = rows 6-7", IMG_SPIKE16[6:], 8),
    ("img_spike24 (24x8)", IMG_SPIKE24, 8),
    ("img_flame (64x16)", IMG_FLAME, 4),
    ("warning = rows 14-15", IMG_FLAME[14:], 8),
    ("falling_block (16x16)", FALLING_BLOCK, 6),
    ("swinging_blade (16x16)", SWINGING_BLADE, 6),
    ("flame_hazard (16x16)", FLAME_HAZARD, 6),
]
W = 1000
H = 320
sheet = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(sheet)
x, y = 12, LABEL_H
row_h = 0
for label, rows, sc in items:
    wpx = len(rows[0]) * sc
    hpx = len(rows) * sc
    if x + wpx > W - 12:
        x = 12
        y += row_h + LABEL_H + 10
        row_h = 0
    d.text((x, y - 14), label, fill=(220, 210, 180))
    blit(d, rows, x, y, sc)
    x += wpx + 24
    row_h = max(row_h, hpx)
sheet.save(os.path.join(IMG_OUT, "v2_trap_family.png"))

# ---------------------------------------------------------------- fragments
def write_frag(name, rows, checkpoint):
    w, h = len(rows[0]), len(rows)
    lines = [
        f"; {name} — {w}x{h} CRY16 trap art (kimi/visual-refinement)",
        f"; Palette VJ-verified (kpalette.py). {checkpoint}",
        f"; NOT linked — Claude integrates, Bob confirms checkpoint.",
        f"{name}:",
    ]
    vals = [CH[c] for row in rows for c in row]
    for i in range(0, len(vals), 8):
        lines.append("        dc.w    " + ",".join(f"${v:04X}" for v in vals[i:i + 8]))
    with open(os.path.join(SPR_OUT, f"{name}.s"), "w") as fh:
        fh.write("\n".join(lines) + "\n")

for name, rows in RUNTIME.items():
    write_frag(name, rows, "Same-size slot replacement — Bob Checkpoint A.")
for name, rows in ASSETS.items():
    write_frag(name, rows, "New OP slot required — Bob Checkpoint B.")

print("sheet:", os.path.join(IMG_OUT, "v2_trap_family.png"))
print("runtime fragments:", list(RUNTIME))
print("design assets:", list(ASSETS))
