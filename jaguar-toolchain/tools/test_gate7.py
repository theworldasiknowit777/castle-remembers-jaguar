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
import symbols  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COF = os.path.join(ROOT, "gate7_castle", "gate7_castle.cof")
OUT = os.environ.get("JSIM_OUT")

S = 0x1000
SYM = symbols.load()                     # state offsets straight from the source's equ chain
OFF = {k: SYM[k] for k in ("HX", "HY", "HVY", "CLIMB", "FLOOR", "FACING", "GSTATE", "GTIMER", "CAUSE", "SEEN",
                           "NOTES", "RUNS", "WINS", "DEATHS", "T_DOOR", "T_LEVER", "T_RUSH", "T_WAIT", "T_BRACE",
                           "T_WATCH", "T_TRAP", "T_CHEST", "SIDE_DOOR", "SIDE_LEVER", "EXIT_X", "AUTOCLOSE",
                           "SHARDS", "GIFT_X", "GIFT_TAKEN", "FB_PH", "FB_T", "FB_Y", "BLADE_CX", "VOICE_ID")}
_CTR = ("DOORL", "DOORR", "LEVL", "LEVR", "PULLS", "RUSH", "WAIT", "CONF", "AVOID", "TRAPS", "CHESTS", "SKIP")
R = {k: SYM["R_BASE"] + SYM["CTR_" + k] for k in _CTR}
M = {k: SYM["M_BASE"] + SYM["CTR_" + k] for k in _CTR}
LEVERS, DOORS, GATES, ENEMY, FENEMY, FSPIKE = (SYM[k] for k in ("LEVERS", "DOORS", "GATES", "ENEMY", "FENEMY", "FSPIKE"))
AX, ADIR, AON, ET, LADS, CHSTATE, CHTRAP, FBX = (SYM[k] for k in ("AX", "ADIR", "AON", "ET", "LADS", "CHSTATE", "CHTRAP", "FBX"))
GROUND = 372
WALK = 2
LAD = dict(L=6, C=152, R=298)
CHESTX = (180, 261, 123, 266)
T_HOUND = 5
V = {k[2:]: SYM[k] for k in SYM if k.startswith("V_")}
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
        return self.s.w(S + LEVERS + 4 * i), self.s.w(S + LEVERS + 2 + 4 * i)

    def door(self, i):           # i: 0 F1L 1 F1R 2 F3L 3 F3R -> (x, open, lock, passed)
        return tuple(self.s.w(S + DOORS + 8 * i + o) for o in (0, 2, 4, 6))

    def enemy(self, slot):
        b = S + ENEMY + 32 * slot
        return dict(type=self.s.sw(b), x=self.s.sw(b + 2) >> 4, dir=self.s.sw(b + 4), stun=self.s.w(b + 18), chase=self.s.w(b + 16),
                    arm=self.s.w(b + 12), org=self.s.w(b + 14), spd=self.s.w(b + 10))

    def plan_enemy(self, floor, slot):
        b = S + FENEMY + 64 * floor + 32 * slot
        return dict(type=self.s.sw(b), x=self.s.sw(b + 2), min=self.s.sw(b + 6), max=self.s.sw(b + 8),
                    org=self.s.w(b + 14))

    def spike(self, floor, slot):
        b = S + FSPIKE + 16 * floor + 8 * slot
        return dict(x=self.s.w(b), w=self.s.w(b + 2), per=self.s.w(b + 4), org=self.s.w(b + 6))

    def status(self, tag=""):
        print("   [%s] f=%d floor=F%d x=%d y=%d climb=%d gs=%d runs=%d wins=%d deaths=%d cause=%d voice=%d enemies=%s" % (
            tag, self.s.frame, self.v("FLOOR") + 1, self.v("HX"), self.v("HY"), self.v("CLIMB"), self.v("GSTATE"),
            self.v("RUNS"), self.v("WINS"), self.v("DEATHS"), self.v("CAUSE"), self.v("VOICE_ID"),
            [(e["type"], e["x"], e["stun"]) for e in (self.enemy(0), self.enemy(1))]))

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
            if self.v("FLOOR") == 2 and self.v("BLADE_CX"):
                # the blade: only step into its sweep at the start of a safe swing
                cx = self.v("BLADE_CX")
                lo, hi = cx - 30, cx + 14
                nxt = hx + WALK * sgn
                if not (lo < hx < hi) and lo < nxt < hi:
                    ph = self.s.l(S + SYM["RUNT"]) % 120
                    if not (42 <= ph <= 46 or 102 <= ph <= 106):
                        pad.discard(d)
                        pad.discard("up")
            if fight and grounded and self.hound_near(hx):
                # the hound: pick a dodge by trying the moves a careful player could make
                plan = self.hound_plan(sgn, steps=max(1, min(4, abs(x - hx) // WALK)))
                if plan is not None:
                    for p in plan:
                        self.s.run_frames(1, pad=p)
                        if self.v("GSTATE"):
                            return
                    continue
            if fight:
                for slot in (0, 1):
                    e = self.enemy(slot)
                    if e["type"] < 0 or e["stun"]:
                        continue
                    a = (e["x"] - hx) * sgn
                    if e["type"] == T_HOUND:
                        # the hound can't be shoved: jump it with it 14-24 px away and closing,
                        # never onto raised spikes; otherwise keep clear of it
                        closing = (e["x"] - hx) * e["dir"] < 0
                        land_ok = not self.spike_at(hx + 32 * sgn)
                        # jump so the hound passes under during the high part of the jump:
                        # clear of it after 1 frame, past it by frame 14 (closing speed rel px/f)
                        dist = abs(e["x"] - hx)
                        lunge = self.s.w(S + ENEMY + 32 * slot + 28)
                        if 20 < lunge and grounded:
                            pad.discard(d)                  # it is crouching: wait for the lunge
                            if 9.5 + 2.4 <= dist <= 2.4 * 14 - 9 + (30 - lunge) * 0:
                                pass
                            continue
                        lunging = 0 < lunge <= 20
                        sniffing = self.s.w(S + ENEMY + 32 * slot + 26) > 0
                        hound_v = 0 if sniffing else e["spd"] / 16.0 * (1.5 if lunging else 1.0)
                        rel = hound_v + (WALK if a > 0 and d in pad else 0)
                        if grounded and closing and rel > 0 and 9.5 + rel <= dist <= rel * 13 - 9:
                            if a < 0:
                                pad.discard(d)
                            if land_ok or a < 0:
                                pad.add("up")
                            else:
                                pad = {"left" if d == "right" else "right"}
                        elif grounded and abs(e["x"] - hx) < 14 and closing:
                            pad = {"left" if e["x"] > hx else "right"}
                        elif grounded and not closing and 10 <= a <= 18:
                            if land_ok:
                                pad.add("up")           # hop a sniffing / receding hound
                            else:
                                pad.discard(d)
                        continue
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
                if self.s.w(S + AON) and grounded:        # arrow in flight
                    ax = self.s.sw(S + AX) >> 4
                    adir = self.s.sw(S + ADIR)
                    gap = (hx + 8) - (ax + 4)
                    if 0 < gap * adir < 34:
                        pad.add("up")
            self.s.run_frames(1, pad=pad)
            if "a" in pad:
                self.s.run_frames(1, pad=set())  # release (standing still) so the next ACT is a new press
        raise AssertionError("goto(%d) stuck at x=%d" % (x, self.v("HX")))

    def hound_near(self, hx):
        return any(e["type"] == T_HOUND and abs(e["x"] - hx) < 80 for e in (self.enemy(0), self.enemy(1)))

    def hound_threat(self, hx, sgn=0):
        """The hound slot if it is near enough to matter: closing, crouched or
        lunging, or (walking direction sgn) standing in the way ahead."""
        for slot in (0, 1):
            e = self.enemy(slot)
            if e["type"] != T_HOUND or e["stun"]:
                continue
            dist = e["x"] - hx
            closing = dist * e["dir"] < 0
            lunge = self.s.w(S + ENEMY + 32 * slot + 28)
            if abs(dist) < 56 and (closing or lunge) or abs(dist) < 20 or 0 < dist * sgn < 40:
                return slot
        return None

    def hound_plan(self, sgn, horizon=34, steps=4):
        """Look ahead (machine snapshots) like a careful player: walk on, or wait
        k frames walking / standing / backing off and then jump. A move counts
        only if the hero lives through it, ends grounded on the same floor, and
        can still survive the next 30 frames whichever way it then walks. First
        survivor wins (walking on first). None if nothing survives."""
        d, back = ("right", "left") if sgn > 0 else ("left", "right")
        cands = [[{d}] * steps]
        for k in range(0, 24):
            for hold in ({d}, set(), {back}):
                for air in ({d}, set(), {back}):
                    cands.append([hold] * k + [air | {"up"}] + [air] * 17)
        cands += [[{back}] * n for n in (8, 16, 32)] + [[set()] * n for n in (4, 16)]
        snap = self.s.snapshot()
        floor = self.v("FLOOR")

        def lives(pads):
            for p in pads:
                self.s.run_frames(1, pad=p)
                if self.v("GSTATE") or self.v("FLOOR") != floor or self.v("CLIMB"):
                    return False
            return True
        try:
            for plan in cands:
                self.s.restore(snap)
                tail = [set()] * max(0, min(horizon, len(plan) + 8) - len(plan))
                if not (lives(plan + tail) and self.v("HY") == GROUND):
                    continue
                after = self.s.snapshot()
                for cont in ({d}, set(), {back}):
                    self.s.restore(after)
                    if lives([cont] * 30):
                        return plan + tail
        finally:
            self.s.restore(snap)
        return None

    def spike_at(self, hx):
        """Would a hero at x hx stand on spikes here (any spike, raised or not)?"""
        for lo, hi in self.spikes_on(self.v("FLOOR")):
            if lo - 8 < hx < hi - 8:
                return True
        return False

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
            if self.v("GSTATE") or (self.v("FLOOR") == 0 and start != 0 and self.v("CLIMB") == 0):
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

    def seed(self, counters=None, pressure=None):
        """Seed the castle's memory (x100 counters, per-category pressure) as if
        earlier runs had happened; the next death rebuilds the castle from it."""
        for k, v in (counters or {}).items():
            self.s.poke_w(S + M[k], v)
        for cat, v in (pressure or {}).items():
            self.s.poke_w(S + SYM["P_BASE"] + 2 * SYM["C_" + cat], v)
        if self.v("RUNS") == 0:
            self.s.poke_w(S + SYM["RUNS"], 1)

    def die_on_skull(self):
        """Die to the F2 patroller to end the run and rebuild."""
        self.choice_floor(0, "L")
        self.climb("up")
        e = self.enemy(0)
        self.goto(e["x"], limit=900, fight=False)
        self.wait_until(lambda: self.v("GSTATE") == 1, 600)
        self.die_and_rebuild()

    def die_and_rebuild(self):
        self.wait_until(lambda: self.v("GSTATE") == 0, 400)

    # ---- a full route: side 'L' or 'R' on choice floors, lever side on lever floors
    def run_route(self, door_side="L", lever_side="L", shove=False, chests=False):
        """Floor by floor to the exit. A long ladder may skip F2, so the
        route follows whatever floor the hero actually reaches. Stops as
        soon as the run ends (death or escape), even inside a helper."""
        assert self.v("FLOOR") == 0
        runs0 = self.v("RUNS")
        for _ in range(6):
            fl = self.v("FLOOR")
            if fl == 4 or self.v("GSTATE") or self.v("RUNS") != runs0:
                break
            if fl in (0, 2):
                self.choice_floor(fl, door_side, chests)
            else:
                self.lever_floor(fl, lever_side, shove, chests)
            if self.v("GSTATE") or self.v("RUNS") != runs0:
                return
            self.climb("up")
            if self.v("RUNS") != runs0:
                return
            assert self.v("FLOOR") > fl or self.v("GSTATE"), "expected to climb past F%d" % (fl + 1)
        if self.v("GSTATE") or self.v("RUNS") != runs0:
            return
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
        """Don't start climbing with a guard about to step onto the ladder (or,
        for the hound, unless the climb is seen to get away in time)."""
        lx = self.v("HX")
        for _ in range(240):
            if self.v("GSTATE"):
                return
            if self.v("FLOOR") in (1, 3) and lx == LAD["C"] and not self.s.w(S + GATES + (0 if self.v("FLOOR") == 1 else 4)):
                return                                  # the gate slammed: the lever floor re-opens it
            if self.v("HX") != lx and self.v("HY") == GROUND:
                self.goto(lx)                           # back to the ladder after a dodge
                continue
            close = [e for e in (self.enemy(0), self.enemy(1))
                     if e["type"] >= 0 and not e["stun"] and (abs(e["x"] - lx) < 20 or
                                                             e["type"] == T_HOUND)]
            if not close:
                return
            if close[0]["type"] == T_HOUND:
                if self.v("HY") != GROUND or self.climb_plan(close[0]):
                    return                              # (the climb itself follows)
                continue                                # dodged off the ladder: walk back, retry
            self.face_and_shove(close[0])

    def climb_plan(self, hound):
        """At a ladder foot with the hound about: wait (for real, 3 frames at a
        time) until a climb is seen to get above its reach alive; step away
        if standing here would be fatal. True when climbing now is safe."""
        for _ in range(60):
            if self.v("GSTATE"):
                return False
            if self.climb_survives():
                return True
            snap = self.s.snapshot()
            ok = True
            for _ in range(12):                         # can we afford to stand 3 frames (and a bit)?
                self.s.run_frames(1)
                if self.v("GSTATE"):
                    ok = False
                    break
            self.s.restore(snap)
            if ok:
                self.s.run_frames(3)
                continue
            e = [x for x in (self.enemy(0), self.enemy(1)) if x["type"] == T_HOUND]
            sgn = 1 if e and e[0]["x"] > self.v("HX") else -1
            for p in self.hound_plan(sgn, steps=1) or [set()]:
                self.s.run_frames(1, pad=p)
            return False                                # off the ladder now: caller walks back
        return False

    def climb_survives(self):
        """Look ahead: would climbing from here, starting now, get off this floor alive?"""
        snap = self.s.snapshot()
        start = self.v("FLOOR")
        try:
            for i in range(200):
                self.s.run_frames(1, pad={"up"})
                if self.v("GSTATE"):
                    return False
                if self.v("FLOOR") != start or (self.v("CLIMB") and self.v("HY") <= GROUND - 44):
                    return True                         # off the floor, or above the hound's reach
                if i == 3 and not self.v("CLIMB"):
                    return False                        # not on a ladder (or the gate is shut)
            return False
        finally:
            self.s.restore(snap)

    def face_and_shove(self, e):
        """Turn toward a guard (one step) and shove it."""
        d = "right" if e["x"] > self.v("HX") else "left"
        self.frames(1, d)
        self.frames(1, "a")
        self.frames(1)

    def chest(self, floor):
        """Open this floor's chest; if it was trapped, run from the flames."""
        if self.s.w(S + CHSTATE + 2 * floor) or self.v("GSTATE"):
            return
        x = CHESTX[floor]
        self.goto(x)
        if self.v("GSTATE"):
            return
        self.act()
        if self.s.w(S + ET):
            self.goto(x - 52 if x > 160 else x + 52)
            self.wait_until(lambda: self.s.w(S + ET) == 0 or self.v("GSTATE"), 200)

    def choice_floor(self, floor, side, chests=False):
        hx = self.v("HX")
        if hx in (LAD["L"], LAD["R"]):              # arrived by the long ladder: already in a corridor
            if chests:
                pass                                # the chest is behind the door; leave it
            self.wait_safe_climb()
            return
        if chests:
            self.chest(floor)
        di = (2 if floor == 2 else 0) + (0 if side == "L" else 1)
        x, opened, lock, _ = self.door(di)
        if lock:
            side = "R" if side == "L" else "L"
            di ^= 1
            x, opened, lock, _ = self.door(di)
        if not opened:
            self.goto(x + 8 if side == "L" else x - 16)
            for _ in range(4):                      # ACT may shove a guard first
                self.act()
                if self.door(di)[1] or self.v("GSTATE"):
                    break
                self.goto(x + 8 if side == "L" else x - 16)
            if self.v("GSTATE"):
                return
            assert self.door(di)[1] == 1, "F%d door did not open" % (floor + 1)
        self.through_corridor(floor, side)

    def lever_floor(self, floor, side, shove, chests=False):
        for _ in range(3):                          # a slammed gate (wait tier) can be re-opened
            self.lever_floor_once(floor, side, shove, chests)
            chests = False
            if self.v("GSTATE") or self.v("FLOOR") != floor or self.s.w(S + GATES + (0 if floor == 1 else 4)):
                return
        assert False, "F%d gate kept slamming shut" % (floor + 1)

    def lever_floor_once(self, floor, side, shove, chests=False):
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
                if self.v("GSTATE") or self.lev(li)[1] != before or self.s.w(S + GATES + (0 if floor == 1 else 4)):
                    break
            if self.v("GSTATE"):
                return
            eff, state = self.lev(li)
            if self.s.w(S + GATES + (0 if floor == 1 else 4)):
                break
            # trapped lever: run to the wall side, out of the flames, and let them burn out
            if self.s.w(S + ET):
                self.goto(34 if sd == "L" else 270)
                self.wait_until(lambda: self.s.w(S + ET) == 0 or self.v("GSTATE"), 200)
        assert self.s.w(S + GATES + (0 if floor == 1 else 4)) == 1, "gate did not open"
        if chests:
            self.chest(floor)
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
    assert b.lev(0)[1] == 1 and b.s.w(S + GATES) == 1, "lever should open the gate"
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
    """Never waiting is noticed: a blade on F3 (t1), an ambush at the F3 ladder top (t2), spikes by the F2 ladder (t3)."""
    b.run_route("R", "R")
    b.wait_until(lambda: b.v("GSTATE") == 0, 400)
    print("   after one fast escape: T_RUSH=%d rush=%d wait=%d blade=%d" % (
        b.v("T_RUSH"), b.m("RUSH"), b.m("WAIT"), b.v("BLADE_CX")))
    assert b.v("T_RUSH") >= 1 and b.v("BLADE_CX") == 188
    b.seed({"RUSH": 900, "WAIT": 0}, {"PACE": 3})
    b.die_on_skull()
    print("   seeded rusher: T_RUSH=%d" % b.v("T_RUSH"))
    assert b.v("T_RUSH") == 3
    assert b.plan_enemy(2, 1)["org"] == 3, b.plan_enemy(2, 1)          # ambush (origin: pace)
    assert b.spike(1, 0)["x"] == 114 and b.spike(1, 1)["x"] == 190     # spikes flank the F2 ladder


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
def chest_shard(b):
    """A real chest gives a memory shard (HUD), then reads empty; it counts as opened."""
    b.chest(0)
    assert b.v("SHARDS") == 1 and b.s.w(S + CHSTATE) == 1, (b.v("SHARDS"), b.s.w(S + CHSTATE))
    assert b.r("CHESTS") == 1 and b.v("VOICE_ID") == V["SHARD"], (b.r("CHESTS"), b.v("VOICE_ID"))
    b.act()
    assert b.v("VOICE_ID") == V["EMPTY"]
    b.shot("chest_open")


@scenario
def greed_memory(b):
    """Opening every chest makes the castle greedy-aware: F4 (then F2, F1) chests turn trap; F3 stays real."""
    b.run_route("L", "L", chests=True)
    assert b.v("GSTATE") == 2, "should escape"
    b.wait_until(lambda: b.v("GSTATE") == 0, 400)
    print("   after escape: chests=%d skipped=%d T_CHEST=%d traps=%s" % (
        b.m("CHESTS"), b.m("SKIP"), b.v("T_CHEST"), [b.s.w(S + CHTRAP + 2 * i) for i in range(4)]))
    assert b.v("T_CHEST") >= 1 and b.s.w(S + CHTRAP + 6) == 1 and b.s.w(S + CHTRAP + 4) == 0
    # skip chests this time: escaping still works, and skipped chests are counted
    b.run_route("R", "R")
    assert b.v("GSTATE") == 2
    b.wait_until(lambda: b.v("GSTATE") == 0, 400)
    assert b.m("SKIP") > 0, b.m("SKIP")


@scenario
def trapped_chest(b):
    """A trapped chest (red clasp) erupts; standing in it kills with cause 'chest'."""
    b.seed({"CHESTS": 900}, {"CHEST": 3})        # (an unused category loses 1 pressure on a death)
    b.die_on_skull()
    assert b.v("T_CHEST") == 3 and b.s.w(S + CHTRAP) == 1, (b.v("T_CHEST"), b.s.w(S + CHTRAP))
    b.goto(CHESTX[0])
    b.act()
    assert b.s.w(S + ET) and b.s.w(S + SYM["ECAUSE"]) == SYM["C_CHEST"]
    assert b.v("VOICE_ID") == V["GREEDRUN"]
    b.frames(40)                                  # stand in it
    assert b.v("GSTATE") == 1 and b.v("CAUSE") == SYM["C_CHEST"], (b.v("GSTATE"), b.v("CAUSE"))


@scenario
def long_ladder(b):
    """Door tier 2: the avoided side's F1 ladder is gold and runs straight to F3 (skips the lever floor)."""
    b.seed({"DOORL": 400}, {"DOOR": 1})
    b.die_on_skull()
    assert b.v("T_DOOR") >= 2 and b.v("SIDE_DOOR") == -1
    kinds = [b.s.w(S + LADS + o) for o in (6, 22, 30)]
    assert kinds == [5, 7, 3], kinds
    b.choice_floor(0, "R")
    b.shot("long_ladder_f1")
    b.climb("up")
    assert b.v("FLOOR") == 2 and b.v("HX") == LAD["R"], (b.v("FLOOR"), b.v("HX"))
    # and it can be left at F2: climb down, step off there
    for _ in range(300):
        b.frames(1, "down")
        if b.v("FLOOR") == 1 and b.v("CLIMB") == 2 and b.v("HY") <= GROUND + 4:
            break
    b.frames(3)
    assert b.v("FLOOR") == 1 and b.v("CLIMB") == 0 and b.v("HY") == GROUND, (b.v("FLOOR"), b.v("CLIMB"), b.v("HY"))


@scenario
def gift_shard(b):
    """The open F3 gift door hides a floating shard: a hop takes it."""
    b.seed({"DOORL": 400}, {"DOOR": 1})
    b.die_on_skull()
    assert b.v("GIFT_X") == 280, b.v("GIFT_X")
    b.choice_floor(0, "R")
    b.climb("up")                                 # the long ladder lands in F3's right corridor
    assert b.v("FLOOR") == 2
    b.goto(276)
    assert b.v("SHARDS") == 0
    b.frames(1, "up")
    b.frames(30)
    assert b.v("SHARDS") == 1 and b.v("GIFT_TAKEN") == 1 and b.v("VOICE_ID") == V["GIFT"]


@scenario
def falling_masonry(b):
    """Waiters get cracked masonry on F4: standing under it shakes it loose; stepping away is safe."""
    b.seed({"WAIT": 600}, {"PACE": 1})
    b.die_on_skull()
    assert b.v("T_WAIT") >= 1 and b.s.w(S + FBX + 6) == 112, (b.v("T_WAIT"), b.s.w(S + FBX + 6))
    b.choice_floor(0, "L")
    b.climb("up")
    b.lever_floor(1, "L", False)
    b.climb("up")
    b.choice_floor(2, "L")
    b.climb("up")
    assert b.v("FLOOR") == 3
    for slot in (0, 1):                           # isolate the masonry from the F4 patrol
        b.s.poke_w(S + ENEMY + 32 * slot, 0xFFFF)
    b.goto(112)
    b.frames(46)
    assert b.v("FB_PH") == 1 and b.v("VOICE_ID") == V["CEILING"], (b.v("FB_PH"), b.v("VOICE_ID"))
    b.shot("masonry_warning")
    b.goto(150)                                   # step clear while it shakes
    b.wait_until(lambda: b.v("FB_PH") == 3, 120)
    assert b.v("GSTATE") == 0, "stepping away should be safe"
    b.wait_until(lambda: b.v("FB_PH") == 0, 200)
    b.goto(112)
    b.frames(140)                                 # stay put: it comes down
    assert b.v("GSTATE") == 1 and b.v("CAUSE") == SYM["C_PACE"], (b.v("GSTATE"), b.v("CAUSE"))


@scenario
def swinging_blade(b):
    """Rushers get a blade on F3: crossing on the back-swing is safe, walking into it is not."""
    b.seed({"RUSH": 600}, {"PACE": 1})
    b.die_on_skull()
    assert b.v("BLADE_CX") == 188
    b.choice_floor(0, "L")
    b.climb("up")
    b.lever_floor(1, "L", False)
    b.climb("up")
    assert b.v("FLOOR") == 2
    b.shot("blade")
    b.choice_floor(2, "R")                        # the right route crosses the blade
    assert b.v("GSTATE") == 0 and b.v("HX") == LAD["R"], "timed crossing should survive"
    # now stand in the middle of the sweep: the low swing must find you
    b.goto(180, fight=False)
    b.wait_until(lambda: b.v("GSTATE") == 1, 240)
    assert b.v("CAUSE") == SYM["C_PACE"] and b.v("VOICE_ID") == V["BLADE"]


@scenario
def castle_hound(b):
    """Shove-happy players meet the Castle Hound: it can't be shoved, but it can be jumped."""
    b.seed({"CONF": 600}, {"GUARD": 2})
    b.die_on_skull()
    assert b.v("T_BRACE") >= 2 and b.plan_enemy(1, 0)["type"] == T_HOUND, (b.v("T_BRACE"), b.plan_enemy(1, 0))
    b.choice_floor(0, "L")
    b.climb("up")
    e = b.enemy(0)
    assert e["type"] == T_HOUND
    b.shot("hound")
    b.goto(88, fight=False)                       # just outside its patrol (100-204)
    for _ in range(600):                          # face it and try to shove when it is close
        e = b.enemy(0)
        d = e["x"] - b.v("HX")
        if 10 < abs(d) < 22:
            b.frames(1, "right" if d > 0 else "left")
            b.frames(1, "a")
            break
        b.frames(1)
    assert b.v("VOICE_ID") == V["HOUND"] and b.enemy(0)["stun"] == 0
    b.frames(1, "up")                             # hop it
    b.frames(30)
    assert b.v("GSTATE") == 0, "jumping the hound should be safe"


@scenario
def voice_hooks(b):
    """Castle voice ids fire for canon hints (text waits for a font object)."""
    b.choice_floor(0, "L")
    b.climb("up")
    b.goto(LAD["C"])
    b.frames(1, "up")
    assert b.v("VOICE_ID") == V["GATESHUT"], b.v("VOICE_ID")
    b.goto(LEVER["L"] - 4)
    b.act()
    assert b.lev(0)[1] == 1
    b.act()
    assert b.v("VOICE_ID") == V["GATEOPEN"], b.v("VOICE_ID")


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
        runs_before = b.v("RUNS")
        try:
            b.run_route(door, lever, shove=rnd.random() < 0.5, chests=rnd.random() < 0.4)
        except AssertionError as e:
            if b.v("GSTATE") == 0:
                raise AssertionError("run %d stuck alive (softlock?): %s" % (run + 1, e))
        tiers = [b.v(k) for k in ("T_DOOR", "T_LEVER", "T_RUSH", "T_WAIT", "T_BRACE", "T_WATCH", "T_TRAP")]
        if b.v("GSTATE") == 2:
            escapes += 1
            outcome = "ESCAPED"
        elif b.v("RUNS") != runs_before and b.v("GSTATE") == 0:
            deaths += 1                                  # died and rebuilt while the bot was busy
            outcome = "died (noticed after rebuild) cause=%s" % ["guard", "door", "lever", "pace", "trap", "chest"][b.v("CAUSE")]
            print("   run %2d %s-doors %s-levers -> %s" % (run + 1, door, lever, outcome))
            continue
        else:
            b.wait_until(lambda: b.v("GSTATE") == 1, 900)
            deaths += 1
            near = [(e["type"], e["x"]) for e in (b.enemy(0), b.enemy(1)) if e["type"] >= 0]
            outcome = "died F%d x=%d cause=%s enemies=%s arrow=%d erupt=%d" % (
                b.v("FLOOR") + 1, b.v("HX"), ["guard", "door", "lever", "pace", "trap"][b.v("CAUSE")], near,
                b.s.w(S + AON), b.s.w(S + ET))
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
