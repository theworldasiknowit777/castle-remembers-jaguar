; ============================================================
; hello.s  —  Minimal Jaguar test program
; Target: Atari Jaguar (68000 + Tom/Jerry)
; Assembler: RMAC 2.5.2   Linker: RLN 1.7.7
; Output: ABS/COF file loaded at $802000, run at $802000
;
; What it does:
;   1. Disables all interrupts and stops GPU/DSP
;   2. Sets up a STOP object in the Object Processor
;   3. Initialises NTSC/PAL video timing
;   4. Enables video with BGEN (background fill) mode
;   5. Sets the background colour to bright blue (CRY: $FF20)
;   6. Loops forever
;
; Visible result in emulator: solid blue screen
; ============================================================

; ---- Tom hardware registers ($F00000 base) -----------------
TOM             equ     $F00000
MEMCON1         equ     TOM+$00
OLP             equ     TOM+$20         ; Object List Pointer
OBF             equ     TOM+$26         ; Object Processor Flag
VMODE           equ     TOM+$28         ; Video Mode
BORD1           equ     TOM+$2A         ; Border colour R/G
BORD2           equ     TOM+$2C         ; Border colour B
HDB1            equ     TOM+$38         ; Horiz Display Begin 1
HDB2            equ     TOM+$3A         ; Horiz Display Begin 2
HDE             equ     TOM+$3C         ; Horiz Display End
VDB             equ     TOM+$46         ; Vert Display Begin
VDE             equ     TOM+$48         ; Vert Display End
VI              equ     TOM+$4E         ; Vertical Interrupt
BG              equ     TOM+$58         ; Background Colour
INT1            equ     TOM+$E0         ; CPU Interrupt Control
G_FLAGS         equ     TOM+$2100       ; GPU Flags
G_CTRL          equ     TOM+$2114       ; GPU Control/Status

; ---- Jerry registers ----------------------------------------
JERRY           equ     $F10000
D_FLAGS         equ     $F1A100         ; DSP Flags
D_CTRL          equ     $F1A114         ; DSP Control/Status
J_INT           equ     $F10020         ; Jerry Interrupt Control
CONFIG          equ     $F14002         ; Hardware config (NTSC/PAL bit)

; ---- NTSC video timing values (CJ values) -------------------
NTSC_WIDTH      equ     1229
NTSC_HMID       equ     787
NTSC_HEIGHT     equ     241
NTSC_VMID       equ     266

; ---- PAL video timing values --------------------------------
PAL_WIDTH       equ     1255
PAL_HMID        equ     821
PAL_HEIGHT      equ     287
PAL_VMID        equ     322

; ---- Video Mode flags ----------------------------------------
VIDEN           equ     $0001           ; Enable video timebase
CRY16           equ     $0000           ; 16-bit CRY pixel mode
BGEN            equ     $0080           ; Fill line buffer with BG colour
PWIDTH4         equ     $0600           ; 4 pixel-clocks per pixel

; ---- Object Processor: STOP object --------------------------
; A STOP object is a single 64-bit (2 longword) phrase.
; Format: bits[2:0] = 100 (type 4), bit 3 = interrupt enable = 0
; The rest can be zero for a simple "stop, no interrupt" object.
STOPOBJ_TYPE    equ     4               ; OP object type = STOP

        .text

; ============================================================
; Entry point — the linker places this at $802000 via -a flag
; ============================================================
start:
        ; --- 1. Disable all maskable interrupts on the 68k ---
        move.w  #$2700,sr               ; SR: supervisor, IPL=7

        ; --- 2. Stop GPU ---
        move.l  #0,G_FLAGS             ; disable GPU interrupts
        move.l  #0,G_CTRL              ; stop GPU

        ; --- 3. Stop DSP ---
        move.l  #$0001F800,D_FLAGS     ; clear DSP interrupt enables
        move.l  #0,D_CTRL              ; stop DSP

        ; --- 4. Disable CPU interrupt sources ---
        move.l  #$1F00<<16,INT1        ; clear all pending CPU IRQs

        ; --- 5. Disable Jerry interrupts ---
        move.w  #$3F00,J_INT           ; clear Jerry interrupt flags

        ; --- 6. Set up a STOP object at address $0 in DRAM ---
        ;   The Object List Pointer (OLP) points to this object.
        ;   STOP object phrase: lower 3 bits = 4 (STOP type)
        ;   We place it at DRAM word 0 ($000000).
        move.l  #STOPOBJ_TYPE,$000000  ; write STOP object lo-lword
        move.l  #0,$000004             ; write STOP object hi-lword
        move.l  #$000000,OLP           ; point OP at $000000

        ; --- 7. Clear the OP flag and border colour ----------
        move.w  #0,OBF
        move.l  #0,BORD1               ; border: black

        ; --- 8. Set stack pointer to top of DRAM ------------
        lea     $1FFFFC,sp

        ; --- 9. Detect NTSC/PAL and initialise video timing -
        ; CONFIG bit 4: 1=NTSC, 0=PAL
        btst    #4,CONFIG
        beq.s   do_pal

do_ntsc:
        ; HDB1/HDB2 — horizontal display begin
        move.w  #NTSC_HMID-(NTSC_WIDTH/2)+4,HDB1
        move.w  #NTSC_HMID-(NTSC_WIDTH/2)+4,HDB2
        ; HDE — horizontal display end
        move.w  #(NTSC_WIDTH/2)-1+$0400,HDE
        ; VDB/VDE — vertical display begin/end
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
        ; VI (vertical interrupt) — set to max so it never fires
        move.w  #$7FFF,VI

        ; --- 10. Set background colour -----------------------
        ; CRY format: C=chroma, R=intensity, Y=luma
        ; $FF20 = bright blue in CRY mode
        move.w  #$FF20,BG

        ; --- 11. Enable video: CRY16 + VIDEN + BGEN + PWIDTH4
        move.w  #CRY16|VIDEN|BGEN|PWIDTH4,VMODE

        ; --- 12. Spin forever --------------------------------
forever:
        bra.s   forever

        .end    start
