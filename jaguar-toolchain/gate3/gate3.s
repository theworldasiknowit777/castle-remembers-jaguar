; ============================================================
; gate3.s  —  Castle Remembers — Phase C: Joystick movement
; Target : Atari Jaguar (68000 + Tom/Jerry)
; Toolchain: RMAC 2.5.2 / RLN 1.7.7
; Load / Entry: $802000
;
; Phase B rendering path preserved VERBATIM.
; Phase C adds LEFT/RIGHT controller reading and updates
; the BITMAP XPOS field in phrase 1 each blanking window,
; while the phrase-0 HEIGHT/DATA refresh loop is unchanged.
;
; Object list layout (USERRAM $004000, phrase-aligned):
;   $004000  BITMAP phrase 0  (PH0: TYPE/YPOS/HEIGHT/LINK/DATA)
;   $004008  BITMAP phrase 1  (PH1: XPOS/DEPTH/PITCH/DWIDTH/IWIDTH)
;   $004010  STOP  phrase 0   (TYPE=4)
;   $004018  STOP  phrase 1   (zeros)
;
; BITMAP phrase 1 field layout (Tech Ref Rev.8 §3.3):
;   PH1 bits [11: 0]  = XPOS  (pixel-clock offset; display starts
;                               at HDB1=177, so XPOS=177 => left edge)
;   PH1 bits [14:12]  = DEPTH (2 = 4bpp, 4 = 16bpp CRY)
;   PH1 bits [17:15]  = PITCH (1 = contiguous phrases)
;   PH1 bits [27:18]  = DWIDTH (phrases per line, 1-based)
;   PH1 bits [37:28]  = IWIDTH (phrases per line)
;   Bits [63:38]      = FLAGS  (REFLECT, RMW, TRANS, RELEASE, …)
;
;   PH1_LO (low 32 bits of phrase 1) = bits [31:0]
;   Current: $4010C101  →  upper mask $4010C000, XPOS=$101=257
;
; Joystick protocol (Jerry $F14000, 16-bit register):
;   JOYSTICK is a 16-bit register.  To read the D-pad on Port 1,
;   select Row 0 by writing $817E.  Then read back the 16-bit word.
;   Row 0 controller matrix (active-LOW):
;     Bit 10 = LEFT  (J10)
;     Bit 11 = RIGHT (J11)
;     Bit  8 = UP    (J8 )  — not used this phase
;     Bit  9 = DOWN  (J9 )  — not used this phase
;   $817E = %1000 0001 0111 1110
;           bit15=1  (joy data enable)
;           bit14-8  = $01 (row 0 select, audio mute off)
;           bits7-0  = $7E (output enables; keeps audio enabled)
;
; hero_xpos at DRAM $000100 (word).  Starts at 257 (gate2 proven position).
; Speed: 2 pixel-clocks per frame.
; Clamp: XPOS_MIN=177 (left edge), XPOS_MAX=486 (right, 16px sprite fits).
; ============================================================

; ---- Tom registers -----------------------------------------
TOM             equ     $F00000
OLP             equ     TOM+$20         ; lo-word at $F00020, hi-word at $F00022
VC              equ     TOM+$06         ; vertical counter (half-lines, read-only)
OBF             equ     TOM+$26
VMODE           equ     TOM+$28
BORD1           equ     TOM+$2A
HDB1            equ     TOM+$38
HDB2            equ     TOM+$3A
HDE             equ     TOM+$3C
VDB             equ     TOM+$46
VDE             equ     TOM+$48
VI              equ     TOM+$4E
BG              equ     TOM+$58
INT1            equ     TOM+$E0
G_FLAGS         equ     TOM+$2100
G_CTRL          equ     TOM+$2114

; ---- Jerry registers ---------------------------------------
D_FLAGS         equ     $F1A100
D_CTRL          equ     $F1A114
J_INT           equ     $F10020
CONFIG          equ     $F14002
JOYSTICK        equ     $F14000         ; Jerry joystick register (16-bit)

; ---- NTSC timing (exact hello.s CJ values) -----------------
NTSC_WIDTH      equ     1229
NTSC_HMID       equ     787
NTSC_HEIGHT     equ     241
NTSC_VMID       equ     266

; ---- PAL timing --------------------------------------------
PAL_WIDTH       equ     1255
PAL_HMID        equ     821
PAL_HEIGHT      equ     287
PAL_VMID        equ     322

; ---- VMODE — CRY16+VIDEN+BGEN+PWIDTH4 ($0681) — proven in Gate-1/2 --
VMODE_VAL       equ     $0681

; ---- Object list and pixel data in USERRAM -----------------
OP_LIST         equ     $004000         ; phrase-aligned
PIX_DATA        equ     $008000         ; 24 rows * 4 phrases * 8 bytes = 768 bytes

; ---- Phase C: X-position limits (pixel-clocks) -------------
;   NTSC active display: HDB1=177 (left edge) to HDB1+326-1=502 (right edge).
;   TOM resolution confirmed by VJaguar log: 326 x 240 16bpp CRY.
;   Hero sprite is 16px wide.
;   XPOS_MIN = 177  (HDB1 — leftmost pixel column)
;   XPOS_MAX = 486  (502 - 16 = last column where full 16px sprite fits)
;   XPOS_START = 257  (gate2 proven starting position; HDB1+80)
XPOS_START      equ     257             ; gate2 proven starting position
XPOS_MIN        equ     177             ; left screen edge (HDB1)
XPOS_MAX        equ     486             ; right clamp: 502-16 (fits 16px sprite)
XPOS_SPEED      equ     2               ; pixel-clocks per frame

; ---- hero_xpos storage in DRAM (word) ----------------------
HERO_XPOS_ADDR  equ     $000100         ; word in DRAM, phrase-clear zone

; ---- Joystick row-select value for Row 0 (D-pad) -----------
;   Written to JOYSTICK ($F14000) as a 16-bit word.
;   $817E selects Row 0: Up/Down/Left/Right on Port 1.
;   Active-LOW: 0 = pressed, 1 = not pressed.
;   Bit 10 = LEFT (J10), Bit 11 = RIGHT (J11).
JOY_ROW0        equ     $817E

; ---- Phrase 0 (static values — unchanged from Phase B) -----
PH0_HI          equ     $00800008
PH0_LO          equ     $020606C0       ; YPOS=216 HEIGHT=24 LINK=$004010 DATA=$008000

; ---- Phrase 1 upper-bit mask (bits[31:12] of PH1_LO) -------
;   Full PH1_LO = $4010C101  →  upper = $4010C000, lower 12 = XPOS=$101
;   PH1_HI (bits[63:32]) = $00000000 always.
PH1_UPPER       equ     $4010C000       ; all PH1_LO bits except XPOS[11:0]

; ---- VDE halfline for NTSC ---------------------------------
VC_VDE          equ     507             ; NTSC VDE = VMID+HEIGHT = 266+241

        .text

; ============================================================
; Entry — Gate-1 (hello.s) startup sequence, then OP setup
; ============================================================
start:
        ; ---- Gate-1 sequence verbatim ---------------------

        ; Disable all maskable interrupts
        move.w  #$2700,sr

        ; Stop GPU
        move.l  #0,G_FLAGS
        move.l  #0,G_CTRL

        ; Stop DSP
        move.l  #$0001F800,D_FLAGS
        move.l  #0,D_CTRL

        ; Clear CPU interrupt pending
        move.l  #$1F000000,INT1

        ; Clear Jerry interrupt flags
        move.w  #$3F00,J_INT

        ; STOP object at DRAM $000000 (safety — OLP will be overwritten)
        move.l  #0,$000000
        move.l  #4,$000004              ; TYPE=4 in bits[2:0] of phrase

        ; Point OLP at $000000 initially (safe STOP)
        move.l  #0,OLP

        ; Clear OBF
        move.w  #0,OBF

        ; Clear border
        move.l  #0,BORD1

        ; Stack to top of DRAM
        lea     $1FFFFC,sp

        ; ---- Phase C: initialise hero X position ----------
        move.w  #XPOS_START,HERO_XPOS_ADDR

        ; ---- Phase B: copy hero pixel data to DRAM --------
        ;   16bpp CRY16, 16px wide = 32 bytes/row = 4 phrases/row.
        ;   24 rows * 32 bytes = 768 bytes = 192 longwords.
        lea     hero_pixels,a1
        lea     PIX_DATA,a0
        move.w  #191,d0                 ; 192 longwords - 1
.copy:  move.l  (a1)+,(a0)+
        dbra    d0,.copy

        ; ---- Phase B: write OP object list -----------------
        ;   Phrase 0: TYPE=0 YPOS=216 HEIGHT=24 LINK=>$004010 DATA=>$008000
        move.l  #PH0_HI,OP_LIST+0
        move.l  #PH0_LO,OP_LIST+4
        ;   Phrase 1: XPOS=XPOS_START DEPTH=4(16bpp) PITCH=1 DWIDTH=4 IWIDTH=4
        move.l  #0,OP_LIST+8
        move.l  #(PH1_UPPER|XPOS_START),OP_LIST+12
        ;   STOP phrase 0: TYPE=4
        move.l  #0,OP_LIST+16
        move.l  #4,OP_LIST+20
        ;   STOP phrase 1: zeros
        move.l  #0,OP_LIST+24
        move.l  #0,OP_LIST+28

        ; ---- Gate-2: point OLP at USERRAM object list -----
        ;   Must swap before writing: MOVE.L #$00004000 stores 0->$F00020
        ;   and $4000->$F00022 giving OLP=$40000000 — wrong.
        ;   swap d0 makes lo/hi correct: OLP = $00004000.
        move.l  #OP_LIST,d0             ; d0 = $00004000
        swap    d0                      ; d0 = $40000000
        move.l  d0,OLP                  ; $F00020=$4000, $F00022=$0000 => OLP=$00004000

        ; ---- Gate-1: NTSC/PAL video timing ----------------
        btst    #4,CONFIG
        beq.s   do_pal

do_ntsc:
        move.w  #NTSC_HMID-(NTSC_WIDTH/2)+4,HDB1
        move.w  #NTSC_HMID-(NTSC_WIDTH/2)+4,HDB2
        move.w  #(NTSC_WIDTH/2)-1+$0400,HDE
        move.w  #NTSC_VMID-NTSC_HEIGHT,VDB
        move.w  #NTSC_VMID+NTSC_HEIGHT,VDE
        bra.s   video_set

do_pal:
        move.w  #PAL_HMID-(PAL_WIDTH/2)+4,HDB1
        move.w  #PAL_HMID-(PAL_WIDTH/2)+4,HDB2
        move.w  #(PAL_WIDTH/2)-1+$0400,HDE
        move.w  #PAL_VMID-PAL_HEIGHT,VDB
        move.w  #PAL_VMID+PAL_HEIGHT,VDE

video_set:
        ; VI = max
        move.w  #$7FFF,VI

        ; BG = black
        move.w  #$0000,BG

        ; Enable video
        move.w  #VMODE_VAL,VMODE

; ============================================================
; Main loop — runs once per frame inside the blanking window.
;
; Each iteration:
;   1. Wait for VC to pass VDE (end of active picture → blanking)
;   2. Read JOYSTICK; update hero_xpos with clamping
;   3. Rebuild PH1_LO = PH1_UPPER | new_xpos; write to OP_LIST+12
;   4. Refresh phrase 0 (Phase-B HEIGHT/DATA fix — unchanged)
;   5. Wait for VC to re-enter picture (new frame)
;   6. Loop
;
; Register usage during loop:
;   d0 = VC scratch / joystick value
;   d1 = hero_xpos (word)
;   d2 = PH1_LO assembled value
; ============================================================

forever:
        ; ----------------------------------------------------------
        ; Step 1: wait until VC passes VDE — active picture finished
        ; ----------------------------------------------------------
.wait_pic:
        move.w  VC,d0
        cmp.w   #VC_VDE,d0
        blt.s   .wait_pic               ; loop while VC < 507

        ; ----------------------------------------------------------
        ; Step 2: read joystick and update hero X position
        ;   JOYSTICK is a 16-bit register at $F14000.
        ;   Write $817E to select Row 0 (D-pad: Up/Down/Left/Right).
        ;   Read back the 16-bit word; bits are active-LOW (0=pressed).
        ;   Bit 10 = LEFT (J10), Bit 11 = RIGHT (J11).
        ; ----------------------------------------------------------
        move.w  #JOY_ROW0,JOYSTICK      ; select Row 0, enable outputs
        move.w  JOYSTICK,d0             ; read Port 1 D-pad state (active-LOW)

        move.w  HERO_XPOS_ADDR,d1       ; d1.w = current xpos

        ; Test LEFT: bit 10 active-LOW (0 = pressed)
        btst    #10,d0
        bne.s   .check_right            ; bit SET = not pressed; skip
        sub.w   #XPOS_SPEED,d1
        cmp.w   #XPOS_MIN,d1
        bge.s   .check_right
        move.w  #XPOS_MIN,d1            ; clamp to left edge

.check_right:
        ; Test RIGHT: bit 11 active-LOW (0 = pressed)
        btst    #11,d0
        bne.s   .write_x                ; bit SET = not pressed; skip
        add.w   #XPOS_SPEED,d1
        cmp.w   #XPOS_MAX,d1
        ble.s   .write_x
        move.w  #XPOS_MAX,d1            ; clamp to right edge

.write_x:
        move.w  d1,HERO_XPOS_ADDR       ; persist updated xpos

        ; ----------------------------------------------------------
        ; Step 3: rebuild PH1_LO and write phrase 1 to object list
        ;   PH1_LO = PH1_UPPER (bits[31:12]) | xpos (bits[11:0])
        ;   PH1_HI is always $00000000.
        ; ----------------------------------------------------------
        move.l  #PH1_UPPER,d2
        and.w   #$0FFF,d1               ; guard: mask to 12 bits
        or.w    d1,d2                   ; inject XPOS into bits[11:0]
        move.l  #0,OP_LIST+8            ; PH1_HI = 0
        move.l  d2,OP_LIST+12           ; PH1_LO with new XPOS

        ; ----------------------------------------------------------
        ; Step 4: refresh phrase 0 (Phase-B HEIGHT/DATA fix —
        ;   OP zeroes HEIGHT after each frame; rewrite here in
        ;   blanking to restore it for the next frame.)
        ;   THIS BLOCK IS UNCHANGED FROM PHASE B.
        ; ----------------------------------------------------------
        move.l  #PH0_HI,OP_LIST+0
        move.l  #PH0_LO,OP_LIST+4

        ; ----------------------------------------------------------
        ; Step 5: wait for VC to wrap back below VDE (new frame)
        ; ----------------------------------------------------------
.wait_blank:
        move.w  VC,d0
        cmp.w   #VC_VDE,d0
        bge.s   .wait_blank             ; loop while VC >= 507

        bra     forever

; ============================================================
; Hero idle sprite — 16x24 pixels, 16bpp CRY16, 4 phrases/row
; 24 rows * 32 bytes = 768 bytes = 192 longwords.
; Stored in .text; copied to PIX_DATA ($008000) at init.
; Palette: 0=$0000(transp) 1=$3601(dark) 2=$D96C(skin) 3=$DA7A(sksh)
;          4=$E011(hair)   5=$F0A4(cloak) 6=$D645(tunic) 7=$D733(tush)
;          8=$D822(belt)   9=$CFCB(gold) 10=$4E1C(steel) 11=$D843(leath)
; ============================================================
hero_pixels:
        dc.l    $00000000,$00000000,$00000000,$E011E011
        dc.l    $E011E011,$00000000,$00000000,$00000000  ; row 00: ......hhhh......
        dc.l    $00000000,$00000000,$0000E011,$E011E011
        dc.l    $E011E011,$E0110000,$00000000,$00000000  ; row 01: .....hhhhhh.....
        dc.l    $00000000,$00000000,$E011E011,$E011E011
        dc.l    $E011E011,$E011E011,$00000000,$00000000  ; row 02: ....hhhhhhhh....
        dc.l    $00000000,$00000000,$E011E011,$E011D96C
        dc.l    $D96CD96C,$D96CD96C,$00000000,$00000000  ; row 03: ....hhhsssss....
        dc.l    $00000000,$00000000,$E011E011,$D96CD96C
        dc.l    $D96CD96C,$D96CD96C,$00000000,$00000000  ; row 04: ....hhssssss....
        dc.l    $00000000,$00000000,$E011E011,$D96CD96C
        dc.l    $3601D96C,$3601D96C,$00000000,$00000000  ; row 05: ....hhssksks....
        dc.l    $00000000,$00000000,$E011E011,$D96CD96C
        dc.l    $D96CD96C,$D96CD96C,$00000000,$00000000  ; row 06: ....hhssssss....
        dc.l    $00000000,$00000000,$E011E011,$E011D96C
        dc.l    $D96CD96C,$DA7AD96C,$00000000,$00000000  ; row 07: ....hhhsssSs....
        dc.l    $00000000,$00000000,$0000E011,$E011E011
        dc.l    $E011E011,$E011DA7A,$00000000,$00000000  ; row 08: .....hhhhhhS....
        dc.l    $00000000,$00000000,$00000000,$E011E011
        dc.l    $E011E011,$E0110000,$00000000,$00000000  ; row 09: ......hhhhh.....
        dc.l    $00000000,$00000000,$F0A4F0A4,$3601CFCB
        dc.l    $D645D645,$D6453601,$00000000,$00000000  ; row 10: ....cckgtttk....
        dc.l    $00000000,$0000F0A4,$F0A4F0A4,$3601D645
        dc.l    $D645D645,$D645D645,$D96C0000,$00000000  ; row 11: ...ccckttttts...
        dc.l    $00000000,$0000F0A4,$F0A4F0A4,$3601D645
        dc.l    $D645D645,$D645D645,$D96C0000,$00000000  ; row 12: ...ccckttttts...
        dc.l    $00000000,$0000F0A4,$F0A4F0A4,$3601D645
        dc.l    $D645D645,$D645D645,$D96C0000,$00000000  ; row 13: ...ccckttttts...
        dc.l    $00000000,$0000F0A4,$CFCBF0A4,$3601D645
        dc.l    $D645D645,$D645D645,$D96C0000,$00000000  ; row 14: ...cgckttttts...
        dc.l    $00000000,$0000F0A4,$4E1CF0A4,$3601D822
        dc.l    $D822D822,$D822D822,$D96C0000,$00000000  ; row 15: ...cwckbbbbbs...
        dc.l    $00000000,$F0A44E1C,$F0A4F0A4,$3601D645
        dc.l    $D645D645,$D645D645,$00000000,$00000000  ; row 16: ..cwcckttttt....
        dc.l    $00000000,$4E1C0000,$F0A4F0A4,$3601D645
        dc.l    $D645D645,$D645D645,$00000000,$00000000  ; row 17: ..w.cckttttt....
        dc.l    $00000000,$4E1C0000,$00003601,$3601D645
        dc.l    $D645D645,$D645D645,$36010000,$00000000  ; row 18: ..w..kktttttk...
        dc.l    $00000000,$00000000,$00000000,$D733D733
        dc.l    $0000D733,$D7330000,$00000000,$00000000  ; row 19: ......TT.TT.....
        dc.l    $00000000,$00000000,$00000000,$D733D733
        dc.l    $0000D733,$D7330000,$00000000,$00000000  ; row 20: ......TT.TT.....
        dc.l    $00000000,$00000000,$00000000,$D843D843
        dc.l    $0000D843,$D8430000,$00000000,$00000000  ; row 21: ......ll.ll.....
        dc.l    $00000000,$00000000,$0000D843,$D843D843
        dc.l    $0000D843,$D843D843,$00000000,$00000000  ; row 22: .....lll.lll....
        dc.l    $00000000,$00000000,$00003601,$36013601
        dc.l    $00003601,$36013601,$00000000,$00000000  ; row 23: .....kkk.kkk....

        .end    start
