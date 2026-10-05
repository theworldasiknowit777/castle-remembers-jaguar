# Castle Remembers — Five-Floor Visual Production Plan

**Branch:** `kimi/visual-refinement` · **Owner of this document:** Kimi (visual production)
**Canon reference:** `original/index.html` (immutable) · **Hardware baseline:** Gate 6 (`gate6_castle.s`)

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

## 3. Five-floor identities (floor bitmap level)

| Floor | Base | Highlight | Mortar | Wear/accent | Signature dressing |
|---|---|---|---|---|---|
| 1 Gatehouse | `$CE7B` + `$D27B` warm tiles | `$CE9C` | `$3943` | `$CE52` pits, `$4238` groove, `$F001` stud | Worn polished path at spawn; running-bond ashlar ✅ **implemented in V0** |
| 2 Gallery | `$C66B` cool (fallback `$4E6B`) | `$C684` restrained | `$2C33` damp | `$3601` cracks, `$3A4B` damp blotches | Two structural cracks; lever/gate ironwork `$4E1C`; no warm accents |
| 3 Awareness | `$CE6F` neutral-dark | `$CE88` | `$3943` | Watcher-gold `$CF8B` eye-motifs, sparse | Deliberate asymmetric damage; favored-side dressing slots for adaptation |
| 4 Pressure | `$CE4A` dark | `$CE6B` minimal | `$2A2B` near-black | `$F001` warning grooves, iron `$4E1C` | Harsh regular grid; trap-ready floor mouths; red inlay warnings near levers |
| 5 Judgment | `$D28B` pale (fallback `$CE8B`) | `$D6C8` cream | `$4433` fine | Gold vein `$CF6B→$CF9A→$CFCB` brightening toward exit | Ceremonial order; exit flanked by `$F001` studs; vein rhymes with WIN flash |

All floors keep the proven 8-row silhouette: highlight cap / course A / mortar / course B /
mortar / shadow base. 16 px tile grid; ≥`$18` intensity steps; `$0000` never used in floor data.

## 4. Enemy family (16×16 CRY16 each)

| Enemy | Floor | Silhouette | Palette | Status |
|---|---|---|---|---|
| Sentinel Skull | 1 | Round cranium, gold-lit eyes | `$3601` outline, `$CE7B/$CE9C` bone, `$CFCB` eyes, `$F001` sockets | ✅ **V0 implemented** |
| Fallen Guard | 2–3 | Angular toppled helm + spear stub | `$4E1C` iron, `$D645` plume remnant, dim `$CF8B` slit | Designed, needs buffer (Bob) |
| Stone Watcher | 3–4 | Square turret head, single gold eye | `$CE7B/$3943` stone, `$CFCB` eye | Designed, needs buffer (Bob) |
| Judgment Wraith | 5 | Tall narrow hood, inner glow | `$3601` body, `$CFCB` core, `$F001` trim | Designed, needs buffer (Bob) |

Canon guards/archers map onto this family; behaviors remain Claude's code.

## 5. Trap visual language (architecture-native)

- **Retracting spikes** — stone-tooth `$CE9C` tips on `$3943` bed; retract = flush dark slots.
- **Crushing masonry** — ceiling block with `$F001` warning groove.
- **Flame jet** — sconce-mounted: `$CFCB` core, `$F001` edge, `$D645` mid (CRY-safe flame).
- **Collapsing floor** — cracked tiles: `$3601` fissures + sag line; matches Floor 2/4 crack language.
- **Trapped chest / lever** — canon cues: red clasp `$F001`, trap knob warm `$D645`.

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
| V2 | Environment bands: walls, arches, ladders, doors, gates | **Bob OP/bandwidth + phrase values**; object-list addresses untouched |
| V3 | Enemy family split (§4) | **Bob buffers**; Claude spawn/behavior hooks |
| V4 | Trap visuals (§5) | Claude trap behavior + **Bob buffers** |
| V5 | Adaptation dressing + Floor 5 judgment/WIN presentation | Claude hooks + Bob integration; BG/flash logic untouched |

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
