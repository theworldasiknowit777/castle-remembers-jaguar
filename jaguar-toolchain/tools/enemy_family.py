# enemy_family.py — Castle Remembers enemy family sprite sheet (kimi/visual-refinement)
#
# Design assets only — 16x16 CRY16 maps for the official roster per
# docs/visual/reference/ref_castle_a.png:
#   Sentinel Skull (V0, shipped), Fallen Guard, Stone Watcher,
#   Judgment Wraith, Castle Hound.
# Nothing here is linked into the game; Bob allocates DRAM buffers and
# Claude wires behavior when V3 lands. Palette anchors per plan §2.
#
# CRY16 decode is the same documented APPROXIMATION as cry_preview.py.

import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_OUT = os.path.join(HERE, "..", "..", "docs", "visual", "previews")
SPR_OUT = os.path.join(HERE, "..", "..", "docs", "visual", "sprites")
os.makedirs(IMG_OUT, exist_ok=True)
os.makedirs(SPR_OUT, exist_ok=True)

TRANS = 0x0000
OUTL = 0x3601   # near-black outline
BONE_M = 0xCE7B # bone/stone mid (proven)
BONE_L = 0xCE9C # bone/stone light
GOLD = 0xCFCB   # proven gold
GOLD_D = 0xCF8B # dim gold — VERIFY-ON-SCREEN (fallback $CFCB)
DKRED = 0xF001  # proven deep red
IRON = 0x4E1C   # proven dark iron grey
GREY_M = 0x4E3C # mid grey — VERIFY-ON-SCREEN (fallback $3943)
GREY_L = 0x4E5A # light grey — VERIFY-ON-SCREEN (fallback $4E1C)
PLUME = 0xD645  # proven warm cloak brown-red
HOUND = 0x4E2C  # hound body — VERIFY-ON-SCREEN (fallback $4E1C)

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
    "g": GOLD_D, "R": DKRED, "i": IRON, "m": GREY_M, "M": GREY_L,
    "p": PLUME, "d": HOUND,
}

SPRITES = {
    # ---- V0 baseline, shipped on this branch ------------------------------
    "sentinel_skull": [
        "................",
        "....OOOOOOOO....",
        "..OObbbbbbbbOO..",
        ".ObbbbbbbbbbbbO.",
        ".ObBBBbbbbBBBbO.",
        ".ObbRGRbbRGRbbO.",
        ".ObbRRRbbRRRbbO.",
        ".ObbbbbOObbbbbO.",
        "..ObbbbRRbbbbO..",
        "..ObbbbbbbbbbO..",
        "...ObbbbbbbbO...",
        "...ObRbRRbRbO...",
        "....ObbbbbbO....",
        ".....OOOOOO.....",
        "................",
        "................",
    ],
    # ---- Fallen Guard: slumped knight, round red shield, plume remnant ----
    "fallen_guard": [
        "................",
        "....OOOO........",
        "...OmMMmO.......",
        "...OMmmMO.......",
        "...OmGGmO.......",
        "...OOOOOO.......",
        ".ppOmmmmO.......",
        ".ppOmmmmmO......",
        "..OmmmmmO.OO....",
        "..OmmmOmOORRRO..",
        "..OmmOmOORRRRRO.",
        "...OOmO.ORGRRRO.",
        "...O.OO.ORRRRRO.",
        "..iO..i.ORRRRO..",
        "..iiiiii..ORRO..",
        "................",
    ],
    # ---- Stone Watcher: square statue head, single gold eye, pedestal -----
    "stone_watcher": [
        "..OO...OO...OO..",
        "..OOOOOOOOOOOO..",
        "..ObbbbbbbbbbbO.",
        "..ObBBBBBBBBbbO.",
        "..ObbbbbbbbbbbO.",
        "..ObbbbGGbbbbO..",
        "..ObbbbGGbbbmO..",
        "..ObbbbbbbbbbO..",
        "..ObbbOObbbbmO..",
        "..ObbbOObbbbmO..",
        "..ObbbbbbbbbbO..",
        "..ObbbbbbbbbbmO.",
        ".OOOOOOOOOOOOOO.",
        ".ObbbbbbbbbbbbO.",
        ".OOOOOOOOOOOOOO.",
        "................",
    ],
    # ---- Judgment Wraith: tall hood, gold core, tattered hem --------------
    "judgment_wraith": [
        ".......OO.......",
        "......OddO......",
        ".....OddddO.....",
        ".....OddddO.....",
        "....OddGGddO....",
        "...OdddddddO....",
        "...OdddGGdddO...",
        "...OdddGGdddO...",
        "..OddddGGddddO..",
        "..OddddddddddO..",
        "..OddddddddddO..",
        "..ORddddddddRO..",
        "..OddOddOddOdO..",
        "..OdO.OdOdO.OdO.",
        "..OO..OOO...OO..",
        "................",
    ],
    # ---- Castle Hound: low four-legged runner, gold eye, raised tail ------
    "castle_hound": [
        "................",
        "................",
        "................",
        "..O.O...........",
        "..OdO........OO.",
        "..OGdOOOO...OO..",
        "..OddddddOOO....",
        "..OBddddddddO...",
        "...OdddddddO....",
        "...OddddddO.....",
        "...Od.Od.Od.....",
        "...Od..Od..Od...",
        "...OO..OO..OO...",
        "................",
        "................",
        "................",
    ],
}

for name, rows in SPRITES.items():
    assert len(rows) == 16, f"{name}: need 16 rows"
    for r in rows:
        assert len(r) == 16, f"{name}: row not 16px: '{r}'"
        for c in r:
            assert c in CH, f"{name}: bad char '{c}'"

# ---- console check ---------------------------------------------------------
for name, rows in SPRITES.items():
    print(f"\n== {name} ==")
    for r in rows:
        print("  " + r)

# ---- sprite sheet render ----------------------------------------------------
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
sheet.save(os.path.join(IMG_OUT, "v1_enemy_family.png"))

# ---- drop-in .s fragments ---------------------------------------------------
def pack(rows):
    vals = [CH[c] for row in rows for c in row]
    return [(vals[i] << 16) | vals[i + 1] for i in range(0, len(vals), 2)]

for name, rows in SPRITES.items():
    lws = pack(rows)
    lines = [
        f"; {name} — 16x16 CRY16 (kimi/visual-refinement design asset)",
        f"; NOT linked into the game — Bob allocates buffer, Claude wires behavior",
        f"{name}_pixels:",
    ]
    for r in range(16):
        chunk = ",".join(f"${v:08X}" for v in lws[r * 8:(r + 1) * 8])
        lines.append(f"        dc.l    {chunk}  ; row {r:02d}")
    with open(os.path.join(SPR_OUT, f"{name}.s"), "w") as fh:
        fh.write("\n".join(lines) + "\n")

print("\nsheet:", os.path.join(IMG_OUT, "v1_enemy_family.png"))
print("fragments:", os.path.abspath(SPR_OUT))
