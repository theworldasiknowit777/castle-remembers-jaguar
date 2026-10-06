# Castle Remembers — Agent State

## Current State

| Gate / Phase | Status | Notes |
|---|---|---|
| Gate 1 — hello.s blue screen | ✅ PASS | Solid blue, 59.9 FPS, NTSC/PAL auto-detect |
| Gate 2 — bitmap hero sprite | ✅ PASS | Phase A bitmap PASS |
| Phase B — authentic hero | ✅ PASS | 16×24 CRY16 hero sprite, 11-colour palette |
| Phase C — LEFT/RIGHT + clamps | ✅ PASS | Controller movement, XPOS_MIN/MAX clamped |
| Gate 3 — First Playable Floor | ✅ PASS | Floor + hero + gravity + Z/C walk, clamps |
| Gate 4 — Vertical Slice | ✅ PASS | Jump + enemy + collision/reset — full gameplay loop |
| Gate 5 — Adaptive Memory | ✅ PASS | Side-bias tracking; enemy adapts spawn + speed on respawn |
| Gate 6 — Three-Floor Castle | ⏳ BUILT — awaiting runtime verification | Three floors, two enemies, ladder transitions, WIN state |
| Gate 7 — Five-Floor Castle | ✅ PLAYABLE (branch `claude/gameplay-refinement`) — awaiting Bob low-level audit | Five floors, doors/levers/gates, chests, long ladder, 6 enemy types (incl. Castle Hound), spikes/eruption/masonry/blade, six-category castle memory, castle-voice state; scripted suite + campaign + soak green, VJ-verified |

## Binary safety (read before touching any .cof / .o / .abs)

**Never use PowerShell 5.1 `>` redirection for binary Git output.** Use `git restore`,
a binary-safe copy, or rebuild with RMAC/RLN. On 2026-10-05 a Gate 7 `.cof` written with
`>` became UTF-16 text (header `FF FE`); Virtual Jaguar ran garbage and stopped with
"Illegal instruction at $E00004". `jaguar-toolchain/tools/check_cof.py` now rejects any
`.cof` that does not start `01 50` with entry `$802000`; the Gate 7 build script, the
jagsim harness and `vj_drive.ps1` all run it.

## Gate 2 Summary

- **Phase A bitmap PASS** — Object Processor BITMAP object renders correctly.
  XPOS_START=257, DEPTH=4 (16bpp CRY16), 4 phrases/line.
- **Phase B authentic hero PASS** — 16×24 pixel hand-crafted hero sprite in
  CRY16 format, 11-colour palette. Phrase-0 HEIGHT/DATA blanking refresh loop
  prevents OP from zeroing HEIGHT each frame.
- **Phase C LEFT/RIGHT + clamps PASS** — Jaguar controller input via JOYSTICK
  register ($F14000, 16-bit, Row 0 = $817E). Bit 10 = LEFT (J10), bit 11 =
  RIGHT (J11), active-LOW. Hero X position stored at DRAM $000100 (word).
  Speed = 2 pixel-clocks/frame. Clamps: XPOS_MIN=177 (left edge), XPOS_MAX=486
  (right edge, 16px sprite fits).

## Gate 3 Summary — First Playable Floor ✅ PASS

- **Floor BITMAP** — 320×8 px CRY16 castle stone floor at YPOS row 210
  (halfline 420). Stone colour `$CE7B` (steel-grey), mortar `$3943`, shadow
  `$3601`. DWIDTH=80 phrases/line, XPOS=177.
- **Hero TRANS** — TRANS flag at phrase bit 47 = PH1_HI bit 15 = `$00008000`.
  `$0000` hero pixels let floor and BG show through.
- **Hero YPOS** — stored at DRAM `$000102` (halflines). Rebuilt each frame:
  `moveq #0,d0 ; move.w ypos,d0 ; lsl.l #3,d0 ; or.l mask,d0`.
  `LSL.L` (not `LSL.W`) keeps D0 upper word clean.
- **Gravity + floor collision** — `yvel += 2` per frame; clamp `ypos=372`
  (= 420−48), `yvel=0` on landing. Hero starts standing on floor.
- **Two-object OP list** — floor BITMAP → hero BITMAP → STOP.
  Both phrase-0s refreshed in blanking window (OP zeroes HEIGHT each frame).
- **Runtime verified** — hero visible, floor visible, hero on floor,
  Z=LEFT (XPOS_MIN=177), C=RIGHT (XPOS_MAX=486), no corruption.

## Gate 4 Summary — Vertical Slice ✅ PASS

- **Jump** — Row 0 bit 8 (S key in VJ); `yvel = JUMP_VEL (-14)` when grounded.
  Gravity (`+2 hl/frame`) pulls hero back down; floor clamp at `ypos=372` stops fall.
- **Enemy BITMAP** — 16×16 CRY16 skull sprite at `PIX_ENEMY ($009000)`.
  Third object in OP list (floor → enemy → hero → STOP).
  Bounces between `XPOS=177` and `XPOS=478` at `ENEMY_SPEED=2` px-clocks/frame.
  TRANS flag set; PH0 refreshed every blank window.
- **Collision + reset** — AABB test each frame: `|hero_x − enemy_x| < 16` AND
  `|hero_y − enemy_y| < 20` (halflines) → hero resets to `XPOS_START=257, YPOS=372`.
  Enemy continues moving uninterrupted.
- **Controls** — Z=LEFT, C=RIGHT, S=JUMP (Virtual Jaguar keyboard Row 0).
- **Runtime verified** — hero jumps, enemy bounces, collision resets hero to centre,
  enemy unaffected by reset. No corruption, no black screen.

## Gate 5 Summary — Adaptive Memory ✅ PASS

- **Side-bias tracking** — every frame the hero is alive, `SIDE_BIAS` (signed word at `$00010A`)
  is decremented if `hero_xpos < 332` (left half) or incremented if `>= 332` (right half).
- **On death:**
  1. `DEATH_COUNT` (`$00010C`) incremented.
  2. Adapted speed = `ENEMY_SPEED + DEATH_COUNT`, capped at `ADAPT_SPEED_MAX=6`.
  3. `SIDE_BIAS < 0` (hid left) → enemy spawns at `XPOS=177` (left edge), moves RIGHT at adapted speed.
  4. `SIDE_BIAS >= 0` (hid right) → enemy spawns at `XPOS=478` (right edge), moves LEFT at adapted speed.
  5. `SIDE_BIAS` reset to 0 for new life.
- **Hero reset** — identical to Gate 4: `XPOS_START=257`, `YPOS=372`, `yvel=0`.
- **Deterministic** — same side-bias sign on death always produces same spawn side and speed.
- **Runtime verified** — hugged left wall, died, enemy spawned from LEFT on next life at higher speed. ✅

## Gate 6 Summary — Three-Floor Castle ⏳ BUILT

- **Source:** `jaguar-toolchain/gate6_castle/gate6_castle.s`
- **Binary:** `jaguar-toolchain/gate6_castle/gate6_castle.cof`
- **Status:** Assembled clean. Runtime verification pending (owner must load in Virtual Jaguar).

### Floor Layout (NTSC rows 0–239)

| Floor | Row | YPOS_HL | Hero YPOS (halflines) | Purpose |
|---|---|---|---|---|
| Floor 1 | 210 | 420 | 372 | Choice / Observation |
| Floor 2 | 140 | 280 | 232 | Lever / Escalation |
| Floor 3 | 70 | 140 | 92 | Exit / Judgment |

### Ladder Zones (grounded touch = instant transition)

| Trigger | Condition | Result |
|---|---|---|
| F1 → F2 | `hero_xpos >= 460` while grounded on Floor 1 | Teleport to Floor 2, xpos=177 |
| F2 → F3 | `hero_xpos <= 194` while grounded on Floor 2 | Teleport to Floor 3, xpos=486 |
| F3 → WIN | `hero_xpos >= 460` while grounded on Floor 3 | WIN state |

### WIN State
- BG alternates gold (`$CFCB`) / black every frame for 180 frames (~3 seconds)
- Then soft-reset to Floor 1. `DEATH_COUNT` preserved. `SIDE_BIAS` cleared.

### Enemies
- **Enemy1** — Floor 1 only. Gate 5 side-bias adaptation fully preserved.
- **Enemy2** — Floor 3 only. Spawn side and speed driven by same `SIDE_BIAS`/`DEATH_COUNT`.
- Both enemies hidden (HEIGHT=0 in PH0) when hero is on a floor where they are inactive.
- Floor 2 is enemy-free (quiet escalation floor).

### Object List at `$004000`

| Offset | Object | Links to |
|---|---|---|
| `$004000` | floor1 BITMAP | floor2 |
| `$004010` | floor2 BITMAP | floor3 |
| `$004020` | floor3 BITMAP | enemy1 |
| `$004030` | enemy1 BITMAP | enemy2 |
| `$004040` | enemy2 BITMAP | hero |
| `$004050` | hero BITMAP | STOP |
| `$004060` | STOP | — |

### DRAM State Map

| Address | Symbol | Size |
|---|---|---|
| `$000100` | HERO_XPOS | word |
| `$000102` | HERO_YPOS | word (halflines) |
| `$000104` | HERO_YVEL | signed word |
| `$000106` | ENEMY1_XPOS | word |
| `$000108` | ENEMY1_DIR | signed word |
| `$00010A` | SIDE_BIAS | signed word |
| `$00010C` | DEATH_COUNT | word |
| `$00010E` | FLOOR_NUM | word (1/2/3) |
| `$000110` | ENEMY2_XPOS | word |
| `$000112` | ENEMY2_DIR | signed word |
| `$000114` | WIN_TIMER | word |

### Runtime Verification Checklist (owner to complete)

- [ ] Hero visible on Floor 1, standing on floor, gravity working
- [ ] Z=LEFT, C=RIGHT movement with clamps; S=JUMP
- [ ] Enemy1 bouncing on Floor 1; collision resets hero to Floor 1 centre
- [ ] Walk right to xpos ≥ 460 while grounded → transition to Floor 2 (enemy-free)
- [ ] Walk left to xpos ≤ 194 while grounded on Floor 2 → transition to Floor 3
- [ ] Enemy2 bouncing on Floor 3; collision resets hero to Floor 1
- [ ] Walk right to xpos ≥ 460 while grounded on Floor 3 → gold BG flash → Floor 1 reset
- [ ] Die repeatedly; confirm enemy adapts speed and spawn side each life
- [ ] No corruption, no black screen, stable 59.9 FPS

## Gate 7 Summary — Five-Floor Castle (Claude, gameplay lead)

- **Branch:** `claude/gameplay-refinement` — Bob reserved for low-level audit / final integration.
- **Source:** `jaguar-toolchain/gate7_castle/gate7_castle.s`; art generated by
  `jaguar-toolchain/tools/mkart.py` into `gate7_castle/castle_art.inc` (Kimi's slots:
  `docs/kimi/gate7-art-spec.md`).
- **Build:** `sh jaguar-toolchain/tools/build_gate7.sh` (Bob's rmac/rln lines).
- **Test:** `python jaguar-toolchain/tools/test_gate7.py` (13 scripted playtests on the real
  68000 code via `tools/jagsim.py`), `tools/soak_gate7.py`, `tools/vj_drive.ps1` (real VJ, F8 shots).
- **Controls:** Z/C walk · S jump / climb up · X climb down / ACT · L ACT (open door, pull lever, shove guard).
- **Design + verification:** `jaguar-toolchain/DEVLOG.md` § Gate 7.
- **V6 castle voice + HUD row:** Kimi's `MSG_*` ids, priority queue and canon observations, plus the six-category icon/pip HUD and the castle-voice text band, all in the normal build. Bob passed Checkpoint B on `fed2955` (O_TEXT, `NOBJ` 19, `TEXTBUF` `$01A000`): `docs/bob/gate7-v6-checkpoint-b.md`.
- **Low-level changes needing Bob's sign-off:** `docs/bob/gate7-lowlevel-review.md`
  (VC field-bit mask — fixes 30 Hz flicker also present in Gate 6; shadow list; runtime
  phrase builder; XPOS origin 0; new memory map).

## Source Files

| File | Description |
|---|---|
| `jaguar-toolchain/gate2/gate2.s` | Phase B source (hero sprite, no input) |
| `jaguar-toolchain/gate2/gate2.cof` | Phase B COFF binary |
| `jaguar-toolchain/gate3/gate3.s` | Phase C source (LEFT/RIGHT movement) |
| `jaguar-toolchain/gate3/gate3.cof` | Phase C COFF binary |
| `jaguar-toolchain/gate3_floor/gate3_floor.s` | Gate 3 source (floor + walking) |
| `jaguar-toolchain/gate3_floor/gate3_floor.cof` | Gate 3 COFF binary |
| `jaguar-toolchain/gate4_slice/gate4_slice.s` | Gate 4 source (vertical slice) |
| `jaguar-toolchain/gate4_slice/gate4_slice.cof` | Gate 4 COFF binary |
| `jaguar-toolchain/gate5_memory/gate5_memory.s` | Gate 5 source (adaptive memory) |
| `jaguar-toolchain/gate5_memory/gate5_memory.cof` | Gate 5 COFF binary |
| `jaguar-toolchain/gate6_castle/gate6_castle.s` | Gate 6 source (three-floor castle) |
| `jaguar-toolchain/gate6_castle/gate6_castle.cof` | Gate 6 COFF binary |
| `jaguar-toolchain/gate7_castle/gate7_castle.s` | Gate 7 source (five-floor castle) |
| `jaguar-toolchain/gate7_castle/gate7_castle.cof` | Gate 7 COFF binary |
| `jaguar-toolchain/tools/` | art generator, build script, jagsim harness, playtests, soak, VJ driver |
| `jaguar-toolchain/DEVLOG.md` | Full development log |

## Evidence Files

| File | Description |
|---|---|
| `jaguar-toolchain/gate3/gate2_pass_1_idle.png` | Gate 2 PASS — idle hero |
| `jaguar-toolchain/gate3/evidence_A_right.png` | Phase C — hero moved RIGHT |
| `jaguar-toolchain/gate3/evidence_B_right_clamp.png` | Phase C — RIGHT clamp hit |
| `jaguar-toolchain/gate3/evidence_C_left_clamp.png` | Phase C — LEFT clamp hit |
| `jaguar-toolchain/gate3/evidence_D_idle.png` | Phase C — idle/no input |
| `jaguar-toolchain/gate3/screenshot_phaseC_idle.png` | Phase C idle screenshot |
| `jaguar-toolchain/gate3/screenshot_phaseC_running.png` | Phase C running screenshot |

## Next Steps

Gate 6 runtime verification pending. Owner loads `gate6_castle.cof` in Virtual Jaguar and completes the checklist above.
On PASS: update Gate 6 status to ✅ PASS, commit evidence screenshots, tag `v0.6-gate6`.
