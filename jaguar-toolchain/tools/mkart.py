"""mkart.py - generate castle_art.inc (CRY16 bitmaps for RMAC) from ASCII maps.

Placeholder art for the five-floor build. Every image is an ASCII map drawn
with the palette letters below; '.' is colour 0 (transparent when the object
has TRANS set). Widths must be multiples of 4 pixels (one OP phrase at 16bpp).

Bob's original hero, skull and floor bitmaps are copied byte-for-byte from
gate6_castle/gate6_castle.s so the authentic hero is unchanged.

Run:  python tools/mkart.py   (from jaguar-toolchain/)
Out:  gate7_castle/castle_art.inc
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from jagsim import rgb_to_cry  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PALETTE_RGB = {
    "W": (120, 70, 30),     # wood
    "w": (70, 40, 15),      # dark wood
    "I": (110, 110, 120),   # iron
    "i": (50, 50, 60),      # dark iron
    "R": (220, 30, 20),     # red
    "D": (110, 15, 10),     # dark red
    "O": (255, 140, 0),     # orange
    "Y": (255, 230, 60),    # yellow
    "G": (230, 180, 40),    # gold
    "K": (190, 100, 45),    # copper (trapped-lever tell)
    "B": (225, 215, 190),   # bone
    "S": (130, 125, 115),   # stone
    "s": (70, 66, 60),      # dark stone
    "H": (240, 240, 240),   # white
    "P": (140, 60, 200),    # purple
    "V": (170, 200, 255),   # ghost blue
    "C": (60, 200, 220),    # cyan
    "k": (25, 25, 30),      # near black (not transparent)
}
PALETTE = {k: rgb_to_cry(v) for k, v in PALETTE_RGB.items()}
PALETTE["."] = 0

IMAGES = {}


def img(name, rows):
    rows = [r for r in rows.strip("\n").split("\n")]
    rows = [r.strip() for r in rows]
    w = len(rows[0])
    assert all(len(r) == w for r in rows), (name, [len(r) for r in rows])
    assert w % 4 == 0, (name, w)
    IMAGES[name] = rows


# ---------------------------------------------------------------- doors 8x40
door = []
for y in range(40):
    if y in (0, 39):
        door.append("iiiiiiii")
    elif y in (6, 20, 33):
        door.append("iIIIIIIi")
    elif y == 22:
        door.append("iWwWwGwi")
    else:
        door.append("iWwWwWwi" if y % 2 else "iwWwWwWi")
img("door_closed", "\n".join(door))
img("door_open", "\n".join(["iiiiiiii"] + ["i......i"] * 38 + ["iiiiiiii"]))
brick = []
for y in range(40):
    if y % 5 == 0:
        brick.append("ssssssss")
    else:
        brick.append("SSSsSSSS" if (y // 5) % 2 else "SsSSSSsS")
img("door_brick", "\n".join(brick))

# ---------------------------------------------------------------- gate 16x32
gate = []
for y in range(32):
    if y in (3, 15, 27):
        gate.append("IIIIIIIIIIIIIIII")
    elif y == 31:
        gate.append(".i...i...i...i..")
    else:
        gate.append(".I...I...I...I..".replace(".I.", ".I."))
img("gate", "\n".join(gate))

# ---------------------------------------------------------------- levers 8x12
img("lever_idle", """
GG......
GGI.....
..I.....
...I....
....I...
.....I..
......I.
......I.
..ssss..
.SSSSSS.
SSSSSSSS
ssssssss
""")
img("lever_tell", """
KK......
KKI.....
..I.....
...I....
....I...
.....I..
......I.
......I.
..ssss..
.SSSSSS.
SSSSSSSS
ssssssss
""")
img("lever_pulled", """
........
........
........
........
........
........
...IIIGG
.IIIIIGG
..ssss..
.SSSSSS.
SSSSSSSS
ssssssss
""")
img("lever_sprung", """
........
........
...R....
....R...
.....I..
......I.
......I.
......I.
..ssss..
.SSRSSS.
SSSSSSSS
ssssssss
""")

# ---------------------------------------------------------------- spikes 16x8 / 24x8
img("spike16", """
.R...R...R...R..
.H...H...H...H..
.I...I...I...I..
III.III.III.III.
III.III.III.III.
IIiIIIiIIIiIIIi.
ssssssssssssssss
ssssssssssssssss
""")
img("spike24", """
.R...R...R...R...R...R..
.H...H...H...H...H...H..
.I...I...I...I...I...I..
III.III.III.III.III.III.
III.III.III.III.III.III.
IIiIIIiIIIiIIIiIIIiIIIi.
ssssssssssssssssssssssss
ssssssssssssssssssssssss
""")

# ---------------------------------------------------------------- exit arch 32x48
exit_rows = []
for y in range(48):
    if y < 12:
        # rounded top: half-width grows toward the bottom of the arch
        half = [6, 9, 11, 12, 13, 14, 14, 15, 15, 16, 16, 16][y]
        row = ""
        for x in range(32):
            d = abs(x - 15.5)
            if d > half:
                row += "."
            elif d > half - 3:
                row += "G"
            else:
                row += "Y" if d < half - 6 else "H"
        exit_rows.append(row)
    else:
        exit_rows.append("GGGH" + ("YYYYYYYYYYYYYYYYYYYYYYYY" if y < 44 else "OOOOOOOOOOOOOOOOOOOOOOOO") + "HGGG")
img("exit", "\n".join(exit_rows))

# ---------------------------------------------------------------- eruption 64x16
flame = []
pattern = ["..Y.....O..Y......Y..O....Y.....", "..YO...OO.YY.....YYOOO...YY....O"]
for y in range(16):
    if y < 4:
        base = ("...Y.......O.......Y........O..." * 2)
        flame.append("".join(c if (x + y) % 3 else "." for x, c in enumerate(base)))
    elif y < 10:
        flame.append(("OYOROYOOROYOOYOROYOOROYOOYORROYO" * 2))
    elif y < 14:
        flame.append(("RORRORRROROORRRRORROROORRROROORR" * 2))
    else:
        flame.append(("DRDDRDDRDRDDRDDRDDRDRDDRDRDDRDDD" * 2))
img("flame", "\n".join(flame))

# ---------------------------------------------------------------- enemies 16x24
img("guard", """
.......RR.......
......RRR.......
.....IIIIII.....
....IIIIIIII....
....IkIkkIkI....
....IIBBBBII....
.....IBBBBI.....
......IIII......
...iIIIIIIIIi...
..iIIIIIIIIIIi..
..iI.IIIIII.Ii..
..WI.IIRRII.IW..
..WI.IIRRII.IW..
..W..IIIIII..W..
..W..iiiiii..W..
.....IIiiII.....
.....II..II.....
.....II..II.....
.....II..II.....
.....Ii..iI.....
.....Ii..iI.....
.....ii..ii.....
....iii..iii....
....kkk..kkk....
""")
img("heavy", """
......RRRR......
.....RRRRR......
....iiiiiiii....
...iIIIIIIIIi...
...iIkIkkIkIi...
...iIIBBBBIIi...
....iIBBBBIi....
.....iIIIIi.....
.SSiIIIIIIIIIi..
SSSSIIIIIIIIIIi.
SSsSIIIIIIIIIIi.
SsRsIIIRRIIIIIW.
SsRsIIIRRIIIIIW.
SSsSIIIIIIIIIIW.
.SSSiiiiiiiiiiW.
....iIIIiiIIIi..
....iII....IIi..
....iII....IIi..
....iII....IIi..
....iIi....iIi..
....iIi....iIi..
....iii....iii..
...iiii....iiii.
...kkkk....kkkk.
""")
img("watcher", """
.....ssssss.....
....sSSSSSSs....
....SSSSSSSS....
....SRRSSRRS....
....SSSSSSSS....
.....SSkkSS.....
......SSSS......
..W.ssSSSSss....
..WsSSSSSSSSs...
.W.SSSSSSSSSSs..
.W.SSsSSSSsSSs..
.W.SS.SSSS.SS...
.WIIIIIIIIIIH...
.W.SS.SSSS.SS...
.W.SSsSSSSsSS...
..WsSSSSSSSSs...
..W.SSSSSSSS....
....SSS..SSS....
....SSS..SSS....
....SSS..SSS....
....SSS..SSS....
...sSSs..sSSs...
..ssssssssssss..
..ssssssssssss..
""")
img("wraith", """
......VVVV......
.....VPPPPV.....
....VPPPPPPV....
....PPkPPkPP....
....PYYPPYYP....
....PPPPPPPP....
.....PPkkPP.....
....VPPPPPPV....
...VPPPPPPPPV...
..VPPPPPPPPPPV..
..PPPPPPPPPPPP..
.VPP.PPPPPP.PPV.
.PP..PPPPPP..PP.
.P...PPPPPP...P.
.....PPPPPP.....
....PPPPPPPP....
....PPPPPPPP....
...PPPPPPPPPP...
...PPPPPPPPPP...
..PPPPP.PPPPPP..
..PPP.PP.PP.PP..
..PP..P..P..PP..
..P...P..P...P..
.....P....P.....
""")
img("arrow_r", """
.......H
WWWWWWII
""")
img("arrow_l", """
H.......
IIWWWWWW
""")


# ---------------------------------------------------------------- chests 16x12
img("chest_closed", """
................
..wwwwwwwwwwww..
.wWWWWWWWWWWWWw.
.wWWWWWWWWWWWWw.
.iiiiiiGGiiiiii.
.wWWWWWGGWWWWWw.
.wWWWWWWWWWWWWw.
.wWWWWWWWWWWWWw.
.iiiiiiiiiiiiii.
.wWWWWWWWWWWWWw.
.wwwwwwwwwwwwww.
................
""")
img("chest_trap", """
................
..wwwwwwwwwwww..
.wWWWWWWWWWWWWw.
.wWWWWWWWWWWWWw.
.iiiiiiRRiiiiii.
.wWWWWWRRWWWWWw.
.wWWWWWWWWWWWWw.
.wWWWWWWWWWWWWw.
.iiiiiiiiiiiiii.
.wWWWWWWWWWWWWw.
.wwwwwwwwwwwwww.
................
""")
img("chest_open", """
..wwwwwwwwwwww..
.wWWWWWWWWWWWWw.
.wwwwwwwwwwwwww.
................
.iiiiiiiiiiiiii.
.wkkkkkkkkkkkkw.
.wkkkkkkkkkkkkw.
.wWWWWWWWWWWWWw.
.iiiiiiiiiiiiii.
.wWWWWWWWWWWWWw.
.wwwwwwwwwwwwww.
................
""")
# ---------------------------------------------------------------- memory shard 8x8
img("shard", """
...HH...
..HCCH..
.HCCCCH.
HCCHCCCH
HCCCCCCH
.HCCCCH.
..HCCH..
...HH...
""")
# ---------------------------------------------------------------- falling masonry 16x16
img("block", """
.......ii.......
.......Ii.......
ssssssssssssssss
sSSSSSSSsSSSSSSs
sSSSSSSSsSSSSSSs
sSSSSSSSsSSSSSSs
ssssssssssssssss
sSSSsSSSSSSSsSSs
sSSSsSSSSkSSsSSs
sSSSsSSSkSSSsSSs
ssssssssssssssss
sSSSSSSkSsSSSSSs
sSSSSSSSSsSSSSSs
.ssssssssssssss.
..s..s..s..s..s.
................
""")
# ---------------------------------------------------------------- swinging blade 16x16
img("blade", """
.......ii.......
.......ii.......
.......ii.......
.......ii.......
.......ii.......
.......ii.......
......iIIi......
.....iIIIIi.....
...HIIIIIIIIH...
..HIIIIIIIIIIH..
.HIIIIIIIIIIIIH.
.HII........IIH.
.HI..........IH.
.H............H.
................
................
""")
# ---------------------------------------------------------------- castle hound 16x16
img("hound", """
................
................
................
................
..........ss....
.........sSSs...
.........sSRSs..
sssssssssSSSSSS.
sSSSSSSSSSSSs...
.sSSSSSSSSSSs...
..sSSSSSSSSSs...
..sSs....sSs....
..sS.....sS.....
..sS.....sS.....
..ss.....ss.....
................
""")

def ladder(lines=244, rail="W", rung="w"):
    rows = []
    for y in range(lines):
        rows.append((".%s%s..........%s%s." % (rail, rail, rail, rail)) if y % 6
                    else (".%s%s%s%s." % (rail, rail, rung * 10, rail * 2)))
    return rows


IMAGES["ladder"] = ladder()
IMAGES["ladder_gold"] = ladder(rail="G", rung="Y")      # the long ladder (canon: drawn gold)


# ---------------------------------------------------------------- Bob's verbatim art
def bob_block(src, label):
    lines = src.split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith(label + ":"))
    out = []
    for l in lines[start + 1:]:
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*:", l) or re.match(r"^\.end(\s|$)", l.strip()):
            break
        if l.strip().startswith(";") and out and not out[-1].strip():
            continue
        out.append(l)
    while out and (not out[-1].strip() or out[-1].strip().startswith(";")):
        out.pop()
    return "\n".join(out)


# Kimi's fragments (docs/visual/sprites/*.s on kimi/visual-refinement) replace a
# placeholder automatically when present AND exactly the slot's size:
#   img_<slot>.s      -> img_<slot>        (her same-size runtime drop-ins)
#   <design name>.s   -> the slot below    (her named design assets)
# Accepts dc.w (one CRY word per pixel) or dc.l (two per long) lists.
KIMI_SLOTS = {
    "falling_block": "block",
    "swinging_blade": "blade",
    "castle_hound": "hound",
}
SPRITES = os.path.join(os.path.dirname(ROOT), "docs", "visual", "sprites")

# V7: Kimi's frozen art, vendored verbatim in jaguar-toolchain/kimi_sprites/
# so the build never needs her branch (see its README for source commits).
# Every entry is required and must be exactly its runtime size: a missing or
# wrong-sized file stops the build. slot -> (file, width, height)
VENDORED = os.path.join(ROOT, "kimi_sprites")
KIMI_VENDORED = {
    # wave 1 enemies (+ b00d520 runtime corrections)
    "skull": ("img_skull.s", 16, 16),
    "guard": ("img_guard.s", 16, 24),
    "heavy": ("img_heavy.s", 16, 24),
    "watcher": ("img_watcher.s", 16, 24),       # right-facing
    "watcher_l": ("img_watcher_l.s", 16, 24),   # left-facing (Watcher aims left)
    "wraith": ("img_wraith.s", 16, 24),
    # wave 2 traps + props
    "spike16": ("img_spike16.s", 16, 8),
    "spike24": ("img_spike24.s", 24, 8),
    "flame": ("img_flame.s", 64, 16),
    "block": ("falling_block.s", 16, 16),
    "blade": ("swinging_blade.s", 16, 16),
    "door_closed": ("img_door_closed.s", 8, 40),
    "door_open": ("img_door_open.s", 8, 40),
    "door_brick": ("img_door_brick.s", 8, 40),
    "gate": ("img_gate.s", 16, 32),
    "lever_idle": ("img_lever_idle.s", 8, 12),
    "lever_tell": ("img_lever_tell.s", 8, 12),
    "lever_pulled": ("img_lever_pulled.s", 8, 12),
    "lever_sprung": ("img_lever_sprung.s", 8, 12),
    "exit": ("img_exit.s", 32, 48),
    "arrow_l": ("img_arrow_l.s", 8, 2),
    "arrow_r": ("img_arrow_r.s", 8, 2),
    # ladders (V7 ladder recovery): 4bpp INDEXED + RGB24 palette, converted below
    "ladder": ("ladder_normal_16x244.s", 16, 244),
    "ladder_gold": ("ladder_gold_16x244.s", 16, 244),
}
VENDORED_ONLY = ("watcher_l",)                  # no placeholder: emitted after the rest


def kimi_indexed_fragment(path, slot, w, h):
    """Kimi's 4bpp indexed export (`<name>_pal:` = 16 x RGB24 dc.l, then h rows of
    w/2 dc.b, high nibble = left pixel, index 0 = transparent) -> the runtime's
    16bpp CRY16 words, colours chosen with the same VJ CRY tables as every
    other asset (jagsim.rgb_to_cry). A same-named .png beside it, when PIL is
    available, must match pixel for pixel."""
    txt = open(path, encoding="utf-8", errors="replace").read()
    pal, rows = [], []
    for ln in txt.splitlines():
        code = ln.split(";")[0]
        if re.search(r"dc\.l\s", code):
            pal += [int(v, 16) for v in re.findall(r"\$([0-9A-Fa-f]{6})(?![0-9A-Fa-f])", code)]
        elif re.search(r"dc\.b\s", code):
            rows.append([int(v, 16) for v in re.findall(r"\$([0-9A-Fa-f]{2})(?![0-9A-Fa-f])", code)])
    if len(pal) != 16 or len(rows) != h or any(len(r) != w // 2 for r in rows):
        print("  kimi %s skipped: %d palette entries, %d rows of %s bytes (need 16, %d of %d)" % (
            os.path.basename(path), len(pal), len(rows), sorted(set(len(r) for r in rows)), h, w // 2))
        return None
    pix = [[n for b in r for n in (b >> 4, b & 15)] for r in rows]
    try:
        from PIL import Image
        png = os.path.splitext(path)[0] + ".png"
        if os.path.exists(png):
            im = Image.open(png).convert("RGBA")
            if im.size != (w, h):
                raise SystemExit("mkart: %s is %dx%d, expected %dx%d" % (os.path.basename(png), im.size[0], im.size[1], w, h))
            for y in range(h):
                for x in range(w):
                    r_, g_, b_, a_ = im.getpixel((x, y))
                    i = pix[y][x]
                    want = (0, 0, 0, 0) if i == 0 else ((pal[i] >> 16) & 255, (pal[i] >> 8) & 255, pal[i] & 255, 255)
                    if (a_ == 0) != (i == 0) or (i and (r_, g_, b_, a_) != want):
                        raise SystemExit("mkart: %s differs from its PNG at (%d,%d)" % (os.path.basename(path), x, y))
    except ImportError:
        pass
    cry = {0: 0}
    for i in sorted(set(v for r in pix for v in r) - {0}):
        cry[i] = rgb_to_cry(((pal[i] >> 16) & 255, (pal[i] >> 8) & 255, pal[i] & 255))
    words = ["%04X" % cry[v] for r in pix for v in r]
    print("  using kimi %s for img_%s (indexed -> CRY16, %d colours)" % (os.path.basename(path), slot, len(cry) - 1))
    return ["        dc.w    " + ",".join("$" + x for x in words[i:i + 8]) for i in range(0, len(words), 8)]


def kimi_vendored():
    found = {}
    for slot, (name, w, h) in KIMI_VENDORED.items():
        if slot in IMAGES and (len(IMAGES[slot][0]), len(IMAGES[slot])) != (w, h):
            raise SystemExit("mkart: runtime slot img_%s is %dx%d, contract says %dx%d"
                             % (slot, len(IMAGES[slot][0]), len(IMAGES[slot]), w, h))
        path = os.path.join(VENDORED, name)
        indexed = "_pal:" in open(path, encoding="utf-8", errors="replace").read()
        got = (kimi_indexed_fragment if indexed else kimi_fragment)(path, slot, w, h)
        if not got:
            raise SystemExit("mkart: Kimi art %s does not fit img_%s (%dx%d)" % (name, slot, w, h))
        found[slot] = got
    return found


def kimi_fragment(path, slot, w, h):
    txt = open(path, encoding="utf-8", errors="replace").read()
    m = re.search(r"(\d+)\s*[x×]\s*(\d+)", txt.splitlines()[0] if txt else "")
    if m and (int(m.group(1)), int(m.group(2))) != (w, h):
        print("  kimi %s skipped: header %s, slot img_%s is %dx%d" % (os.path.basename(path), m.group(0), slot, w, h))
        return None
    words = []
    for ln in txt.splitlines():
        code = ln.split(";")[0]
        if re.search(r"dc\.l\s", code):
            for v in re.findall(r"\$([0-9A-Fa-f]{8})", code):
                words += [v[:4], v[4:]]
        elif re.search(r"dc\.w\s", code):
            words += re.findall(r"\$([0-9A-Fa-f]{4})(?![0-9A-Fa-f])", code)
    if len(words) != w * h:
        print("  kimi %s skipped: %d pixels, slot img_%s needs %dx%d" % (os.path.basename(path), len(words), slot, w, h))
        return None
    print("  using kimi %s for img_%s" % (os.path.basename(path), slot))
    return ["        dc.w    " + ",".join("$" + x.upper() for x in words[i:i + 8]) for i in range(0, len(words), 8)]


# V7 environment bands (Bob Checkpoint C): five opaque 320x180 CRY16 backdrops,
# all resident in DRAM from BANDS_BASE ($020000), BAND_SIZE ($1C200) apart. The
# vendored files are included as they are (no 2.3 MB of generated copies):
# castle_bands.inc is only a wrapper, and every build re-validates each file.
BAND_W, BAND_H = 320, 180
BAND_SIZE = BAND_W * BAND_H * 2                 # $1C200
BANDS_DIR = os.path.join(VENDORED, "bands")
BAND_FILES = ["img_band_f%d.s" % n for n in range(1, 6)]


def check_bands():
    """Each band must be exactly 320x180 CRY16 words (dc.w), label img_band_fN;
    a phrase-aligned size is what keeps every band start phrase-aligned."""
    if BAND_SIZE % 8:
        raise SystemExit("mkart: band size $%X is not a whole number of phrases" % BAND_SIZE)
    for n, name in enumerate(BAND_FILES, 1):
        path = os.path.join(BANDS_DIR, name)
        txt = open(path, encoding="utf-8", errors="replace").read()
        words = []
        label = None
        for ln in txt.splitlines():
            code = ln.split(";")[0]
            m = re.match(r"^(img_band_f\d):", code)
            if m:
                label = m.group(1)
            elif re.search(r"dc\.w\s", code):
                words += re.findall(r"\$([0-9A-Fa-f]{4})(?![0-9A-Fa-f])", code)
            elif code.strip():
                raise SystemExit("mkart: %s has an unexpected line: %r" % (name, code.strip()[:40]))
        if label != "img_band_f%d" % n:
            raise SystemExit("mkart: %s: label %r, expected img_band_f%d" % (name, label, n))
        if len(words) != BAND_W * BAND_H:
            raise SystemExit("mkart: %s has %d pixels, a %dx%d band needs %d" % (name, len(words), BAND_W, BAND_H, BAND_W * BAND_H))
    return BAND_FILES


def emit_bands(out_dir):
    check_bands()
    o = ["; castle_bands.inc - GENERATED by tools/mkart.py. Do not edit.",
         "; Kimi's five 320x180 CRY16 environment bands (vendored, verbatim) in ROM; the",
         "; boot code copies them once to BANDS_BASE (all resident, never swapped).",
         "        .phrase",
         "bands_start:"]
    for name in BAND_FILES:
        o.append('        .include "../kimi_sprites/bands/%s"' % name)
    o.append("bands_end:")
    with open(os.path.join(out_dir, "castle_bands.inc"), "w", newline="\n") as f:
        f.write("\n".join(o) + "\n")
    print("wrote castle_bands.inc: 5 bands, %d bytes each, %d bytes total" % (BAND_SIZE, BAND_SIZE * 5))


def kimi_art(images):
    found = {}
    if not os.path.isdir(SPRITES):
        return found
    for slot, rows in images.items():
        names = ["img_%s.s" % slot] + ["%s.s" % k for k, v in KIMI_SLOTS.items() if v == slot]
        for n in names:
            path = os.path.join(SPRITES, n)
            if os.path.exists(path):
                got = kimi_fragment(path, slot, len(rows[0]), len(rows))
                if got:
                    found[slot] = got
                    break
    return found


def emit():
    src = open(os.path.join(ROOT, "gate6_castle", "gate6_castle.s"), encoding="utf-8", errors="replace").read()
    o = []
    o.append("; castle_art.inc - GENERATED by tools/mkart.py. Edit the ASCII maps there, not this file.")
    o.append("; CRY16 bitmaps, each a whole number of phrases wide. Copied to DRAM at PIXBASE.")
    o.append("; Palette (CRY16, chosen against Virtual Jaguar's cry2rgb tables):")
    for k, v in PALETTE_RGB.items():
        o.append(";   %s = $%04X  rgb%s" % (k, PALETTE[k], v))
    o.append("")
    o.append("        .phrase")
    o.append("pix_start:")
    o.append("; ---- Bob's authentic art (verbatim from gate6_castle.s) ----")
    vendored = kimi_vendored()
    for lbl, name, w, h in (("floor_pixels", "img_floor", 320, 8), ("enemy_pixels", "img_skull", 16, 16),
                            ("hero_pixels", "img_hero", 16, 24)):
        if name == "img_skull":                     # Kimi's Sentinel Skull replaces Bob's
            o.append("%s:\t\t\t\t; %dx%d (Kimi img_skull.s)" % (name, w, h))
            o.extend(vendored["skull"])
            continue
        o.append("%s:\t\t\t\t; %dx%d" % (name, w, h))
        o.append(bob_block(src, lbl))
    o.append("; ---- placeholder art (Kimi to replace; keep sizes or tell Claude) ----")
    kimi = kimi_art(IMAGES)
    kimi.update({k: v for k, v in vendored.items() if k in IMAGES})
    for name, rows in IMAGES.items():
        o.append("img_%s:\t\t\t\t; %dx%d%s" % (name, len(rows[0]), len(rows), " (Kimi)" if name in kimi else ""))
        if name in kimi:
            o.extend(kimi[name])
            continue
        for r in rows:
            words = ["$%04X" % PALETTE[c] for c in r]
            for i in range(0, len(words), 8):
                o.append("        dc.w    " + ",".join(words[i:i + 8]))
    for name in VENDORED_ONLY:
        fname, w, h = KIMI_VENDORED[name]
        o.append("img_%s:\t\t\t\t; %dx%d (Kimi %s)" % (name, w, h, fname))
        o.extend(vendored[name])
    o.append("pix_end:")
    # exact size of the art block (for the memory-map guards in test_gate7.py)
    art_words = 320 * 8 + 16 * 16 + 16 * 24 + sum(len(r[0]) * len(r) for r in IMAGES.values()) +         sum(KIMI_VENDORED[n][1] * KIMI_VENDORED[n][2] for n in VENDORED_ONLY)
    o.append("ART_BYTES        equ     %d" % (art_words * 2))
    o.append("")
    out_dir = os.path.join(ROOT, "gate7_castle")
    os.makedirs(out_dir, exist_ok=True)
    emit_bands(out_dir)
    with open(os.path.join(out_dir, "castle_art.inc"), "w", newline="\n") as f:
        f.write("\n".join(o) + "\n")
    print("wrote castle_art.inc:", ", ".join("%s %dx%d" % (k, len(v[0]), len(v)) for k, v in IMAGES.items()))
    print("palette:", {k: "$%04X" % v for k, v in PALETTE.items()})


if __name__ == "__main__":
    emit()
