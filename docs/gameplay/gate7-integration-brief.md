# Five-Floor Castle — Gameplay Integration Brief

Branch `claude/gameplay-refinement` · source `jaguar-toolchain/gate7_castle/gate7_castle.s`
Lanes: gameplay = Claude · OP / memory map / phrase safety = Bob · visuals = Kimi.
Wave 2 adds chests and greed, the long ladder and gift shard, falling masonry, the
swinging blade, the Castle Hound, and castle-voice state.

## 0. Shared coordinates

- **Horizontal:** screen x = XPOS, 0..319, left edges.
- **Vertical:**
  - The floor surface is halfline 420 on every floor (VJ screen row 194).
  - The hero (16×24) stands with its top at halfline 372.
- **Ladders** (16 wide) at x = 6 (L), 152 (C), 298 (R):
  - *Up-ladder*: halflines 20→420, out through the ceiling.
  - *Hole*: 436→504, under the floor slab.
  - *Long ladder*: both at once, 20→504, drawn gold.
- **Reach:**
  - ACT works within 14 px of an object's centre.
  - Grabbing a ladder needs the hero's centre within 9 px of it.
  - A chest is reached at the hero's x = chest x.
- **Hit boxes:**
  - Hero: body x+4..x+12, feet x+5..x+11.
  - Enemies: x+3..x+13. The top 6 rows are harmless (skull and hound: top 4 rows).
  - Spikes: x+3..x+w−3.
  - Masonry: x+2..x+14.
  - Blade: x+3..x+13.
- **Jump:** peak 72 halflines, 16 frames of air, 32 px of travel.

## 1. Floor-by-floor structure

| Floor | Role (canon) | Fixed contents | What the castle adds as it learns |
|---|---|---|---|
| **F1 Gatehouse** | Choice | Doors L 94 / R 218 hiding ladders L/R. **Chest x=180**, real until greed t3 | **Door t1:** spikes in the favoured corridor (41 / 263). **Door t2:** favoured door tight (75 / 237); the **avoided-side ladder becomes the gold long ladder to F3**. **Door t3:** corridor Fallen Guard. **Greed t3:** chest trapped |
| **F2 Gallery** | Lever | Levers 80 / 232, gate over the C ladder, patrol 100–204. **Chest x=261** | **Lever:** trusted lever dud (t2) or trap (t3). **Rush t3:** spikes at 114 / 190. **Wait:** gate slams after 5/3.5/2.5 s; **masonry over x=172 at t2**. **Brace t2:** patrol becomes the **Castle Hound**. **Watch t2:** patrol widens. **Greed t2:** chest trapped. **Long ladder** passes through on the avoided side (you can step off here) |
| **F3** | Choice II | Doors again; fixed spikes at 55 / 249. **Chest x=123** (always real) | **Door t1:** other door open as a gift **with a memory shard floating behind it** (x 280 / 32, hop to take). **Door t1–2:** corridor guard. **Door t2:** favoured spikes retract. **Door t3:** favoured door bricked. **Rush t1:** **swinging blade** between the C hole and the R door (rest x 188). **Rush t2:** ambush at the ladder top. **Trap t1:** spikes widen. The long ladder lands in the avoided-side corridor |
| **F4 Pressure** | Lever | Levers, gate, patrol 47–257. **Chest x=266** | **Lever:** trusted lever = eruption trap (t1); other lever = alarm (t3). **Wait t1:** **masonry over x=112**. **Brace t3:** patrol becomes a hound. **Watch t3:** Stone Watcher at 52. **Trap t2:** spike at 190. **Greed t1:** chest trapped |
| **F5 Judgment** | Exit | Exit arch x=277 (32×48); Judgment Wraith 180–261 | **Rush t2:** Wraith covers the ladder top. **Wait t3:** whole floor. **Brace t2:** armoured. **Trap t3:** spike by the exit. **1 escape + favours RIGHT:** exit moves left (x 11). **2 escapes:** Stone Watcher at the exit |

**Run length.**
- A clean neutral escape still takes about 13 s (806 frames).
- Chests are optional detours: four chests add about 6 s.
- Adapted castles lengthen runs:
  - the blade waits on F3;
  - masonry blocks loitering;
  - the hound must be jumped.
- The long ladder is the canon *shortcut*: the reward for using the side you avoid.

## 2. Enemy and trap roles

| Name | Memory link | Behaviour | Counter |
|---|---|---|---|
| Sentinel Skull | baseline | patrol; +2/16 px per death | jump or shove |
| Fallen Guard | door / pace / watch | patrol; chases within 81 px after "watch" | shove (3 s stun, 1.2 s after "brace") |
| Fallen Guard, heavy | brace t3 | first shove only staggers (0.6 s) | shove twice |
| Stone Watcher | watch t3 / 2 escapes | static archer, knee-height arrow every 2.4 s | jump the arrow, or shove it |
| Judgment Wraith | F5 always | pursues; patrol shape and armour adapt | shove, slip past |
| **Castle Hound** | **brace t2 (F2), t3 (F4)** | fast patrol (26/16 px, capped below hero speed); sniffs 0.5 s at each end and 0.75 s when the hero arrives on its floor; crouches 10 frames, then lunges ×1.5 at a hero just ahead | **cannot be shoved** ("THE HOUND WILL NOT BE PUSHED."); jump it (16 rows) |
| Spikes | trap / door / pace | static, or up 1.0 s (1.3 s for waiters) of every 1.8–2.0 s | hop |
| Eruption | trapped lever / **trapped chest** | 0.55 s ember warning, then 1.6 s of flame ±32 px | run |
| **Falling masonry** | **wait t1 (F4), t2 (F2)** | stand under the cracked slab 0.75 s: it shakes 0.5 s, then drops; rubble 1.5 s, then it resets | don't loiter under cracks |
| **Swinging blade** | **rush t1 (F3)** | fixed 2 s pendulum (±30 px). Deadly only in the low middle of the swing, about 23 frames per pass, leaving a 36-frame safe window | cross on the back-swing |
| Gate slam | wait | the gate closes N s after opening; pulled levers reset | move |

**Greed (canon chest rule).**
- Greedy means opened ≥ 1.5 and opened > 2 × skipped, where skipped counts chests left shut on floors you stood on.
- The tiers turn F4's chest, then F2's, then F1's into traps; the red clasp is the tell.
- F3's chest is always real.
- A real chest gives a memory shard. Shards show as white pips on the HUD.

## 3. Interaction zones (keep art clear of these)

| Zone | Where | Trigger |
|---|---|---|
| Door | 8×40, top at halfline 340 | ACT within 14 px of x+4. A closed door is a wall |
| Lever | 8×12 at 80 / 232, top 396 | ACT within 14 px of x+4 |
| **Chest** | 16×12 at 180 / 261 / 123 / 266, top 396 | ACT within 14 px of x+8 |
| Ladder foot / hole | ladder x ±9 | S climbs up (blocked by a shut gate: "THE GATE IS SHUT."); X climbs down |
| **Gift shard** | 8×8 at (280 or 32, halfline 340) | touch while hopping |
| Exit | arch centre ±12 | win |
| Safe havens | on any ladder, or inside a ladder hole | no enemy, spike, arrow, eruption, masonry or blade can kill you there |

- **ACT priority:** shove > chest > lever > door. Chest and lever reach zones never overlap.
- **Placement rule kept:** no hazard's lethal zone overlaps a ladder grab, door, lever or chest reach zone.
  - The blade's deadly column (hero x 160–200) sits between the C hole and the R door.
  - The masonry columns (F4 x 112, F2 x 172) sit between the levers and the C ladder.

## 4. Object-slot use: no new OP objects

**Every wave-2 prop is drawn in a slot that floor leaves idle.** Consequences:

- `NOBJ` stays at 18.
- The LINK chain is unchanged.
- No new phrase constants; everything goes through the audited runtime builder.

| Floor type | Idle slots | Wave-2 use |
|---|---|---|
| F1 / F3 (choice) | gate, lever L, lever R, exit | chest → gate slot; blade (F3) → lever L slot; gift shard (F3) → exit slot |
| F2 / F4 (lever) | door L, door R, exit | chest → door L slot; masonry → door R slot |
| F5 | doors, gate, levers | nothing yet |

**What Bob should confirm (no checkpoint is triggered, listed for the final audit):**
- **Art region grows** to 37,184 B. It is still packed and phrase-aligned at `$010000`–`$019140`.
- **State block grows** to 784 B, still within `$001000`.
- **One slot now shows different images at different sizes per floor.** For example, the gate slot draws a 16×12 chest on choice floors. Size and data come from the same per-frame object records.

## 5. Kimi's art: integration status

- **V7 integrated art** (verbatim copies in `jaguar-toolchain/kimi_sprites/`, imported by `tools/mkart.py` into the existing slots, size-checked):
  - **Enemies:** skull, guard, heavy, watcher (both facings), wraith. These are the `b00d520` runtime corrections.
  - **Traps:** spikes 16/24, eruption, falling masonry, swinging blade.
  - **Props:** doors (closed / open / bricked), portcullis, four lever states, exit arch, arrows.
  - **Ladders:** normal and gold, 16×244 (recovered indexed export, converted to CRY16 by `mkart.py`).
- **Still placeholder:**
  - Castle Hound
  - chests and shard
  - decals
  - backdrops (Bob)

`tools/mkart.py` imports Kimi's fragments automatically on merge. A fragment is used only when it exactly matches the slot size; otherwise the generator prints why.

**Accepted formats:**
- `docs/visual/sprites/img_<slot>.s`, or her named designs.
- `dc.w` or `dc.l` lists.

**Dry run against `kimi/visual-refinement` @ `ea56c3b` (her fragments copied in, not committed):**

- **21 of 22 drop in:**
  - doors ×3, gate, levers ×4
  - spike16, spike24, exit, flame
  - guard, heavy, watcher, wraith
  - arrows ×2
  - `falling_block` → `img_block`, `swinging_blade` → `img_blade`, `castle_hound` → `img_hound`
- **Needs Kimi:**
  - `img_ladder` must now be **16×244**. The long ladder runs through the floor (halflines 20→504).
  - New slots:

| Slot | Size | Purpose |
|---|---|---|
| `img_ladder_gold` | 16×244 | canon gold long ladder |
| `img_chest_closed` | 16×12 | real chest |
| `img_chest_trap` | 16×12 | trapped chest; **red clasp tell, `$E2DD`** |
| `img_chest_open` | 16×12 | opened chest |
| `img_shard` | 8×8 | memory shard |

- **Not yet linked:**
  - **Bands and decals:** Checkpoint C / B.
  - **V6 font:** the text is ready, see §6. Rendering is Checkpoint B (buffer choice is Bob's).

## 6. Castle voice and HUD row (V6, text band enabled)

- **Ids:** Kimi's V6 `MSG_*` (0–63, verbatim from `docs/visual/sprites/messages.s`) plus 23 gameplay-lane `MSGX_*` (64–86).
  - `tools/mkmsg.py` generates `gate7_castle/msg_ids.inc` and `messages.inc`.
  - Each `msgtab` entry: priority, frames, line 1, line 2.
- **Priority** (higher replaces lower):
  - 5 death / escape / rebuild
  - 4 observation / whisper
  - 3 floor title
  - 2 gameplay warning
  - 1 interaction prompt
- **Queueing:**
  - A refused or displaced warning or above waits in a 6-slot queue: highest first, FIFO on ties.
  - Prompts are contextual (re-asserted every frame), so they are simply dropped.
- **Events wired:**
  - floor titles on first visit per run
  - prompts: open, pull, shove, climb, down, sealed, exit
  - warnings: gate shut / slam / alarm, bricked, dud, jammed, shard, gift shard, trapped lever / chest, ceiling, heavy, hound
  - death lines per cause
  - rebuild "THE CASTLE OBSERVED YOU / RECONSTRUCTING…"
  - canon observation:
    - death by cause (door / lever side, rush / wait, trap, chest, guard or arrow with floor #)
    - escape by top tier
  - run start "…IT HAS WATCHED YOU # TIME(S)." (not on the first run), then the floor-1 whisper
  - per-floor whispers (Kimi's `W_*`)
  - escape "YOU ESCAPED", then "THE CASTLE FORGETS / …FOR NOW."
- **Same memory and same event give the same id** (tested).
- **`#`** is replaced at draw time by `MSG_ARG`: runs, or floor number.
- **HUD memory row** (Kimi `V6_HUD_MEMORY_ROW.md`, `hud_icons.s` via `tools/mkfont.py`):
  - six 8×8 icons + three 3×3 pips (doors, levers, pace, guards, traps, chests)
  - dim when the tier is 0
  - the newest pip rings in `HUD_FLASH` for 0.5 s after a rebuild raises a tier
  - floors and this run's shards sit on a strip underneath
  - read-only on gameplay state
- **Text rendering** is always on: `O_TEXT`, `NOBJ` 19, `TEXTBUF` `$01A000`. Bob passed Checkpoint B on `fed2955` (`docs/bob/gate7-v6-checkpoint-b.md`).

## 7. Before competition-ready polish

1. **Castle-voice rendering:** done; enabled in the normal build after Bob's Checkpoint B.
2. **Kimi art merge:** 21 slots automatic; the ladder (16×244) and the 6 new slots in §5.
3. **Environment bands** (Bob C).
4. **Hero animation:** owner-gated.
5. **Audio / EEPROM memory:** Bob.

**Deferred low-level items for the final Bob return:**
- VC field-bit mask.
- NTSC/PAL CONFIG byte.
- Final shadow→LIVE validation.

## 8. Regression gates (run after every wave)

`tools/test_gate7.py`:
- the scripted suite;
- the `campaign` 15-run softlock hunt, which now also opens chests at random.

`tools/soak_gate7.py`: the 20,000-frame random-input soak.

Real Virtual Jaguar F8 checks via `tools/vj_drive.ps1`.
