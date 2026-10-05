# AGENTS.md — Castle Remembers Jaguar · IBM Bob Hackathon
## Continuity State (authoritative)

> **Every new task must begin by running the three commands below and reading this
> file in full before changing anything.**

```powershell
git status
git rev-parse HEAD
git remote -v
```

---

## Repository

| Item | Value |
|---|---|
| Local path | `C:\Users\Owner\.bob\castle-remembers-jaguar` |
| Remote | `https://github.com/theworldasiknowit777/castle-remembers-jaguar.git` |
| Authoritative branch | `main` |
| Known validated HEAD | `499c867daf00681cd16599ae235e13ad2a46c7e5` |
| Pre-Bob baseline tag | `pre-bob-baseline` |
| Baseline commit | `f285ff1bcb2dad8fe97038a71be4a01b5b996335` |

---

## Protected Source

`/original/index.html` is **immutable**.  
Its SHA-256 must continue to match the value stored at project creation.  
**Never modify, move, or delete this file.**

---

## Gates

### Gate 1 — COMPLETE ✅

**Native Windows Jaguar development pipeline proven.**

| Component | Version | Result |
|---|---|---|
| RMAC assembler | 2.5.2 | ✅ assembles 68000 + .objproc |
| RLN linker | 1.7.7 | ✅ links to ABS and COFF |
| Virtual Jaguar emulator | v2.1.3 R5 | ✅ loads COFF, runs at ~59.9 FPS |
| Visible output | solid blue screen (CRY `$FF20`) | ✅ PASS |

Full pipeline: RMAC → RLN → Jaguar COFF/ABS → Virtual Jaguar → visible output.

---

### Gate 2 — COMPLETE / PASS

Phase A — TOM BITMAP rectangle: PASS
Phase B — authentic Castle Remembers hero: PASS
Phase C — Jaguar LEFT/RIGHT controller movement + clamps: PASS

Verified runtime:
- hero visible in Virtual Jaguar
- LEFT movement works
- RIGHT movement works
- clamps verified
- XPOS_START = 257
- XPOS_MIN = 177
- XPOS_MAX = 486

Gate 3 — NOT STARTED

**Goal:** Authentic Castle Remembers hero rendered through TOM Object Processor,
controllable LEFT/RIGHT.

**Sub-goals in order:**
1. Solid BITMAP object visible through TOM OP in Virtual Jaguar
2. Hero pixel data substituted for solid fill
3. LEFT/RIGHT joypad input moves the hero

#### What is proven

- RMAC `.objproc` directive is supported and correctly encodes OP phrases.
- `bitmap` operand order confirmed: `bitmap data_addr, XPOS, YPOS, dwidth, iwidth, height, bpp`
- XPOS encoding verified via flat-binary decode: XPOS appears verbatim in the low byte
  of phrase 1's low 32-bit word. Field moves linearly (0 → 100 → 200) as operand changes.
- Assemble with `-fr` (flat/absolute) for field verification; use `-fb` + RLN for emulator builds.

#### Known failed path — do not repeat

Reading fixed byte offsets from RMAC `-fb` COFF relocatable object files was **invalid**.
Those offsets contained COFF section headers and metadata, not resolved OP phrases.
The probe showed XPOS stuck at 0 regardless of input — this was an artifact of reading
the wrong location, not evidence that `.objproc` ignores XPOS.

#### Current correct path

```
.objproc → BITMAP + STOP in DRAM → assemble (-fb) → link (RLN) → COFF → Virtual Jaguar
```

- Object list must live in Jaguar **main DRAM** (`$000000`–`$1FFFFF`), not TOM GPU local RAM.
- Both the OP object list and bitmap pixel data belong in main DRAM.
- OLP register (`$F00020`) must point to the phrase-aligned object list in DRAM.
- BITMAP object requires 16-byte (double-phrase) alignment.
- VDB/VDE values must be consistent with the BITMAP's YPOS for it to appear on screen.

#### RMAC `.objproc` branch directive — status

The `branch` directive's exact syntax is non-obvious; quick tests showed inconsistent
output. **Do not use `.objproc branch` for Gate 2.**  
Use hand-encoded BRANCH phrases (`dc.l`) if clip objects are needed, or omit clip
branches entirely for the first solid-bitmap test (BITMAP + STOP is sufficient).

#### Architectural rule

Always distinguish **Jaguar main DRAM** from **TOM GPU local RAM** (`$F03000`–`$F03FFF`).
Verify hardware field layouts against authoritative Jaguar documentation
(Tom/Jerry Hardware Reference Manual) — do not infer bit positions from partial decodes.

---

## Stop Conditions

- Every gate ends **PASS** or **BLOCKED** — no partial states.
- On PASS or BLOCKED: document findings, commit, push, verify `local HEAD == remote HEAD`.
- Do not begin the next gate until the current gate is fully committed and pushed.

---

## Do Not Recreate

- The Git repository or its remote
- The `pre-bob-baseline` tag or its commit
- The Gate 1 toolchain setup
- `/original/index.html` or any file under `/original/`
