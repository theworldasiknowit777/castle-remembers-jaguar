# Gate 7 — Low-Level Integration Review & Visual Readiness Brief

**Reviewed by:** Bob  
**Date:** 2025  
**Branches audited:** `claude/gameplay-refinement @ f4a42ed`, `kimi/visual-refinement`  
**Scope:** Memory safety, OP safety, integration gates only. No gameplay redesign. No art direction.

---

## 1. Full DRAM Memory Map — Gate 7

| Range | Size | Owner / Use | Status |
|---|---|---|---|
| `$000000` | 8 B | Bob's startup STOP phrase | ✅ PASS |
| `$001000 – $001293` | 660 B | Game state block (`a5` base), 165 word offsets | ✅ PASS |
| `$002000 – $00211F` | 288 B | Object records — 18 × 16 bytes | ✅ PASS |
| `$002120 – $003FFF` | ~7 KB | **Unallocated — free** | ✅ FREE |
| `$004000 – $00412F` | 288 B | LIVE OP list (OLP word-swap, Bob's verbatim) | ✅ PASS |
| `$004130 – $0047FF` | ~1.7 KB | Unallocated | ✅ FREE |
| `$004800 – $00492F` | 288 B | SHADOW list (next-frame staging) | ✅ PASS |
| `$004930 – $00EFFF` | ~43 KB | **Unallocated — Zone C free** | ✅ FREE |
| `$00F000 – $00FEFF` | 3,840 B | HUD bitmap 320×6 CRY16, CPU-drawn | ✅ PASS |
| `$00FF00 – $00FFFF` | 256 B | Unallocated tail | ✅ FREE |
| `$010000 – $01653F` | 25,920 B | PIXBASE art block — 22 images, phrase-aligned (§2) | ✅ PASS |
| `$016540 – $1FFBff` | ~1.9 MB | **Unallocated — Zone A/B, vast free space** | ✅ FREE |
| `$1FFFFC` | 4 B | Stack pointer (Bob) | ✅ PASS |

> **PIX_FLOOR / PIX_ENEMY overlap: CONFIRMED RESOLVED.**  
> Gate 6 placed `PIX_ENEMY=$009000` inside `PIX_FLOOR=$008000+5120` (floor extends to `$009400`).  
> Gate 7 eliminates both constants. All art lives at `PIXBASE=$010000`. No overlap.

---

## 2. PIXBASE Art Buffer Detail

Computed from `castle_art.inc` on `claude/gameplay-refinement`. Each entry phrase-aligned (8-byte boundary). CRY16 = 2 bytes/pixel.

| Symbol | Dimensions | DRAM Start | DRAM End | Bytes | Notes |
|---|---|---|---|---|---|
| `img_floor` | 320×8 | `$010000` | `$0113FF` | 5,120 | Bob's authentic stone — opaque, no TRANS |
| `img_skull` | 16×16 | `$011400` | `$0115FF` | 512 | Bob's sentinel skull (Gate 2 lineage) |
| `img_hero` | 16×24 | `$011600` | `$0118FF` | 768 | Bob's 11-colour Visigothic warrior — TRANS |
| `img_door_closed` | 8×40 | `$011900` | `$011B7F` | 640 | Claude placeholder — Kimi may replace |
| `img_door_open` | 8×40 | `$011B80` | `$011DFF` | 640 | Claude placeholder |
| `img_door_brick` | 8×40 | `$011E00` | `$01207F` | 640 | Claude placeholder |
| `img_gate` | 16×32 | `$012080` | `$01247F` | 1,024 | Claude placeholder |
| `img_lever_idle` | 8×12 | `$012480` | `$01253F` | 192 | Claude placeholder |
| `img_lever_tell` | 8×12 | `$012540` | `$0125FF` | 192 | Claude placeholder |
| `img_lever_pulled` | 8×12 | `$012600` | `$0126BF` | 192 | Claude placeholder |
| `img_lever_sprung` | 8×12 | `$0126C0` | `$01277F` | 192 | Claude placeholder |
| `img_spike16` | 16×8 | `$012780` | `$01287F` | 256 | Claude placeholder — Kimi design asset ready |
| `img_spike24` | 24×8 | `$012880` | `$0129FF` | 384 | Claude placeholder — Kimi design asset ready |
| `img_exit` | 32×48 | `$012A00` | `$0135FF` | 3,072 | Claude placeholder |
| `img_flame` | 64×16 | `$013600` | `$013DFF` | 2,048 | Claude placeholder — Kimi design asset ready |
| `img_guard` | 16×24 | `$013E00` | `$0140FF` | 768 | Claude placeholder — Kimi design asset ready |
| `img_heavy` | 16×24 | `$014100` | `$0143FF` | 768 | Claude placeholder — Kimi design asset ready |
| `img_watcher` | 16×24 | `$014400` | `$0146FF` | 768 | Claude placeholder — Kimi design asset ready |
| `img_wraith` | 16×24 | `$014700` | `$0149FF` | 768 | Claude placeholder — Kimi design asset ready |
| `img_arrow_r` | 8×2 | `$014A00` | `$014A1F` | 32 | Claude placeholder |
| `img_arrow_l` | 8×2 | `$014A20` | `$014A3F` | 32 | Claude placeholder |
| `img_ladder` | 16×216 | `$014A40` | `$01653F` | 6,912 | Claude placeholder |
| **pix_end / total** | | | `$016540` | **25,920 B** | 25.3 KB — 1.2% of 2 MB DRAM |

---

## 3. Safe Candidate Art Regions

| Zone | Range | Available | Recommended Use |
|---|---|---|---|
| **Zone A — PIXBASE tail** | `$016540 – $01BFFF` | ~43 KB | Kimi replacement art, additional enemy frames, trap variants |
| **Zone B — Upper DRAM** | `$01C000 – $1FFBff` | ~1.87 MB | Environment bands, animation strips, V7+ art |
| **Zone C — Mid DRAM** | `$004930 – $00EFFF` | ~43 KB | CPU-built transient bitmaps, per-floor overlays |

**Stack guard:** Reserve `$1FFC00 – $1FFFFC` (1 KB). Do not place art above `$1FFC00` without stack audit.

---

## 4. Object Processor Constraints — Must Not Violate

### 4.1 Phrase encoding (runtime build_list)

```
PH0_HI = (DATA >> 3) << 8  |  (LINK >> 11)
PH0_LO = ((LINK & $7F8) << 21) | (HEIGHT << 14) | (YPOS << 3)    ; TYPE=0
PH1_HI = (IWIDTH >> 4) | flags       ; $8000 = TRANS
PH1_LO = ((IWIDTH & $F) << 28) | (DWIDTH << 18) | $C000 | XPOS   ; PITCH=1, DEPTH=4
```

| Rule | Constraint | Violation consequence |
|---|---|---|
| Phrase alignment | DATA and LINK addresses must be 8-byte aligned | OP reads garbage |
| DEPTH = 4 | `$C000` in PH1_LO encodes PITCH 1 + DEPTH 4 (CRY16). Never change. | Colour corruption |
| DWIDTH = IWIDTH = ceil(width/4) | 16 px = 4 phrases; 24 px = 6 phrases; 320 px = 80 phrases | Tearing / shearing |
| HEIGHT in OB_H | Must be set before build_list. Shadow→LIVE copy does the refresh. | Sprite invisible frame 2+ |
| TRANS flag ($8000 in OB_FL) | All sprites except img_floor must have TRANS. $0000 pixels are transparent. | Opaque black box |
| XPOS origin = 0 | XORG=0. XPOS = screen pixel x. NOT HDB1=177. | Castle starts mid-screen |
| STOP terminator | Object chain must end in TYPE=4 STOP after NOBJ objects. | OP runs into garbage |

### 4.2 VC field-bit mask — ⚠️ CAUTION (open hardware question)

`and.w #$07FF,d0` applied to VC read. VJ sets VC bit 11 on every second field.
Without the mask: 30 Hz, alternate frames black. Mask is harmless on real hardware
(VC bit 11 unused in non-interlaced mode per Tech Ref). **Deferred to hardware verification.**

### 4.3 CONFIG byte — ⚠️ CAUTION (legacy defect)

`CONFIG equ $F14002` + `btst #4,CONFIG` reads the high byte. Bob's `videoinit.inc`
uses `$F14003` (low byte where the PAL bit lives). VJ returns `$FF` for both →
NTSC chosen by luck. Defect on real hardware. **Bob will fix before hardware submission.
Kimi and Claude do not need to touch this.**

---

## 5. Bandwidth & OP Risks for Five-Floor Visuals

| Risk | Finding | Status |
|---|---|---|
| Floor bitmap per-line bandwidth | 80 phrases/line for 320 px floor. Well within Jaguar DRAM bandwidth budget. | ✅ SAFE |
| Environment bands (Kimi V2) | One OP BITMAP per band. Width = phrase multiple. No per-line bandwidth concern. | ✅ FEASIBLE |
| Taller bands | Height only affects DRAM size (Zone A/B has space), not per-line cost. | ✅ FEASIBLE |
| Additional OP objects for bands | 18 objects today; capacity ~109 before SHADOW collision. 5–8 new objects: zero concern. | ✅ SAFE |
| Taller bands and physics | FLOOR_HL and GROUND_Y are physics constants independent of art YPOS. No physics shift forced. | ✅ ART-ONLY |
| Wide sprites (img_flame 64 px, img_exit 32 px) | Widest sprites. Still negligible vs bandwidth ceiling. | ✅ SAFE |
| Kimi trap sprites (falling block, swinging blade) | 16×16 designs ready but not yet in castle_art.inc or OP list. New OP slots + NOBJ increment required. | ⚠️ BOB REVIEW AT INTEGRATION |
| $0000 transparency | Kimi's trap designs correctly use $0000 for background. | ✅ CONFIRMED CORRECT |

---

## 6. Trap Sprites Not Yet Integrated

Kimi has completed pixel designs for:
- `falling_block` — 16×16 CRY16 (in `docs/visual/sprites/falling_block.s`)
- `swinging_blade` — 16×16 CRY16 (in `docs/visual/sprites/swinging_blade.s`)
- `flame_hazard` — 16×16 CRY16 (in `docs/visual/sprites/flame_hazard.s`)
- `spikes` — 16×16 CRY16 (in `docs/visual/sprites/spikes.s`)

`img_spike16`, `img_spike24`, and `img_flame` slots already exist in `castle_art.inc`.
Falling block and swinging blade require new OP slots. Integration path for those:

1. Append pixel data to `castle_art.inc` after `pix_end` (Zone A)
2. Add `O_FBLOCK` / `O_BLADE` constants and increment `NOBJ` from 18 → 20
3. Add `OB_DATA` init in `set_objects`
4. Claude wires gameplay trigger logic

**Bob reviews step 2–3 before commit.**

---

## 7. Integration Contract

### Kimi may change safely (no Bob review before drafting)
- Pixel data in `castle_art.inc` for any "Claude placeholder" slot — **same dimensions only**
- CRY16 colour values within existing art (palette swaps, stonework detail, tone)
- New design asset files under `docs/visual/sprites/` (not linked until Claude wires them)
- V2 environment-band planning documents in `docs/visual/`
- Preview PNGs and reference art

### Requires Bob review before touching game source
- **Any dimension change** to an existing art slot (breaks all downstream PIXBASE offsets)
- **New images appended** past `pix_end` (Bob confirms layout, NOBJ, copy loop)
- **Any change to `img_floor`, `img_skull`, or `img_hero`** — protected proven art
- Any new image wider than 64 px (band-level) — DWIDTH/IWIDTH math must be confirmed
- Any colour value that might accidentally use `$0000` as an opaque pixel in a TRANS sprite

### Claude may integrate safely
- Gameplay logic using existing OB_ records and state offsets
- Same-size pixel data swaps for Claude-placeholder slots once Kimi supplies replacements
- Falling block / swinging blade OP integration after Bob confirms NOBJ change

### Claude must not do without Bob review
- Change `PIXBASE`, `LIVE`, `SHADOW`, `HUDBUF`, or `STATE` base addresses
- Change the phrase encoding formula in `build_list`
- Change the Shadow→LIVE copy loop (object count or stride)
- Change `XORG`
- Modify `img_floor`, `img_skull`, or `img_hero` pixel data

---

## 8. PASS / CAUTION / BLOCKED Summary

| Item | Status |
|---|---|
| PIX_FLOOR / PIX_ENEMY overlap | ✅ PASS — resolved in Gate 7 |
| DRAM layout — no collisions | ✅ PASS — confirmed by address arithmetic |
| OP phrase encoding (runtime build_list) | ✅ PASS — verified against Gate 6 known-good constants |
| Shadow→LIVE refresh (HEIGHT problem) | ✅ PASS — copies all 18 headers each blank |
| XPOS origin = 0 | ✅ PASS — Gate 6 XPOS_MIN=177 bug fixed |
| Memory headroom for visual expansion | ✅ PASS — ~1.9 MB free above pix_end |
| Environment bands (Kimi V2) | ✅ FEASIBLE — OP and bandwidth headroom confirmed |
| VC field-bit mask | ⚠️ CAUTION — deferred to hardware verification |
| CONFIG byte $F14002 vs $F14003 | ⚠️ CAUTION — deferred to hardware submission; Bob owns |
| Falling block / swinging blade OP slots | 🔵 REVIEW NEEDED at integration time |
| Dimension change to existing art slots | 🚫 BLOCKED — Bob sign-off required |
| img_floor / img_skull / img_hero modification | 🚫 BLOCKED — explicit review gate + runtime re-verification |

---

## 9. Review Checkpoints

| Checkpoint | Trigger | Owner | Effort |
|---|---|---|---|
| **A — Same-size art replacement** | Kimi supplies replacement for any existing slot | Bob confirms dimensions + phrase count + $0000 transparency; Claude drops in | Low |
| **B — New art slot** | Falling block, swinging blade, or any new image | Bob updates layout table, assigns address, adds O_ constant, increments NOBJ | Medium |
| **C — Environment band** | Kimi proposes width × height for a floor band | Bob confirms DWIDTH phrase math, allocates Zone A/B address, adds OP slot | Medium |
| **D — Pre-competition hardware pass** | Before any real hardware submission | Fix CONFIG byte, verify VC mask, full soak — Bob owns entirely | Bob only |

---

*Scope boundary: No source files changed. No gameplay features added. Review stops here until a checkpoint is triggered.*
