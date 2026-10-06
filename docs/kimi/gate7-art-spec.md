# Gate 7 — art slots for Kimi

The five-floor build runs on placeholder art drawn as ASCII maps in
`jaguar-toolchain/tools/mkart.py`.

- `mkart.py` writes `gate7_castle/castle_art.inc` (CRY16 words). The build copies it to DRAM at `$010000`.
- To replace an image, edit its map in `mkart.py` (or hand Claude a PNG at the listed size) and run `sh tools/build_gate7.sh`.

## Hard constraints (from the Object Processor)

- **16-bit CRY**, colour `$0000` = transparent on every object except the floor slab.
- **Width must be a multiple of 4 pixels**: one 8-byte phrase per 4 pixels.
- **Keep the listed sizes** unless you tell Claude. Sizes feed the collision boxes and the per-frame object records.
- The real colours are Virtual Jaguar's CRY tables.
  - `tools/jagsim.py` has `rgb_to_cry()` and `cry_to_rgb()` (VJ's own `cry2rgb.h`), and `mkart.py` uses them.
  - Bob's original palette words do not look like their names. Under VJ's tables:

| Word | Bob's name | Actual colour |
|---|---|---|
| `$CE7B` | stone | olive |
| `$3601` | shadow | black |
| `$F001` | skull red | black |
| `$E011` | hero | near-black |

  - The hero and skull are kept byte-for-byte until you decide.
- Screen is 320×240.
  - The floor surface is at screen row 194 in VJ (halfline 420). Everything stands on it.
  - Above the floor are about 180 rows of empty castle wall: room for backgrounds.

## Slots

| Image | Size (px) | States / notes | Placement |
|---|---|---|---|
| `img_floor` | 320×8 | floor slab, opaque (Bob's) | y = floor |
| `img_ladder` | **16×244** (wave 2; was 16×216) | **Still a placeholder: Kimi's asset is 16×216.** One tall strip. The game shows the top 200 lines (up-ladder), 34 lines (hole below the floor), or 242 lines (a ladder that passes through the floor) | x = 6 / 152 / 298 |
| `img_ladder_gold` | 16×244 | **new**: the canon gold long ladder (door tier 2, avoided side, runs F1 to F3) | same x |
| `img_door_closed` | 8×40 | wall (blocks walking) — **Kimi art integrated (V7 wave 2)** | x = 94 / 218 (tight: 75 / 237) |
| `img_door_open` | 8×40 | open frame — **Kimi art integrated (V7 wave 2)** | same |
| `img_door_brick` | 8×40 | bricked by the castle (cannot open) — **Kimi art integrated (V7 wave 2)** | same |
| `img_gate` | 16×32 | portcullis; drawn down over the centre ladder, or raised 48 rows when open — **Kimi art integrated (V7 wave 2)** | x = 152 |
| `img_lever_idle` | 8×12 | gold knob — **Kimi art integrated (V7 wave 2)** | x = 80 / 232 |
| `img_lever_tell` | 8×12 | **trapped lever**: same lever, wrong-coloured knob (copper). Must stay subtle but learnable — **Kimi art integrated (V7 wave 2)** | same |
| `img_lever_pulled` | 8×12 | handle down — **Kimi art integrated (V7 wave 2)** | same |
| `img_lever_sprung` | 8×12 | dud/trap after use: broken — **Kimi art integrated (V7 wave 2)** | same |
| `img_spike16`, `img_spike24` | 16×8, 24×8 | raised. **Bottom 2 rows are also drawn alone as the retracted state** (keep them a "slot" plate) — **Kimi art integrated (V7 wave 2)** | various |
| `img_exit` | 32×48 | exit arch, bright: the goal — **Kimi art integrated (V7 wave 2)** | x = 277 (or 11 when moved left) |
| `img_flame` | 64×16 | eruption. **Bottom 2 rows alone flash as the 0.55 s warning** (keep them embers) — **Kimi art integrated (V7 wave 2)** | ±32 px around a lever |
| `img_skull` | 16×16 | Sentinel Skull — **Kimi `img_skull.s` integrated (V7, b00d520 steel palette)** | patrols |
| `img_guard` | 16×24 | Fallen Guard — **Kimi art integrated (V7 wave 1)** | patrols / chases |
| `img_heavy` | 16×24 | Fallen Guard, armoured (needs two shoves): must read as tougher — **Kimi art integrated (V7 wave 1)** | |
| `img_watcher` | 16×24 | Stone Watcher, static archer statue — **Kimi art integrated (V7)**; faces where it aims: `img_watcher` (right) / `img_watcher_l` (left), swapped by `E_DIR` | |
| `img_wraith` | 16×24 | Judgment Wraith, F5 pursuer — **Kimi art integrated (V7 wave 1)** | |
| `img_arrow_r`, `img_arrow_l` | 8×2 | arrow, both directions (no hardware flip used) — **Kimi art integrated (V7 wave 2)** | knee height |
| `img_hero` | 16×24 | Bob's authentic hero (single frame) | |
| `img_chest_closed` | 16×12 | **new**: real chest | F1 180 · F2 261 · F3 123 · F4 266 |
| `img_chest_trap` | 16×12 | **new**: trapped chest. Canon tell: **red clasp** (`$E2DD`); otherwise identical to closed | same |
| `img_chest_open` | 16×12 | **new**: opened / empty | same |
| `img_shard` | 8×8 | **new**: memory shard (chests, F3 gift); floats at halfline 340 | F3 x 32 / 280 |
| `img_block` | 16×16 | **new**: falling masonry. Hangs at halfline 60, shakes ±2 px when cracking, falls, lies as rubble. Your `falling_block.s` — **Kimi art integrated (V7 wave 2)** | F4 x 112 · F2 x 172 |
| `img_blade` | 16×16 | **new**: swinging blade, drawn at the swing position (no separate chain). Your `swinging_blade.s` — **Kimi art integrated (V7 wave 2)** | F3, around x 188 |
| `img_hound` | 16×16 | **new**: Castle Hound. Your `castle_hound.s` drops in | F2/F4 patrol |

**Fragment import (wave 2).**
- `tools/mkart.py` uses `docs/visual/sprites/img_<slot>.s` (or `falling_block` / `swinging_blade` / `castle_hound`) whenever the file exists and **exactly** matches the slot size. `dc.w` and `dc.l` lists both work.
- Dry run against `kimi/visual-refinement` @ `ea56c3b`: **21 of 22 drop in**. Only `img_ladder` (16×216 vs 16×244) is skipped.
- None of the new props needs a new OP object. Each is drawn in an object slot its floor leaves idle, so this is not Bob Checkpoint B.

## Gameplay-readability requirements

1. **Collision boxes are narrower than the sprites.**
   - Hero: x+4..x+12, feet x+5..x+11. Enemies: x+3..x+13, top 6 rows (skull: top 4 rows) don't hurt.
   - Keep each silhouette's solid mass inside those boxes.
2. **Stunned guards flicker** (drawn every other 4 frames). No extra frame is needed.
3. **The trapped-lever tell and the heavy guard** are the two "learnable" cues the original relies on. Keep them distinct at 1× scale.
4. **HUD colours** (pips, CPU-drawn) are the castle's memory categories: doors orange `$F8FF`, levers gold `$EAE7`, pace cyan `$2BDD`, guards red `$E2DD`, traps purple `$53C9`. Avoid reusing them for unrelated props.

## Wanted next (no code dependency; drop them in as maps or PNGs)

- Hero walk frames (2–4 × 16×24) and a climb frame.
- Floor-specific wall backdrops. This needs a new background object, so tell Claude the size first; the DRAM budget is fine.
