# castle-remembers-jaguar

**The Castle Remembers** — Atari Jaguar port

---

## Project History

**The Castle Remembers** is an original game by Tony Topil, developed as a separate HTML browser game before the documented IBM Bob porting session.
It is a single-file HTML5 browser game in which the castle learns the player's habits and adapts
its layout accordingly — rooms, traps, doors, and levers shift based on observed play style.

The pre-Bob version (save-state version 3, Sep 29 2026) is preserved verbatim in `original/`.
That snapshot predates the documented October 4 IBM Bob session and is the authoritative port baseline. Its September 29 archive date falls inside the hackathon period; it is not evidence of pre-September-28 completion.

The **IBM Bob / Atari Jaguar migration** — porting the game to native Motorola 68000 assembly
for the Jaguar console — constitutes the new hackathon work.

---

## Repository Structure

```
original/           Frozen, verbatim pre-Bob Castle Remembers baseline
                    Do not modify. Authoritative source of truth for the port.

jaguar/             Port planning notes (native gate code is in jaguar-toolchain/)

jaguar-toolchain/   Reproducible native Windows Jaguar development bootstrap
                    RMAC 2.5.2 assembler, RLN 1.7.7 linker, Virtual Jaguar v2.1.3 R5
                    hello.s / hello.abs / hello.cof — Gate 1 proof-of-execution

docs/bob/           IBM Bob development records, session reports, gate summaries
docs/jaguar/        Jaguar hardware reference, migration notes, architecture docs

tests/              Behavioral-equivalence plan; no full parity suite on main
```

---

## Gates

| Gate | Status | Description |
|------|--------|-------------|
| Gate 0 | Preserved | Frozen pre-Bob HTML baseline |
| Gate 1 | Recorded runtime PASS | Native Windows toolchain and blue screen |
| Gate 2 | Recorded runtime PASS | Hero bitmap, authentic sprite and controller movement |
| Gate 3 | Recorded runtime PASS | Floor, gravity, walking and clamps |
| Gate 4 | Recorded runtime PASS | Jump, enemy, collision and reset |
| Gate 5 | Recorded runtime PASS | Side-bias memory; adapted enemy spawn and speed |
| Gate 6 | Built; runtime verification pending | Three floors, two enemies, ladder transitions and WIN |

Statuses above follow `AGENTS.md` and `jaguar-toolchain/DEVLOG.md` on main. The existing `v0.6-gate6` tag is not proof of runtime verification.

Gate 7 is on `claude/gameplay-refinement`, inspected at `7aaaa30cf5a91bdef198e9fcbeae807353836ad6`; it is not merged into main. It has recorded Virtual Jaguar evidence and scripted tests, with broader Bob low-level audit items still open. Gate 7 evidence does not certify Gate 6.

## IBM Bob hackathon entry

**Castle Remembers Jaguar is the entry.** The HTML browser game and Python/Pygame game are separate projects. `original/` is a preserved reference snapshot, not a substitute live demo for Jaguar.

- [Project description, track and stack](docs/submission/PROJECT.md)
- [Dated improvements and Bob attribution](docs/submission/EVIDENCE.md)
- [PDF pitch deck](docs/submission/Castle-Remembers-Jaguar-Pitch.pdf)
- [Testing, recording sequence and live demo requirements](docs/submission/DEMO.md)
- [Submission checklist](docs/submission/CHECKLIST.md)

The YouTube and live Jaguar URLs remain outstanding. No runtime Bob/LLM service or GPU/DSP acceleration is claimed. This documentation update changes no gameplay or baseline files.

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
