# Evidence and improvement ledger

## Provenance boundary

`pre-bob-baseline` is an annotated tag whose object is `a50baa684cd08570951f571aaf0305b4f16cfa18`; it resolves to baseline commit `f285ff1bcb2dad8fe97038a71be4a01b5b996335` (Oct 4). The preserved file’s documented archive timestamp is September 29, within the hackathon window but before the first documented Bob session on October 4. Do not describe that snapshot as predating September 28. The README’s broad “before any AI involvement” assertion is not independently established by an absence of AI references in source. The defensible claim is **pre-Bob baseline**.

SHA-256 of `original/index.html`, freshly checked Oct 8:
`5f9232b89dd2828bfe80cd7828df08b90b065f620bb226ec92a86731fe79634a`

HTML is a separate original application. Its castle adaptation, five-floor design, dialogue, sprites, browser persistence and audio are baseline features, not inventions credited to the Jaguar port. Porting or adapting them to assembly is new work.

## Dated history (repository local timestamps)

| Date | Commit | Improvement | Attribution and evidence limit |
|---|---|---|---|
| Oct 4 | `f285ff1` | Preserve HTML baseline | Preservation, not newly built gameplay |
| Oct 4 | `499c867` | Windows RMAC/RLN/VJ bootstrap; blue-screen execution | Bob session explicitly identified in `docs/bob/gate-1-report.md`; screenshot exists |
| Oct 5 | `c04af7e` | Hero bitmap and controller movement | Bob foundation per continuity/devlog; idle and clamp screenshots |
| Oct 5 | `7a08182` | Floor, jump, collision, adaptive enemy; Gate 6 assembly | Gates 3–5 runtime passes recorded; Gate 6 still pending |
| Oct 5 | `f4a42ed`, `8f89cb7` | Gate 7 five floors, interactions, traps, expanded memory | Claude gameplay lane; do not credit all to Bob |
| Oct 5 | `5ccc4ab`, `7662c20` | Reject corrupt COF and fix PowerShell entry guard | Gameplay/tooling lane; binary-safe handling |
| Oct 5–6 | `fed2955`, `3e1fc36` | Castle voice/HUD; enable text after Checkpoint B | Implementation by Claude/Kimi; Bob approval documented for `fed2955` |
| Oct 6–7 | `0f6a185`, `cfbad1b` | Ladders and five resident environment bands | Kimi art / Claude integration; Bob Checkpoint C approval recorded |
| Oct 7 | `a9f22da`, `7aaaa30` | Baseline-derived climb frames and wall-base presentation | Later branch work; not solely Bob-generated |

All commits above fall within September 28–October 18. Commit dates establish repository timing, not who performed each action. Attribution comes from contemporaneous reports; attach original Bob session exports/screenshots to strengthen it.

## Verification levels

1. Fresh inspection: refs, source, original hash, existing screenshots and COF header.
2. Recorded runtime evidence: AGENTS/DEVLOG report Gates 1–5 passed. Gate 7 images and records show Virtual Jaguar execution, including V6 and V7 milestones.
3. Historical metrics: `cfbad1b` environment-band DEVLOG records 34/34 scenarios, 20,000 soak frames without invariant violations, and VJ 59.9–60.1 FPS. These are milestone-specific historical results, not an Oct 8 rerun or hardware benchmark.
4. Gate 6: tag `v0.6-gate6` already points at `7a08182`; a tag does not prove runtime PASS. Later Gate 7 audit identifies possible Gate 6 issues (field-bit handling, positions, overlapping art). Do not use Gate 6 as the headline demo until separately checked.
5. Gate 7: B/C approvals do not close the broader low-level audit. `docs/bob/gate7-lowlevel-review.md` still requests review of VC masking, startup/config details and shadow/live handling. No physical Jaguar verification claimed.

## Bob proof to capture before recording

- Original Bob session/task view for Gate 1 and native foundation; show the actual prompt, investigation and resulting file/commit.
- Bob’s Checkpoint B response against `fed2955` and Checkpoint C response about object ordering, resident memory and alignment.
- One concrete review-to-change example, with before/after code and test evidence.
- Redact credentials and unrelated account information. Do not fabricate a conversation or recreate one as historical evidence.
- Keep a brief human/Claude/Kimi/Bob attribution note. Codex prepared submission documentation; it did not retroactively create Bob evidence.

## Source links

- [Official event](https://hackathon.stackup.dev/web/events/building-with-ibm-bob)
- [Main snapshot](https://github.com/theworldasiknowit777/castle-remembers-jaguar/tree/7a0818241be3c4036398547520128c5273f04509)
- [Gate 7 candidate](https://github.com/theworldasiknowit777/castle-remembers-jaguar/tree/7aaaa30cf5a91bdef198e9fcbeae807353836ad6)
- [Gate 1 report](https://github.com/theworldasiknowit777/castle-remembers-jaguar/blob/7a0818241be3c4036398547520128c5273f04509/docs/bob/gate-1-report.md)
- [Gate 7 devlog](https://github.com/theworldasiknowit777/castle-remembers-jaguar/blob/7aaaa30cf5a91bdef198e9fcbeae807353836ad6/jaguar-toolchain/DEVLOG.md)
- [Checkpoint B](https://github.com/theworldasiknowit777/castle-remembers-jaguar/blob/7aaaa30cf5a91bdef198e9fcbeae807353836ad6/docs/bob/gate7-v6-checkpoint-b.md)
- [Audit and Checkpoint C](https://github.com/theworldasiknowit777/castle-remembers-jaguar/blob/7aaaa30cf5a91bdef198e9fcbeae807353836ad6/docs/bob/gate7-lowlevel-review.md)

## Asset review

Reviewed repository root, all remote branch file inventories, runtime evidence folders and relevant Library search results. Found existing concept images and browser source; no submission PDF or recorded demo identified in those results. Search is not proof that none exists elsewhere. Reuse committed VJ screenshots in this pitch. Concept art, showcase/debug builds and simulated renders are not ordinary gameplay evidence. Each reused deck image is labeled with its original milestone.

## Oct 8 local checks

Baseline SHA-256 and frozen-tree comparison passed. The candidate COF header guard passed. A fresh full Gate 7 scripted run was attempted after installing Unicorn, but was interrupted before completion; no fresh suite PASS is claimed. The historical metrics above remain explicitly tied to their original milestone. No Virtual Jaguar or physical-console run was performed in this environment.
