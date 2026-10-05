; ============================================================
; gate7_castle.s  —  Castle Remembers — Five-Floor Castle
; Target : Atari Jaguar (68000 + Tom/Jerry)
; Toolchain: RMAC 2.5.2 / RLN 1.7.7
; Load / Entry: $802000
;
; Builds on Gate 6 (gate6_castle.s). Bob's proven startup, OLP word-swap,
; video timing, joypad row-0 read and BITMAP phrase layout are reused; the
; gameplay layer above them is new and follows the original game
; (original/index.html) — see GATE7_DESIGN in DEVLOG.md.
;
; FIVE FLOORS (one screen per floor, flip on ladders):
;   F1 Choice    — two doors (ACT opens) lead to side ladders up
;   F2 Lever     — two levers, one gate over the centre ladder
;   F3 Choice    — doors again; static spikes in both corridors
;   F4 Lever     — levers + gate, harsher
;   F5 Judgment  — the Judgment Wraith guards the exit arch
;
; CONTROLS (Virtual Jaguar default keys):
;   Z / C   LEFT / RIGHT               (pad Left/Right, J10/J11)
;   S       JUMP, or climb UP a ladder (pad Up, J8)
;   X       climb DOWN a ladder hole, otherwise ACT (pad Down, J9)
;   L       ACT: open door / pull lever / shove a guard (pad A, B1)
;
; THE CASTLE REMEMBERS (deterministic, persists across runs until reset):
;   door side, lever side, rush vs wait, confront vs avoid, trap deaths.
;   Each run end merges the run into memory (decay x0.8, win weight 2),
;   updates per-category pressure 0..3, and the next castle is rebuilt
;   from it (build_plan). Top-right HUD pips show each category's tier.
;
; LOW-LEVEL CHANGES vs Gate 6 (for Bob's audit):
;   * Object list is generated each frame into SHADOW, then copied to the
;     live list (OLP) at the start of vertical blank. The copy rewrites
;     every header, which is also the OP HEIGHT/DATA refresh.
;   * Phrase fields are built at runtime by build_list from the same
;     field layout Gate 6 uses (PH0: DATA<<43 | LINK<<24 | HEIGHT<<14 |
;     YPOS<<3; PH1: TRANS<<47 | IWIDTH<<28 | DWIDTH<<18 | PITCH 1 |
;     DEPTH 4 | XPOS). No hand-packed constants.
;   * Pixel data lives at PIXBASE ($010000) — no overlaps.
; ============================================================

; ---- Tom registers (verbatim) ------------------------------
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

; ---- Jerry registers (verbatim) ----------------------------
D_FLAGS         equ     $F1A100
D_CTRL          equ     $F1A114
J_INT           equ     $F10020
CONFIG          equ     $F14002
JOYSTICK        equ     $F14000
JOYBUTS         equ     $F14002

; ---- NTSC / PAL timing (verbatim) --------------------------
NTSC_WIDTH      equ     1229
NTSC_HMID       equ     787
NTSC_HEIGHT     equ     241
NTSC_VMID       equ     266
PAL_WIDTH       equ     1255
PAL_HMID        equ     821
PAL_HEIGHT      equ     287
PAL_VMID        equ     322

VMODE_VAL       equ     $0681           ; CRY16 + VIDEN + BGEN + PWIDTH4
BG_VAL          equ     $0000
BG_WIN          equ     $CFCB           ; Bob's gold flash
BG_DEATH        equ     $E26E           ; dark red
BG_WHISPER      equ     $D746           ; dim ember: "the castle remembers"
VC_VDE          equ     507
JOY_ROW0        equ     $817E

; ---- DRAM map ----------------------------------------------
STATE           equ     $001000         ; game state block (a5)
OBJS            equ     $002000         ; object records, 16 bytes each
LIVE            equ     $004000         ; live OP list (OLP points here)
SHADOW          equ     $004800         ; next frame's list, copied in blank
HUDBUF          equ     $00F000         ; 320x6 CRY16 HUD, drawn by the CPU
PIXBASE         equ     $010000         ; art copied here from ROM

; ---- objects (list order = draw order) ---------------------
O_LAD0          equ     0
O_LAD1          equ     1
O_LAD2          equ     2
O_FLOOR         equ     3
O_EXIT          equ     4
O_DOORL         equ     5
O_DOORR         equ     6
O_GATE          equ     7
O_LEVL          equ     8
O_LEVR          equ     9
O_SPKA          equ     10
O_SPKB          equ     11
O_FLAME         equ     12
O_EN0           equ     13
O_EN1           equ     14
O_ARROW         equ     15
O_HERO          equ     16
O_HUD           equ     17
NOBJ            equ     18              ; STOP sits at index NOBJ

OB_DATA         equ     0               ; long: DRAM address of pixels
OB_X            equ     4               ; screen px 0..319 (XPOS = x+177)
OB_Y            equ     6               ; halflines (YPOS)
OB_H            equ     8               ; lines; 0 = hidden
OB_W            equ     10              ; phrases per line (IWIDTH=DWIDTH)
OB_FL           equ     12              ; PH1 high-word flags ($8000 TRANS)

TRANS           equ     $8000
XORG            equ     0               ; XPOS of screen px 0: line-buffer pixel 0 is the
                                        ; left edge (Tech Ref p.18; confirmed in VJ). Gate 6
                                        ; used 177 (=HDB1), which put half the castle off-screen.

; ---- geometry (screen px, halflines) -----------------------
FLOOR_HL        equ     420             ; floor surface (Gate 6 F1)
GROUND_Y        equ     372             ; hero top when standing (Bob: F1_YPOS)
HERO_HMAX       equ     304             ; 320-16
WALK            equ     2               ; Bob: XPOS_SPEED
JUMP_VEL        equ     -16             ; Gate 6 was -14; -16 clears 24px spikes
GRAVITY         equ     2               ; Bob: GRAVITY
CLIMB_V         equ     4
FLIP_TOP        equ     16
FLIP_BOT        equ     440
FLIP_DY         equ     420
LAD_L           equ     6
LAD_C           equ     152
LAD_R           equ     298
DOOR_LX         equ     94
DOOR_RX         equ     218
DOOR_LT         equ     75              ; "tight" door positions
DOOR_RT         equ     237
LEVER_LX        equ     80
LEVER_RX        equ     232
EXIT_RX         equ     277
EXIT_LX         equ     11
REACH           equ     14              ; ACT radius, centre to centre (orig 46px)
GRAB            equ     9               ; ladder grab radius

; ---- timings (frames @60Hz) ---------------------------------
DEATH_FRAMES    equ     90
WIN_FRAMES      equ     180             ; Bob: WIN_FRAMES
WHISPER_FRAMES  equ     48
ERUPT_WARN      equ     33
ERUPT_LIVE      equ     96
ARCHER_CD       equ     144
ALARM_FRAMES    equ     240

; ---- enemy types --------------------------------------------
T_SKULL         equ     0               ; Sentinel Skull: patrol baseline (Bob's skull)
T_GUARD         equ     1               ; Fallen Guard
T_HEAVY         equ     2               ; Fallen Guard, armoured (two shoves)
T_WATCHER       equ     3               ; Stone Watcher: static archer
T_WRAITH        equ     4               ; Judgment Wraith: F5 pursuer

; ---- memory categories --------------------------------------
C_GUARD         equ     0
C_DOOR          equ     1
C_LEVER         equ     2
C_PACE          equ     3
C_TRAP          equ     4

; ---- pad bits (active high in PAD) ---------------------------
P_LEFT          equ     0
P_RIGHT         equ     1
P_UP            equ     2
P_DOWN          equ     3
P_A             equ     4

; ---- state block offsets (a5) --------------------------------
PAD             equ     0
PADPREV         equ     2
PADNEW          equ     4
HX              equ     6
HY              equ     8
HVY             equ     10
CLIMB           equ     12              ; 0 / 1 up-ladder / 2 ladder hole
FLOOR           equ     14              ; 0..4
FACING          equ     16
GSTATE          equ     20              ; 0 play, 1 dying, 2 escaped
GTIMER          equ     22
BGVAL           equ     24
WHISPER         equ     26
RUNT            equ     28              ; long, frames this run
IDLE            equ     32              ; long, idle frames this run
CAUSE           equ     36
SEEN            equ     38              ; floors visited this run (bits)
NOTES           equ     40              ; floors the castle adapted (bits)
HUDDIRTY        equ     42
R_BASE          equ     44              ; run counters (10 words)
M_BASE          equ     64              ; memory counters, x100 (10 words)
CTR_DOORL       equ     0
CTR_DOORR       equ     2
CTR_LEVL        equ     4
CTR_LEVR        equ     6
CTR_PULLS       equ     8
CTR_RUSH        equ     10
CTR_WAIT        equ     12
CTR_CONF        equ     14
CTR_AVOID       equ     16
CTR_TRAPS       equ     18
NCTR            equ     10
P_BASE          equ     84              ; pressure per category 0..3
RUNS            equ     94
WINS            equ     96
DEATHS          equ     98              ; Bob's DEATH_COUNT, now persistent
T_DOOR          equ     100
T_LEVER         equ     102
T_RUSH          equ     104
T_WAIT          equ     106
T_BRACE         equ     108
T_WATCH         equ     110
T_TRAP          equ     112
SIDE_DOOR       equ     114             ; -1 left, +1 right, 0 none
SIDE_LEVER      equ     116
EXIT_X          equ     118
SIDE_BIAS       equ     120             ; Bob's Gate 5 signal, per run
AUTOCLOSE       equ     122
SPIKE_ON        equ     124
STUN_T          equ     126
DOORS           equ     128             ; 4 x 8: F1L F1R F3L F3R
D_X             equ     0
D_OPEN          equ     2
D_LOCK          equ     4
D_PASSED        equ     6
LEVERS          equ     160             ; 4 x 4: F2L F2R F4L F4R
LV_EFF          equ     0               ; 0 open 1 dud 2 trap 3 alarm
LV_STATE        equ     2               ; 0 idle 1 pulled 2 sprung
GATES           equ     176             ; 2 x 4: F2 F4
G_OPEN          equ     0
G_T             equ     2
FSPIKE          equ     184             ; 5 floors x 2 x 8
SP_X            equ     0
SP_W            equ     2               ; 0 none, 16 or 24 px
SP_PER          equ     4               ; 0 static, else retract period
SP_ORG          equ     6
FENEMY          equ     264             ; 5 floors x 2 x 32 (plan)
ENEMY           equ     584             ; 2 x 32 (current floor, live)
E_TYPE          equ     0               ; -1 none
E_X             equ     2               ; plan: px; live: px*16
E_DIR           equ     4
E_MIN           equ     6
E_MAX           equ     8
E_SPD           equ     10              ; 1/16 px per frame
E_ARM           equ     12
E_ORG           equ     14              ; memory category of a kill
E_CHASE         equ     16
E_STUN          equ     18
E_ALARM         equ     20
E_CNT           equ     22              ; confronted/avoided counted
E_SIDE          equ     24
E_SHOOT         equ     26
AX              equ     648             ; arrow, px*16
ADIR            equ     650
AON             equ     652
EX              equ     654             ; eruption left px
ET              equ     656             ; eruption timer
STATE_SIZE      equ     660


; ============================================================
        .text

start:
        ; ---- proven startup (verbatim from Gate 6) ----------
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

        ; ---- clear state, HUD; copy art ----------------------
        lea     STATE,a5
        move.l  a5,a0
        move.w  #STATE_SIZE/4,d0
.clr:   clr.l   (a0)+
        dbra    d0,.clr

        lea     pix_start,a1
        lea     PIXBASE,a0
        move.w  #(pix_end-pix_start)/4-1,d0
.art:   move.l  (a1)+,(a0)+
        dbra    d0,.art

        bsr     init_objects
        bsr     build_plan
        bsr     new_run
        bsr     set_objects
        bsr     build_list
        bsr     copy_list
        bsr     draw_hud

        ; ---- OLP (proven word-swap) --------------------------
        move.l  #LIVE,d0
        swap    d0
        move.l  d0,OLP

        ; ---- video timing (verbatim) -------------------------
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
;   blank:   copy SHADOW -> LIVE (refreshes every header), write BG
;   then:    run one frame of game logic and build the next SHADOW
;            (may run on into the active picture; it only touches SHADOW)
; ============================================================
main:
.wait_blank:
        move.w  VC,d0
        and.w   #$07FF,d0               ; drop the field bit (VC bit 11 is set on
        cmp.w   #VC_VDE,d0              ; alternate fields in VJ; Gate 6 compared
        blt.s   .wait_blank             ; it raw and refreshed every 2nd frame)
        bsr     copy_list
        move.w  BGVAL(a5),BG

        bsr     game_frame
        bsr     set_objects
        bsr     build_list
        tst.w   HUDDIRTY(a5)
        beq.s   .wait_new
        bsr     draw_hud
.wait_new:
        move.w  VC,d0
        and.w   #$07FF,d0
        cmp.w   #VC_VDE,d0
        bge.s   .wait_new
        bra     main

; ============================================================
; copy_list — SHADOW -> LIVE, NOBJ headers (STOP is static)
; ============================================================
copy_list:
        lea     SHADOW,a0
        lea     LIVE,a1
        moveq   #NOBJ-1,d0
.qc:     move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        dbra    d0,.qc
        rts

; ============================================================
; build_list — object records -> BITMAP headers in SHADOW
;   PH0_HI = DATA<<8 | LINK>>11        (DATA, LINK phrase-aligned)
;   PH0_LO = (LINK&$7F8)<<21 | H<<14 | Y<<3
;   PH1_HI = W>>4 | flags
;   PH1_LO = (W&$F)<<28 | W<<18 | $C000 (PITCH 1, DEPTH 4) | XPOS
; ============================================================
build_list:
        lea     OBJS,a0
        lea     SHADOW,a1
        move.l  #LIVE+16,d6             ; LINK of object 0
        moveq   #NOBJ-1,d7
.obj:
        move.l  OB_DATA(a0),d0
        lsl.l   #8,d0
        move.l  d6,d1
        moveq   #11,d2
        lsr.l   d2,d1
        or.l    d1,d0
        move.l  d0,(a1)+                ; PH0_HI

        move.l  d6,d1
        and.l   #$7F8,d1
        moveq   #21,d2
        lsl.l   d2,d1
        moveq   #0,d0
        move.w  OB_H(a0),d0
        moveq   #14,d2
        lsl.l   d2,d0
        or.l    d0,d1
        moveq   #0,d0
        move.w  OB_Y(a0),d0
        lsl.l   #3,d0
        or.l    d0,d1
        move.l  d1,(a1)+                ; PH0_LO

        moveq   #0,d0
        move.w  OB_W(a0),d0
        move.w  d0,d3
        lsr.w   #4,d0
        or.w    OB_FL(a0),d0
        move.l  d0,(a1)+                ; PH1_HI

        moveq   #0,d1
        move.w  d3,d1
        moveq   #18,d2
        lsl.l   d2,d1
        moveq   #$F,d0
        and.w   d3,d0
        ror.l   #4,d0
        or.l    d0,d1
        or.l    #$C000,d1
        move.w  OB_X(a0),d0
        add.w   #XORG,d0
        and.w   #$0FFF,d0
        or.w    d0,d1
        move.l  d1,(a1)+                ; PH1_LO

        add.l   #16,d6
        lea     16(a0),a0
        dbra    d7,.obj
        rts

; ============================================================
; init_objects — clear records, set static widths/flags, STOP
; ============================================================
init_objects:
        lea     OBJS,a0
        moveq   #NOBJ*4-1,d0
.qc:     clr.l   (a0)+
        dbra    d0,.qc
        lea     OBJS,a0
        moveq   #NOBJ-1,d0
.qt:     move.w  #TRANS,OB_FL(a0)
        lea     16(a0),a0
        dbra    d0,.qt
        clr.w   OBJS+(O_FLOOR*16)+OB_FL   ; floor slab is opaque (as Gate 6)

        lea     LIVE+(NOBJ*16),a0
        bsr.s   .stop
        lea     SHADOW+(NOBJ*16),a0
.stop:  clr.l   (a0)+
        move.l  #4,(a0)+                ; STOP: TYPE=4 in low longword
        clr.l   (a0)+
        clr.l   (a0)+
        rts

; ============================================================
; read_pad — row 0 of pad 1: D-pad on J8-J11, A on B1 (active low)
; ============================================================
read_pad:
        move.w  #JOY_ROW0,JOYSTICK
        move.w  JOYSTICK,d0
        move.w  JOYBUTS,d1
        moveq   #0,d2
        btst    #10,d0
        bne.s   .q1
        bset    #P_LEFT,d2
.q1:     btst    #11,d0
        bne.s   .q2
        bset    #P_RIGHT,d2
.q2:     btst    #8,d0
        bne.s   .q3
        bset    #P_UP,d2
.q3:     btst    #9,d0
        bne.s   .q4
        bset    #P_DOWN,d2
.q4:     btst    #1,d1
        bne.s   .q5
        bset    #P_A,d2
.q5:     move.w  PAD(a5),d3
        move.w  d3,PADPREV(a5)
        move.w  d2,PAD(a5)
        not.w   d3
        and.w   d2,d3
        move.w  d3,PADNEW(a5)
        rts

; ============================================================
; game_frame
; ============================================================
game_frame:
        bsr     read_pad
        move.w  GSTATE(a5),d0
        beq     play_frame
        subq.w  #1,GTIMER(a5)
        move.w  GTIMER(a5),d1
        cmp.w   #1,d0
        bne.s   .win
        btst    #3,d1                   ; dying: slow red pulse
        beq.s   .dk
        move.w  #BG_DEATH,BGVAL(a5)
        bra.s   .dt
.dk:    clr.w   BGVAL(a5)
.dt:    tst.w   d1
        bne.s   .out
        moveq   #0,d0
        bra.s   .end
.win:   btst    #2,d1                   ; escaped: gold pulse
        beq.s   .wk
        move.w  #BG_WIN,BGVAL(a5)
        bra.s   .wt
.wk:    clr.w   BGVAL(a5)
.wt:    tst.w   d1
        bne.s   .out
        moveq   #1,d0
.end:   bsr     end_run
        bsr     build_plan
        bsr     new_run
.out:   rts

play_frame:
        addq.l  #1,RUNT(a5)
        ; Bob's Gate 5 side bias (left/right half of the screen)
        cmp.w   #160-8,HX(a5)
        bge.s   .br
        cmp.w   #-30000,SIDE_BIAS(a5)
        ble.s   .bd
        subq.w  #1,SIDE_BIAS(a5)
        bra.s   .bd
.br:    cmp.w   #30000,SIDE_BIAS(a5)
        bge.s   .bd
        addq.w  #1,SIDE_BIAS(a5)
.bd:
        bsr     hero_update
        bsr     gate_update
        bsr     enemies_update
        bsr     arrow_update
        bsr     hazards_update
        bsr     exit_check

        clr.w   BGVAL(a5)
        move.w  WHISPER(a5),d0
        beq.s   .nw
        subq.w  #1,WHISPER(a5)
        and.w   #8,d0
        beq.s   .nw
        move.w  #BG_WHISPER,BGVAL(a5)
.nw:    rts

; kill — d0 = memory category of the cause
kill:
        tst.w   GSTATE(a5)
        bne.s   .qk
        move.w  d0,CAUSE(a5)
        move.w  #1,GSTATE(a5)
        move.w  #DEATH_FRAMES,GTIMER(a5)
        clr.w   CLIMB(a5)
.qk:     rts

; ============================================================
; HERO
; ============================================================
hero_update:
        tst.w   CLIMB(a5)
        bne     climb_update

        moveq   #0,d4                   ; d4 = active this frame
        ; ---- mount a ladder (grounded only) -----------------
        cmp.w   #GROUND_Y,HY(a5)
        bne.s   .nomount
        tst.w   HVY(a5)
        bne.s   .nomount
        btst    #P_UP,PAD+1(a5)
        beq.s   .tdown
        moveq   #1,d0
        bsr     find_ladder
        tst.w   d1
        bmi.s   .nomount
        bsr     gate_blocks
        tst.w   d0
        bne.s   .nomount
        moveq   #1,d0
        bra     start_climb
.tdown: btst    #P_DOWN,PADNEW+1(a5)
        beq.s   .nomount
        moveq   #2,d0
        bsr     find_ladder
        tst.w   d1
        bmi.s   .nomount
        moveq   #2,d0
        bra     start_climb
.nomount:
        ; ---- ACT (A, or X when not at a ladder hole) ----------
        move.w  PADNEW(a5),d0
        and.w   #(1<<P_A)|(1<<P_DOWN),d0
        beq.s   .noact
        bsr     do_act
.noact:
        ; ---- walk ---------------------------------------------
        move.w  HX(a5),d3               ; old x
        move.w  d3,d1
        btst    #P_LEFT,PAD+1(a5)
        beq.s   .nl
        subq.w  #WALK,d1
        move.w  #-1,FACING(a5)
        moveq   #1,d4
.nl:    btst    #P_RIGHT,PAD+1(a5)
        beq.s   .nr
        addq.w  #WALK,d1
        move.w  #1,FACING(a5)
        moveq   #1,d4
.nr:    tst.w   d1
        bpl.s   .c1
        moveq   #0,d1
.c1:    cmp.w   #HERO_HMAX,d1
        ble.s   .c2
        move.w  #HERO_HMAX,d1
.c2:    bsr     doors_clamp
        move.w  d1,HX(a5)

        ; ---- jump (Bob: S held while grounded) --------------
        btst    #P_UP,PAD+1(a5)
        beq.s   .phys
        cmp.w   #GROUND_Y,HY(a5)
        bne.s   .phys
        tst.w   HVY(a5)
        bne.s   .phys
        move.w  #JUMP_VEL,HVY(a5)
.phys:
        move.w  HVY(a5),d0
        addq.w  #GRAVITY,d0
        move.w  HY(a5),d1
        add.w   d0,d1
        cmp.w   #GROUND_Y,d1
        blt.s   .air
        move.w  #GROUND_Y,d1
        moveq   #0,d0
        bra.s   .land
.air:   moveq   #1,d4
.land:  move.w  d0,HVY(a5)
        move.w  d1,HY(a5)
idle_acct:
        tst.w   d4
        bne.s   .qa
        addq.l  #1,IDLE(a5)
.qa:     rts

; d0 = 1 up-ladder / 2 ladder hole, d1 = ladder x
start_climb:
        move.w  d0,CLIMB(a5)
        move.w  d1,HX(a5)
        clr.w   HVY(a5)
        rts

climb_update:
        moveq   #0,d4
        move.w  HY(a5),d0
        btst    #P_UP,PAD+1(a5)
        beq.s   .nu
        subq.w  #CLIMB_V,d0
        moveq   #1,d4
.nu:    btst    #P_DOWN,PAD+1(a5)
        beq.s   .nd
        addq.w  #CLIMB_V,d0
        moveq   #1,d4
.nd:    cmp.w   #1,CLIMB(a5)
        bne.s   .hole
        ; on an up-ladder: floor below, next floor above
        cmp.w   #GROUND_Y,d0
        blt.s   .uptop
        move.w  #GROUND_Y,d0            ; back at the floor
        btst    #P_UP,PAD+1(a5)
        bne.s   .store
        clr.w   CLIMB(a5)               ; dismount
        bra.s   .store
.uptop: cmp.w   #FLIP_TOP,d0
        bge.s   .store
        add.w   #FLIP_DY,d0             ; through the ceiling: next floor up
        move.w  d0,HY(a5)
        move.w  #2,CLIMB(a5)
        move.w  FLOOR(a5),d0
        addq.w  #1,d0
        bsr     enter_floor
        bra     idle_acct
.hole:  ; in a ladder hole below the floor
        cmp.w   #GROUND_Y,d0
        bgt.s   .holebot
        move.w  #GROUND_Y,d0
        btst    #P_DOWN,PAD+1(a5)
        bne.s   .store
        clr.w   CLIMB(a5)
        bra.s   .store
.holebot:
        cmp.w   #FLIP_BOT,d0
        ble.s   .store
        sub.w   #FLIP_DY,d0             ; down through the floor: floor below
        move.w  d0,HY(a5)
        move.w  #1,CLIMB(a5)
        move.w  FLOOR(a5),d0
        subq.w  #1,d0
        bsr     enter_floor
        bra     idle_acct
.store: move.w  d0,HY(a5)
        bra     idle_acct

; find_ladder — d0 = kind (1 up, 2 hole); out d1 = ladder x or -1
find_ladder:
        lea     ladtab,a0
        move.w  FLOOR(a5),d1
        mulu    #12,d1
        add.w   d1,a0
        move.w  HX(a5),d3
        moveq   #2,d2
.ql:     move.w  (a0)+,d1
        cmp.w   (a0)+,d0
        bne.s   .qn
        move.w  d3,d5
        sub.w   d1,d5
        bpl.s   .qp
        neg.w   d5
.qp:     cmp.w   #GRAB,d5
        ble.s   .qf
.qn:     dbra    d2,.ql
        moveq   #-1,d1
.qf:     rts

; gate_blocks — d1 = ladder x; d0 = 1 if a shut gate blocks it
gate_blocks:
        moveq   #0,d0
        cmp.w   #LAD_C,d1
        bne.s   .qo
        bsr     gate_ptr
        tst.l   d2
        beq.s   .qo
        tst.w   G_OPEN(a1)
        bne.s   .qo
        moveq   #1,d0
.qo:     rts

; gate_ptr — a1 = this floor's gate, d2 = 0 if the floor has none
gate_ptr:
        lea     GATES(a5),a1
        moveq   #1,d2
        cmp.w   #1,FLOOR(a5)
        beq.s   .qy
        addq.l  #4,a1
        cmp.w   #3,FLOOR(a5)
        beq.s   .qy
        moveq   #0,d2
.qy:     rts

; doors_clamp — d3 old x, d1 new x (in/out). Closed doors are walls;
;   crossing an open door's centre counts the door as taken (once).
doors_clamp:
        lea     DOORS(a5),a0
        move.w  FLOOR(a5),d0
        beq.s   .qf
        cmp.w   #2,d0
        bne     .qr
        lea     16(a0),a0
.qf:     moveq   #0,d7                   ; 0 = left door, 1 = right door
.loop:  move.w  D_X(a0),d2
        tst.w   D_OPEN(a0)
        bne.s   .open
        move.w  d3,d5                   ; from the left?
        add.w   #16,d5
        cmp.w   d2,d5
        bgt.s   .fromr
        move.w  d1,d5
        add.w   #16,d5
        cmp.w   d2,d5
        ble.s   .next
        move.w  d2,d1
        sub.w   #16,d1
        bra.s   .next
.fromr: move.w  d2,d5
        addq.w  #8,d5
        cmp.w   d5,d3
        blt.s   .next
        cmp.w   d5,d1
        bge.s   .next
        move.w  d5,d1
        bra.s   .next
.open:  tst.w   D_PASSED(a0)
        bne.s   .next
        move.w  d3,d5
        addq.w  #4,d5
        cmp.w   d2,d5
        slt     d6
        move.w  d1,d5
        addq.w  #4,d5
        cmp.w   d2,d5
        slt     d5
        cmp.b   d5,d6
        beq.s   .next
        move.w  #1,D_PASSED(a0)
        tst.w   d7
        bne.s   .cr
        addq.w  #1,R_BASE+CTR_DOORL(a5)
        bra.s   .next
.cr:    addq.w  #1,R_BASE+CTR_DOORR(a5)
.next:  lea     8(a0),a0
        addq.w  #1,d7
        cmp.w   #2,d7
        blt.s   .loop
.qr:     rts

; ============================================================
; ACT: shove a guard ahead > pull a lever > open a door
; ============================================================
do_act:
        cmp.w   #GROUND_Y-56,HY(a5)
        blt.s   .lev
        lea     ENEMY(a5),a0
        moveq   #1,d7
.sh:    tst.w   E_TYPE(a0)
        bmi.s   .shn
        tst.w   E_STUN(a0)
        bne.s   .shn
        move.w  E_X(a0),d0
        asr.w   #4,d0
        sub.w   HX(a5),d0               ; enemy - hero
        muls    FACING(a5),d0
        cmp.w   #-3,d0
        ble.s   .shn
        cmp.w   #28,d0
        bge.s   .shn
        bra     shove
.shn:   lea     32(a0),a0
        dbra    d7,.sh
.lev:   ; levers (F2, F4)
        lea     LEVERS(a5),a0
        move.w  FLOOR(a5),d0
        cmp.w   #1,d0
        beq.s   .lf
        cmp.w   #3,d0
        bne.s   .door
        addq.l  #8,a0
.lf:    move.w  #LEVER_LX+4,d1
        bsr     near_hero
        bne.s   .tryr
        moveq   #0,d6
        bra     pull_lever
.tryr:  addq.l  #4,a0
        move.w  #LEVER_RX+4,d1
        bsr     near_hero
        bne.s   .done
        moveq   #1,d6
        bra     pull_lever
.door:  ; doors (F1, F3)
        lea     DOORS(a5),a0
        tst.w   d0
        beq.s   .df
        cmp.w   #2,d0
        bne.s   .done
        lea     16(a0),a0
.df:    moveq   #1,d7
.dl:    move.w  D_X(a0),d1
        addq.w  #4,d1
        bsr     near_hero
        bne.s   .dn
        tst.w   D_OPEN(a0)
        bne.s   .dn
        tst.w   D_LOCK(a0)
        bne.s   .bricked
        move.w  #1,D_OPEN(a0)
        rts
.bricked:
        move.w  #12,WHISPER(a5)         ; brief ember flash: "bricked up"
        rts
.dn:    lea     8(a0),a0
        dbra    d7,.dl
.done:  rts

; near_hero — d1 = object centre px; Z set if within REACH of hero centre
near_hero:
        move.w  HX(a5),d5
        addq.w  #8,d5
        sub.w   d1,d5
        bpl.s   .qp
        neg.w   d5
.qp:     cmp.w   #REACH,d5
        bgt.s   .no
        moveq   #0,d5                   ; Z=1
        rts
.no:    moveq   #1,d5                   ; Z=0
        rts

; shove — a0 = enemy
shove:
        moveq   #10,d1                  ; push px
        tst.w   E_ARM(a0)
        beq.s   .norm
        subq.w  #1,E_ARM(a0)
        move.w  #36,E_STUN(a0)
        moveq   #21,d1
        bra.s   .push
.norm:  move.w  STUN_T(a5),E_STUN(a0)
.push:  muls    FACING(a5),d1
        lsl.w   #4,d1
        add.w   E_X(a0),d1
        bsr     clamp_ex
        move.w  d1,E_X(a0)
        clr.w   E_ALARM(a0)
        clr.w   E_SHOOT(a0)
        tst.w   E_CNT(a0)
        bne.s   .qc
        move.w  #1,E_CNT(a0)
        addq.w  #1,R_BASE+CTR_CONF(a5)
.qc:     rts

; clamp_ex — clamp d1 (px*16) to enemy a0's [min,max]
clamp_ex:
        move.w  E_MIN(a0),d0
        lsl.w   #4,d0
        cmp.w   d0,d1
        bge.s   .q1
        move.w  d0,d1
.q1:     move.w  E_MAX(a0),d0
        lsl.w   #4,d0
        cmp.w   d0,d1
        ble.s   .q2
        move.w  d0,d1
.q2:     rts

; pull_lever — a0 = lever, d6 = 0 left / 1 right
pull_lever:
        cmp.w   #2,LV_STATE(a0)
        beq.s   .qr                      ; jammed
        bsr     gate_ptr
        tst.w   G_OPEN(a1)
        bne.s   .qr                      ; gate already open
        addq.w  #1,R_BASE+CTR_PULLS(a5)
        tst.w   d6
        bne.s   .rr
        addq.w  #1,R_BASE+CTR_LEVL(a5)
        bra.s   .eff
.rr:    addq.w  #1,R_BASE+CTR_LEVR(a5)
.eff:   move.w  LV_EFF(a0),d0
        beq.s   .open
        cmp.w   #3,d0
        beq.s   .alarm
        move.w  #2,LV_STATE(a0)         ; dud or trap: sprung for good
        cmp.w   #2,d0
        bne.s   .qr
        addq.w  #1,R_BASE+CTR_TRAPS(a5) ; trap: eruption at the lever
        move.w  #LEVER_LX+4-32,d1
        tst.w   d6
        beq.s   .ex
        move.w  #LEVER_RX+4-32,d1
.ex:    move.w  d1,EX(a5)
        move.w  #ERUPT_WARN+ERUPT_LIVE,ET(a5)
.qr:     rts
.alarm: move.l  a0,-(sp)                ; every guard on the floor wakes...
        lea     ENEMY(a5),a0
        moveq   #1,d7
.al:    move.w  #ALARM_FRAMES,E_ALARM(a0)
        bsr     enemy_touch
        tst.w   d0
        bne.s   .pin                    ; ...except one pinned under the hero
        cmp.w   #20,E_STUN(a0)          ; a stunned guard gets up startled: at most
        ble.s   .pin                    ; 1/3 s more, so there is time to react
        move.w  #20,E_STUN(a0)
.pin:   lea     32(a0),a0
        dbra    d7,.al
        move.l  (sp)+,a0
.open:  move.w  #1,LV_STATE(a0)
        move.w  #1,G_OPEN(a1)
        clr.w   G_T(a1)
        rts

; ============================================================
; gate auto-close (the castle will not wait)
; ============================================================
gate_update:
        bsr     gate_ptr
        tst.w   d2
        beq.s   .qr
        tst.w   G_OPEN(a1)
        beq.s   .qr
        move.w  AUTOCLOSE(a5),d0
        beq.s   .qr
        addq.w  #1,G_T(a1)
        cmp.w   G_T(a1),d0
        bgt.s   .qr
        tst.w   CLIMB(a5)               ; never shut on the climber
        beq.s   .shut
        cmp.w   #LAD_C,HX(a5)
        beq.s   .qr
.shut:  clr.w   G_OPEN(a1)
        clr.w   G_T(a1)
        lea     LEVERS(a5),a0
        cmp.w   #1,FLOOR(a5)
        beq.s   .lv
        addq.l  #8,a0
.lv:    cmp.w   #1,LV_STATE(a0)
        bne.s   .l2
        clr.w   LV_STATE(a0)
.l2:    cmp.w   #1,LV_STATE+4(a0)
        bne.s   .qr
        clr.w   LV_STATE+4(a0)
.qr:     rts

; ============================================================
; ENEMIES (current floor)
; ============================================================
enemies_update:
        lea     ENEMY(a5),a0
        moveq   #1,d7
.lp:    tst.w   E_TYPE(a0)
        bmi     .next
        tst.w   E_STUN(a0)
        beq.s   .awake
        subq.w  #1,E_STUN(a0)
        bne     .next
        bsr     enemy_touch             ; can't stand up inside the hero
        tst.w   d0
        beq     .next
        move.w  #12,E_STUN(a0)
        bra     .next
.awake: tst.w   E_ALARM(a0)
        beq.s   .na
        subq.w  #1,E_ALARM(a0)
.na:    move.w  E_X(a0),d1
        asr.w   #4,d1                   ; d1 = enemy px
        move.w  HX(a5),d2
        sub.w   d1,d2                   ; d2 = hero - enemy
        move.w  d2,d3
        bpl.s   .ab
        neg.w   d3                      ; d3 = |dx|
.ab:    cmp.w   #T_WATCHER,E_TYPE(a0)
        beq     .archer

        ; ---- chase? ---------------------------------------
        moveq   #0,d5
        tst.w   CLIMB(a5)
        bne.s   .move
        tst.w   E_ALARM(a0)
        beq.s   .ca
        cmp.w   #190,d3
        bge.s   .move
        moveq   #2,d5
        bra.s   .move
.ca:    tst.w   E_CHASE(a0)
        beq.s   .move
        cmp.w   #81,d3
        bge.s   .move
        moveq   #1,d5
.move:  move.w  E_SPD(a0),d0
        tst.w   d5
        beq.s   .patrol
        tst.w   d2                      ; face the hero
        beq.s   .sp
        moveq   #1,d6
        tst.w   d2
        bpl.s   .fd
        moveq   #-1,d6
.fd:    move.w  d6,E_DIR(a0)
.sp:    move.w  d0,d6
        lsr.w   #1,d6                   ; chase: x1.5
        cmp.w   #2,d5
        bne.s   .sp2
        move.w  d0,d6
        mulu    #5,d6
        lsr.w   #3,d6                   ; alarmed: x1.6
.sp2:   add.w   d6,d0
        muls    E_DIR(a0),d0
        add.w   E_X(a0),d0
        move.w  d0,d1
        bsr     clamp_ex
        move.w  d1,E_X(a0)
        bra.s   .after
.patrol:
        muls    E_DIR(a0),d0
        add.w   E_X(a0),d0
        move.w  E_MIN(a0),d1
        lsl.w   #4,d1
        cmp.w   d1,d0
        bgt.s   .pmax
        move.w  d1,d0
        move.w  #1,E_DIR(a0)
        bra.s   .pst
.pmax:  move.w  E_MAX(a0),d1
        lsl.w   #4,d1
        cmp.w   d1,d0
        blt.s   .pst
        move.w  d1,d0
        move.w  #-1,E_DIR(a0)
.pst:   move.w  d0,E_X(a0)
.after: bsr     avoid_track
        bsr     enemy_touch
        tst.w   d0
        beq.s   .next
        move.w  E_ORG(a0),d0
        bsr     kill
        bra.s   .next

.archer:
        moveq   #1,d6                   ; face the hero
        tst.w   d2
        bpl.s   .af
        moveq   #-1,d6
.af:    move.w  d6,E_DIR(a0)
        cmp.w   #1000,E_SHOOT(a0)
        bge.s   .acap
        addq.w  #1,E_SHOOT(a0)
.acap:  cmp.w   #ARCHER_CD,E_SHOOT(a0)
        blt.s   .atouch
        cmp.w   #219,d3                 ; alert range
        bge.s   .atouch
        tst.w   AON(a5)
        bne.s   .atouch
        clr.w   E_SHOOT(a0)
        move.w  #1,AON(a5)
        move.w  d6,ADIR(a5)
        move.w  d6,d0
        muls    #9,d0
        add.w   d1,d0
        addq.w  #4,d0                   ; centre(+8) - half arrow(4)
        lsl.w   #4,d0
        move.w  d0,AX(a5)
.atouch:
        bsr     avoid_track
        bsr     enemy_touch
        tst.w   d0
        beq.s   .next
        move.w  E_ORG(a0),d0
        bsr     kill
.next:  lea     32(a0),a0
        dbra    d7,.lp
        rts

; avoid_track — a0 = enemy. Slipping past an unshoved guard counts once.
avoid_track:
        tst.w   CLIMB(a5)
        bne.s   .qr
        move.w  E_X(a0),d0
        asr.w   #4,d0
        moveq   #1,d1
        cmp.w   HX(a5),d0
        ble.s   .qs
        moveq   #-1,d1
.qs:     move.w  E_SIDE(a0),d0
        move.w  d1,E_SIDE(a0)
        tst.w   d0
        beq.s   .qr
        cmp.w   d0,d1
        beq.s   .qr
        tst.w   E_CNT(a0)
        bne.s   .qr
        move.w  #1,E_CNT(a0)
        addq.w  #1,R_BASE+CTR_AVOID(a5)
.qr:     rts

; enemy_touch — a0 = enemy; d0 = 1 if it overlaps the hero
;   hero box x+4..x+12, y+8..y+48; enemy x+3..x+13, top..floor
enemy_touch:
        moveq   #0,d0
        move.w  E_X(a0),d1
        asr.w   #4,d1
        sub.w   HX(a5),d1
        bpl.s   .qp
        neg.w   d1
.qp:     cmp.w   #9,d1
        bge.s   .qr
        move.w  #FLOOR_HL-24,d1         ; skull: lower 12 rows hurt
        tst.w   E_TYPE(a0)
        beq.s   .qt
        move.w  #FLOOR_HL-36,d1         ; 24-row enemies: below the helmet
.qt:    sub.w   #48,d1
        cmp.w   HY(a5),d1
        bge.s   .qr
        cmp.w   #FLOOR_HL-8,HY(a5)      ; inside a ladder hole: out of reach
        bge.s   .qr
        moveq   #1,d0
.qr:    rts

; ============================================================
; ARROW
; ============================================================
arrow_update:
        tst.w   AON(a5)
        beq.s   .qr
        move.w  ADIR(a5),d0
        muls    #48,d0                  ; 3 px/frame
        add.w   AX(a5),d0
        move.w  d0,AX(a5)
        bmi.s   .off
        cmp.w   #312*16,d0
        bgt.s   .off
        tst.w   CLIMB(a5)
        bne.s   .qr
        asr.w   #4,d0
        sub.w   HX(a5),d0
        subq.w  #4,d0                   ; (ax+4) - (hx+8)
        bpl.s   .qp
        neg.w   d0
.qp:     cmp.w   #8,d0
        bge.s   .qr
        move.w  HY(a5),d0
        add.w   #48,d0
        cmp.w   #FLOOR_HL-24,d0         ; knee height: jump to dodge
        ble.s   .qr
        clr.w   AON(a5)
        moveq   #C_GUARD,d0
        bra     kill
.off:   clr.w   AON(a5)
.qr:     rts

; ============================================================
; SPIKES and ERUPTION
; ============================================================
hazards_update:
        lea     FSPIKE(a5),a0
        move.w  FLOOR(a5),d0
        lsl.w   #4,d0
        add.w   d0,a0
        moveq   #1,d7
.sl:    tst.w   SP_W(a0)
        beq.s   .sn
        bsr     spike_up
        tst.w   d0
        beq.s   .sn
        tst.w   CLIMB(a5)
        bne.s   .sn
        move.w  HY(a5),d0
        cmp.w   #FLOOR_HL-14-48,d0      ; feet within 14 halflines of the floor
        ble.s   .sn
        move.w  HX(a5),d0
        addq.w  #5,d0                   ; hero feet x+5..x+11 vs spike x+3..x+w-3
        move.w  SP_X(a0),d1
        add.w   SP_W(a0),d1
        subq.w  #3,d1
        cmp.w   d1,d0
        bge.s   .sn
        addq.w  #6,d0
        move.w  SP_X(a0),d1
        addq.w  #3,d1
        cmp.w   d1,d0
        ble.s   .sn
        addq.w  #1,R_BASE+CTR_TRAPS(a5)
        move.w  SP_ORG(a0),d0
        bra     kill
.sn:    lea     8(a0),a0
        dbra    d7,.sl

        ; ---- eruption from a trapped lever --------------------
        tst.w   ET(a5)
        beq.s   .qr
        subq.w  #1,ET(a5)
        cmp.w   #ERUPT_LIVE,ET(a5)
        bgt.s   .qr                      ; still the warning
        tst.w   CLIMB(a5)
        bne.s   .qr
        move.w  HY(a5),d0
        cmp.w   #FLOOR_HL-38-48,d0
        ble.s   .qr
        move.w  HX(a5),d0
        addq.w  #4,d0
        move.w  EX(a5),d1
        add.w   #64,d1
        cmp.w   d1,d0
        bge.s   .qr
        addq.w  #8,d0
        cmp.w   EX(a5),d0
        ble.s   .qr
        moveq   #C_LEVER,d0
        bra     kill
.qr:     rts

; spike_up — a0 = spike; d0 = 1 if raised now
spike_up:
        moveq   #1,d0
        move.w  SP_PER(a0),d1
        beq.s   .qr
        move.l  RUNT(a5),d0
        divu    d1,d0
        swap    d0                      ; remainder
        cmp.w   SPIKE_ON(a5),d0
        blt.s   .on
        moveq   #0,d0
        rts
.on:    moveq   #1,d0
.qr:     rts

; ============================================================
; EXIT
; ============================================================
exit_check:
        cmp.w   #4,FLOOR(a5)
        bne.s   .qr
        tst.w   CLIMB(a5)
        bne.s   .qr
        cmp.w   #GROUND_Y,HY(a5)
        bne.s   .qr
        move.w  HX(a5),d0
        sub.w   EXIT_X(a5),d0
        subq.w  #8,d0                   ; (hx+8) - (ex+16)
        bpl.s   .qp
        neg.w   d0
.qp:     cmp.w   #12,d0
        bge.s   .qr
        move.w  #2,GSTATE(a5)
        move.w  #WIN_FRAMES,GTIMER(a5)
.qr:     rts

; ============================================================
; RUNS
; ============================================================
new_run:
        lea     R_BASE(a5),a0
        moveq   #NCTR-1,d0
.qc:     clr.w   (a0)+
        dbra    d0,.qc
        clr.l   RUNT(a5)
        clr.l   IDLE(a5)
        clr.w   SEEN(a5)
        clr.w   CLIMB(a5)
        clr.w   HVY(a5)
        clr.w   GSTATE(a5)
        clr.w   SIDE_BIAS(a5)
        clr.w   WHISPER(a5)
        move.w  #LAD_C,HX(a5)
        move.w  #GROUND_Y,HY(a5)
        move.w  #1,FACING(a5)
        moveq   #0,d0
        bsr     enter_floor
        tst.w   RUNS(a5)
        beq.s   .qr
        tst.w   NOTES(a5)               ; rebuilt castle: it remembers
        beq.s   .qr
        move.w  #WHISPER_FRAMES,WHISPER(a5)
.qr:     rts

; enter_floor — d0 = floor 0..4. Wakes that floor's planned enemies.
enter_floor:
        move.w  d0,FLOOR(a5)
        clr.w   AON(a5)
        clr.w   ET(a5)
        move.w  #1,HUDDIRTY(a5)
        move.w  SEEN(a5),d1
        btst    d0,d1
        bne.s   .seen
        bset    d0,d1
        move.w  d1,SEEN(a5)
        move.w  NOTES(a5),d1
        btst    d0,d1
        beq.s   .seen
        tst.w   d0
        beq.s   .seen                   ; F1 whisper plays at run start
        move.w  #WHISPER_FRAMES,WHISPER(a5)
.seen:  lea     FENEMY(a5),a1
        lsl.w   #6,d0
        add.w   d0,a1
        lea     ENEMY(a5),a0
        moveq   #1,d7
.qe:     moveq   #15,d0                  ; copy the 32-byte plan slot
        move.l  a0,a2
        move.l  a1,a3
.cp:    move.w  (a3)+,(a2)+
        dbra    d0,.cp
        move.w  E_TYPE(a0),d0
        bmi.s   .qn
        move.w  E_X(a0),d1
        lsl.w   #4,d1
        move.w  d1,E_X(a0)
        add.w   d0,d0
        lea     speedtab,a2
        move.w  0(a2,d0.w),d1
        tst.w   E_TYPE(a0)
        bne.s   .ns
        move.w  DEATHS(a5),d2           ; Bob's Gate 5: skulls speed up per death
        cmp.w   #4,d2
        ble.s   .dc
        moveq   #4,d2
.dc:    add.w   d2,d2                   ; +2 per death, max +8
        add.w   d2,d1
.ns:    tst.w   T_RUSH(a5)
        beq.s   .nr
        mulu    #27,d1                  ; rush: guards x1.35
        divu    #20,d1
.nr:    move.w  d1,E_SPD(a0)
        clr.w   E_STUN(a0)
        clr.w   E_ALARM(a0)
        clr.w   E_CNT(a0)
        clr.w   E_SIDE(a0)
        move.w  #ARCHER_CD/2,E_SHOOT(a0)
.qn:     lea     32(a0),a0
        lea     32(a1),a1
        dbra    d7,.qe
        rts

; ============================================================
; end_run — d0 = 1 escaped / 0 died. Merge this run into memory.
; ============================================================
end_run:
        move.w  d0,d7
        ; ---- pace: rush if idle < 18% of the run ---------------
        move.l  IDLE(a5),d0
        move.l  RUNT(a5),d1
.fit:   cmp.l   #$FFFF,d1
        bls.s   .ok
        lsr.l   #1,d0
        lsr.l   #1,d1
        bra.s   .fit
.ok:    mulu    #100,d0
        mulu    #18,d1
        cmp.l   d1,d0
        bhs.s   .wait
        move.w  #1,R_BASE+CTR_RUSH(a5)
        bra.s   .merge
.wait:  move.w  #1,R_BASE+CTR_WAIT(a5)
.merge:
        moveq   #-1,d5                  ; category exempt from decay
        move.w  #100,d4                 ; weight x100
        tst.w   d7
        bne.s   .w2
        move.w  CAUSE(a5),d5
        bra.s   .mg
.w2:    move.w  #200,d4
.mg:    lea     R_BASE(a5),a0
        lea     M_BASE(a5),a1
        lea     ctrcat,a2
        moveq   #NCTR-1,d6
.ml:    moveq   #0,d0
        move.w  (a1),d0
        move.w  (a2)+,d1
        cmp.w   d5,d1
        beq.s   .nodecay
        mulu    #4,d0                   ; decay x0.8
        divu    #5,d0
        and.l   #$FFFF,d0
.nodecay:
        move.w  (a0)+,d1
        mulu    d4,d1
        add.l   d1,d0
        cmp.l   #60000,d0
        bls.s   .st
        move.l  #60000,d0
.st:    move.w  d0,(a1)+
        dbra    d6,.ml

        ; ---- pressure -----------------------------------------
        bsr     used_mask               ; d3 = used categories (bits)
        lea     P_BASE(a5),a0
        moveq   #0,d6
.pl:    move.w  (a0),d0
        tst.w   d7
        beq.s   .pdeath
        btst    d6,d3
        beq.s   .pn
        cmp.w   #3,d0
        bge.s   .pn
        addq.w  #1,d0
        bra.s   .pn
.pdeath:
        cmp.w   d5,d6
        bne.s   .pu
        tst.w   d0
        bne.s   .pn
        moveq   #1,d0
        bra.s   .pn
.pu:    btst    d6,d3
        bne.s   .pn
        tst.w   d0
        beq.s   .pn
        subq.w  #1,d0
.pn:    move.w  d0,(a0)+
        addq.w  #1,d6
        cmp.w   #5,d6
        blt.s   .pl

        addq.w  #1,RUNS(a5)
        tst.w   d7
        beq.s   .died
        addq.w  #1,WINS(a5)
        rts
.died:  addq.w  #1,DEATHS(a5)
        rts

; used_mask — d3 = categories this run used (pace always)
used_mask:
        moveq   #1<<C_PACE,d3
        move.w  R_BASE+CTR_CONF(a5),d0
        add.w   R_BASE+CTR_AVOID(a5),d0
        beq.s   .q1
        bset    #C_GUARD,d3
.q1:     move.w  R_BASE+CTR_DOORL(a5),d0
        add.w   R_BASE+CTR_DOORR(a5),d0
        beq.s   .q2
        bset    #C_DOOR,d3
.q2:     tst.w   R_BASE+CTR_PULLS(a5)
        beq.s   .q3
        bset    #C_LEVER,d3
.q3:     tst.w   R_BASE+CTR_TRAPS(a5)
        beq.s   .q4
        bset    #C_TRAP,d3
.q4:     rts

; favored — d0 = a (left), d1 = b (right), x100.
;   Out d0 = -1 left, +1 right, 0 no clear preference.
;   Needs a+b >= 0.9, |a-b| >= 0.9 and the larger >= 60% of the total.
favored:
        moveq   #0,d2
        move.w  d0,d2
        moveq   #0,d3
        move.w  d1,d3
        move.l  d2,d4
        add.l   d3,d4                   ; sum
        cmp.l   #90,d4
        blo.s   .none
        move.l  d2,d1
        sub.l   d3,d1
        bpl.s   .ab
        neg.l   d1
.ab:    cmp.l   #90,d1
        blo.s   .none
        moveq   #-1,d0
        move.l  d2,d1
        cmp.l   d3,d2
        bhs.s   .mx
        moveq   #1,d0
        move.l  d3,d1
.mx:    mulu    #10,d1
        move.l  d4,d2
        add.l   d2,d2
        move.l  d2,d3
        add.l   d2,d2
        add.l   d3,d2                   ; sum*6
        cmp.l   d2,d1
        bhs.s   .qr
.none:  moveq   #0,d0
.qr:     rts

; tier_of — d0 = category; out d0 = min(3, 1 + pressure)
tier_of:
        add.w   d0,d0
        move.w  P_BASE(a5,d0.w),d0
        addq.w  #1,d0
        cmp.w   #3,d0
        ble.s   .qr
        moveq   #3,d0
.qr:     rts

; ============================================================
; build_plan — rebuild the castle from memory (deterministic)
; ============================================================
build_plan:
        lea     FSPIKE(a5),a0
        move.w  #(80+320)/4-1,d0        ; FSPIKE and FENEMY are adjacent
.qc:     clr.l   (a0)+
        dbra    d0,.qc
        lea     FENEMY(a5),a0
        moveq   #9,d0
.qt:     move.w  #-1,E_TYPE(a0)
        lea     32(a0),a0
        dbra    d0,.qt
        lea     T_DOOR(a5),a0
        moveq   #8,d0                   ; tiers + both sides
.qz:     clr.w   (a0)+
        dbra    d0,.qz
        clr.w   NOTES(a5)

        lea     DOORS(a5),a0            ; doors closed
        moveq   #3,d0
.qd:     clr.l   (a0)+
        clr.l   (a0)+
        dbra    d0,.qd
        move.w  #DOOR_LX,DOORS+0+D_X(a5)
        move.w  #DOOR_RX,DOORS+8+D_X(a5)
        move.w  #DOOR_LX,DOORS+16+D_X(a5)
        move.w  #DOOR_RX,DOORS+24+D_X(a5)
        lea     LEVERS(a5),a0           ; levers all "open", gates shut
        moveq   #5,d0
.ql:     clr.l   (a0)+
        dbra    d0,.ql
        clr.w   AUTOCLOSE(a5)
        move.w  #60,SPIKE_ON(a5)
        move.w  #180,STUN_T(a5)
        move.w  #EXIT_RX,EXIT_X(a5)

        ; F3 corridors always have static spikes
        lea     FSPIKE+(2*16)(a5),a0
        move.w  #55,SP_X(a0)
        move.w  #16,SP_W(a0)
        move.w  #C_TRAP,SP_ORG(a0)
        move.w  #320-55-16,8+SP_X(a0)
        move.w  #16,8+SP_W(a0)
        move.w  #C_TRAP,8+SP_ORG(a0)

        tst.w   RUNS(a5)
        beq     place

        ; ---- what did the castle learn? -----------------------
        move.w  M_BASE+CTR_DOORL(a5),d0
        move.w  M_BASE+CTR_DOORR(a5),d1
        bsr     favored
        move.w  d0,SIDE_DOOR(a5)
        beq.s   .nd
        moveq   #C_DOOR,d0
        bsr     tier_of
        move.w  d0,T_DOOR(a5)
.nd:    move.w  M_BASE+CTR_LEVL(a5),d0
        move.w  M_BASE+CTR_LEVR(a5),d1
        bsr     favored
        move.w  d0,SIDE_LEVER(a5)
        beq.s   .nl
        moveq   #C_LEVER,d0
        bsr     tier_of
        move.w  d0,T_LEVER(a5)
.nl:    move.w  M_BASE+CTR_RUSH(a5),d1
        cmp.w   M_BASE+CTR_WAIT(a5),d1
        beq.s   .np
        moveq   #C_PACE,d0
        bsr     tier_of
        cmp.w   M_BASE+CTR_WAIT(a5),d1
        bls.s   .pw
        move.w  d0,T_RUSH(a5)
        bra.s   .np
.pw:    move.w  d0,T_WAIT(a5)
.np:    moveq   #0,d1
        move.w  M_BASE+CTR_CONF(a5),d1
        moveq   #0,d2
        move.w  M_BASE+CTR_AVOID(a5),d2
        sub.l   d2,d1                   ; confronted - avoided
        moveq   #C_GUARD,d0
        bsr     tier_of
        cmp.l   #90,d1
        blt.s   .nb
        move.w  d0,T_BRACE(a5)
        bra.s   .ng
.nb:    cmp.l   #-90,d1
        bgt.s   .ng
        move.w  d0,T_WATCH(a5)
.ng:    cmp.w   #150,M_BASE+CTR_TRAPS(a5)
        blo.s   .nt
        moveq   #C_TRAP,d0
        bsr     tier_of
        move.w  d0,T_TRAP(a5)
.nt:    ; escapes: the way out moves away from your favourite side
        tst.w   WINS(a5)
        beq.s   place
        cmp.w   #1,SIDE_DOOR(a5)
        bne.s   place
        move.w  #EXIT_LX,EXIT_X(a5)
        bset    #4,NOTES+1(a5)

place:
        ; ---- base guard type (watch -> chasers, brace 3 -> heavies)
        moveq   #T_SKULL,d6
        moveq   #0,d5                   ; d5 = chase flag for guards
        cmp.w   #3,T_BRACE(a5)
        blt.s   .b1
        moveq   #T_HEAVY,d6
.b1:    tst.w   T_WATCH(a5)
        beq.s   .b2
        moveq   #1,d5
        cmp.w   #T_HEAVY,d6
        beq.s   .b2
        moveq   #T_GUARD,d6
.b2:
        ; ---- G1, F2: patrol between the levers ----------------
        lea     FENEMY+(1*64)(a5),a0
        move.w  d6,d0
        move.w  #100,d3
        move.w  #204,d4
        cmp.w   #2,T_WATCH(a5)
        blt.s   .g1
        move.w  #28,d3
        move.w  #276,d4
.g1:    move.w  #123,d1
        moveq   #1,d2
        tst.w   RUNS(a5)
        beq.s   .g1s
        move.w  d3,d1                   ; Bob's Gate 5: comes from the side
        tst.w   SIDE_BIAS(a5)           ; you hid on last life
        bmi.s   .g1s
        move.w  d4,d1
        moveq   #-1,d2
.g1s:   moveq   #C_GUARD,d7
        bsr     set_enemy

        ; ---- G3, F4 ----------------------------------------
        lea     FENEMY+(3*64)(a5),a0
        move.w  d6,d0
        move.w  #47,d3
        move.w  #257,d4
        cmp.w   #2,T_WATCH(a5)
        blt.s   .g3
        move.w  #28,d3
        move.w  #276,d4
.g3:    move.w  #209,d1
        moveq   #-1,d2
        moveq   #C_GUARD,d7
        bsr     set_enemy

        ; ---- G4, F5: the Judgment Wraith ---------------------
        lea     FENEMY+(4*64)(a5),a0
        moveq   #T_WRAITH,d0
        moveq   #C_GUARD,d7
        cmp.w   #EXIT_RX,EXIT_X(a5)
        bne.s   .g4l
        move.w  #180,d3
        move.w  #261,d4
        cmp.w   #2,T_RUSH(a5)
        blt.s   .g4r
        move.w  #138,d3                 ; covers the ladder top
        moveq   #C_PACE,d7
.g4r:   move.w  d4,d1
        moveq   #-1,d2
        bra.s   .g4w
.g4l:   move.w  #42,d3
        move.w  #123,d4
        cmp.w   #2,T_RUSH(a5)
        blt.s   .g4lr
        move.w  #166,d4
        moveq   #C_PACE,d7
.g4lr:  move.w  d3,d1
        moveq   #1,d2
.g4w:   cmp.w   #3,T_WAIT(a5)
        blt.s   .g4s
        move.w  #28,d3                  ; waits get the whole floor
        move.w  #276,d4
        moveq   #C_PACE,d7
.g4s:   move.w  d5,-(sp)
        moveq   #1,d5                   ; the Wraith always pursues
        bsr     set_enemy
        move.w  (sp)+,d5
        cmp.w   #2,T_BRACE(a5)
        blt.s   .g4a
        move.w  #1,E_ARM(a0)
.g4a:   cmp.w   #C_PACE,d7
        bne.s   .doors
        bset    #4,NOTES+1(a5)

        ; ---- DOOR habit -------------------------------------
.doors: move.w  T_DOOR(a5),d0
        beq     .levers
        bset    #0,NOTES+1(a5)
        bset    #2,NOTES+1(a5)
        moveq   #0,d1                   ; d1 = favoured slot (0 L / 1 R)
        tst.w   SIDE_DOOR(a5)
        bmi.s   .ds
        moveq   #1,d1
.ds:    ; t>=1: F1 spikes in the favoured corridor (retracting)
        lea     FSPIKE+(0*16)(a5),a0
        move.w  #41,SP_X(a0)
        tst.w   d1
        beq.s   .ds1
        move.w  #263,SP_X(a0)
.ds1:   move.w  #16,SP_W(a0)
        move.w  #108,SP_PER(a0)
        move.w  #C_DOOR,SP_ORG(a0)
        ; t>=1: F3 other door starts open (a gift)
        lea     DOORS+16(a5),a0
        tst.w   d1
        bne.s   .dg
        lea     8(a0),a0
.dg:    move.w  #1,D_OPEN(a0)
        ; t 1..2: F3 guard in the favoured corridor
        cmp.w   #3,T_DOOR(a5)
        bge.s   .d3
        lea     FENEMY+(2*64)(a5),a0
        moveq   #T_GUARD,d0
        cmp.w   #3,T_BRACE(a5)
        blt.s   .dgt
        moveq   #T_HEAVY,d0
.dgt:   move.w  #33,d3
        move.w  #76,d4
        move.w  d4,d1
        moveq   #-1,d2
        tst.w   SIDE_DOOR(a5)
        bmi.s   .dgp
        move.w  #228,d3
        move.w  #271,d4
        move.w  d3,d1
        moveq   #1,d2
.dgp:   moveq   #C_DOOR,d7
        bsr     set_enemy
        ; t==2: F3 favoured spikes start retracting
        cmp.w   #2,T_DOOR(a5)
        bne.s   .d2
        lea     FSPIKE+(2*16)(a5),a0
        tst.w   SIDE_DOOR(a5)
        bmi.s   .dsp
        lea     8(a0),a0
.dsp:   move.w  #108,SP_PER(a0)
        move.w  #C_DOOR,SP_ORG(a0)
.d2:    cmp.w   #2,T_DOOR(a5)
        blt     .levers
.d3:    ; t>=2: favoured F1 door moves tight against the spikes
        tst.w   SIDE_DOOR(a5)
        bmi.s   .dtl
        move.w  #DOOR_RT,DOORS+8+D_X(a5)
        bra.s   .dt
.dtl:   move.w  #DOOR_LT,DOORS+0+D_X(a5)
.dt:    cmp.w   #3,T_DOOR(a5)
        blt.s   .levers
        ; t>=3: F1 corridor guard, F3 favoured door bricked up
        lea     FENEMY+(0*64)(a5),a0
        moveq   #T_GUARD,d0
        cmp.w   #3,T_BRACE(a5)
        blt.s   .dh
        moveq   #T_HEAVY,d0
.dh:    move.w  #23,d3
        move.w  #57,d4
        move.w  d3,d1
        moveq   #1,d2
        lea     DOORS+16(a5),a1
        tst.w   SIDE_DOOR(a5)
        bmi.s   .dhp
        move.w  #247,d3
        move.w  #280,d4
        move.w  d4,d1
        moveq   #-1,d2
        lea     8(a1),a1
.dhp:   move.w  #1,D_LOCK(a1)
        moveq   #C_DOOR,d7
        bsr     set_enemy

        ; ---- LEVER habit ------------------------------------
.levers:
        move.w  T_LEVER(a5),d0
        beq.s   .pace
        bset    #1,NOTES+1(a5)
        bset    #3,NOTES+1(a5)
        moveq   #0,d1                   ; byte offset of favoured lever
        moveq   #4,d2                   ; ... and of the other one
        tst.w   SIDE_LEVER(a5)
        bmi.s   .lp
        moveq   #4,d1
        moveq   #0,d2
.lp:    lea     LEVERS(a5),a0
        move.w  #2,8+LV_EFF(a0,d1.w)    ; t1: F4 favoured lever is a trap
        cmp.w   #2,d0
        blt.s   .pace
        move.w  #1,LV_EFF(a0,d1.w)      ; t2: F2 favoured lever is a dud
        cmp.w   #3,d0
        blt.s   .pace
        move.w  #2,LV_EFF(a0,d1.w)      ; t3: ...a trap instead,
        move.w  #3,8+LV_EFF(a0,d2.w)    ;     and F4's other lever raises the alarm

        ; ---- PACE habit -------------------------------------
.pace:  move.w  T_RUSH(a5),d0
        beq.s   .wait
        cmp.w   #2,d0
        blt     .guards
        bset    #2,NOTES+1(a5)
        lea     FENEMY+(2*64)+32(a5),a0   ; ambush at the top of the F2 ladder
        move.w  d6,d0
        cmp.w   #T_SKULL,d0
        bne.s   .pa
        moveq   #T_GUARD,d0
.pa:    move.w  #109,d3
        move.w  #195,d4
        move.w  d4,d1
        moveq   #-1,d2
        moveq   #C_PACE,d7
        bsr     set_enemy
        cmp.w   #3,T_RUSH(a5)
        blt     .guards
        bset    #1,NOTES+1(a5)
        lea     FSPIKE+(1*16)(a5),a0      ; spikes flank the F2 centre ladder
        move.w  #114,SP_X(a0)
        move.w  #190,8+SP_X(a0)
        moveq   #1,d0
.ps:    move.w  #16,SP_W(a0)
        move.w  #120,SP_PER(a0)
        move.w  #C_PACE,SP_ORG(a0)
        lea     8(a0),a0
        dbra    d0,.ps
        bra.s   .guards
.wait:  move.w  T_WAIT(a5),d0
        beq.s   .guards
        bset    #1,NOTES+1(a5)
        bset    #3,NOTES+1(a5)
        lea     closetab,a0
        add.w   d0,d0
        move.w  -2(a0,d0.w),AUTOCLOSE(a5)
        cmp.w   #4,d0
        blt     .guards
        move.w  #78,SPIKE_ON(a5)

        ; ---- GUARD habit ------------------------------------
.guards:
        move.w  T_BRACE(a5),d0
        beq.s   .watch
        move.w  #72,STUN_T(a5)          ; shoves stun for less
        bset    #4,NOTES+1(a5)
.watch: cmp.w   #3,T_WATCH(a5)
        blt.s   .traps
        bset    #3,NOTES+1(a5)
        lea     FENEMY+(3*64)+32(a5),a0   ; a Stone Watcher on F4
        moveq   #T_WATCHER,d0
        move.w  #52,d1
        move.w  d1,d3
        move.w  d1,d4
        moveq   #1,d2
        moveq   #C_GUARD,d7
        bsr     set_enemy

        ; ---- TRAP deaths ------------------------------------
.traps: move.w  T_TRAP(a5),d0
        beq.s   .esc
        bset    #2,NOTES+1(a5)
        move.w  #24,FSPIKE+(2*16)+SP_W(a5) ; F3 spikes widen
        move.w  #320-55-24,FSPIKE+(2*16)+8+SP_X(a5)
        move.w  #24,FSPIKE+(2*16)+8+SP_W(a5)
        cmp.w   #2,d0
        blt.s   .esc
        bset    #3,NOTES+1(a5)
        lea     FSPIKE+(3*16)(a5),a0
        move.w  #190,SP_X(a0)
        move.w  #16,SP_W(a0)
        move.w  #120,SP_PER(a0)
        move.w  #C_TRAP,SP_ORG(a0)
        cmp.w   #3,d0
        blt.s   .esc
        bset    #4,NOTES+1(a5)
        lea     FSPIKE+(4*16)(a5),a0      ; spikes beside the exit
        move.w  #255,SP_X(a0)
        cmp.w   #EXIT_RX,EXIT_X(a5)
        beq.s   .tx
        move.w  #46,SP_X(a0)
.tx:    move.w  #16,SP_W(a0)
        move.w  #120,SP_PER(a0)
        move.w  #C_TRAP,SP_ORG(a0)

        ; ---- ESCAPES: a Stone Watcher guards the exit -------------
.esc:   cmp.w   #2,WINS(a5)
        blt.s   .qr
        bset    #4,NOTES+1(a5)
        lea     FENEMY+(4*64)+32(a5),a0
        moveq   #T_WATCHER,d0
        move.w  #219,d1
        moveq   #1,d2
        cmp.w   #EXIT_RX,EXIT_X(a5)
        beq.s   .ew
        move.w  #85,d1
        moveq   #-1,d2
.ew:    move.w  d1,d3
        move.w  d1,d4
        moveq   #C_GUARD,d7
        bsr     set_enemy
.qr:     move.w  #1,HUDDIRTY(a5)
        rts

; set_enemy — a0 = plan slot; d0 type, d1 x, d2 dir, d3 min, d4 max,
;             d5 chase, d7 origin category
set_enemy:
        move.w  d0,E_TYPE(a0)
        move.w  d1,E_X(a0)
        move.w  d2,E_DIR(a0)
        move.w  d3,E_MIN(a0)
        move.w  d4,E_MAX(a0)
        move.w  d7,E_ORG(a0)
        move.w  d5,E_CHASE(a0)
        clr.w   E_ARM(a0)
        cmp.w   #T_HEAVY,d0
        bne.s   .qr
        move.w  #1,E_ARM(a0)
.qr:     rts

; ============================================================
; set_objects — what is on screen this frame
; ============================================================
set_objects:
        lea     OBJS,a4
        ; ---- ladders ------------------------------------------
        lea     ladtab,a0
        move.w  FLOOR(a5),d0
        mulu    #12,d0
        add.w   d0,a0
        move.l  a4,a1
        moveq   #2,d7
.lad:   move.w  (a0)+,OB_X(a1)
        move.w  (a0)+,d0
        move.l  #PIXBASE+(img_ladder-pix_start),OB_DATA(a1)
        move.w  #4,OB_W(a1)
        clr.w   OB_H(a1)
        cmp.w   #1,d0
        bne.s   .lh
        move.w  #20,OB_Y(a1)
        move.w  #200,OB_H(a1)
        bra.s   .ln
.lh:    cmp.w   #2,d0
        bne.s   .ln
        move.w  #FLOOR_HL+16,OB_Y(a1)
        move.w  #34,OB_H(a1)
.ln:    lea     16(a1),a1
        dbra    d7,.lad

        ; ---- floor slab (Bob's art) ---------------------------
        lea     O_FLOOR*16(a4),a1
        move.l  #PIXBASE+(img_floor-pix_start),OB_DATA(a1)
        clr.w   OB_X(a1)
        move.w  #FLOOR_HL,OB_Y(a1)
        move.w  #8,OB_H(a1)
        move.w  #80,OB_W(a1)

        ; ---- exit arch (F5) -----------------------------------
        lea     O_EXIT*16(a4),a1
        clr.w   OB_H(a1)
        cmp.w   #4,FLOOR(a5)
        bne.s   .nx
        move.l  #PIXBASE+(img_exit-pix_start),OB_DATA(a1)
        move.w  EXIT_X(a5),OB_X(a1)
        move.w  #FLOOR_HL-96,OB_Y(a1)
        move.w  #48,OB_H(a1)
        move.w  #8,OB_W(a1)
.nx:
        ; ---- doors (F1, F3) -----------------------------------
        lea     O_DOORL*16(a4),a1
        clr.w   OB_H(a1)
        clr.w   OB_H+16(a1)
        lea     DOORS(a5),a0
        move.w  FLOOR(a5),d0
        beq.s   .df
        cmp.w   #2,d0
        bne.s   .nd
        lea     16(a0),a0
.df:    moveq   #1,d7
.dl:    move.w  D_X(a0),OB_X(a1)
        move.w  #FLOOR_HL-80,OB_Y(a1)
        move.w  #40,OB_H(a1)
        move.w  #2,OB_W(a1)
        move.l  #PIXBASE+(img_door_closed-pix_start),d0
        tst.w   D_OPEN(a0)
        beq.s   .dc
        move.l  #PIXBASE+(img_door_open-pix_start),d0
.dc:    tst.w   D_LOCK(a0)
        beq.s   .dd
        move.l  #PIXBASE+(img_door_brick-pix_start),d0
.dd:    move.l  d0,OB_DATA(a1)
        lea     8(a0),a0
        lea     16(a1),a1
        dbra    d7,.dl
.nd:
        ; ---- gate + levers (F2, F4) -----------------------------
        bsr     gate_ptr
        move.l  a1,a2                   ; a2 = this floor's gate state
        lea     O_GATE*16(a4),a1
        clr.w   OB_H(a1)
        clr.w   OB_H+16(a1)
        clr.w   OB_H+32(a1)
        tst.w   d2
        beq     .ng
        move.l  #PIXBASE+(img_gate-pix_start),OB_DATA(a1)
        move.w  #LAD_C,OB_X(a1)
        move.w  #32,OB_H(a1)
        move.w  #4,OB_W(a1)
        move.w  #FLOOR_HL-64,d0
        tst.w   G_OPEN(a2)
        beq.s   .gs
        sub.w   #96,d0                  ; raised
.gs:    move.w  d0,OB_Y(a1)
        lea     LEVERS(a5),a0
        cmp.w   #1,FLOOR(a5)
        beq.s   .lv
        addq.l  #8,a0
.lv:    lea     16(a1),a1
        move.w  #LEVER_LX,d1
        moveq   #1,d7
.ll:    move.w  d1,OB_X(a1)
        move.w  #FLOOR_HL-24,OB_Y(a1)
        move.w  #12,OB_H(a1)
        move.w  #2,OB_W(a1)
        move.l  #PIXBASE+(img_lever_idle-pix_start),d0
        cmp.w   #2,LV_EFF(a0)
        bne.s   .lt
        move.l  #PIXBASE+(img_lever_tell-pix_start),d0  ; a trapped lever's knob looks wrong
.lt:    cmp.w   #1,LV_STATE(a0)
        bne.s   .ls
        move.l  #PIXBASE+(img_lever_pulled-pix_start),d0
.ls:    cmp.w   #2,LV_STATE(a0)
        bne.s   .lw
        move.l  #PIXBASE+(img_lever_sprung-pix_start),d0
.lw:    move.l  d0,OB_DATA(a1)
        lea     4(a0),a0
        lea     16(a1),a1
        move.w  #LEVER_RX,d1
        dbra    d7,.ll
.ng:
        ; ---- spikes -------------------------------------------
        lea     O_SPKA*16(a4),a1
        lea     FSPIKE(a5),a0
        move.w  FLOOR(a5),d0
        lsl.w   #4,d0
        add.w   d0,a0
        moveq   #1,d7
.sp:    clr.w   OB_H(a1)
        move.w  SP_W(a0),d2
        beq.s   .spn
        move.w  SP_X(a0),OB_X(a1)
        move.w  d2,d0
        lsr.w   #2,d0
        move.w  d0,OB_W(a1)
        move.l  #PIXBASE+(img_spike16-pix_start),d3
        cmp.w   #16,d2
        beq.s   .s16
        move.l  #PIXBASE+(img_spike24-pix_start),d3
.s16:   bsr     spike_up
        tst.w   d0
        beq.s   .sdown
        move.l  d3,OB_DATA(a1)
        move.w  #FLOOR_HL-16,OB_Y(a1)
        move.w  #8,OB_H(a1)
        bra.s   .spn
.sdown: mulu    #12,d2                  ; skip 6 rows: only the slots show
        add.l   d2,d3
        move.l  d3,OB_DATA(a1)
        move.w  #FLOOR_HL-4,OB_Y(a1)
        move.w  #2,OB_H(a1)
.spn:   lea     8(a0),a0
        lea     16(a1),a1
        dbra    d7,.sp

        ; ---- eruption -----------------------------------------
        lea     O_FLAME*16(a4),a1
        clr.w   OB_H(a1)
        move.w  ET(a5),d0
        beq.s   .nf
        move.w  EX(a5),OB_X(a1)
        move.w  #16,OB_W(a1)
        cmp.w   #ERUPT_LIVE,d0
        ble.s   .fl
        btst    #2,d0                   ; warning: flashing embers
        beq.s   .nf
        move.l  #PIXBASE+(img_flame-pix_start)+(14*128),OB_DATA(a1)
        move.w  #FLOOR_HL-4,OB_Y(a1)
        move.w  #2,OB_H(a1)
        bra.s   .nf
.fl:    move.l  #PIXBASE+(img_flame-pix_start),OB_DATA(a1)
        move.w  #FLOOR_HL-32,OB_Y(a1)
        move.w  #16,OB_H(a1)
.nf:
        ; ---- enemies ------------------------------------------
        lea     O_EN0*16(a4),a1
        lea     ENEMY(a5),a0
        moveq   #1,d7
.en:    clr.w   OB_H(a1)
        move.w  E_TYPE(a0),d0
        bmi.s   .enn
        move.w  E_STUN(a0),d1           ; stunned: flicker
        btst    #2,d1
        bne.s   .enn
        move.w  E_X(a0),d1
        asr.w   #4,d1
        move.w  d1,OB_X(a1)
        move.w  #4,OB_W(a1)
        lsl.w   #2,d0
        lea     enimg,a2
        move.l  0(a2,d0.w),OB_DATA(a1)
        move.w  #24,d1
        tst.w   E_TYPE(a0)
        bne.s   .e24
        moveq   #16,d1
.e24:   move.w  d1,OB_H(a1)
        add.w   d1,d1
        neg.w   d1
        add.w   #FLOOR_HL,d1
        move.w  d1,OB_Y(a1)
.enn:   lea     32(a0),a0
        lea     16(a1),a1
        dbra    d7,.en

        ; ---- arrow --------------------------------------------
        lea     O_ARROW*16(a4),a1
        clr.w   OB_H(a1)
        tst.w   AON(a5)
        beq.s   .na
        move.w  AX(a5),d0
        asr.w   #4,d0
        move.w  d0,OB_X(a1)
        move.w  #FLOOR_HL-20,OB_Y(a1)
        move.w  #2,OB_H(a1)
        move.w  #2,OB_W(a1)
        move.l  #PIXBASE+(img_arrow_r-pix_start),OB_DATA(a1)
        tst.w   ADIR(a5)
        bpl.s   .na
        move.l  #PIXBASE+(img_arrow_l-pix_start),OB_DATA(a1)
.na:
        ; ---- hero (Bob's sprite) -------------------------------
        lea     O_HERO*16(a4),a1
        move.l  #PIXBASE+(img_hero-pix_start),OB_DATA(a1)
        move.w  HX(a5),OB_X(a1)
        move.w  HY(a5),OB_Y(a1)
        move.w  #4,OB_W(a1)
        move.w  #24,OB_H(a1)
        cmp.w   #1,GSTATE(a5)
        bne.s   .hv
        btst    #2,GTIMER+1(a5)
        beq.s   .hv
        clr.w   OB_H(a1)
.hv:
        ; ---- HUD -----------------------------------------------
        lea     O_HUD*16(a4),a1
        move.l  #HUDBUF,OB_DATA(a1)
        clr.w   OB_X(a1)
        move.w  #40,OB_Y(a1)             ; VJ shows from about halfline 32
        move.w  #6,OB_H(a1)
        move.w  #80,OB_W(a1)
        rts

; ============================================================
; draw_hud — floor pips (left) and memory pips (right)
; ============================================================
draw_hud:
        clr.w   HUDDIRTY(a5)
        lea     HUDBUF,a0
        move.w  #320*6*2/4-1,d0
.qc:     clr.l   (a0)+
        dbra    d0,.qc
        ; floors: current gold, visited stone, unseen dark
        moveq   #0,d6
.qf:     move.w  #$671E,d2
        move.w  SEEN(a5),d0
        btst    d6,d0
        beq.s   .fc
        move.w  #$8883,d2
.fc:    cmp.w   FLOOR(a5),d6
        bne.s   .fd
        move.w  #$EAE7,d2
.fd:    move.w  d6,d0
        mulu    #10,d0
        addq.w  #4,d0
        moveq   #7,d1
        bsr     hud_rect
        addq.w  #1,d6
        cmp.w   #5,d6
        blt.s   .qf
        ; memory: five categories x three pips (tier)
        lea     hudcats,a3
        moveq   #0,d6
.qm:     move.w  (a3)+,d0                ; tier offset (or two, max taken)
        move.w  0(a5,d0.w),d4
        move.w  (a3)+,d0
        beq.s   .m1
        move.w  0(a5,d0.w),d1
        cmp.w   d1,d4
        bge.s   .m1
        move.w  d1,d4
.m1:    move.w  (a3)+,d3                ; category colour
        moveq   #0,d5
.mp:    move.w  #$671E,d2
        cmp.w   d4,d5
        bge.s   .mc
        move.w  d3,d2
.mc:    move.w  d6,d0
        mulu    #26,d0
        add.w   #186,d0
        move.w  d5,d1
        mulu    #8,d1
        add.w   d1,d0
        moveq   #6,d1
        bsr     hud_rect
        addq.w  #1,d5
        cmp.w   #3,d5
        blt.s   .mp
        addq.w  #1,d6
        cmp.w   #5,d6
        blt.s   .qm
        rts

; hud_rect — d0 = x, d1 = width, d2 = colour; rows 1..4
hud_rect:
        lea     HUDBUF+640,a0
        add.w   d0,d0
        add.w   d0,a0
        moveq   #3,d7
.qr:     move.l  a0,a1
        move.w  d1,d0
        subq.w  #1,d0
.qx:     move.w  d2,(a1)+
        dbra    d0,.qx
        lea     640(a0),a0
        dbra    d7,.qr
        rts

; ============================================================
; TABLES
; ============================================================
        .even
; ladders per floor: (x, kind) x3 — kind 1 up, 2 hole from below
ladtab:
        dc.w    LAD_L,1, LAD_R,1, 0,0           ; F1
        dc.w    LAD_C,1, LAD_L,2, LAD_R,2       ; F2
        dc.w    LAD_L,1, LAD_R,1, LAD_C,2       ; F3
        dc.w    LAD_C,1, LAD_L,2, LAD_R,2       ; F4
        dc.w    LAD_C,2, 0,0, 0,0               ; F5
; base speed per enemy type, 1/16 px per frame
; Ratios follow the original (guard 70 vs player 230 px/s, x1.25 patrol,
; x0.85 heavy); hero walks 32, so even a rushed, alarmed guard is slower.
speedtab:
        dc.w    12, 15, 10, 0, 16
; memory counter -> category (decay exemption on a death of that cause)
ctrcat:
        dc.w    C_DOOR,C_DOOR,C_LEVER,C_LEVER,C_LEVER
        dc.w    C_PACE,C_PACE,C_GUARD,C_GUARD,C_TRAP
; gate auto-close frames for wait tier 1..3 (5 / 3.5 / 2.5 s)
closetab:
        dc.w    300, 210, 150
; HUD: tier offset, second tier offset (0 = none), colour
hudcats:
        dc.w    T_DOOR,0,$F8FF                  ; doors  - orange
        dc.w    T_LEVER,0,$EAE7                 ; levers - gold
        dc.w    T_RUSH,T_WAIT,$2BDD             ; pace   - cyan
        dc.w    T_BRACE,T_WATCH,$E2DD           ; guards - red
        dc.w    T_TRAP,0,$53C9                  ; traps  - purple
enimg:
        dc.l    PIXBASE+(img_skull-pix_start), PIXBASE+(img_guard-pix_start), PIXBASE+(img_heavy-pix_start)
        dc.l    PIXBASE+(img_watcher-pix_start), PIXBASE+(img_wraith-pix_start)

; ============================================================
; ART (generated by tools/mkart.py)
; ============================================================
        .include "castle_art.inc"

        .end    start
