"""soak_gate7.py - randomized soak test + per-frame CPU budget for gate7_castle.

Plays N frames of seeded random input (held for random stretches, like a
mashing player) and checks invariants every frame:
  * the CPU never faults; the object list always ends in STOP
  * hero x/y inside the playfield, floor 0..4, never inside a closed door
  * a run never lasts forever without input mattering (softlock watchdog)
Also measures, per frame, the halfline at which the main loop reaches its
"wait for next frame" loop, i.e. how much of the frame the logic used.

    python tools/soak_gate7.py [frames] [seed] [instr_per_halfline]
"""
import os
import random
import struct
import zlib
import sys

sys.path.insert(0, os.path.dirname(__file__))
from jagsim import JagSim, HALFLINES_PER_FRAME  # noqa: E402
import symbols  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COF = os.environ.get("COF") or os.path.join(ROOT, "gate7_castle", "gate7_castle.cof")
S = 0x1000
SYM = symbols.load()
NOBJ = int(os.environ.get("NOBJ", "20"))      # 17 gameplay objects + environment band + HUD + text band
LIVE = 0x4000
BANDS_BASE, BAND_SIZE = SYM["BANDS_BASE"], SYM["BAND_SIZE"]


def find_wait_blank(sim):
    """Locate main's '.wait_blank' loop: move.w VC,d0 / cmp.w #507,d0 / blt.s."""
    code = bytes(sim.uc.mem_read(0x802000, 0x400))
    pat = bytes.fromhex("303900F00006" "C07C07FF" "B07C01FB" "6D")
    i = code.find(pat)
    if i < 0:
        raise RuntimeError("wait_blank loop not found")
    return 0x802000 + i, 0x802000 + i + len(pat)


def main():
    frames = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    ipl = int(sys.argv[3]) if len(sys.argv) > 3 else 18
    rnd = random.Random(seed)
    sim = JagSim(COF, instr_per_halfline=ipl)
    lo, hi = find_wait_blank(sim)
    band_crc = None
    prev_fl = None
    since_blank = None        # halflines since the last blank started (logic deadline: 525)

    done_at = []          # halfline (relative to blank start at 507) when logic finished
    blank_hl = None
    keys = ["left", "right", "up", "down", "a"]
    pad = set()
    hold = 0
    runs_seen = set()
    floors_seen = set()
    max_run_frames = 0
    run_start = 0
    last_runs = 0
    problems = []

    for f in range(frames):
        if hold <= 0:
            pad = set(k for k in keys if rnd.random() < (0.45 if k in ("left", "right") else 0.25))
            if "left" in pad and "right" in pad:
                pad.discard(rnd.choice(["left", "right"]))
            hold = rnd.randint(2, 40)
        hold -= 1
        sim.pad = pad
        vdb, vde = sim.io_w(0x46), sim.io_w(0x48)
        finished = None
        for hl in range(HALFLINES_PER_FRAME):
            sim.vc = hl
            if vdb <= hl < vde and hl % 2 == 0:
                sim._op_line(hl)
            sim._run_halfline()
            if since_blank is not None:
                since_blank += 1
                if lo <= sim.pc < hi and hl < 507:
                    done_at.append(since_blank)      # back waiting for blank: logic done
                    since_blank = None
            if hl == 507 and sim.io_w(0x28):          # video on: the loop is running
                if since_blank is not None:
                    problems.append("frame %d: logic overran a whole frame" % f)
                since_blank = 0
        sim.frame += 1
        if not sim.io_w(0x28):
            continue                                   # still booting (art + bands being copied)
        if band_crc is None:
            band_crc = zlib.crc32(bytes(sim.uc.mem_read(BANDS_BASE, 5 * BAND_SIZE)))
        # ---- invariants ------------------------------------------
        hx, hy, fl, climb, gs = (sim.sw(S + SYM["HX"]), sim.sw(S + SYM["HY"]), sim.sw(S + SYM["FLOOR"]), sim.sw(S + SYM["CLIMB"]), sim.sw(S + SYM["GSTATE"]))
        if not (0 <= hx <= 304 and 0 <= hy <= 460 and 0 <= fl <= 4):
            problems.append("frame %d: bad hero state x=%d y=%d floor=%d" % (f, hx, hy, fl))
        if fl in (0, 2) and gs == 0:
            for d in range(2):
                b = S + SYM["DOORS"] + 8 * (d + (2 if fl == 2 else 0))
                dx, dopen = sim.w(b), sim.w(b + 2)
                if not dopen and hx + 16 > dx and hx < dx + 8 and hy == 372:
                    problems.append("frame %d: hero inside closed door F%d x=%d door=%d" % (f, fl + 1, hx, dx))
        # LIVE is copied from SHADOW at blank, and SHADOW is built when the previous frame's
        # logic finishes (blank + ~80 halflines, i.e. early in this frame). So the whole list
        # (band, ladders, hero) shows FLOOR as it stood at that moment: this frame's floor or
        # the last frame's, never a stale or invalid band.
        band0 = struct.unpack(">QQ", sim.uc.mem_read(LIVE, 16))
        live_data = ((band0[0] >> 43) & 0x1FFFFF) << 3
        ok_data = {BANDS_BASE + x * BAND_SIZE for x in (fl, prev_fl) if x is not None}
        if live_data not in ok_data or (band0[1] >> 47) & 1 or (band0[1] >> 28) & 0x3FF != 80 or ((band0[0] >> 14) & 0x3FF) != 180:
            problems.append("frame %d: environment band object wrong: data $%X (floor %d / last %s), trans %d, w %d, h %d"
                            % (f, live_data, fl + 1, "-" if prev_fl is None else prev_fl + 1, (band0[1] >> 47) & 1,
                               (band0[1] >> 28) & 0x3FF, (band0[0] >> 14) & 0x3FF))
        prev_fl = fl
        stop = struct.unpack(">Q", sim.uc.mem_read(LIVE + NOBJ * 16, 8))[0]
        if stop & 7 != 4:
            problems.append("frame %d: object list lost its STOP" % f)
        runs = sim.w(S + SYM["RUNS"])
        if runs != last_runs:
            max_run_frames = max(max_run_frames, f - run_start)
            run_start, last_runs = f, runs
        floors_seen.add(fl)
        runs_seen.add(runs)
        if len(problems) > 20:
            break

    max_run_frames = max(max_run_frames, frames - run_start)
    if zlib.crc32(bytes(sim.uc.mem_read(BANDS_BASE, 5 * BAND_SIZE))) != band_crc:
        problems.append("the resident environment bands were modified during the run")
    done_at.sort()
    n = len(done_at)
    print("soak: %d frames, seed %d, %d instr/halfline" % (n, seed, ipl))
    print("  runs ended: %d (deaths %d, escapes %d); floors reached: %s" % (
        sim.w(S + SYM["RUNS"]), sim.w(S + SYM["DEATHS"]), sim.w(S + SYM["WINS"]), sorted(x + 1 for x in floors_seen)))
    print("  longest run: %d frames" % max_run_frames)
    print("  logic finished at blank+N halflines: median %d, p99 %d, max %d (frame is %d halflines)" % (
        done_at[n // 2], done_at[int(n * 0.99)], done_at[-1], HALFLINES_PER_FRAME))
    tiers = [sim.w(S + SYM[k]) for k in ("T_DOOR", "T_LEVER", "T_RUSH", "T_WAIT", "T_BRACE", "T_WATCH", "T_TRAP", "T_CHEST")]
    print("  final tiers door/lever/rush/wait/brace/watch/trap/chest: %s" % tiers)
    if problems:
        print("  PROBLEMS:")
        for p in problems[:20]:
            print("   ", p)
        return 1
    print("  no invariant violations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
