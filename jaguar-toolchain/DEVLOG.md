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
