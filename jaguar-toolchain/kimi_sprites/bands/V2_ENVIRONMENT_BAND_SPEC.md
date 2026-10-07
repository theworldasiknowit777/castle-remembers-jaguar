# Castle Remembers — V2 Environment-Band Spec

**Status:** approved direction for production. Backdrop *assets* are produced in the
Kimi lane; runtime integration (new OP object, address allocation) is a **Bob
Checkpoint C** review. Sized against Gate 7 geometry (`claude/gameplay-refinement`,
slot sizes per `docs/kimi/gate7-art-spec.md`). All CRY16 words verified against
Virtual Jaguar's `cry2rgb.h` tables (via `tools/jagsim.py: rgb_to_cry()`).

## 0. Review status (Bob, `docs/bob/gate7-visual-integration-review.md`)

- PIX_FLOOR/PIX_ENEMY overlap: **RESOLVED** in Gate 7 (all art at PIXBASE=`$010000`).
- Environment bands: **FEASIBLE** — OP and bandwidth headroom confirmed.
- V1 sprite palette debt: **CONFIRMED** — `$F001` renders black, `$CE7B` renders
  olive, `$CFCB` renders green. Repaired in production milestone 1; all words in
  this spec are VJ-verified.

## 1. Geometry basis (Gate 7)

| Element | Value |
|---|---|
| Screen | 320×240; floor surface at screen row 194 (halfline 420) |
| Backdrop canvas | rows 0–193 (~180 usable rows) |
| Ladders | x = 6 / 152 / 298, strip 16×216 |
| Doors | x = 94 / 218 (tight: 75 / 237), 8×40, top halfline 340 |
| Gate (portcullis) | x = 152, 16×32, over centre ladder |
| Levers | x = 80 / 232, 8×12, top halfline 396 |
| Exit arch (F5) | x = 277 (or 11), 32×48 |
| Flame warning/eruption | 64×16, ±32 px around a lever |
| Spikes | 16×8 / 24×8; bottom 2 rows = retracted slot |
| Floors | F1 Choice · F2 Lever · F3 Choice+spikes · F4 Lever (harsher) · F5 Battlements/exit |

## 2. Backdrop slot assumptions (art-side only)

- One full-screen wall backdrop per floor: **5 bitmaps, 320×180 px, 16-bit CRY**
  (rows 0–179). Rows 180–193 stay deep-shadow wainscot (part of bitmap or BG colour).
- Width 320 = 80 phrases, multiple of 4 ✓. Fully opaque (backdrop needs no TRANS).
- Provisional DRAM cost: 115,200 B per backdrop; residency strategy (all-resident
  vs swap-on-`enter_floor`) and addressing are **Bob's Checkpoint C decision**.
  Zone B (`$01C000–$1FFBff`, ~1.87 MB) is the intended region.
- Runtime form: one new BITMAP object behind the floor slab, data pointer switched
  per floor (Claude's list insertion point: before `O_LAD0`).

## 3. Shared visual language (all floors)

- **Bands (screen rows):** A 0–47 upper wall/sky · B 48–111 arch & column band ·
  C 112–175 dressing band (banners, torches, alcoves) · D 176–193 wainscot/shadow.
- **Ashlar grid:** 16×8 px courses, 1 px mortar `$8828`, staggered rows; block face =
  base stone, top-left 1 px highlight, bottom-right 1 px shadow.
- **Gameplay clarity rule:** bands C–D keep contrast low behind walk paths; hero and
  enemy silhouettes own the floor line.
- **Recess rule:** doors, levers, ladders, gate and exit get framed recesses
  (darker surround + 1 px highlight lip) so interactables read as set into the wall.
- **HUD quarantine:** `$F8FF` `$EAE7` `$2BDD` `$E2DD` `$53C9` are HUD-only.
  Torch edge `$E7E9` rgb(232,121,30) is near HUD orange — keep torches mid-screen,
  darker, never in the HUD row.
- **Wear kit:** cracks `$9816`; moss `$AB60` at low mortar joints; debris `$98A9`;
  ash `$8860` above sconces. Density varies per floor.

## 4. Verified palette (CRY16 → actual RGB under VJ tables)

| Role | Word | Actual RGB |
|---|---|---|
| Warm stone mid / light / dark | `$9881` / `$98AB` / `$9852` | (128,122,102) / (170,162,135) / (81,78,65) |
| Cool stone mid / light / dark | `$7870` / `$789D` / `$7748` | (100,111,108) / (141,156,151) / (66,64,71) |
| Pale stone mid / light / dark | `$9893` / `$98BD` / `$985C` | (146,140,116) / (188,180,149) / (91,87,72) |
| Solemn blue-grey mid / light / dark | `$6770` / `$67B3` / `$673E` | (88,93,111) / (141,149,178) / (49,51,61) |
| Mortar / deep shadow | `$8828` / `$9816` | (38,39,35) / (21,20,17) |
| Torch core / edge / ember | `$B8FF` / `$E7E9` / `$E578` | (254,207,134) / (232,121,30) / (119,45,15) |
| Banner red / dark / gold trim | `$E397` / `$E35C` / `$C9C5` | (150,33,20) / (91,20,12) / (196,164,78) |
| Wood / dark wood | `$C87A` / `$C84A` | (121,90,48) / (73,54,29) |
| Iron dark / light | `$773A` / `$7776` | (53,52,57) / (109,106,117) |
| Night window / moon | `$3640` / `$77E1` | (25,35,63) / (208,202,224) |
| Moss / bone / ash | `$AB60` / `$98A9` / `$8860` | (74,95,42) / (168,161,134) / (92,95,86) |
| Dawn low / high sky / glow / star | `$B65C` / `$4648` / `$C7DD` / `$77F1` | (91,56,48) / (37,43,71) / (220,143,88) / (223,216,240) |
| Warning red / dark red / copper tell | `$E2DD` / `$E26E` / `$D6BF` | (220,32,29) / (110,16,15) / (198,102,47) |

Note: `$E2DD` doubles as the HUD "guards" red — in world art use it only in small
warning accents away from the HUD row, or prefer `$E26E`.

## 5. Floor 1 — Gatehouse / Choice

| | |
|---|---|
| Role | Introduction; two doors, first castle decision |
| Identity | Grounded, inhabited, worn — the lived-in fortress |
| Stone | Warm `$9881` base, `$98AB` hi, `$9852` sh |
| Band A | Warm ashlar; two small barred night windows `$3640` flanking centre |
| Band B | Round Visigothic arches over door x-positions (`$9852` recess, `$98AB` lip); squat columns at thirds |
| Band C | Two banners `$E397`/`$E35C`/`$C9C5` flanking centre ladder; torch sconces near doors (ash `$8860` above) |
| Band D | `$9852` wainscot; heaviest moss + debris of all floors; worn path under spawn |
| Easter egg | Weathered carving `IBM HACKATHON MMXXVI` in one Band B block, chiselled relief (`$9852` cut, `$98AB` top lip), partially moss-covered |
| Trap tells | None — F1 walls stay clean so later tells stay meaningful |
| Message | "You have been here before." Warm, familiar, shabby |

## 6. Floor 2 — Gallery / Lever

| | |
|---|---|
| Role | First lever/gate puzzle; the castle starts testing |
| Identity | Cool, exposed, tense — open gallery above the gatehouse |
| Stone | Cool `$7870` base, `$789D` hi, `$7748` sh |
| Band A | Colonnade: three tall open arches, night sky `$3640`, moon `$77E1` in one; missing blocks at arch tops |
| Band B | Long unbroken ashlar (exposure); gate shaft recess `$7748` above centre ladder |
| Band C | Lever niches at x 80/232: `$7748` arch + `$773A` iron bracket; one torn banner scrap only, left |
| Band D | `$7748` wainscot, thin moss, scattered debris |
| Trap tells | Trapped-lever niche: one hairline crack `$9816` in the arch lip (learnable) |
| Message | Height and exposure; first "the castle is watching" |

## 7. Floor 3 — Hall of Echoes / Choice II (spikes)

| | |
|---|---|
| Role | Second choice, now punished — static spikes in both corridors |
| Identity | F1's room, decayed and hostile: the castle remembers, in the walls |
| Stone | Warm family again, desaturated by ~15% more mortar/shadow pixels |
| Band A | F1's windows, one bricked up (`$9852` infill) |
| Band B | F1's arches damaged: one broken, fallen voussoir debris below |
| Band C | F1's banners tattered (`$E35C` strips); one torch dead (ember `$E578` only) |
| Band D | Spike-bed recesses `$9816` exactly under spike positions; bone debris `$98A9` |
| Trap tells | Crack clusters radiate from spike positions; bone debris = "something happened here" |
| Message | Visual rhyme with F1 does the storytelling |

## 8. Floor 4 — Vault / Pressure

| | |
|---|---|
| Role | Final lever/gate test, harsher; last barrier before judgment |
| Identity | Severe blue-grey inner vault, ceiling pressing down |
| Stone | Solemn `$6770` base, `$67B3` hi, `$673E` sh |
| Band A | No sky; vault ribs `$673E` converging toward centre |
| Band B | Narrower, taller niches; heavy columns flank the gate shaft |
| Band C | Lever niches iron-bound (`$773A` straps); trap tell escalated to two hairline cracks |
| Band D | `$673E` wainscot, no moss — the deep castle is dead, not aged |
| Trap tells | Ember `$E578` rows near lever niches pre-echo the eruption |
| Message | Held breath; most monochrome floor so F5's sky lands as release |

## 9. Floor 5 — Battlements / Judgment & Escape

| | |
|---|---|
| Role | Finale: wraith pursuit to the exit arch |
| Identity | Open battlements at dawn — exposure, judgment, release |
| Stone | Pale `$9893` base, `$98BD` hi, `$985C` sh |
| Band A | Open sky: `$4648` high → `$B65C` low, dawn glow `$C7DD` on the exit side, stars `$77F1` far side |
| Band B | Crenellation silhouette `$985C` against sky; broken merlon over the exit |
| Band C | Exit recess `$985C`/`$98BD`; arch interior = brightest shape in the game; wraith patrol region backed by plain pale ashlar (dark silhouette reads) |
| Band D | `$985C` wainscot, wind-blown debris, no moss |
| Ladder cue | Final ascent hole rimmed with `$C7DD` dawn spill — climbing toward light |
| Message | The only floor with horizon; escape is literally brighter |

## 10. Traversal / door / lever / trap language

- **Ladders:** wood `$C87A`/`$C84A`; wall shaft darkened in floor shadow family; F5 dawn rim.
- **Doors:** `$C87A` planks, `$773A` straps, per-floor arch recess; bricked variant fills the arch with the floor's own stone (reads as "the castle did this").
- **Levers:** gold knob (idle); trapped = copper `$D6BF` tell + niche hairline crack; pulled = handle down; sprung = broken.
- **Traps:** trap-family sprites unchanged except palette repair; environment adds tells (cracks, debris, embers), never mechanics.
- **Gate:** portcullis `$773A`/`$7776` in a wall-integrated shaft.

## 11. Integration contract

- **Kimi (autonomous):** same-size pixel replacements, palettes, sheets, previews,
  dc.l/include fragments, backdrop art assets (not linked), commits + pushes to
  `kimi/visual-refinement`.
- **Bob Checkpoint A:** dimension/phrase/`$0000`-transparency confirmation per
  replacement slot. **Checkpoint B:** new slots (falling block, swinging blade,
  font). **Checkpoint C:** environment-band runtime integration. **Checkpoint D:**
  pre-hardware pass (CONFIG byte, VC mask).
- **Claude:** gameplay code, integration of delivered fragments, `mkart.py` maps.
- Protected: `img_floor`, `img_skull`, `img_hero` pixel data; phrase encoding;
  memory base addresses; video timing.

## 12. Deferred

- No DRAM assignment, no OP objects, no win-state/whisper rendering (V6 lane),
  no hero animation (owner approval gate), no audio, no EEPROM.
