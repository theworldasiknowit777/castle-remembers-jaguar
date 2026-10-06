# V7 Ladder Correction Pass — Correction Note

Branch target: `kimi/visual-refinement` (baseline `bda9139`)
Scope: ART CORRECTION ONLY. No gameplay, geometry, collision, HUD, or trap changes.

## 1. Runtime issue addressed

| | Old art | Gate 7 runtime contract |
|---|---|---|
| Size | 16x216 | **16x244** |
| Normal draw | short by ~28 rows | ~200 rows |
| Through-floor draw | short by ~26 rows | ~242 rows |
| Stub/hole draw | OK | ~34 rows |

Both new assets are exactly **16 px wide x 244 px tall**, preserving the
transparency contract (index 0 transparent) and the 16 px ladder column.
Claude's ladder geometry and climb path are untouched and authoritative.

## 2. Deliverables

- `ladder_normal_16x244.png` / `ladder_normal_16x244.s` — normal ladder
- `ladder_gold_16x244.s` / `ladder_gold_16x244.png` — gold / special
  long-ladder variant (gift-shard route), same geometry, gold/brass palette
- `ladder_correction_preview.png` — mockup: tiling through floor opening,
  ~200-row normal segment, ~242-row through-floor segment, 6x top/bottom crops
- This note.

## 3. Pixel design (both variants)

- Rails: 3 px each side (x=0..2, x=13..15), full 244-row height, shaded
  outer-edge dark -> inner-edge light. Side faces only: **nothing outside
  x=0..15**, so no decorative protrusion implies a wider collision area.
- Rungs: 10 px bars (x=3..12), 2 px tall, pitch 16 px, first at row 8, last
  at row 232 -> symmetric 8 px clear margin top and bottom. Because rungs are
  placed identically at both ends, the sprite tiles visually cleanly through
  the floor opening and stays readable in any vertical crop (top, bottom, stub).
- Continuous full-height rails guarantee legibility when only the lower or
  upper portion is visible (normal ~200-row draw, ~242-row through-floor draw,
  ~34-row stub).
- Small deterministic wood-grain variation and a 2 px dark notch tick on the
  rails every 61 rows carry the established wooden / Visigothic language; a
  1 px stone accent pin sits on every 4th rung. All accents stay inside the
  16 px column.

## 4. Palettes (CRY16, index 0 = transparent)

Normal (wood, RGB24):
```
0: 000000  1: 1A0F08  2: 2B1A10  3: 4A2F1C  4: 6B452A
5: 8A5A33  6: A9743F  7: C89055  8: 3A3A42  9: 5C5C66
10: 18181E 11: 8A5A33 12: 4A2F1C 13: 6B452A 14: A9743F 15: C89055
```
Gold (RGB24):
```
0: 000000  1: 241A04  2: 3C2C0A  3: 624812  4: 8C681E
5: B08C30  6: D0AC4A  7: EED278  8: 3A3A42  9: 5C5C66
10: 18181E 11: B08C30 12: 624812 13: 8C681E 14: D0AC4A 15: EED278
```
Gold reuses the normal ladder's shape 1:1 (identical silhouette and rung
positions) so it drops into the same collision/climb path; only shading differs.

## 5. Assembly fragment format

- CRY16 4bpp indexed: 2 pixels/byte, 8 bytes per row, 244 rows = 1952 bytes.
- **The per-row byte layout is byte-identical in structure to the old 16x216
  art** — the correction is purely the row count (216 -> 244). If the build's
  sprite object header encodes height, update it to 244 (0x00F4). No other
  runtime change should be needed.
- NOTE: the fragment syntax (`dc.b` rows + `dc.l` palette block) follows the
  established CRY16 convention; verify label names against the existing
  ladder fragment when merging — only the label/`include` wiring may differ.

## 6. Masonry overlap (optional item) — DEFERRED

The falling-masonry sprite overlapping the castle-message band at the top of
the screen cannot be fixed purely in art within the existing sprite dimensions
and slot: the overlap is a placement/position issue (hazard hangs at the top
of the screen where the message band lives), not pixel content. Per the task
boundary (do not move the hazard, alter fall path, timing, collision, or OP
objects), no art change was made. Documented here and deferred — needs either
a reserved clear band in the message row during the hang phase (runtime) or
an approved slot nudge (design), neither of which is in scope for this pass.

## 7. Boundaries respected

No new props, no gameplay changes, no enemy art, no trap mechanics, no
HUD/message changes, no background integration. Art only.
