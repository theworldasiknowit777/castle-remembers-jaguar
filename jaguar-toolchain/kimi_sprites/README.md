# Kimi's art (vendored, read-only)

Verbatim copies of Kimi's frozen sprites from `kimi/visual-refinement` @ `b00d520`
(`docs/visual/sprites/`), so the Gate 7 build never needs her branch. Never edit
these; re-copy from her branch if she ships a new version.

`tools/mkart.py` (`KIMI_VENDORED`) imports every file below into its existing slot
in `castle_art.inc`. Each is required and size-checked: a missing or wrong-sized
file stops the build.

| File | Slot | What | Size | Blob |
|---|---|---|---|---|
| `img_skull.s` | `img_skull` | Sentinel Skull (b00d520 steel palette) | 16×16 | `0e84637` |
| `img_guard.s` | `img_guard` | Fallen Guard (b00d520 grounded) | 16×24 | `d51593d` |
| `img_heavy.s` | `img_heavy` | Heavy Fallen Guard (b00d520 grounded) | 16×24 | `f3f6bf0` |
| `img_watcher.s` | `img_watcher` | Stone Watcher, right-facing (b00d520 grounded) | 16×24 | `62cda25` |
| `img_watcher_l.s` | `img_watcher_l` | Stone Watcher, left-facing | 16×24 | `7e0f69c` |
| `img_wraith.s` | `img_wraith` | Judgment Wraith | 16×24 | `0d877c6` |
| `img_spike16.s` | `img_spike16` | spikes, 16 wide | 16×8 | `4899768` |
| `img_spike24.s` | `img_spike24` | spikes, 24 wide | 24×8 | `c7afce2` |
| `img_flame.s` | `img_flame` | eruption (rows 14–15 = warning embers) | 64×16 | `efc4c4c` |
| `falling_block.s` | `img_block` | falling masonry | 16×16 | `bc842c0` |
| `swinging_blade.s` | `img_blade` | swinging blade | 16×16 | `a262b72` |
| `img_door_closed.s` | `img_door_closed` | door, closed | 8×40 | `e1bf0de` |
| `img_door_open.s` | `img_door_open` | door, open | 8×40 | `0817513` |
| `img_door_brick.s` | `img_door_brick` | door, bricked up | 8×40 | `192f182` |
| `img_gate.s` | `img_gate` | portcullis | 16×32 | `fd8bfc0` |
| `img_lever_idle.s` | `img_lever_idle` | lever, idle | 8×12 | `2ae57da` |
| `img_lever_tell.s` | `img_lever_tell` | lever, trapped tell | 8×12 | `3037c32` |
| `img_lever_pulled.s` | `img_lever_pulled` | lever, pulled | 8×12 | `4df1943` |
| `img_lever_sprung.s` | `img_lever_sprung` | lever, sprung | 8×12 | `cbc54a9` |
| `img_exit.s` | `img_exit` | exit arch | 32×48 | `d956d33` |
| `img_arrow_l.s` | `img_arrow_l` | arrow, flying left | 8×2 | `195b8e8` |
| `img_arrow_r.s` | `img_arrow_r` | arrow, flying right | 8×2 | `e397df0` |

**Not integrated yet:**
- `img_ladder.s`: 16×216, but the runtime ladder is 16×244. It draws 200 rows (up-ladder), 242 (up + hole) or 34 (hole stub). A 16×244 asset (and a gold variant) is needed.
- `castle_hound.s`: not in the V7 enemy contract so far.
- `flame_hazard.s`: 16×16, but there is no runtime slot.
- Decals and the 320×180 backdrops: a later wave; backdrops need Bob.

`sentinel_skull.s` (V7 wave 1) is superseded by `img_skull.s` and was removed.
