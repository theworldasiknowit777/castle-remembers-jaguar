"""jagsim.py - headless test harness for the Castle Remembers Jaguar builds.

Runs the real 68000 code from an RLN COFF (.cof) under the Unicorn CPU
emulator, with a small model of the parts of Tom/Jerry the game touches:

  * VC ($F00006) advances with executed instructions (INSTR_PER_HALFLINE),
    wrapping at HALFLINES_PER_FRAME, so the game's "wait for VDE / wait for
    wrap" loop paces real frames and the per-frame instruction budget of the
    blanking window can be measured.
  * The Object Processor runs once per displayed line (VDB..VDE, step 2
    halflines), walking the list from the word-swapped OLP. BITMAP objects are
    drawn (optional) and their HEIGHT/DATA are written back to DRAM exactly as
    the Tech Ref describes, so missing per-frame refreshes show up as missing
    objects, just like on hardware.
  * JOYSTICK ($F14000) / JOYBUTS ($F14002) return the scripted pad state for
    row 0 of pad 1 (Up/Down/Left/Right on J8-J11, Pause/A on B0/B1).

This is a TEST MODEL, not an emulator: colours are approximate, timing is an
estimate, and Virtual Jaguar remains the reference for final verification.

Usage as a library:
    sim = JagSim("gate7_castle.cof")
    sim.run_frames(60, pad={"right"})
    print(sim.w(0x100))            # read a DRAM word
    sim.render_png("out.png")      # last displayed frame
"""
import struct
import sys

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UcError
from unicorn.m68k_const import UC_M68K_REG_PC, UC_M68K_REG_SR, UC_CPU_M68K_M68000

DRAM_SIZE = 0x200000
ROM_BASE, ROM_SIZE = 0x800000, 0x200000
IO_BASE, IO_SIZE = 0xF00000, 0x20000

HALFLINES_PER_FRAME = 525      # NTSC field: VC counts 0..524
INSTR_PER_HALFLINE = 26        # ~422 68k cycles per halfline / ~16 cycles per instr

VC_OFF = 0x06
OLP_OFF = 0x20
VDB_OFF = 0x46
VDE_OFF = 0x48
BG_OFF = 0x58
JOY_OFF = 0x14000
JOYB_OFF = 0x14002

PAD_BITS = {"up": 8, "down": 9, "left": 10, "right": 11}
BUT_BITS = {"pause": 0, "a": 1}


import json as _json
import os as _os

_CRY = _json.load(open(_os.path.join(_os.path.dirname(__file__), "cry_tables.json")))


def cry_to_rgb(w):
    """CRY16 -> RGB using Virtual Jaguar's own tables (src/cry2rgb.h, v2.1.3-R5)."""
    c, r, y = (w >> 12) & 0xF, (w >> 8) & 0xF, w & 0xFF
    return tuple((_CRY[t][c][r] * y) >> 8 for t in ("redcv", "greencv", "bluecv"))


def rgb_to_cry(rgb):
    """Closest CRY16 word to an (r, g, b) colour (brute force; for picking art colours)."""
    best, bw = None, 0
    for c in range(16):
        for r in range(16):
            base = [_CRY[t][c][r] for t in ("redcv", "greencv", "bluecv")]
            m = max(base) or 1
            y = max(0, min(255, round(max(rgb) * 256 / m)))
            got = [(b * y) >> 8 for b in base]
            d = sum((a - g) ** 2 for a, g in zip(rgb, got))
            if best is None or d < best:
                best, bw = d, (c << 12) | (r << 8) | y
    return bw


class JagSim:
    def __init__(self, cof_path, instr_per_halfline=INSTR_PER_HALFLINE):
        self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        self.uc.ctl_set_cpu_model(UC_CPU_M68K_M68000)
        self.uc.mem_map(0, DRAM_SIZE)
        self.uc.mem_map(ROM_BASE, ROM_SIZE)
        self.io = bytearray(IO_SIZE)
        self.uc.mmio_map(IO_BASE, IO_SIZE, self._io_read, None, self._io_write, None)
        self.ipl = instr_per_halfline
        self.xorg = 0              # XPOS shown at screen x 0 (VJ: line buffer pixel 0)
        self.vc = 0
        self.frame = 0
        self.pad = set()
        self.joy_select = 0
        self.frame_buf = None
        self.draw = False
        self.bg = 0
        self.halted = None
        self.blank_instr = []          # instructions spent from VDE to wrap, per frame
        self._instr_this_blank = 0
        self.pc = self._load_cof(cof_path)
        # 68000 reset: SSP/PC from vectors; RLN COFF entry is jumped to directly.
        self.uc.reg_write(UC_M68K_REG_PC, self.pc)
        self.uc.reg_write(UC_M68K_REG_SR, 0x2700)   # supervisor, IPL 7 (reset state)

    # ---------------------------------------------------------------- loading
    def _load_cof(self, path):
        from check_cof import check
        problems = check(path)
        if problems:
            raise ValueError("refusing %s: %s" % (path, "; ".join(problems)))
        data = open(path, "rb").read()
        magic, nsect = struct.unpack(">HH", data[0:4])
        if magic != 0x0150:
            raise ValueError("not a 68k COFF: magic %04X" % magic)
        opt_size = struct.unpack(">H", data[16:18])[0]
        entry = struct.unpack(">I", data[20 + 16:20 + 20])[0]
        sh = 20 + opt_size
        for i in range(nsect):
            name, paddr, vaddr, size, scnptr = struct.unpack(">8sIIII", data[sh + i * 40: sh + i * 40 + 24])
            name = name.rstrip(b"\0").decode()
            if size and name != ".bss" and scnptr:
                self.uc.mem_write(vaddr, data[scnptr:scnptr + size])
        return entry

    # ---------------------------------------------------------------- MMIO
    def _io_read(self, uc, off, size, _):
        if off in (JOY_OFF + 1, JOYB_OFF + 1) and size == 1:
            return self._io_read(uc, off - 1, 2, None) & 0xFF
        if off in (JOY_OFF, JOYB_OFF) and size == 1:
            # Virtual Jaguar: byte reads return the matching half of the word,
            # so btst #4,$F14002 sees bit 12 of JOYBUTS (always 1 there).
            return self._io_read(uc, off, 2, None) >> 8
        if off == VC_OFF and size == 2:
            # VJ (jaguar.cpp HalflineCallback) sets bit 11 on alternate fields
            return self.vc | (0x0800 if self.frame & 1 else 0)
        if off == JOY_OFF and size == 2:
            v = 0xFFFF
            if self.joy_select == 0x817E:
                for k, b in PAD_BITS.items():
                    if k in self.pad:
                        v &= ~(1 << b)
            return v
        if off == JOYB_OFF and size == 2:
            v = 0xFFFF                    # bit 4 set = NTSC (VJ: 0xFFEF | 0x10)
            if self.joy_select == 0x817E:
                for k, b in BUT_BITS.items():
                    if k in self.pad:
                        v &= ~(1 << b)
            return v
        return int.from_bytes(self.io[off:off + size], "big")

    def _io_write(self, uc, off, size, value, _):
        self.io[off:off + size] = value.to_bytes(size, "big")
        if off == JOY_OFF and size == 2:
            self.joy_select = value & 0xFFFF

    def io_w(self, off):
        return int.from_bytes(self.io[off:off + 2], "big")

    # ---------------------------------------------------------------- memory
    def w(self, addr):
        return struct.unpack(">H", self.uc.mem_read(addr, 2))[0]

    def sw(self, addr):
        return struct.unpack(">h", self.uc.mem_read(addr, 2))[0]

    def l(self, addr):
        return struct.unpack(">I", self.uc.mem_read(addr, 4))[0]

    def poke_w(self, addr, v):
        self.uc.mem_write(addr, struct.pack(">H", v & 0xFFFF))

    # ---------------------------------------------------------------- OP model
    def olp(self):
        lo, hi = self.io_w(OLP_OFF), self.io_w(OLP_OFF + 2)
        return (lo | (hi << 16)) & 0xFFFFF8

    def _op_line(self, vc):
        """Run the Object Processor for the display line at halfline vc."""
        addr = self.olp()
        for _ in range(64):           # guard against list loops
            if addr + 16 > DRAM_SIZE:
                return
            p0 = struct.unpack(">Q", self.uc.mem_read(addr, 8))[0]
            typ = p0 & 7
            if typ == 4:              # STOP
                return
            link = ((p0 >> 24) & 0x7FFFF) << 3
            if typ == 0:              # BITMAP
                ypos = (p0 >> 3) & 0x7FF
                height = (p0 >> 14) & 0x3FF
                data = ((p0 >> 43) & 0x1FFFFF) << 3
                if vc >= ypos and height > 0:
                    p1 = struct.unpack(">Q", self.uc.mem_read(addr + 8, 8))[0]
                    if self.draw:
                        self._draw_line(vc, p1, data)
                    dwidth = (p1 >> 18) & 0x3FF
                    height -= 1
                    data += dwidth * 8
                    p0 = (p0 & ~((0x3FF << 14) | (0x1FFFFF << 43))) | (height << 14) | ((data >> 3) << 43)
                    self.uc.mem_write(addr, struct.pack(">Q", p0))
                addr = link
            elif typ == 3:            # BRANCH
                ypos = (p0 >> 3) & 0x7FF
                cc = (p0 >> 14) & 7
                take = {0: vc == ypos or ypos == 0x7FF, 1: ypos > vc, 2: ypos < vc}.get(cc, False)
                addr = link if take else addr + 8
            else:                     # scaled / GPU objects not used here
                addr = link

    def _draw_line(self, vc, p1, data):
        xpos = p1 & 0xFFF
        if xpos & 0x800:
            xpos -= 0x1000
        depth = (p1 >> 12) & 7
        iwidth = (p1 >> 28) & 0x3FF
        trans = (p1 >> 47) & 1
        if depth != 4:
            return
        row = vc // 2
        if not (0 <= row < len(self.frame_buf)):
            return
        line = self.frame_buf[row]
        pix = self.uc.mem_read(data, iwidth * 8)
        for i in range(iwidth * 4):
            v = (pix[i * 2] << 8) | pix[i * 2 + 1]
            if trans and v == 0:
                continue
            x = xpos - self.xorg + i
            if 0 <= x < len(line):
                line[x] = v

    # ---------------------------------------------------------------- running
    def _run_halfline(self):
        try:
            self.uc.emu_start(self.pc, 0xFFFFFFFF, count=self.ipl)
        except UcError as e:
            self.pc = self.uc.reg_read(UC_M68K_REG_PC)
            self.halted = "CPU fault at PC=%06X: %s" % (self.pc, e)
            raise RuntimeError(self.halted)
        self.pc = self.uc.reg_read(UC_M68K_REG_PC)

    def run_frames(self, n, pad=(), draw_last=False):
        """Run n whole frames with the given pad state held."""
        self.pad = set(pad)
        for i in range(n):
            self.draw = draw_last and i == n - 1
            if self.draw:
                self.frame_buf = [[None] * 330 for _ in range(262)]
                self.bg = self.io_w(BG_OFF)
            vdb, vde = self.io_w(VDB_OFF), self.io_w(VDE_OFF)
            for hl in range(HALFLINES_PER_FRAME):
                self.vc = hl
                if vdb <= hl < vde and hl % 2 == 0 and self.olp_valid():
                    self._op_line(hl)
                self._run_halfline()
                if hl >= 507:
                    self._instr_this_blank += self.ipl
            self.frame += 1
        return self

    def snapshot(self):
        """Whole machine state (for look-ahead bots); restore() rewinds to it."""
        return (self.uc.context_save(), bytes(self.uc.mem_read(0, DRAM_SIZE)), bytes(self.io),
                self.pc, self.vc, self.frame, self.joy_select, self._instr_this_blank, len(self.blank_instr))

    def restore(self, snap):
        ctx, dram, io, self.pc, self.vc, self.frame, self.joy_select, self._instr_this_blank, nb = snap
        self.uc.context_restore(ctx)
        self.uc.mem_write(0, dram)
        self.io[:] = io
        del self.blank_instr[nb:]

    def olp_valid(self):
        return self.io_w(VDE_OFF) != 0

    def render_png(self, path, scale=2):
        from PIL import Image
        h, wdt = len(self.frame_buf), len(self.frame_buf[0])
        img = Image.new("RGB", (wdt, h))
        bgc = cry_to_rgb(self.bg)
        px = img.load()
        for y in range(h):
            for x in range(wdt):
                v = self.frame_buf[y][x]
                px[x, y] = bgc if v is None else cry_to_rgb(v)
        img.resize((wdt * scale, h * scale), Image.NEAREST).save(path)


if __name__ == "__main__":
    sim = JagSim(sys.argv[1])
    sim.run_frames(int(sys.argv[2]) if len(sys.argv) > 2 else 30, draw_last=True)
    sim.render_png(sys.argv[3] if len(sys.argv) > 3 else "jagsim_frame.png")
    print("frames", sim.frame, "PC %06X" % sim.pc)
