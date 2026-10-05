# Castle Remembers — Five-Floor Visual Production Plan

**Branch:** `kimi/visual-refinement` · **Owner of this document:** Kimi (visual production)
**Canon reference:** `original/index.html` (immutable) · **Hardware baseline:** Gate 6 (`gate6_castle.s`)

---

## 0. Canon preservation — expand, never replace

Canonical references: <https://topilcreations.itch.io/castleremembers>, `original/index.html`,
and the official target-look sheets in `docs/visual/reference/` (§10).

**Preserve (non-negotiable):**

- **Name & voice.** THE CASTLE REMEMBERS. The whisper speaker ("…it has watched you N times")
  and the win release — "THE CASTLE FORGETS …for now." — are canon text.
- **Canon taglines (from the official sheets):** "THE PAST WATCHES. THE CASTLE LEARNS." ·
  "CAN YOU ESCAPE?" · "THE SAME MAN. A DEADLIER CASTLE." · "A GAME THAT REMEMBERS YOU." ·
  "SOME CASTLES HAVE WALLS. THIS ONE HAS MEMORY." · "CLIMB. EXPLORE. ADAPT. SURVIVE. ESCAPE."
- **Canon loop:** EXPLORE → INTERACT → SURVIVE → ASCEND → ESCAPE → ADAPT → REMEMBER → DIE.
- **Structure.** Five floors: F1/F3 choice floors (two doors hiding ladders), F2/F4 lever
  floors (gate blocks the centre ladder, two levers), F5 exit door onto the battlements.
  Reach the top floor to escape. Every run reshapes the castle.
- **Play.** Climb ladders, open doors, act, avoid guards and traps (spikes, trapped chests
  and levers, archers), chests and shards; death rebuilds a hardened castle.
- **Adaptation categories (canon):** favored door side, trusted lever, rushing, waiting,
  slipping past, trap-springing, chest-opening.
- **Hero identity.** The Visigothic warrior: nasal helmet with gold cross inlay, chainmail,
  fur cloak, round shield with gold rampant-beast emblem, sword. The Jaguar CRY16 hero sprite
  stays unchanged; the poster's 8-frame animation strip (IDLE/WALK/RUN/JUMP/CLIMB/ATTACK/
  HURT/DEATH) is a **future owner-approved expansion only** (see §7, V7).
- **Heraldry.** Gold rampant beast on deep red — the recurring banner/shield emblem.
- **Art direction.** "Visigothic pixel look, all procedural"; palette relationships: cool
  slab stone warmed by torchlight, red cloak/banners, gold judgment accents, sunset
  battlements. The poster's own "COLOR PALETTE (CRY16)" swatches (greys, deep red, browns,
  tan, gold, cream) confirm the warm-axis anchor strategy of §2.

**Expand for Jaguar (never replace):** deeper ashlar and horseshoe-arch architecture, the
official enemy family given castle-native sprites, traps rendered as architecture, the
gold-vein path on F5, distinct per-floor color identities. The canon sunset sky
(`#f2a65a`/`#c8474a` — warm-axis hues, feasible in CRY16) targets the F5 battlement
backdrop in milestone V2.

---

## 1. Canon structure (from the original game)

| Floor | Type | Canon mechanics | Mood target |
|---|---|---|---|
| 1 | CHOICE | Left/right doors hiding ladders; first enemy pressure; chest | Grounded, inhabited, worn — home ground |
| 2 | LEVER | Gate blocks centre ladder; two levers | Cool, exposed gallery; rising tension |
| 3 | CHOICE | Second route choice; adaptation hardens favored side | The castle visibly *aware*; hostile asymmetry |
| 4 | LEVER | Harsher gate/lever chamber; archer canon | Dark, dangerous, warning motifs |
| 5 | EXIT | Final door onto battlements; sunset sky; strongest guard | Solemn, ceremonial, gold judgment |

Canon adaptation (visual targets): favored door corridors gain spikes / bricked-up doors /
guards; trusted levers become trapped (knob color cue); rushing adds ladder-flanking spikes
that retract for waiters; waiting shortens gate timers; chests become mimics (red clasp cue);
top guard patrols widen.

## 2. CRY16 palette discipline

All colors anchor to values proven on-screen in Gates 1–6. **Important:** real Jaguar CRY16
decoding renders `$CE7B` as sage-green-grey (verified against Gate 6 runtime screenshots), not
the warm grey my offline preview tool approximates. Every chroma-shifted value below is
**VERIFY-ON-SCREEN** with a documented grey-axis fallback. Bob adjudicates during integration.

Anchor groups: **N** `$CE..` stone · **G** `$CF..` gold/cream · **W** `$D6/$DA..` warm mids ·
**R** `$F0..` deep red · **K** greys (`$36../$39../$4E..`, chroma off).

The official hero sheet's "COLOR PALETTE (CRY16)" row (three greys, deep red, two browns,
tan, gold, cream) validates these groups — the shipped look lives entirely on the CRY warm
axis plus greys.

## 3. Five-floor identities (floor bitmap level)

Color script follows the official five-floor sheet (`ref_castle_a.png`): the castle's stone is
one material; **light and dressing carry the per-floor identity** (torch warmth, banners,
eery glow, shadow depth, gold ceremony).

| Floor | Base | Highlight | Mortar | Wear/accent | Signature dressing |
|---|---|---|---|---|---|
| 1 Gatehouse | `$CE7B` + `$D27B` warm tiles | `$CE9C` | `$3943` | `$CE52` pits, `$4238` groove, `$F001` stud | Worn polished path at spawn; running-bond ashlar ✅ **implemented in V0**; red rampant-beast banners + torch warmth arrive with V2 bands |
| 2 Gallery | `$C66B` cool (fallback `$4E6B`) | `$C684` restrained | `$2C33` damp | `$3601` cracks, `$3A4B` damp blotches | Amber torch gallery: columns + chandelier (V2); lever/gate ironwork `$4E1C`; two structural cracks |
| 3 Awareness | `$CE6F` neutral-dark | `$CE88` | `$3943` | Watcher-gold `$CF8B` eye-motifs, sparse | Eerie green cast — CRY's sage decode of low-R values may carry this; **VERIFY-ON-SCREEN**; deliberate asymmetric damage; favored-side dressing slots |
| 4 Pressure | `$CE4A` dark | `$CE6B` minimal | `$2A2B` near-black | `$F001` warning grooves, iron `$4E1C` | Poster reads violet-dark; saturated violet is **not CRY-feasible** — approximate with dark grey + deep-red accents (**VERIFY**); harsh grid; trap mouths; red inlay warnings near levers |
| 5 Judgment | `$D28B` pale (fallback `$CE8B`) | `$D6C8` cream | `$4433` fine | Gold vein `$CF6B→$CF9A→$CFCB` brightening toward exit | Ceremonial order; great horseshoe-arch doorway; exit flanked by `$F001` studs; vein rhymes with WIN flash |

All floors keep the proven 8-row silhouette: highlight cap / course A / mortar / course B /
mortar / shadow base. 16 px tile grid; ≥`$18` intensity steps; `$0000` never used in floor data.

## 4. Enemy family — official roster (per `ref_castle_a.png`)

| Enemy | Floor | Silhouette | Palette | Status |
|---|---|---|---|---|
| Sentinel Skull | 1 | Round cranium, gold-lit eyes | `$3601` outline, `$CE7B/$CE9C` bone, `$CFCB` eyes, `$F001` sockets | ✅ **V0 implemented** |
| Fallen Guard | 2–3 | Armored knight, red shield, broken stance | `$4E1C` iron, `$F001` shield red, `$D645` plume remnant | Designed, needs buffer (Bob) |
| Stone Watcher | 3–4 | Square turret head statue, single gold eye | `$CE7B/$3943` stone, `$CFCB` eye | Designed, needs buffer (Bob) |
| Judgment Wraith | 5 | Tall narrow hooded pursuer, inner glow | `$3601` body, `$CFCB` core, `$F001` trim | Designed, needs buffer (Bob) |
| Castle Hound | 2/4 patrol | Low four-legged runner — widest, lowest silhouette | `$4E1C` dark body, `$CE52` mid, `$CFCB` eyes | New from official sheet; design next |

The F3 winged creature on the sheet reads as ambient castle wildlife (bat); treat as V2
backdrop dressing unless Claude assigns it behavior. Canon guards/archers map onto this
family; behaviors remain Claude's code.

Pixel maps committed at `docs/visual/sprites/*.s` (drop-in data fragments generated by
`jaguar-toolchain/tools/enemy_family.py`; sheet preview: `docs/visual/previews/v1_enemy_family.png`).
Not linked into the game — Bob allocates buffers at V3.

## 5. Trap visual language — official roster (per `ref_castle_a.png`)

- **Spikes** — stone-tooth `$CE9C` tips on `$3943` bed; retracted = flush dark slots.
- **Falling Block** — ceiling masonry slab with `$F001` warning groove and cracked seam.
- **Flame Hazard** — sconce-mounted jet: `$CFCB` core, `$F001` edge, `$D645` mid (CRY-safe flame).
- **Swinging Blade** — chained crescent: `$4E1C` iron arm, `$CE9C` edge glint, chain links `$3943`.

Traps read as castle architecture, never pasted-on arcade objects. Trapped chest/lever keep
canon tells: red clasp `$F001`, warm trap knob `$D645`.

## 6. Making adaptation visible (design slots, not code)

Visual responses the art will support once Claude wires behavior: defensive dressing density on
the favored route, bricked door texture variant, sealed vs. open door frames, harsher lighting
emphasis, fortified ladder mouths. Each is a pixel-data variant; selection logic is a handoff to
Claude/Bob.

## 7. Milestone roadmap

| MS | Content | Dependency class |
|---|---|---|
| **V0** ✅ | In-place floor + enemy pixel redesign (this branch) | None — SAFE VISUAL DATA CHANGE |
| V1 | Five per-floor floor bitmaps (§3) | Needs Claude five-floor code + **Bob memory map** (new buffers) |
| V2 | Environment bands: walls, arches, banners, ladders, doors, gates, F5 sunset | **Bob OP/bandwidth + phrase values**; object-list addresses untouched |
| V3 | Enemy family split (§4, incl. Castle Hound) | **Bob buffers**; Claude spawn/behavior hooks |
| V4 | Trap visuals (§5) | Claude trap behavior + **Bob buffers** |
| V5 | Adaptation dressing + Floor 5 judgment/WIN presentation | Claude hooks + Bob integration; BG/flash logic untouched |
| V6 | Title screen + whisper presentation ("…it has watched you N times", "THE CASTLE FORGETS") | Kimi glyph/banner design; **Claude/Bob** text rendering + state hooks |
| V7 | Hero animation frames (IDLE/WALK/RUN/JUMP/CLIMB/ATTACK/HURT/DEATH per hero sheet) | **Owner approval required** (hero is protected); then Claude animation code + Bob buffers |

## 8. Findings preserved for Bob (do not fix in visual lane)

1. **Overlap:** `PIX_FLOOR=$008000` + 5120 B reaches `$009400` exclusive; `PIX_ENEMY=$009000`
   appears to overlap it. Unexamined, unrepaired. V0 floor rows 6–7 stay uniform dark so the
   overlap region remains visually flat either way.
2. **Truncated enemy table (found in V0):** committed Gate 6 `enemy_pixels` was 64 `dc.l` =
   **256 bytes**, but the copy loop moves 128 longwords = **512 bytes** — an over-read of 256
   bytes into `hero_pixels`. V0's table is the full 512 bytes the code expects. Bob to confirm
   what the baseline actually displayed and whether Gates 4–5 share the defect.
3. Offline preview tool (`jaguar-toolchain/tools/cry_preview.py`) uses an **approximate**
   CRY16→RGB decode; runtime screenshots show true decode is greener. Structure previews only.

## 9. Boundaries (unchanged)

No visual work touches: OLP setup, TOM/JERRY registers, video timing, phrase encoding formulas,
controller logic, gravity/collision, `SIDE_BIAS`/`DEATH_COUNT`, death/respawn, object-list
memory addresses, DRAM allocation. Anything needing those becomes a written handoff to
Claude/Bob. Hero sprite is preserved unchanged.

## 10. Reference assets (official target-look sheets)

| File | Content |
|---|---|
| `docs/visual/reference/ref_castle_a.png` | Five-floor cross-section poster: floor names/copy, enemy roster, trap roster, "A LIVING CASTLE" feature list, canon loop |
| `docs/visual/reference/ref_castle_b.png` | Hero sheet: Visigothic warrior details, CRY16 palette swatches, 8-frame sprite concept, Floor 1 gatehouse mockup, UI portrait |

These sheets are the visual target. All palette/identity decisions above trace to them; where
CRY16 cannot reproduce a poster hue (F3 teal, F4 violet), the nearest warm-axis/grey
approximation is marked VERIFY-ON-SCREEN and Bob adjudicates at integration.
