; ============================================================
; gate5_memory.s  —  Castle Remembers — Gate 5: Adaptive Memory
; Target : Atari Jaguar (68000 + Tom/Jerry)
; Toolchain: RMAC 2.5.2 / RLN 1.7.7
; Load / Entry: $802000
;
; Builds directly on Gate 4 (gate4_slice.s) — all proven code
; preserved verbatim.  One new system added:
;
;   THE CASTLE REMEMBERS — Side-Bias Adaptation
;   =============================================
;   Each frame the hero is alive, SIDE_BIAS is updated:
;     hero_xpos < SCREEN_MID (332) -> SIDE_BIAS--   (left-biased)
;     hero_xpos >= SCREEN_MID      -> SIDE_BIAS++   (right-biased)
;
;   On death (collision):
;     1. Read sign of SIDE_BIAS.
;        SIDE_BIAS < 0  -> hero hid LEFT  -> enemy spawns on LEFT,  moves RIGHT
;        SIDE_BIAS >= 0 -> hero hid RIGHT -> enemy spawns on RIGHT, moves LEFT
;     2. Increment DEATH_COUNT.
;        From death 1 onward, enemy base speed = ENEMY_SPEED + DEATH_COUNT
;        (caps at ADAPT_SPEED_MAX=6 to stay fair).
;     3. Reset SIDE_BIAS = 0 for the next life.
;
;   Visible result:
;     - Run 1: enemy starts centre-right, speed 2 (normal).
;     - Die hugging left side: enemy spawns on LEFT next life,
;       approaching from the side you were hiding on.
;     - Die hugging right side: enemy spawns on RIGHT instead.
;     - Each death makes the enemy slightly faster (caps at +4).
;     - Same behaviour pattern produces the same spawn and speed.
;     - No Gate 4 behaviour regressed.
;
; DRAM state additions ($00010A+):
;   $00010A  SIDE_BIAS   signed word; + = right-biased, - = left-biased
;   $00010C  DEATH_COUNT word; 0 on first life, incremented on each death
;   $00010E  (reserved word, phrase-pad)
;
; All Gate 4 DRAM ($000100-$000108) and object list layout unchanged.
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

; ---- DRAM state — Gate 4 (unchanged) ----------------------
HERO_XPOS       equ     $000100
HERO_YPOS       equ     $000102
HERO_YVEL       equ     $000104
ENEMY_XPOS      equ     $000106
ENEMY_DIR       equ     $000108

; ---- DRAM state — Gate 5 additions -------------------------
SIDE_BIAS       equ     $00010A         ; signed word: - = left, + = right
DEATH_COUNT     equ     $00010C         ; word: how many times hero has died

; ---- Joystick ----------------------------------------------
JOY_ROW0        equ     $817E

; ---- Hero walk/jump limits ---------------------------------
XPOS_MIN        equ     177
XPOS_MAX        equ     486
XPOS_START      equ     257
XPOS_SPEED      equ     2
JUMP_VEL        equ     -14

; ---- Physics -----------------------------------------------
GRAVITY         equ     2
FLOOR_YPOS      equ     372

; ---- Screen centre (pixel-clocks) for side-bias tracking ---
; Display runs XPOS_MIN=177 to XPOS_MAX=486; midpoint = (177+486)/2 = 331
SCREEN_MID      equ     332

; ---- Enemy -------------------------------------------------
ENEMY_XMIN      equ     177
ENEMY_XMAX      equ     478
ENEMY_SPEED     equ     2               ; base speed (pixel-clocks/frame)
ADAPT_SPEED_MAX equ     6               ; cap: base + max 4 deaths of acceleration
ENEMY_START_X   equ     350             ; first-life start (centre-right)
ENEMY_YPOS_HL   equ     380

; ---- Collision bbox thresholds -----------------------------
COLL_X_THRESH   equ     16
COLL_Y_THRESH   equ     20

; ---- VC blanking threshold ---------------------------------
VC_VDE          equ     507

; ---- Floor BITMAP PH0 (static) -----------------------------
;   DATA=PIX_FLOOR>>3=$001000  LINK=$004010>>3=$000802(->enemy)
;   HEIGHT=8  YPOS=420  TYPE=0
FLOOR_PH0_HI    equ     $00800008
FLOOR_PH0_LO    equ     $02020D20

; ---- Floor BITMAP PH1 (static) -----------------------------
FLOOR_PH1_HI    equ     $00000005
FLOOR_PH1_LO    equ     $0140C0B1

; ---- Enemy BITMAP PH0 (static Y) ---------------------------
;   DATA=PIX_ENEMY>>3=$001200  LINK=$004020>>3=$000804(->hero)
;   HEIGHT=16  YPOS=380
ENEMY_PH0_HI    equ     $00900008
ENEMY_PH0_LO    equ     $04040BB8

; ---- Enemy BITMAP PH1 (dynamic XPOS) -----------------------
ENEMY_PH1_HI    equ     $00008000
ENEMY_PH1_UPPER equ     $4010C000

; ---- Hero BITMAP PH0 (dynamic YPOS) ------------------------
;   DATA=PIX_HERO>>3=$001280  LINK=$004030>>3=$000806(->STOP)
;   HEIGHT=24
HERO_PH0_HI     equ     $00940008
HERO_PH0_LO_MSK equ     $06060000

; ---- Hero BITMAP PH1 (dynamic XPOS, TRANS) -----------------
HERO_PH1_HI     equ     $00008000
HERO_PH1_UPPER  equ     $4010C000

; ---- STOP object -------------------------------------------
STOP_PH0_LO     equ     $00000004

; ============================================================
        .text

; ============================================================
; Entry — proven startup (verbatim gate4_slice.s)
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

; ---- Initialise DRAM state (Gate 4 unchanged) --------------
        move.w  #XPOS_START,HERO_XPOS
        move.w  #FLOOR_YPOS,HERO_YPOS
        move.w  #0,HERO_YVEL
        move.w  #ENEMY_START_X,ENEMY_XPOS
        move.w  #ENEMY_SPEED,ENEMY_DIR

; ---- Initialise Gate 5 memory state ------------------------
        move.w  #0,SIDE_BIAS            ; no bias yet
        move.w  #0,DEATH_COUNT          ; first life

; ---- Copy floor pixel data ($008000) -----------------------
        lea     floor_pixels,a1
        lea     PIX_FLOOR,a0
        move.w  #1279,d0
.copy_floor:
        move.l  (a1)+,(a0)+
        dbra    d0,.copy_floor

; ---- Copy enemy pixel data ($009000) -----------------------
        lea     enemy_pixels,a1
        lea     PIX_ENEMY,a0
        move.w  #127,d0
.copy_enemy:
        move.l  (a1)+,(a0)+
        dbra    d0,.copy_enemy

; ---- Copy hero pixel data ($009400) ------------------------
        lea     hero_pixels,a1
        lea     PIX_HERO,a0
        move.w  #191,d0
.copy_hero:
        move.l  (a1)+,(a0)+
        dbra    d0,.copy_hero

; ---- Build object list at $004000 --------------------------
        move.l  #FLOOR_PH0_HI,OP_LIST+0
        move.l  #FLOOR_PH0_LO,OP_LIST+4
        move.l  #FLOOR_PH1_HI,OP_LIST+8
        move.l  #FLOOR_PH1_LO,OP_LIST+12

        move.l  #ENEMY_PH0_HI,OP_LIST+16
        move.l  #ENEMY_PH0_LO,OP_LIST+20
        move.l  #ENEMY_PH1_HI,OP_LIST+24
        move.l  #(ENEMY_PH1_UPPER|ENEMY_START_X),OP_LIST+28

        move.l  #HERO_PH0_HI,OP_LIST+32
        moveq   #0,d0
        move.w  #FLOOR_YPOS,d0
        lsl.l   #3,d0
        or.l    #HERO_PH0_LO_MSK,d0
        move.l  d0,OP_LIST+36
        move.l  #HERO_PH1_HI,OP_LIST+40
        move.l  #(HERO_PH1_UPPER|XPOS_START),OP_LIST+44

        move.l  #0,OP_LIST+48
        move.l  #STOP_PH0_LO,OP_LIST+52
        move.l  #0,OP_LIST+56
        move.l  #0,OP_LIST+60

; ---- Point OLP at object list (swap trick) -----------------
        move.l  #OP_LIST,d0
        swap    d0
        move.l  d0,OLP

; ---- NTSC/PAL video timing ---------------------------------
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
; Main loop — one iteration per frame in blanking window
;
; Register allocation:
;   d0 = scratch
;   d1 = hero_xpos (word)
;   d2 = hero_ypos (word, halflines)
;   d3 = hero_yvel (signed word)
;   d4 = enemy_xpos (word)
;   d5 = enemy_dir  (word, signed speed magnitude with sign)
; ============================================================

forever:
        ; --------------------------------------------------
        ; Wait for end of active picture
        ; --------------------------------------------------
.wait_pic:
        move.w  VC,d0
        cmp.w   #VC_VDE,d0
        blt.s   .wait_pic

        ; --------------------------------------------------
        ; Read joystick Row 0
        ; --------------------------------------------------
        move.w  #JOY_ROW0,JOYSTICK
        move.w  JOYSTICK,d0

        move.w  HERO_XPOS,d1
        move.w  HERO_YPOS,d2
        move.w  HERO_YVEL,d3

        ; LEFT (bit 10, active-LOW)
        btst    #10,d0
        bne.s   .chk_right
        sub.w   #XPOS_SPEED,d1
        cmp.w   #XPOS_MIN,d1
        bge.s   .chk_right
        move.w  #XPOS_MIN,d1

.chk_right:
        ; RIGHT (bit 11, active-LOW)
        btst    #11,d0
        bne.s   .chk_jump
        add.w   #XPOS_SPEED,d1
        cmp.w   #XPOS_MAX,d1
        ble.s   .chk_jump
        move.w  #XPOS_MAX,d1

.chk_jump:
        ; JUMP (bit 8, active-LOW); only when grounded
        btst    #8,d0
        bne.s   .physics
        cmp.w   #FLOOR_YPOS,d2
        bne.s   .physics
        tst.w   d3
        bne.s   .physics
        move.w  #JUMP_VEL,d3

.physics:
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
        ; Side-bias tracking — update every frame hero is alive
        ;   hero_xpos < SCREEN_MID -> left-biased -> bias--
        ;   hero_xpos >= SCREEN_MID -> right-biased -> bias++
        ; --------------------------------------------------
        cmp.w   #SCREEN_MID,d1
        bge.s   .bias_right
        sub.w   #1,SIDE_BIAS
        bra.s   .bias_done
.bias_right:
        add.w   #1,SIDE_BIAS
.bias_done:

        ; --------------------------------------------------
        ; Enemy AI — bounce using current ENEMY_DIR
        ; --------------------------------------------------
        move.w  ENEMY_XPOS,d4
        move.w  ENEMY_DIR,d5

        add.w   d5,d4

        cmp.w   #ENEMY_XMIN,d4
        bge.s   .chk_emax
        move.w  #ENEMY_XMIN,d4
        neg.w   d5
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
        ; Collision detection
        ; --------------------------------------------------
        move.w  d1,d0
        sub.w   d4,d0
        bpl.s   .abs_x
        neg.w   d0
.abs_x:
        cmp.w   #COLL_X_THRESH,d0
        bge.s   .no_hit

        move.w  d2,d0
        sub.w   #ENEMY_YPOS_HL,d0
        bpl.s   .abs_y
        neg.w   d0
.abs_y:
        cmp.w   #COLL_Y_THRESH,d0
        bge.s   .no_hit

        ; ==================================================
        ; DEATH — apply adaptive memory before resetting
        ; ==================================================

        ; 1. Increment death count
        add.w   #1,DEATH_COUNT

        ; 2. Compute adapted speed:
        ;    speed = ENEMY_SPEED + DEATH_COUNT
        ;    capped at ADAPT_SPEED_MAX
        move.w  DEATH_COUNT,d0
        add.w   #ENEMY_SPEED,d0
        cmp.w   #ADAPT_SPEED_MAX,d0
        ble.s   .speed_ok
        move.w  #ADAPT_SPEED_MAX,d0
.speed_ok:
        ; d0 = adapted speed magnitude (positive, 2..6)

        ; 3. Choose enemy spawn side from SIDE_BIAS:
        ;    SIDE_BIAS < 0 -> hero hid LEFT -> spawn enemy LEFT, move RIGHT (+speed)
        ;    SIDE_BIAS >= 0 -> hero hid RIGHT -> spawn enemy RIGHT, move LEFT (-speed)
        tst.w   SIDE_BIAS
        bmi.s   .spawn_left

.spawn_right:
        ; hero was on right side — enemy appears on right, moves left
        move.w  #ENEMY_XMAX,ENEMY_XPOS
        neg.w   d0                  ; direction = -speed (moving left)
        move.w  d0,ENEMY_DIR
        bra.s   .death_done

.spawn_left:
        ; hero was on left side — enemy appears on left, moves right
        move.w  #ENEMY_XMIN,ENEMY_XPOS
        move.w  d0,ENEMY_DIR        ; direction = +speed (moving right)

.death_done:
        ; 4. Reset bias for this life
        move.w  #0,SIDE_BIAS

        ; 5. Reset hero to start
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
        move.w  d4,d0
        and.w   #$0FFF,d0
        or.l    #ENEMY_PH1_UPPER,d0
        move.l  d0,OP_LIST+28

        ; --------------------------------------------------
        ; Refresh phrase 0s (OP zeroes HEIGHT each frame)
        ; --------------------------------------------------
        move.l  #FLOOR_PH0_HI,OP_LIST+0
        move.l  #FLOOR_PH0_LO,OP_LIST+4
        move.l  #ENEMY_PH0_HI,OP_LIST+16
        move.l  #ENEMY_PH0_LO,OP_LIST+20

        ; --------------------------------------------------
        ; Wait for new frame
        ; --------------------------------------------------
.wait_blank:
        move.w  VC,d0
        cmp.w   #VC_VDE,d0
        bge.s   .wait_blank

        bra     forever

; ============================================================
; Castle stone floor — 320x8 px CRY16 (verbatim)
; ============================================================
floor_pixels:
        .rept   160
        dc.l    $CE7BCE7B
        .endr
        .rept   160
        dc.l    $CE7BCE7B
        .endr
        .rept   160
        dc.l    $CE7BCE7B
        .endr
        .rept   160
        dc.l    $39433943
        .endr
        .rept   160
        dc.l    $CE7BCE7B
        .endr
        .rept   160
        dc.l    $CE7BCE7B
        .endr
        .rept   160
        dc.l    $39433943
        .endr
        .rept   160
        dc.l    $36013601
        .endr

; ============================================================
; Enemy sprite — 16x16 px CRY16 (verbatim gate4_slice.s)
; ============================================================
enemy_pixels:
        dc.l    $00000000,$00000000,$00000000,$00000000  ; row 0
        dc.l    $00003601,$36013601,$36013601,$36010000  ; row 1
        dc.l    $00003601,$F001CFCB,$CFCBF001,$36010000  ; row 2
        dc.l    $36013601,$F001CFCB,$CFCBF001,$36013601  ; row 3
        dc.l    $36013601,$36013601,$36013601,$36013601  ; row 4
        dc.l    $36013601,$CFCB3601,$3601CFCB,$36013601  ; row 5
        dc.l    $36013601,$3601CFCB,$CFCB3601,$36013601  ; row 6
        dc.l    $00003601,$36013601,$36013601,$36010000  ; row 7
        dc.l    $00003601,$36013601,$36013601,$36010000  ; row 8
        dc.l    $36013601,$3601CFCB,$CFCB3601,$36013601  ; row 9
        dc.l    $36013601,$CFCB3601,$3601CFCB,$36013601  ; row 10
        dc.l    $36013601,$36013601,$36013601,$36013601  ; row 11
        dc.l    $00003601,$36013601,$36013601,$36010000  ; row 12
        dc.l    $00003601,$3601CFCB,$CFCB3601,$36010000  ; row 13
        dc.l    $00000000,$3601CFCB,$CFCB3601,$00000000  ; row 14
        dc.l    $00000000,$00003601,$36010000,$00000000  ; row 15

; ============================================================
; Hero idle sprite — 16x24 px CRY16 (verbatim)
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
