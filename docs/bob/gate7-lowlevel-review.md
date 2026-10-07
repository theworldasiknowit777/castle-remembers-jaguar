# Gate 7 — low-level changes for Bob's audit

Branch `claude/gameplay-refinement`. Gameplay is Claude's; these items touch the layer
Bob owns, so each is listed with the evidence and the exact code. Nothing here changes
Gate 1–6 files.

## 1. VC wait loop masks the field bit — **please confirm**

```asm
.wait_blank:  move.w VC,d0 / and.w #$07FF,d0 / cmp.w #VC_VDE,d0 / blt.s .wait_blank
.wait_new:    move.w VC,d0 / and.w #$07FF,d0 / cmp.w #VC_VDE,d0 / bge.s .wait_new
```

- Virtual Jaguar Rx R5, `src/jaguar.cpp`, `HalflineCallback()`: at the end of each field
  `lowerField = !lowerField; vc = (lowerField ? 0x0800 : 0x0000);` so VC reads ≥ $0800 for
  the whole of every second field.
- Unmasked (Gate 6), `cmp.w #507` treats that whole field as blanking: the list is refreshed
  once per two frames, every other frame is blank, and the game runs at 30 Hz.
- Evidence:
  - `tools/jagsim.py` models the bit. It gives Gate 6 `[0, 3852, 0, 3852, …]` drawn pixels per frame, and Gate 7 draws every frame.
  - In the real VJ, three of five F8 screenshots of the unmasked build were black. Six of six with the mask had content.
- **Open question:** does hardware set bit 11 in non-interlaced mode? The mask is harmless either way.

## 2. Shadow object list

- `build_list` writes next frame's headers to `SHADOW` ($004800).
- At the start of blank, `copy_list` copies 18×16 bytes to `LIVE` ($004000), where OLP points.
  - The copy rewrites every header, which also performs the HEIGHT/DATA refresh.
  - It takes about 4 halflines of the 18-halfline blank.
- Game logic then runs into the next frame's active display. It only ever touches SHADOW.
- Why: gameplay cost no longer has to fit in the blank. Measured logic finishes about 67 halflines after blank (worst case 320, during HUD redraw), against a 525-halfline deadline.
- OLP setup is Bob's verbatim word-swap.

## 3. Phrases built at runtime from symbolic fields

`build_list` (one loop for all objects):

```
PH0_HI = DATA<<8 | LINK>>11            (DATA, LINK phrase-aligned addresses)
PH0_LO = (LINK & $7F8)<<21 | HEIGHT<<14 | YPOS<<3      (TYPE 0)
PH1_HI = IWIDTH>>4 | flags ($8000 = TRANS)
PH1_LO = (IWIDTH&$F)<<28 | DWIDTH<<18 | $C000 (PITCH 1, DEPTH 4) | XPOS
```

- This is Gate 6's field layout. With Gate 6's inputs it produces Gate 6's correct constants: hero `$00940008`, floor PH1 `$00000005 / $0140C0B1`.
- It also removes the hand-arithmetic errors found in Gate 6:
  - F2 YPOS `$0380` = 112 halflines, not 280.
  - F3 YPOS `$01B8` = 55, not 140.
  - E1 YPOS is odd (375).
- The STOP object (TYPE 4 in the low longword) is written once after the 18 objects, in both lists.

## 4. XPOS origin = 0

- `XORG equ 0`: screen pixel x has XPOS x.
- Tech Ref p.18: "Address 0 refers to the left-most pixel in the line buffer".
- The VJ F8 screenshot of the first Gate 7 build (XORG 177) showed the castle starting mid-screen with its right half cut off.
- Gate 6's XPOS_MIN=177 is HDB1, the display-begin pixel clock, not the XPOS origin.

## 5. Memory map (Gate 7, with the V6 text band and the V7 environment bands)

| Range | Use |
|---|---|
| `$000000` | Bob's startup STOP phrase (kept verbatim) |
| `$001000–$0013A9` | game state (a5 base); offsets at the top of `gate7_castle.s` |
| `$002000–$00213F` | 20 object records × 16 bytes (data.l, x, y, h, w, flags) |
| `$004000–$00414F` | LIVE list: 20 BITMAPs + STOP (OLP) |
| `$004800–$00494F` | SHADOW list |
| `$00F000–$00FEFF` | HUD bitmap 160×12 CRY16, CPU-drawn |
| `$010000–$019540` | all art (38,208 B, `ART_BYTES`), copied once from ROM `pix_start..pix_end`, packed, phrase-aligned |
| `$01A000–$01D1FF` | `TEXTBUF`: castle-voice text band 320×20 CRY16 (Checkpoint B) |
| `$020000–$0ACA00` | five environment bands, 320×180 CRY16 (Checkpoint C), `$01C200` B each: F1 `$020000`, F2 `$03C200`, F3 `$058400`, F4 `$074600`, F5 `$090800` |
| `$1FFFFC` | stack (Bob) |

- No overlaps.
- The Gate 6 issue (`PIX_ENEMY $9000` inside `PIX_FLOOR $8000+5120`) does not exist in Gate 7.

## 6. Left exactly as Bob wrote it, for your decision

- `btst #4,CONFIG` with `CONFIG = $F14002`:
  - This is a byte test of the high byte (JOYBUTS bit 12).
  - Bob's `include/videoinit.inc` tests `$F14003`.
  - VJ returns $FF in that byte, so NTSC is chosen by luck; real hardware is unknown.
- The startup STOP phrase at `$000000` (TYPE 4 in the high longword) is really a zero-height BITMAP. It is harmless because OLP is pointed at the real list before video starts.
- `VI = $7FFF`, interrupts masked, polled VC: unchanged.

## 7. Assembler note

RMAC evaluates expressions strictly left to right: `FSPIKE+2*16` assembles as `(FSPIKE+2)*16`. Gate 7 parenthesises every product. Worth remembering for any hand-written equates.

## 8. How to re-verify

```sh
sh jaguar-toolchain/tools/build_gate7.sh
python jaguar-toolchain/tools/test_gate7.py           # 13 scripted playtests
python jaguar-toolchain/tools/soak_gate7.py 20000 1 18
powershell -File jaguar-toolchain/tools/vj_drive.ps1 -Rom jaguar-toolchain/gate7_castle/gate7_castle.cof -Out shots -Script "wait:3;tap:F8"
```

- VJ's own screenshots land in `%LOCALAPPDATA%\virtualjaguar\screenshots`.
- Screen-grabs of the OpenGL window are unreliable (often black). Use F8.

## Wave 2 addendum (gameplay only, no checkpoint triggered)

- **No new OP objects, LINK changes or phrase constants.**
  - Chest, masonry, blade and gift shard are drawn in object slots their floor leaves idle (see `docs/gameplay/gate7-integration-brief.md` §4).
  - A slot may now draw a different image and size per floor. Size and data come from the same per-frame object records that `build_list` already turns into phrases.
- **Art region:** 37,184 B, packed and phrase-aligned at `$010000`–`$019140` (was ~26 KB). Copied once at boot by the same loop.
- **State block:** 784 B in `$001000` (was 660). Laid out as an `equ` chain; `P_BASE` (used with 8-bit indexed addressing) stays at 90.
- **Castle-voice text is state only.** Drawing it (Kimi's `font_data.s` into a CPU buffer, or the HUD buffer) is your Checkpoint B call.
- Still deferred to your final return: the VC field-bit mask, the NTSC/PAL `CONFIG` byte, and final shadow→LIVE validation.

## Checkpoint C implementation: environment bands (V7)

Bob's approval was followed as written, including the Gate 7 address amendment (not the Gate 6 table at `$010000`).

- **Object:** `O_BAND` = index 0, so it draws first and sits behind everything. Every other index moves up by one. `NOBJ` is 20, STOP is at index 20, and HUD and text remain the last two objects (`O_HUD` 18, `O_TEXT` 19).
- **Fields:** opaque (no TRANS), 80 phrases × 180 lines, x 0, y halfline 32 (screen row 0). `DATA` is switched per floor from `bandtab` in `set_objects`, so it goes through the normal `set_objects` → `build_list` → `copy_list` refresh every blank.
- **Residency:** all five bands are copied once at boot from ROM (`bands_start..bands_end`, 576,000 B) by a 32-byte `movem.l` loop, 18,000 passes, before the video is switched on. Nothing is copied or swapped on a floor change, and nothing writes to the bands afterwards.
- **Guards (Bob's list):**
  1. Phrase alignment: `BANDS_BASE`, `BAND_SIZE` and every band address are multiples of 8.
  2. The band is refreshed through the normal list build and copy every blank.
  3. The band object has no TRANS flag (record, SHADOW and LIVE).
  4. W = 80 phrases, H = 180.
  5. Gameplay constants, collision, ladders, floor physics, HUD, `TEXTBUF` and the art slots are unchanged. Gameplay state is identical to the pre-band build `0f6a185` for 1,820 frames of scripted input.
  6. Scripted tests, campaign, soak, COFF guard and VJ screenshots of all five floors.
- **Gate 7 note:** the static-LINK guard from Gate 6 does not apply, because `build_list` generates every LINK. The guard here verifies the `O_*` indices (one slot each, 0..19), `NOBJ`, STOP placement and the SHADOW → LIVE copy length (20 headers), and that each LINK points at the next object.
- **Tests:** `band_guards` (addresses, region collisions, indices, STOP, LINK chain, resident data equals Kimi's files, the band object), `band_floors` (a real five-floor route: pointer and pixels on every floor, bands unmodified afterwards), `band_no_gameplay_effect` (against the `0f6a185` build). The soak checks the band object on every frame and the CRC of the band region at the end.
- **Boot:** the band copy adds about 8 simulated frames before the video switches on. The test harness now waits for video-on (`JagSim.boot_wait`) rather than a fixed 5 frames.
