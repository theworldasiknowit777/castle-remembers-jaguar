# Demo recording and live environment

## Recording target: 2 minutes 50 seconds

Use normal Gate 7, pinned to `7aaaa30cf5a91bdef198e9fcbeae807353836ad6`, after a fresh smoke run and remaining audit review. If it fails, use verified Gate 5 and revise the deck/description to that scope. Do not silently replace the candidate with Gate 6. Do not substitute the separate HTML application.

| Time | Screen / action | Suggested narration |
|---|---|---|
| 0:00–0:15 | Title, creator, Jaguar runtime | “I’m Tony Topil. Castle Remembers Jaguar is my native Atari Jaguar entry. It adapts an existing HTML game; the browser game is a separate project.” |
| 0:15–0:35 | Pinned repo, original hash, Bob task evidence | “The preserved browser build defines the source behavior. During this hackathon Bob helped establish the Windows assembler, linker and emulator workflow and build the native foundation.” |
| 0:35–1:00 | Actual Bob prompt/review; source and COF build | “Here is the recorded Bob work and its result. Later, Bob reviewed the text object and resident background memory. Claude handled later gameplay and Kimi contributed art.” Show only evidence actually available. |
| 1:00–1:40 | Normal VJ gameplay: walk, open door, climb, jump | “This is the native 68000 build running in Virtual Jaguar. Controller input drives doors, ladders and collision across the castle.” Show an interaction working; do not spend the entire segment traversing five floors. |
| 1:40–2:05 | Planned death/rebuild, observation and changed memory HUD | “The game records habits, reconstructs the castle, and exposes its observations. These deterministic rules carry the original game’s idea into the native port.” Pre-rehearse the behavior; no debug state injection presented as normal play. |
| 2:05–2:30 | Actual test output, COF guard, evidence ledger | “The repository separates scripted model checks from real-emulator evidence. Bob’s display reviews are recorded. The broader audit remains open, and Gate 6 is not runtime-certified.” Update audit wording only when evidence changes. |
| 2:30–2:50 | Open live Jaguar URL; closing slide | “Judges can use this live Jaguar environment and reproduce the pinned build from the repository. Next are hardware validation and deeper parity testing.” Say this only after the live environment exists and has been tested. |

If a needed clip is unavailable, shorten the claim instead of manufacturing evidence. Target 170 seconds; inspect the exported duration, leaving 10 seconds under the 180-second cap. Capture at readable 1080p with microphone narration. If OpenGL recording is black, change capture mode and verify a short test; existing F8 screenshots support evidence but do not replace a moving demonstration.

Controls documented for Gate 7: Z/C move; S jump/climb up; X climb down/ACT; L ACT. Confirm the recorder’s VJ mapping. Gate 5 uses Z/C/S only.

## YouTube completion

1. Record the pinned normal build and real Bob evidence; edit to <=3:00.
2. Upload to the owner’s YouTube account (public or unlisted, viewable by judges without sign-in or access requests).
3. Check playback, readable source/test clips, sound and total duration in a signed-out browser.
4. Put the actual watch URL in PROJECT.md and the official form. Keep a source recording locally; optionally store a transcript in the repository. No video URL is currently verified.

## Live Jaguar demo: unresolved submission dependency

The official requirement is a URL to a live working environment. A COF download or the separate HTML game is insufficient as evidence of an interactive Jaguar environment.

Preferred paths, in order of practical feasibility:

1. Use an existing browser-accessible Jaguar emulator **only if** it demonstrably loads this exact normal COF, exposes controls, and can lawfully redistribute its required components. Test cold boot, door, ladder, death/rebuild and reset on a second device. No compatible hosted runtime has been established by this audit.
2. Host a dedicated, isolated Virtual Jaguar desktop accessible through a browser remote-display session. Judges need scoped game controls and reset, no development account credentials, no access to the owner’s personal desktop, and availability throughout judging. Confirm this URL format with organizers before relying on it.
3. If neither is feasible, request an explicit organizer exception for a native-console entry: downloadable COF plus prerecorded emulator demo and reproduction instructions. An exception must actually be granted; a download landing page alone does not satisfy the literal rule.

The owner must select/provide the hosting account or existing compatible environment, confirm organizer acceptance where needed, and supply the resulting URL. This submission task does not authorize buying hosting or exposing a personal desktop. Deadline priority: settle this before polishing more gameplay.

## Local reproduction (not a submitted live URL)

For main/Gate 5: download the pinned RMAC/RLN/Virtual Jaguar tools using `jaguar-toolchain/TOOLCHAIN-SETUP.md`; open `jaguar-toolchain/gate5_memory/gate5_memory.cof` with Jaguar > Open File. Keep original files unchanged.

For Gate 7 use the exact candidate checkout and its existing tools:

```sh
git clone https://github.com/theworldasiknowit777/castle-remembers-jaguar.git
cd castle-remembers-jaguar
git checkout 7aaaa30cf5a91bdef198e9fcbeae807353836ad6
python -m pip install unicorn pillow
python jaguar-toolchain/tools/check_cof.py jaguar-toolchain/gate7_castle/gate7_castle.cof
python jaguar-toolchain/tools/test_gate7.py
# With RMAC/RLN available as required by the existing script:
sh jaguar-toolchain/tools/build_gate7.sh
```

The supplied Python test model is not full Virtual Jaguar emulation. For runtime checking, open the COF in the documented Windows VJ build and follow the actions above. Dependencies are not fully version-locked in the original branch; record tested local versions with the final recording. Never redirect binary Git output through PowerShell 5.1 `>`.
