# Owner handoff

## Pinned candidate

Use Gate 7 commit `7aaaa30cf5a91bdef198e9fcbeae807353836ad6` for the demo unless
the owner intentionally selects and verifies another candidate. It is a
separate branch and is not merged by this submission-documentation work.

## Checks completed October 13

- `python jaguar-toolchain/tools/check_cof.py jaguar-toolchain/gate7_castle/gate7_castle.cof` passed.
- `python jaguar-toolchain/tools/test_gate7.py route` passed a normal five-floor escape.
- Fresh `boot`, `controls`, `band_guards`, `band_floors`, `hero_facing`, and
  `hero_climb` scenarios passed.
- `python jaguar-toolchain/tools/soak_gate7.py 1000 1 18` reported no invariant violations.
- The normal COF cold-booted in local Virtual Jaguar at 59.9-60 FPS.

The historical 20,000-frame soak and 34/34 milestone counts remain historical
DEVLOG results, not fresh October 13 reruns. Cross-build comparison scenarios
need a writable temporary directory and `KIMI_REF=origin/kimi/visual-refinement`
when the Kimi branch exists only as a remote-tracking ref; their full runs exceed
the current execution window and are not claimed as fresh passes.

## Owner actions before submission

1. Test the local browser wrapper in `emulatorjs-local/` with the exact pinned
   COF, then select an approved hosting account and publish only after a
   second-device check. The resulting URL must be free and usable by judges.
2. Record an English demo of the normal build, keep it at or below three
   minutes, upload it to the owner's YouTube account, and verify playback while
   signed out. Put the verified watch URL in the form and submission documents.
3. Obtain Bob or owner decisions for the remaining low-level audit items: VC
   field-bit mask, NTSC/PAL configuration byte, and final SHADOW-to-LIVE
   validation. Do not represent these as independently signed off until they
   are.
4. Recheck the repository, PDF, live URL, and video URL just before the
   October 18 23:59 Eastern deadline, then freeze the submitted artifacts.

No proposed Gate 7 enhancement is a competition requirement. The remaining
requirements are the live URL, video, owner-controlled publication, and final
approval decisions above.
