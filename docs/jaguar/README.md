# docs/jaguar/ — Jaguar Technical & Migration Documentation

Reference documentation for Atari Jaguar hardware and migration notes
from the HTML5 original to the Jaguar port.

## Contents

| File | Description |
|------|-------------|
| *(Gate 2+)* | 68000 memory map, Object Processor reference |
| *(Gate 2+)* | HTML5 → 68000 migration notes |
| *(Gate 2+)* | Level generator porting notes |

## Hardware Reference Summary

### Memory Map

| Range | Description |
|-------|-------------|
| `$000000–$1FFFFF` | DRAM (2 MB) |
| `$800000–$DFFFFF` | Cartridge ROM |
| `$F00000–$F0FFFF` | Tom (GPU + blitter + OP) registers |
| `$F10000–$F1FFFF` | Jerry (DSP + audio + joystick) registers |

### Key Registers

| Register | Address | Description |
|----------|---------|-------------|
| `OLP` | `$F00020` | Object List Pointer |
| `VMODE` | `$F00028` | Video Mode |
| `BG` | `$F00058` | Background Colour (CRY format) |
| `G_CTRL` | `$F02114` | GPU Control/Status |
| `D_CTRL` | `$F1A114` | DSP Control/Status |
| `CONFIG` | `$F14002` | Hardware config (bit 4 = NTSC) |

### Load / Entry Addresses

- Cartridge ROM base: `$800000`
- Conventional game entry: `$802000`
- DRAM top: `$200000` (SP init: `$1FFFFC`)
