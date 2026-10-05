# trap_family.py — Castle Remembers trap sprite sheets (kimi/visual-refinement)
#
# Design assets only — 16x16 CRY16 maps for the official trap roster per
# docs/visual/reference/ref_castle_a.png:
#   Spikes, Falling Block, Flame Hazard, Swinging Blade.
# Architecture-native: each trap reads as part of the castle masonry/ironwork.
# Not linked into the game; Bob allocates buffers, Claude wires behavior (V4).
# CRY16 decode: same documented APPROXIMATION as cry_preview.py.

import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_OUT = os.path.join(HERE, "..", "..", "docs", "visual", "previews")
SPR_OUT = os.path.join(HERE, "..", "..", "docs", "visual", "sprites")
os.makedirs(IMG_OUT, exist_ok=True)
os.makedirs(SPR_OUT, exist_ok=True)

TRANS = 0x0000
OUTL = 0x3601   # near-black outline / crack
BONE_M = 0xCE7B # stone mid (proven)
BONE_L = 0xCE9C # stone light / edge glint
GOLD = 0xCFCB   # proven gold (flame mid)
DKRED = 0xF001  # proven deep red (warning groove, flame edge)
IRON = 0x4E1C   # proven dark iron grey
MORTAR = 0x3943 # proven mortar grey
GREY_M = 0x4E3C # mid grey — VERIFY-ON-SCREEN (fallback $3943)
PLUME = 0xD645  # proven warm brown (flame wisp)
HOT = 0xF0A4    # proven bright warm (hero chest) — flame core

def cry(v):
    if v == 0x0000:
        return None
    y = v & 0xFF
    if (v >> 15) == 0:
        return (y, y, y)
    r = (v >> 11) & 0xF
    return (max(0, min(255, int(y + (r - 7.5) * 16))), y, y)

CH = {
    ".": TRANS, "O": OUTL, "b": BONE_M, "B": BONE_L, "G": GOLD,
    "R": DKRED, "i": IRON, "m": MORTAR, "M": GREY_M, "p": PLUME, "Y": HOT,
}

SPRITES = {
    # ---- Spikes: stone teeth on mortar bed (retracted = bed only) --------
    "spikes": [
        "................",
        "................",
        "................",
        "................",
        "................",
        ".B...B...B...B..",
        ".BB..BB..BB..BB.",
        ".bb..bb..bb..bb.",
        ".bb..bb..bb..bb.",
        ".bbb.bbb.bbb.bbb",
        ".bbb.bbb.bbb.bbb",
        ".bbb.bbb.bbb.bbb",
        "OOOOOOOOOOOOOOOO",
        "mmmmmmmmmmmmmmmm",
        "OOOOOOOOOOOOOOOO",
        "................",
    ],
    # ---- Falling Block: cracked masonry slab, red warning groove ---------
    "falling_block": [
        "......OOOO......",
        "......OiiO......",
        "OOOOOOOOOOOOOOOO",
        "ObbbbbbbbbbbbbbO",
        "ObBBbbbBbbbBBbbO",
        "ObbbbbbObbbbbbbO",
        "ObbbbbbbObbbbbbO",
        "ObbbbbbObbbbbbbO",
        "ObbbbbOOObbbbbbO",
        "ObbbbbbbObbbbbbO",
        "ObbbbbbBbbbbbbbO",
        "ObbbbbbbbbbbbbbO",
        "ORRRRRRRRRRRRRRO",
        "OOOOOOOOOOOOOOOO",
        "................",
        "................",
    ],
    # ---- Flame Hazard: iron sconce + rising jet (core/mid/edge/wisp) -----
    "flame_hazard": [
        ".......p........",
        "......pRp.......",
        "......RYR.......",
        ".....pRYRp......",
        ".....RYGYR......",
        ".....RYGYR......",
        "....pRYGYRp.....",
        "....RYYYYR......",
        "....RYGGYR......",
        "...pRYYYYRp.....",
        "...RYYGGYYR.....",
        "...RYYYYYYR.....",
        "..ORRYYYYYYRRO..",
        "..OiiiiiiiiiO...",
        "...OiiiiiiO.....",
        "....OOOOOO......",
    ],
    # ---- Swinging Blade: chain links + crescent blade, edge glint --------
    "swinging_blade": [
        ".......O........",
        ".......i........",
        ".......O........",
        ".......i........",
        ".......O........",
        "......OOO.......",
        ".....OiBiO......",
        "....OiiiiiO.....",
        "...OiiiiiiiO....",
        "..OiiiiiO.......",
        "..OiiiO.........",
        "..OiBO..........",
        "..OBO...........",
        "...O............",
        "................",
        "................",
    ],
}

for name, rows in SPRITES.items():
    assert len(rows) == 16, f"{name}: need 16 rows"
    for r in rows:
        assert len(r) == 16, f"{name}: row not 16px: '{r}' ({len(r)})"
        for c in r:
            assert c in CH, f"{name}: bad char '{c}'"

for name, rows in SPRITES.items():
    print(f"\n== {name} ==")
    for r in rows:
        print("  " + r)

BG = (14, 14, 20)
SCALE = 12
CELL = 16 * SCALE
LABEL_H = 26
sheet = Image.new("RGB", (len(SPRITES) * (CELL + 16) + 16, CELL + LABEL_H + 16), BG)
d = ImageDraw.Draw(sheet)
for i, (name, rows) in enumerate(SPRITES.items()):
    x0 = 16 + i * (CELL + 16)
    d.text((x0, 4), name.replace("_", " ").upper(), fill=(220, 210, 180))
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            col = cry(CH[c])
            if col is None:
                continue
            d.rectangle([x0 + x * SCALE, LABEL_H + y * SCALE,
                         x0 + (x + 1) * SCALE - 1, LABEL_H + (y + 1) * SCALE - 1],
                        fill=col)
sheet.save(os.path.join(IMG_OUT, "v1_trap_family.png"))

def pack(rows):
    vals = [CH[c] for row in rows for c in row]
    return [(vals[i] << 16) | vals[i + 1] for i in range(0, len(vals), 2)]

for name, rows in SPRITES.items():
    lws = pack(rows)
    lines = [
        f"; {name} — 16x16 CRY16 trap (kimi/visual-refinement design asset)",
        f"; NOT linked into the game — Bob allocates buffer, Claude wires behavior",
        f"{name}_pixels:",
    ]
    for r in range(16):
        chunk = ",".join(f"${v:08X}" for v in lws[r * 8:(r + 1) * 8])
        lines.append(f"        dc.l    {chunk}  ; row {r:02d}")
    with open(os.path.join(SPR_OUT, f"{name}.s"), "w") as fh:
        fh.write("\n".join(lines) + "\n")

print("\nsheet:", os.path.join(IMG_OUT, "v1_trap_family.png"))
print("fragments:", os.path.abspath(SPR_OUT))
