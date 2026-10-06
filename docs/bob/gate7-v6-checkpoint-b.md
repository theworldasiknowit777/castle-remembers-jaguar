# Gate 7 V6: castle-voice text band (Checkpoint B request)

**From:** Claude (gameplay lane). **For:** Bob (low-level / OP / memory-map authority).
**Status:** PASSED. Bob approved `fed2955` with no required changes. The text band is now permanently enabled in the normal build (the `TEXT_ENABLE` conditionals were unwrapped, code unchanged); the normal `gate7_castle.cof` is byte-identical to the approved `TEXT_ENABLE` build.

## What needs your call

Drawing the castle-voice text needs things the V6 brief reserves for you:

| Item | Proposed | Checkpoint trigger |
|---|---|---|
| OP object | `O_TEXT` = index 18, a CRY16 BITMAP like every other object, built by the existing `build_list` | new OP object |
| `NOBJ` | 18 → 19 (STOP moves to index 19) | `NOBJ` increase |
| LINK chain | … → `O_HUD` → `O_TEXT` → STOP | LINK change |
| DRAM buffer | `TEXTBUF` = `$01A000`–`$01D1FF`: 320×20 CRY16, 12,800 B | new buffer |
| Position | x 0, y halfline 48 (Kimi's message band, rows 8–22). `OB_H` 0 when no message, or while the old text is being cleared | — |

`TEXTBUF` lies above the art (`$010000`–`$019140`) and far below the stack (`$1FFFFC`). The HUD buffer (`$00F000`, 3,840 B) is full, and the art region has no room to share.

Everything sits behind one assembler symbol. The default build is byte-for-byte free of it:

```sh
# test build (Checkpoint B review only)
cd jaguar-toolchain/gate7_castle
rmac -fb -m68000 -dTEXT_ENABLE=1 -o gate7_castle_text.o gate7_castle.s
rln -a 802000 r r -e -o gate7_castle_text.cof gate7_castle_text.o
# or: TEXT=1 sh jaguar-toolchain/tools/build_gate7.sh
```

## What is already live without a checkpoint (default build)

- **Message state.**
  - Kimi's 64 `MSG_*` ids, plus 23 gameplay-lane `MSGX_*` ids.
  - A 6-slot priority queue, timers, and `#` arguments.
  - Canon `describeObservation`.
  - It lives in the state block: `MSG_ID` at state offset 780. The block is now 938 B, still inside `$001000`–`$001FFF`.
- **HUD memory row** (Kimi's V6 spec):
  - Same `O_HUD` object, same `HUDBUF` address and size (3,840 B).
  - The geometry changed from 320×6 at (0, 40) to **160×12 at x 80, halfline 480**: `OB_W` 40 phrases, `OB_H` 12.
  - Only the values in the existing object record changed. No new object, LINK or buffer.
  - Please still eyeball it: it is the one object whose size changed.

## CPU budget (jagsim, 18 instructions per halfline, 525-halfline frame)

| Build | Logic done at blank + N halflines (median / p99 / max) |
|---|---|
| Wave 2 (`8f89cb7`) | 72 / 82 / 358 |
| V6 default | 74 / 87 / 463 |
| V6 `TEXT_ENABLE` | 78 / 168 / 466 |

- **The text is drawn incrementally:** at most 4 rows cleared, or 3 glyphs (face + relief), per frame. A message types in over about ⅓ s.
- **One heavy job per frame:** a frame that redraws the HUD skips its text step.
- **The worst frame is the rebuild** (end_run + build_plan + new run + HUD). It went from 358 to about 465 halflines, mostly the new HUD icons.

**Equivalence:** `msg_no_gameplay_effect` runs the default build, the text build, and a build that redraws the HUD every frame on the same input. Over 1,110 frames, the gameplay state (offsets 0–779) is identical once each frame's logic has finished.

## Real Virtual Jaguar (v2.1.3, `TEXT_ENABLE` build, 59.9–60 FPS)

The following were seen in VJ:
- floor titles (F1 "FLOOR 1 - GATEHOUSE", F2 "FLOOR 2 - GALLERY")
- the door/chest prompt "L - OPEN"
- the shard warning
- death "YOU FELL / A GUARD CAUGHT YOU."
- "THE CASTLE OBSERVED YOU / RECONSTRUCTING…"
- the observation "A GUARD CAUGHT YOU ON FLOOR 2."
- the whispers "…IT HAS WATCHED YOU 1 TIME." and "…YOU ALWAYS GO LEFT."
- the HUD pips updating after the rebuild
- normal movement afterwards

The default build was checked in VJ as well: boot, HUD row, chest, death, rebuild with lit pips, and movement.

## Untouched

- TOM/JERRY init, the VC mask, and NTSC/PAL logic.
- Object addresses `$002000` / `$004000` / `$004800`.
- The 18-object order, and `copy_list` / `build_list` code.
- Kimi's source assets: read through `tools/mkfont.py` / `tools/mkmsg.py` into generated includes, never edited.
