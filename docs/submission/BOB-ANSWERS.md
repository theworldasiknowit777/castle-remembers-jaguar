# IBM Bob tool-usage answers (for the submission form)

Every claim below is checked against this repository (`jaguar-toolchain/DEVLOG.md`, `AGENTS.md`, `docs/bob/`, `docs/submission/EVIDENCE.md`). Items in [brackets] are the owner's to fill from Bob's own task history.

## 1. What Bob helped with

Bob built the native foundation of the Jaguar port. It identified RMAC 2.5.2 and RLN 1.7.7 as the working native Windows toolchain (load address `$802000`) and got the first blue screen running in Virtual Jaguar (Gate 1). It then built the Object Processor bitmap rendering, the hero sprite and controller movement (Gate 2), the floor and gravity (Gate 3), the jump, enemy and collision (Gate 4), and the adaptive side-bias memory with `SIDE_BIAS` and `DEATH_COUNT` (Gate 5).

For the five-floor Gate 7 build, Bob acted as the low-level authority. It reviewed the castle-voice text object at Checkpoint B (`fed2955`) and the resident environment-band memory map at Checkpoint C. Its address amendment (`BANDS_BASE $020000`) is in the final build. Gate 7 gameplay was implemented with Claude and the art came from Kimi; the repository documents that split.

## 2. Bob tools used

[List only the tools that appear in Bob's own task history.]

## 3. Time saved

[Owner's honest estimate, or "not measured".]

## 4. Specific examples

**Transparency bug.** The hero's transparent (`$0000`) pixels were not letting the floor show through. The TRANS flag had been set at `$00000020`, which is phrase bit 37 and sits inside the IWIDTH field. Bob traced the BITMAP phrase layout and moved it to phrase bit 47, which is PH1_HI bit 15, `$00008000`. The hero was transparent over the floor on the next build (`DEVLOG.md`, "TRANS flag — corrected bit position").

**Joystick bug.** The first input code read a 32-bit longword and tested bits 22/23, which span both of the controller's rows. Bob's fix writes `$817E` (16-bit) to `JOYSTICK` to select Row 0 and reads bits 10 and 11 as LEFT and RIGHT, active-low (`DEVLOG.md`, Gate 2 input).

The Jaguar has no software debugger, so both bugs could only be found by reading the hardware layout and checking the pixels.
