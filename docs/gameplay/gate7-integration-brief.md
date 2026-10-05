# Five-Floor Castle — Gameplay Integration Brief

Branch `claude/gameplay-refinement` @ `f4a42ed` (local) · source `jaguar-toolchain/gate7_castle/gate7_castle.s`
Lanes: gameplay = Claude · OP / memory map / phrase safety = Bob · visuals = Kimi.

## 0. Shared coordinates (everything below uses these)

- **Screen x = XPOS**, 0..319, left edges. Sprites are 16 px wide unless noted.
- **Floor surface is halfline 420** on every floor. In VJ this is screen row 194.
  - Hero is 16×24 and stands with its top at halfline 372.
  - Rows above the floor, about halfline 40–420, are free wall space for V2 bands.
- **Ladders** (16 wide) sit at x = **6 (L), 152 (C), 298 (R)**.
  - An *up-ladder* spans halflines 20→420 and exits through the ceiling.
  - A *ladder hole* spans 436→504, under the floor slab: the ladder you came up, or the way back down.
- **Reach:** ACT works within 14 px of an object's centre. Grabbing a ladder needs the hero's centre within 9 px of it.
- **Hit boxes:**
  - Hero body x+4..x+12; feet x+5..x+11.
  - Enemies x+3..x+13. Their top 6 rows are harmless (skull: top 4 rows).
  - Spikes hurt from x+3 to x+w−3.
- **Jump:** peak 72 halflines, airtime 16 frames, 32 px of travel. It clears 16- and 24-wide spikes, the skull, and arrows. It does **not** clear a closed door (40 rows tall).

## 1. Floor-by-floor structure

| Floor | Role (canon) | Entry | Up-route | Fixed contents | Adaptive contents (what the castle adds) |
|---|---|---|---|---|---|
| **F1 Gatehouse** | Choice / Observation | start x=152 | L or R ladder, each behind a door | doors L x=94, R x=218 | **door tier 1+:** retracting spikes in the favoured corridor (x=41 / 263). **Tier 2+:** favoured door moves tight (75 / 237). **Tier 3:** corridor Fallen Guard (L 23–57 / R 247–280) |
| **F2 Gallery** | Lever / Escalation | hole L or R | C ladder, gated | levers x=80 / 232; gate over C; Sentinel Skull patrol 100–204 | **lever:** trusted lever becomes a dud (t2) or trap (t3). **Rush t3:** spikes flank the ladder (114, 190). **Watch t2:** patrol widens to 28–276. **Wait:** gate slams after 5 / 3.5 / 2.5 s |
| **F3** | Choice / Adaptation | hole C (x=152) | L or R ladder, behind doors | doors 94 / 218; static spikes both corridors (55, 249; 16 wide) | **door t1:** other door left open (gift). **Door t1–2:** corridor guard (L 33–76 / R 228–271). **Door t2:** favoured spikes retract. **Door t3:** favoured door bricked. **Rush t2:** ambush guard at the ladder top (109–195). **Trap t1:** spikes widen to 24 |
| **F4 Pressure** | Lever / Pressure | hole L or R | C ladder, gated | levers, gate; patrol 47–257 | **lever t1:** trusted lever = trap (eruption). **Lever t3:** other lever = alarm. **Trap t2:** spike at 190 (next to the ladder). **Watch t3:** Stone Watcher at x=52. **Watch t2:** patrol 28–276 |
| **F5 Judgment** | Judgment / Exit | hole C | exit arch (32×48) at x=277 | Judgment Wraith (always pursues), 180–261 | **rush t2:** Wraith covers the ladder top (138–261). **Wait t3:** whole floor (28–276). **Brace t2:** Wraith armoured. **Trap t3:** spike beside the exit. **Escapes ≥1 + favours RIGHT doors:** exit moves left (x=11). **Escapes ≥2:** Stone Watcher guards the exit |

- **Neutral run length:** a clean bot escape takes about 13 s (804 frames). The original's runs were longer; see §5.
- **Death:** one touch. A red pulse, then the castle merges what it saw, rebuilds, and a new run starts on F1.
- **Escape:** gold pulse, double-weight memory merge, rebuild.

## 2. Enemy and trap roles

| Name | Role | Behaviour summary | Readability need |
|---|---|---|---|
| Sentinel Skull | baseline patrol | bounces min↔max; +2/16 px per death (Gate 5 lineage) | low and small, clearly jumpable |
| Fallen Guard | corridor and gallery pressure | patrols; chases within 81 px when the castle saw you *avoid* guards | humanoid; one shove stuns |
| Fallen Guard, heavy | "brace" counter | two shoves (the first only staggers for 0.6 s) | must read as tougher than the plain guard |
| Stone Watcher | ranged defence | static, turns to face you, knee-height arrow every 2.4 s | the arrow must read at 8×2 |
| Judgment Wraith | F5 final pursuer | always chases; patrol shape and armour adapt | distinct from everything below F5 |
| Spikes, static | F3 corridor gate-keeping | always up | |
| Spikes, retracting | adaptive pressure | up 1.0 s (1.3 s for players who wait) of every 1.8–2.0 s | retracted state = bottom 2 rows only |
| Eruption | trapped-lever punishment | 0.55 s ember warning, then 1.6 s of flame, ±32 px around the lever | the warning must be unmistakable |
| Gate slam | anti-waiting | an open gate closes after N seconds; pulled levers reset | |

- **Shove (ACT facing a guard within 28 px):** stun 3 s (1.2 s after the castle learns "brace"), push 10 px.
- **Alarm:** wakes the floor's guards to chase at ×1.6 within 190 px. A guard pinned under the hero stays down, and stunned guards rise after at most 1/3 s. These fairness rules go beyond the original.

## 3. Interaction zones (per floor; all must stay unobstructed by art)

| Zone | Where | Trigger |
|---|---|---|
| Door | 8×40 at the door x, top at halfline 340 | ACT within 14 px of door centre (x+4). Closed door = solid wall for the hero only |
| Lever | 8×12 at x 80 / 232, top at halfline 396 | ACT within 14 px of lever centre (x+4) |
| Ladder foot | ladder x ±9 (centre to centre), standing on the floor | S climbs (blocked while the gate is shut) |
| Ladder hole | ladder x ±9, standing on the floor | X climbs down |
| Exit | arch centre ±12 px, standing on the floor | win |
| Eruption | lever centre ±32, feet within 38 halflines of the floor | death while active |
| Safe spots | inside a ladder hole (hero top below halfline 412) and on any ladder | enemies, spikes, arrows and eruptions can't reach you |

**ACT priority:** shove a guard ahead > pull a lever > open a door. A player near a guard may shove when they meant to pull, so keep guard patrols off the exact lever positions when placing art.

## 4. Where Kimi's art plugs in

- Art is packed by `tools/mkart.py` into `gate7_castle/castle_art.inc`, then copied to DRAM at boot.
- **Slot table:** `docs/kimi/gate7-art-spec.md`.
- **Adding or resizing any object or buffer needs Bob's sign-off** (memory map and OP bandwidth). `build_list` itself handles any object count.

| Kimi asset (kimi/visual-refinement) | Game slot | Fit |
|---|---|---|
| V0 Gatehouse floor, Sentinel Skull | `img_floor`, `img_skull` (pulled from `gate6_castle.s`) | ✅ drops in on merge, same sizes |
| `fallen_guard`, `stone_watcher`, `judgment_wraith` (16×16) | `img_guard` / `img_heavy` / `img_watcher` / `img_wraith` (**16×24**) | ⚠ **size decision needed**, see below |
| `spikes` (16×16) | `img_spike16` / `img_spike24` (16×8, 24×8) | ⚠ the game uses an 8-row spike whose bottom 2 rows are the retracted state. Use rows 8–15 of Kimi's sheet, or tell Claude to raise spike height |
| `flame_hazard` (16×16) | `img_flame` (64×16) | ✅ tile it 4× across. The bottom 2 rows double as the warning |
| `falling_block`, `swinging_blade` (16×16) | none yet | gameplay proposal in §5 |
| `castle_hound` (16×16) | none yet | gameplay proposal in §5 |
| V2 environment bands (walls, arches, banners, doors, gates, F5 sunset) | new background objects *before* `O_LAD0` in the list. Doors and gates reuse their existing slots | **Bob:** OP bandwidth and buffer placement. **Claude:** nothing to change in gameplay if bands stay behind the play objects |

**Size decision (Claude's recommendation): adopt Kimi's 16×16 for all enemies.**

- Gameplay will move to a per-type height table: `enemy_touch` and the Y position computation in `set_objects`.
- 16-row humanoids are jumpable like the skull, which better matches the original (guards were jumpable there).
- The heavy then needs its own 16×16 variant, e.g. shield or darker plate.
- This is a gameplay-only change. Claude makes it once Kimi confirms the size.

**Palette warning for Kimi (with Bob as tie-breaker).** The plan uses `$F001` as the red "warning groove / stud / clasp". Under VJ's own CRY tables (`cry2rgb.h`, mirrored in `tools/jagsim.py`):

| Word | Renders as |
|---|---|
| `$F001` | black (intensity byte 01) |
| `$3601` | black |
| `$E011` | near-black |
| `$CE7B` | olive |

- Red warning tones that read: `$E2DD` (red), `$E26E` (dark red).
- Copper trap tell: `$D6BF`.
- `tools/jagsim.py: rgb_to_cry()` picks words from RGB.

## 5. Missing before competition-ready polish

**Gameplay (Claude, no low-level impact unless noted)**

1. **Chests and the greed category** (canon: one per floor F1–F4; trapped when greedy; red-clasp tell). Needs a chest art slot.
2. **Pacing / floor density.** Runs are short. Canon additions that lengthen floors without new mechanics:
   - the **long ladder** (door tier 2: the avoided-side ladder skips F2);
   - the **gift shard** behind the open F3 door.
3. **New trap families (Kimi's sheet), proposed rules:**
   - *Falling Block*: punishes **waiting**.
     - A cracked ceiling slab above the lever-floor ladder foot drops 0.5 s after you stand under it for over 1.5 s.
     - Telegraph: dust or crack flash. Replaces nothing; added at wait tier 2+.
   - *Swinging Blade*: punishes **rushing**.
     - A pendulum across one F3 corridor on a fixed 2 s rhythm; pass on the back-swing.
     - Added at rush tier 1+ instead of the speed-up only.
   - *Flame*: already the eruption; Kimi's tile is a drop-in.
4. **Castle Hound** (2/4 patrol, low runner): proposed as the "watch" tier-1 replacement for the skull on F2/F4.
   - Fast while patrolling, slow to turn; it can be jumped but not shoved.
   - It gives the avoid-habit its own counter.
5. **Castle voice.** Whispers, floor titles, the title screen and the "castle observed you" rebuild screen are currently only a background pulse.
   - Needs a small font bitmap object (Kimi art + **Bob** OP slot); the text and triggers are Claude's.
6. **Hero animation:** walk, climb and hurt frames (Kimi, owner approval; hero protected).
7. **Audio:** none. The DSP is untouched; **Bob** only.
8. **Memory survives power-off:** the original saves to localStorage; here memory lasts until reset. EEPROM is a **Bob** decision.

**Bob must review before merge** (details: `docs/bob/gate7-lowlevel-review.md`)

- The VC field-bit mask, which fixes VJ's every-other-frame blank. The bug is also present in Gate 6 / `main`.
- Shadow list copied in blank; runtime phrase builder; XPOS origin 0.
- Gate 7 memory map: state `$1000`, objects `$2000`, lists `$4000` / `$4800`, HUD `$F000`, art `$10000+`.
- Left verbatim for Bob's decision: `btst #4,$F14002` tests the high byte (Bob's `videoinit.inc` tests `$F14003`).
- Any V2 band or new trap or enemy buffer: allocation is Bob's.

**Non-negotiable rules for any new content**

- Only the favoured side or trusted lever is ever hardened. The other door and other lever always work, so no castle is unwinnable.
- Every lethal element has a readable telegraph or a fixed rhythm.
- Ladder holes and ladders stay safe havens.
- No new hazard may overlap a ladder foot, lever or door reach zone (§3).
- `tools/test_gate7.py campaign` must stay green, with no softlocks, after every wave.
