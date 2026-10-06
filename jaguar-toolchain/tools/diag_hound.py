"""diag_hound.py - is a hound death avoidable? Replays the campaign (SEED) up to
its first hound death, then, from snapshots 10..90 frames before the death,
searches every wait-k-then-jump/back-off input pattern for one that survives
60 frames. Prints what the bot's own planner returned on the way in.

    python tools/diag_hound.py [runs]
"""
import os
import random
import sys

import test_gate7 as t

HIST = []
DEAD = []


def main(max_runs=15):
    b = t.Bot("diag")
    real = b.s.run_frames

    def rec(n, pad=(), draw_last=False):
        for _ in range(n):
            if b.v("GSTATE") == 0 and not DEAD:
                HIST.append(b.s.snapshot())
                del HIST[:-200]
            elif b.v("GSTATE") == 1:
                DEAD.append(1)
            real(1, pad=pad, draw_last=draw_last)
        return b.s
    b.s.run_frames = rec
    orig_plan = t.Bot.hound_plan

    def logged(self, sgn, horizon=34, steps=4):
        p = orig_plan(self, sgn, horizon, steps)
        hx = self.v("HX")
        sl = self.hound_threat(hx)
        e = self.enemy(sl) if sl is not None else {}
        print("     plan f=%d F%d hx=%d hound x=%s dir=%s lunge=%d sniff=%d -> %s" % (
            self.s.frame, self.v("FLOOR") + 1, hx, e.get("x"), e.get("dir"),
            self.s.w(t.S + t.ENEMY + 32 * (sl or 0) + 28), self.s.w(t.S + t.ENEMY + 32 * (sl or 0) + 26),
            None if p is None else "%d frames" % len(p)))
        return p
    t.Bot.hound_plan = logged

    scen = os.environ.get("SCEN")
    if scen:
        try:
            t.SCENARIOS[scen](b)
        except AssertionError as e:
            print("scenario:", e)
        max_runs = 1
    rnd = random.Random(int(os.environ.get("SEED", "7")))
    for run in range(max_runs if not scen else 0):
        door = rnd.choice("LLR") if run < 8 else rnd.choice("LR")
        lever = rnd.choice("LRR")
        if rnd.random() < 0.3:
            b.frames(rnd.randint(200, 700))
        runs0 = b.v("RUNS")
        try:
            b.run_route(door, lever, shove=rnd.random() < 0.5, chests=rnd.random() < 0.4)
        except AssertionError:
            pass
        if b.v("GSTATE") == 2:
            print("run %d escaped" % (run + 1))
            b.wait_until(lambda: b.v("GSTATE") == 0, 400)
            continue
        if b.v("GSTATE") == 0 and b.v("RUNS") == runs0:
            b.wait_until(lambda: b.v("GSTATE") == 1, 900)
        print("run %d died F%d x=%d enemies=%s" % (run + 1, b.v("FLOOR") + 1, b.v("HX"),
                                                 [(e["type"], e["x"]) for e in (b.enemy(0), b.enemy(1))]))
    if True:
        # find the first frame of death in the history
        b.s.run_frames = real
        death = len(HIST)                   # history stops at the last live frame
        for back in (10, 20, 30, 45, 60, 90):
            i = death - back
            if i < 0:
                break
            found = None
            for k in range(0, 30):
                for hold in ({"left"}, {"right"}, set()):
                    for air in ({"left"}, {"right"}, set()):
                        b.s.restore(HIST[i])
                        if b.v("GSTATE"):
                            continue
                        plan = [hold] * k + [air | {"up"}] + [air] * 59
                        ok = True
                        for p in plan[:60]:
                            real(1, pad=p)
                            if b.v("GSTATE"):
                                ok = False
                                break
                        if ok:
                            found = (k, sorted(hold), sorted(air))
                            break
                    if found:
                        break
                if found:
                    break
            b.s.restore(HIST[i])
            print("  %d frames before death (hx=%d hound=%s): survivable=%s" % (
                back, b.v("HX"), [(e["type"], e["x"], e["dir"]) for e in (b.enemy(0), b.enemy(1))], found))
        return


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 15)
