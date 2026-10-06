; hud_icons.s - V6 HUD memory-row icons (kimi/visual-refinement)
; Six 8x8 bitmask icons, 8 bytes each, bit 7 = leftmost column.
; Order: doors, levers, pace, guards, traps, chests.
; Colour equates: lit + dim per category (VJ-verified).
; NOT linked - Claude wires HUD state; Bob Checkpoint B only if the
; renderer needs new protected buffers or OP changes.

HUD_DOORS   _LIT equ     $F8FF
HUD_DOORS   _DIM equ     $F859
HUD_LEVERS  _LIT equ     $EAE7
HUD_LEVERS  _DIM equ     $EA51
HUD_PACE    _LIT equ     $2BDD
HUD_PACE    _DIM equ     $2B4D
HUD_GUARDS  _LIT equ     $E2DD
HUD_GUARDS  _DIM equ     $E24D
HUD_TRAPS   _LIT equ     $53C9
HUD_TRAPS   _DIM equ     $5346
HUD_CHESTS  _LIT equ     $7CC4
HUD_CHESTS  _DIM equ     $7C46

HUD_FLASH    equ     $77F1   ; STAR white intensify ring

hud_icons:
        dc.b    $3C,$60,$60,$6C,$6C,$6C,$6C,$6C   ; doors
        dc.b    $06,$0C,$18,$30,$60,$C0,$FE,$7C   ; levers
        dc.b    $44,$66,$33,$19,$19,$33,$66,$44   ; pace
        dc.b    $3C,$7E,$66,$7E,$3C,$18,$3C,$00   ; guards
        dc.b    $49,$49,$DB,$DB,$FF,$00,$AA,$55   ; traps
        dc.b    $7E,$FF,$99,$FF,$FF,$DB,$FF,$7E   ; chests
