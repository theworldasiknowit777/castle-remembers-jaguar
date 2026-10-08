# Castle Remembers Jaguar — IBM Bob submission

Evidence cutoff: October 8, 2026. Prepared by Codex from repository history; this packaging work is not attributed to IBM Bob.

## Project description (89 words)

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

- `main` inspected at `7a0818241be3c4036398547520128c5273f04509`: Gates 1–5 recorded PASS, Gate 6 built/pending.
- Strongest demo candidate: `claude/gameplay-refinement` at `7aaaa30cf5a91bdef198e9fcbeae807353836ad6`. It has Gate 7 runtime images and development records. It is not merged into main; broad low-level audit items remain open.
- This documentation branch is based on main and does not merge or change gameplay. Pin the candidate SHA in the submission and recording. If the final candidate changes, refresh claims and evidence together.

## Submission fields still requiring real URLs

- YouTube demo URL: **not yet supplied or verified**.
- Live Jaguar demo URL: **not yet supplied or verified**.
- Repository: https://github.com/theworldasiknowit777/castle-remembers-jaguar
- Pitch: `docs/submission/Castle-Remembers-Jaguar-Pitch.pdf`.

A browser link to the HTML game does not demonstrate this Jaguar entry. A GitHub source page, screenshot gallery, downloadable COF, or YouTube video alone is not a live working environment.
