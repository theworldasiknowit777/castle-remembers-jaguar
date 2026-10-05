# prop_family.py — Castle Remembers doors, gate, levers, exit, arrows, ladder
# (kimi/visual-refinement)
#
# Same-size replacements for Gate 7 placeholder slots (Bob Checkpoint A):
#   img_door_closed / img_door_open / img_door_brick   8x40
#   img_gate                                          16x32  portcullis
#   img_lever_idle / tell / pulled / sprung            8x12
#   img_exit                                          32x48  bright goal arch
#   img_arrow_r / img_arrow_l                          8x2
#   img_ladder                                        16x216 wood strip
#
# Rules honoured: $0000 transparent (all these sprites are TRANS); solid mass
# stays inside collision boxes; trapped-lever tell = copper knob ($D6BF),
# subtle but learnable. Palette VJ-verified via kpalette.py.
# Fragments are dc.w lists matching castle_art.inc. NOT linked — Claude
# integrates, Bob confirms Checkpoint A.

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
    "m": PAL["MORTAR"],
    "w": PAL["WARM_M"],
    "W": PAL["WARM_L"],
    "d": PAL["WARM_D"],
    "i": PAL["IRON_D"],
    "I": PAL["IRON_L"],
    "W2": None,  # placeholder (unused two-char keys not supported)
}
del CH["W2"]
CH.update({
    "o": PAL["WOOD"],
    "b": PAL["WOOD_D"],
    "G": PAL["GOLD"],
    "K": PAL["COPPER"],
    "P": PAL["PALE_L"],
    "p": PAL["PALE_D"],
    "D": PAL["DAWN_GL"],
    "Y": PAL["FLAME_Y"],
    "B": PAL["BONE"],
    "R": PAL["BANNER"],
})

def rows_to_list(rows):
    return [list(r) for r in rows]

# ---------------------------------------------------------------- doors (8x40)
def door_closed():
    g = [["."] * 8 for _ in range(40)]
    for y in range(1, 39):
        for x in range(1, 7):
            g[y][x] = "o"                      # planks
    for x in range(1, 7):                      # vertical grain
        if x in (3,):
            for y in range(1, 39):
                g[y][x] = "b"
    for y in (8, 9, 29, 30):                   # iron straps
        for x in range(1, 7):
            g[y][x] = "i"
    for y in (8, 29):                          # studs
        g[y][2] = "I"; g[y][5] = "I"
    g[19][4] = "I"; g[20][4] = "i"; g[20][5] = "i"; g[21][4] = "i"  # ring pull
    for y in range(40):                        # frame + outline
        g[y][0] = "O"; g[y][7] = "O"
    for x in range(8):
        g[0][x] = "O" if x in (0, 7) else ("d" if 1 <= x <= 6 else "O")
        g[39][x] = "k" if 1 <= x <= 6 else "O"
    g[0][1] = "."; g[0][6] = "."               # arch corners
    g[1][1] = "o"; g[1][6] = "o"
    return ["".join(r) for r in g]

def door_open():
    g = [["."] * 8 for _ in range(40)]
    for y in range(2, 39):                     # side jambs only
        g[y][0] = "O"; g[y][1] = "d"
        g[y][6] = "d"; g[y][7] = "O"
    for x in range(8):                         # lintel
        g[0][x] = "O" if x in (0, 7) else "."
        g[1][x] = "d" if 1 <= x <= 6 else "O"
    for y in range(2, 38):                     # dark passage beyond
        for x in range(2, 6):
            g[y][x] = "k"
    return ["".join(r) for r in g]

def door_brick():
    g = [["."] * 8 for _ in range(40)]
    for y in range(1, 39):                     # bricked infill, staggered courses
        course = (y // 4) % 2
        for x in range(1, 7):
            g[y][x] = "w"
        g[y][1 + (3 if course else 0)] = "m"
        g[y][5 - (3 if course else 0)] = "m"
        if y % 4 == 0:
            for x in range(1, 7):
                g[y][x] = "m"
    for y in range(40):
        g[y][0] = "O"; g[y][7] = "O"
    for x in range(2, 6):
        g[0][x] = "."
    g[0][0] = "O"; g[0][7] = "O"
    return ["".join(r) for r in g]

# ---------------------------------------------------------------- gate (16x32)
def gate():
    g = [["."] * 16 for _ in range(32)]
    for y in range(32):                        # side channels
        g[y][0] = "i"; g[y][15] = "i"
    for x in range(2, 14, 2):                  # vertical bars
        for y in range(1, 29):
            g[y][x] = "I"
            g[y][x + 1] = "i"
    for y in (4, 5, 14, 15, 24, 25):           # crossbars
        for x in range(1, 15):
            g[y][x] = "i" if g[y][x] == "." else "I"
    for x in range(2, 14, 2):                  # pointed tips
        g[29][x] = "I"
        g[30][x] = "i" if x % 4 else "I"
        g[31][x] = "I" if x % 4 == 2 else "."
    return ["".join(r) for r in g]

# ---------------------------------------------------------------- levers (8x12)
def lever(knob, pulled=False, sprung=False):
    g = [["."] * 8 for _ in range(12)]
    for x in range(2, 6):                      # pedestal
        g[11][x] = "i"
        g[10][x] = "i"
    g[11][2] = "O"; g[11][5] = "O"
    if sprung:
        g[9][3] = "i"; g[10][3] = "I"          # snapped stump
        g[11][6] = knob; g[10][6] = "."        # fallen knob
        g[9][2] = "k"
    elif pulled:
        for i in range(4):                     # handle down-right
            g[7 + i][3 + i] = "i"
        g[10][6] = knob; g[11][6] = knob
        g[10][7] = "."
    else:
        for i in range(5):                     # handle up-right
            g[8 - i][3 + (i // 2)] = "i"
        g[2][4] = knob; g[3][4] = knob
        g[2][5] = knob
    return ["".join(r) for r in g]

# ---------------------------------------------------------------- exit (32x48)
def exit_arch():
    g = [["."] * 32 for _ in range(48)]
    cx = 16
    r = 13
    # stone surround: pale blocks with dark outline
    for y in range(48):
        for x in range(32):
            dx = abs(x - cx)
            if y >= r:
                in_arch = dx <= 10
                edge = dx in (11, 12)
            else:
                d2 = (dx) ** 2 + (y - r) ** 2
                in_arch = d2 <= 10 ** 2
                edge = 10 ** 2 < d2 <= 13 ** 2
            if edge:
                g[y][x] = "P" if (x + y) % 5 else "p"
            elif in_arch:
                # glowing interior: brightest at centre-bottom
                dist = ((x - cx) ** 2 + (y - 46) ** 2) ** 0.5
                g[y][x] = "Y" if dist < 9 else "D"
    # outline around surround
    for y in range(48):
        for x in range(32):
            if g[y][x] == ".":
                continue
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < 32 and 0 <= ny < 48 and g[ny][nx] == ".":
                    if g[y][x] in ("P", "p"):
                        g[y][x] = g[y][x]
    # threshold steps
    for x in range(4, 28):
        g[47][x] = "p"
        g[46][x] = "P" if 4 <= x <= 28 else g[46][x]
    return ["".join(r) for r in g]

# ---------------------------------------------------------------- arrows (8x2)
def arrow(direction):
    g = [["."] * 8 for _ in range(2)]
    if direction == "r":
        g[0][5] = "I"; g[0][6] = "I"; g[0][7] = "I"
        g[1][0] = "R"; g[1][1] = "B"
        for x in range(2, 7):
            g[1][x] = "o"
        g[0][4] = "o"
    else:
        g[0][0] = "I"; g[0][1] = "I"; g[0][2] = "I"
        g[1][6] = "R"; g[1][7] = "B"
        for x in range(1, 6):
            g[1][x] = "o"
        g[0][3] = "o"
    return ["".join(r) for r in g]

# ---------------------------------------------------------------- ladder (16x216)
def ladder():
    g = [["."] * 16 for _ in range(216)]
    for y in range(216):
        g[y][3] = "o"; g[y][4] = "b"           # rails
        g[y][11] = "o"; g[y][12] = "b"
        if y % 8 == 3:                         # rungs
            for x in range(3, 13):
                g[y][x] = "o"
                g[y][x] = "o"
            for x in (3, 11):
                g[y][x] = "i"                  # bolts
        if y % 8 == 4:
            for x in range(4, 12):
                g[y][x] = "b"
    return ["".join(r) for r in g]

SPRITES = {
    "img_door_closed": door_closed(),
    "img_door_open": door_open(),
    "img_door_brick": door_brick(),
    "img_gate": gate(),
    "img_lever_idle": lever("G"),
    "img_lever_tell": lever("K"),
    "img_lever_pulled": lever("G", pulled=True),
    "img_lever_sprung": lever("G", sprung=True),
    "img_exit": exit_arch(),
    "img_arrow_r": arrow("r"),
    "img_arrow_l": arrow("l"),
    "img_ladder": ladder(),
}

EXPECT = {
    "img_door_closed": (8, 40), "img_door_open": (8, 40), "img_door_brick": (8, 40),
    "img_gate": (16, 32), "img_lever_idle": (8, 12), "img_lever_tell": (8, 12),
    "img_lever_pulled": (8, 12), "img_lever_sprung": (8, 12),
    "img_exit": (32, 48), "img_arrow_r": (8, 2), "img_arrow_l": (8, 2),
    "img_ladder": (16, 216),
}

for name, rows in SPRITES.items():
    w, h = EXPECT[name]
    assert len(rows) == h, f"{name}: need {h} rows, got {len(rows)}"
    for r in rows:
        assert len(r) == w, f"{name}: row not {w}px: '{r}' ({len(r)})"
        for c in r:
            assert c in CH, f"{name}: bad char '{c}'"

# ---------------------------------------------------------------- preview
BG = (14, 14, 20)
SCALE = 5
LABEL_H = 18
sheet = Image.new("RGB", (1000, 330), BG)
d = ImageDraw.Draw(sheet)
x, y, row_h = 12, LABEL_H, 0
for name, rows in SPRITES.items():
    wpx, hpx = len(rows[0]) * SCALE, len(rows) * SCALE
    if x + wpx > 988:
        x = 12
        y += row_h + LABEL_H + 8
        row_h = 0
    d.text((x, y - 12), name.replace("img_", ""), fill=(220, 210, 180))
    for yy, row in enumerate(rows):
        for xx, c in enumerate(row):
            if c == ".":
                continue
            d.rectangle([x + xx * SCALE, y + yy * SCALE,
                         x + (xx + 1) * SCALE - 1, y + (yy + 1) * SCALE - 1],
                        fill=cry_to_rgb(CH[c]))
    x += wpx + 20
    row_h = max(row_h, hpx)
sheet.save(os.path.join(IMG_OUT, "v2_props.png"))

# ---------------------------------------------------------------- fragments
def write_frag(name, rows):
    w, h = len(rows[0]), len(rows)
    lines = [
        f"; {name} — {w}x{h} CRY16 prop art (kimi/visual-refinement)",
        f"; Palette VJ-verified (kpalette.py). Same-size slot replacement — Bob Checkpoint A.",
        f"; NOT linked — Claude integrates.",
        f"{name}:",
    ]
    vals = [CH[c] for row in rows for c in row]
    for i in range(0, len(vals), 8):
        lines.append("        dc.w    " + ",".join(f"${v:04X}" for v in vals[i:i + 8]))
    with open(os.path.join(SPR_OUT, f"{name}.s"), "w") as fh:
        fh.write("\n".join(lines) + "\n")

for name, rows in SPRITES.items():
    write_frag(name, rows)

print("sheet:", os.path.join(IMG_OUT, "v2_props.png"))
print("fragments:", list(SPRITES))
