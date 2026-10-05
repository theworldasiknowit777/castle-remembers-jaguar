; ============================================================
; gate4_slice.s  —  Castle Remembers — Gate 4: Vertical Slice
; Target : Atari Jaguar (68000 + Tom/Jerry)
; Toolchain: RMAC 2.5.2 / RLN 1.7.7
; Load / Entry: $802000
;
; Builds directly on Gate 3 (gate3_floor.s) — all proven code
; preserved verbatim.  Adds:
;   1. JUMP  — A/Up button (Row 0 bit 8, active-LOW); yvel=-14
;              when hero is on the floor.
;   2. ENEMY — 16x16 CRY16 BITMAP; bounces left/right across the
;              floor autonomously.  Third object in OP list.
;   3. COLLISION + RESET — axis-aligned bbox test each frame;
;              overlap -> hero resets to start position.
;
; Complete gameplay loop: walk, jump, dodge enemy, get hit, respawn.
;
; Object list at $004000 (phrase-aligned):
;   $004000  floor  BITMAP PH0/PH1   (static, PH0 refreshed)
;   $004010  enemy  BITMAP PH0/PH1   (XPOS dynamic)
;   $004020  hero   BITMAP PH0/PH1   (XPOS+YPOS dynamic, TRANS)
;   $004030  STOP   PH0/PH1
;
; DRAM state ($000100 region):
;   $000100  hero_xpos   word  pixel-clocks  initial=XPOS_START
;   $000102  hero_ypos   word  halflines     initial=FLOOR_YPOS
;   $000104  hero_yvel   signed word hl/fr   initial=0
;   $000106  enemy_xpos  word  pixel-clocks  initial=350
;   $000108  enemy_dir   word  +2 or -2      initial=+2
;
; Pixel data:
;   $008000  PIX_FLOOR  5120 bytes  (320x8 CRY16 stone)
;   $009000  PIX_ENEMY   512 bytes  (16x16 CRY16 skull/bat)
;   $009400  PIX_HERO    768 bytes  (16x24 CRY16 hero, verbatim)
;
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

; ---- Video mode --------------------------------------------
VMODE_VAL       equ     $0681           ; CRY16+VIDEN+BGEN+PWIDTH4
BG_VAL          equ     $0000           ; black castle background

; ---- Object list base --------------------------------------
OP_LIST         equ     $004000

; ---- Object list offsets -----------------------------------
; floor  PH0=$004000  PH1=$004008
; enemy  PH0=$004010  PH1=$004018
; hero   PH0=$004020  PH1=$004028
; STOP   PH0=$004030  PH1=$004038

; ---- Pixel data addresses ----------------------------------
PIX_FLOOR       equ     $008000         ; 320x8  CRY16 = 5120 bytes
PIX_ENEMY       equ     $009000         ; 16x16  CRY16 =  512 bytes
PIX_HERO        equ     $009400         ; 16x24  CRY16 =  768 bytes

; ---- DRAM state --------------------------------------------
HERO_XPOS       equ     $000100
HERO_YPOS       equ     $000102
HERO_YVEL       equ     $000104
ENEMY_XPOS      equ     $000106
ENEMY_DIR       equ     $000108

; ---- Joystick ----------------------------------------------
JOY_ROW0        equ     $817E
; Bit 8  = Up   (active-LOW) — used for jump
; Bit 10 = Left (active-LOW)
; Bit 11 = Right(active-LOW)

; ---- Hero walk/jump limits ---------------------------------
XPOS_MIN        equ     177
XPOS_MAX        equ     486
XPOS_START      equ     257
XPOS_SPEED      equ     2
JUMP_VEL        equ     -14             ; halflines/frame upward

; ---- Physics -----------------------------------------------
GRAVITY         equ     2
FLOOR_YPOS      equ     372             ; hero ypos when standing (halflines)
                                        ; = row210*2 - 24rows*2 = 420-48

; ---- Enemy -------------------------------------------------
ENEMY_XMIN      equ     177
ENEMY_XMAX      equ     478             ; 486-8 (enemy is 16px wide)
ENEMY_SPEED     equ     2               ; pixel-clocks/frame
ENEMY_START_X   equ     350
ENEMY_YPOS_HL   equ     380             ; halflines; row 210 - 16rows*2 = 420-40
                                        ; enemy stands on same floor plane

; ---- Collision bbox half-widths ----------------------------
; hero  = 16px wide, 24px tall -> half = 8, 12 (in pixels / halflines)
; enemy = 16px wide, 16px tall -> half = 8, 8
; Combined threshold (sum of halves, pixel-clocks / halflines):
COLL_X_THRESH   equ     16              ; |hero_x - enemy_x| < 16
COLL_Y_THRESH   equ     20              ; |hero_y - enemy_y| < 20

; ---- VC blanking threshold ---------------------------------
VC_VDE          equ     507

; ---- Floor BITMAP PH0 (static) -----------------------------
;   DATA = PIX_FLOOR>>3 = $001000   LINK = $004010>>3 = $000802 (->enemy)
;   HEIGHT=8  YPOS=420  TYPE=0
;   PH0_HI: DATA bit12->PH0_HI.23=$00800000; LINK bit11->PH0_HI.3=$00000008
;   PH0_LO: LINK[7:0]=$02->bits31:24=$02000000; HEIGHT=8<<14=$020000; YPOS=420<<3=$D20
FLOOR_PH0_HI    equ     $00800008
FLOOR_PH0_LO    equ     $02020D20

; ---- Floor BITMAP PH1 (static) -----------------------------
;   XPOS=177=$B1  DEPTH=4  PITCH=1  DWIDTH=80  IWIDTH=80  TRANS=0
FLOOR_PH1_HI    equ     $00000005
FLOOR_PH1_LO    equ     $0140C0B1

; ---- Enemy BITMAP PH0 (static Y, dynamic X in PH1) --------
;   DATA = PIX_ENEMY>>3 = $009000>>3 = $001200
;   LINK = $004020>>3 = $000804 (->hero)
;   HEIGHT=16  YPOS=ENEMY_YPOS_HL=380  TYPE=0
;
;   DATA=$1200: bit12->PH0_HI.23=$00800000; bit9->PH0_HI.20=$00100000
;   LINK=$804:  bit11->PH0_HI.3=$00000008; bit2->PH0_HI bit(2+0)... 
;   Let's compute carefully:
;   DATA_ADDR = PIX_ENEMY>>3 = $009000>>3 = $1200
;     $1200 = b0001_0010_0000_0000
;     bit12=1 -> phrase55 -> PH0_HI bit23 = $00800000
;     bit9 =1 -> phrase52 -> PH0_HI bit20 = $00100000
;     -> DATA contrib = $00900000
;   LINK_ADDR = $004020>>3 = $000804
;     $804 = b0000_1000_0000_0100
;     bit11=1 -> phrase35 -> PH0_HI bit3 = $00000008
;     -> PH0_HI = $00900008
;   LINK[7:0] = $04 -> PH0_LO bits[31:24] = $04000000
;   HEIGHT=16: 16<<14 = $040000 -> PH0_LO $00040000
;   YPOS=380:  380<<3 = $BB8   -> PH0_LO $00000BB8
;   PH0_LO = $04040BB8
ENEMY_PH0_HI    equ     $00900008
ENEMY_PH0_LO    equ     $04040BB8

; ---- Enemy BITMAP PH1 (dynamic XPOS) -----------------------
;   DWIDTH=4  IWIDTH=4  DEPTH=4  PITCH=1  TRANS=1
;   Same PH1 layout as hero: PH1_HI=$00008000, UPPER=$4010C000
ENEMY_PH1_HI    equ     $00008000
ENEMY_PH1_UPPER equ     $4010C000

; ---- Hero BITMAP PH0 (dynamic YPOS) -----------------------
;   DATA = PIX_HERO>>3 = $009400>>3 = $001280
;   LINK = $004030>>3 = $000806 (->STOP)
;   HEIGHT=24  TYPE=0
;   DATA=$1280: bit12->PH0_HI.23=$00800000; bit9->PH0_HI.20=$00100000
;               bit7 ->PH0_HI.18=$00040000
;   LINK=$806:  bit11->PH0_HI.3=$00000008; bit1->PH0_HI.1=$00000002
;   PH0_HI = $00940008 | $00000002 = $0094000A
;
;   Wait — recompute LINK for new address $004030:
;   $004030>>3 = $000806
;   $806 = b0000_1000_0000_0110
;   bit11=1 -> phrase35 -> PH0_HI bit3 = $00000008
;   bit2 =1 -> phrase26 -> PH0_HI... phrase bits 43:24 = LINK[19:0]
;   LINK in PH0: phrase bits[42:24] = LINK[18:0]
;   LINK[18:0] = $806 -> 
;     bit11 of LINK -> phrase bit (24+11)=35 -> PH0_HI bit (35-32)=3  = $00000008
;     bit2  of LINK -> phrase bit (24+2) =26 -> PH0_LO bit (26-0) ... 
;     phrase bit 26 is in PH0_LO (covers bits 31:0).
;     PH0_LO bit 26 = $04000000... no wait.
;   Let me be precise about LINK placement in PH0:
;   PH0 phrase bits [42:24] = LINK[18:0] (object addr >> 3)
;   PH0_HI = phrase bits [63:32]
;   PH0_LO = phrase bits [31:0]
;   LINK bit 11 -> phrase bit 24+11=35 -> PH0_HI bit 3  = $00000008
;   LINK bit 2  -> phrase bit 24+2 =26 -> PH0_LO bit 26 = $04000000
;   LINK bit 1  -> phrase bit 24+1 =25 -> PH0_LO bit 25 = $02000000
;   So LINK=$806 contributes:
;     PH0_HI: $00000008
;     PH0_LO bits[31:24]: $04|$02 = $06 -> upper byte = $06000000
;   LINK[7:0] in PH0_LO[31:24] = $06 -> $06000000
;
;   PH0_HI = DATA_contrib | LINK_contrib_hi = $00940000 | $00000008 = $00940008
;   PH0_LO = LINK_lo | HEIGHT | YPOS_field
;     LINK_lo = $06000000
;     HEIGHT=24: 24<<14 = $060000 -> $00060000
;     YPOS = dynamic
;   HERO_PH0_LO_MSK = $06060000
HERO_PH0_HI     equ     $00940008
HERO_PH0_LO_MSK equ     $06060000       ; | (hero_ypos_hl << 3) each frame

; ---- Hero BITMAP PH1 (dynamic XPOS) -----------------------
;   DWIDTH=4  IWIDTH=4  DEPTH=4  PITCH=1  TRANS=1
HERO_PH1_HI     equ     $00008000
HERO_PH1_UPPER  equ     $4010C000

; ---- STOP object -------------------------------------------
STOP_PH0_LO     equ     $00000004       ; TYPE=4

; ============================================================
        .text

; ============================================================
; Entry — proven startup (verbatim gate3_floor.s)
; ============================================================
start:
        move.w  #$2700,sr
        move.l  #0,G_FLAGS
        move.l  #0,G_CTRL
        move.l  #$0001F800,D_FLAGS
        move.l  #0,D_CTRL
        move.l  #$1F000000,INT1
        move.w  #$3F00,J_INT
        move.l  #0,$000000
        move.l  #4,$000004
        move.l  #0,OLP
        move.w  #0,OBF
        move.l  #0,BORD1
        lea     $1FFFFC,sp

; ---- Initialise DRAM state ---------------------------------
        move.w  #XPOS_START,HERO_XPOS
        move.w  #FLOOR_YPOS,HERO_YPOS
        move.w  #0,HERO_YVEL
        move.w  #ENEMY_START_X,ENEMY_XPOS
        move.w  #ENEMY_SPEED,ENEMY_DIR

; ---- Copy floor pixel data to $008000 (5120 bytes = 1280 longs) ----
        lea     floor_pixels,a1
        lea     PIX_FLOOR,a0
        move.w  #1279,d0
.copy_floor:
        move.l  (a1)+,(a0)+
        dbra    d0,.copy_floor

; ---- Copy enemy pixel data to $009000 (512 bytes = 128 longs) ------
        lea     enemy_pixels,a1
        lea     PIX_ENEMY,a0
        move.w  #127,d0
.copy_enemy:
        move.l  (a1)+,(a0)+
        dbra    d0,.copy_enemy

; ---- Copy hero pixel data to $009400 (768 bytes = 192 longs) -------
        lea     hero_pixels,a1
        lea     PIX_HERO,a0
        move.w  #191,d0
.copy_hero:
        move.l  (a1)+,(a0)+
        dbra    d0,.copy_hero

; ---- Build object list at $004000 --------------------------
        ; Floor BITMAP (static PH1; PH0 refreshed each blank)
        move.l  #FLOOR_PH0_HI,OP_LIST+0
        move.l  #FLOOR_PH0_LO,OP_LIST+4
        move.l  #FLOOR_PH1_HI,OP_LIST+8
        move.l  #FLOOR_PH1_LO,OP_LIST+12

        ; Enemy BITMAP (initial XPOS)
        move.l  #ENEMY_PH0_HI,OP_LIST+16
        move.l  #ENEMY_PH0_LO,OP_LIST+20
        move.l  #ENEMY_PH1_HI,OP_LIST+24
        move.l  #(ENEMY_PH1_UPPER|ENEMY_START_X),OP_LIST+28

        ; Hero BITMAP (initial YPOS = FLOOR_YPOS, XPOS = XPOS_START)
        move.l  #HERO_PH0_HI,OP_LIST+32
        moveq   #0,d0
        move.w  #FLOOR_YPOS,d0
        lsl.l   #3,d0
        or.l    #HERO_PH0_LO_MSK,d0
        move.l  d0,OP_LIST+36
        move.l  #HERO_PH1_HI,OP_LIST+40
        move.l  #(HERO_PH1_UPPER|XPOS_START),OP_LIST+44

        ; STOP
        move.l  #0,OP_LIST+48
        move.l  #STOP_PH0_LO,OP_LIST+52
        move.l  #0,OP_LIST+56
        move.l  #0,OP_LIST+60

; ---- Point OLP at object list (swap trick) -----------------
        move.l  #OP_LIST,d0
        swap    d0
        move.l  d0,OLP

; ---- NTSC/PAL video timing (verbatim gate3_floor.s) --------
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
        move.w  #BG_VAL,BG
        move.w  #VMODE_VAL,VMODE

; ============================================================
; Main loop — runs once per frame in blanking window
;
; Register allocation:
;   d0 = scratch
;   d1 = hero_xpos (word)
;   d2 = hero_ypos (word, halflines)
;   d3 = hero_yvel (signed word)
;   d4 = enemy_xpos (word)
;   d5 = enemy_dir  (word, +2 or -2)
; ============================================================

forever:
        ; --------------------------------------------------
        ; Wait for end of active picture (blanking start)
        ; --------------------------------------------------
.wait_pic:
        move.w  VC,d0
        cmp.w   #VC_VDE,d0
        blt.s   .wait_pic

        ; --------------------------------------------------
        ; Read joystick Row 0 (D-pad + fire, active-LOW)
        ; --------------------------------------------------
        move.w  #JOY_ROW0,JOYSTICK
        move.w  JOYSTICK,d0

        move.w  HERO_XPOS,d1
        move.w  HERO_YPOS,d2
        move.w  HERO_YVEL,d3

        ; LEFT (bit 10)
        btst    #10,d0
        bne.s   .chk_right
        sub.w   #XPOS_SPEED,d1
        cmp.w   #XPOS_MIN,d1
        bge.s   .chk_right
        move.w  #XPOS_MIN,d1

.chk_right:
        ; RIGHT (bit 11)
        btst    #11,d0
        bne.s   .chk_jump
        add.w   #XPOS_SPEED,d1
        cmp.w   #XPOS_MAX,d1
        ble.s   .chk_jump
        move.w  #XPOS_MAX,d1

.chk_jump:
        ; JUMP (bit 8 = Up, active-LOW)
        ; Only jump when on the floor (yvel=0 and ypos=FLOOR_YPOS)
        btst    #8,d0
        bne.s   .physics            ; bit set = not pressed

        ; Check hero is grounded: ypos == FLOOR_YPOS and yvel == 0
        cmp.w   #FLOOR_YPOS,d2
        bne.s   .physics
        tst.w   d3
        bne.s   .physics
        move.w  #JUMP_VEL,d3       ; launch upward

.physics:
        ; Gravity + floor collision
        add.w   #GRAVITY,d3
        add.w   d3,d2
        cmp.w   #FLOOR_YPOS,d2
        ble.s   .no_floor
        move.w  #FLOOR_YPOS,d2
        moveq   #0,d3
.no_floor:

        move.w  d1,HERO_XPOS
        move.w  d2,HERO_YPOS
        move.w  d3,HERO_YVEL

        ; --------------------------------------------------
        ; Enemy AI — bounce left/right on floor
        ; --------------------------------------------------
        move.w  ENEMY_XPOS,d4
        move.w  ENEMY_DIR,d5

        add.w   d5,d4               ; move by direction

        cmp.w   #ENEMY_XMIN,d4
        bge.s   .chk_emax
        move.w  #ENEMY_XMIN,d4
        neg.w   d5                  ; reverse direction
        bra.s   .store_enemy

.chk_emax:
        cmp.w   #ENEMY_XMAX,d4
        ble.s   .store_enemy
        move.w  #ENEMY_XMAX,d4
        neg.w   d5

.store_enemy:
        move.w  d4,ENEMY_XPOS
        move.w  d5,ENEMY_DIR

        ; --------------------------------------------------
        ; Collision detection — axis-aligned bbox
        ;   hero  centre X = hero_xpos + 8
        ;   enemy centre X = enemy_xpos + 8
        ;   delta_x = |hero_xpos - enemy_xpos|
        ;   delta_y = |hero_ypos - enemy_ypos_hl|
        ;   hit if delta_x < COLL_X_THRESH AND delta_y < COLL_Y_THRESH
        ;
        ; hero_ypos is in halflines; enemy is fixed at ENEMY_YPOS_HL.
        ; --------------------------------------------------
        move.w  d1,d0               ; d0 = hero_xpos
        sub.w   d4,d0               ; d0 = hero_x - enemy_x
        bpl.s   .abs_x
        neg.w   d0                  ; abs
.abs_x:
        cmp.w   #COLL_X_THRESH,d0
        bge.s   .no_hit             ; too far apart horizontally

        move.w  d2,d0               ; d0 = hero_ypos (halflines)
        sub.w   #ENEMY_YPOS_HL,d0  ; d0 = hero_y - enemy_y
        bpl.s   .abs_y
        neg.w   d0
.abs_y:
        cmp.w   #COLL_Y_THRESH,d0
        bge.s   .no_hit             ; too far apart vertically

        ; HIT — reset hero to start
        move.w  #XPOS_START,d1
        move.w  #FLOOR_YPOS,d2
        moveq   #0,d3
        move.w  d1,HERO_XPOS
        move.w  d2,HERO_YPOS
        move.w  d3,HERO_YVEL

.no_hit:
        ; --------------------------------------------------
        ; Write hero BITMAP phrase 0 (dynamic YPOS)
        ; --------------------------------------------------
        move.l  #HERO_PH0_HI,OP_LIST+32
        moveq   #0,d0
        move.w  d2,d0
        lsl.l   #3,d0
        or.l    #HERO_PH0_LO_MSK,d0
        move.l  d0,OP_LIST+36

        ; --------------------------------------------------
        ; Write hero BITMAP phrase 1 (dynamic XPOS)
        ; --------------------------------------------------
        move.l  #HERO_PH1_HI,OP_LIST+40
        move.l  #HERO_PH1_UPPER,d0
        and.w   #$0FFF,d1
        or.w    d1,d0
        move.l  d0,OP_LIST+44

        ; --------------------------------------------------
        ; Write enemy BITMAP phrase 1 (dynamic XPOS)
        ; --------------------------------------------------
        move.l  #ENEMY_PH1_HI,OP_LIST+24
        move.w  d4,d0               ; d0[15:0] = enemy_xpos
        and.w   #$0FFF,d0           ; mask to 12-bit XPOS field
        or.l    #ENEMY_PH1_UPPER,d0 ; merge DWIDTH/IWIDTH/DEPTH/PITCH upper bits
        move.l  d0,OP_LIST+28

        ; --------------------------------------------------
        ; Refresh floor BITMAP phrase 0 (OP zeroes HEIGHT each frame)
        ; --------------------------------------------------
        move.l  #FLOOR_PH0_HI,OP_LIST+0
        move.l  #FLOOR_PH0_LO,OP_LIST+4

        ; --------------------------------------------------
        ; Refresh enemy BITMAP phrase 0 (OP zeroes HEIGHT each frame)
        ; --------------------------------------------------
        move.l  #ENEMY_PH0_HI,OP_LIST+16
        move.l  #ENEMY_PH0_LO,OP_LIST+20

        ; --------------------------------------------------
        ; Wait for new frame (VC drops below VC_VDE)
        ; --------------------------------------------------
.wait_blank:
        move.w  VC,d0
        cmp.w   #VC_VDE,d0
        bge.s   .wait_blank

        bra     forever

; ============================================================
; Castle stone floor — 320x8 px CRY16 (verbatim gate3_floor.s)
; Copied to PIX_FLOOR ($008000).  5120 bytes = 1280 longwords.
; ============================================================
floor_pixels:
        ; Row 0 — bright stone top
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
; Enemy sprite — 16x16 px CRY16, skull/threat silhouette.
; Copied to PIX_ENEMY ($009000).  512 bytes = 128 longwords.
; TRANS flag set: $0000 pixels transparent.
;
; Palette:
;   $0000 = transparent
;   $F001 = bright red (danger / eye glow)
;   $3601 = near-black outline
;   $CFCB = pale bone/gold
; ============================================================
enemy_pixels:
        ; row 0
        dc.l    $00000000,$00000000,$00000000,$00000000
        ; row 1
        dc.l    $00003601,$36013601,$36013601,$36010000
        ; row 2
        dc.l    $00003601,$F001CFCB,$CFCBF001,$36010000
        ; row 3
        dc.l    $36013601,$F001CFCB,$CFCBF001,$36013601
        ; row 4
        dc.l    $36013601,$36013601,$36013601,$36013601
        ; row 5
        dc.l    $36013601,$CFCB3601,$3601CFCB,$36013601
        ; row 6
        dc.l    $36013601,$3601CFCB,$CFCB3601,$36013601
        ; row 7
        dc.l    $00003601,$36013601,$36013601,$36010000
        ; row 8
        dc.l    $00003601,$36013601,$36013601,$36010000
        ; row 9
        dc.l    $36013601,$3601CFCB,$CFCB3601,$36013601
        ; row 10
        dc.l    $36013601,$CFCB3601,$3601CFCB,$36013601
        ; row 11
        dc.l    $36013601,$36013601,$36013601,$36013601
        ; row 12
        dc.l    $00003601,$36013601,$36013601,$36010000
        ; row 13
        dc.l    $00003601,$3601CFCB,$CFCB3601,$36010000
        ; row 14
        dc.l    $00000000,$3601CFCB,$CFCB3601,$00000000
        ; row 15
        dc.l    $00000000,$00003601,$36010000,$00000000

; ============================================================
; Hero idle sprite — 16x24 px CRY16 (verbatim gate3_floor.s)
; Copied to PIX_HERO ($009400).  768 bytes = 192 longwords.
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
