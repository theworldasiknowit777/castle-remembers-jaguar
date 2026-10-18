# IBM Bob tool-usage answers (for the submission form)

Every claim below is checked against this repository (`jaguar-toolchain/DEVLOG.md`, `AGENTS.md`, `docs/bob/`, `docs/submission/EVIDENCE.md`). Items in [brackets] are the owner's to fill from Bob's own task history.

## 1. What Bob helped with

Bob built the native foundation of the Jaguar port and then acted as the low-level authority for the five-floor Gate 7 build.

**Bob's own work (Gates 1-5, corroborated by `DEVLOG.md` and `AGENTS.md`)**
- **Toolchain:** identified RMAC 2.5.2 and RLN 1.7.7 as the working native Windows toolchain (`-fb -m68000`, link at `$802000`) and got the first blue screen running in Virtual Jaguar.
- **Controller input:** diagnosed broken joystick input (a 32-bit read tested bits 22/23) and specified the 16-bit Row 0 select `$817E`, bits 10/11, active-low.
- **Object Processor:** found that the OP zeroes HEIGHT in phrase 0 every frame and built the blanking-window refresh loop that keeps BITMAP objects visible. Corrected the TRANS flag to phrase bit 47 (`$00008000`), and fixed `LSL.W` versus `LSL.L` upper-word corruption in the Y-position build.
- **Game logic:** gravity and floor clamp in halflines, the jump, the AABB collision test, and the Gate 5 adaptive side-bias (`SIDE_BIAS`, `DEATH_COUNT`, spawn side and speed on respawn).
- **Documentation:** `DEVLOG.md` entries and the Gate 1 report.

**Bob as reviewer of Gate 7**
- Memory-safety, OP-safety and visual-readiness review of Gate 7 (`docs/bob/gate7-visual-integration-review.md`).
- Low-level review request and findings (`docs/bob/gate7-lowlevel-review.md`).
- Checkpoint B (`fed2955`): approved the castle-voice text object with no required changes.
- Checkpoint C: approved the resident environment bands, with the address amendment `BANDS_BASE $020000`, which is in the final build.

**Not Bob's work (declared)**: Gate 7 gameplay was implemented with Claude and its art came from Kimi, and Gate 6 is built but not runtime-verified. The late climb, wall-base and jump changes are Claude's.

## 2. Bob tools used

As reported in Bob's own session summary (not independently verifiable from the repository): `write_file` (the gate `.s` sources and `DEVLOG.md`), `apply_diff` / `search_and_replace` (per-gate patches), `execute_command` (running `rmac.exe` and `rln.exe`), `read_file`, `grep`, `update_todo_list`, symbol search over the large Gate 7 source, and HTML artifact output. [Owner: delete any tool you do not see in Bob's task history.]

## 3. Time saved

[Owner's estimate. Bob's own summary estimated 12-15 hours of a roughly 20-hour project; the repository cannot confirm that figure.]

## 4. Specific examples

**Transparency bug.** The hero's transparent (`$0000`) pixels were not letting the floor show through. The TRANS flag had been set at `$00000020`, which is phrase bit 37 and sits inside the IWIDTH field. Bob traced the BITMAP phrase layout and moved it to phrase bit 47, which is PH1_HI bit 15, `$00008000`. The hero was transparent over the floor on the next build (`DEVLOG.md`, "TRANS flag — corrected bit position").

**Joystick bug.** The first input code read a 32-bit longword and tested bits 22/23, which span both of the controller's rows. Bob's fix writes `$817E` (16-bit) to `JOYSTICK` to select Row 0 and reads bits 10 and 11 as LEFT and RIGHT, active-low (`DEVLOG.md`, Gate 2 input).

The Jaguar has no software debugger, so both bugs could only be found by reading the hardware layout and checking the pixels.
