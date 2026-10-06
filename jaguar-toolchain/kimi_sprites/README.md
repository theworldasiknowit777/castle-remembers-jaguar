# Kimi's enemy art (vendored, read-only)

Verbatim copies of Kimi's frozen enemy sprites from `kimi/visual-refinement`
(`docs/visual/sprites/`), so the Gate 7 build never needs her branch. Never
edit these; re-copy from her branch if she ships a new version.

| File | Slot | Size | Kimi commit | Blob |
|---|---|---|---|---|
| `sentinel_skull.s` | `img_skull` (Sentinel Skull) | 16×16 | `ad01114` | `c705425` |
| `img_guard.s` | `img_guard` (Fallen Guard) | 16×24 | `25e4298` | `660b5c5` |
| `img_heavy.s` | `img_heavy` (Heavy Fallen Guard) | 16×24 | `25e4298` | `5f9b5af` |
| `img_watcher.s` | `img_watcher` (Stone Watcher) | 16×24 | `25e4298` | `47fca44` |
| `img_wraith.s` | `img_wraith` (Judgment Wraith) | 16×24 | `25e4298` | `0d877c6` |

`tools/mkart.py` imports exactly these files (V7 wave 1: enemies) into the
existing slots in `castle_art.inc`. No other Kimi art is integrated yet.
