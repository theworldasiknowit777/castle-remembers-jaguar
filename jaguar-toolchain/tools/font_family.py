# font_family.py — Castle Remembers V6 castle-voice font (kimi/visual-refinement)
#
# Chiselled-stone bitmap font for whispers, floor titles, rebuild screen,
# death/win messages and interaction prompts. Asset production only:
# Claude owns text/state logic, Bob owns font-buffer / OP review (Checkpoint B).
#
# Contract (see §contract printed at runtime and in font_data.s header):
#   - glyph cell 6x8 (5x7 glyph + 1 col right spacing + 1 row bottom spacing)
#   - fixed advance 6 px, line pitch 10 px
#   - two colours: face PALE_L $98BD, relief shadow BLACK $3601 at (+1,+1)
#   - CPU-render bitmask format: 7 bytes per glyph, bit 4 = leftmost column
#   - glyph order string below doubles as the index table
#
# Palette VJ-verified via kpalette.py. Deterministic output.

import os
from PIL import Image, ImageDraw

from kpalette import PAL, cry_to_rgb

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_OUT = os.path.join(HERE, "..", "..", "docs", "visual", "previews")
SPR_OUT = os.path.join(HERE, "..", "..", "docs", "visual", "sprites")
os.makedirs(IMG_OUT, exist_ok=True)
os.makedirs(SPR_OUT, exist_ok=True)

FACE = PAL["PALE_L"]      # $98BD — pale chiselled stone
RELIEF = PAL["BLACK"]     # $3601 — relief shadow, opaque under TRANS

# ---------------------------------------------------------------- glyphs (5x7)
G = {
"A": ["01110","10001","10001","11111","10001","10001","10001"],
"B": ["11110","10001","10001","11110","10001","10001","11110"],
"C": ["01110","10001","10000","10000","10000","10001","01110"],
"D": ["11110","10001","10001","10001","10001","10001","11110"],
"E": ["11111","10000","10000","11110","10000","10000","11111"],
"F": ["11111","10000","10000","11110","10000","10000","10000"],
"G": ["01110","10001","10000","10111","10001","10001","01111"],
"H": ["10001","10001","10001","11111","10001","10001","10001"],
"I": ["111","010","010","010","010","010","111"],
"J": ["00111","00010","00010","00010","00010","10010","01100"],
"K": ["10001","10010","10100","11000","10100","10010","10001"],
"L": ["10000","10000","10000","10000","10000","10000","11111"],
"M": ["10001","11011","10101","10101","10001","10001","10001"],
"N": ["10001","11001","10101","10011","10001","10001","10001"],
"O": ["01110","10001","10001","10001","10001","10001","01110"],
"P": ["11110","10001","10001","11110","10000","10000","10000"],
"Q": ["01110","10001","10001","10001","10101","10010","01101"],
"R": ["11110","10001","10001","11110","10100","10010","10001"],
"S": ["01111","10000","10000","01110","00001","00001","11110"],
"T": ["11111","00100","00100","00100","00100","00100","00100"],
"U": ["10001","10001","10001","10001","10001","10001","01110"],
"V": ["10001","10001","10001","10001","10001","01010","00100"],
"W": ["10001","10001","10001","10101","10101","11011","10001"],
"X": ["10001","01010","00100","00100","00100","01010","10001"],
"Y": ["10001","01010","00100","00100","00100","00100","00100"],
"Z": ["11111","00001","00010","00100","01000","10000","11111"],
"0": ["01110","10001","10011","10101","11001","10001","01110"],
"1": ["010","110","010","010","010","010","111"],
"2": ["01110","10001","00001","00110","01000","10000","11111"],
"3": ["11111","00010","00100","00010","00001","10001","01110"],
"4": ["00010","00110","01010","10010","11111","00010","00010"],
"5": ["11111","10000","11110","00001","00001","10001","01110"],
"6": ["00110","01000","10000","11110","10001","10001","01110"],
"7": ["11111","00001","00010","00100","01000","01000","01000"],
"8": ["01110","10001","10001","01110","10001","10001","01110"],
"9": ["01110","10001","10001","01111","00001","00010","01100"],
".": ["00000","00000","00000","00000","00000","01100","01100"],
",": ["00000","00000","00000","00000","00100","00100","01000"],
":": ["00000","00100","00100","00000","00100","00100","00000"],
";": ["00000","00100","00100","00000","00100","00100","01000"],
"!": ["00100","00100","00100","00100","00100","00000","00100"],
"?": ["01110","10001","00001","00110","00100","00000","00100"],
"-": ["00000","00000","00000","01110","00000","00000","00000"],
"+": ["00000","00100","00100","11111","00100","00100","00000"],
"/": ["00001","00010","00010","00100","01000","01000","10000"],
"%": ["11001","11010","00010","00100","01000","01011","10011"],
"(": ["00010","00100","01000","01000","01000","00100","00010"],
")": ["01000","00100","00010","00010","00010","00100","01000"],
" ": ["00000","00000","00000","00000","00000","00000","00000"],
"\u2026": ["00000","00000","00000","00000","00000","10101","10101"],  # …
"\u2191": ["00100","01110","10101","00100","00100","00100","00100"],  # ↑
"\u2193": ["00100","00100","00100","00100","10101","01110","00100"],  # ↓
"\u2190": ["00000","00100","01100","11111","01100","00100","00000"],  # ←
"\u2192": ["00000","00100","00110","11111","00110","00100","00000"],  # →
}

ORDER = ("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
         ".,:;!?-+/%() \u2026\u2191\u2193\u2190\u2192")

for ch in ORDER:
    rows = G[ch]
    assert len(rows) == 7, f"{ch!r}: need 7 rows"
    for r in rows:
        assert len(r) <= 5, f"{ch!r}: row too wide: '{r}'"
        assert set(r) <= set("01"), f"{ch!r}: bad pixel"

CELL_W, CELL_H = 6, 8          # advance 6, cell height 8
LINE_PITCH = 10

def glyph_mask(ch):
    """7 bytes, bit 4 = leftmost column."""
    out = []
    for r in G[ch]:
        v = 0
        for i, b in enumerate(r):
            if b == "1":
                v |= 1 << (4 - i)
        out.append(v)
    return out

# ---------------------------------------------------------------- rendering
def draw_text(img, x, y, text, face=FACE, relief=RELIEF, backing=None):
    """CPU-style render into a pixel-word 2D buffer (rows of CRY16 words)."""
    if backing is not None:
        w = len(text) * CELL_W - 1
        for yy in range(y - 2, y + 9):
            for xx in range(x - 2, x + w + 2):
                if 0 <= xx < len(img[0]) and 0 <= yy < len(img):
                    img[yy][xx] = backing
    cx = x
    for ch in text:
        rows = G[ch]
        for ry, row in enumerate(rows):
            for i, b in enumerate(row):
                if b == "1":
                    yy, xx = y + ry, cx + i
                    if 0 <= yy + 1 < len(img) and 0 <= xx + 1 < len(img[0]):
                        img[yy + 1][xx + 1] = relief
                    if 0 <= yy < len(img) and 0 <= xx < len(img[0]):
                        img[yy][xx] = face
        cx += CELL_W

def text_width(text):
    return len(text) * CELL_W - 1

def center_x(text):
    return (320 - text_width(text)) // 2

def render_png(rows, path, scale=1):
    h, w = len(rows), len(rows[0])
    img = Image.new("RGB", (w * scale, h * scale))
    d = ImageDraw.Draw(img)
    for y, row in enumerate(rows):
        for x, wd in enumerate(row):
            d.rectangle([x * scale, y * scale, (x + 1) * scale - 1,
                         (y + 1) * scale - 1], fill=cry_to_rgb(wd))
    img.save(path)

# ---------------------------------------------------------------- glyph sheet
def glyph_sheet():
    cols = 9
    rows_n = (len(ORDER) + cols - 1) // cols
    cw, chh = 6 * 14, 8 * 14 + 18     # glyph cell + label strip
    big = Image.new("RGB", (cols * cw, rows_n * chh))
    d = ImageDraw.Draw(big)
    for idx, ch in enumerate(ORDER):
        gx, gy = (idx % cols) * cw, (idx // cols) * chh
        # render glyph into sheet buffer then blit scaled
        for ry, row in enumerate(G[ch]):
            for i, b in enumerate(row):
                if b == "1":
                    for sx in range(12):
                        for sy in range(12):
                            d.rectangle([gx + 12 + i * 12 + sx + 12, gy + 12 + ry * 12 + sy + 12,
                                         gx + 12 + i * 12 + sx + 12, gy + 12 + ry * 12 + sy + 12],
                                        fill=cry_to_rgb(RELIEF))
                    d.rectangle([gx + 12 + i * 12, gy + 12 + ry * 12,
                                 gx + 12 + i * 12 + 11, gy + 12 + ry * 12 + 11],
                                fill=cry_to_rgb(FACE))
        label = {" ": "SP", "\u2026": "ELL", "\u2191": "UP", "\u2193": "DN",
                 "\u2190": "LT", "\u2192": "RT"}.get(ch, ch)
        d.text((gx + 30, gy + 12 + 7 * 12 + 6), label, fill=(40, 36, 30))
    # stone background rendered straight to PIL
    comp = Image.new("RGB", (cols * cw, rows_n * chh))
    ds = ImageDraw.Draw(comp)
    stone_c = cry_to_rgb(PAL["WARM_M"])
    mortar_c = cry_to_rgb(PAL["MORTAR"])
    ds.rectangle([0, 0, cols * cw, rows_n * chh], fill=stone_c)
    for y in range(0, rows_n * chh, 16):
        ds.line([0, y, cols * cw, y], fill=mortar_c)
    # glyph layer composited on top (only where drawn)
    mask = Image.new("L", (cols * cw, rows_n * chh), 0)
    dm = ImageDraw.Draw(mask)
    for idx, ch in enumerate(ORDER):
        gx, gy = (idx % cols) * cw, (idx // cols) * chh
        for ry, row in enumerate(G[ch]):
            for i, b in enumerate(row):
                if b == "1":
                    dm.rectangle([gx + 12 + i * 12, gy + 12 + ry * 12,
                                  gx + 12 + i * 12 + 23, gy + 12 + ry * 12 + 23], fill=255)
    comp.paste(big, (0, 0), mask)
    for idx, ch in enumerate(ORDER):             # labels on the stone layer
        gx, gy = (idx % cols) * cw, (idx // cols) * chh
        label = {" ": "SP", "\u2026": "ELL", "\u2191": "UP", "\u2193": "DN",
                 "\u2190": "LT", "\u2192": "RT"}.get(ch, ch)
        ds.text((gx + 30, gy + 12 + 7 * 12 + 6), label, fill=(40, 36, 30))
    comp.save(os.path.join(IMG_OUT, "v6_font_sheet.png"))
    return None

# ---------------------------------------------------------------- mockups (320x240)
import backdrop_family as bf

def scene(floor_rows):
    """Backdrop (320x180) + wainscot + floor slab + dark below = 320x240."""
    img = [r[:] for r in floor_rows]
    for y in range(180, 240):
        img.append([PAL["BLACK"]] * 320)
    for y in range(180, 194):                    # wainscot
        img[y] = [PAL["WARM_D"] if y % 8 else PAL["MORTAR"] for _ in range(320)]
    for y in range(194, 202):                    # floor slab strip
        img[y] = [PAL["WARM_M"] if y % 4 else PAL["MORTAR"] for _ in range(320)]
    return img[:240]

def mock_whisper():
    img = scene(bf.floor2())
    t = "IT KNOWS WHICH LEVER YOU TRUST"
    draw_text(img, center_x(t), 14, t)
    return img

def mock_title():
    img = scene(bf.floor1())
    t = "FLOOR 1 - GATEHOUSE"
    draw_text(img, center_x(t), 8, t)
    p = "S"+ "\u2191" +" CLIMB   L - ACT   X"+ "\u2193" +" DOWN"
    draw_text(img, center_x(p), 226, p)
    return img

def mock_rebuild():
    img = [[PAL["BLACK"]] * 320 for _ in range(240)]
    lines = ["THE CASTLE REMEMBERS", "",
             "IT HAS WATCHED YOU 3 TIMES", "",
             "IT ADAPTS."]
    y = 92
    for ln in lines:
        if ln:
            draw_text(img, center_x(ln), y, ln, backing=PAL["BLACK"])
        y += LINE_PITCH + 4
    return img

def mock_end():
    img = scene(bf.floor5())
    t1 = "YOU ESCAPED"
    t2 = "THE CASTLE FORGETS \u2026FOR NOW"
    draw_text(img, center_x(t1), 30, t1)
    draw_text(img, center_x(t2), 30 + LINE_PITCH + 6, t2)
    return img

# ---------------------------------------------------------------- run
sheet = glyph_sheet()

MOCKS = {
    "v6_mock_whisper.png": mock_whisper,
    "v6_mock_title.png": mock_title,
    "v6_mock_rebuild.png": mock_rebuild,
    "v6_mock_end.png": mock_end,
}
for name, fn in MOCKS.items():
    rows = fn()
    assert len(rows) == 240 and all(len(r) == 320 for r in rows)
    render_png(rows, os.path.join(IMG_OUT, name), scale=2)

# ---------------------------------------------------------------- fragment
lines = [
    "; font_data.s — Castle Remembers V6 castle-voice font (kimi/visual-refinement)",
    "; Chiselled-stone 5x7 glyphs in a 6x8 cell. CPU-render bitmask format.",
    "; Contract for Claude:",
    ";   advance 6 px, line pitch 10 px, glyph cell 6x8",
    ";   face = $98BD (PALE_L), relief shadow = $3601 (BLACK) at (+1,+1)",
    ";   7 bytes per glyph, bit 4 = leftmost column",
    ";   index = position in FONT_ORDER below",
    "; Palette VJ-verified (kpalette.py). New runtime asset — Bob Checkpoint B.",
    "; NOT linked — Claude owns text logic, Bob owns buffer/OP approach.",
    "",
    "FONT_FACE    equ     $98BD",
    "FONT_RELIEF  equ     $3601",
    "FONT_ADV     equ     6",
    "FONT_PITCH   equ     10",
    "",
    "; FONT_ORDER: A-Z 0-9 . , : ; ! ? - + / % ( ) SP ELLIPSIS UP DOWN LEFT RIGHT",
    "font_glyphs:",
]
for ch in ORDER:
    label = ch if ch.isalnum() else {" ": "SP", "\u2026": "ELLIPSIS",
        "\u2191": "UP", "\u2193": "DOWN", "\u2190": "LEFT", "\u2192": "RIGHT"}.get(ch, ch)
    lines.append("        dc.b    " + ",".join(f"${b:02X}" for b in glyph_mask(ch))
                 + f"   ; {label}")
with open(os.path.join(SPR_OUT, "font_data.s"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")

print("glyphs:", len(ORDER))
print("sheet:", os.path.join(IMG_OUT, "v6_font_sheet.png"))
print("mockups:", list(MOCKS))
print("fragment:", os.path.join(SPR_OUT, "font_data.s"))
print("max line check: 'IT KNOWS WHICH LEVER YOU TRUST' =",
      text_width("IT KNOWS WHICH LEVER YOU TRUST"), "px of 320")
