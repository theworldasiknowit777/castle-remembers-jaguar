# castle-remembers-jaguar

**The Castle Remembers** — Atari Jaguar port

---

## Project History

**The Castle Remembers** is an original game by Tony Topil, created *before* this hackathon.
It is a single-file HTML5 browser game in which the castle learns the player's habits and adapts
its layout accordingly — rooms, traps, doors, and levers shift based on observed play style.

The pre-Bob version (save-state version 3, Sep 29 2026) is preserved verbatim in `original/`.
That code predates any IBM Bob or AI involvement and is the authoritative baseline.

The **IBM Bob / Atari Jaguar migration** — porting the game to native Motorola 68000 assembly
for the Jaguar console — constitutes the new hackathon work.

---

## Repository Structure

```
original/           Frozen, verbatim pre-Bob Castle Remembers baseline
                    Do not modify. Authoritative source of truth for the port.

jaguar/             Atari Jaguar port (68000 assembly + GPU/DSP code)
                    GATE 2+ work goes here.

jaguar-toolchain/   Reproducible native Windows Jaguar development bootstrap
                    RMAC 2.5.2 assembler, RLN 1.7.7 linker, Virtual Jaguar v2.1.3 R5
                    hello.s / hello.abs / hello.cof — Gate 1 proof-of-execution

docs/bob/           IBM Bob development records, session reports, gate summaries
docs/jaguar/        Jaguar hardware reference, migration notes, architecture docs

tests/              Behavioral-equivalence tests (Gate 2+)
                    Goal: verify Jaguar port matches original game logic
```

---

## Gates

| Gate | Status | Description |
|------|--------|-------------|
| Gate 0 | ✓ complete | Pre-Bob Castle Remembers baseline preserved |
| Gate 1 | ✓ complete | Native Windows Jaguar toolchain established; blue-screen proof |
| Gate 2 | not started | Port game engine to 68000 assembly |
| Gate 3 | not started | GPU/DSP integration |
| Gate 4 | not started | Behavioral-equivalence validation |

---

## Toolchain (Gate 1)

All tools run natively on Windows 10 x64. No WSL, no cross-compiler.

| Tool | Version | Source |
|------|---------|--------|
| RMAC assembler | 2.5.2 | rmac.sourceforge.io |
| RLN linker | 1.7.7 | rmac.sourceforge.io |
| Virtual Jaguar | v2.1.3 R5 | OldLincoln fork (Qt5) |

### Reproducible build

```powershell
cd jaguar-toolchain

# Assemble
.\bin\rmac.exe -fb -m68000 -o hello\hello.o hello\hello.s

# Link → ABS  (hardware / flash cart)
.\bin\rln.exe -a 802000 -e 802000 -o hello\hello.abs hello\hello.o

# Link → COF  (emulator preferred)
.\bin\rln.exe -a 802000 -e 802000 -c -o hello\hello.cof hello\hello.o

# Launch emulator, then: Jaguar > Open File > hello\hello.cof
Start-Process .\emulator\vjaguar\virtualjaguar.exe
```

**Result:** solid blue screen at 59.9 FPS.  
Screenshot: `jaguar-toolchain/hello/screenshot.png`

---

## License

`original/` — copyright Tony Topil. All rights reserved.  
`jaguar/` — copyright Tony Topil. All rights reserved.  
`jaguar-toolchain/include/jaguar.inc` — copyright 1992–1995 Atari Computer Corporation
(community-distributed reference header; not for redistribution).  
Third-party binaries (RMAC, RLN, Virtual Jaguar) are not committed to this repository;
see `jaguar-toolchain/TOOLCHAIN-SETUP.md` for pinned download instructions.
