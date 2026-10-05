"""test_gate7.py - scripted playtests of gate7_castle.cof under jagsim.

Each scenario drives the real 68000 build with pad input, the way a player
would (walk, ACT, climb, jump), and asserts on the game state in DRAM.

    python tools/test_gate7.py            # all scenarios
    python tools/test_gate7.py route      # one scenario
    JSIM_OUT=dir python tools/test_gate7.py   # also save frames there
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from jagsim import JagSim  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COF = os.path.join(ROOT, "gate7_castle", "gate7_castle.cof")
OUT = os.environ.get("JSIM_OUT")

S = 0x1000
OFF = dict(HX=6, HY=8, HVY=10, CLIMB=12, FLOOR=14, GSTATE=20, GTIMER=22, CAUSE=36, SEEN=38, NOTES=40,
           RUNS=94, WINS=96, DEATHS=98, T_DOOR=100, T_LEVER=102, T_RUSH=104, T_WAIT=106, T_BRACE=108,
           T_WATCH=110, T_TRAP=112, SIDE_DOOR=114, SIDE_LEVER=116, EXIT_X=118, AUTOCLOSE=122)
R = dict(DOORL=44, DOORR=46, LEVL=48, LEVR=50, PULLS=52, RUSH=54, WAIT=56, CONF=58, AVOID=60, TRAPS=62)
M = {k: v + 20 for k, v in R.items()}
GROUND = 372
WALK = 2
LAD = dict(L=6, C=152, R=298)
LEVER = dict(L=80, R=232)
DOOR = dict(L=94, R=218)


class Bot:
    def __init__(self, name):
        self.s = JagSim(COF)
        self.name = name
        self.shots = 0
        self.s.run_frames(5)

    # ---- state
    def v(self, k):
        return self.s.sw(S + OFF[k])

    def r(self, k):
        return self.s.w(S + R[k])

    def m(self, k):
        return self.s.w(S + M[k])

    def lev(self, i):            # i: 0 F2L 1 F2R 2 F4L 3 F4R -> (effect, state)
        return self.s.w(S + 160 + 4 * i), self.s.w(S + 162 + 4 * i)

    def door(self, i):           # i: 0 F1L 1 F1R 2 F3L 3 F3R -> (x, open, lock, passed)
        return tuple(self.s.w(S + 128 + 8 * i + o) for o in (0, 2, 4, 6))

    def enemy(self, slot):
        b = S + 584 + 32 * slot
        return dict(type=self.s.sw(b), x=self.s.sw(b + 2) >> 4, stun=self.s.w(b + 18), chase=self.s.w(b + 16),
                    arm=self.s.w(b + 12), org=self.s.w(b + 14), spd=self.s.w(b + 10))

    def plan_enemy(self, floor, slot):
        b = S + 264 + 64 * floor + 32 * slot
        return dict(type=self.s.sw(b), x=self.s.sw(b + 2), min=self.s.sw(b + 6), max=self.s.sw(b + 8),
                    org=self.s.w(b + 14))

    def spike(self, floor, slot):
        b = S + 184 + 16 * floor + 8 * slot
        return dict(x=self.s.w(b), w=self.s.w(b + 2), per=self.s.w(b + 4), org=self.s.w(b + 6))

    def status(self, tag=""):
        print("   [%s] f=%d floor=F%d x=%d y=%d climb=%d gs=%d runs=%d wins=%d deaths=%d" % (
            tag, self.s.frame, self.v("FLOOR") + 1, self.v("HX"), self.v("HY"), self.v("CLIMB"), self.v("GSTATE"),
            self.v("RUNS"), self.v("WINS"), self.v("DEATHS")))

    def shot(self, label):
        if not OUT:
            return
        self.s.run_frames(1, draw_last=True)
        self.shots += 1
        self.s.render_png(os.path.join(OUT, "%s_%02d_%s.png" % (self.name, self.shots, label)))

    # ---- actions
    def frames(self, n, *pad):
        self.s.run_frames(n, pad=set(pad))

    def goto(self, x, limit=600, jump_over=None, fight=True):
        """Walk until hero x == x (2px steps), hopping spikes and arrows and
        shoving guards that block the way, like a careful player."""
        if jump_over is None:
            jump_over = self.spikes_on(self.v("FLOOR"))
        for _ in range(limit):
            hx = self.v("HX")
            if abs(hx - x) <= 1 or self.v("GSTATE"):
                return
            d = "right" if x > hx else "left"
            sgn = 1 if d == "right" else -1
            pad = {d}
            grounded = self.v("HY") == GROUND and self.v("HVY") == 0
            for lo, hi in jump_over:
                # hero x values that touch this spike: (lo-8, hi-8) exclusive.
                # Jump on the last safe pixel before the zone; a jump spans 32px.
                zlo, zhi = lo - 8, hi - 8
                nxt = hx + WALK * sgn
                if grounded and ((sgn < 0 and hx >= zhi and nxt < zhi) or (sgn > 0 and hx <= zlo and nxt > zlo)):
                    land = hx + 32 * sgn
                    # a guard that stays stunned for the whole jump (16 frames) is no threat
                    # (a guard pinned under the hero can't get up, so it isn't a threat either)
                    if any(e["type"] >= 0 and e["stun"] < 24 and abs(e["x"] - land) < 28 and abs(e["x"] - hx) >= 9
                           for e in (self.enemy(0), self.enemy(1))):
                        pad.discard(d)          # a guard is under the landing spot: wait at the edge
                    else:
                        pad.add("up")
            if fight:
                for slot in (0, 1):
                    e = self.enemy(slot)
                    if e["type"] < 0 or e["stun"]:
                        continue
                    a = (e["x"] - hx) * sgn
                    if 8 <= a <= 40 and grounded and self.at_spike_edge(hx, sgn, jump_over):
                        pad.add("a")                    # waiting at a spike: shove it, then jump
                        pad.discard(d)
                    elif 8 <= a <= 24 and grounded:
                        pad.add("a")
                    elif -8 < a < 8 and e["stun"] == 0:
                        pad.discard(d)          # never walk into it
                    elif -22 < a <= -8 and grounded:
                        self.face_and_shove(e)  # coming from behind: turn and shove
                        pad = set()
                if self.s.w(S + 652) and grounded:        # arrow in flight
                    ax = self.s.sw(S + 648) >> 4
                    adir = self.s.sw(S + 650)
                    gap = (hx + 8) - (ax + 4)
                    if 0 < gap * adir < 34:
                        pad.add("up")
            self.s.run_frames(1, pad=pad)
            if "a" in pad:
                self.s.run_frames(1, pad=set())  # release (standing still) so the next ACT is a new press
        raise AssertionError("goto(%d) stuck at x=%d" % (x, self.v("HX")))

    @staticmethod
    def at_spike_edge(hx, sgn, zones):
        for lo, hi in zones:
            zlo, zhi = lo - 8, hi - 8
            if (sgn < 0 and 0 <= hx - zhi <= 2) or (sgn > 0 and 0 <= zlo - hx <= 2):
                return True
        return False

    def act(self, button="a"):
        self.frames(1, button)
        self.frames(2)

    def climb(self, direction="up", limit=400):
        start = self.v("FLOOR")
        key = "up" if direction == "up" else "down"
        for _ in range(limit):
            pad = {key}
            if key == "up" and self.v("CLIMB") == 2 and self.v("HY") <= 432:
                # about to step out of a ladder hole: wait for the guard to pass
                busy = [e for e in (self.enemy(0), self.enemy(1))
                        if e["type"] >= 0 and not e["stun"] and abs(e["x"] - self.v("HX")) < 26]
                if busy:
                    pad = {"down"} if self.v("HY") < 420 else set()   # duck back into the hole
            self.s.run_frames(1, pad=pad)
            if self.v("GSTATE"):
                return
            if self.v("FLOOR") != start and self.v("CLIMB") == 0:
                self.frames(2)
                return
        raise AssertionError("climb %s from F%d never arrived (y=%d climb=%d)" % (
            direction, start + 1, self.v("HY"), self.v("CLIMB")))

    def wait_until(self, cond, limit=600, *pad):
        for _ in range(limit):
            if cond():
                return
            self.s.run_frames(1, pad=set(pad))
        raise AssertionError("wait_until timed out")

    def die_and_rebuild(self):
        self.wait_until(lambda: self.v("GSTATE") == 0, 400)

    # ---- a full route: side 'L' or 'R' on choice floors, lever side on lever floors
    def run_route(self, door_side="L", lever_side="L", shove=False):
        assert self.v("FLOOR") == 0
        self.choice_floor(0, door_side)
        self.climb("up")
        assert self.v("FLOOR") == 1, "expected F2"
        self.lever_floor(1, lever_side, shove)
        self.climb("up")
        assert self.v("FLOOR") == 2, "expected F3"
        self.choice_floor(2, door_side)
        self.climb("up")
        assert self.v("FLOOR") == 3, "expected F4"
        self.lever_floor(3, lever_side, shove)
        self.climb("up")
        assert self.v("FLOOR") == 4, "expected F5"
        ex = self.v("EXIT_X") + 8
        self.goto(ex)
        self.frames(2)

    def spikes_on(self, floor):
        out = []
        for i in (0, 1):
            sp = self.spike(floor, i)
            if sp["w"]:
                out.append((sp["x"], sp["x"] + sp["w"]))
        return out

    def through_corridor(self, floor, side):
        self.goto(LAD[side])
        if self.v("GSTATE") == 0:
            self.wait_safe_climb()

    def wait_safe_climb(self):
        """Don't start climbing with a guard about to step onto the ladder."""
        for _ in range(240):
            close = [e for e in (self.enemy(0), self.enemy(1))
                     if e["type"] >= 0 and not e["stun"] and abs(e["x"] - self.v("HX")) < 20]
            if not close:
                return
            self.face_and_shove(close[0])

    def face_and_shove(self, e):
        """Turn toward a guard (one step) and shove it."""
        d = "right" if e["x"] > self.v("HX") else "left"
        self.frames(1, d)
        self.frames(1, "a")
        self.frames(1)

    def choice_floor(self, floor, side):
        di = (2 if floor == 2 else 0) + (0 if side == "L" else 1)
        x, opened, lock, _ = self.door(di)
        if lock:
            side = "R" if side == "L" else "L"
            di ^= 1
            x, opened, lock, _ = self.door(di)
        if not opened:
            self.goto(x + 8 if side == "L" else x - 16)
            self.act()
            assert self.door(di)[1] == 1, "F%d door did not open" % (floor + 1)
        self.through_corridor(floor, side)

    def lever_floor(self, floor, side, shove):
        gi = 0 if floor == 1 else 2
        order = [side, "R" if side == "L" else "L"]
        for sd in order:
            self.goto(LEVER[sd] - 4)
            if shove:
                self.try_shove()
            li = gi + (0 if sd == "L" else 1)
            for _ in range(4):                  # ACT may shove a guard first
                before = self.lev(li)[1]
                self.act()
                if self.v("GSTATE") or self.lev(li)[1] != before or self.s.w(S + 176 + (0 if floor == 1 else 4)):
                    break
            if self.v("GSTATE"):
                return
            eff, state = self.lev(li)
            if self.s.w(S + 176 + (0 if floor == 1 else 4)):
                break
            # trapped lever: run to the wall side, out of the flames, and let them burn out
            if self.s.w(S + 656):
                self.goto(34 if sd == "L" else 270)
                self.wait_until(lambda: self.s.w(S + 656) == 0 or self.v("GSTATE"), 200)
        assert self.s.w(S + 176 + (0 if floor == 1 else 4)) == 1, "gate did not open"
        self.goto(LAD["C"])
        if self.v("GSTATE") == 0:
            self.wait_safe_climb()

    def try_shove(self):
        for slot in (0, 1):
            e = self.enemy(slot)
            if e["type"] >= 0 and abs(e["x"] - self.v("HX")) < 30:
                self.act()


SCENARIOS = {}


def scenario(fn):
    SCENARIOS[fn.__name__] = fn
    return fn


@scenario
def boot(b):
    """Neutral castle on first boot: F1, two closed doors, two up-ladders."""
    assert b.v("FLOOR") == 0 and b.v("HX") == 152 and b.v("HY") == GROUND
    assert b.door(0)[:3] == (94, 0, 0) and b.door(1)[:3] == (218, 0, 0)
    assert b.v("RUNS") == 0 and b.v("NOTES") == 0
    b.shot("boot")


@scenario
def controls(b):
    """Z/C walk with clamps, S jumps and lands, closed doors are walls."""
    x0 = b.v("HX")
    b.frames(10, "right")
    assert b.v("HX") == x0 + 20, b.v("HX")
    b.frames(10, "left")
    assert b.v("HX") == x0
    b.frames(1, "up")
    b.frames(6)
    assert b.v("HY") < GROUND, "jump did not lift"
    b.frames(30)
    assert b.v("HY") == GROUND and b.v("HVY") == 0, "did not land"
    b.frames(200, "left")
    assert b.v("HX") == DOOR["L"] + 8, "closed door should stop the hero, x=%d" % b.v("HX")
    b.frames(200, "right")
    assert b.v("HX") == DOOR["R"] - 16, "closed right door, x=%d" % b.v("HX")


@scenario
def route(b):
    """Full five-floor escape on the neutral castle, LEFT doors / LEFT levers."""
    b.run_route("L", "L")
    b.status("at exit")
    assert b.v("GSTATE") == 2, "should be escaping"
    b.shot("escape")
    b.wait_until(lambda: b.v("GSTATE") == 0, 400)
    assert b.v("RUNS") == 1 and b.v("WINS") == 1 and b.v("FLOOR") == 0
    assert b.m("DOORL") == 400 and b.m("DOORR") == 0, (b.m("DOORL"), b.m("DOORR"))
    assert b.m("LEVL") == 400, b.m("LEVL")


@scenario
def retreat(b):
    """Climbing back down a ladder hole returns to the floor below."""
    b.goto(DOOR["R"] - 16)
    b.act()
    b.goto(LAD["R"])
    b.climb("up")
    assert b.v("FLOOR") == 1 and b.v("HX") == LAD["R"]
    b.frames(1, "down")
    b.climb("down")
    assert b.v("FLOOR") == 0 and b.v("HX") == LAD["R"] and b.v("HY") == GROUND


@scenario
def gate_blocks(b):
    """The F2 centre ladder cannot be climbed until a lever opens the gate."""
    b.goto(DOOR["L"] + 8)
    b.act()
    b.goto(LAD["L"])
    b.climb("up")
    b.goto(LAD["C"])
    b.frames(1, "up")
    assert b.v("CLIMB") == 0, "mounted the ladder through a shut gate"
    b.shot("gate_shut")
    b.goto(LEVER["L"] - 4)
    b.act()
    assert b.lev(0)[1] == 1 and b.s.w(S + 176) == 1, "lever should open the gate"
    b.goto(LAD["C"])
    b.climb("up")
    assert b.v("FLOOR") == 2


@scenario
def skull_death(b):
    """F2's Sentinel Skull kills on touch; death returns to F1 and the castle remembers."""
    b.goto(DOOR["L"] + 8)
    b.act()
    b.goto(LAD["L"])
    b.climb("up")
    e = b.enemy(0)
    assert e["type"] == 0, e
    b.goto(e["x"], limit=600)
    b.wait_until(lambda: b.v("GSTATE") == 1, 300)
    assert b.v("CAUSE") == 0
    b.shot("death")
    b.die_and_rebuild()
    assert b.v("RUNS") == 1 and b.v("DEATHS") == 1 and b.v("FLOOR") == 0


@scenario
def shove(b):
    """ACT facing a guard stuns it and counts as confronting it."""
    b.goto(DOOR["L"] + 8)
    b.act()
    b.goto(LAD["L"])
    b.climb("up")
    for _ in range(400):
        e = b.enemy(0)
        d = e["x"] - b.v("HX")
        if 4 < d < 20:
            b.frames(1, "right")
            b.act()
            break
        b.frames(1, "right" if d > 20 else "left" if d < 4 else None)
    e = b.enemy(0)
    assert e["stun"] > 0, e
    assert b.r("CONF") == 1


@scenario
def door_memory(b):
    """Going LEFT every run teaches the castle: spikes, a gift door, a guard, then bricks."""
    for i in range(3):
        b.run_route("L", "R")
        b.wait_until(lambda: b.v("GSTATE") == 0, 400)
        print("   after escape %d: T_DOOR=%d side=%d notes=%s" % (i + 1, b.v("T_DOOR"), b.v("SIDE_DOOR"),
                                                                bin(b.v("NOTES"))))
    assert b.v("SIDE_DOOR") == -1
    assert b.v("T_DOOR") == 3, b.v("T_DOOR")
    assert b.spike(0, 0)["w"] == 16 and b.spike(0, 0)["x"] == 41, b.spike(0, 0)
    assert b.door(0)[0] == 75, "favoured F1 door should move tight"
    assert b.door(2)[2] == 1, "favoured F3 door should be bricked"
    assert b.door(3)[1] == 1, "other F3 door left open as a gift"
    assert b.plan_enemy(0, 0)["type"] in (1, 2), b.plan_enemy(0, 0)   # guard, or heavy if it learned "brace"
    b.shot("f1_adapted")
    # the castle must still be escapable the other way
    b.run_route("R", "R")
    assert b.v("GSTATE") == 2, "adapted castle should still be escapable"


@scenario
def lever_memory(b):
    """Trusting the LEFT lever: F4 left becomes a trap, then F2 left a dud; the other lever works."""
    for i in range(2):
        b.run_route("R", "L")
        b.wait_until(lambda: b.v("GSTATE") == 0, 400)
        print("   after escape %d: T_LEVER=%d side=%d levers=%s" % (
            i + 1, b.v("T_LEVER"), b.v("SIDE_LEVER"), [b.lev(k)[0] for k in range(4)]))
    assert b.v("SIDE_LEVER") == -1 and b.v("T_LEVER") == 3
    assert b.lev(2)[0] == 2, "t1: F4 trusted lever is a trap"
    assert b.lev(0)[0] == 2, "t3: F2 trusted lever is a trap (t2 was a dud)"
    assert b.lev(3)[0] == 3, "t3: F4 other lever raises the alarm"
    assert b.lev(1)[0] == 0, "F2 other lever must still open the gate"
    # pull the trusted lever on F2: dud, then the other one works
    b.run_route("R", "L")
    assert b.v("GSTATE") == 2, "should still escape using the other levers"


@scenario
def rush_memory(b):
    """Never waiting is noticed: guards speed up, an ambush waits on F3."""
    for i in range(3):
        b.run_route("R", "R")
        b.wait_until(lambda: b.v("GSTATE") == 0, 400)
    print("   T_RUSH=%d T_WAIT=%d rush=%d wait=%d" % (b.v("T_RUSH"), b.v("T_WAIT"), b.m("RUSH"), b.m("WAIT")))
    assert b.v("T_RUSH") >= 2
    assert b.plan_enemy(2, 1)["org"] == 3, b.plan_enemy(2, 1)


@scenario
def wait_memory(b):
    """Lingering is noticed: gates slam shut after a few seconds."""
    for i in range(2):
        b.frames(900)                       # stand still for 15 s each run
        b.run_route("R", "R")
        b.wait_until(lambda: b.v("GSTATE") == 0, 400)
    print("   T_WAIT=%d autoclose=%d" % (b.v("T_WAIT"), b.v("AUTOCLOSE")))
    assert b.v("T_WAIT") >= 1 and b.v("AUTOCLOSE") in (300, 210, 150)


@scenario
def trap_memory(b):
    """Dying on spikes twice widens the F3 spikes."""
    for i in range(2):
        side = "L" if i == 0 else "R"
        b.goto(DOOR[side] + (8 if side == "L" else -16))
        b.act()
        b.through_corridor(0, side)
        b.climb("up")
        b.lever_floor(1, "L", False)
        b.climb("up")
        b.goto(DOOR["L"] + 8)
        b.act()
        b.goto(60, jump_over=[])            # walk into the static spikes
        b.wait_until(lambda: b.v("GSTATE") == 1, 120)
        assert b.v("CAUSE") == 4, b.v("CAUSE")
        b.die_and_rebuild()
    print("   traps=%d T_TRAP=%d" % (b.m("TRAPS"), b.v("T_TRAP")))
    assert b.v("T_TRAP") >= 1 and b.spike(2, 0)["w"] == 24


@scenario
def campaign(b):
    """15 runs with seeded random habits: every rebuilt castle must stay escapable (softlock hunt)."""
    import random
    rnd = random.Random(int(os.environ.get("SEED", "7")))
    escapes = deaths = 0
    for run in range(15):
        door = rnd.choice("LLR") if run < 8 else rnd.choice("LR")
        lever = rnd.choice("LRR")
        if rnd.random() < 0.3:
            b.frames(rnd.randint(200, 700))      # sometimes linger
        try:
            b.run_route(door, lever, shove=rnd.random() < 0.5)
        except AssertionError as e:
            if b.v("GSTATE") == 0:
                raise AssertionError("run %d stuck alive (softlock?): %s" % (run + 1, e))
        tiers = [b.v(k) for k in ("T_DOOR", "T_LEVER", "T_RUSH", "T_WAIT", "T_BRACE", "T_WATCH", "T_TRAP")]
        if b.v("GSTATE") == 2:
            escapes += 1
            outcome = "ESCAPED"
        else:
            b.wait_until(lambda: b.v("GSTATE") == 1, 900)
            deaths += 1
            near = [(e["type"], e["x"]) for e in (b.enemy(0), b.enemy(1)) if e["type"] >= 0]
            outcome = "died F%d x=%d cause=%s enemies=%s arrow=%d erupt=%d" % (
                b.v("FLOOR") + 1, b.v("HX"), ["guard", "door", "lever", "pace", "trap"][b.v("CAUSE")], near,
                b.s.w(S + 652), b.s.w(S + 656))
        b.wait_until(lambda: b.v("GSTATE") == 0, 400)
        print("   run %2d %s-doors %s-levers tiers d/l/r/w/b/wa/t=%s -> %s" % (run + 1, door, lever, tiers, outcome))
    print("   escapes %d, deaths %d" % (escapes, deaths))
    assert escapes >= 8, "the adapted castle should stay beatable by a careful player"


def main(names):
    if OUT:
        os.makedirs(OUT, exist_ok=True)
    failed = 0
    for name in names:
        fn = SCENARIOS[name]
        print("== %s: %s" % (name, fn.__doc__))
        b = Bot(name)
        try:
            fn(b)
            print("   PASS")
        except AssertionError as e:
            failed += 1
            print("   FAIL:", e)
            b.status("state")
        except RuntimeError as e:
            failed += 1
            print("   CRASH:", e)
    print("%d/%d scenarios passed" % (len(names) - failed, len(names)))
    return failed


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1:] or list(SCENARIOS)) else 0)
