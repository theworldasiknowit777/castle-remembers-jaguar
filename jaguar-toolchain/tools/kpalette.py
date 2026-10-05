# kpalette.py — Castle Remembers verified CRY16 palette (kimi/visual-refinement)
#
# Single source of truth for all Kimi art tools. Every word here is verified
# against Virtual Jaguar's own cry2rgb.h tables (cry_tables.json, mirrored by
# tools/jagsim.py). REPLACES the old approximate decode in cry_preview.py:
# $F001 renders BLACK, not red; $CE7B renders olive, not grey.
#
# Usage: from kpalette import PAL, cry_to_rgb, rgb_to_cry

import json
import os

_CRY = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "cry_tables.json")))


def cry_to_rgb(w):
    """CRY16 -> RGB using Virtual Jaguar's own tables (src/cry2rgb.h, v2.1.3-R5)."""
    c, r, y = (w >> 12) & 0xF, (w >> 8) & 0xF, w & 0xFF
    return tuple((_CRY[t][c][r] * y) >> 8 for t in ("redcv", "greencv", "bluecv"))


def rgb_to_cry(rgb):
    """Closest CRY16 word to an (r, g, b) colour (brute force; for picking art colours)."""
    best, bw = None, 0
    for c in range(16):
        for r in range(16):
            base = [_CRY[t][c][r] for t in ("redcv", "greencv", "bluecv")]
            m = max(base) or 1
            y = max(0, min(255, round(max(rgb) * 256 / m)))
            got = [(b * y) >> 8 for b in base]
            d = sum((a - g) ** 2 for a, g in zip(rgb, got))
            if best is None or d < best:
                best, bw = d, (c << 12) | (r << 8) | y
    return bw


TRANS = 0x0000  # transparent on every TRANS sprite — never use as a colour

# Verified palette (name -> word). RGB comments are the ACTUAL VJ decode.
PAL = {
    # outlines / shadow
    "BLACK":    0x3601,  # (0,0,0) opaque black — safe under TRANS (word != $0000)
    "SHADOW":   0x9816,  # (21,20,17) deep shadow / cracks
    "MORTAR":   0x8828,  # (38,39,35)
    # warm stone (F1/F3)
    "WARM_M":   0x9881,  # (128,122,102)
    "WARM_L":   0x98AB,  # (170,162,135)
    "WARM_D":   0x9852,  # (81,78,65)
    # cool stone (F2)
    "COOL_M":   0x7870,  # (100,111,108)
    "COOL_L":   0x789D,  # (141,156,151)
    "COOL_D":   0x7748,  # (66,64,71)
    # pale stone (F5)
    "PALE_M":   0x9893,  # (146,140,116)
    "PALE_L":   0x98BD,  # (188,180,149)
    "PALE_D":   0x985C,  # (91,87,72)
    # solemn blue-grey (F4)
    "SOLE_M":   0x6770,  # (88,93,111)
    "SOLE_L":   0x67B3,  # (141,149,178)
    "SOLE_D":   0x673E,  # (49,51,61)
    # fire
    "FLAME_Y":  0xB8FF,  # (254,207,134) core
    "FLAME_O":  0xE7E9,  # (232,121,30) edge
    "EMBER":    0xE578,  # (119,45,15) dim ember / warning rows
    # banners / cloth
    "BANNER":   0xE397,  # (150,33,20)
    "BANNER_D": 0xE35C,  # (91,20,12)
    "GOLDTRIM": 0xC9C5,  # (196,164,78)
    # wood
    "WOOD":     0xC87A,  # (121,90,48)
    "WOOD_D":   0xC84A,  # (73,54,29)
    # iron
    "IRON_D":   0x773A,  # (53,52,57)
    "IRON_L":   0x7776,  # (109,106,117)
    # sky / dressing
    "NIGHT":    0x3640,  # (25,35,63) night window
    "MOON":     0x77E1,  # (208,202,224)
    "MOSS":     0xAB60,  # (74,95,42)
    "BONE":     0x98A9,  # (168,161,134) debris / bone
    "ASH":      0x8860,  # (92,95,86)
    # dawn (F5)
    "DAWN_LO":  0xB65C,  # (91,56,48)
    "DAWN_HI":  0x4648,  # (37,43,71)
    "DAWN_GL":  0xC7DD,  # (220,143,88)
    "STAR":     0x77F1,  # (223,216,240)
    # warning / tells (VJ-verified reds — $F001 is BLACK, never use it)
    "WARN_R":   0xE2DD,  # (220,32,29) bright warning red (HUD guard red — small use only)
    "WARN_D":   0xE26E,  # (110,16,15) dark warning red — preferred in-world
    "COPPER":   0xD6BF,  # (198,102,47) trapped-lever tell
    "GOLD":     0xEAE7,  # (230,173,30) lever knob gold (matches HUD lever gold)
}

if __name__ == "__main__":
    for name, w in PAL.items():
        print(f"{name:10s} ${w:04X}  rgb{cry_to_rgb(w)}")
