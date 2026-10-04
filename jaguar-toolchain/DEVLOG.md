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
