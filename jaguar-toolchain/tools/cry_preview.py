# cry_preview.py — Castle Remembers visual milestone tool (kimi/visual-refinement)
#
# Milestone V0: in-place pixel-data redesign of the Gate 6 castle floor
# (320x8 CRY16, PIX_FLOOR, 5120 bytes) and enemy sprite (16x16 CRY16,
# PIX_ENEMY, 512 bytes). Same sizes, same addresses — no memory-map change.
#
# CRY16 -> RGB decode below is an APPROXIMATION for preview only:
#   bit15 C=0 -> grey(Y,Y,Y); C=1 -> (clamp(Y+(R-7.5)*16), Y, Y), R=bits14-11.
# It matches every proven on-screen anchor in the project ($CE7B stone,
# $3943/$3601 greys, $CFCB gold, $F001 dark red, $D96C/$DA7A skin).
# Final color judgment happens on hardware/emulator in Bob's runtime gate.

import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_OUT = os.path.join(HERE, "..", "..", "docs", "visual", "previews")
GEN_OUT = os.path.join(HERE, "gen")
os.makedirs(IMG_OUT, exist_ok=True)
os.makedirs(GEN_OUT, exist_ok=True)

# ---- palette (all values proven in gates 1-6 or intensity variants) -------
HI     = 0xCE9C   # top-edge highlight   ($CE7B + Y$21)
POLISH = 0xCE8E   # worn polished path   ($CE7B + Y$13)
BASE   = 0xCE7B   # proven floor stone
WARM   = 0xD27B   # warm sandstone variant — VERIFY-ON-SCREEN, fallback $CE7B
PIT    = 0xCE52   # wear pit / chip      ($CE7B - Y$29)
MORTAR = 0x3943   # proven mortar grey
GROOVE = 0x4238   # ground-down groove, darker warm-grey
STUD   = 0xF001   # proven deep red (iron fitting)
SHADOW = 0x3601   # proven near-black
BONE_L = 0xCE9C   # skull bone highlight
BONE_M = 0xCE7B   # skull bone mid
GOLD   = 0xCFCB   # proven gold (eye glow)
DKRED  = 0xF001   # socket / outline accent
OUTL   = 0x3601   # outline
TRANS  = 0x0000   # transparent (sprites only)

def cry(v):
    """Approximate CRY16 -> (r,g,b). None = transparent."""
    if v == 0x0000:
        return None
    y = v & 0xFF
    if (v >> 15) == 0:
        return (y, y, y)
    r = (v >> 11) & 0xF
    red = max(0, min(255, int(y + (r - 7.5) * 16)))
    return (red, y, y)

# ---- OLD data (as committed at gate6 baseline) -----------------------------
OLD_FLOOR_ROW = [BASE, BASE, BASE, MORTAR, BASE, BASE, MORTAR, SHADOW]

OLD_ENEMY_LW = [
    [0x00000000, 0x00000000, 0x00000000, 0x00000000],
    [0x00003601, 0x36013601, 0x36013601, 0x36010000],
    [0x00003601, 0xF001CFCB, 0xCFCBF001, 0x36010000],
    [0x36013601, 0xF001CFCB, 0xCFCBF001, 0x36013601],
    [0x36013601, 0x36013601, 0x36013601, 0x36013601],
    [0x36013601, 0xCFCB3601, 0x3601CFCB, 0x36013601],
    [0x36013601, 0x3601CFCB, 0xCFCB3601, 0x36013601],
    [0x00003601, 0x36013601, 0x36013601, 0x36010000],
    [0x00003601, 0x36013601, 0x36013601, 0x36010000],
    [0x36013601, 0x3601CFCB, 0xCFCB3601, 0x36013601],
    [0x36013601, 0xCFCB3601, 0x3601CFCB, 0x36013601],
    [0x36013601, 0x36013601, 0x36013601, 0x36013601],
    [0x00003601, 0x36013601, 0x36013601, 0x36010000],
    [0x00003601, 0x3601CFCB, 0xCFCB3601, 0x36010000],
    [0x00000000, 0x3601CFCB, 0xCFCB3601, 0x00000000],
    [0x00000000, 0x00003601, 0x36010000, 0x00000000],
]

def lw_to_px(row_lw):
    """Longwords -> 16 pixel values (hi word = left pixel)."""
    px = []
    for lw in row_lw:
        px.append((lw >> 16) & 0xFFFF)
        px.append(lw & 0xFFFF)
    return px

OLD_ENEMY = [lw_to_px(r) for r in OLD_ENEMY_LW]

# ---- NEW floor design (Gatehouse ashlar, 320x8) ----------------------------
# Overlap safety: PIX_ENEMY init overwrites floor bytes $1000-$11FF
# (row 6 px 256-319, row 7 px 0-127). Rows 6-7 stay uniform dark, as before.
def new_floor():
    f = [[BASE] * 320 for _ in range(8)]
    # row 0: highlight, worn polished path at spawn (px 56-103), chips
    f[0] = [HI] * 320
    for x in range(56, 104):
        f[0][x] = POLISH
    for x in (64, 65, 88, 89):
        f[0][x] = PIT
    # rows 1-2: ashlar course A, joints at x%16==15, warm tiles T3/T6/T9/T12
    warm_tiles = {3, 6, 9, 12}
    for r in (1, 2):
        for x in range(320):
            if x % 16 == 15:
                f[r][x] = MORTAR
            elif (x // 16) in warm_tiles:
                f[r][x] = WARM
    # row 3: mortar line with ground-down groove under spawn
    f[3] = [GROOVE if 72 <= x <= 87 else MORTAR for x in range(320)]
    # rows 4-5: ashlar course B (offset 8), joints at x%16==7
    for r in (4, 5):
        for x in range(320):
            if x % 16 == 7:
                f[r][x] = MORTAR
    # row 5 wear pits around spawn + one iron stud
    for span in ((62, 64), (79, 81), (95, 97)):
        for x in range(span[0], span[1] + 1):
            f[5][x] = PIT
    f[5][90] = STUD
    f[5][91] = STUD
    # row 6: uniform mortar (overlap zone begins mid-row; keep flat)
    f[6] = [MORTAR] * 320
    # row 7: uniform shadow
    f[7] = [SHADOW] * 320
    return f

# ---- NEW enemy design (Sentinel Skull refined, 16x16) ----------------------
# .=transparent O=outline b=bone-mid B=bone-light G=gold-eye R=dark-red
NEW_ENEMY_MAP = [
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
]
ECHAR = {".": TRANS, "O": OUTL, "b": BONE_M, "B": BONE_L, "G": GOLD, "R": DKRED}
NEW_ENEMY = [[ECHAR[c] for c in row] for row in NEW_ENEMY_MAP]
for row in NEW_ENEMY:
    assert len(row) == 16, "enemy row not 16 px"

# ---- render helpers ---------------------------------------------------------
BG = (14, 14, 20)

def render(px_rows, scale):
    h, w = len(px_rows), len(px_rows[0])
    img = Image.new("RGB", (w * scale, h * scale), BG)
    d = ImageDraw.Draw(img)
    for y, row in enumerate(px_rows):
        for x, v in enumerate(row):
            c = cry(v)
            if c is None:
                continue
            d.rectangle([x * scale, y * scale, (x + 1) * scale - 1,
                         (y + 1) * scale - 1], fill=c)
    return img

def with_label(img, label):
    out = Image.new("RGB", (img.width, img.height + 18), BG)
    out.paste(img, (0, 18))
    ImageDraw.Draw(out).text((4, 3), label, fill=(200, 200, 200))
    return out

# floor before/after stacked
old_floor = [[v] * 320 for v in OLD_FLOOR_ROW]
fl_before = with_label(render(old_floor, 4), "BEFORE — gate6 baseline (uniform courses)")
fl_after = with_label(render(new_floor(), 4), "AFTER — V0 Gatehouse ashlar (warm, worn, spawn path)")
combo = Image.new("RGB", (fl_before.width, fl_before.height + fl_after.height + 8), BG)
combo.paste(fl_before, (0, 0))
combo.paste(fl_after, (0, fl_before.height + 8))
combo.save(os.path.join(IMG_OUT, "v0_floor_before_after.png"))

# enemy before/after side by side
en_before = with_label(render(OLD_ENEMY, 14), "BEFORE — gate6 skull")
en_after = with_label(render(NEW_ENEMY, 14), "AFTER — V0 Sentinel Skull")
combo2 = Image.new("RGB", (en_before.width + en_after.width + 12,
                           max(en_before.height, en_after.height)), BG)
combo2.paste(en_before, (0, 0))
combo2.paste(en_after, (en_before.width + 12, 0))
combo2.save(os.path.join(IMG_OUT, "v0_enemy_before_after.png"))

# ---- emit .s data blocks ----------------------------------------------------
def pack_lw(row):
    return [(row[i] << 16) | row[i + 1] for i in range(0, len(row), 2)]

def emit_floor(path, f):
    with open(path, "w") as fh:
        for r, row in enumerate(f):
            fh.write(f"; row {r}\n")
            lws = pack_lw(row)
            for i in range(0, len(lws), 8):
                chunk = ",".join(f"${v:08X}" for v in lws[i:i + 8])
                fh.write(f"        dc.l    {chunk}\n")

def emit_enemy(path, e):
    with open(path, "w") as fh:
        for r, row in enumerate(e):
            lws = pack_lw(row)
            fh.write(f"        dc.l    {','.join(f'${v:08X}' for v in lws)}  ; row {r:02d}\n")

emit_floor(os.path.join(GEN_OUT, "floor_block.txt"), new_floor())
emit_enemy(os.path.join(GEN_OUT, "enemy_block.txt"), NEW_ENEMY)

# ---- console verification ---------------------------------------------------
print("NEW ENEMY (ASCII):")
for row in NEW_ENEMY_MAP:
    print("  " + row)
sizes = os.path.getsize(os.path.join(GEN_OUT, "floor_block.txt"))
print(f"\nfloor_block.txt bytes={sizes}")
print("enemy rows:", len(NEW_ENEMY), " floor rows:", len(new_floor()))
print("previews written to", os.path.abspath(IMG_OUT))
