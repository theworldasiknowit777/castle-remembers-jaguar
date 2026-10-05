# V2 Visual Wave — Integration Notes (Kimi → Claude / Bob)

Branch: `kimi/visual-refinement` @ `fc12c3b` (pushed to origin).
Everything below is **data + previews only**. Nothing is linked into any build.
No source, OP list, memory map, or gameplay files were touched.

## 1. What was delivered

### Palette repair (fixes V1 defect set)
- `jaguar-toolchain/tools/kpalette.py` — single palette source, every word
  verified against VJ's `cry2rgb.h` (uses `tools/cry_tables.json`).
- Defects fixed: `$F001` renders **black** (not red), `$CE7B` olive, `$CFCB` green.
  Warning red is now `$E26E` (dark, in-world) / `$E2DD` (bright, small use);
  copper tell `$D6BF`.

### Traps — runtime drop-ins (`docs/visual/sprites/`)
| Fragment | Slot | Size | Notes |
|---|---|---|---|
| `img_spike16.s` | `img_spike16` | 16×8 | rows 6–7 alone = retracted slot plate |
| `img_spike24.s` | `img_spike24` | 24×8 | same |
| `img_flame.s` | `img_flame` | 64×16 | 4 jets; rows 14–15 alone = ember warning |
| `falling_block.s` | — new | 16×16 | Checkpoint B (new OP slot) |
| `swinging_blade.s` | — new | 16×16 | Checkpoint B; polished silhouette |
| `flame_hazard.s` | — new | 16×16 | sconce-jet design asset |

### Enemies — runtime drop-ins (16×24, per owner wave sizing)
| Fragment | Slot | Notes |
|---|---|---|
| `img_guard.s` | `img_guard` | helm + tattered red tunic + sword |
| `img_heavy.s` | `img_heavy` | full plate + shield with red studs — reads tougher |
| `img_watcher.s` | `img_watcher` | stone statue, gold eye, bow |
| `img_wraith.s` | `img_wraith` | hooded, legless, red eyes — unmistakable F5 pursuer |
| `castle_hound.s` | — new | 16×16 design asset (Claude's watch tier-1 proposal) |

`img_skull`, `img_hero`, `img_floor` untouched (protected art).

### Props — runtime drop-ins
`img_door_closed/open/brick` (8×40), `img_gate` (16×32),
`img_lever_idle/tell/pulled/sprung` (8×12 — tell = copper knob),
`img_exit` (32×48, brightest shape in the game), `img_arrow_r/l` (8×2),
`img_ladder` (16×216 wood strip).

### Environment bands (`docs/visual/bands/`)
- `img_band_f1..f5.s` — 320×180 opaque CRY16, 115,200 B each.
- F1 gatehouse (warm, banners, torches, **IBM HACKATHON MMXXVI carving** at
  x≈122 y≈42), F2 moonlit gallery, F3 damaged F1 echo, F4 solemn vault,
  F5 dawn battlements with glowing exit arch.
- Backdrop canvas rows 0–179; floor surface row 194 stays clear.

### Adaptation decals (`docs/visual/sprites/decal_*.s`)
Transparent overlays: `decal_crack_16` (16×8), `decal_grate` (16×16),
`decal_chain` (8×16), `decal_bones` (16×8). Composite escalation preview:
`docs/visual/previews/v2_adaptation.png`.

## 2. Previews (all VJ-accurate colour)
`v2_trap_family.png` · `v2_enemy_family.png` · `v2_props.png` ·
`v2_band_f1..f5.png` + `v2_bands.png` · `v2_adaptation.png` ·
`v2_easter_egg_zoom.png`

## 3. What Claude can do now (safe lane)
- Drop any same-size fragment into `mkart.py` maps / `castle_art.inc` and rebuild
  (`sh tools/build_gate7.sh`). Fragment format matches (`dc.w` lists, label = slot).
- Verify against `tools/test_gate7.py campaign` after each drop-in.

## 4. What needs Bob
- **Checkpoint A** per same-size replacement: confirm dimensions, phrase counts,
  `$0000` transparency (all drop-ins use `$0000` only where transparency is meant;
  band bitmaps are fully opaque — asserted in the generator).
- **Checkpoint B**: falling block, swinging blade, flame hazard, castle hound,
  decals — new OP slots + NOBJ.
- **Checkpoint C**: environment bands. Proposed: one opaque BITMAP object behind
  the floor slab, 320×180, pointer switched on `enter_floor`. Residency: 5×115 KB
  all-resident in Zone B, or swap from ROM-side storage — Bob's call.
  Generator asserts: exactly 320×180, zero `$0000` pixels.

## 5. Known soft spots (future polish, optional)
- Watcher's bow is thin at 1× — readable via the gold eye + pedestal instead.
- Guard's sword is minimal at 16 px.
- F5 merlon rhythm is uniform; could add one more broken merlon far-left.
- Hero walk/climb frames remain owner-approval-gated (V7).

## 6. Regenerating
```
cd jaguar-toolchain
python tools/trap_family.py        # traps
python tools/enemy_family_24.py    # enemies
python tools/prop_family.py        # props
python tools/backdrop_family.py    # bands
python tools/adaptation_states.py  # decals + escalation sheet (imports the above)
```
All deterministic (seeded); re-running reproduces the committed files.
