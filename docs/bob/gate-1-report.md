# Gate 1 Report — Native Windows Jaguar Development Path

**Date:** October 4, 2026  
**Status:** ✓ COMPLETE  
**Session:** IBM Bob hackathon, Gate 1

---

## Objective

Establish a complete, reproducible native Windows Jaguar development path:
assemble → link → execute in emulator. Verify with a visible output.

## Tools Obtained

| Tool | Version | Source | Binary |
|------|---------|--------|--------|
| RMAC assembler | 2.5.2 (Jun 13 2026) | rmac.sourceforge.io | pre-built Windows x64 |
| RLN linker | 1.7.7 | rmac.sourceforge.io | pre-built Windows x64 |
| Virtual Jaguar | v2.1.3 R5 (GCC/Qt5) | OldLincoln fork | portable Windows app |

No WSL, no Linux cross-compiler, no Cygwin. All tools run natively on Windows 10 x64.

## Source Written

`jaguar-toolchain/hello/hello.s` — 146-line Motorola 68000 assembly program.  
Written from scratch; no SDK, no C runtime, no startup file dependency.

### What it does

1. SR ← `$2700` (supervisor, IPL=7, all interrupts masked)
2. Stop GPU: zero `G_FLAGS` / `G_CTRL`
3. Stop DSP: zero `D_FLAGS` / `D_CTRL`
4. Clear CPU interrupt sources (`INT1`), Jerry interrupts (`J_INT`)
5. Write STOP object (type=4) at DRAM `$000000`; set `OLP` → `$000000`
6. SP ← `$1FFFFC` (top of 2 MB DRAM)
7. Detect NTSC/PAL via `CONFIG` bit 4; program `HDB1/2`, `HDE`, `VDB`, `VDE`, `VI`
8. Write BG colour `$FF20` (bright blue, CRY format) to `BG` register
9. Enable video: `VMODE = CRY16 | VIDEN | BGEN | PWIDTH4`
10. `bra.s forever` — infinite loop

## Build Commands

```powershell
# Assemble (BSD object format, 68000 CPU)
.\bin\rmac.exe -fb -m68000 -o hello\hello.o hello\hello.s

# Link → Jaguar ABS type 1 (hardware / flash cart)
.\bin\rln.exe -a 802000 -e 802000 -o hello\hello.abs hello\hello.o

# Link → COFF/MC68000 (emulator preferred)
.\bin\rln.exe -a 802000 -e 802000 -c -o hello\hello.cof hello\hello.o
```

## Outputs Verified

| File | Size | Format | Verified |
|------|------|--------|---------|
| `hello.o` | 1,033 B | BSD relocatable object | assembled, no errors |
| `hello.abs` | 276 B | Jaguar ABS type 1, magic `0x601B` | header parsed ✓ |
| `hello.cof` | 408 B | COFF/MC68000, magic `0x0150` | header parsed ✓ |

### Binary verification

**ABS header:**
- Magic: `0x601B` (Jaguar ABS type 1)
- Text size: `0xF0` (240 bytes of 68k machine code)
- Entry: `0x00802000` / Load: `0x00802000`
- First instruction: `46 FC 27 00` = `MOVE.W #$2700,SR` ✓

**COFF header:**
- Magic: `0x0150` (MC68000)
- `.text` section: 240 bytes at `0x00802000`, file offset `0xA8`
- Entry: `0x00802000`

## Execution Result

Virtual Jaguar v2.1.3 R5 loaded `hello.cof`:
- **59.9 FPS** displayed in status bar
- **Solid blue screen** (CRY `$FF20`) rendered correctly
- No crash, no illegal instruction, no black screen

Screenshot: `jaguar-toolchain/hello/screenshot.png`

## Key Technical Notes

- **Load address `$802000`:** Jaguar cartridge ROM window at `$800000`; first 8 KB is
  boot ROM header. Games use `$802000` as cold-start entry.
- **CRY colour `$FF20`:** Jaguar BG register uses 16-bit CRY (Chroma/Red-intensity/Y-luma).
  `$FF20` → saturated blue. BGEN fills each line buffer with this colour.
- **STOP object:** Object Processor needs a valid list even with no sprites.
  Type-4 STOP at DRAM `$0` with `OLP=0` is the minimal valid list.
- **NTSC/PAL:** `CONFIG` register `$F14002` bit 4 set = NTSC, clear = PAL.
