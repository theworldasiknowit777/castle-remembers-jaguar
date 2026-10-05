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
| `img_ladder` | 16×216 | one tall strip; the game shows the top 200 lines (up-ladder) or 34 lines (hole below the floor) | x = 6 / 152 / 298 |
| `img_door_closed` | 8×40 | wall (blocks walking) | x = 94 / 218 (tight: 75 / 237) |
| `img_door_open` | 8×40 | open frame | same |
| `img_door_brick` | 8×40 | bricked by the castle (cannot open) | same |
| `img_gate` | 16×32 | portcullis; drawn down over the centre ladder, or raised 48 rows when open | x = 152 |
| `img_lever_idle` | 8×12 | gold knob | x = 80 / 232 |
| `img_lever_tell` | 8×12 | **trapped lever**: same lever, wrong-coloured knob (copper). Must stay subtle but learnable | same |
| `img_lever_pulled` | 8×12 | handle down | same |
| `img_lever_sprung` | 8×12 | dud/trap after use: broken | same |
| `img_spike16`, `img_spike24` | 16×8, 24×8 | raised. **Bottom 2 rows are also drawn alone as the retracted state** (keep them a "slot" plate) | various |
| `img_exit` | 32×48 | exit arch, bright: the goal | x = 277 (or 11 when moved left) |
| `img_flame` | 64×16 | eruption. **Bottom 2 rows alone flash as the 0.55 s warning** (keep them embers) | ±32 px around a lever |
| `img_skull` | 16×16 | Sentinel Skull (Bob's) | patrols |
| `img_guard` | 16×24 | Fallen Guard | patrols / chases |
| `img_heavy` | 16×24 | Fallen Guard, armoured (needs two shoves): must read as tougher | |
| `img_watcher` | 16×24 | Stone Watcher, static archer statue that turns to face the hero | |
| `img_wraith` | 16×24 | Judgment Wraith, F5 pursuer | |
| `img_arrow_r`, `img_arrow_l` | 8×2 | arrow, both directions (no hardware flip used) | knee height |
| `img_hero` | 16×24 | Bob's authentic hero (single frame) | |

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
