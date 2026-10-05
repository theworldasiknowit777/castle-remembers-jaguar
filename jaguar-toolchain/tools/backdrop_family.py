# backdrop_family.py — Castle Remembers five-floor environment bands
# (kimi/visual-refinement)
#
# Generates the F1-F5 320x180 wall backdrop art assets per
# docs/visual/V2_ENVIRONMENT_BAND_SPEC.md. Art assets only:
# NOT linked into the game — runtime integration (new OP BITMAP object,
# Zone B address, per-floor pointer switch) is Bob Checkpoint C + Claude.
#
# Each floor is a full 320x180 16-bit CRY bitmap (opaque; rows 0-179).
# Preview PNGs render with VJ-accurate colours via kpalette.py.
#
# Output:
#   docs/visual/previews/v2_band_f1..f5.png  (2x previews)
#   docs/visual/previews/v2_bands.png        (contact sheet, all five)
#   docs/visual/bands/img_band_f1..f5.s      (dc.w fragments, drop-in data)

import os
import random
from PIL import Image, ImageDraw

from kpalette import PAL, cry_to_rgb

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_OUT = os.path.join(HERE, "..", "..", "docs", "visual", "previews")
BAND_OUT = os.path.join(HERE, "..", "..", "docs", "visual", "bands")
os.makedirs(IMG_OUT, exist_ok=True)
os.makedirs(BAND_OUT, exist_ok=True)

W, H = 320, 180

# ---------------------------------------------------------------- helpers

def new_img(fill):
    return [[fill] * W for _ in range(H)]

def px(img, x, y, c):
    if 0 <= x < W and 0 <= y < H:
        img[y][x] = c

def rect(img, x0, y0, x1, y1, c):
    for y in range(max(0, y0), min(H, y1 + 1)):
        for x in range(max(0, x0), min(W, x1 + 1)):
            img[y][x] = c

def ashlar(img, fam, rng, wear=0.0, y0=0, y1=H - 1):
    """Block courses 16x8, 1px mortar, staggered. fam = (mid, light, dark)."""
    mid, light, dark = fam
    rect(img, 0, y0, W - 1, y1, PAL["MORTAR"])
    course = 0
    y = y0
    while y <= y1:
        off = 8 if course % 2 else 0
        x = -16 + off
        while x < W:
            bx0, bx1 = x + 1, min(x + 14, W - 1)
            by0, by1 = y + 1, min(y + 6, y1)
            face = mid
            r = rng.random()
            if r < 0.12:
                face = light
            elif r < 0.24:
                face = dark
            rect(img, bx0, by0, bx1, by1, face)
            for xx in range(bx0, bx1 + 1):          # top highlight
                px(img, xx, by0, light)
            for xx in range(bx0, bx1 + 1):          # bottom shadow
                px(img, xx, by1, dark)
            for yy in range(by0, by1 + 1):          # left hi / right sh
                px(img, bx0, yy, light)
                px(img, bx1, yy, dark)
            x += 16
        y += 8
        course += 1
    # wear: random pitting
    n = int(W * (y1 - y0) * wear / 24)
    for _ in range(n):
        px(img, rng.randrange(W), rng.randrange(y0, y1 + 1), dark)

def crack(img, x, y, length, rng, c=None):
    c = c if c is not None else PAL["SHADOW"]
    for _ in range(length):
        px(img, x, y, c)
        x += rng.choice((-1, 0, 0, 1))
        y += rng.choice((0, 0, 1))

def arch_recess(img, cx, ytop, half_w, ybot, recess_c, lip_c):
    """Round arch recess: lip ring then darker interior."""
    r = half_w
    for dy in range(-r, 1):
        dx = int((r * r - dy * dy) ** 0.5)
        for x in (cx - dx, cx + dx):
            px(img, x, ytop + r + dy, lip_c)
    rect(img, cx - half_w, ytop + r, cx - half_w, ybot, lip_c)
    rect(img, cx + half_w, ytop + r, cx + half_w, ybot, lip_c)
    for dy in range(-r + 1, 1):
        dx = int(((r - 1) ** 2 - dy * dy) ** 0.5)
        rect(img, cx - dx, ytop + r + dy, cx + dx, ytop + r + dy, recess_c)
    rect(img, cx - half_w + 1, ytop + r + 1, cx + half_w - 1, ybot, recess_c)

def banner(img, x, y0, wdt, ylen, torn=False, bg=None):
    """Hanging banner: rod, red field, gold trim, pointed (or torn) hem."""
    rect(img, x - 1, y0, x + wdt, y0, PAL["WOOD_D"])            # rod
    bg = bg if bg is not None else PAL["MORTAR"]
    body = PAL["BANNER_D"] if torn else PAL["BANNER"]
    trim = PAL["BANNER_D"] if torn else PAL["GOLDTRIM"]
    yend = y0 + ylen
    rect(img, x, y0 + 1, x + wdt - 1, yend, body)
    rect(img, x, y0 + 1, x, yend, trim)
    rect(img, x + wdt - 1, y0 + 1, x + wdt - 1, yend, trim)
    rect(img, x, y0 + 1, x + wdt - 1, y0 + 2, trim)
    if torn:
        for i in range(wdt):
            if i % 3 == 1:
                rect(img, x + i, yend - 3 - (i % 4), x + i, yend, bg)
    else:
        mid = x + wdt // 2
        for i in range(wdt // 2):
            rect(img, x + i, yend - (wdt // 2 - i), x + i, yend, bg)
            rect(img, x + wdt - 1 - i, yend - (wdt // 2 - i),
                 x + wdt - 1 - i, yend, bg)
        px(img, mid, yend, trim)

def torch(img, x, y, lit=True):
    """Wall sconce: bracket + flame (or dead ember) + ash smudge above."""
    rect(img, x - 1, y, x + 1, y + 5, PAL["IRON_D"])            # bracket
    rect(img, x - 2, y + 4, x + 2, y + 5, PAL["IRON_D"])
    if lit:
        px(img, x, y - 1, PAL["FLAME_Y"])
        rect(img, x - 1, y - 3, x + 1, y - 2, PAL["FLAME_O"])
        px(img, x, y - 4, PAL["FLAME_O"])
        px(img, x, y - 5, PAL["EMBER"])
        rect(img, x - 1, y - 8, x + 1, y - 7, PAL["ASH"])       # smudge
    else:
        px(img, x, y - 1, PAL["EMBER"])
        rect(img, x - 1, y - 8, x + 1, y - 7, PAL["ASH"])

def window_barred(img, x, y, wdt=12, hgt=20, bricked=False, fam=None):
    """Small barred night window with stone lip; or bricked-up infill."""
    lip_l, lip_d = (fam[1], fam[2]) if fam else (PAL["WARM_L"], PAL["WARM_D"])
    rect(img, x - 1, y - 1, x + wdt, y + hgt, lip_l)
    if bricked:
        rect(img, x, y, x + wdt - 1, y + hgt - 1, lip_d)
        for yy in range(y, y + hgt, 4):                          # infill courses
            rect(img, x, yy, x + wdt - 1, yy, PAL["MORTAR"])
        return
    rect(img, x, y, x + wdt - 1, y + hgt - 1, PAL["NIGHT"])
    rect(img, x + wdt // 3, y, x + wdt // 3, y + hgt - 1, PAL["BLACK"])
    rect(img, x + 2 * wdt // 3, y, x + 2 * wdt // 3, y + hgt - 1, PAL["BLACK"])
    rect(img, x, y + hgt // 2, x + wdt - 1, y + hgt // 2, PAL["BLACK"])

def niche(img, cx, ytop, bound=False, tell=0):
    """Lever niche: small arch recess, iron bracket; optional crack tells."""
    arch_recess(img, cx, ytop, 8, ytop + 26, PAL["SHADOW"], PAL["MORTAR"])
    rect(img, cx - 2, ytop + 20, cx + 2, ytop + 24, PAL["IRON_D"])
    if bound:
        rect(img, cx - 8, ytop + 12, cx + 8, ytop + 13, PAL["IRON_D"])
    for i in range(tell):
        crack(img, cx - 6 + 12 * i, ytop + 2, 5, random.Random(40 + i))

def moss(img, rng, n, y0=150, y1=179):
    for _ in range(n):
        x, y = rng.randrange(W), rng.randrange(y0, y1)
        rect(img, x, y, x + rng.randrange(1, 3), y, PAL["MOSS"])

def debris(img, rng, n, y0=168, y1=179, c=None):
    c = c if c is not None else PAL["BONE"]
    for _ in range(n):
        x, y = rng.randrange(W), rng.randrange(y0, y1)
        px(img, x, y, c)
        if rng.random() < 0.5:
            px(img, x + 1, y, c)

def shaft(img, x, dark_c):
    """Subtle vertical darkening behind a 16px ladder strip."""
    for y in range(H):
        for xx in (x - 1, x + 16):
            px(img, xx, y, dark_c)

# 3x5 carving font (easter egg)
FONT = {
    "A": ["010", "101", "111", "101", "101"],
    "B": ["110", "101", "110", "101", "110"],
    "C": ["011", "100", "100", "100", "011"],
    "H": ["101", "101", "111", "101", "101"],
    "I": ["111", "010", "010", "010", "111"],
    "K": ["101", "101", "110", "101", "101"],
    "M": ["101", "111", "111", "101", "101"],
    "N": ["101", "111", "111", "111", "101"],
    "O": ["010", "101", "101", "101", "010"],
    "T": ["111", "010", "010", "010", "010"],
    "V": ["101", "101", "101", "101", "010"],
    "X": ["101", "101", "010", "101", "101"],
    "2": ["110", "001", "010", "100", "111"],
    "0": ["111", "101", "101", "101", "111"],
    "6": ["011", "100", "111", "101", "111"],
    " ": ["000", "000", "000", "000", "000"],
}

def carve(img, text, x, y, cut_c, lip_c, rng):
    """Weathered chiselled inscription: cut pixels + light lip above-left."""
    cx = x
    for ch in text:
        glyph = FONT[ch]
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    if rng.random() < 0.06:       # weathering loss
                        continue
                    px(img, cx + gx, y + gy, cut_c)
                    if lip_c is not None:
                        px(img, cx + gx, y + gy - 1, lip_c)
        cx += 4

# ---------------------------------------------------------------- floors
WARM = (PAL["WARM_M"], PAL["WARM_L"], PAL["WARM_D"])
COOL = (PAL["COOL_M"], PAL["COOL_L"], PAL["COOL_D"])
PALE = (PAL["PALE_M"], PAL["PALE_L"], PAL["PALE_D"])
SOLE = (PAL["SOLE_M"], PAL["SOLE_L"], PAL["SOLE_D"])

def floor1():
    rng = random.Random(1)
    img = new_img(PAL["WARM_M"])
    ashlar(img, WARM, rng, wear=0.5)
    window_barred(img, 66, 16, fam=WARM)
    window_barred(img, 240, 16, fam=WARM)
    arch_recess(img, 98, 128, 12, 179, PAL["WARM_D"], PAL["WARM_L"])    # door L
    arch_recess(img, 222, 128, 12, 179, PAL["WARM_D"], PAL["WARM_L"])   # door R
    banner(img, 120, 58, 12, 52, bg=PAL["WARM_M"])
    banner(img, 188, 58, 12, 52, bg=PAL["WARM_M"])
    torch(img, 72, 130)
    torch(img, 248, 130)
    shaft(img, 6, PAL["WARM_D"])
    shaft(img, 298, PAL["WARM_D"])
    carve(img, "IBM HACKATHON MMXXVI", 122, 42, PAL["SHADOW"],
          None, rng)                                            # easter egg
    crack(img, 40, 96, 14, rng)
    crack(img, 282, 60, 10, rng)
    moss(img, rng, 90)
    debris(img, rng, 40)
    return img

def floor2():
    rng = random.Random(2)
    img = new_img(PAL["COOL_M"])
    ashlar(img, COOL, rng, wear=0.3)
    # colonnade: three open arches with night sky
    for cx in (60, 160, 260):
        arch_recess(img, cx, 6, 18, 62, PAL["NIGHT"], PAL["COOL_L"])
    # moon in the right arch
    for dy in range(-5, 6):
        for dx in range(-5, 6):
            if dx * dx + dy * dy <= 25:
                px(img, 260 + dx, 24 + dy, PAL["MOON"])
    px(img, 52, 20, PAL["STAR"]); px(img, 70, 34, PAL["STAR"])
    px(img, 150, 18, PAL["STAR"]); px(img, 172, 40, PAL["STAR"])
    # missing blocks at arch tops (weathering)
    rect(img, 48, 6, 54, 10, PAL["NIGHT"])
    rect(img, 150, 6, 154, 8, PAL["NIGHT"])
    # gate shaft recess above centre ladder
    rect(img, 148, 48, 172, 110, PAL["COOL_D"])
    rect(img, 146, 48, 147, 179, PAL["IRON_D"])
    rect(img, 173, 48, 174, 179, PAL["IRON_D"])
    # lever niches
    niche(img, 84, 132)
    niche(img, 236, 132)
    # torn banner scrap, left only
    banner(img, 28, 66, 10, 30, torn=True, bg=PAL["COOL_M"])
    shaft(img, 6, PAL["COOL_D"])
    shaft(img, 298, PAL["COOL_D"])
    moss(img, rng, 25)
    debris(img, rng, 25)
    return img

def floor3():
    rng = random.Random(3)
    img = new_img(PAL["WARM_M"])
    ashlar(img, WARM, rng, wear=0.9)
    # F1 echo: same windows, but the left one bricked up
    window_barred(img, 66, 16, fam=WARM, bricked=True)
    window_barred(img, 240, 16, fam=WARM)
    # door arches; left one damaged (jagged top bite)
    arch_recess(img, 98, 128, 12, 179, PAL["WARM_D"], PAL["WARM_L"])
    arch_recess(img, 222, 128, 12, 179, PAL["WARM_D"], PAL["WARM_L"])
    rect(img, 92, 128, 104, 136, PAL["SHADOW"])
    debris(img, rng, 14, y0=140, y1=150)
    # tattered banners, one dead torch
    banner(img, 120, 58, 12, 30, torn=True, bg=PAL["WARM_M"])
    banner(img, 188, 58, 12, 22, torn=True, bg=PAL["WARM_M"])
    torch(img, 72, 130, lit=False)
    torch(img, 248, 130)
    shaft(img, 6, PAL["WARM_D"])
    shaft(img, 298, PAL["WARM_D"])
    # heavier cracks; clusters radiating from the spike corridors (55, 249)
    for x0 in (52, 60, 246, 253):
        crack(img, x0, 168, 12, rng)
    crack(img, 150, 30, 18, rng)
    crack(img, 200, 90, 12, rng)
    debris(img, rng, 30, c=PAL["BONE"])
    moss(img, rng, 40)
    return img

def floor4():
    rng = random.Random(4)
    img = new_img(PAL["SOLE_M"])
    ashlar(img, SOLE, rng, wear=0.15)
    # vault ribs converging toward the centre
    for x0 in (0, 60, 120, 200, 260, 319):
        steps = 60
        for i in range(steps):
            x = x0 + (160 - x0) * i // steps
            y = i
            rect(img, x, y, x + 1, y + 1, PAL["SOLE_D"])
    # heavy columns flanking the gate shaft
    for cx in (134, 178):
        rect(img, cx, 48, cx + 7, 179, PAL["SOLE_D"])
        rect(img, cx + 1, 48, cx + 1, 179, PAL["SOLE_L"])
        rect(img, cx - 2, 44, cx + 9, 47, PAL["SOLE_L"])     # capital
    rect(img, 148, 48, 172, 110, PAL["SOLE_D"])
    rect(img, 146, 48, 147, 179, PAL["IRON_D"])
    rect(img, 173, 48, 174, 179, PAL["IRON_D"])
    # iron-bound lever niches with escalated tells
    niche(img, 84, 132, bound=True, tell=2)
    niche(img, 236, 132, bound=True, tell=2)
    # ember pre-glow near niches
    for x in (76, 92, 228, 244):
        px(img, x, 166, PAL["EMBER"])
        px(img, x + 2, 168, PAL["EMBER"])
    shaft(img, 6, PAL["SOLE_D"])
    shaft(img, 298, PAL["SOLE_D"])
    debris(img, rng, 12, c=PAL["ASH"])
    return img

def floor5():
    rng = random.Random(5)
    img = new_img(PAL["PALE_M"])
    # sky rows 0-99: dawn gradient, brighter toward the exit side (right)
    for y in range(100):
        t = y / 99.0
        base = PAL["DAWN_HI"] if t < 0.45 else (PAL["NIGHT"] if t < 0.6
              else PAL["DAWN_LO"])
        rect(img, 0, y, W - 1, y, base)
    for y in range(70, 100):                                   # glow near exit
        for x in range(200, W):
            if (x - 277) ** 2 + (y - 100) ** 2 < 60 ** 2:
                img[y][x] = PAL["DAWN_GL"] if (x - 277) ** 2 + (y - 100) ** 2 < 30 ** 2 else PAL["DAWN_LO"]
    for _ in range(40):                                        # stars, left/top
        x, y = rng.randrange(0, 190), rng.randrange(2, 44)
        px(img, x, y, PAL["STAR"])
    # battlement wall with crenellations
    ashlar(img, PALE, rng, wear=0.4, y0=100, y1=179)
    y = 96
    x = 0
    while x < W:                                               # merlons
        if not (272 <= x <= 296):                              # broken over exit
            rect(img, x, y - 16, x + 13, y, PALE[2])
            rect(img, x, y - 16, x + 13, y - 15, PALE[1])
        x += 28
    rect(img, 272, 92, 282, 96, PALE[2])                       # broken stump
    # exit arch emphasis (x=277): recess + pale lip + glow spill
    arch_recess(img, 293, 130, 18, 179, PAL["DAWN_GL"], PAL["PALE_L"])
    # wraith patrol region (180-261) stays plain — already flat ashlar
    shaft(img, 6, PAL["PALE_D"])
    shaft(img, 298, PAL["PALE_D"])
    debris(img, rng, 25, c=PAL["ASH"])
    return img

FLOORS = {
    "img_band_f1": floor1,
    "img_band_f2": floor2,
    "img_band_f3": floor3,
    "img_band_f4": floor4,
    "img_band_f5": floor5,
}

# ---------------------------------------------------------------- output
def render(rows, scale):
    img = Image.new("RGB", (W * scale, H * scale))
    d = ImageDraw.Draw(img)
    for y, row in enumerate(rows):
        for x, w in enumerate(row):
            d.rectangle([x * scale, y * scale, (x + 1) * scale - 1,
                         (y + 1) * scale - 1], fill=cry_to_rgb(w))
    return img

contact = Image.new("RGB", (W + 16, 5 * (H + 22)), (14, 14, 20))
dc = ImageDraw.Draw(contact)
for i, (name, fn) in enumerate(FLOORS.items()):
    rows = fn()
    assert len(rows) == H and all(len(r) == W for r in rows), name
    assert all(w != 0x0000 for row in rows for w in row), f"{name}: transparent pixel"
    prev = render(rows, 2)
    prev.save(os.path.join(IMG_OUT, f"v2_band_f{i + 1}.png"))
    dc.text((8, i * (H + 22) + 4), name.upper(), fill=(220, 210, 180))
    contact.paste(render(rows, 1), (8, i * (H + 22) + 18))
    # fragment
    vals = [w for row in rows for w in row]
    lines = [
        f"; {name} — 320x180 CRY16 wall backdrop (kimi/visual-refinement)",
        f"; Per docs/visual/V2_ENVIRONMENT_BAND_SPEC.md. Opaque (no TRANS).",
        f"; NOT linked — runtime integration is Bob Checkpoint C + Claude.",
        f"{name}:",
    ]
    for j in range(0, len(vals), 8):
        lines.append("        dc.w    " + ",".join(f"${v:04X}" for v in vals[j:j + 8]))
    with open(os.path.join(BAND_OUT, f"{name}.s"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
contact.save(os.path.join(IMG_OUT, "v2_bands.png"))

print("previews:", os.path.join(IMG_OUT, "v2_band_f1..f5.png"), "+ v2_bands.png")
print("fragments:", os.path.abspath(BAND_OUT))
