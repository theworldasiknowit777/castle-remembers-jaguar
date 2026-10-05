; ============================================================
; gate3_floor.s  —  Castle Remembers — Gate 3: First Playable Floor
; Target : Atari Jaguar (68000 + Tom/Jerry)
; Toolchain: RMAC 2.5.2 / RLN 1.7.7
; Load / Entry: $802000
;
; Builds on the proven Phase C (gate3.s) rendering path.
; Adds:
;   - Castle stone floor BITMAP (320×8 px, CRY16, at YPOS row 210)
;   - Hero YPOS driven from DRAM variable (with TRANS flag)
;   - Gravity + floor collision: hero stays on floor plane
;   - Horizontal walk speed unchanged (2 px-clocks/frame, clamped)
;
; Object list at USERRAM $004000 (phrase-aligned):
;   $004000  floor BITMAP phrase 0
;   $004008  floor BITMAP phrase 1
;   $004010  hero  BITMAP phrase 0  (YPOS refreshed per frame)
;   $004018  hero  BITMAP phrase 1  (XPOS refreshed per frame, TRANS=1)
;   $004020  STOP  phrase 0         (TYPE=4)
;   $004028  STOP  phrase 1         (zeros)
;
; DRAM state (phrase-safe region $000100):
;   $000100  hero_xpos  (word, pixel-clocks)   initial=257
;   $000102  hero_ypos  (word, halflines)       initial=372
;   $000104  hero_yvel  (signed word, hl/frame) initial=0
;
; Floor BITMAP (CRY16, 320px × 8 rows):
;   Pixel data at $008000, 5120 bytes (80 phrases/row × 8 rows).
;   YPOS=420 halflines = row 210.  DEPTH=4 (16bpp CRY16).
;   DWIDTH=80 phrases/line, IWIDTH=80.
;
;   Stone colours (proven CRY16 values from gate3 palette):
;     $CE7B = steel-light grey  (#c9ced8)  <- bright stone face
;     $3943 = belt dark          (#3a2a1a)  <- mortar joint
;     $3601 = outline dark       (#14101a)  <- shadow/bottom edge
;
; Hero BITMAP (CRY16, 16px × 24 rows):
;   Pixel data at $009400, 768 bytes (4 phrases/row × 24 rows).
;   TRANS flag set: $0000 pixels let floor/BG show through.
;   YPOS updated each frame from hero_ypos.
;   DWIDTH=4, IWIDTH=4, DEPTH=4, PITCH=1.
;
; Floor collision:
;   FLOOR_YPOS = 372 halflines (= 210*2 - 24*2 = hero stands on floor top)
;   Gravity: YVEL += GRAVITY (+2 halflines/frame) each frame.
;   Each frame: hero_ypos += hero_yvel.
;   If hero_ypos >= FLOOR_YPOS: hero_ypos=FLOOR_YPOS, hero_yvel=0.
;   (Hero starts on floor: ypos=372, yvel=0.)
;
; PH0 field encoding (64-bit phrase, big-endian in DRAM):
;   Phrase bits[63:43] = DATA[20:0]  = pixdata_addr >> 3
;   Phrase bits[42:24] = LINK[18:0]  = next_obj_addr >> 3
;   Phrase bits[23:14] = HEIGHT[9:0]
;   Phrase bits[13:3]  = YPOS[10:0]  (halflines, absolute)
;   Phrase bits[2:0]   = TYPE        (0=BITMAP, 4=STOP)
;   PH0_HI = phrase[63:32], PH0_LO = phrase[31:0]
;
; PH1 field encoding (BITMAP second phrase):
;   Phrase bits[11:0]  = XPOS[11:0]  (pixel-clocks, absolute)
;   Phrase bits[14:12] = DEPTH        (4=16bpp CRY16)
;   Phrase bits[17:15] = PITCH        (1=contiguous)
;   Phrase bits[27:18] = DWIDTH[9:0]  (phrases per line)
;   Phrase bits[37:28] = IWIDTH[9:0]  (phrases per line, same as DWIDTH)
;   Phrase bit  47     = TRANS        (PH1_HI bit 15 = $00008000)
;   PH1_HI = phrase[63:32], PH1_LO = phrase[31:0]
;
; D0 construction for dynamic PH0_LO:
;   Always: moveq #0,d0 ; move.w ypos_hl,d0 ; lsl.l #3,d0 ; or.l mask,d0
;   lsl.l (not lsl.w) ensures no stale bits in the upper half of D0
;   can corrupt the longword write to OP_LIST.
;
; OLP swap trick (proven in gate2/3):
;   MOVE.L #addr,d0; SWAP d0; MOVE.L d0,OLP
;   Stores addr[31:16]->$F00020(low), addr[15:0]->$F00022(high)
;   -> OLP = addr.  Direct MOVE.L would put them backwards.
; ============================================================

; ---- Tom registers -----------------------------------------
TOM             equ     $F00000
OLP             equ     TOM+$20
VC              equ     TOM+$06
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
JOYSTICK        equ     $F14000

; ---- NTSC timing -------------------------------------------
NTSC_WIDTH      equ     1229
NTSC_HMID       equ     787
NTSC_HEIGHT     equ     241
NTSC_VMID       equ     266

; ---- PAL timing --------------------------------------------
PAL_WIDTH       equ     1255
PAL_HMID        equ     821
PAL_HEIGHT      equ     287
PAL_VMID        equ     322

; ---- Video mode ($0681 = CRY16+VIDEN+BGEN+PWIDTH4) --------
VMODE_VAL       equ     $0681

; ---- Background colour -------------------------------------
;   $0000 = black castle darkness; hero and floor stand out.
BG_VAL          equ     $0000

; ---- Object list base --------------------------------------
OP_LIST         equ     $004000

; ---- Pixel data addresses ----------------------------------
PIX_FLOOR       equ     $008000         ; 320x8 CRY16 = 5120 bytes
PIX_HERO        equ     $009400         ; 16x24 CRY16 = 768 bytes

; ---- DRAM state addresses (word each) ----------------------
HERO_XPOS       equ     $000100
HERO_YPOS       equ     $000102
HERO_YVEL       equ     $000104

; ---- Joystick ----------------------------------------------
JOY_ROW0        equ     $817E

; ---- Hero walk limits (pixel-clocks) -----------------------
XPOS_MIN        equ     177
XPOS_MAX        equ     486
XPOS_START      equ     257
XPOS_SPEED      equ     2

; ---- Physics -----------------------------------------------
GRAVITY         equ     2               ; halflines added to yvel each frame
FLOOR_YPOS      equ     372             ; hero_ypos when standing on floor
                                        ; = 210*2 - 24*2 = 420 - 48

; ---- Floor BITMAP PH0 (static) -----------------------------
;   DATA_VAL  = PIX_FLOOR >> 3 = $008000>>3 = $001000
;   LINK_VAL  = $004010 >> 3   = $000802   (-> hero BITMAP)
;   HEIGHT    = 8
;   YPOS      = 420 halflines  (row 210)
;   TYPE      = 0
;
;   PH0_HI: DATA bit12->phrase55->PH0_HI.23 -> $00800000
;           LINK bit11->phrase35->PH0_HI.3  -> $00000008
;           = $00800008
;
;   PH0_LO: LINK[7:0]=$02->bits[31:24]      -> $02000000
;           HEIGHT=8:  8<<14=$020000         -> $00020000
;           YPOS=420:  420<<3=$D20           -> $00000D20
;           = $02020D20
FLOOR_PH0_HI    equ     $00800008
FLOOR_PH0_LO    equ     $02020D20

; ---- Floor BITMAP PH1 (static) -----------------------------
;   XPOS   = 177 = $B1
;   DEPTH  = 4 (16bpp CRY16) -> bit14=1    -> $00004000
;   PITCH  = 1               -> bit15=1    -> $00008000
;   DWIDTH = 80: bit24=1,bit22=1            -> $01400000
;   IWIDTH = 80: IWIDTH[4]->phrase32->PH1_HI.0 -> +$00000001
;                IWIDTH[6]->phrase34->PH1_HI.2 -> +$00000004
;   Floor has no TRANS (solid); PH1_HI = $00000005
;   PH1_LO = $01400000|$00008000|$00004000|$000000B1 = $0140C0B1
FLOOR_PH1_HI    equ     $00000005
FLOOR_PH1_LO    equ     $0140C0B1

; ---- Hero BITMAP PH0 constants (dynamic YPOS) --------------
;   DATA_VAL  = PIX_HERO >> 3 = $009400>>3 = $001280
;   LINK_VAL  = $004020 >> 3  = $000804   (-> STOP)
;   HEIGHT    = 24
;   TYPE      = 0
;
;   PH0_HI: DATA=$1280: bit12->PH0_HI.23 -> $00800000
;                       bit9 ->PH0_HI.20 -> $00100000
;                       bit7 ->PH0_HI.18 -> $00040000
;           LINK=$804:  bit11->PH0_HI.3  -> $00000008
;           = $00940008
;
;   PH0_LO upper (LINK[7:0]+HEIGHT, no YPOS):
;           LINK[7:0]=$04->bits[31:24]     -> $04000000
;           HEIGHT=24: 24<<14=$060000      -> $00060000
;           = $04060000  (OR with ypos_hl<<3 per frame)
;
;   Construction: moveq #0,d0 ; move.w ypos,d0 ; lsl.l #3,d0
;                 or.l #HERO_PH0_LO_MSK,d0
;   lsl.l (not lsl.w) keeps upper 16 bits of D0 clean.
HERO_PH0_HI     equ     $00940008
HERO_PH0_LO_MSK equ     $04060000       ; | (hero_ypos_hl << 3) each frame

; ---- Hero BITMAP PH1 constants (dynamic XPOS) --------------
;   DWIDTH=4, IWIDTH=4, DEPTH=4, PITCH=1, TRANS=1
;
;   TRANS is at phrase bit 47 of the BITMAP's second phrase (PH1).
;   PH1_HI covers phrase bits [63:32] of that phrase.
;   Bit 47 of the phrase = bit (47-32) = bit 15 of PH1_HI.
;   -> PH1_HI = $00008000
;
;   PH1_UPPER = $4010C000 (proven from gate3: DWIDTH=4,IWIDTH=4,
;               DEPTH=4,PITCH=1; XPOS=0 base — OR xpos each frame)
HERO_PH1_HI     equ     $00008000       ; TRANS at phrase bit 47 = PH1_HI bit 15
HERO_PH1_UPPER  equ     $4010C000

; ---- STOP object constants ---------------------------------
STOP_PH0_LO     equ     $00000004       ; TYPE=4

; ---- VC blanking threshold (NTSC) --------------------------
VC_VDE          equ     507

; ============================================================
        .text

; ============================================================
; Entry — Gate-1 startup sequence (verbatim from hello.s / gate3.s)
; ============================================================
start:
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

        ; Safety STOP object at DRAM $000000
        move.l  #0,$000000
        move.l  #4,$000004

        ; Point OLP at $000000 (safe STOP) until we're ready
        move.l  #0,OLP

        ; Clear OBF and border
        move.w  #0,OBF
        move.l  #0,BORD1

        ; Stack to top of DRAM
        lea     $1FFFFC,sp

; ============================================================
; Initialise DRAM state
; ============================================================
        move.w  #XPOS_START,HERO_XPOS   ; hero starts at screen centre
        move.w  #FLOOR_YPOS,HERO_YPOS   ; hero standing on floor
        move.w  #0,HERO_YVEL            ; no vertical velocity

; ============================================================
; Copy floor pixel data to DRAM ($008000)
;   5120 bytes = 1280 longwords
; ============================================================
        lea     floor_pixels,a1
        lea     PIX_FLOOR,a0
        move.w  #1279,d0
.copy_floor:
        move.l  (a1)+,(a0)+
        dbra    d0,.copy_floor

; ============================================================
; Copy hero pixel data to DRAM ($009400)
;   768 bytes = 192 longwords
; ============================================================
        lea     hero_pixels,a1
        lea     PIX_HERO,a0
        move.w  #191,d0
.copy_hero:
        move.l  (a1)+,(a0)+
        dbra    d0,.copy_hero

; ============================================================
; Build object list at $004000
; ============================================================
        ; Floor BITMAP phrase 0 (static)
        move.l  #FLOOR_PH0_HI,OP_LIST+0
        move.l  #FLOOR_PH0_LO,OP_LIST+4

        ; Floor BITMAP phrase 1 (static)
        move.l  #FLOOR_PH1_HI,OP_LIST+8
        move.l  #FLOOR_PH1_LO,OP_LIST+12

        ; Hero BITMAP phrase 0 (initial YPOS = FLOOR_YPOS)
        ;   moveq #0 + lsl.l ensures a clean 32-bit value in D0.
        move.l  #HERO_PH0_HI,OP_LIST+16
        moveq   #0,d0
        move.w  #FLOOR_YPOS,d0          ; d0[15:0] = 372, d0[31:16] = 0
        lsl.l   #3,d0                   ; d0 = 372<<3 = 2976 ($BA0); upper half clean
        or.l    #HERO_PH0_LO_MSK,d0    ; merge LINK/HEIGHT static bits
        move.l  d0,OP_LIST+20

        ; Hero BITMAP phrase 1 (initial XPOS, TRANS flag)
        move.l  #HERO_PH1_HI,OP_LIST+24
        move.l  #(HERO_PH1_UPPER|XPOS_START),OP_LIST+28

        ; STOP phrase 0
        move.l  #0,OP_LIST+32
        move.l  #STOP_PH0_LO,OP_LIST+36

        ; STOP phrase 1
        move.l  #0,OP_LIST+40
        move.l  #0,OP_LIST+44

; ============================================================
; Point OLP at object list (swap trick — proven gate2/3)
; ============================================================
        move.l  #OP_LIST,d0
        swap    d0
        move.l  d0,OLP

; ============================================================
; NTSC/PAL video timing (verbatim from gate3.s)
; ============================================================
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
        move.w  #$7FFF,VI
        move.w  #BG_VAL,BG              ; black castle background
        move.w  #VMODE_VAL,VMODE        ; enable video

; ============================================================
; Main loop — one iteration per frame, runs in blanking window.
;
; Steps each frame:
;   1. Wait VC > VC_VDE (active picture ended, now in blanking)
;   2. Read joystick Row 0; update hero_xpos (LEFT/RIGHT + clamp)
;   3. Physics: yvel += GRAVITY; ypos += yvel; floor clamp
;   4. Rebuild and write hero BITMAP phrase 0 (new YPOS)
;   5. Rebuild and write hero BITMAP phrase 1 (new XPOS)
;   6. Refresh floor BITMAP phrase 0 (OP zeroes HEIGHT each frame)
;   7. Wait VC < VC_VDE (new frame started)
;   8. Loop
;
; Register use:
;   d0 = scratch (VC polls, joystick word, assembled PH values)
;   d1 = hero_xpos (word)
;   d2 = hero_ypos (word, halflines)
;   d3 = hero_yvel (signed word)
; ============================================================

forever:
        ; --------------------------------------------------
        ; Step 1: wait for end of active picture (blanking)
        ; --------------------------------------------------
.wait_pic:
        move.w  VC,d0
        cmp.w   #VC_VDE,d0
        blt.s   .wait_pic

        ; --------------------------------------------------
        ; Step 2: joystick — LEFT/RIGHT horizontal movement
        ;   Proven gate3.s path: unchanged.
        ; --------------------------------------------------
        move.w  #JOY_ROW0,JOYSTICK     ; select Row 0 (D-pad)
        move.w  JOYSTICK,d0            ; read active-LOW bits

        move.w  HERO_XPOS,d1

        ; LEFT (bit 10 active-LOW)
        btst    #10,d0
        bne.s   .chk_right
        sub.w   #XPOS_SPEED,d1
        cmp.w   #XPOS_MIN,d1
        bge.s   .chk_right
        move.w  #XPOS_MIN,d1

.chk_right:
        ; RIGHT (bit 11 active-LOW)
        btst    #11,d0
        bne.s   .store_x
        add.w   #XPOS_SPEED,d1
        cmp.w   #XPOS_MAX,d1
        ble.s   .store_x
        move.w  #XPOS_MAX,d1

.store_x:
        move.w  d1,HERO_XPOS

        ; --------------------------------------------------
        ; Step 3: physics — gravity + floor collision
        ;
        ;   yvel += GRAVITY  (positive = downward, halflines/frame)
        ;   ypos += yvel
        ;   if ypos >= FLOOR_YPOS: ypos = FLOOR_YPOS, yvel = 0
        ;   hero_ypos and hero_yvel are signed words.
        ; --------------------------------------------------
        move.w  HERO_YPOS,d2
        move.w  HERO_YVEL,d3

        add.w   #GRAVITY,d3            ; apply gravity
        add.w   d3,d2                  ; move hero downward

        cmp.w   #FLOOR_YPOS,d2
        ble.s   .no_floor_hit
        move.w  #FLOOR_YPOS,d2        ; clamp to floor surface
        moveq   #0,d3                  ; zero velocity on landing

.no_floor_hit:
        move.w  d2,HERO_YPOS
        move.w  d3,HERO_YVEL

        ; --------------------------------------------------
        ; Step 4: write hero BITMAP phrase 0 (dynamic YPOS)
        ;   PH0_LO = HERO_PH0_LO_MSK | (hero_ypos_hl << 3)
        ;   YPOS field = bits[13:3] of PH0_LO.
        ;   moveq #0 + lsl.l keeps D0[31:16] clean before
        ;   the OR with the 32-bit mask constant.
        ; --------------------------------------------------
        move.l  #HERO_PH0_HI,OP_LIST+16
        moveq   #0,d0
        move.w  d2,d0                  ; d0[15:0] = ypos_hl, d0[31:16] = 0
        lsl.l   #3,d0                  ; d0 = ypos_hl<<3; upper half clean
        or.l    #HERO_PH0_LO_MSK,d0   ; inject LINK/HEIGHT static bits
        move.l  d0,OP_LIST+20

        ; --------------------------------------------------
        ; Step 5: write hero BITMAP phrase 1 (dynamic XPOS)
        ;   PH1_LO = HERO_PH1_UPPER | (hero_xpos & $0FFF)
        ;   PH1_HI = HERO_PH1_HI = $00008000 (TRANS at phrase bit 47)
        ; --------------------------------------------------
        move.l  #HERO_PH1_HI,OP_LIST+24
        move.l  #HERO_PH1_UPPER,d0
        and.w   #$0FFF,d1
        or.w    d1,d0
        move.l  d0,OP_LIST+28

        ; --------------------------------------------------
        ; Step 6: refresh floor BITMAP phrase 0
        ;   OP zeroes HEIGHT after each frame; restore in blanking.
        ;   Phrase 1 is static (no HEIGHT field) — no refresh needed.
        ; --------------------------------------------------
        move.l  #FLOOR_PH0_HI,OP_LIST+0
        move.l  #FLOOR_PH0_LO,OP_LIST+4

        ; --------------------------------------------------
        ; Step 7: wait for new frame (VC drops below VC_VDE)
        ; --------------------------------------------------
.wait_blank:
        move.w  VC,d0
        cmp.w   #VC_VDE,d0
        bge.s   .wait_blank

        bra     forever

; ============================================================
; Castle stone floor — 320×8 pixels, CRY16, stored in .text.
; Copied to PIX_FLOOR ($008000) at init.  5120 bytes total.
;
; Colour key (proven CRY16 values from gate3 palette):
;   $CE7B = steel-light grey -- bright stone face
;   $3943 = belt dark         -- mortar joint (dark brown-black)
;   $3601 = outline dark      -- shadow bottom edge
;
; Layout (8 rows, each 320 pixels = 160 longwords):
;   Row 0: bright stone top  ($CE7B)
;   Row 1: stone fill        ($CE7B)
;   Row 2: stone fill        ($CE7B)
;   Row 3: mortar joint      ($3943)
;   Row 4: stone fill        ($CE7B)
;   Row 5: stone fill        ($CE7B)
;   Row 6: mortar joint      ($3943)
;   Row 7: shadow bottom     ($3601)
; ============================================================
floor_pixels:
        ; Row 0 — bright stone top (160 longwords = 320 pixels)
        .rept   160
        dc.l    $CE7BCE7B
        .endr
        ; Row 1 — stone fill
        .rept   160
        dc.l    $CE7BCE7B
        .endr
        ; Row 2 — stone fill
        .rept   160
        dc.l    $CE7BCE7B
        .endr
        ; Row 3 — mortar joint
        .rept   160
        dc.l    $39433943
        .endr
        ; Row 4 — stone fill
        .rept   160
        dc.l    $CE7BCE7B
        .endr
        ; Row 5 — stone fill
        .rept   160
        dc.l    $CE7BCE7B
        .endr
        ; Row 6 — mortar joint
        .rept   160
        dc.l    $39433943
        .endr
        ; Row 7 — shadow bottom
        .rept   160
        dc.l    $36013601
        .endr

; ============================================================
; Hero idle sprite — 16×24 pixels, CRY16, stored in .text.
; Copied to PIX_HERO ($009400) at init.  768 bytes total.
; VERBATIM from gate3.s.  $0000 = transparent (TRANS flag set
; on the BITMAP object lets floor/BG show through).
;
; Palette (16bpp CRY16 values):
;   $0000=transparent  $E011=hair      $D96C=skin
;   $DA7A=skin shadow  $3601=dark      $F0A4=cloak red
;   $D645=tunic brown  $D733=tunic shd $D822=belt
;   $CFCB=gold         $4E1C=steel     $D843=leather
; ============================================================
hero_pixels:
        dc.l    $00000000,$00000000,$00000000,$E011E011
        dc.l    $E011E011,$00000000,$00000000,$00000000  ; row 00
        dc.l    $00000000,$00000000,$0000E011,$E011E011
        dc.l    $E011E011,$E0110000,$00000000,$00000000  ; row 01
        dc.l    $00000000,$00000000,$E011E011,$E011E011
        dc.l    $E011E011,$E011E011,$00000000,$00000000  ; row 02
        dc.l    $00000000,$00000000,$E011E011,$E011D96C
        dc.l    $D96CD96C,$D96CD96C,$00000000,$00000000  ; row 03
        dc.l    $00000000,$00000000,$E011E011,$D96CD96C
        dc.l    $D96CD96C,$D96CD96C,$00000000,$00000000  ; row 04
        dc.l    $00000000,$00000000,$E011E011,$D96CD96C
        dc.l    $3601D96C,$3601D96C,$00000000,$00000000  ; row 05
        dc.l    $00000000,$00000000,$E011E011,$D96CD96C
        dc.l    $D96CD96C,$D96CD96C,$00000000,$00000000  ; row 06
        dc.l    $00000000,$00000000,$E011E011,$E011D96C
        dc.l    $D96CD96C,$DA7AD96C,$00000000,$00000000  ; row 07
        dc.l    $00000000,$00000000,$0000E011,$E011E011
        dc.l    $E011E011,$E011DA7A,$00000000,$00000000  ; row 08
        dc.l    $00000000,$00000000,$00000000,$E011E011
        dc.l    $E011E011,$E0110000,$00000000,$00000000  ; row 09
        dc.l    $00000000,$00000000,$F0A4F0A4,$3601CFCB
        dc.l    $D645D645,$D6453601,$00000000,$00000000  ; row 10
        dc.l    $00000000,$0000F0A4,$F0A4F0A4,$3601D645
        dc.l    $D645D645,$D645D645,$D96C0000,$00000000  ; row 11
        dc.l    $00000000,$0000F0A4,$F0A4F0A4,$3601D645
        dc.l    $D645D645,$D645D645,$D96C0000,$00000000  ; row 12
        dc.l    $00000000,$0000F0A4,$F0A4F0A4,$3601D645
        dc.l    $D645D645,$D645D645,$D96C0000,$00000000  ; row 13
        dc.l    $00000000,$0000F0A4,$CFCBF0A4,$3601D645
        dc.l    $D645D645,$D645D645,$D96C0000,$00000000  ; row 14
        dc.l    $00000000,$0000F0A4,$4E1CF0A4,$3601D822
        dc.l    $D822D822,$D822D822,$D96C0000,$00000000  ; row 15
        dc.l    $00000000,$F0A44E1C,$F0A4F0A4,$3601D645
        dc.l    $D645D645,$D645D645,$00000000,$00000000  ; row 16
        dc.l    $00000000,$4E1C0000,$F0A4F0A4,$3601D645
        dc.l    $D645D645,$D645D645,$00000000,$00000000  ; row 17
        dc.l    $00000000,$4E1C0000,$00003601,$3601D645
        dc.l    $D645D645,$D645D645,$36010000,$00000000  ; row 18
        dc.l    $00000000,$00000000,$00000000,$D733D733
        dc.l    $0000D733,$D7330000,$00000000,$00000000  ; row 19
        dc.l    $00000000,$00000000,$00000000,$D733D733
        dc.l    $0000D733,$D7330000,$00000000,$00000000  ; row 20
        dc.l    $00000000,$00000000,$00000000,$D843D843
        dc.l    $0000D843,$D8430000,$00000000,$00000000  ; row 21
        dc.l    $00000000,$00000000,$0000D843,$D843D843
        dc.l    $0000D843,$D843D843,$00000000,$00000000  ; row 22
        dc.l    $00000000,$00000000,$00003601,$36013601
        dc.l    $00003601,$36013601,$00000000,$00000000  ; row 23

        .end    start
