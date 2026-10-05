# enemy_family_24.py — Castle Remembers enemy family, Gate 7 runtime sizes
# (kimi/visual-refinement)
#
# 16x24 same-size replacements for the Gate 7 slots (Bob Checkpoint A):
#   img_guard    Fallen Guard         — humanoid knight, tattered red tunic
#   img_heavy    Fallen Guard, heavy  — full plate + big shield, reads tougher
#   img_watcher  Stone Watcher        — statue archer on pedestal, bow
#   img_wraith   Judgment Wraith      — hooded, legless, floats; F5 pursuer
# Design asset (no slot yet, Checkpoint B):
#   castle_hound 16x16 — low runner (Claude's "watch" tier-1 proposal)
#
# Sentinel Skull is Bob's protected art (img_skull) — not touched here.
# Palette VJ-verified via kpalette.py ($F001 black / $CE7B olive defects fixed).
# Collision awareness: solid mass inside x+3..x+13; detail in top 6 rows is
# harmless (integration brief §0). Fragments are dc.w lists, castle_art.inc style.
# NOT linked — Claude integrates, Bob confirms checkpoints.

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
    "P": PAL["PALE_L"],
    "R": PAL["BANNER"],
    "r": PAL["BANNER_D"],
    "G": PAL["GOLDTRIM"],
    "g": PAL["GOLD"],
    "c": PAL["COOL_M"],
    "C": PAL["COOL_L"],
    "s": PAL["SOLE_M"],
    "S": PAL["SOLE_D"],
    "W": PAL["WOOD"],
    "e": PAL["EMBER"],
    "E": PAL["WARN_R"],
}

SPRITES = {
    # ---- Fallen Guard: plume remnant (harmless top), helm, red tunic, sword
    "img_guard": [
        "................",
        "......rG........",
        ".....rGGr.......",
        "....OOOO........",
        "...OiiIIiO......",
        "...OiOiiO.......",
        "...OikikiO......",
        "...OIIIIIiO.....",
        "....OiiiiO......",
        "..ORRRRRRRO.....",
        ".ORrRRRRRrRO....",
        ".ORRRRRRRRRO....",
        ".ORRRkRRRROIi...",
        ".ORrRRRrRO.OI...",
        "..ORRRRRRO..Oi..",
        "..ORRkRRRO..Oi..",
        "..ORRRRRRO..O...",
        "...OiOOiOO......",
        "...OiO.OiO......",
        "..ORiO.ORiO.....",
        "..OiiO.OiiO.....",
        "..OiO..OiO......",
        "..OOOO.OOOO.....",
        "................",
    ],
    # ---- Heavy: no plume, full plate, big shield left, darker mass
    "img_heavy": [
        "................",
        "................",
        "....OOOOO.......",
        "...OiiiiiO......",
        "..OiIIIIIiO.....",
        "..OiOiiiOiO.....",
        "..OikikikiO.....",
        "..OIIIIIIIiO....",
        "...OiiiiiO......",
        "..OIIIIIIIO.....",
        ".OOOOIIIIIIiO...",
        ".OIIIIOIIiIIiO..",
        ".OIiEIOiiiiiIO..",
        ".OIIIIOiiiiiiO..",
        ".OIIEIO.OiiIO...",
        ".OIIIIO.OiiO....",
        ".OIiEIO.OiiO....",
        ".OIIIIOiOOiOO...",
        ".OOOOOOiO.OiO...",
        ".......OiO.OiO..",
        "......OiiO.OiiO.",
        "......OiO..OiO..",
        "......OOOO.OOOO.",
        "................",
    ],
    # ---- Stone Watcher: square statue head, gold eye, bow at ready, pedestal
    "img_watcher": [
        "..OO...OO.......",
        "..OOOOOOOO......",
        ".OccccccccO.....",
        ".OcCCCCCCcO.....",
        ".OcCccccCcO.....",
        ".OcccggcccO.....",
        ".OcccggcccO.W...",
        ".OcCCCCCCcO.W...",
        ".OccccccccO..W..",
        ".OcOOccOOcO..W..",
        ".OccccccccO...W.",
        "..OccccccO....W.",
        "..OCCCCCCO...W..",
        "..OcccccccO..W..",
        "..OcCCccCcO.W...",
        "..OccccccccO....",
        "..OccccccccO....",
        ".OOccccccccOO...",
        ".OcCCCCCCCCCcO..",
        ".OcccccccccccO..",
        ".OOOOOOOOOOOOO..",
        ".OcccccccccccO..",
        ".OOOOOOOOOOOOO..",
        "................",
    ],
    # ---- Judgment Wraith: tall hood, pale void face, red eyes, tattered hem
    "img_wraith": [
        ".......OO.......",
        "......OSSO......",
        ".....OSssSO.....",
        "....OSssssSO....",
        "....OSPPPSSO....",
        "....SPEEEPSO....",
        "....SPPPPPSO....",
        "...OSsPPPsSO....",
        "...OSssssssSO...",
        "..OSssssssssSO..",
        "..OSsskSSkssSO..",
        "..OSssssssssSO..",
        ".OSssssssssssSO.",
        ".OSsSSssssSSsSO.",
        ".OSssssssssssSO.",
        ".OSssSSSSSSssSO.",
        ".OSssssssssssSO.",
        ".OSssssssssssSO.",
        ".OSsSOSSsSOSSO..",
        ".OSsO.SSsO.SsO..",
        ".OSO..SsO..SO...",
        ".OO...SO...O....",
        "................",
        "................",
    ],
}

ASSETS = {
    # ---- Castle Hound: low four-legged runner (design asset, no slot yet)
    "castle_hound": [
        "................",
        "................",
        "................",
        "..O.O...........",
        "..OSO........OO.",
        "..OESOOOO...OO..",
        "..OSSSSSOOO.....",
        "..OBSSSSSSSO....",
        "...OSSSSSSO.....",
        "...OSSSSSO......",
        "...OS.OS.OS.....",
        "...OS..OS..OS...",
        "...OO..OO..OO...",
        "................",
        "................",
        "................",
    ],
}

# ---- validation -------------------------------------------------------------
for name, rows in SPRITES.items():
    assert len(rows) == 24, f"{name}: need 24 rows, got {len(rows)}"
    for r in rows:
        assert len(r) == 16, f"{name}: row not 16px: '{r}' ({len(r)})"
        for c in r:
            assert c in CH, f"{name}: bad char '{c}'"
for name, rows in ASSETS.items():
    assert len(rows) == 16 and all(len(r) == 16 for r in rows), name

# ---- preview sheet ----------------------------------------------------------
BG = (14, 14, 20)
SCALE = 8
LABEL_H = 22
names = list(SPRITES) + list(ASSETS)
sheet = Image.new("RGB", (len(names) * (16 * SCALE + 24) + 16,
                          24 * SCALE + LABEL_H + 16), BG)
d = ImageDraw.Draw(sheet)
for i, name in enumerate(names):
    rows = SPRITES.get(name) or ASSETS[name]
    x0 = 16 + i * (16 * SCALE + 24)
    d.text((x0, 4), name.replace("img_", "").upper(), fill=(220, 210, 180))
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c == ".":
                continue
            d.rectangle([x0 + x * SCALE, LABEL_H + y * SCALE,
                         x0 + (x + 1) * SCALE - 1, LABEL_H + (y + 1) * SCALE - 1],
                        fill=cry_to_rgb(CH[c]))
sheet.save(os.path.join(IMG_OUT, "v2_enemy_family.png"))

# ---- fragments ---------------------------------------------------------------
def write_frag(name, rows, checkpoint):
    w, h = len(rows[0]), len(rows)
    lines = [
        f"; {name} — {w}x{h} CRY16 enemy art (kimi/visual-refinement)",
        f"; Palette VJ-verified (kpalette.py). {checkpoint}",
        f"; NOT linked — Claude integrates, Bob confirms checkpoint.",
        f"{name}:",
    ]
    vals = [CH[c] for row in rows for c in row]
    for i in range(0, len(vals), 8):
        lines.append("        dc.w    " + ",".join(f"${v:04X}" for v in vals[i:i + 8]))
    with open(os.path.join(SPR_OUT, f"{name}.s"), "w") as fh:
        fh.write("\n".join(lines) + "\n")

for name, rows in SPRITES.items():
    write_frag(name, rows, "Same-size slot replacement — Bob Checkpoint A.")
for name, rows in ASSETS.items():
    write_frag(name, rows, "New OP slot required — Bob Checkpoint B.")

print("sheet:", os.path.join(IMG_OUT, "v2_enemy_family.png"))
print("runtime fragments:", list(SPRITES))
print("design assets:", list(ASSETS))
