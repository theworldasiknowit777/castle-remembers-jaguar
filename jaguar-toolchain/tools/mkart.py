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


def ladder(lines=216):
    rows = []
    for y in range(lines):
        rows.append(".WW..........WW." if y % 6 else ".WWwwwwwwwwwwWW.")
    return rows


IMAGES["ladder"] = ladder()


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
    for lbl, name, w, h in (("floor_pixels", "img_floor", 320, 8), ("enemy_pixels", "img_skull", 16, 16),
                            ("hero_pixels", "img_hero", 16, 24)):
        o.append("%s:\t\t\t\t; %dx%d" % (name, w, h))
        o.append(bob_block(src, lbl))
    o.append("; ---- placeholder art (Kimi to replace; keep sizes or tell Claude) ----")
    for name, rows in IMAGES.items():
        o.append("img_%s:\t\t\t\t; %dx%d" % (name, len(rows[0]), len(rows)))
        for r in rows:
            words = ["$%04X" % PALETTE[c] for c in r]
            for i in range(0, len(words), 8):
                o.append("        dc.w    " + ",".join(words[i:i + 8]))
    o.append("pix_end:")
    o.append("")
    out_dir = os.path.join(ROOT, "gate7_castle")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "castle_art.inc"), "w", newline="\n") as f:
        f.write("\n".join(o) + "\n")
    print("wrote castle_art.inc:", ", ".join("%s %dx%d" % (k, len(v[0]), len(v)) for k, v in IMAGES.items()))
    print("palette:", {k: "$%04X" % v for k, v in PALETTE.items()})


if __name__ == "__main__":
    emit()
