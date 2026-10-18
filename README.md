# The Castle Remembers — Atari Jaguar Port

**The Castle Remembers** is an adaptive-action game being migrated from an
HTML5 prototype to a native Atari Jaguar program written in Motorola 68000
assembly. The castle observes where the player spends time, then uses that
memory to alter enemy respawns and difficulty after a collision.

This repository is the hackathon project for **Building with IBM Bob**. It
preserves the original browser game as an immutable baseline and documents the
new native Jaguar work separately.

## Play it

**Live demo:** https://theworldasiknowit777.github.io/castle-remembers-jaguar/play/ runs the real
Gate 7 Jaguar binary in a browser Jaguar emulator. Arrow keys move, Up jumps or climbs up,
Down climbs down or acts, Z acts (open a door, pull a lever, shove a guard).
The same `.cof` runs in Virtual Jaguar; see `docs/submission/DEMO.md`.

> **Current release state — Gate 6 is built and assembled; its runtime
> verification in Virtual Jaguar is still pending.** The earlier rendering,
> movement, physics, collision, and adaptive-memory gates were runtime
> verified. See [Verification status](#verification-status) before treating
> the Gate 6 binary as a release.

## What is playable

The current native build, `jaguar-toolchain/gate6_castle/gate6_castle.cof`,
implements a three-floor vertical castle:

| Floor | Role | Behaviour |
|---|---|---|
| 1 | Choice / observation | Enemy 1 patrols; the game records the side the player favours. |
| 2 | Quiet escalation | No enemy; a grounded edge transition advances the player. |
| 3 | Exit / judgment | Enemy 2 patrols; reaching the exit triggers a gold win flash and reset. |

On any death, the hero respawns on Floor 1. The game increments a death count,
uses the remembered left/right bias to choose an enemy spawn side, and increases
speed up to a fixed cap. This makes the adaptation deterministic and visible in
a short demo.

## Controls

In Virtual Jaguar's keyboard input mapping:

| Key | Action |
|---|---|
| `Z` | Move left |
| `C` | Move right |
| `S` | Jump while grounded |

The hero is constrained to the display bounds. Ladder transitions occur by
touching the specified edge while grounded: Floor 1 right → Floor 2; Floor 2
left → Floor 3; Floor 3 right → win state.

## Build and run on Windows

The project uses a native Windows Jaguar toolchain: **RMAC 2.5.2**, **RLN
1.7.7**, and **Virtual Jaguar v2.1.3 R5**. The executables are intentionally
not committed. Install them first by following
[jaguar-toolchain/TOOLCHAIN-SETUP.md](jaguar-toolchain/TOOLCHAIN-SETUP.md).

From the repository root:

```powershell
Set-Location jaguar-toolchain

# Assemble the Motorola 68000 source.
.\bin\rmac.exe -fb -m68000 -o gate6_castle\gate6_castle.o gate6_castle\gate6_castle.s

# Link the emulator-loadable COFF binary.
.\bin\rln.exe -a 802000 r r -e -o gate6_castle\gate6_castle.cof gate6_castle\gate6_castle.o

# Start the emulator, then choose Jaguar > Open File and select gate6_castle\gate6_castle.cof.
Start-Process .\emulator\vjaguar\virtualjaguar.exe
```

The committed `gate6_castle.cof` is provided for emulator testing when the
toolchain is unavailable locally. The source entry point and load address are
`$802000`.

## Verification status

| Gate | Scope | Status |
|---|---|---|
| 0 | Pre-Bob browser baseline preserved | Complete |
| 1 | Native Windows toolchain and blue-screen proof | Runtime verified |
| 2 | 16×24 CRY16 hero rendering and controller movement | Runtime verified |
| 3 | Floor, gravity, walking bounds | Runtime verified |
| 4 | Jump, enemy, collision, reset | Runtime verified |
| 5 | Adaptive side-bias tracking and enemy respawn | Runtime verified |
| 6 | Three floors, transitions, second enemy, win state | **Built; runtime verification pending** |

The statuses above follow `AGENTS.md` and `jaguar-toolchain/DEVLOG.md`. The
existing `v0.6-gate6` tag is not proof of runtime verification.

**Gate 7 (the submitted build)** is `jaguar-toolchain/gate7_castle/gate7_castle.cof`,
game code frozen at `88874d8d1fd28925fae7d2416bd2d7dcf63e79cf` and merged into
`main`. It has recorded Virtual Jaguar evidence and scripted tests, with broader Bob
low-level audit items still open. Gate 7 evidence does not certify Gate 6.

### Gate 6 manual test checklist

Run this checklist in Virtual Jaguar before release:

1. Confirm the hero appears on Floor 1, stands on the floor, and jumps/lands correctly.
2. Confirm `Z`/`C` movement and both horizontal bounds.
3. Confirm Enemy 1 patrols on Floor 1 and collision resets the hero.
4. Walk right on Floor 1 while grounded to enter enemy-free Floor 2.
5. Walk left on Floor 2 while grounded to enter Floor 3.
6. Confirm Enemy 2 patrols on Floor 3 and its collision resets the hero to Floor 1.
7. Walk right on Floor 3 while grounded; confirm the gold/black win flash and reset.
8. Die repeatedly after favouring each side; confirm spawn side and speed adapt.
9. Confirm no visual corruption or black screen and stable 59.9 FPS.

Detailed gate design, assembly decisions, and prior runtime evidence are in
[jaguar-toolchain/DEVLOG.md](jaguar-toolchain/DEVLOG.md) and
[AGENTS.md](AGENTS.md).

## Project history and scope

**The Castle Remembers** is an original game by Tony Topil, developed as a
separate HTML browser game before the documented IBM Bob porting session. It is
a single-file HTML5 browser game in which the castle learns the player's habits
and adapts its layout accordingly—rooms, traps, doors, and levers shift based
on observed play style.

The pre-Bob version (save-state version 3, September 29, 2026) is preserved
verbatim in [`original/`](original/). That snapshot predates the documented
October 4 IBM Bob session and is the authoritative port baseline. Its September
29 archive date falls inside the hackathon period; it is not evidence of
pre-September-28 completion.

The IBM Bob / Atari Jaguar migration—porting the game to native Motorola 68000
assembly for the Jaguar console—constitutes the new hackathon work. Full
browser-to-Jaguar behavioural equivalence remains future work; the existing
`tests/` directory documents that planned harness rather than a completed
automated test suite.

## IBM Bob hackathon entry

**Castle Remembers Jaguar is the entry.** The HTML browser game and
Python/Pygame game are separate projects. `original/` is a preserved reference
snapshot, not a substitute live demo for Jaguar.

- [Project description, track and stack](docs/submission/PROJECT.md)
- [Dated improvements and Bob attribution](docs/submission/EVIDENCE.md)
- [PDF pitch deck](docs/submission/Castle-Remembers-Jaguar-Pitch.pdf)
- [Testing, recording sequence and live demo requirements](docs/submission/DEMO.md)
- [Submission checklist](docs/submission/CHECKLIST.md)

The YouTube and live Jaguar URLs remain outstanding. No runtime Bob/LLM service
or GPU/DSP acceleration is claimed. This documentation update changes no
gameplay or baseline files.

## IBM Bob contribution

IBM Bob was used in the development workflow to investigate the unfamiliar
Jaguar environment, establish the Windows build path, reason through low-level
Tom/Jerry and Object Processor setup, and document repeatable build and
verification steps. The audit trail includes:

- [Gate 1 report](docs/bob/gate-1-report.md): the native toolchain, hardware
  initialization, binary-format checks, and emulator proof.
- [Development log](jaguar-toolchain/DEVLOG.md): subsequent rendering, input,
  physics, collision, adaptive-memory, and three-floor implementation work.
- [Original baseline notes](original/README.md): provenance showing what
  existed before the IBM Bob hacking period.

## Repository layout

```text
original/            Immutable pre-Bob HTML5 baseline
jaguar/              Jaguar-port planning notes
jaguar-toolchain/    68000 source, build outputs, setup guide, and dev log
  gate6_castle/      Current three-floor COFF build
docs/bob/            IBM Bob development records
docs/jaguar/         Hardware and migration notes
docs/submission/     Submission materials and evidence
tests/               Planned behavioural-equivalence test area
```

## License and third-party tools

`original/` and `jaguar/` are copyright Tony Topil. The Atari header reference
in `jaguar-toolchain/include/jaguar.inc` is copyright Atari Computer
 Corporation. RMAC, RLN, and Virtual Jaguar are not redistributed here; see the
 toolchain setup guide for their sources and installation instructions.
