# Atari Jaguar Native Windows Dev Path — Complete Dev Log

All steps executed natively on Windows 10 x64. No WSL, no cross-compiler, no emulated Linux.

---

## 1. Toolchain Inventory

| Component | Version | Source | Binary path |
|---|---|---|---|
| RMAC assembler | 2.5.2 (Jun 13 2026) | rmac.sourceforge.io | `bin/rmac.exe` |
| RLN linker | 1.7.7 | rmac.sourceforge.io | `bin/rln.exe` |
| Virtual Jaguar emulator | v2.1.3 R5 (GCC/Qt) | OldLincoln fork | `emulator/vjaguar/virtualjaguar.exe` |

---

## 2. Source Files Written

### `hello/hello.s`  — 68000 assembly, 146 lines

Self-contained; no C runtime or SDK dependency.

**What it does:**
1. Sets SR to supervisor mode, IPL=7 (all interrupts masked)
2. Zeros GPU flags and control registers (stops GPU)
3. Zeros DSP flags and control registers (stops DSP)
4. Clears pending CPU interrupt sources via `INT1`
5. Clears Jerry interrupt flags via `J_INT`
6. Writes a STOP object (type=4) at DRAM address `$000000`
7. Points the Object List Pointer (`OLP`) at `$000000`
8. Clears `OBF` and `BORD1`
9. Sets stack pointer to `$1FFFFC` (top of 2 MB DRAM)
10. Reads `CONFIG` bit 4 to detect NTSC vs PAL
11. Programs horizontal/vertical display registers for the detected standard
12. Sets `BG` (background colour) to `$FF20` (bright blue, CRY format)
13. Enables video: `VMODE = CRY16 | VIDEN | BGEN | PWIDTH4`
14. Spins in an infinite branch loop

**Visible result:** solid blue screen at 59.9 FPS in Virtual Jaguar.

### `include/jaguar.inc`  — official Atari hardware equates

Copyright 1992–1995 Atari Computer Corporation; community-distributed reference header.
Defines all Tom, Jerry, GPU, DSP, Blitter, and joystick register addresses.
Not used by `hello.s` directly (all equates are inline), but included for completeness.

---

## 3. Assemble

```powershell
.\bin\rmac.exe -fb -m68000 -o hello\hello.o hello\hello.s
```

| Flag | Meaning |
|---|---|
| `-fb` | BSD object format (required for Jaguar; use `-fa` for Atari ST only) |
| `-m68000` | Target CPU = Motorola 68000 |
| `-o hello\hello.o` | Output object file |

**Output:** `hello/hello.o` — 1033 bytes, BSD a.out relocatable object.

No warnings, no errors.

---

## 4. Link to ABS

```powershell
.\bin\rln.exe -a 802000 -e 802000 -o hello\hello.abs hello\hello.o
```

| Flag | Meaning |
|---|---|
| `-a 802000` | Load address (hex) — Jaguar cartridge ROM mapped at `$802000` |
| `-e 802000` | Entry point (hex) — execution starts at load address |
| `-o hello\hello.abs` | Output file |

**Output:** `hello/hello.abs` — 276 bytes.

---

## 5. Link to COF (COFF, for emulator use)

```powershell
.\bin\rln.exe -a 802000 -e 802000 -c -o hello\hello.cof hello\hello.o
```

Flag `-c` requests COFF output instead of ABS.

**Output:** `hello/hello.cof` — 408 bytes.

---

## 6. Binary Verification

### hello.abs — Jaguar ABS type 1 header

```
Magic:        0x601B   (Jaguar ABS type 1, valid)
Flags:        0x0000
Text size:      0xF0   (240 bytes of 68k machine code)
Data size:    0x0000
BSS size:     0x0000
Entry point:  0x00802000
Text base:    0x00802000  (load address)
```

First instruction at entry (`$802000`):

```
46 FC 27 00  →  MOVE.W #$2700,SR   ✓ (disable all interrupts)
```

### hello.cof — COFF/MC68000 header

```
COFF magic:   0x0150  (MC68000, valid)
Sections:     3  (.text / .data / .bss)
Text size:    0x000000F0  (240 bytes)
Data size:    0x00000000
BSS size:     0x00000000
Entry point:  0x00802000
Text base:    0x00802000
```

Section layout:

| Section | Virtual addr | Size | File offset |
|---|---|---|---|
| `.text` | `$00802000` | 240 B | `0xA8` |
| `.data` | `$008020F0` | 0 B | — |
| `.bss`  | `$008020F0` | 0 B | — |

---

## 7. Emulator Setup

Virtual Jaguar v2.1.3 R5 is a Qt5 application; no install required, runs from the extracted folder.

**One-time BIOS note:** Virtual Jaguar can run without a BIOS ROM but will show a warning on first launch. The emulator proceeds normally and loads the ROM image regardless.

**Load ROM:**  
`Jaguar → Open File (Ctrl+O)` → select `hello/hello.cof` (or `hello.abs`)

---

## 8. Execution Result

Virtual Jaguar launched, loaded `hello.cof`, and executed the 68k code:

- Emulator running at **59.9 FPS** (confirmed in status bar)
- Screen displays **solid blue** (CRY `$FF20`) — exactly the programmed background colour
- No crash, no black screen, no illegal instruction exception

Screenshot captured: `hello/screenshot.png`

---

## 9. File Manifest

```
jaguar-toolchain/
├── bin/
│   ├── rmac.exe              RMAC 2.5.2 assembler (Windows x64)
│   ├── rln.exe               RLN 1.7.7 linker     (Windows x64)
│   ├── rmac-2.5.2-win64.zip  original archive
│   └── rln-1.7.7-win64.zip   original archive
├── emulator/
│   ├── vjaguar-rx-R5.zip     original archive
│   └── vjaguar/
│       └── virtualjaguar.exe Virtual Jaguar v2.1.3 R5
├── hello/
│   ├── hello.s               68000 source (written from scratch)
│   ├── hello.o               BSD object  (1033 bytes)
│   ├── hello.abs             Jaguar ABS  (276 bytes)  ← runs on hardware
│   ├── hello.cof             COFF        (408 bytes)  ← loads in emulator
│   └── screenshot.png        proof of execution (blue screen, 59.9 FPS)
├── include/
│   ├── jaguar.inc            official Atari hardware equates
│   ├── startup.inc           reference startup stub
│   └── videoinit.inc         reference video init equates
└── DEVLOG.md                 this file
```

---

## 10. Reproducible Build Commands

```powershell
cd C:\Users\Owner\.bob\playground\jaguar-toolchain

# Assemble
.\bin\rmac.exe -fb -m68000 -o hello\hello.o hello\hello.s

# Link → ABS (hardware / flash cart)
.\bin\rln.exe -a 802000 -e 802000 -o hello\hello.abs hello\hello.o

# Link → COF (emulator preferred)
.\bin\rln.exe -a 802000 -e 802000 -c -o hello\hello.cof hello\hello.o

# Launch in emulator
Start-Process .\emulator\vjaguar\virtualjaguar.exe
# Then: Jaguar > Open File > hello\hello.cof
```

---

## 11. Key Technical Notes

- **Load address `$802000`:** Jaguar cartridge ROM window starts at `$800000`; `$802000` avoids the first 8 KB which the boot ROM uses for the header/entry vector. Games commonly use `$802000` as their cold start address.
- **CRY colour format:** The Jaguar BG register uses 16-bit CRY (Chroma/Red/Y-luma). `$FF20` maps to a saturated blue in CRY space, visible as a solid blue fill when `BGEN` is active.
- **BGEN mode:** Setting bit 7 of `VMODE` causes the Object Processor to fill every line buffer with the `BG` register value before rendering — the simplest way to get a coloured screen without a bitmap.
- **STOP object:** The Object Processor must have a valid object list even when not rendering sprites. A single STOP object (type 4) at DRAM `$0` with `OLP` pointing there satisfies this constraint.
- **NTSC/PAL detection:** Hardware `CONFIG` register bit 4 is set on NTSC consoles. Separate timing constants are applied for each standard to produce a centred, full-height display.

---

## Phase C — Joystick LEFT/RIGHT Input & Hero Horizontal Movement

### Source: `gate3/gate3.s`

Phase C adds Jaguar controller input on top of the proven Phase B rendering
path. **No rendering code was modified** — the TOM/Object Processor path,
the phrase-0 HEIGHT/DATA blanking refresh, the CLUT, and the pixel data are
all preserved verbatim.

#### Input correction — JOYSTICK register protocol

`JOYSTICK` at `$F14000` is a **16-bit** register. The prior implementation
incorrectly used 32-bit longword reads and tested bits 22/23 (which span both
`JOYSTICK` and `JOYBUTS` as a combined longword — wrong). The corrected
implementation:

1. Writes `$817E` (16-bit word) to `JOYSTICK` to select **Row 0** and enable
   the joypad data outputs for Port 1.
2. Reads `JOYSTICK` back as a 16-bit word.
3. Tests the correct bit positions for the D-pad (active-LOW, 0 = pressed).

#### Jaguar controller matrix — Row 0

`JOY_ROW0 = $817E`

| Bit | Signal | Direction | Active |
|-----|--------|-----------|--------|
| 8   | J8 / Up    | Up    | LOW (0 = pressed) |
| 9   | J9 / Down  | Down  | LOW (0 = pressed) |
| 10  | J10 / Left | **LEFT**  | LOW (0 = pressed) |
| 11  | J11 / Right| **RIGHT** | LOW (0 = pressed) |

Row select value `$817E` decoded:
```
Bit 15   = 1  (joy data enable — must be set to enable outputs)
Bits 14:8 = $01 (Row 0 select; keeps audio mute bit clear)
Bits 7:0  = $7E (output drive enables; keeps audio enabled)
```

#### What Phase C adds / changes

| Symbol | Value | Purpose |
|---|---|---|
| `JOYSTICK` | `$F14000` | Jerry 16-bit joypad register |
| `JOY_ROW0` | `$817E` | Row 0 select — D-pad on Port 1 |
| `HERO_XPOS_ADDR` | `$000100` | DRAM word holding current XPOS |
| `XPOS_START` | `257` | Initial position (NTSC screen centre) |
| `XPOS_MIN` / `XPOS_MAX` | `177` / `700` | Screen edge clamps |
| `XPOS_SPEED` | `2` | Pixel-clocks per frame |
| `PH1_UPPER` | `$4010C000` | Fixed upper bits of PH1_LO |

#### Per-frame loop (blanking window)

```
forever:
  1. wait until VC > 507  (end of active picture)
  2. move.w #$817E,JOYSTICK   (select Row 0, enable outputs)
  3. move.w JOYSTICK,d0       (read Port 1 D-pad, active-LOW)
  4. btst #10,d0  → LEFT  (J10)?  sub #2 from xpos, clamp XPOS_MIN
  5. btst #11,d0  → RIGHT (J11)?  add #2 to xpos,  clamp XPOS_MAX
  6. PH1_LO = PH1_UPPER | (xpos & $FFF); write to OP_LIST+8/12
  7. move.l #PH0_HI,OP_LIST+0  (refresh phrase 0 — unchanged Phase B)
     move.l #PH0_LO,OP_LIST+4
  8. wait until VC < 507  (new frame started)
  9. bra forever
```

#### BITMAP phrase 1 XPOS field

XPOS lives in bits [11:0] of PH1_LO (the low longword of BITMAP phrase 1).
All other PH1_LO bits (DEPTH=4/16bpp, PITCH=1, DWIDTH=4, IWIDTH=4) are
preserved in `PH1_UPPER = $4010C000` and OR'd with the new XPOS each frame.

#### Build commands

```powershell
cd C:\Users\Owner\.bob\playground\jaguar-toolchain

# Assemble
.\bin\rmac.exe -fb -m68000 -o gate3\gate3.o gate3\gate3.s

# Link → COF (emulator)
.\bin\rln.exe -a 802000 r r -e -o gate3\gate3.cof gate3\gate3.o
```

#### Binary metrics

| File | COF size | Text segment | Notes |
|---|---|---|---|
| `gate2\gate2.cof` | 1336 B | `$490` = 1168 B | Phase B baseline |
| `gate3\gate3.cof` | 1440 B | `$4F8` = 1272 B | +104 B controller code |

Zero warnings, zero errors on assemble and link.

#### Gate 2 evidence (Phase B screenshots preserved)

| File | Description |
|---|---|
| `gate2/screenshot_gate2.png` | Gate-2 v1 |
| `gate2/screenshot_gate2_v2.png` | Gate-2 v2 |
| `gate2/screenshot_gate2_v3.jpg` | Gate-2 v3 |
| `gate2/screenshot_gate2_v4.jpg` | Gate-2 v4 |
| `gate2/screenshot_gate2_v5.jpg` | Gate-2 v5 |
| `gate2/screenshot_phaseB.jpg` | Phase B pass |
| `gate2/screenshot_phaseB2.jpg` | Phase B pass 2 |


---

## Gate 3 — First Playable Floor

### Source: `gate3_floor/gate3_floor.s`

Builds directly on the proven Phase C path (`gate3/gate3.s`).
**No gate2/gate3 rendering or controller code was modified.**

#### What Gate 3 adds

| Addition | Detail |
|---|---|
| Castle stone floor BITMAP | 320×8 px CRY16, YPOS row 210, full-width platform |
| Hero YPOS variable | stored at DRAM `$000102` (word, halflines); updated per frame |
| TRANS flag on hero BITMAP | PH1_HI bit 15 (`$00008000`) = phrase bit 47; `$0000` hero pixels are transparent |
| Gravity + floor collision | `yvel += 2` per frame; clamp `ypos = 372` when landing |
| Two-object OP list | floor BITMAP → hero BITMAP → STOP (floor behind hero) |

#### Object list layout (`$004000`)

```
$004000  floor BITMAP phrase 0  PH0_HI=$00800008  PH0_LO=$02020D20  (static, refreshed each blank)
$004008  floor BITMAP phrase 1  PH1_HI=$00000005  PH1_LO=$0140C0B1  (XPOS=177,DEPTH=4,DWIDTH=80)
$004010  hero  BITMAP phrase 0  PH0_HI=$00940008  PH0_LO=dynamic    (YPOS rebuilt each frame)
$004018  hero  BITMAP phrase 1  PH1_HI=$00008000  PH1_LO=dynamic    (XPOS rebuilt; TRANS phrase bit 47)
$004020  STOP  phrase 0         $00000000/$00000004
$004028  STOP  phrase 1         $00000000/$00000000
```

#### DRAM state map

| Address | Symbol | Size | Initial |
|---|---|---|---|
| `$000100` | `HERO_XPOS` | word | 257 (screen centre) |
| `$000102` | `HERO_YPOS` | word (halflines) | 372 (standing on floor) |
| `$000104` | `HERO_YVEL` | signed word (hl/frame) | 0 |
| `$008000` | `PIX_FLOOR` | 5120 bytes | 320×8 CRY16 stone tiles |
| `$009400` | `PIX_HERO`  | 768 bytes | 16×24 CRY16 hero (verbatim gate3) |

#### Floor geometry

- NTSC display rows 0–239; floor top at **row 210**, YPOS halfline = `420`.
- Hero height = 24 rows = 48 halflines; hero YPOS when standing = `420 − 48 = 372`.
- `FLOOR_YPOS = 372` is the clamp value in the physics loop.
- Floor XPOS = 177 (left display edge), width = 320 px → covers hero walk range 177–486.

#### TRANS flag — corrected bit position

The BITMAP object's second phrase (PH1) has FLAGS at the high longword (PH1_HI = phrase bits [63:32]).
TRANS is at **phrase bit 47** = PH1_HI bit 15 → `$00008000`.

Prior draft had `$00000020` (phrase bit 37) which is within the IWIDTH field, not TRANS.

#### D0 construction for dynamic PH0_LO

`MOVE.W` only writes the low 16 bits of D0; the upper 16 bits are not cleared.
Sequence used everywhere a dynamic PH0_LO is built:

```asm
moveq   #0,d0             ; clear full 32 bits
move.w  ypos_hl,d0        ; load YPOS halflines into low word
lsl.l   #3,d0             ; shift into bits[13:3] — LSL.L keeps upper half clean
or.l    #HERO_PH0_LO_MSK,d0  ; merge static LINK/HEIGHT bits
move.l  d0,OP_LIST+n      ; write clean longword
```

`LSL.L` (not `LSL.W`) is mandatory: `LSL.W` shifts only bits [15:0] and leaves bits [31:16] unchanged.

#### Per-frame loop

```
forever:
  1. wait VC > 507        (end of active picture → blanking)
  2. write $817E → JOYSTICK; read back (Row 0 D-pad, active-LOW)
     btst #10,d0 → LEFT?  sub #2 from xpos, clamp XPOS_MIN=177
     btst #11,d0 → RIGHT? add #2 to xpos,  clamp XPOS_MAX=486
     store xpos
  3. yvel += GRAVITY(2); ypos += yvel
     if ypos >= 372: ypos=372, yvel=0   (floor collision)
     store ypos, yvel
  4. rebuild hero PH0_LO = $04060000 | (ypos<<3); write PH0_HI/LO → OP_LIST+16/20
  5. rebuild hero PH1_LO = $4010C000 | (xpos&$FFF); write PH1_HI/LO → OP_LIST+24/28
  6. refresh floor PH0_HI/LO → OP_LIST+0/4  (OP zeroes HEIGHT each frame)
  7. wait VC < 507        (new frame started)
  8. bra forever
```

#### Build commands

```powershell
cd C:\Users\Owner\.bob\playground\jaguar-toolchain

# Assemble
.\bin\rmac.exe -fb -m68000 -o gate3_floor\gate3_floor.o gate3_floor\gate3_floor.s

# Link -> COF (emulator)
.\bin\rln.exe -a 802000 x x -e -o gate3_floor\gate3_floor.cof gate3_floor\gate3_floor.o
```

#### Binary metrics

| File | COF size | Notes |
|---|---|---|
| `gate3\gate3.cof` | 1440 B | Phase C baseline (controller only) |
| `gate3_floor\gate3_floor.cof` | 6712 B | +5272 B: floor pixel data (5120 B) + new code |

Zero warnings, zero errors on assemble and link.

#### Runtime verification — PASS ✅

Tested in Virtual Jaguar v2.1.3 R5, NTSC mode, keyboard controller:

| Check | Result |
|---|---|
| Hero visible at screen centre | ✅ |
| Floor visible at row 210 (stone texture with mortar lines) | ✅ |
| Hero standing on floor surface (YPOS clamp working) | ✅ |
| Z key → hero moves LEFT; hits left clamp at XPOS=177 | ✅ |
| C key → hero moves RIGHT; hits right clamp at XPOS=486 | ✅ |
| No rendering corruption or black screen | ✅ |


---

## Gate 4 — Vertical Slice

### Source: `gate4_slice/gate4_slice.s`

Builds directly on Gate 3 (`gate3_floor.s`). All proven rendering, controller,
and physics code preserved verbatim. Adds jump, an autonomous enemy, and
collision-triggered hero reset.

#### What Gate 4 adds

| Addition | Detail |
|---|---|
| Jump | Row 0 bit 8 (S key in VJ); `yvel = -14` hl/frame when grounded; gravity returns hero to floor |
| Enemy BITMAP | 16×16 CRY16 skull sprite at `PIX_ENEMY ($009000)`; bounces XPOS 177–478 at 2 px-clocks/frame |
| Collision + reset | AABB: `|Δx| < 16` AND `|Δy| < 20` (halflines) → hero snaps to `XPOS_START=257, YPOS=372` |

#### Object list layout (`$004000`)

```
$004000  floor  BITMAP PH0/PH1   (PH0 refreshed each blank; PH1 static)
$004010  enemy  BITMAP PH0/PH1   (PH0 refreshed; PH1_LO dynamic XPOS)
$004020  hero   BITMAP PH0/PH1   (PH0 dynamic YPOS; PH1 dynamic XPOS; TRANS)
$004030  STOP   PH0/PH1
```

Order matters: floor → enemy → hero → STOP draws floor behind enemy behind hero.

#### DRAM state map

| Address | Symbol | Size | Initial |
|---|---|---|---|
| `$000100` | `HERO_XPOS` | word | 257 |
| `$000102` | `HERO_YPOS` | word (halflines) | 372 |
| `$000104` | `HERO_YVEL` | signed word | 0 |
| `$000106` | `ENEMY_XPOS` | word | 350 |
| `$000108` | `ENEMY_DIR` | word (+2 or -2) | +2 |
| `$008000` | `PIX_FLOOR` | 5120 bytes | 320×8 CRY16 stone (verbatim) |
| `$009000` | `PIX_ENEMY` | 512 bytes | 16×16 CRY16 skull sprite |
| `$009400` | `PIX_HERO` | 768 bytes | 16×24 CRY16 hero (verbatim) |

#### Jump logic

```asm
btst    #8,d0           ; Up button, active-LOW
bne.s   .physics        ; not pressed
cmp.w   #FLOOR_YPOS,d2  ; hero must be grounded
bne.s   .physics
tst.w   d3              ; and yvel must be zero
bne.s   .physics
move.w  #JUMP_VEL,d3    ; JUMP_VEL = -14 halflines/frame
```

Double-grounded check (`ypos == FLOOR_YPOS AND yvel == 0`) prevents
double-jumps or air re-triggers.

#### Enemy AI

```
each frame:
  enemy_xpos += enemy_dir
  if enemy_xpos <= ENEMY_XMIN: enemy_xpos = ENEMY_XMIN; enemy_dir = +2
  if enemy_xpos >= ENEMY_XMAX: enemy_xpos = ENEMY_XMAX; enemy_dir = -2
```

#### Collision + reset

```
delta_x = |hero_xpos - enemy_xpos|
delta_y = |hero_ypos - ENEMY_YPOS_HL|
if delta_x < 16 AND delta_y < 20:
    hero_xpos = XPOS_START (257)
    hero_ypos = FLOOR_YPOS (372)
    hero_yvel = 0
```

#### Build commands

```powershell
cd C:\Users\Owner\.bob\playground\jaguar-toolchain

.\bin\rmac.exe -fb -m68000 -o gate4_slice\gate4_slice.o gate4_slice\gate4_slice.s
.\bin\rln.exe -a 802000 r r -e -o gate4_slice\gate4_slice.cof gate4_slice\gate4_slice.o
```

Zero warnings, zero errors on assemble and link.

#### Runtime verification — PASS ✅

Tested in Virtual Jaguar v2.1.3 R5, NTSC mode, keyboard controller:

| Check | Result |
|---|---|
| Hero visible, standing on floor | ✅ |
| Enemy visible, bouncing left/right on floor | ✅ |
| Z = LEFT, C = RIGHT, clamps working | ✅ |
| S = JUMP — hero launches upward and returns to floor | ✅ |
| Hero touches enemy → snaps to centre start position | ✅ |
| Enemy continues moving after hero reset | ✅ |
| No rendering corruption or black screen | ✅ |

---

## Gate 5 — Adaptive Memory: The Castle Remembers

### Source: `gate5_memory/gate5_memory.s`

Builds directly on Gate 4 (`gate4_slice.s`). All Gate 4 code preserved verbatim.
One new system: **side-bias tracking** that persists across respawn and deterministically
alters the enemy's spawn position and speed on the next life.

#### Design

The castle tracks one player tendency per life: which half of the screen the hero
occupies most. On death it uses that record to place the enemy on the side the hero
was hiding, approaching faster than before.

#### New DRAM state

| Address | Symbol | Size | Initial | Purpose |
|---|---|---|---|---|
| `$00010A` | `SIDE_BIAS` | signed word | 0 | Cumulative left/right tendency this life |
| `$00010C` | `DEATH_COUNT` | word | 0 | How many times hero has died this session |

All Gate 4 DRAM (`$000100`–`$000108`) and object list layout unchanged.

#### Per-frame bias update (while hero is alive)

```asm
cmp.w   #SCREEN_MID,d1      ; SCREEN_MID = 332 pixel-clocks
bge.s   .bias_right
sub.w   #1,SIDE_BIAS         ; left of centre -> bias toward left
bra.s   .bias_done
.bias_right:
add.w   #1,SIDE_BIAS         ; right of centre -> bias toward right
```

`SCREEN_MID = 332` is the midpoint of the 177–486 walk range.
Running at 60 fps, 1 second fully left = −60 bias; 1 second fully right = +60.

#### On death sequence

```
1. DEATH_COUNT++
2. adapted_speed = ENEMY_SPEED + DEATH_COUNT  (capped at ADAPT_SPEED_MAX=6)
3. if SIDE_BIAS < 0:  enemy_xpos = ENEMY_XMIN(177);  enemy_dir = +adapted_speed
   if SIDE_BIAS >= 0: enemy_xpos = ENEMY_XMAX(478);  enemy_dir = -adapted_speed
4. SIDE_BIAS = 0
5. hero reset: xpos=257, ypos=372, yvel=0  (identical to Gate 4)
```

#### Speed escalation table

| Death # | Speed |
|---|---|
| 0 (first life) | 2 (base) |
| 1 | 3 |
| 2 | 4 |
| 3 | 5 |
| 4+ | 6 (cap) |

#### Build commands

```powershell
cd C:\Users\Owner\.bob\playground\jaguar-toolchain

.\bin\rmac.exe -fb -m68000 -o gate5_memory\gate5_memory.o gate5_memory\gate5_memory.s
.\bin\rln.exe -a 802000 r r -e -o gate5_memory\gate5_memory.cof gate5_memory\gate5_memory.o
```

Zero warnings, zero errors on assemble and link.

#### Runtime verification — PASS ✅

Tested in Virtual Jaguar v2.1.3 R5, NTSC mode, keyboard controller:

| Check | Result |
|---|---|
| Run 1: enemy starts centre-right, speed 2, normal behaviour | ✅ |
| Hero side-bias recorded during play (left/right half tracking) | ✅ |
| Death/respawn triggers — hero resets to centre | ✅ |
| Run 2: enemy spawns from the side hero was hugging | ✅ |
| Run 2: enemy visibly faster than run 1 | ✅ |
| Same bias pattern produces same spawn side and speed | ✅ |
| All Gate 4 behaviour preserved (Z/C/S/gravity/collision) | ✅ |
| No rendering corruption or black screen | ✅ |

## Gate 6 — Three-Floor Castle

### Source: `gate6_castle/gate6_castle.s`

Builds directly on Gate 5 (`gate5_memory.s`). All Gate 5 systems preserved verbatim.
Adds a three-floor vertical castle layout, ladder zone transitions, a second enemy on
the top floor, and an escape/WIN state with a gold BG flash.

#### What Gate 6 adds

- Three distinct floors all visible simultaneously as stacked horizontal platforms
- Instant grounded-touch ladder transitions between floors
- Enemy2 on Floor 3, hidden while hero is on Floors 1–2, adaptive on entry
- WIN state: gold BG flash (180 frames) then soft-reset to Floor 1
- `FLOOR_NUM`, `ENEMY2_XPOS`, `ENEMY2_DIR`, `WIN_TIMER` added to DRAM
- `do_death` subroutine refactored to adapt both Enemy1 and Enemy2 simultaneously

#### Floor layout (NTSC rows 0–239)

| Floor | Screen row | YPOS_HL | Hero YPOS | Purpose |
|---|---|---|---|---|
| Floor 1 | 210 | 420 | 372 | Choice / Observation |
| Floor 2 | 140 | 280 | 232 | Lever / Escalation |
| Floor 3 | 70 | 140 | 92 | Exit / Judgment |

All three floor BITMAPs share the same `PIX_FLOOR` pixel data (`$008000`).
Floor PH1_LO is identical for all floors — only YPOS and LINK differ in PH0.

#### Ladder zones (grounded = `yvel==0` and `ypos==floor_ypos`)

| Zone | Condition | Result |
|---|---|---|
| F1 → F2 | xpos ≥ 460, grounded on Floor 1 | FLOOR_NUM=2, ypos=232, xpos=177 |
| F2 → F3 | xpos ≤ 194, grounded on Floor 2 | FLOOR_NUM=3, ypos=92, xpos=486 |
| F3 → WIN | xpos ≥ 460, grounded on Floor 3 | WIN_TIMER=180, BG=$CFCB |

The grounded test (`tst.w d3 / bne .no_ladder`) prevents mid-air trigger.

#### Object list layout (`$004000`)

| Offset | Object | PH0_HI | LINK (>>3) |
|---|---|---|---|
| `+$00` | floor1 BITMAP | `$00800008` | `$000802` → floor2 |
| `+$10` | floor2 BITMAP | `$00800008` | `$000804` → floor3 |
| `+$20` | floor3 BITMAP | `$00800008` | `$000806` → enemy1 |
| `+$30` | enemy1 BITMAP | `$00900008` | `$000808` → enemy2 |
| `+$40` | enemy2 BITMAP | `$00900008` | `$00080A` → hero |
| `+$50` | hero BITMAP | `$00940008` | `$00080C` → STOP |
| `+$60` | STOP | `$00000000` | — |

Enemy visibility is controlled by HEIGHT in PH0_LO:
- `E1_PH0_LO` = `$08040BB8` (HEIGHT=16, shown)
- `E1_PH0_LO_HIDE` = `$08000BB8` (HEIGHT=0, hidden)
- `E2_PH0_LO` = `$0A040360` (HEIGHT=16, shown)
- `E2_PH0_LO_HIDE` = `$0A000360` (HEIGHT=0, hidden)

OP skips objects with HEIGHT=0, so hidden enemies consume no scanlines.

#### DRAM state map (extends Gate 5)

| Address | Symbol | Size | Notes |
|---|---|---|---|
| `$000100` | HERO_XPOS | word | |
| `$000102` | HERO_YPOS | word | halflines |
| `$000104` | HERO_YVEL | signed word | |
| `$000106` | ENEMY1_XPOS | word | |
| `$000108` | ENEMY1_DIR | signed word | |
| `$00010A` | SIDE_BIAS | signed word | per-life accumulator |
| `$00010C` | DEATH_COUNT | word | session total |
| `$00010E` | FLOOR_NUM | word | 1, 2, or 3 |
| `$000110` | ENEMY2_XPOS | word | |
| `$000112` | ENEMY2_DIR | signed word | |
| `$000114` | WIN_TIMER | word | counts down from 180 |

#### do_death subroutine

Called via `bsr do_death` on any collision on any floor. Returns with d1/d2/d3/d6
updated to Floor 1 start position so the main loop continues cleanly.

```
1. DEATH_COUNT++
2. adapted_speed = ENEMY_SPEED + DEATH_COUNT  (cap ADAPT_SPEED_MAX=6)
3. if SIDE_BIAS < 0:  both enemies spawn at XMIN(177), dir = +adapted_speed
   if SIDE_BIAS >= 0: both enemies spawn at XMAX(478), dir = -adapted_speed
4. SIDE_BIAS = 0
5. hero reset: xpos=257, ypos=F1_YPOS(372), yvel=0, FLOOR_NUM=1
6. registers d1=257, d2=372, d3=0, d6=1 written back to DRAM
```

#### WIN state flash

```asm
btst    #0,d7           ; alternating gold/black on odd/even countdown frames
beq.s   .win_dark
move.w  #BG_WIN,BG      ; $CFCB — gold
bra.s   .win_tick
.win_dark:
move.w  #BG_VAL,BG      ; $0000 — black
.win_tick:
sub.w   #1,d7
move.w  d7,WIN_TIMER
bne.s   .win_refresh_op ; skip gameplay, keep OP refreshed
; on zero: reset to Floor 1
```

Floor PH0s are still refreshed during WIN countdown (OP zeroes HEIGHT every frame).

#### Build commands

```powershell
cd C:\Users\Owner\.bob\castle-remembers-jaguar\jaguar-toolchain

.\bin\rmac.exe -fb -m68000 -o gate6_castle\gate6_castle.o gate6_castle\gate6_castle.s
.\bin\rln.exe -a 802000 r r -e -o gate6_castle\gate6_castle.cof gate6_castle\gate6_castle.o
```

Zero warnings, zero errors on assemble and link.

#### Runtime verification — PENDING ⏳

Owner must load `gate6_castle.cof` in Virtual Jaguar v2.1.3 R5 (NTSC) and verify:

| Check | Result |
|---|---|
| Hero visible on Floor 1, standing, gravity working | ⏳ |
| Z=LEFT, C=RIGHT, S=JUMP, clamps working | ⏳ |
| Enemy1 bouncing on Floor 1; collision resets hero | ⏳ |
| Walk right edge on Floor 1 (grounded) → Floor 2 transition | ⏳ |
| Floor 2 is enemy-free | ⏳ |
| Walk left edge on Floor 2 (grounded) → Floor 3 transition | ⏳ |
| Enemy2 visible and bouncing on Floor 3 | ⏳ |
| Enemy2 collision resets hero to Floor 1 | ⏳ |
| Walk right edge on Floor 3 (grounded) → gold flash + Floor 1 reset | ⏳ |
| Die repeatedly; speed and spawn side adapt per SIDE_BIAS | ⏳ |
| No corruption, no black screen, stable 59.9 FPS | ⏳ |
---

## Gate 7 — Five-Floor Castle (Claude, gameplay lead) — `claude/gameplay-refinement`

**Source:** `gate7_castle/gate7_castle.s` + generated `gate7_castle/castle_art.inc`
**Binary:** `gate7_castle/gate7_castle.cof`
**Canon:** `original/index.html` (rules summarised from the HTML game, line refs in the
commit message history of this branch).

### What the player gets

One screen per floor; ladders flip between floors (climb up through the ceiling,
or down through a ladder hole in the floor).

| Floor | Role | Contents |
|---|---|---|
| F1 | Choice / Observation | two closed doors (ACT opens) guard the L and R ladders |
| F2 | Lever / Escalation | two levers, a gate over the centre ladder, Sentinel Skull patrol |
| F3 | Choice / Adaptation | doors again, static spikes in both corridors |
| F4 | Lever / Pressure | levers + gate, harsher patrol |
| F5 | Judgment / Exit | Judgment Wraith pursues; exit arch (moves to the left once you favour RIGHT doors and have escaped) |

Death (one touch) ends the run: red pulse, the castle merges what it saw into memory,
rebuilds itself, new run on F1. Escape: gold pulse (Bob's $CFCB), merge with double
weight, rebuild.

### Controls (Virtual Jaguar default keys)

| Key | Pad | Action |
|---|---|---|
| Z / C | Left / Right (J10/J11) | walk |
| S | Up (J8) | jump; at a ladder foot: climb up |
| X | Down (J9) | at a ladder hole: climb down; otherwise ACT |
| L | A (B1, JOYBUTS row 0) | ACT: shove a guard ahead > pull lever > open door |

### Enemies (behaviour; art is Kimi's)

| Enemy | Type | Behaviour |
|---|---|---|
| Sentinel Skull | 0 | patrol baseline (Bob's skull); +2/16 px speed per death, max +8 (Gate 5 lineage) |
| Fallen Guard | 1 | patrol; chases within 81 px when the castle saw you avoid guards |
| Fallen Guard (heavy) | 2 | armour 1: first shove only staggers (0.6 s), second shove stuns |
| Stone Watcher | 3 | static archer, faces you, arrow every 2.4 s at knee height — jump it |
| Judgment Wraith | 4 | F5 pursuer; its patrol covers the ladder top (rush) or the whole floor (wait); armoured (brace 2+) |

Shove = ACT facing a guard within 28 px: stun 3 s (1.2 s after "brace"), push 10 px.
Alarm (alarm lever): every guard on the floor wakes and chases within 190 px at x1.6
(fairness, beyond the original: a guard pinned under the hero stays down, and a stunned
guard gets up after at most 1/3 s, so there is always time to turn and shove).
Speeds keep the original's ratios — even a rushed, alarmed guard is slower than the hero.

### Traps

| Trap | Where | Rule |
|---|---|---|
| Static spikes | F3 corridors (always) | jump them (16 px window; 8 px when widened) |
| Retracting spikes | adaptations on F1/F2/F3/F4/F5 | up 1.0 s (1.3 s for waiters) of every 1.8–2.0 s |
| Eruption | a trapped lever | 0.55 s ember warning, then 1.6 s of flame ±32 px — run |
| Gate slam | lever floors, waiters | gate shuts 5 / 3.5 / 2.5 s after opening; levers reset |

A trapped lever's knob is copper instead of gold (the original's tell).

### The castle remembers (deterministic port of `mergeRun` / `buildPlan`)

Memory counters (x100 fixed point) persist across runs: doors L/R, levers L/R,
pulls, rush/wait, confronted/avoided, trap deaths. Each run end: decay x0.8 (the
death's own category is exempt), add the run x100 (x200 on escape), update pressure
0..3 per category, rebuild. `tier = min(3, 1 + pressure)` once a habit is detected
(`favored()`: total >= 0.9, gap >= 0.9, share >= 60%).

| Habit | Tier 1 | Tier 2 | Tier 3 |
|---|---|---|---|
| Door side P | F1 spikes in P corridor; F3 other door left open (gift); F3 guard in P corridor | F3 P spikes retract; F1 P door moves tight | F1 P-corridor guard; F3 P door bricked |
| Lever side P | F4 P lever is a trap | F2 P lever is a dud | F2 P trap; F4 other lever raises the alarm |
| Rush | guards x1.35 | ambush at the F3 ladder top; Wraith covers F5 ladder | spikes flank the F2 centre ladder |
| Wait | gates slam after 5 s | 3.5 s, spikes stay up longer | 2.5 s; Wraith patrols all of F5 |
| Confront (brace) | shoves stun 1.2 s | Wraith armoured | every guard heavy |
| Avoid (watch) | guards chase | patrols widen | Stone Watcher on F4 |
| Trap deaths | F3 spikes widen | spikes on F4 | spikes by the exit |
| Escapes | — | 1: exit moves away from favoured RIGHT | 2: Stone Watcher guards the exit |

Softlock rule (from the original): only the favoured side / trusted lever is ever
hardened, so the other door and the other lever always work.

**Visible adaptation:** HUD top-left = floors (gold current, grey visited); top-right =
five categories x three pips (orange doors, gold levers, cyan pace, red guards, purple
traps). Entering a floor the castle changed for you pulses the background ember red.

### Verification

| Check | How | Result |
|---|---|---|
| 13 scripted playtests (controls, full escape, retreat, gate, death, shove, all five memory categories, 15-run campaign) | `tools/test_gate7.py` under `tools/jagsim.py` | 13/13 PASS |
| Softlock hunt: 15 consecutive rebuilt castles, random habits | `campaign` scenario | 0 stuck; 13 escapes / 2 deaths across escalating castles |
| 20,000 frames random input, invariants every frame | `tools/soak_gate7.py` | 0 violations |
| CPU budget (pessimistic 18 instr/halfline) | soak probe | logic done ~68 halflines after blank (max 325; deadline 525) |
| Real Virtual Jaguar v2.1.3 R5 | `tools/vj_drive.ps1` + F8 framebuffer shots | F1 → door → ladder → F2 → lever → gate, death → rebuilt castle with HUD pips and adapted spikes; every frame drawn |

### Bugs found in the Gate 6 foundation (fixed in Gate 7; Gate 6 untouched)

1. **Every other frame was blank in Virtual Jaguar.** VJ sets VC bit 11 on alternate
   fields (`jaguar.cpp`, `HalflineCallback`: `vc = lowerField ? 0x0800 : 0`). The raw
   `cmp.w #507,VC` saw "blank" for the whole odd field, so the list was refreshed every
   2nd frame and the game ran at 30 Hz. Fix: `and.w #$07FF` before comparing. The
   harness now models the bit and reproduces Gate 6 as `[0, 3852, 0, 3852, …]` pixels.
2. **XPOS origin.** XPOS 0 is the left edge (Tech Ref p.18; VJ screenshot confirms);
   Gate 6's XPOS_MIN=177 (=HDB1) put the castle's right half off-screen. Gate 7 XORG=0.
3. **Floors 2/3 drawn at the wrong height** (`$0380` = 112 halflines, not 280; `$01B8`
   = 55, not 140). Gate 7 builds every phrase at runtime from symbolic fields.
4. **PIX_ENEMY ($9000) overlapped PIX_FLOOR** ($8000+5120): skull pixels in the floor.
   Gate 7 copies all art to PIXBASE $010000 back to back, no overlaps.
5. **`btst #4,CONFIG` tests $F14002's high byte** (bit 12 of JOYBUTS). Bob's own
   videoinit.inc tests `$F14003`. Works in VJ only because that byte reads $FF. Kept
   verbatim in Gate 7 (protected startup) — Bob to decide.
6. **RMAC has no operator precedence** — `FSPIKE+2*16` assembles as `(FSPIKE+2)*16`.
   Every product in Gate 7 is parenthesised.
7. **Palette:** under VJ's real CRY tables Bob's "steel grey" $CE7B is olive, "shadow"
   $3601 and most hero colours are near-black, and the skull's $F001 is black. Left as
   is (Kimi's area); placeholder art uses colours picked against the real tables.

### Build

```sh
sh tools/build_gate7.sh          # mkart.py -> rmac -> rln (Bob's Gate 6 link line)
python tools/test_gate7.py       # scripted playtests (needs: pip install unicorn pillow)
python tools/soak_gate7.py 20000 1 18
```

```powershell
.\bin\rmac.exe -fb -m68000 -o gate7_castle\gate7_castle.o gate7_castle\gate7_castle.s
.\bin\rln.exe -a 802000 r r -e -o gate7_castle\gate7_castle.cof gate7_castle\gate7_castle.o
```

### Gate 7 wave 2: chests, long ladder, masonry, blade, hound, castle voice

All gameplay-side. **No new OP objects:** each new prop is drawn in an object slot its floor leaves idle.

| Prop | Slot |
|---|---|
| chest | gate slot on F1/F3, door L slot on F2/F4 |
| masonry | door R slot |
| blade | lever L slot |
| gift shard | exit slot |

`NOBJ` (18), the LINK chain and the phrase builder are unchanged.

| Feature | Canon / design | Memory link |
|---|---|---|
| Chests F1–F4 (x 180/261/123/266) | canon: real chest → memory shard; trapped → eruption ("greedy hands"); F3 always real | new category **greed**: opened ≥ 1.5 and > 2× skipped. Tiers trap F4 → F2 → F1. Red-clasp tell |
| Long ladder | canon: door t2, the avoided side's F1 ladder runs to F3, drawn gold; you may step off at F2 | door |
| Gift shard | canon: floats behind the F3 gift door; hop to take | door t1 |
| Falling masonry | Jaguar edition: standing 0.75 s under the cracked slab → 0.5 s shake → drop → rubble 1.5 s → reset | wait t1 (F4), t2 (F2) |
| Swinging blade | Jaguar edition: fixed 2 s pendulum on F3, deadly only low in the swing (36-frame safe window) | rush t1 |
| Castle Hound | Jaguar edition: fast patrol, sniff pause at each end and for 0.75 s when you arrive on its floor (no blind spawn), telegraphed lunge ×1.5; jumpable, **cannot be shoved** | brace t2 (F2), t3 (F4) |
| Castle voice | canon lines in `voicetab`; `VOICE_ID`/`VOICE_T` set by every hint, death, escape, and floor whisper | — |

**Engineering:**
- The state block is now an `equ` chain (784 B). `tools/symbols.py` evaluates it for the test tools, so offsets never drift.
- The ladder table moved to RAM (`LADS`, built by the plan; kind bits 1 up / 2 hole / 4 gold). Only gold ladders pass through a floor, and they end at F3 like the canon one.
- The art region is 37,184 B at `$010000`. `mkart.py` imports Kimi's `docs/visual/sprites` fragments automatically when sizes match.

**New scenarios:**
- `chest_shard`, `greed_memory`, `trapped_chest`
- `long_ladder`, `gift_shard`
- `falling_masonry`, `swinging_blade`, `castle_hound`
- `voice_hooks`

The campaign now opens chests at random.

**Hound fairness and the bot:**
- The hound now also sniffs for 0.75 s when the hero arrives on its floor, so a ladder never delivers the hero onto a hound that is already running at them.
- `jagsim.py` gained `snapshot()`/`restore()`. The bot's hound handling is a look-ahead "careful player": walk on, or wait / step back and then jump, and take the first move that lives, stays on the floor and leaves a safe next 30 frames. At a ladder it waits until a climb is seen to get above the hound's reach.
- `tools/diag_hound.py` replays a run to its first death and rewinds 10–90 frames to check whether any simple input would have lived. Every hound death in the failing runs was avoidable, so these were bot faults, not unfair spawns.
- The bot re-pulls a lever when the wait tier slams the gate (the slam resets the lever).

**Regression (wave 2):**
- 22/22 scenarios.
- Campaign: seed 7 and seed 11 each 14 escapes, 1 death, 0 softlocks.
- Soak: 20,000 frames, no invariant violations; logic finishes at blank+72 halflines median, max 358 of 525.
- COFF guard: OK.

### Gate 7 V6: castle voice + six-category HUD row

Built on Kimi's frozen V6 package:
- `ea56c3b`: font
- `8beafe7`: messages + table
- `b1701f1`: HUD row

Her files are read, never edited: `tools/mkmsg.py` and `tools/mkfont.py` generate `msg_ids.inc`, `messages.inc`, `font*.inc` and `hud_*.inc` (committed, so the build never needs her branch).

**Message system (default build, state only):**
- **Ids:** Kimi's 64 `MSG_*` verbatim, plus 23 `MSGX_*` gameplay-lane lines (canon hint/death text her package doesn't carry).
- **Priority:**
  - 5 death / escape / rebuild
  - 4 observation / whisper
  - 3 floor title
  - 2 gameplay warning
  - 1 interaction prompt
- **Queue:** 6 slots. Warnings and above wait their turn; prompts are re-asserted every frame and dropped when refused.
- **Observations:** canon `describeObservation` (`pick_observation`). Deaths go by cause; escapes go by the top tier in canon category order.
- **Run start:** "…IT HAS WATCHED YOU # TIMES." (not on the first run), then the floor-1 whisper.
- **Floors:** title on first visit per run. Whispers are Kimi's `W_*` (door side, gift/gone door, lever trust/here, rush/wait, brace/watch, trap, chest, exit moved/guarded).
- **Prompts:** open, pull, shove, climb, down, sealed, exit (`prompt_update`).

**HUD row (default build, existing object + buffer):**
- `HUDBUF` was reshaped from 320×6 to 160×12 at x 80, halfline 480 (Kimi's band y 224+).
- Six blocks of 8×8 icon + three 3×3 pips. Lit/dim colours come from her palette; chests are greed green.
- On a tier gain at rebuild, the newest pip rings `HUD_FLASH` for 30 frames.
- Floors and shards sit on a strip underneath.
- Read-only on gameplay state.

**Text band (`-dTEXT_ENABLE`, Bob Checkpoint B):**
- One more OP object (`NOBJ` 19), with `TEXTBUF` at `$01A000` (320×20 CRY16).
- Drawn incrementally: 4 rows cleared or 3 glyphs per frame, never in a HUD-redraw frame. A message types in over about ⅓ s.
- Centred, `#` becomes `MSG_ARG`, relief at (+1,+1).
- Real VJ: titles, prompt, shard warning, death / rebuild / observation / whisper lines, pip update and continued play all seen at 60 FPS.
- See `docs/bob/gate7-v6-checkpoint-b.md`.

**Bugs found by the new tests:**
- The flash ring was drawn one row low (a register reused for the y coordinate).
- The `OBSERVED` screen consumed the guard line's floor `#`.
- `move.w #100,d6` left garbage high bits for `divu`.
- Warnings were dropped under titles.
- A one-shot full-band redraw cost ~3 frames of CPU.

**New scenarios:**
- `msg_width`, `msg_observations`, `msg_rebuild_sequence`, `msg_priority`, `msg_events`, `msg_digits`
- `msg_text_render` (pixel-exact against a Python reference)
- `hud_states` (every category × tier + flash, pixel-exact)
- `msg_no_gameplay_effect` (default vs text build vs HUD-every-frame; settled state identical)

**Regression (V6):**
- 31/31 scenarios.
- Campaign (seed 7): 14 escapes, 1 death, 0 softlocks, run for run identical to wave 2.
- Soak (20,000 frames, no invariant violations):
  - default: logic done at blank+74 / p99 87 / max 463 of 525 halflines
  - text build: 78 / 168 / 466
  - same runs, deaths and final tiers as wave 2
- COFF guard: OK.
- Real VJ: both builds, evidence in `gate7_castle/v6_evidence/`.

**Notes for Kimi (no revision requested in this pass):**
- `hud_icons.s` equate names contain a space (`HUD_DOORS   _LIT`). The generator tolerates it.
- The table's floor-title priority (4) sits above whispers. The production hierarchy puts titles below observations; `msgtab` follows production.
- Action responses (gate shut, empty, …) are `MSGX_*` warnings until her package carries them.
- `img_ladder` is still 16×216 against the 16×244 slot (placeholder kept).

### Gate 7 V6 lock: text band enabled (Bob Checkpoint B passed)

- Bob reviewed `fed2955` and approved the text-object architecture with no required changes.
- The four `TEXT_ENABLE` conditionals are unwrapped (bodies unchanged), so the normal build always has `O_TEXT`, `NOBJ` 19 and `TEXTBUF` `$01A000`. `TEXT=1` is gone from `build_gate7.sh`; the soak expects 19 objects.
- The normal `gate7_castle.cof` (`e607e17`) is byte-identical to the approved `TEXT_ENABLE` build of `fed2955`.
- **Checks on the exact normal build:**
  - COFF guard OK
  - V6 tests 10/10
  - gameplay scenarios 20/20
  - campaign 14/15 escapes, 0 softlocks
  - soak 20,000 frames, no invariant violations, max 466 of 525 halflines
- **Real VJ (59.9–60 FPS):** F1/F2 titles, "L - OPEN", shard, death, OBSERVED/RECONSTRUCTING, floor-2 observation, both whispers, door and pace pips after the rebuild, continued play. Shots in `gate7_castle/v6_evidence/`.

### Gate 7 V7 wave 1: Kimi's enemy art

**Integrated in the existing slots** (same image labels, same `enimg` / `enrows`, same object):

| Slot | Kimi file | Size |
|---|---|---|
| `img_skull` | `sentinel_skull.s` (superseded in wave 2 by `img_skull.s`) | 16×16 |
| `img_guard` | `img_guard.s` | 16×24 |
| `img_heavy` | `img_heavy.s` | 16×24 |
| `img_watcher` | `img_watcher.s` | 16×24 |
| `img_wraith` | `img_wraith.s` | 16×24 |

- Verbatim copies live in `jaguar-toolchain/kimi_sprites/` (blob hashes in its README), so the build never needs her branch.
- `mkart.py` requires them: a missing or wrong-sized file stops the build.
- **No gameplay or architecture change.** The `3e1fc36` source assembled with the new `castle_art.inc` gives the same `gate7_castle.cof` byte for byte. AI, speeds, hitboxes, shove, hound, spawns, memory, object indices, `NOBJ` 19, LINK, buffers and init are untouched.
- **Art region:** +256 B, still below `TEXTBUF` (`$01A000`).

**Showcase test build** (VJ art review only, never shipped):
- `-dSHOWCASE=1 -dSHOW_A=t -dSHOW_B=t` puts enemy types `t` in F1's two idle enemy slots (corridors). This is how the Heavy Guard and Stone Watcher, which need memory tiers, were seen in VJ.
- The hook is assembled out of the normal build.

**Runtime / art mismatches found:**
- **Bob's legacy skull was 8×16 data in a 16×16 slot.** It was 4 longs (8 px) per row, 256 B, but drawn with `OB_W` 4 and `OB_H` 16. So the OP showed pairs of rows side by side and read 256 B past it into the hero art. Kimi's true 16×16 skull fixes this; that's the +256 B.
- **Kimi's skull uses Bob's Gate 3 colours.** `$CE7B` ("steel-grey") and `$3601` render green and dark green through VJ's CRY tables (as the floor slab does), and `$F001` renders black. It is integrated verbatim, as visual authority. Her other four enemies use her VJ-verified palette.
- **The spec's Stone Watcher "turns to face the hero",** but the runtime draws enemies unmirrored, so the bow always faces right. Mirroring would need a new object flag or a second image, which is outside this wave.
- **Sprites have 1–2 blank bottom rows.** Feet sit 1 px above the floor line (2 px for the floating skull and wraith). No clipping.

**VJ (60 FPS)**, evidence in `gate7_castle/v7_evidence/`:
- **Normal build:**
  - F2 skull patrolling past the gate, levers and ladder
  - message band and HUD untouched
  - death, rebuild, whispers
  - no corruption afterwards
- **Showcase builds:** skull + guard, heavy + watcher, wraith + guard; transparency clean; no garbage pixels; on the floor line. A shoved guard reads as the stun flicker next to the open door.

### Gate 7 V7 wave 2: Kimi's runtime corrections + trap and prop art

**Corrections from `b00d520`:**
- `img_skull.s`: steel palette and red eyes, replacing the green `$CE7B` body and black `$F001` eyes. It supersedes `sentinel_skull.s`, which is removed.
- `img_guard.s`, `img_heavy.s`, `img_watcher.s`: grounded on the floor line.
- `img_watcher_l.s`: the left-facing Watcher.

**Watcher facing (integrated):**
- The archer AI already sets `E_DIR` toward the hero every frame, and its arrows fly that way. The enemy draw now swaps `OB_DATA` to `img_watcher_l` when a Watcher's `E_DIR` is negative.
- This is the existing data-pointer mechanism: no new object, `NOBJ`, LINK, buffer or gameplay change. Art +768 B.

**Traps and props integrated in their existing slots:**

| Slot | Kimi file | Size |
|---|---|---|
| `img_spike16` / `img_spike24` | same names | 16×8 / 24×8 |
| `img_flame` (eruption) | `img_flame.s` | 64×16 |
| `img_block` (falling masonry) | `falling_block.s` | 16×16 |
| `img_blade` (swinging blade) | `swinging_blade.s` | 16×16 |
| `img_door_closed` / `img_door_open` / `img_door_brick` | same names | 8×40 |
| `img_gate` (portcullis) | `img_gate.s` | 16×32 |
| `img_lever_idle` / `img_lever_tell` / `img_lever_pulled` / `img_lever_sprung` | same names | 8×12 |
| `img_exit` | `img_exit.s` | 32×48 |
| `img_arrow_l` / `img_arrow_r` | same names | 8×2 |

- `mkart.py` `KIMI_VENDORED` checks every file against its runtime slot, and the build stops on any mismatch.
- **Art region:** `$010000`–`$019540` (38,208 B), 2,752 B below `TEXTBUF`.
- **No gameplay change.** The source diff is the Watcher pointer swap plus the test-only `SHOWCASE` hooks (seeds, start floor). Trap timing, damage, gates, levers, doors, memory, AI and physics are untouched.

**Not integrated (art/runtime mismatches and no-slot assets):**
- **Ladder.** Kimi's `img_ladder.s` is 16×216. The runtime ladder is 16×244: the up-ladder draws 200 rows, up + hole 242, the hole stub 34. A 16×244 ladder (and a gold variant, the long ladder) is required; traversal was not shortened.
- **`flame_hazard.s` (16×16):** there is no runtime slot. The eruption is the 64×16 `img_flame`.
- **Hound, chests, shard, decals, backdrops:** outside this wave.

**Presentation notes:**
- **The masonry hangs at halfline 60, inside the castle-message band.** VJ shows a whisper drawn over the hanging slab. Moving it would change the fall (gameplay); it's for a later layout pass.
- **Arrows pass through a closed door.** This is unchanged gameplay; it is only visible because of the showcase placement.

**Showcase test builds** (`-dSHOWCASE`; never shipped):
- `SHOW_C1/V1`, `SHOW_C2/V2`, `SHOW_PC/P` seed memory as `seed()` does; `SHOW_FLOOR` starts the run on a floor; `SHOW_A/B` place enemy types.
- These put masonry (F4), the blade (F3), the eruption (a trapped F1 chest), the bricked door (F3), the exit (F5) and the Watcher in front of the camera.

**VJ (60 FPS)**, evidence `gate7_castle/v7_evidence/w2_*`:
- **Spikes:** raised spikes and the slot plates.
- **Eruption:** the ember warning, then the full flame.
- **Masonry:** hanging, falling, hit, landed.
- **Blade:** clear of the ladders and doors.
- **Doors:** closed, open, bricked, and the open gift door.
- **Portcullis:** over the centre ladder, and raised after the lever.
- **Levers:** idle, then pulled.
- **Exit arch:** reads as the goal.
- **Ladder:** placeholder, the climb is aligned.
- **Watcher:** faces left, with left-flying arrows readable.

### Gate 7 V7 ladder recovery: Kimi's 16×244 ladders

- **Source:** the recovered package (`ladder_normal_16x244` and `ladder_gold_16x244`, `.s` + `.png`, plus preview and note), vendored unchanged in `kimi_sprites/`. The art was not regenerated.
- **Format finding:** the `.s` files are 4bpp indexed with RGB24 palettes (1,952 B each), not the runtime's direct 16bpp CRY16 words (16 × 244 × 2 = 7,808 B).
- **Conversion:** `mkart.py` decodes the indices (high nibble is the left pixel) and maps each of the 9 used colours to CRY16 with `jagsim.rgb_to_cry`, the same VJ tables as the other Kimi art. Index 0 becomes `$0000`, which is transparent.
- **Checks:**
  - 16×244 is enforced, and the build stops on any mismatch.
  - The `.s` decodes to its PNG with 0 differing pixels (both files).
  - The converted words round-trip to the PNG with identical shape and transparency, and at most 9 per colour channel of quantisation error.
- **No code change.** `gate7_castle.s` is untouched, and the COFF is the same size because the placeholder was already 16×244. Nothing changed in ladder geometry, climb path, collision, OP count, LINK or buffers.
- **VJ (60 FPS):** both variants seen at every draw height, with the hero climbing the gold long ladder F1 → F3.
  - up-ladder, 200 rows (normal F3 left, gold F1 right)
  - through-floor, 242 rows (gold on F2, normal on F3)
  - hole stub, 34 rows (F2 left, F3 centre)
  - Evidence is in `gate7_castle/v7_evidence/ladder_*`.
