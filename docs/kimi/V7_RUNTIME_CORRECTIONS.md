# V7 Runtime Correction Note — Enemy Presentation

Branch `kimi/visual-refinement`, baseline Claude `68df4b7`.
Evidence: `jaguar-toolchain/gate7_castle/v7_evidence/` (Virtual Jaguar is
authoritative). Generator: `tools/enemy_family_24.py` (regenerates everything
below; deterministic). No gameplay, hitbox, floor-Y, OP or memory changes.

## 1. Sentinel Skull palette correction → `docs/visual/sprites/img_skull.s`

VJ evidence (`vj_zoom_floor_strips.png`, strip 1/4): the integrated skull
rendered **green** — its body words were `$CE7B`, the same olive-green as
Bob's floor slab — and its eye words `$F001` rendered **black**.

Corrected, same 16×16 silhouette, same transparency contract, same 2 px
deliberate float, same runtime slot:

| Role | Old word (VJ result) | New word (VJ result) |
|---|---|---|
| body | `$CE7B` (olive green) | `$789D` (steel grey 141,156,151) |
| light | `$CE9C` (green) | `$67B3` (cold steel light 141,149,178) |
| shade | — | `$7870` (steel mid) |
| eyes | `$F001` (black) | `$E2DD` (red 220,32,29) |
| eye glint | `$CFCB` (green) | `$77E1` (pale moon) |
| outline | `$3601` (black ✓) | `$3601` (unchanged) |

The skull now reads as a steel sentinel and is unmistakable against the green
floor. **Supersedes `sentinel_skull.s` (deleted); the castle_art.inc comment
referencing it should now point at `img_skull.s`.**

## 2. Bottom alignment → `img_guard.s`, `img_heavy.s`, `img_watcher.s`

VJ evidence: guard / heavy / watcher each carried ~1 empty row at the bottom
and read slightly ungrounded. Art shifted **down one row** (dropped bottom
empty row, prepended empty top row): feet and pedestal base now occupy the
last sprite row and sit flush on the floor line. Plume/crenellation detail
moved from row 0–1 to row 1–2, still inside the harmless top zone.

- **Wraith: unchanged** — rows 22–23 stay empty; the 2 px float is
  intentional (it hovers; `vj_zoom_floor_strips.png` strip 3 confirms it
  reads correctly).
- **Skull: unchanged alignment** — 2 px float retained.

## 3. Stone Watcher facing → `img_watcher_l.s` (new, same size)

Decision: **facing matters** — the Watcher's threat read is its aim direction
(bow side), and canon has it "turn to face you". The runtime does not mirror
sprites, so:

- `img_watcher.s` = **right-facing** (bow on viewer's right) — the asset
  Claude already integrated, now grounded per §2.
- `img_watcher_l.s` = **left-facing**, pixel-mirror, identical palette and
  16×24 dimensions.

Integration choice is Claude's: swap the object DATA pointer by facing (no
new slot), or a second slot (Bob Checkpoint B). No mirroring hardware or OP
changes requested.

## What did NOT change

Castle Hound (untouched), silhouettes, hitboxes, dimensions, transparency
contracts, trap/prop/background assets, gameplay logic, OP objects, memory
layout.

## Files

- `docs/visual/sprites/img_skull.s` (new), `img_guard.s` / `img_heavy.s` /
  `img_watcher.s` (regenerated), `img_watcher_l.s` (new)
- `docs/visual/previews/v2_enemy_family.png` (regenerated sheet, 7 entries)
- deleted: `docs/visual/sprites/sentinel_skull.s` (superseded)
