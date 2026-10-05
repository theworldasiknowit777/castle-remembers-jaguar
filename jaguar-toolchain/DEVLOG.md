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

