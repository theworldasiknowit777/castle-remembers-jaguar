# Local EmulatorJS validation wrapper

This unhosted wrapper is for a local browser check of the pinned Gate 7
candidate `7aaaa30cf5a91bdef198e9fcbeae807353836ad6`. It is not a deployed game,
does not supply a judging URL, and does not bundle the candidate binary or any
emulator core.

## Local setup

1. Check out the pinned Gate 7 commit in a separate directory.
2. Create `docs/submission/emulatorjs-local/game/` beside `index.html`.
3. Copy that checkout's `jaguar-toolchain/gate7_castle/gate7_castle.cof` to
   `game/gate7_castle.cof` using a binary-safe copy.
4. From this directory, serve the files over HTTP, for example:

   ```powershell
   py -3 -m http.server 8080
   ```

5. Open `http://localhost:8080/` in a browser with internet access. The page
   requests EmulatorJS Stable assets from its public CDN and selects its
   documented Jaguar / `virtualjaguar` core.

The Virtual Jaguar libretro core documents `.cof` as a supported content
extension. A successful load still must be tested; this wrapper is not proof of
compatibility, a public deployment, or an organizer-approved live environment.

## Required local checks

- Cold boot to the Gate 7 title scene.
- Z/C movement, S jump/climb, X down/ACT, and L ACT.
- A door or lever interaction, ladder transition, death/rebuild, and reset.
- Repeat the check in a separate browser/device before publishing.

## Notices before any public deployment

- EmulatorJS and the Virtual Jaguar core are GPL-3.0 projects. Review and
  retain their current license and attribution requirements before bundling or
  self-hosting emulator assets.
- Do not expose a personal desktop, development credentials, or private source
  paths. Use an owner-approved hosting account and public URL only after the
  local check passes.
- Preserve the candidate's existing copyright, original baseline, contributor
  attribution, and IBM Bob evidence boundaries. Do not describe this wrapper as
  IBM Bob work or as a hardware certification.
