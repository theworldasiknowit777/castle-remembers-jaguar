# V6 HUD Memory-Row Spec — Castle Remembers (Jaguar)

Six-category memory HUD: **doors, levers, pace, guards, traps, chests/greed**.
Mockups: `v6h_normal/whisper/rebuild/multi/late.png`. Icons: `hud_icons.s`.
Content/mockup only — Claude wires category state; Bob Checkpoint B only if
the renderer needs new protected buffers or OP changes.

## Layout contract

- Row band **y = 224..239** (below the floor slab at row 194; never covers
  hero, enemies, doors, levers, ladders or holes).
- Six blocks, 21px each, 28px apart, centred (x0 = 27). Whole row = 266px.
- Block: 8×8 icon at (x, y+2), three 3×3 pips at (x+10+4·n, y+4).
- Pressure 0–3: **0** = dim icon, all pips hollow · **1–3** = lit icon + n lit
  pips. The pips ARE the tier counter Claude already maintains.
- **Intensify**: when a category gains a tier, ring the newest pip in
  `HUD_FLASH` white for ~0.5 s, then settle. No numbers anywhere.

## Palette (VJ-verified; five reserved by Claude, chests proposed)

| Category | Lit | Dim | Icon |
|---|---|---|---|
| doors | `$F8FF` | `$F859` | arch door |
| levers | `$EAE7` | `$EA51` | lever throw |
| pace | `$2BDD` | `$2B4D` | motion chevrons |
| guards | `$E2DD` | `$E24D` | helm |
| traps | `$53C9` | `$5346` | spike teeth |
| chests | `$7CC4` | `$7C46` | clasped chest |

## Coexistence with the message band

- Whispers/titles draw at y 8–22 (top) — the HUD row never overlaps.
- Prompts draw above objects (y ≥ 130); the HUD row stays at the bottom.
- Rebuild/death/win screens may keep the row visible as a memory summary
  (see `v6h_rebuild.png`) — Claude's choice; the row is passive there.
- Subordinate to gameplay: 16 px tall, saturated colour only where a tier
  is active; dormant categories sit near-black.
