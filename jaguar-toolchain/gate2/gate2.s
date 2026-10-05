; ============================================================
; gate2.s  —  Castle Remembers hero sprite — Phase B
; Target : Atari Jaguar (68000 + Tom/Jerry)
; Toolchain: RMAC 2.5.2 / RLN 1.7.7
; Load / Entry: $802000
;
; Startup is the proven Gate-1 (hello.s) sequence verbatim.
; OP object list at USERRAM $004000 (phrase-aligned).
; CLUT at $002000 (Jerry GPU CLUT, 32 words).
; Pixel data at $008000 (24 rows * 1 phrase * 8 bytes = 192 bytes).
;
; BITMAP object (Tech Ref Rev.8 verified field map):
;   Phrase 0: PH0_HI=$00800008  PH0_LO=$020606C0
;     TYPE   [2:0]   = 0  (BITMAP)
;     YPOS   [13:3]  = 216 halflines  (screen line 108, NTSC centre)
;     HEIGHT [23:14] = 24 lines
;     LINK   [42:24] = $00802 => $004010  (STOP object)
;     DATA   [63:43] = $01000 => $008000  (pixel data)
;   Phrase 1: PH1_HI=$00000000  PH1_LO=$1004A101
;     XPOS   [11:0]  = 257 pixel-clocks  (screen centre, HDB1=177)
;     DEPTH  [14:12] = 2  (4 bpp, paletted)
;     PITCH  [17:15] = 1  (contiguous)
;     DWIDTH [27:18] = 1  phrase/line   (16px * 4bpp = 8 bytes)
;     IWIDTH [37:28] = 1  phrase
;   STOP phrase at $004010:
;     Phrase 0 BE64 = 0x00000000_00000004  (TYPE=4)
;
; CLUT (Jerry GPU CLUT, 32 * 16-bit words at $F00400):
;   Index 0 = $0000  transparent / background
;   Index 1 = $1083  outline dark  #14101a
;   Index 2 = $EE13  skin          #e8c19b
;   Index 3 = $CCCE  skin shadow   #c99a72
;   Index 4 = $28E2  hair          #2a1c14
;   Index 5 = $A125  cloak red     #a3262a
;   Index 6 = $6AA6  tunic brown   #6d5433
;   Index 7 = $49A4  tunic shadow  #4a3722
;   Index 8 = $3943  belt          #3a2a1a
;   Index 9 = $DD89  gold          #d8b04c
;   Index10 = $CE7B  steel light   #c9ced8
;   Index11 = $4983  leather       #4a3219
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

; ---- VMODE — CRY16+VIDEN+BGEN+PWIDTH4 ($0681) — proven in Gate-1 and Gate-2 v1
VMODE_VAL       equ     $0681

; ---- Object list and pixel data in USERRAM -----------------
OP_LIST         equ     $004000         ; phrase-aligned
PIX_DATA        equ     $008000         ; 24 rows * 4 phrases * 8 bytes = 768 bytes

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
        move.l  #4,$000004          ; TYPE=4 in bits[2:0] of phrase

        ; Point OLP at $000000 initially (safe STOP)
        move.l  #0,OLP

        ; Clear OBF
        move.w  #0,OBF

        ; Clear border
        move.l  #0,BORD1

        ; Stack to top of DRAM
        lea     $1FFFFC,sp

        ; ---- Phase B: copy hero pixel data to DRAM ----------------
        ;   16bpp CRY16, 16px wide = 32 bytes/row = 4 phrases/row.
        ;   24 rows * 32 bytes = 768 bytes = 192 longwords.
        ;   Source: hero_pixels in .text, destination: PIX_DATA ($008000).
        lea     hero_pixels,a1
        lea     PIX_DATA,a0
        move.w  #191,d0         ; 192 longwords - 1
.copy:  move.l  (a1)+,(a0)+
        dbra    d0,.copy

        ; ---- Phase B: write OP object list -----------------
        ;   BITMAP 16px x 24 lines, YPOS=216 hl (line 108), XPOS=257, DEPTH=4(16bpp)
        ;   BITMAP ph0: PH0_HI=$00800008  PH0_LO=$020606C0
        ;     TYPE=0 YPOS=216 HEIGHT=24 LINK=>$004010 DATA=>$008000
        move.l  #$00800008,OP_LIST+0
        move.l  #$020606C0,OP_LIST+4
        ;   BITMAP ph1: PH1_HI=$00000000  PH1_LO=$4010C101
        ;     XPOS=257 DEPTH=4(16bpp) PITCH=1 DWIDTH=4 IWIDTH=4
        move.l  #$00000000,OP_LIST+8
        move.l  #$4010C101,OP_LIST+12
        ;   STOP ph0:   0x00000000_00000004  (TYPE=4)
        move.l  #$00000000,OP_LIST+16
        move.l  #$00000004,OP_LIST+20
        ;   STOP ph1:   all zeros
        move.l  #$00000000,OP_LIST+24
        move.l  #$00000000,OP_LIST+28

        ; ---- Gate-2: point OLP at USERRAM object list -----
        ;   OLP is lo/hi word: $F00020=LOW, $F00022=HIGH.
        ;   OPGetListPointer() = GET16($20) | (GET16($22)<<16)
        ;   A plain MOVE.L #$00004000,$F00020 stores $0000->$F00020, $4000->$F00022
        ;   giving OLP=$40000000 — wrong.  swap d0 before writing fixes it.
        move.l  #OP_LIST,d0             ; d0 = $00004000
        swap    d0                      ; d0 = $40000000
        move.l  d0,OLP                  ; $F00020=$4000(LOW), $F00022=$0000(HIGH) => OLP=$00004000

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

        ; ---- Per-frame object list refresh ----------------
        ;   Tech Ref p.18: after each frame the OP writes HEIGHT=0 and
        ;   advances DATA, making the object inactive next frame.
        ;   Fix: poll VC > VDE (507) to detect end of active picture,
        ;   rewrite phrase 0, then wait for VC to re-enter picture.
        ;   Window = ~543 halflines (~34 ms) — immune to 68k timing jitter.
        ;   VDE (NTSC) = NTSC_VMID+NTSC_HEIGHT = 266+241 = 507 halflines.

PH0_HI          equ     $00800008
PH0_LO          equ     $020606C0       ; YPOS=216 HEIGHT=24 LINK=$004010 DATA=$008000
VC_VDE          equ     507             ; NTSC VDE halflines

forever:
        ; wait until VC passes VDE — active picture just finished
.wait_pic:
        move.w  VC,d0
        cmp.w   #VC_VDE,d0
        blt.s   .wait_pic               ; loop while VC < 507 (still in picture)

        ; now VC >= 507 — in blanking; refresh phrase 0 safely
        move.l  #PH0_HI,OP_LIST+0
        move.l  #PH0_LO,OP_LIST+4

        ; wait for VC to wrap back below VDE (new frame started)
.wait_blank:
        move.w  VC,d0
        cmp.w   #VC_VDE,d0
        bge.s   .wait_blank             ; loop while VC >= 507 (still in blank)

        bra.s   forever

; ============================================================
; Hero idle sprite — 16x24 pixels, 16bpp CRY16, 4 phrases per row
; Each row = 8 longwords (32 bytes).  Stored in .text so the
; COFF loads it; copied to PIX_DATA ($008000) at init.
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
