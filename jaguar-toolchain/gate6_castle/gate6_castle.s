; ============================================================
; gate6_castle.s  —  Castle Remembers — Gate 6: Three-Floor Castle
; Target : Atari Jaguar (68000 + Tom/Jerry)
; Toolchain: RMAC 2.5.2 / RLN 1.7.7
; Load / Entry: $802000
;
; Builds on Gate 5 (gate5_memory.s). All proven systems preserved.
; Adds three distinct floors with ladder transitions, two enemies,
; and a win/escape state on Floor 3.
;
; FLOOR LAYOUT (NTSC rows 0-239):
;   Floor 1 — Choice/Observation  — row 210, YPOS_HL=420, hero_ypos=372
;   Floor 2 — Lever/Escalation    — row 140, YPOS_HL=280, hero_ypos=232
;   Floor 3 — Exit/Judgment       — row  70, YPOS_HL=140, hero_ypos= 92
;
; LADDER ZONES (grounded touch = instant floor transition):
;   F1->F2: hero_xpos >= LADDER_R1 (460) on Floor 1 -> go to Floor 2, xpos=177
;   F2->F3: hero_xpos <= LADDER_L2 (194) on Floor 2 -> go to Floor 3, xpos=460
;   F3 exit: hero_xpos >= LADDER_R3 (460) on Floor 3 -> WIN state
;
; WIN STATE: BG flashes bright gold for 180 frames, then resets to Floor 1.
;   Preserves SIDE_BIAS / DEATH_COUNT across win (soft reset only).
;
; ENEMIES:
;   Enemy1 — Floor 1 only. Gate 5 side-bias adaptation preserved.
;   Enemy2 — Floor 3 only. Spawn side and speed driven by SIDE_BIAS + DEATH_COUNT.
;     Hidden (HEIGHT=0) when hero is not on Floor 3.
;   Neither enemy is shown on Floor 2 (quiet escalation floor).
;
; DEATH from any floor respawns hero at Floor 1 start. DEATH_COUNT++.
; SIDE_BIAS resets on death (not on floor transition — keeps accruing).
;
; OBJECT LIST at $004000:
;   $004000  floor1 BITMAP  LINK->floor2   (PH0 refreshed; PH1 static)
;   $004010  floor2 BITMAP  LINK->floor3
;   $004020  floor3 BITMAP  LINK->enemy1
;   $004030  enemy1 BITMAP  LINK->enemy2   (hidden on F2/F3: HEIGHT set 0)
;   $004040  enemy2 BITMAP  LINK->hero     (hidden on F1/F2: HEIGHT set 0)
;   $004050  hero   BITMAP  LINK->STOP     (YPOS/XPOS dynamic, TRANS)
;   $004060  STOP
;
; DRAM state:
;   $000100  HERO_XPOS    word
;   $000102  HERO_YPOS    word (halflines)
;   $000104  HERO_YVEL    signed word
;   $000106  ENEMY1_XPOS  word
;   $000108  ENEMY1_DIR   word
;   $00010A  SIDE_BIAS    signed word
;   $00010C  DEATH_COUNT  word
;   $00010E  FLOOR_NUM    word (1, 2, or 3)
;   $000110  ENEMY2_XPOS  word
;   $000112  ENEMY2_DIR   word
;   $000114  WIN_TIMER    word (counts down during win flash, 0=not winning)
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
VMODE_VAL       equ     $0681
BG_VAL          equ     $0000
BG_WIN          equ     $CFCB           ; gold flash on escape

; ---- Object list base --------------------------------------
OP_LIST         equ     $004000
; floor1 @+0   floor2 @+16   floor3 @+32
; enemy1 @+48  enemy2 @+64   hero   @+80   STOP @+96

; ---- Pixel data --------------------------------------------
PIX_FLOOR       equ     $008000         ; 320x8 CRY16, 5120 bytes (shared all floors)
PIX_ENEMY       equ     $009000         ; 16x16 CRY16, 512 bytes (shared both enemies)
PIX_HERO        equ     $009400         ; 16x24 CRY16, 768 bytes

; ---- DRAM state --------------------------------------------
HERO_XPOS       equ     $000100
HERO_YPOS       equ     $000102
HERO_YVEL       equ     $000104
ENEMY1_XPOS     equ     $000106
ENEMY1_DIR      equ     $000108
SIDE_BIAS       equ     $00010A
DEATH_COUNT     equ     $00010C
FLOOR_NUM       equ     $00010E
ENEMY2_XPOS     equ     $000110
ENEMY2_DIR      equ     $000112
WIN_TIMER       equ     $000114

; ---- Joystick ----------------------------------------------
JOY_ROW0        equ     $817E

; ---- Hero limits -------------------------------------------
XPOS_MIN        equ     177
XPOS_MAX        equ     486
XPOS_START      equ     257
XPOS_SPEED      equ     2
JUMP_VEL        equ     -14

; ---- Physics -----------------------------------------------
GRAVITY         equ     2

; ---- Floor standing YPOS (halflines) -----------------------
F1_YPOS         equ     372             ; Floor1: 420-48
F2_YPOS         equ     232             ; Floor2: 280-48
F3_YPOS         equ     92              ; Floor3: 140-48

; ---- Ladder zones ------------------------------------------
LADDER_R1       equ     460             ; F1 right edge -> climb to F2
LADDER_L2       equ     194             ; F2 left edge  -> climb to F3
LADDER_R3       equ     460             ; F3 right edge -> WIN

; ---- Screen midpoint for bias tracking ---------------------
SCREEN_MID      equ     332

; ---- Enemy base constants ----------------------------------
ENEMY_XMIN      equ     177
ENEMY_XMAX      equ     478
ENEMY_SPEED     equ     2
ADAPT_SPEED_MAX equ     6
ENEMY1_START_X  equ     350
ENEMY2_START_X  equ     300

; ---- Enemy Y positions (halflines) -------------------------
; Enemy on floor: floor_YPOS_HL - 32 (16px * 2 halflines/px)
ENEMY1_YPOS_HL  equ     380             ; Floor1: proven value
ENEMY2_YPOS_HL  equ     108             ; Floor3: 140-32

; ---- Collision thresholds ----------------------------------
COLL_X_THRESH   equ     16
COLL_Y_THRESH   equ     20

; ---- Win timer count ---------------------------------------
WIN_FRAMES      equ     180             ; 3 seconds at 60fps

; ---- VC blanking -------------------------------------------
VC_VDE          equ     507

; ============================================================
; OBJECT PHRASE CONSTANTS
; All addresses are precise — verified by hand.
;
; Formula recap:
;   PH0_HI = DATA[12:8]->PH0_HI[23:19] | LINK[11]->PH0_HI[3]
;   PH0_LO = LINK[7:0]->bits[31:24] | HEIGHT<<14 | YPOS<<3
;   PH1_HI = TRANS->bit15 | IWIDTH upper bits
;   PH1_LO = PITCH<<15|DEPTH<<12|DWIDTH<<18|XPOS
; ============================================================

; ---- Floor1 BITMAP -----------------------------------------
;   DATA=PIX_FLOOR>>3=$001000  LINK=$004010>>3=$000802(->floor2)
;   HEIGHT=8  YPOS_HL=420  XPOS=177  DEPTH=4  PITCH=1  DWIDTH=80 IWIDTH=80
F1_PH0_HI       equ     $00800008
F1_PH0_LO       equ     $02020D20
F1_PH1_HI       equ     $00000005
F1_PH1_LO       equ     $0140C0B1

; ---- Floor2 BITMAP -----------------------------------------
;   DATA=PIX_FLOOR>>3=$001000  LINK=$004020>>3=$000804(->floor3)
;   HEIGHT=8  YPOS_HL=280=$118  XPOS=177
;   PH0_LO: LINK[7:0]=$04->$04000000; 8<<14=$020000; 280<<3=$0380
F2_PH0_HI       equ     $00800008
F2_PH0_LO       equ     $04020380
F2_PH1_HI       equ     $00000005
F2_PH1_LO       equ     $0140C0B1

; ---- Floor3 BITMAP -----------------------------------------
;   DATA=PIX_FLOOR>>3=$001000  LINK=$004030>>3=$000806(->enemy1)
;   HEIGHT=8  YPOS_HL=140=$8C  XPOS=177
;   PH0_LO: LINK[7:0]=$06->$06000000; 8<<14=$020000; 140<<3=$0238
F3_PH0_HI       equ     $00800008
F3_PH0_LO       equ     $060201B8
F3_PH1_HI       equ     $00000005
F3_PH1_LO       equ     $0140C0B1

; ---- Enemy1 BITMAP -----------------------------------------
;   DATA=PIX_ENEMY>>3=$001200  LINK=$004040>>3=$000808(->enemy2)
;   HEIGHT=16  YPOS_HL=380  XPOS dynamic
;   DATA=$1200: bit12->PH0_HI.23=$00800000; bit9->PH0_HI.20=$00100000 -> $00900000
;   LINK=$808: bit11->PH0_HI.3=$00000008 -> PH0_HI=$00900008
;   PH0_LO: LINK[7:0]=$08->$08000000; 16<<14=$040000; 380<<3=$0BB8
E1_PH0_HI       equ     $00900008
E1_PH0_LO       equ     $08040BB8
E1_PH0_LO_HIDE  equ     $08000BB8       ; HEIGHT=0: hide enemy1 (OP skips it)
E1_PH1_HI       equ     $00008000
E1_PH1_UPPER    equ     $4010C000

; ---- Enemy2 BITMAP -----------------------------------------
;   DATA=PIX_ENEMY>>3=$001200  LINK=$004050>>3=$00080A(->hero)
;   HEIGHT=16  YPOS_HL=108  XPOS dynamic
;   LINK=$80A: bit11->PH0_HI.3=$00000008 -> PH0_HI=$00900008
;   PH0_LO: LINK[7:0]=$0A->$0A000000; 16<<14=$040000; 108<<3=$0360... 
;   wait: 108*8=864. 864=$360. PH0_LO=$0A040000|$360=$0A040360
E2_PH0_HI       equ     $00900008
E2_PH0_LO       equ     $0A040360
E2_PH0_LO_HIDE  equ     $0A000360       ; HEIGHT=0: hide enemy2
E2_PH1_HI       equ     $00008000
E2_PH1_UPPER    equ     $4010C000

; ---- Hero BITMAP -------------------------------------------
;   DATA=PIX_HERO>>3=$001280  LINK=$004060>>3=$00080C(->STOP)
;   HEIGHT=24  YPOS dynamic  XPOS dynamic  TRANS=1
;   DATA=$1280: bit12=$00800000; bit9=$00100000; bit7=$00040000 -> $00940000
;   LINK=$80C: bit11->PH0_HI.3=$00000008; bit3->PH0_LO.27=... 
;   LINK[7:0]=$0C -> PH0_LO[31:24]=$0C000000; 24<<14=$060000
HERO_PH0_HI     equ     $00940008
HERO_PH0_LO_MSK equ     $0C060000       ; | (ypos<<3)
HERO_PH1_HI     equ     $00008000
HERO_PH1_UPPER  equ     $4010C000

; ---- STOP object -------------------------------------------
STOP_PH0_LO     equ     $00000004

; ============================================================
        .text

; ============================================================
; Entry — proven startup (verbatim)
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

; ---- Full DRAM init ----------------------------------------
        move.w  #XPOS_START,HERO_XPOS
        move.w  #F1_YPOS,HERO_YPOS
        move.w  #0,HERO_YVEL
        move.w  #ENEMY1_START_X,ENEMY1_XPOS
        move.w  #ENEMY_SPEED,ENEMY1_DIR
        move.w  #0,SIDE_BIAS
        move.w  #0,DEATH_COUNT
        move.w  #1,FLOOR_NUM            ; start on Floor 1
        move.w  #ENEMY2_START_X,ENEMY2_XPOS
        move.w  #ENEMY_SPEED,ENEMY2_DIR
        move.w  #0,WIN_TIMER

; ---- Copy pixel data ---------------------------------------
        lea     floor_pixels,a1
        lea     PIX_FLOOR,a0
        move.w  #1279,d0
.copy_floor:
        move.l  (a1)+,(a0)+
        dbra    d0,.copy_floor

        lea     enemy_pixels,a1
        lea     PIX_ENEMY,a0
        move.w  #127,d0
.copy_enemy:
        move.l  (a1)+,(a0)+
        dbra    d0,.copy_enemy

        lea     hero_pixels,a1
        lea     PIX_HERO,a0
        move.w  #191,d0
.copy_hero:
        move.l  (a1)+,(a0)+
        dbra    d0,.copy_hero

; ---- Build object list at $004000 --------------------------
        ; Floor1 (always visible, static PH1)
        move.l  #F1_PH0_HI,OP_LIST+0
        move.l  #F1_PH0_LO,OP_LIST+4
        move.l  #F1_PH1_HI,OP_LIST+8
        move.l  #F1_PH1_LO,OP_LIST+12

        ; Floor2 (always visible)
        move.l  #F2_PH0_HI,OP_LIST+16
        move.l  #F2_PH0_LO,OP_LIST+20
        move.l  #F2_PH1_HI,OP_LIST+24
        move.l  #F2_PH1_LO,OP_LIST+28

        ; Floor3 (always visible)
        move.l  #F3_PH0_HI,OP_LIST+32
        move.l  #F3_PH0_LO,OP_LIST+36
        move.l  #F3_PH1_HI,OP_LIST+40
        move.l  #F3_PH1_LO,OP_LIST+44

        ; Enemy1 (Floor 1, initial pos)
        move.l  #E1_PH0_HI,OP_LIST+48
        move.l  #E1_PH0_LO,OP_LIST+52
        move.l  #E1_PH1_HI,OP_LIST+56
        move.l  #(E1_PH1_UPPER|ENEMY1_START_X),OP_LIST+60

        ; Enemy2 (Floor 3, hidden at start — on Floor1)
        move.l  #E2_PH0_HI,OP_LIST+64
        move.l  #E2_PH0_LO_HIDE,OP_LIST+68
        move.l  #E2_PH1_HI,OP_LIST+72
        move.l  #(E2_PH1_UPPER|ENEMY2_START_X),OP_LIST+76

        ; Hero (initial Floor1 pos)
        move.l  #HERO_PH0_HI,OP_LIST+80
        moveq   #0,d0
        move.w  #F1_YPOS,d0
        lsl.l   #3,d0
        or.l    #HERO_PH0_LO_MSK,d0
        move.l  d0,OP_LIST+84
        move.l  #HERO_PH1_HI,OP_LIST+88
        move.l  #(HERO_PH1_UPPER|XPOS_START),OP_LIST+92

        ; STOP
        move.l  #0,OP_LIST+96
        move.l  #STOP_PH0_LO,OP_LIST+100
        move.l  #0,OP_LIST+104
        move.l  #0,OP_LIST+108

; ---- Point OLP ---------------------------------------------
        move.l  #OP_LIST,d0
        swap    d0
        move.l  d0,OLP

; ---- Video timing ------------------------------------------
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
; MAIN LOOP
;
; Register allocation:
;   d0 = scratch
;   d1 = hero_xpos (word)
;   d2 = hero_ypos (word, halflines)
;   d3 = hero_yvel (signed word)
;   d4 = enemy1_xpos (word)
;   d5 = enemy1_dir  (word)
;   d6 = floor_num   (word, 1/2/3)
;   d7 = win_timer   (word)
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
        ; WIN TIMER — if active, flash BG and count down
        ; --------------------------------------------------
        move.w  WIN_TIMER,d7
        tst.w   d7
        beq     .not_winning

        ; Alternating gold flash: odd frames gold, even frames black
        btst    #0,d7
        beq.s   .win_dark
        move.w  #BG_WIN,BG
        bra.s   .win_tick
.win_dark:
        move.w  #BG_VAL,BG
.win_tick:
        sub.w   #1,d7
        move.w  d7,WIN_TIMER
        bne.s   .win_refresh_op         ; still counting — skip gameplay

        ; Timer hit zero — reset to Floor 1
        move.w  #BG_VAL,BG
        move.w  #XPOS_START,HERO_XPOS
        move.w  #F1_YPOS,HERO_YPOS
        move.w  #0,HERO_YVEL
        move.w  #1,FLOOR_NUM
        move.w  #ENEMY1_START_X,ENEMY1_XPOS
        move.w  #ENEMY_SPEED,ENEMY1_DIR
        ; enemy2 reset with adapted params preserved from last death
        ; (SIDE_BIAS already 0 from last death; just keep DEATH_COUNT)
        move.w  #0,SIDE_BIAS

.win_refresh_op:
        ; Still need to refresh PH0s so OP doesn't blank the floors
        move.l  #F1_PH0_HI,OP_LIST+0
        move.l  #F1_PH0_LO,OP_LIST+4
        move.l  #F2_PH0_HI,OP_LIST+16
        move.l  #F2_PH0_LO,OP_LIST+20
        move.l  #F3_PH0_HI,OP_LIST+32
        move.l  #F3_PH0_LO,OP_LIST+36
        bra     .wait_frame

.not_winning:
        ; --------------------------------------------------
        ; Load game state into registers
        ; --------------------------------------------------
        move.w  HERO_XPOS,d1
        move.w  HERO_YPOS,d2
        move.w  HERO_YVEL,d3
        move.w  FLOOR_NUM,d6

        ; --------------------------------------------------
        ; Read joystick
        ; --------------------------------------------------
        move.w  #JOY_ROW0,JOYSTICK
        move.w  JOYSTICK,d0

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
        ; JUMP (bit 8) — only when grounded on current floor
        btst    #8,d0
        bne.s   .physics
        ; determine current floor clamp to check grounded
        cmp.w   #1,d6
        bne.s   .jmp_chk_f2
        cmp.w   #F1_YPOS,d2
        bne.s   .physics
        bra.s   .do_jump
.jmp_chk_f2:
        cmp.w   #2,d6
        bne.s   .jmp_chk_f3
        cmp.w   #F2_YPOS,d2
        bne.s   .physics
        bra.s   .do_jump
.jmp_chk_f3:
        cmp.w   #F3_YPOS,d2
        bne.s   .physics
.do_jump:
        tst.w   d3
        bne.s   .physics
        move.w  #JUMP_VEL,d3

.physics:
        add.w   #GRAVITY,d3
        add.w   d3,d2

        ; Floor clamp for current floor
        cmp.w   #1,d6
        bne.s   .phys_f2
        cmp.w   #F1_YPOS,d2
        ble.s   .phys_done
        move.w  #F1_YPOS,d2
        moveq   #0,d3
        bra.s   .phys_done
.phys_f2:
        cmp.w   #2,d6
        bne.s   .phys_f3
        cmp.w   #F2_YPOS,d2
        ble.s   .phys_done
        move.w  #F2_YPOS,d2
        moveq   #0,d3
        bra.s   .phys_done
.phys_f3:
        cmp.w   #F3_YPOS,d2
        ble.s   .phys_done
        move.w  #F3_YPOS,d2
        moveq   #0,d3
.phys_done:

        ; --------------------------------------------------
        ; Side-bias tracking (runs on all floors)
        ; --------------------------------------------------
        cmp.w   #SCREEN_MID,d1
        bge.s   .bias_right
        sub.w   #1,SIDE_BIAS
        bra.s   .bias_done
.bias_right:
        add.w   #1,SIDE_BIAS
.bias_done:

        ; --------------------------------------------------
        ; Ladder / floor transition checks (only when grounded)
        ; --------------------------------------------------
        ; Must be grounded: check yvel==0 and ypos==floor_ypos
        tst.w   d3
        bne.s   .no_ladder              ; airborne

        cmp.w   #1,d6
        bne.s   .ldr_chk_f2

        ; Floor 1: right edge -> Floor 2
        cmp.w   #F1_YPOS,d2
        bne.s   .no_ladder
        cmp.w   #LADDER_R1,d1
        blt.s   .no_ladder
        ; Transition F1 -> F2
        move.w  #2,d6
        move.w  #F2_YPOS,d2
        move.w  #XPOS_MIN,d1            ; land on left side of F2
        moveq   #0,d3
        bra.s   .ladder_done

.ldr_chk_f2:
        cmp.w   #2,d6
        bne.s   .ldr_chk_f3

        ; Floor 2: left edge -> Floor 3
        cmp.w   #F2_YPOS,d2
        bne.s   .no_ladder
        cmp.w   #LADDER_L2,d1
        bgt.s   .no_ladder
        ; Transition F2 -> F3
        move.w  #3,d6
        move.w  #F3_YPOS,d2
        move.w  #XPOS_MAX,d1            ; land on right side of F3
        moveq   #0,d3
        bra.s   .ladder_done

.ldr_chk_f3:
        ; Floor 3: right edge -> WIN
        cmp.w   #F3_YPOS,d2
        bne.s   .no_ladder
        cmp.w   #LADDER_R3,d1
        blt.s   .no_ladder
        ; ESCAPE — start win timer
        move.w  #WIN_FRAMES,WIN_TIMER
        move.w  #BG_WIN,BG
        ; hero stays visible; just let timer take over
        move.w  d1,HERO_XPOS
        move.w  d2,HERO_YPOS
        move.w  d3,HERO_YVEL
        move.w  d6,FLOOR_NUM
        bra     .skip_enemies

.ladder_done:
.no_ladder:

        ; --------------------------------------------------
        ; Store hero state
        ; --------------------------------------------------
        move.w  d1,HERO_XPOS
        move.w  d2,HERO_YPOS
        move.w  d3,HERO_YVEL
        move.w  d6,FLOOR_NUM

        ; --------------------------------------------------
        ; Enemy1 — active only on Floor 1
        ; --------------------------------------------------
        cmp.w   #1,d6
        bne     .enemy1_hide

        move.w  ENEMY1_XPOS,d4
        move.w  ENEMY1_DIR,d5

        add.w   d5,d4
        cmp.w   #ENEMY_XMIN,d4
        bge.s   .e1_chk_max
        move.w  #ENEMY_XMIN,d4
        neg.w   d5
        bra.s   .e1_store
.e1_chk_max:
        cmp.w   #ENEMY_XMAX,d4
        ble.s   .e1_store
        move.w  #ENEMY_XMAX,d4
        neg.w   d5
.e1_store:
        move.w  d4,ENEMY1_XPOS
        move.w  d5,ENEMY1_DIR

        ; Collision with enemy1 (hero on Floor1)
        move.w  d1,d0
        sub.w   d4,d0
        bpl.s   .e1_abs
        neg.w   d0
.e1_abs:
        cmp.w   #COLL_X_THRESH,d0
        bge.s   .e1_no_hit

        move.w  d2,d0
        sub.w   #ENEMY1_YPOS_HL,d0
        bpl.s   .e1_abs_y
        neg.w   d0
.e1_abs_y:
        cmp.w   #COLL_Y_THRESH,d0
        bge.s   .e1_no_hit

        ; Death on Floor 1
        bsr     do_death
        bra     .skip_enemies

.e1_no_hit:
        ; Write enemy1 PH1 with current xpos
        move.l  #E1_PH1_HI,OP_LIST+56
        move.w  d4,d0
        and.w   #$0FFF,d0
        or.l    #E1_PH1_UPPER,d0
        move.l  d0,OP_LIST+60
        ; Show enemy1 (restore HEIGHT in PH0_LO)
        move.l  #E1_PH0_HI,OP_LIST+48
        move.l  #E1_PH0_LO,OP_LIST+52
        ; Hide enemy2
        move.l  #E2_PH0_HI,OP_LIST+64
        move.l  #E2_PH0_LO_HIDE,OP_LIST+68
        bra     .enemies_done

.enemy1_hide:
        ; Not on Floor 1 — hide enemy1
        move.l  #E1_PH0_HI,OP_LIST+48
        move.l  #E1_PH0_LO_HIDE,OP_LIST+52

        ; --------------------------------------------------
        ; Enemy2 — active only on Floor 3
        ; --------------------------------------------------
        cmp.w   #3,d6
        bne     .enemy2_hide

        move.w  ENEMY2_XPOS,d4
        move.w  ENEMY2_DIR,d5

        add.w   d5,d4
        cmp.w   #ENEMY_XMIN,d4
        bge.s   .e2_chk_max
        move.w  #ENEMY_XMIN,d4
        neg.w   d5
        bra.s   .e2_store
.e2_chk_max:
        cmp.w   #ENEMY_XMAX,d4
        ble.s   .e2_store
        move.w  #ENEMY_XMAX,d4
        neg.w   d5
.e2_store:
        move.w  d4,ENEMY2_XPOS
        move.w  d5,ENEMY2_DIR

        ; Collision with enemy2 (hero on Floor3)
        move.w  d1,d0
        sub.w   d4,d0
        bpl.s   .e2_abs
        neg.w   d0
.e2_abs:
        cmp.w   #COLL_X_THRESH,d0
        bge.s   .e2_no_hit

        move.w  d2,d0
        sub.w   #ENEMY2_YPOS_HL,d0
        bpl.s   .e2_abs_y
        neg.w   d0
.e2_abs_y:
        cmp.w   #COLL_Y_THRESH,d0
        bge.s   .e2_no_hit

        ; Death on Floor 3
        bsr     do_death
        bra     .skip_enemies

.e2_no_hit:
        ; Write enemy2 PH1
        move.l  #E2_PH1_HI,OP_LIST+72
        move.w  d4,d0
        and.w   #$0FFF,d0
        or.l    #E2_PH1_UPPER,d0
        move.l  d0,OP_LIST+76
        ; Show enemy2
        move.l  #E2_PH0_HI,OP_LIST+64
        move.l  #E2_PH0_LO,OP_LIST+68
        bra.s   .enemies_done

.enemy2_hide:
        ; Floor 2 (or unexpected) — hide both enemies
        move.l  #E2_PH0_HI,OP_LIST+64
        move.l  #E2_PH0_LO_HIDE,OP_LIST+68

.enemies_done:
.skip_enemies:

        ; --------------------------------------------------
        ; Write hero BITMAP (dynamic YPOS + XPOS)
        ; --------------------------------------------------
        move.w  HERO_XPOS,d1
        move.w  HERO_YPOS,d2

        move.l  #HERO_PH0_HI,OP_LIST+80
        moveq   #0,d0
        move.w  d2,d0
        lsl.l   #3,d0
        or.l    #HERO_PH0_LO_MSK,d0
        move.l  d0,OP_LIST+84

        move.l  #HERO_PH1_HI,OP_LIST+88
        move.l  #HERO_PH1_UPPER,d0
        and.w   #$0FFF,d1
        or.w    d1,d0
        move.l  d0,OP_LIST+92

        ; --------------------------------------------------
        ; Refresh all floor PH0s (OP zeroes HEIGHT each frame)
        ; --------------------------------------------------
        move.l  #F1_PH0_HI,OP_LIST+0
        move.l  #F1_PH0_LO,OP_LIST+4
        move.l  #F2_PH0_HI,OP_LIST+16
        move.l  #F2_PH0_LO,OP_LIST+20
        move.l  #F3_PH0_HI,OP_LIST+32
        move.l  #F3_PH0_LO,OP_LIST+36

        ; --------------------------------------------------
        ; Wait for new frame
        ; --------------------------------------------------
.wait_frame:
        move.w  VC,d0
        cmp.w   #VC_VDE,d0
        bge.s   .wait_frame

        bra     forever

; ============================================================
; do_death — subroutine called on any collision death
;   Applies adaptive memory, resets hero to Floor 1 start.
;   Preserves DEATH_COUNT and SIDE_BIAS accumulation logic.
;   Called with BSR; must not trash d1-d6 (restores hero via DRAM).
; ============================================================
do_death:
        ; 1. Increment death count
        add.w   #1,DEATH_COUNT

        ; 2. Compute adapted speed = ENEMY_SPEED + DEATH_COUNT, cap at MAX
        move.w  DEATH_COUNT,d0
        add.w   #ENEMY_SPEED,d0
        cmp.w   #ADAPT_SPEED_MAX,d0
        ble.s   .ds_speed_ok
        move.w  #ADAPT_SPEED_MAX,d0
.ds_speed_ok:
        ; d0 = adapted speed magnitude

        ; 3. Spawn side from SIDE_BIAS — applies to BOTH enemies
        tst.w   SIDE_BIAS
        bmi.s   .ds_spawn_left

        ; Hero was right-biased — enemies come from right
        move.w  #ENEMY_XMAX,ENEMY1_XPOS
        move.w  #ENEMY_XMAX,ENEMY2_XPOS
        neg.w   d0
        move.w  d0,ENEMY1_DIR
        move.w  d0,ENEMY2_DIR
        bra.s   .ds_bias_done

.ds_spawn_left:
        ; Hero was left-biased — enemies come from left
        move.w  #ENEMY_XMIN,ENEMY1_XPOS
        move.w  #ENEMY_XMIN,ENEMY2_XPOS
        move.w  d0,ENEMY1_DIR
        move.w  d0,ENEMY2_DIR

.ds_bias_done:
        ; 4. Reset SIDE_BIAS for this life
        move.w  #0,SIDE_BIAS

        ; 5. Reset hero to Floor 1 start
        move.w  #XPOS_START,HERO_XPOS
        move.w  #F1_YPOS,HERO_YPOS
        move.w  #0,HERO_YVEL
        move.w  #1,FLOOR_NUM

        ; 6. Force registers to match new state (caller uses d1/d2/d3/d6)
        move.w  #XPOS_START,d1
        move.w  #F1_YPOS,d2
        moveq   #0,d3
        move.w  #1,d6

        rts

; ============================================================
; Castle stone floor — 320x8 px CRY16
; V0 Gatehouse ashlar (kimi/visual-refinement)
; Pixel data only — same address (PIX_FLOOR), same 5120 bytes.
; Rows 6-7 kept uniform dark: PIX_ENEMY init overwrites floor
; bytes $1000-$11FF (overlap finding preserved for Bob's audit).
; ============================================================
floor_pixels:
; row 0 — highlight cap, worn polished path px56-103, chips
        dc.l    $CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C
        dc.l    $CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C
        dc.l    $CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C
        dc.l    $CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE8ECE8E,$CE8ECE8E,$CE8ECE8E,$CE8ECE8E
        dc.l    $CE52CE52,$CE8ECE8E,$CE8ECE8E,$CE8ECE8E,$CE8ECE8E,$CE8ECE8E,$CE8ECE8E,$CE8ECE8E
        dc.l    $CE8ECE8E,$CE8ECE8E,$CE8ECE8E,$CE8ECE8E,$CE52CE52,$CE8ECE8E,$CE8ECE8E,$CE8ECE8E
        dc.l    $CE8ECE8E,$CE8ECE8E,$CE8ECE8E,$CE8ECE8E,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C
        dc.l    $CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C
        dc.l    $CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C
        dc.l    $CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C
        dc.l    $CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C
        dc.l    $CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C
        dc.l    $CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C
        dc.l    $CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C
        dc.l    $CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C
        dc.l    $CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C
        dc.l    $CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C
        dc.l    $CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C
        dc.l    $CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C
        dc.l    $CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C,$CE9CCE9C
; row 1 — ashlar course A, joints x%16=15, warm tiles T3/T6/T9/T12
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
; row 2 — ashlar course A (repeat of row 1)
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27BD27B,$D27B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943
; row 3 — mortar, ground-down groove px72-87 under spawn
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$42384238,$42384238,$42384238,$42384238
        dc.l    $42384238,$42384238,$42384238,$42384238,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
; row 4 — ashlar course B, joints x%16=7
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
; row 5 — course B + wear pits px62-64/79-81/95-97, iron stud px90-91
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE52CE52
        dc.l    $CE52CE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE52
        dc.l    $CE52CE52,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$F001F001,$CE7BCE7B,$CE7BCE52
        dc.l    $CE52CE52,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
        dc.l    $CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3943,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B
; row 6 — uniform mortar (overlap zone: keep flat)
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
        dc.l    $39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943,$39433943
; row 7 — uniform shadow base (overlap zone: keep flat)
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601
        dc.l    $36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601,$36013601

; ============================================================
; Enemy sprite — 16x16 px CRY16
; V0 Sentinel Skull (kimi/visual-refinement)
; Pixel data only — same address (PIX_ENEMY), same 512 bytes.
; ============================================================
enemy_pixels:
        dc.l    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000  ; row 00
        dc.l    $00000000,$00000000,$36013601,$36013601,$36013601,$36013601,$00000000,$00000000  ; row 01
        dc.l    $00000000,$36013601,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$36013601,$00000000  ; row 02
        dc.l    $00003601,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$36010000  ; row 03
        dc.l    $00003601,$CE7BCE9C,$CE9CCE9C,$CE7BCE7B,$CE7BCE7B,$CE9CCE9C,$CE9CCE7B,$36010000  ; row 04
        dc.l    $00003601,$CE7BCE7B,$F001CFCB,$F001CE7B,$CE7BF001,$CFCBF001,$CE7BCE7B,$36010000  ; row 05
        dc.l    $00003601,$CE7BCE7B,$F001F001,$F001CE7B,$CE7BF001,$F001F001,$CE7BCE7B,$36010000  ; row 06
        dc.l    $00003601,$CE7BCE7B,$CE7BCE7B,$CE7B3601,$3601CE7B,$CE7BCE7B,$CE7BCE7B,$36010000  ; row 07
        dc.l    $00000000,$3601CE7B,$CE7BCE7B,$CE7BF001,$F001CE7B,$CE7BCE7B,$CE7B3601,$00000000  ; row 08
        dc.l    $00000000,$3601CE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3601,$00000000  ; row 09
        dc.l    $00000000,$00003601,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$CE7BCE7B,$36010000,$00000000  ; row 10
        dc.l    $00000000,$00003601,$CE7BF001,$CE7BF001,$F001CE7B,$F001CE7B,$36010000,$00000000  ; row 11
        dc.l    $00000000,$00000000,$3601CE7B,$CE7BCE7B,$CE7BCE7B,$CE7B3601,$00000000,$00000000  ; row 12
        dc.l    $00000000,$00000000,$00003601,$36013601,$36013601,$36010000,$00000000,$00000000  ; row 13
        dc.l    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000  ; row 14
        dc.l    $00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000,$00000000  ; row 15

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
