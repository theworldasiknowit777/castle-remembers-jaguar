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
    "L": PAL["SOLE_L"],
    "n": PAL["MOON"],
}

# V7 correction (Virtual Jaguar evidence, gate7_castle/v7_evidence/):
# the integrated skull used $CE7B body -> renders GREEN, same as the floor
# slab, and $F001 eyes -> render BLACK. Same 16x16 silhouette, steel-grey
# palette (COOL_L body / SOLE_L light / COOL_M shade), red eyes with pale
# glint, outline BLACK. Distinct from the green floor. 2px float retained.
IMG_SKULL = [
    "................",
    "....OOOOOOOO....",
    "..OOCCCCCCCCOO..",
    ".OCCCCCCCCCCCCO.",
    ".OCLLLCCCCLLLCO.",
    ".OCCEnECCEnECCO.",
    ".OCCEEECCEEECCO.",
    ".OCCCCCOOCCCCCO.",
    "..OCCCCEECCCCO..",
    "..OCCCCCCCCCCO..",
    "...OCCCCCCCCO...",
    "...OCECEECECO...",
    "....OCCCCCCO....",
    ".....OOOOOO.....",
    "................",
    "................",
]

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

# ---- V7 grounding + facing ---------------------------------------------------
# VJ evidence: guard/heavy/watcher sat ~1 empty row above the floor. Shift
# their art down one row so feet/pedestal sit flush (top rows stay within the
# harmless zone). Wraith and skull keep their deliberate 2px float.
for _name in ("img_guard", "img_heavy", "img_watcher"):
    _rows = SPRITES[_name]
    assert set(_rows[23]) <= set("."), f"{_name}: bottom row not empty"
    SPRITES[_name] = ["." * 16] + _rows[:23]

# The runtime does not mirror enemies. The Watcher reads as aiming with its
# bow on the viewer's right: img_watcher = RIGHT-facing. Provide an identical
# left-facing variant so Claude can swap the data pointer by facing.
SPRITES["img_watcher_l"] = [r[::-1] for r in SPRITES["img_watcher"]]

# ---- validation -------------------------------------------------------------
for name, rows in SPRITES.items():
    assert len(rows) == 24, f"{name}: need 24 rows, got {len(rows)}"
    for r in rows:
        assert len(r) == 16, f"{name}: row not 16px: '{r}' ({len(r)})"
        for c in r:
            assert c in CH, f"{name}: bad char '{c}'"
for name, rows in ASSETS.items():
    assert len(rows) == 16 and all(len(r) == 16 for r in rows), name
assert len(IMG_SKULL) == 16 and all(len(r) == 16 for r in IMG_SKULL)
assert all(c in CH for r in IMG_SKULL for c in r)

# ---- preview sheet ----------------------------------------------------------
BG = (14, 14, 20)
SCALE = 8
LABEL_H = 22
names = ["img_skull"] + list(SPRITES) + list(ASSETS)
sheet = Image.new("RGB", (len(names) * (16 * SCALE + 24) + 16,
                          24 * SCALE + LABEL_H + 16), BG)
d = ImageDraw.Draw(sheet)
for i, name in enumerate(names):
    rows = IMG_SKULL if name == "img_skull" else (SPRITES.get(name) or ASSETS[name])
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

write_frag("img_skull", IMG_SKULL,
           "Same-size slot replacement — Bob Checkpoint A. V7 palette correction; supersedes sentinel_skull.s.")
for name, rows in SPRITES.items():
    note = ("Same-size slot replacement — Bob Checkpoint A."
            if name != "img_watcher_l" else
            "Left-facing variant of img_watcher (same size) — pointer swap or new slot, Claude/Bob decide.")
    write_frag(name, rows, note)
for name, rows in ASSETS.items():
    write_frag(name, rows, "New OP slot required — Bob Checkpoint B.")

print("sheet:", os.path.join(IMG_OUT, "v2_enemy_family.png"))
print("runtime fragments:", ["img_skull"] + list(SPRITES))
print("design assets:", list(ASSETS))
