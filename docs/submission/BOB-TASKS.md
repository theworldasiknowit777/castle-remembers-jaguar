# Bob tasks to run before submitting (Oct 18)

Judges score Tool Usage & Depth (30%) on whether Bob was part of the workflow, and all Bob work must be declared. These are real open review items; run them in IBM Bob on this repo (branch `main`), screenshot the task view, and save Bob's answer under `docs/bob/` (e.g. `gate7-final-audit.md`). Record only what Bob actually says; do not edit its verdict.

1. **Open audit items** — "Read `docs/bob/gate7-lowlevel-review.md` and `jaguar-toolchain/gate7_castle/gate7_castle.s`. Review the three open items: the VC field-bit mask (`and.w #$07FF` before the VDE compare), the NTSC/PAL configuration byte, and the SHADOW-to-LIVE copy at blank. For each: sound / unsound, why, and any change you would require."
2. **Late changes** — "Review `hero_sync` (the two hero stride slots are overwritten from ROM at the start of blank while the Object Processor is not reading, tracked by `HEROSET`) and the per-floor background write (`basetab`, written to `BG` at blank). Any OP, memory-map or timing risk? Memory map is in the review doc."
3. **Final sign-off** — "Given items 1–2, may commit `88874d8` (Gate 7) be described as audited? List exactly what you did and did not verify."

After each answer: copy Bob's text into `docs/bob/`, add one line to `docs/bob/README.md`, update the wording in `PROJECT.md`, `EVIDENCE.md` and the deck only to what Bob concluded.
