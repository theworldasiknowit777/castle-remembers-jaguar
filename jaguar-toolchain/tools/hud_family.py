# hud_family.py — Castle Remembers V6 HUD memory-category row
# (kimi/visual-refinement)
#
# Six-category memory HUD (doors, levers, pace, guards, traps, chests/greed),
# designed to sit at the bottom of the screen alongside the V6 message band.
# Asset/mockup work only: Claude wires the six categories into HUD state;
# Bob only returns if the final renderer needs new protected buffers/OP.
#
# Layout contract (see docs/kimi/V6_HUD_MEMORY_ROW.md):
#   row band y=224..239 (below the floor slab, never over gameplay)
#   per category: 8x8 icon + three 3x3 pips; 0-3 pressure
#   0 = dim icon, no pips · 1-3 = lit icon + n lit pips
#   intensify = newly lit pip ringed in STAR white for ~0.5 s
#
# Palette: Claude's five reserved category colours + proposed chests green
# ($7CC4 lit / $7C46 dim). Dim variants computed at ~35% intensity.

import os
from PIL import Image, ImageDraw

from kpalette import PAL, cry_to_rgb, rgb_to_cry
from font_family import draw_text, center_x, text_width, render_png
import backdrop_family as bf

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_OUT = os.path.join(HERE, "..", "..", "docs", "visual", "previews")
SPR_OUT = os.path.join(HERE, "..", "..", "docs", "visual", "sprites")
DOC_OUT = os.path.join(HERE, "..", "..", "docs", "kimi")
os.makedirs(IMG_OUT, exist_ok=True)
os.makedirs(SPR_OUT, exist_ok=True)
os.makedirs(DOC_OUT, exist_ok=True)

ELL = "\u2026"

CATS = [
    # name, lit word, dim word, 8x8 icon (1 = body pixel)
    ("doors",  0xF8FF, rgb_to_cry((89, 47, 0)),
     ["00111100","01100000","01100000","01101100","01101100","01101100","01101100","01101100"]),
    ("levers", 0xEAE7, rgb_to_cry((81, 61, 11)),
     ["00000110","00001100","00011000","00110000","01100000","11000000","11111110","01111100"]),
    ("pace",   0x2BDD, rgb_to_cry((20, 71, 77)),
     ["01000100","01100110","00110011","00011001","00011001","00110011","01100110","01000100"]),
    ("guards", 0xE2DD, rgb_to_cry((77, 11, 10)),
     ["00111100","01111110","01100110","01111110","00111100","00011000","00111100","00000000"]),
    ("traps",  0x53C9, rgb_to_cry((46, 23, 70)),
     ["01001001","01001001","11011011","11011011","11111111","00000000","10101010","01010101"]),
    ("chests", 0x7CC4, 0x7C46,
     ["01111110","11111111","10011001","11111111","11111111","11011011","11111111","01111110"]),
]
for name, lit, dim, icon in CATS:
    assert len(icon) == 8 and all(len(r) == 8 for r in icon), name

HUD_Y = 224
BLOCK_W = 21                       # icon 8 + gap 2 + pips 11
GAP = 28
ROW_W = 6 * BLOCK_W + 5 * GAP
X0 = (320 - ROW_W) // 2

def draw_hud(img, tiers, flash=None):
    """tiers: dict name->0..3. flash: name whose newest pip is flashing."""
    for i, (name, lit, dim, icon) in enumerate(CATS):
        x = X0 + i * (BLOCK_W + GAP)
        t = tiers.get(name, 0)
        ic = lit if t > 0 else dim
        for ry, row in enumerate(icon):
            for xx, b in enumerate(row):
                if b == "1":
                    img[HUD_Y + 2 + ry][x + xx] = ic
        for p in range(3):
            px0 = x + 10 + p * 4
            py0 = HUD_Y + 4
            on = p < t
            c = lit if on else PAL["MORTAR"]
            for dy in range(3):
                for dx in range(3):
                    img[py0 + dy][px0 + dx] = c
            if not on:                            # hollow centre for off pips
                img[py0 + 1][px0 + 1] = PAL["BLACK"]
            if flash == name and p == t - 1:      # intensify flash ring
                for dx in range(-1, 4):
                    img[py0 - 1][px0 + dx] = PAL["STAR"]
                    img[py0 + 3][px0 + dx] = PAL["STAR"]
                for dy in range(-1, 4):
                    img[py0 + dy][px0 - 1] = PAL["STAR"]
                    img[py0 + dy][px0 + 3] = PAL["STAR"]

def scene(floor_rows):
    img = [r[:] for r in floor_rows]
    for y in range(180, 240):
        img.append([PAL["BLACK"]] * 320)
    for y in range(180, 194):
        img[y] = [PAL["WARM_D"] if y % 8 else PAL["MORTAR"] for _ in range(320)]
    for y in range(194, 202):
        img[y] = [PAL["WARM_M"] if y % 4 else PAL["MORTAR"] for _ in range(320)]
    return img[:240]

# ---------------------------------------------------------------- mockups
def m_normal():                                   # early run: doors tier 1
    img = scene(bf.floor1())
    draw_text(img, center_x("FLOOR 1 - GATEHOUSE"), 8, "FLOOR 1 - GATEHOUSE")
    draw_hud(img, {"doors": 1})
    return img

def m_whisper():                                  # whisper + HUD coexist
    img = scene(bf.floor3())
    t = f"{ELL}YOU ALWAYS GO LEFT."
    draw_text(img, center_x(t), 14, t)
    draw_hud(img, {"doors": 2, "traps": 1})
    return img

def m_rebuild():                                  # rebuild screen + HUD summary
    img = [[PAL["BLACK"]] * 320 for _ in range(240)]
    draw_text(img, center_x("THE CASTLE OBSERVED YOU"), 92, "THE CASTLE OBSERVED YOU")
    draw_text(img, center_x("YOU WENT LEFT AGAIN."), 114, "YOU WENT LEFT AGAIN.")
    draw_text(img, center_x("THE LEFT SIDE STAYS ARMED."), 124, "THE LEFT SIDE STAYS ARMED.")
    r = f"RECONSTRUCTING{ELL}"
    draw_text(img, center_x(r), 156, r)
    draw_hud(img, {"doors": 2, "traps": 1})
    return img

def m_multi():                                    # several categories at once
    img = scene(bf.floor3())
    draw_hud(img, {"doors": 2, "levers": 1, "pace": 1, "traps": 2},
             flash="traps")
    return img

def m_late():                                     # high-pressure late run, F5
    img = scene(bf.floor5())
    draw_hud(img, {"doors": 3, "levers": 3, "pace": 2, "guards": 3,
                   "traps": 2, "chests": 2}, flash="guards")
    return img

MOCKS = {
    "v6h_normal.png": m_normal,
    "v6h_whisper.png": m_whisper,
    "v6h_rebuild.png": m_rebuild,
    "v6h_multi.png": m_multi,
    "v6h_late.png": m_late,
}
for name, fn in MOCKS.items():
    rows = fn()
    assert len(rows) == 240 and all(len(r) == 320 for r in rows)
    render_png(rows, os.path.join(IMG_OUT, name), scale=2)

# ---------------------------------------------------------------- icon fragment
lines = [
    "; hud_icons.s - V6 HUD memory-row icons (kimi/visual-refinement)",
    "; Six 8x8 bitmask icons, 8 bytes each, bit 7 = leftmost column.",
    "; Order: doors, levers, pace, guards, traps, chests.",
    "; Colour equates: lit + dim per category (VJ-verified).",
    "; NOT linked - Claude wires HUD state; Bob Checkpoint B only if the",
    "; renderer needs new protected buffers or OP changes.",
    "",
]
for name, lit, dim, _ in CATS:
    lines.append(f"HUD_{name.upper():<8}_LIT equ     ${lit:04X}")
    lines.append(f"HUD_{name.upper():<8}_DIM equ     ${dim:04X}")
lines += ["", "HUD_FLASH    equ     $77F1   ; STAR white intensify ring",
          "", "hud_icons:"]
for name, lit, dim, icon in CATS:
    vals = [int(r, 2) for r in icon]
    lines.append("        dc.b    " + ",".join(f"${v:02X}" for v in vals)
                 + f"   ; {name}")
with open(os.path.join(SPR_OUT, "hud_icons.s"), "w") as fh:
    fh.write("\n".join(lines) + "\n")

# ---------------------------------------------------------------- spec doc
doc = f"""# V6 HUD Memory-Row Spec — Castle Remembers (Jaguar)

Six-category memory HUD: **doors, levers, pace, guards, traps, chests/greed**.
Mockups: `v6h_normal/whisper/rebuild/multi/late.png`. Icons: `hud_icons.s`.
Content/mockup only — Claude wires category state; Bob Checkpoint B only if
the renderer needs new protected buffers or OP changes.

## Layout contract

- Row band **y = {HUD_Y}..239** (below the floor slab at row 194; never covers
  hero, enemies, doors, levers, ladders or holes).
- Six blocks, {BLOCK_W}px each, {GAP}px apart, centred (x0 = {X0}). Whole row = {ROW_W}px.
- Block: 8×8 icon at (x, y+2), three 3×3 pips at (x+10+4·n, y+4).
- Pressure 0–3: **0** = dim icon, all pips hollow · **1–3** = lit icon + n lit
  pips. The pips ARE the tier counter Claude already maintains.
- **Intensify**: when a category gains a tier, ring the newest pip in
  `HUD_FLASH` white for ~0.5 s, then settle. No numbers anywhere.

## Palette (VJ-verified; five reserved by Claude, chests proposed)

| Category | Lit | Dim | Icon |
|---|---|---|---|
| doors | `$F8FF` | `${CATS[0][2]:04X}` | arch door |
| levers | `$EAE7` | `${CATS[1][2]:04X}` | lever throw |
| pace | `$2BDD` | `${CATS[2][2]:04X}` | motion chevrons |
| guards | `$E2DD` | `${CATS[3][2]:04X}` | helm |
| traps | `$53C9` | `${CATS[4][2]:04X}` | spike teeth |
| chests | `$7CC4` | `$7C46` | clasped chest |

## Coexistence with the message band

- Whispers/titles draw at y 8–22 (top) — the HUD row never overlaps.
- Prompts draw above objects (y ≥ 130); the HUD row stays at the bottom.
- Rebuild/death/win screens may keep the row visible as a memory summary
  (see `v6h_rebuild.png`) — Claude's choice; the row is passive there.
- Subordinate to gameplay: 16 px tall, saturated colour only where a tier
  is active; dormant categories sit near-black.
"""
with open(os.path.join(DOC_OUT, "V6_HUD_MEMORY_ROW.md"), "w", encoding="utf-8") as fh:
    fh.write(doc)

print("mockups:", list(MOCKS))
print("icons:", os.path.join(SPR_OUT, "hud_icons.s"))
print("spec:", os.path.join(DOC_OUT, "V6_HUD_MEMORY_ROW.md"))
