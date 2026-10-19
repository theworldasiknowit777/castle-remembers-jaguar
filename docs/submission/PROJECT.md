# Castle Remembers Jaguar — IBM Bob submission

Evidence cutoff: October 8, 2026. Prepared by Codex from repository history; this packaging work is not attributed to IBM Bob.

## Project description (<=100 words)

Castle Remembers Jaguar brings an adaptive castle game to native Atari Jaguar assembly. IBM Bob helped establish the Windows build toolchain, implement the rendering and adaptive-memory foundation, and review later display and memory architecture. The separate HTML game supplies the preserved behavioral baseline. Jaguar development adds controller input, collision, enemy adaptation, and a five-floor branch with doors, levers, traps, and castle observations. Repository records distinguish Bob’s work from Claude gameplay and Kimi art contributions. Gates 1–5 have recorded runtime passes; Gate 7 has emulator evidence. Gate 6 remains unverified.

## Entry and track

**Entry:** Castle Remembers Jaguar, by Tony Topil. The HTML browser game and Python/Pygame version are separate projects, not this competition entry. `original/` is a frozen reference copy, not the Jaguar live demo.

**Recommended track:** Theme 2 — Experienced Developers — Modernize What Matters. The strongest fit is transforming an existing game into a native legacy-platform application while preserving its reference behavior. This is a cross-platform reimplementation, not a framework upgrade or a claim that Jaguar is newer hardware. Theme 1 emphasizes an unfamiliar app and a seeded issue; the documented migration fits Theme 2 more directly. Confirm the team’s registration category before submission.

**Team introduction:** Tony Topil — game creator, project direction and runtime review. Do not list AI tools as human team members. Confirm any additional human teammates on the submission form.

## Technology summary

| Component | Role and evidence |
|---|---|
| Motorola 68000 assembly | Native Jaguar program; committed `.s`, `.o`, `.cof` artifacts |
| Atari Jaguar Object Processor / CRY16 | Bitmap rendering, sprites, object lists and display buffers |
| RMAC 2.5.2 / RLN 1.7.7 | Native Windows assembler and linker per toolchain report |
| Virtual Jaguar Rx 2.1.3 R5 | Recorded runtime checks; not real-hardware certification |
| IBM Bob | Initial toolchain and native foundation; documented Gate 7 B/C architecture approvals |
| Python, Unicorn, Pillow | Gate 7 build/asset helpers and a partial headless hardware test model |
| PowerShell / shell / Git / GitHub | Local automation, build scripts and evidence history |
| Claude / Kimi | Disclosed gameplay and visual collaborators on Gate 7 |
| HTML5 / JavaScript / Canvas / Web Audio | Separate source game, retained only as the port’s reference baseline |

The adaptive rules are game logic. Bob is a development tool; no runtime Bob service, LLM inference, GPU/DSP acceleration, persistent Jaguar save parity, or full browser-game equivalence is claimed.

## Release scope

- Gates 1–5 have recorded runtime passes; Gate 6 was built but remains runtime-unverified.
- The Gate 7 gameplay candidate at `88874d8d1fd28925fae7d2416bd2d7dcf63e79cf` has recorded Virtual Jaguar evidence and scripted tests. It was merged into `main` in `499d7fbe5487dda40ac8a24f2e8fa5412dbbc4f1`; broad low-level and physical-hardware review items remain open.
- The owner reports that the entry was submitted. The completed event form is not recorded in this repository.

## Improvements made during the hacking period (Sept 28 – Oct 18)

The preserved HTML game (Sept 29 snapshot) is the pre-Bob baseline and is not claimed as new work. New during the hackathon: the entire native Atari Jaguar implementation in 68000 assembly.

- Oct 4: Windows RMAC/RLN/Virtual Jaguar toolchain and first native frame (IBM Bob).
- Oct 5: hero sprite, controller movement, floor, jump, collision and adaptive enemy respawn, Gates 2–5 (IBM Bob).
- Oct 5–7: Gate 7 five-floor castle with doors, levers, gates, chests, ladders, six enemy types, traps and a six-category castle memory (Claude); castle-voice text and HUD, with Bob Checkpoint B review; five resident environment bands and Bob Checkpoint C review (Kimi art).
- Oct 7: hero facing, walk and climb frames, ladder art, wall-base presentation.
- Oct 13–18: fresh smoke tests, merge of Gate 7 into `main`, browser demo page (`docs/play/`), pitch deck and submission documentation.

## Submission fields

- Repository: https://github.com/theworldasiknowit777/castle-remembers-jaguar
- Pitch: `docs/submission/Castle-Remembers-Jaguar-Pitch.pdf`.
- Browser demo URL: https://theworldasiknowit777.github.io/castle-remembers-jaguar/play/ (the page is configured for GitHub Pages; this documentation update did not independently verify public playback).
- YouTube demo URL: not recorded in this repository; the owner reports the entry was submitted.

The separate HTML game, a screenshot gallery or a downloadable COF alone is not a live working environment; the `/play/` page runs the real COF in a browser emulator.
