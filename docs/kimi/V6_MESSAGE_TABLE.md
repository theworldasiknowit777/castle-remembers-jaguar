# V6 Canon Message Table — Castle Remembers (Jaguar)

Branch `kimi/visual-refinement`. Font contract: cell 6×8, advance 6 px,
line pitch 10 px, face `$98BD`, relief `$3601` (see `font_data.s`).
Canon source: `original/index.html`. `#` marks a runtime digit substitution.
Content only — Claude owns the message/state system; Bob Checkpoint B for
the render path. No OP objects or buffers are allocated here.

Positions: `top` = y 14, centered · `crown` = y 8, centered · `center` =
centered block · `above-object` = 10 px above the interaction object,
clamped to screen · `bottom` = y 226, centered.

| ID | Text | px | Type | Position | Pri | Dur s | Wrap line 2 |
|---|---|---|---|---|---|---|---|
| `MSG_TITLE_A` | THE CASTLE | 59 | screen | center y=88 | 5 | 0 |  |
| `MSG_TITLE_B` | REMEMBERS | 53 | screen | center y=102 | 5 | 0 |  |
| `MSG_TITLE_SUB` | CLIMB. LEARN. ADAPT. ESCAPE. | 167 | screen | center y=120 | 4 | 0 |  |
| `MSG_TITLE_GO` | PRESS PAUSE TO BEGIN | 119 | screen | center y=200 | 4 | 0 |  |
| `MSG_OBSERVED` | THE CASTLE OBSERVED YOU | 137 | screen | center y=96 | 5 | 1.6 |  |
| `MSG_REBUILD` | RECONSTRUCTING… | 89 | screen | center y=140 | 5 | 0 |  |
| `MSG_REMEMBERS` | THE CASTLE REMEMBERS | 119 | end | center y=88 | 5 | 0 |  |
| `MSG_WATCHED1` | …IT HAS WATCHED YOU 1 TIME. | 161 | end | center y=104 | 4 | 0 |  |
| `MSG_WATCHEDN` | …IT HAS WATCHED YOU # TIMES. | 167 | end | center y=104 | 4 | 0 |  |
| `MSG_FORGETS` | THE CASTLE FORGETS | 107 | end | center y=88 | 5 | 0 |  |
| `MSG_FORNOW` | …FOR NOW. | 53 | end | center y=104 | 5 | 0 |  |
| `MSG_ESCAPED` | YOU ESCAPED | 65 | end | center y=88 | 5 | 0 |  |
| `MSG_FELL` | YOU FELL | 47 | end | center y=88 | 5 | 0 |  |
| `MSG_RISE` | RISE AGAIN | 59 | end | center y=210 | 3 | 0 |  |
| `MSG_ENTERAGAIN` | ENTER AGAIN | 65 | end | center y=210 | 3 | 0 |  |
| `MSG_W_DOOR_L` | …YOU ALWAYS GO LEFT. | 119 | whisper | top | 3 | 2.6 |  |
| `MSG_W_DOOR_R` | …YOU ALWAYS GO RIGHT. | 125 | whisper | top | 3 | 2.6 |  |
| `MSG_W_DOOR_GONE_L` | …THE LEFT WAY IS GONE. | 131 | whisper | top | 3 | 2.6 |  |
| `MSG_W_DOOR_GONE_R` | …THE RIGHT WAY IS GONE. | 137 | whisper | top | 3 | 2.6 |  |
| `MSG_W_DOOR_GIFT_L` | …THE LEFT DOOR WAS LEFT OPEN FOR YOU. | 221 | whisper | top | 3 | 2.6 |  |
| `MSG_W_DOOR_GIFT_R` | …THE RIGHT DOOR WAS LEFT OPEN FOR YOU. | 227 | whisper | top | 3 | 2.6 |  |
| `MSG_W_LEVER_TRUST` | …IT KNOWS WHICH LEVER YOU TRUST. | 191 | whisper | top | 3 | 2.6 |  |
| `MSG_W_LEVER_HERE` | …THE LEVER YOU TRUST IS HERE TOO. | 197 | whisper | top | 3 | 2.6 |  |
| `MSG_W_RUSH` | …YOU NEVER STOP TO LOOK. | 143 | whisper | top | 3 | 2.6 |  |
| `MSG_W_WAIT` | …YOU LIKE TO WAIT. | 107 | whisper | top | 3 | 2.6 |  |
| `MSG_W_BRACE` | …THE GUARDS HAVE FELT YOUR HANDS. | 197 | whisper | top | 3 | 2.6 |  |
| `MSG_W_WATCH` | …THE GUARDS KNOW YOU SLIP PAST. | 185 | whisper | top | 3 | 2.6 |  |
| `MSG_W_TRAP` | …THE SPIKES GREW FOR YOU. | 149 | whisper | top | 3 | 2.6 |  |
| `MSG_W_CHEST` | …IT SAW YOU OPEN EVERY BOX. | 161 | whisper | top | 3 | 2.6 |  |
| `MSG_W_EXIT_MOVED` | …THE WAY OUT HAS MOVED. | 137 | whisper | top | 4 | 2.6 |  |
| `MSG_W_EXIT_GUARD` | …IT WILL NOT LET YOU LEAVE SO EASILY. | 221 | whisper | top | 4 | 2.6 |  |
| `MSG_O_FIRST` | IT HAS NOT SEEN YOU YET. | 143 | observation | center y=118 | 4 | 2.0 |  |
| `MSG_O_DOOR_L` | YOU WENT LEFT AGAIN. | 119 | observation | center y=118 | 4 | 2.0 | THE LEFT SIDE STAYS ARMED. |
| `MSG_O_DOOR_R` | YOU WENT RIGHT AGAIN. | 125 | observation | center y=118 | 4 | 2.0 | THE RIGHT SIDE STAYS ARMED. |
| `MSG_O_LEVER_L` | YOU PULLED THE LEFT LEVER AGAIN. | 191 | observation | center y=118 | 4 | 2.0 | IT STAYS ARMED. |
| `MSG_O_LEVER_R` | YOU PULLED THE RIGHT LEVER AGAIN. | 197 | observation | center y=118 | 4 | 2.0 | IT STAYS ARMED. |
| `MSG_O_RUSH` | YOU RUSHED. THE AMBUSH STAYS. | 173 | observation | center y=118 | 4 | 2.0 |  |
| `MSG_O_WAIT` | YOU WAITED. THE GATES KEEP CLOSING. | 209 | observation | center y=118 | 4 | 2.0 |  |
| `MSG_O_TRAP` | YOU SPRANG THE TRAPS. THE SPIKES STAY. | 227 | observation | center y=118 | 4 | 2.0 |  |
| `MSG_O_CHEST` | YOU OPENED EVERY CHEST. IT STAYS PACKED. | 239 | observation | center y=118 | 4 | 2.0 |  |
| `MSG_O_GUARD` | A GUARD CAUGHT YOU ON FLOOR #. | 179 | observation | center y=118 | 4 | 2.0 |  |
| `MSG_O_ARROW` | AN ARROW FOUND YOU ON FLOOR #. | 179 | observation | center y=118 | 4 | 2.0 |  |
| `MSG_O_WIN_DOOR_L` | YOU ESCAPED THROUGH LEFT DOORS. | 185 | observation | center y=118 | 4 | 2.0 |  |
| `MSG_O_WIN_DOOR_R` | YOU ESCAPED THROUGH RIGHT DOORS. | 191 | observation | center y=118 | 4 | 2.0 |  |
| `MSG_O_WIN_LEVER_L` | YOU ESCAPED PULLING THE LEFT LEVER. | 209 | observation | center y=118 | 4 | 2.0 |  |
| `MSG_O_WIN_LEVER_R` | YOU ESCAPED PULLING THE RIGHT LEVER. | 215 | observation | center y=118 | 4 | 2.0 |  |
| `MSG_O_WIN_RUSH` | YOU ESCAPED WITHOUT STOPPING. | 173 | observation | center y=118 | 4 | 2.0 |  |
| `MSG_O_WIN_WAIT` | YOU ESCAPED BY WAITING. | 137 | observation | center y=118 | 4 | 2.0 |  |
| `MSG_O_WIN_BRACE` | YOU ESCAPED BY SHOVING GUARDS. | 179 | observation | center y=118 | 4 | 2.0 |  |
| `MSG_O_WIN_WATCH` | YOU ESCAPED BY SLIPPING PAST. | 173 | observation | center y=118 | 4 | 2.0 |  |
| `MSG_O_WIN_TRAP` | YOU SPRANG TRAPS AND STILL ESCAPED. | 209 | observation | center y=118 | 4 | 2.0 |  |
| `MSG_O_WIN_CHEST` | YOU ESCAPED AFTER OPENING EVERY CHEST. | 227 | observation | center y=118 | 4 | 2.0 |  |
| `MSG_F1` | FLOOR 1 - GATEHOUSE | 113 | title | crown | 4 | 2.0 |  |
| `MSG_F2` | FLOOR 2 - GALLERY | 101 | title | crown | 4 | 2.0 |  |
| `MSG_F3` | FLOOR 3 - HALL OF ECHOES | 143 | title | crown | 4 | 2.0 |  |
| `MSG_F4` | FLOOR 4 - VAULT | 89 | title | crown | 4 | 2.0 |  |
| `MSG_F5` | FLOOR 5 - JUDGMENT | 107 | title | crown | 4 | 2.0 |  |
| `MSG_P_OPEN` | L - OPEN | 47 | prompt | above-object | 2 | 0 |  |
| `MSG_P_PULL` | L - PULL | 47 | prompt | above-object | 2 | 0 |  |
| `MSG_P_SHOVE` | L - SHOVE | 53 | prompt | above-object | 2 | 0 |  |
| `MSG_P_CLIMB` | S - CLIMB | 53 | prompt | above-object | 2 | 0 |  |
| `MSG_P_DOWN` | X - DOWN | 47 | prompt | above-object | 2 | 0 |  |
| `MSG_P_SEALED` | SEALED | 35 | prompt | above-object | 2 | 0 |  |
| `MSG_P_EXIT` | EXIT | 23 | prompt | above-object | 2 | 0 |  |

## Canon originals (where Jaguar text was shortened)

Meanings preserved; dynamic counts/times dropped or reduced to `#`.

| ID | Canon original (original/index.html) |
|---|---|
| `MSG_TITLE_GO` | TAP OR PRESS ENTER (binding is Claude's; PAUSE suggested) |
| `MSG_REBUILD` | RECONSTRUCTING + animated dots |
| `MSG_WATCHED1` | …it has watched you 1 time. |
| `MSG_WATCHEDN` | …it has watched you N times. — # = runtime digit substitution |
| `MSG_FORNOW` | …for now. |
| `MSG_RISE` | TAP TO RISE AGAIN |
| `MSG_ENTERAGAIN` | TAP TO ENTER AGAIN |
| `MSG_W_DOOR_L` | …you always go left. |
| `MSG_W_DOOR_R` | …you always go right. |
| `MSG_W_DOOR_GONE_L` | …the left way is gone. (door tier 3: bricked) |
| `MSG_W_DOOR_GONE_R` | …the right way is gone. |
| `MSG_W_DOOR_GIFT_L` | …the left door was left open for you. (door tier 1-2 gift) |
| `MSG_W_DOOR_GIFT_R` | …the right door was left open for you. |
| `MSG_W_LEVER_TRUST` | …it knows which lever you trust. |
| `MSG_W_LEVER_HERE` | …the lever you trust is here too. |
| `MSG_W_RUSH` | …you never stop to look. |
| `MSG_W_WAIT` | …you like to wait. |
| `MSG_W_BRACE` | …the guards have felt your hands. |
| `MSG_W_WATCH` | …the guards know you slip past. |
| `MSG_W_TRAP` | …the spikes grew for you. |
| `MSG_W_CHEST` | …it saw you open every box. |
| `MSG_W_EXIT_MOVED` | …the way out has moved. |
| `MSG_W_EXIT_GUARD` | …it will not let you leave so easily. |
| `MSG_O_FIRST` | IT HAS NOT SEEN YOU YET. |
| `MSG_O_DOOR_L` | YOU WENT LEFT AGAIN (N OF M DOORS). THE LEFT SIDE STAYS ARMED. |
| `MSG_O_DOOR_R` | YOU WENT RIGHT AGAIN (N OF M DOORS). THE RIGHT SIDE STAYS ARMED. |
| `MSG_O_LEVER_L` | YOU PULLED THE LEFT LEVER AGAIN. IT STAYS ARMED. |
| `MSG_O_LEVER_R` | YOU PULLED THE RIGHT LEVER AGAIN. IT STAYS ARMED. |
| `MSG_O_RUSH` | YOU RUSHED (N% STANDING STILL). THE AMBUSH STAYS. |
| `MSG_O_WAIT` | YOU WAITED (N% STANDING STILL). THE GATES KEEP CLOSING. |
| `MSG_O_TRAP` | YOU SPRANG N TRAPS AND FELL ON FLOOR F. THE SPIKES STAY. |
| `MSG_O_CHEST` | YOU OPENED N CHESTS. THE CASTLE PACKED ONE FOR YOU. IT STAYS PACKED. |
| `MSG_O_GUARD` | A GUARD CAUGHT YOU ON FLOOR F. SHOVED X, SLIPPED PAST Y. |
| `MSG_O_ARROW` | AN ARROW FOUND YOU ON FLOOR F. SHOVED X, SLIPPED PAST Y. |
| `MSG_O_WIN_DOOR_L` | YOU ESCAPED THROUGH LEFT DOORS (N OF M). |
| `MSG_O_WIN_DOOR_R` | YOU ESCAPED THROUGH RIGHT DOORS (N OF M). |
| `MSG_O_WIN_LEVER_L` | YOU ESCAPED PULLING THE LEFT LEVER (N OF M). |
| `MSG_O_WIN_LEVER_R` | YOU ESCAPED PULLING THE RIGHT LEVER (N OF M). |
| `MSG_O_WIN_RUSH` | YOU ESCAPED IN T.Ts WITHOUT STOPPING (N% STILL). |
| `MSG_O_WIN_WAIT` | YOU ESCAPED IN T.Ts BY WAITING (N% STILL). |
| `MSG_O_WIN_BRACE` | YOU ESCAPED BY SHOVING N GUARDS. |
| `MSG_O_WIN_WATCH` | YOU ESCAPED BY SLIPPING PAST N GUARDS. |
| `MSG_O_WIN_TRAP` | YOU SPRANG N TRAPS AND STILL ESCAPED. |
| `MSG_O_WIN_CHEST` | YOU ESCAPED AFTER OPENING N OF M CHESTS. |
| `MSG_P_SEALED` | (bricked door: canon flavour, no canon string) |

## Whisper queue behaviour (canon)

- Whispers are title `THE CASTLE REMEMBERS` + sub-line, 2.6 s each, queued
  on run start (death merge) and on floor entry for that floor's tier notes.
- On escape: `THE CASTLE FORGETS` + `…for now.`, double-weight memory merge.
- Priority 4 whispers (exit moved / exit guarded) jump the queue.

## String data

`docs/visual/sprites/messages.s` — `MSG_*` index equates in table order,
then `msg_strings:` as 0-terminated ASCII (`$85` = ellipsis glyph, `#` kept
literal for Claude's digit substitution). Optional second line for wrapped
observations follows its parent as `<ID>_2`.
