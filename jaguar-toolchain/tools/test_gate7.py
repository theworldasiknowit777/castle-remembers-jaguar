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
                           "SHARDS", "GIFT_X", "GIFT_TAKEN", "FB_PH", "FB_T", "FB_Y", "BLADE_CX", "MSG_ID", "MSG_PRI", "MSG_T", "MSG_ARG", "OBS_ID")}
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
V = {k[5:]: SYM[k] for k in SYM if k.startswith("MSGX_")}   # gameplay-lane message ids
MSGIDS = {SYM[k]: k for k in SYM if k.startswith(("MSG_", "MSGX_")) and k in symbols.load(
    os.path.join(ROOT, "gate7_castle", "msg_ids.inc"))}
LEVER = dict(L=80, R=232)
DOOR = dict(L=94, R=218)


class Bot:
    def __init__(self, name):
        self.s = JagSim(COF)
        self.name = name
        self.shots = 0
        self.s.boot_wait()

    # ---- state
    def v(self, k):
        return self.s.sw(S + OFF[k])

    def said(self, mid):
        """Is message mid showing, or waiting its turn in the castle-voice queue?"""
        if self.v("MSG_ID") == mid:
            return True
        q = S + SYM["MSG_Q"]
        return any(self.s.w(q + 8 * i + 2) and self.s.w(q + 8 * i) == mid for i in range(SYM["MSG_QN"]))

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
        print("   [%s] f=%d floor=F%d x=%d y=%d climb=%d gs=%d runs=%d wins=%d deaths=%d cause=%d msg=%d enemies=%s" % (
            tag, self.s.frame, self.v("FLOOR") + 1, self.v("HX"), self.v("HY"), self.v("CLIMB"), self.v("GSTATE"),
            self.v("RUNS"), self.v("WINS"), self.v("DEATHS"), self.v("CAUSE"), self.v("MSG_ID"),
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
    assert b.r("CHESTS") == 1 and b.said(V["SHARD"]), (b.r("CHESTS"), b.v("MSG_ID"))
    b.act()
    assert b.said(V["EMPTY"])
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
    assert b.said(V["TRAP_CHEST"])
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
    assert b.v("SHARDS") == 1 and b.v("GIFT_TAKEN") == 1 and b.said(V["GIFT_SHARD"])


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
    assert b.v("FB_PH") == 1 and b.said(V["CEILING"]), (b.v("FB_PH"), b.v("MSG_ID"))
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
    assert b.v("CAUSE") == SYM["C_PACE"] and b.said(V["D_BLADE"])


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
    assert b.said(V["HOUND"]) and b.enemy(0)["stun"] == 0
    b.frames(1, "up")                             # hop it
    b.frames(30)
    assert b.v("GSTATE") == 0, "jumping the hound should be safe"


@scenario
def voice_hooks(b):
    """Castle voice ids fire for canon hints."""
    b.choice_floor(0, "L")
    b.climb("up")
    b.goto(LAD["C"])
    b.frames(1, "up")
    assert b.said(V["GATE_SHUT"]), b.v("MSG_ID")
    b.goto(LEVER["L"] - 4)
    b.act()
    assert b.lev(0)[1] == 1
    b.act()
    assert b.said(V["GATE_OPEN"]), b.v("MSG_ID")


# ---------------------------------------------------------------- castle voice (V6)
ELL = "\x85"                                         # Kimi's ellipsis glyph byte
FONT_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,:;!?-+/%() #" + ELL)
MT = {k: SYM[k] for k in ("MT_PROMPT", "MT_WARN", "MT_TITLE", "MT_OBSERVE", "MT_EVENT")}


def message_table():
    """id -> (priority, frames, line1, line2) from the generated messages.inc."""
    import re
    src = open(os.path.join(ROOT, "gate7_castle", "messages.inc"), encoding="utf-8").read()
    strings = {"msg_none": ""}
    for label, data in re.findall(r"^(\w+):\s*\n\s+dc\.b\s+([\d,]+)", src, re.M):
        strings[label] = "".join(chr(int(v)) for v in data.split(",")).split("\0")[0]
    body = src[src.index("msgtab:"):src.index("msgtab_end:")]
    rows = re.findall(r"dc\.w\s+(\w+),(\d+)\s*\n\s*dc\.l\s+(\w+),(\w+)", body)
    return {i: (SYM[ty], int(fr), strings[l1], strings[l2]) for i, (ty, fr, l1, l2) in enumerate(rows)}


def expand(line, arg):
    """The renderer's '#' rule: the number in decimal, no leading zeros."""
    return line.replace("#", str(arg))


def at_rebuild(b, cause, ctr=None, won=False, arrow=False, floor=0, idle=None):
    """End the run now (as death by cause, or an escape) with this run's
    counters, and let the castle rebuild: the observation id it chose."""
    for k, v in (ctr or {}).items():
        b.s.poke_w(S + R[k], v)
    if idle is not None:                                 # (idle, runt) frames: pace of this run
        b.s.uc.mem_write(S + SYM["IDLE"], idle[0].to_bytes(4, "big"))
        b.s.uc.mem_write(S + SYM["RUNT"], idle[1].to_bytes(4, "big"))
    b.s.poke_w(S + SYM["CAUSE"], SYM["C_" + cause] if cause else 0)
    b.s.poke_w(S + SYM["KILL_ARROW"], 1 if arrow else 0)
    b.s.poke_w(S + SYM["DEATH_FLOOR"], floor)
    b.s.poke_w(S + SYM["GSTATE"], 2 if won else 1)
    b.s.poke_w(S + SYM["GTIMER"], 1)
    runs = b.v("RUNS")
    b.wait_until(lambda: b.v("RUNS") != runs and b.v("GSTATE") == 0, 10)
    return b.v("OBS_ID")


@scenario
def msg_width(b):
    """Every message line fits the 320 px band (53 glyphs, '#' as 3 digits) with Kimi's V6 glyphs."""
    table = message_table()
    assert len(table) == SYM["MSG_COUNT"], (len(table), SYM["MSG_COUNT"])
    for i, (ty, frames, l1, l2) in table.items():
        assert ty in MT.values() and frames > 0, (MSGIDS.get(i), ty, frames)
        for line in (l1, l2):
            assert len(expand(line, 999)) <= SYM["MSG_LINE_MAX"], (MSGIDS.get(i), line)
            assert set(line) <= FONT_CHARS, (MSGIDS.get(i), set(line) - FONT_CHARS)
    print("   %d messages (%d Kimi), longest line %d glyphs" % (
        len(table), SYM["MSGX_" + "GATE_SHUT"], max(max(len(r[2]), len(r[3])) for r in table.values())))


@scenario
def msg_observations(b):
    """Canon describeObservation: each death cause / escape habit -> its own MSG_O_* id, deterministically."""
    cases = [
        ("door left", dict(cause="DOOR", ctr={"DOORL": 2, "DOORR": 0}), "MSG_O_DOOR_L"),
        ("door right", dict(cause="DOOR", ctr={"DOORL": 0, "DOORR": 2}), "MSG_O_DOOR_R"),
        ("lever left", dict(cause="LEVER", ctr={"LEVL": 1, "LEVR": 0}), "MSG_O_LEVER_L"),
        ("lever right", dict(cause="LEVER", ctr={"LEVL": 0, "LEVR": 1}), "MSG_O_LEVER_R"),
        ("rush", dict(cause="PACE", idle=(0, 2000)), "MSG_O_RUSH"),
        ("wait", dict(cause="PACE", idle=(1500, 2000)), "MSG_O_WAIT"),
        ("trap", dict(cause="TRAP"), "MSG_O_TRAP"),
        ("chest", dict(cause="CHEST"), "MSG_O_CHEST"),
        ("guard F3", dict(cause="GUARD", floor=2), "MSG_O_GUARD"),
        ("arrow F4", dict(cause="GUARD", floor=3, arrow=True), "MSG_O_ARROW"),
    ]
    for name, kw, want in cases:
        got = [at_rebuild(Bot("obs"), **kw) for _ in range(2)]
        print("   %-11s -> %s" % (name, MSGIDS.get(got[0], got[0])))
        assert got[0] == SYM[want], (name, MSGIDS.get(got[0]), want)
        assert got[1] == got[0], (name, "not deterministic", got)
    # the guard/arrow line carries the floor number for its '#'
    g = Bot("arg")
    at_rebuild(g, "GUARD", floor=2)
    g.wait_until(lambda: g.v("MSG_ID") == SYM["MSG_O_GUARD"], 400)
    assert g.v("MSG_ARG") == 3, g.v("MSG_ARG")
    # escapes: the habit the castle now presses hardest (canon CATS order on ties)
    for name, pres, fam in (("doors", {"DOOR": 2}, ("MSG_O_WIN_DOOR_L", "MSG_O_WIN_DOOR_R")),
                            ("levers", {"LEVER": 2}, ("MSG_O_WIN_LEVER_L", "MSG_O_WIN_LEVER_R")),
                            ("traps", {"TRAP": 2}, ("MSG_O_WIN_TRAP",)),
                            ("chests", {"CHEST": 3}, ("MSG_O_WIN_CHEST",))):
        got = []
        for _ in range(2):
            w = Bot("win")
            w.seed({"DOORL": 400, "LEVL": 400, "TRAPS": 300, "CHESTS": 900}, pres)
            got.append(at_rebuild(w, None, ctr={"DOORL": 1, "LEVL": 1}, won=True, idle=(300, 2000)))
            tiers = dict(door=w.v("T_DOOR"), lever=w.v("T_LEVER"), trap=w.v("T_TRAP"), chest=w.v("T_CHEST"))
        print("   win %-7s tiers %s -> %s" % (name, tiers, MSGIDS.get(got[0], got[0])))
        assert got[0] == got[1], (name, "not deterministic", got)
        assert MSGIDS.get(got[0]) in fam or tiers[name[:-1]] < max(tiers.values()), (name, MSGIDS.get(got[0]), tiers)


@scenario
def msg_rebuild_sequence(b):
    """Death -> cause line -> OBSERVED/REBUILD -> observation -> watched-N whisper -> floor title, by priority."""
    e = b.enemy(0)
    b.choice_floor(0, "L")
    b.climb("up")
    seq = []
    for _ in range(3000):
        if b.v("GSTATE") == 0 and b.v("RUNS") == 0:
            e = b.enemy(0)
            b.s.run_frames(1, pad={"right" if e["x"] > b.v("HX") else "left"})
        else:
            b.s.run_frames(1)
        m = b.v("MSG_ID")
        if m >= 0 and (not seq or seq[-1][0] != m):
            seq.append((m, b.v("MSG_PRI"), b.v("MSG_ARG")))
        if b.v("RUNS") == 1 and b.v("MSG_PRI") == 0 and b.v("MSG_T") == 0 and len(seq) >= 5 \
                and b.s.w(S + SYM["MSG_Q"] + 2) == 0:
            break
    names = [MSGIDS.get(m, m) for m, _, _ in seq]
    print("   " + " > ".join(names))
    i = names.index("MSGX_D_GUARD")
    after = names[i:]
    assert after[1] == "MSG_OBSERVED", after
    assert after[2] == "MSG_O_GUARD", after
    assert after[3] == "MSG_WATCHED1", after
    assert "MSG_F1" in after[4:], after
    pris = [p for _, p, _ in seq[i + 1:]]
    assert pris == sorted(pris, reverse=True), ("queue must drain highest priority first", pris)


@scenario
def msg_priority(b):
    """A prompt cannot interrupt a title; the title expires exactly on time; then the prompt shows; death interrupts anything."""
    assert b.v("MSG_ID") == SYM["MSG_F1"] and b.v("MSG_PRI") == MT["MT_TITLE"], MSGIDS.get(b.v("MSG_ID"))
    b.goto(DOOR["L"] + 8)                                # beside a shut door: a prompt wants to show
    assert b.v("MSG_ID") == SYM["MSG_F1"], "prompt must not interrupt a title"
    left = b.v("MSG_T")
    b.frames(left - 1)
    assert b.v("MSG_ID") == SYM["MSG_F1"]
    b.frames(1)
    assert b.v("MSG_ID") == SYM["MSG_P_OPEN"] and b.v("MSG_PRI") == MT["MT_PROMPT"], MSGIDS.get(b.v("MSG_ID"))
    b.goto(152)
    b.frames(10)
    assert b.v("MSG_ID") == -1 and b.v("MSG_PRI") == 0, "a prompt lapses once out of reach"
    b.choice_floor(0, "L")
    b.climb("up")
    assert b.v("MSG_ID") == SYM["MSG_F2"], MSGIDS.get(b.v("MSG_ID"))
    e = b.enemy(0)
    b.goto(e["x"], limit=900, fight=False)
    b.wait_until(lambda: b.v("GSTATE") == 1, 600)
    assert b.v("MSG_PRI") == MT["MT_EVENT"] and b.v("MSG_ID") == V["D_GUARD"], MSGIDS.get(b.v("MSG_ID"))


@scenario
def msg_events(b):
    """Gate slam: a gameplay warning that waits behind the floor title and then shows; same event, same id."""
    ids = []
    for _ in range(2):
        w = Bot("ev")
        w.seed({"WAIT": 900}, {"PACE": 2})
        w.die_on_skull()                                 # wait tier: gates slam
        assert w.v("AUTOCLOSE"), "wait tier should arm the slam"
        w.choice_floor(0, "L")
        w.climb("up")
        w.goto(LEVER["L"] - 4)
        w.act()
        assert w.s.w(S + GATES), "gate should open"
        for _ in range(900):
            w.frames(1)
            if w.said(V["SLAM"]):
                break
        assert w.said(V["SLAM"]) and not w.s.w(S + GATES), "the slam should be announced"
        w.wait_until(lambda: w.v("MSG_ID") == V["SLAM"], 900)
        assert w.v("MSG_PRI") == MT["MT_WARN"]
        ids.append(w.v("MSG_ID"))
    assert ids[0] == ids[1]
    print("   gate slam -> %s (warning), both runs" % MSGIDS[ids[0]])


@scenario
def msg_digits(b):
    """'#' becomes the number: the watched-N whisper carries RUNS (and renders it, text build)."""
    for runs in (1, 7, 12):
        t = Bot("dig")
        t.s.poke_w(S + SYM["RUNS"], runs - 1)
        at_rebuild(t, "GUARD")
        t.wait_until(lambda: t.v("MSG_ID") in (SYM["MSG_WATCHED1"], SYM["MSG_WATCHEDN"]), 600)
        want = "MSG_WATCHED1" if runs == 1 else "MSG_WATCHEDN"
        assert MSGIDS[t.v("MSG_ID")] == want and t.v("MSG_ARG") == runs, (runs, MSGIDS[t.v("MSG_ID")], t.v("MSG_ARG"))
        line = message_table()[t.v("MSG_ID")][3]
        print("   runs %2d -> %s" % (runs, expand(line, runs).replace(ELL, "...")))
    for arg, out in ((0, "0"), (7, "7"), (12, "12"), (100, "100"), (305, "305")):
        assert expand("#", arg) == out


def _text_build(tag):
    """Assemble gate7_castle.s (text band always on since Checkpoint B) into the temp dir."""
    import subprocess, tempfile
    import mkfont
    glyphs, table = mkfont.main()
    out = os.path.join(tempfile.gettempdir(), "g7_%s.cof" % tag)
    obj = out[:-4] + ".o"
    bindir = os.environ.get("JAG_BIN", r"C:/Users/Owner/.bob/playground/jaguar-toolchain/bin")
    cwd = os.path.join(ROOT, "gate7_castle")
    subprocess.run([os.path.join(bindir, "rmac.exe"), "-fb", "-m68000", "-o", obj, "gate7_castle.s"],
                   cwd=cwd, check=True, capture_output=True)
    subprocess.run([os.path.join(bindir, "rln.exe"), "-a", "802000", "r", "r", "-e", "-o", out, obj],
                   cwd=cwd, check=True, capture_output=True)
    return out, glyphs, table


def _reference_band(line1, line2, arg, glyphs, table, face, relief):
    """What draw_text must produce: 320x20, centred, relief at (+1,+1) under the face."""
    band = [[0] * 320 for _ in range(20)]
    for text, top in ((expand(line1, arg), 1), (expand(line2, arg), 11)):
        x0 = (320 - len(text) * 6) // 2
        for col, off in ((relief, 1), (face, 0)):
            for k, ch in enumerate(text):
                gi = table[ord(ch) & 0xFF]
                if gi == 0xFF:
                    continue
                for r, byte in enumerate(glyphs[gi]):
                    bits = int(byte, 16)
                    for c in range(5):
                        if bits & (1 << (4 - c)):
                            band[top + r + off][x0 + k * 6 + c + off] = col
    return band


def _text_bot(cof):
    tb = Bot.__new__(Bot)
    tb.s, tb.name, tb.shots = JagSim(cof), "text", 0
    tb.s.boot_wait()
    return tb


def _check_band(tb, glyphs, table):
    tb.wait_until(lambda: tb.s.w(S + SYM["MSG_DPH"]) == 0 and tb.s.w(S + SYM["MSG_DIRTY"]) == 0, 120)
    fe = symbols.load(os.path.join(ROOT, "gate7_castle", "font_eq.inc"))
    m = tb.v("MSG_ID")
    _, _, l1, l2 = message_table()[m]
    want = _reference_band(l1, l2, tb.v("MSG_ARG"), glyphs, table, fe["KFONT_FACE"], fe["KFONT_RELIEF"])
    got = tb.s.uc.mem_read(SYM["TEXTBUF"], 320 * 20 * 2)
    diff = sum(1 for r in range(20) for x in range(320)
               if int.from_bytes(got[(r * 320 + x) * 2:(r * 320 + x) * 2 + 2], "big") != want[r][x])
    assert diff == 0, "%s: %d text pixels differ from the reference" % (MSGIDS.get(m), diff)
    return expand(l1, tb.v("MSG_ARG")), expand(l2, tb.v("MSG_ARG")), sum(1 for row in want for v in row if v)


@scenario
def msg_text_render(b):
    """(Checkpoint B build) draw_text matches the Python reference pixel for pixel: title, prompt, whisper with digits."""
    cof, glyphs, table = _text_build("text")
    tb = _text_bot(cof)
    tb.frames(2)
    shown = [_check_band(tb, glyphs, table)]             # F1 title
    tb.goto(DOOR["L"] + 8)
    tb.frames(tb.v("MSG_T") + 2)
    shown.append(_check_band(tb, glyphs, table))         # the door prompt
    tb.s.poke_w(S + SYM["RUNS"], 11)
    at_rebuild(tb, "GUARD", floor=1)
    tb.wait_until(lambda: tb.v("MSG_ID") == SYM["MSG_WATCHEDN"], 900)
    tb.frames(2)
    shown.append(_check_band(tb, glyphs, table))         # "...it has watched you 12 times."
    for l1, l2, n in shown:
        print("   pixel-exact: %-28s | %-34s (%d px)" % (l1.replace(ELL, "..."), l2.replace(ELL, "..."), n))
        if OUT:
            tb.shot("text")


@scenario
def hud_states(b):
    """The six-category memory row: icon lit/dim + pips = tier for every category and tier, flash ring, read-only."""
    import mkfont
    cols, flash, icons = mkfont.main_hud()
    cats = ("T_DOOR", "T_LEVER", "T_RUSH", "T_BRACE", "T_TRAP", "T_CHEST")
    names = ("DOORS", "LEVERS", "PACE", "GUARDS", "TRAPS", "CHESTS")
    W = SYM["HUD_W"]

    def reference(tiers, fl_cat=-1):
        img = [[0] * W for _ in range(SYM["HUD_H"])]
        for i, n in enumerate(names):
            lit, dim = int(cols[(n, "LIT")][1:], 16), int(cols[(n, "DIM")][1:], 16)
            x0 = 2 + SYM["HUD_PITCH"] * i
            for r, byte in enumerate(icons[i]):
                for c in range(8):
                    if int(byte, 16) & (0x80 >> c):
                        img[r][x0 + c] = lit if tiers[i] else dim
            for p in range(3):
                px = x0 + 10 + 4 * p
                ring = [(0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2)]
                if p < tiers[i]:
                    for dy in range(3):
                        for dx in range(3):
                            img[2 + dy][px + dx] = lit
                    if i == fl_cat and p == tiers[i] - 1:
                        for dx, dy in ring:
                            img[2 + dy][px + dx] = int(flash[1:], 16)
                else:
                    for dx, dy in ring:
                        img[2 + dy][px + dx] = dim
        return img

    def got():
        raw = b.s.uc.mem_read(SYM["HUDBUF"], W * SYM["HUD_H"] * 2)
        return [[int.from_bytes(raw[(r * W + x) * 2:(r * W + x) * 2 + 2], "big") for x in range(W)] for r in range(9)]

    def show(tiers, fl_cat=-1):
        for k, v in zip(cats, tiers):
            b.s.poke_w(S + SYM[k], v)
        b.s.poke_w(S + SYM["T_WAIT"], 0)
        b.s.poke_w(S + SYM["T_WATCH"], 0)
        b.s.poke_w(S + SYM["HUD_FL_T"], 20 if fl_cat >= 0 else 0)
        b.s.poke_w(S + SYM["HUD_FL_CAT"], max(fl_cat, 0))
        b.s.poke_w(S + SYM["HUDDIRTY"], 1)
        b.frames(2)
        want = reference(tiers, fl_cat)[:9]
        bad = sum(1 for r in range(9) for x in range(W) if got()[r][x] != want[r][x])
        assert bad == 0, (tiers, fl_cat, "%d HUD pixels differ" % bad)

    for tier in range(4):                                # every category at every tier
        show([tier] * 6)
    for i in range(6):                                   # each category alone
        t = [0] * 6
        t[i] = 3 - i % 3
        show(t)
    show([1, 2, 3, 0, 1, 2], fl_cat=2)                   # newest pip of pace wears the ring
    b.frames(21)
    assert b.s.w(S + SYM["HUDDIRTY"]) == 0 and b.s.w(S + SYM["HUD_FL_T"]) == 0
    print("   4 uniform + 6 single-category + flash states pixel-exact; flash settles after %d frames" % SYM["HUD_FLASH_FR"])
    # a real tier gain lights a pip and rings it
    h = Bot("gain")
    h.seed({"TRAPS": 300}, {"TRAP": 2})
    at_rebuild(h, "TRAP")
    assert h.v("T_TRAP") >= 1 and h.s.w(S + SYM["HUD_FL_T"]) > 0 and h.s.w(S + SYM["HUD_FL_CAT"]) == 4, (
        h.v("T_TRAP"), h.s.w(S + SYM["HUD_FL_T"]), h.s.w(S + SYM["HUD_FL_CAT"]))


def _settled_frame(sim, pad, hi_off, loop):
    """Run one frame; return the gameplay state as it stood when that frame's
    logic had finished (CPU back in main's wait loop), not mid-logic."""
    from jagsim import HALFLINES_PER_FRAME
    sim.pad = set(pad)
    vdb, vde = sim.io_w(0x46), sim.io_w(0x48)
    got = None
    for hl in range(HALFLINES_PER_FRAME):
        sim.vc = hl
        if vdb <= hl < vde and hl % 2 == 0 and sim.olp_valid():
            sim._op_line(hl)
        sim._run_halfline()
        if got is None and hl < 507 and loop[0] <= sim.pc < loop[1]:
            got = bytes(sim.uc.mem_read(S, hi_off))
    sim.frame += 1
    return got


@scenario
def msg_no_gameplay_effect(b):
    """Presentation never changes gameplay: text build vs normal build, and a HUD redrawn every frame, same input -> same settled state."""
    from soak_gate7 import find_wait_blank
    cof = _text_build("nogp")[0]
    a, c, d = Bot("a"), _text_bot(cof), Bot("d")
    loops = [find_wait_blank(x.s) for x in (a, c, d)]
    skip = {SYM["HUDDIRTY"], SYM["HUDDIRTY"] + 1}
    hi = SYM["MSG_ID"]                                   # gameplay state = everything before the message block
    script = [("right", 25), ("a", 1), (None, 3), ("right", 60), ("up", 160), ("left", 30), ("a", 1), (None, 10),
              ("left", 60), (None, 200), ("right", 120), ("up", 40), (None, 400)]
    frame = compared = 0
    for key, n in script:
        for _ in range(n):
            pad = {key} if key else set()
            d.s.poke_w(S + SYM["HUDDIRTY"], 1)           # d: HUD redrawn every single frame
            st = [_settled_frame(x.s, pad, hi, lp) for x, lp in zip((a, c, d), loops)]
            frame += 1
            if any(v is None for v in st):
                assert all(v is None for v in st), "frame %d: one build did not finish its logic" % frame
                continue
            compared += 1
            for go, tag in ((st[1], "text build"), (st[2], "HUD every frame")):
                diff = [i for i in range(hi) if st[0][i] != go[i] and i not in skip]
                assert not diff, "%s: gameplay state diverged at frame %d (offset %d)" % (tag, frame, diff[0])
    print("   %d frames x3 builds, settled gameplay state identical (%d bytes, %d frames compared)" % (frame, hi, compared))

# ---------------------------------------------------------------- environment bands (Bob Checkpoint C)
BAND_REF = "0f6a185"                                  # the pre-band baseline the gameplay must still equal
BANDS_DIR = os.path.join(ROOT, "kimi_sprites", "bands")
BAND_ADDR = (0x020000, 0x03C200, 0x058400, 0x074600, 0x090800)     # Bob's Checkpoint C table
BAND_END = 0x0ACA00


def band_words(n):
    """Kimi's vendored img_band_f<n+1>.s as a list of CRY16 words."""
    import re
    txt = open(os.path.join(BANDS_DIR, "img_band_f%d.s" % (n + 1)), encoding="utf-8", errors="replace").read()
    out = []
    for ln in txt.splitlines():
        out += [int(w, 16) for w in re.findall(r"\$([0-9A-Fa-f]{4})(?![0-9A-Fa-f])", ln.split(";")[0])]
    return out


def live_band(sim):
    """(data, ypos, height, iwidth, trans, link, type) of object 0 in LIVE."""
    import struct
    p0, p1 = struct.unpack(">QQ", bytes(sim.uc.mem_read(SYM["LIVE"], 16)))
    return dict(data=((p0 >> 43) & 0x1FFFFF) << 3, y=(p0 >> 3) & 0x7FF, h=(p0 >> 14) & 0x3FF,
                iw=(p1 >> 28) & 0x3FF, trans=(p1 >> 47) & 1, link=((p0 >> 24) & 0x7FFFF) << 3, typ=p0 & 7)


@scenario
def band_guards(b):
    """Bob's Checkpoint C guards: addresses, object indices, STOP, list lengths, the band object, resident data."""
    import re
    import struct
    S_ = SYM
    # 1. phrase alignment and Bob's address table
    assert S_["BANDS_BASE"] == BAND_ADDR[0] and S_["BANDS_BASE"] % 8 == 0
    assert S_["BAND_SIZE"] == 0x1C200 and S_["BAND_SIZE"] % 8 == 0 and S_["BAND_SIZE"] == 320 * 180 * 2
    for n in range(5):
        assert S_["BANDS_BASE"] + n * S_["BAND_SIZE"] == BAND_ADDR[n] and BAND_ADDR[n] % 8 == 0, n
    assert S_["BANDS_BASE"] + 5 * S_["BAND_SIZE"] == BAND_END
    # 2. the region collides with nothing
    art = open(os.path.join(ROOT, "gate7_castle", "castle_art.inc"), encoding="utf-8").read()
    art_bytes = int(re.search(r"^ART_BYTES\s+equ\s+(\d+)", art, re.M).group(1))
    art_end = S_["PIXBASE"] + art_bytes
    tail = bytes(b.s.uc.mem_read(art_end, S_["TEXTBUF"] - art_end))
    assert not any(tail), "art was copied past ART_BYTES (undercounted size)"
    assert any(bytes(b.s.uc.mem_read(art_end - 64, 64))), "last 64 bytes of the art are empty (overcounted size)"
    assert art_end <= S_["TEXTBUF"], "art runs into the text buffer"
    assert S_["TEXTBUF"] + 320 * 20 * 2 <= S_["BANDS_BASE"], "text buffer runs into the bands"
    assert S_["HUDBUF"] + S_["HUD_W"] * S_["HUD_H"] * 2 <= S_["PIXBASE"]
    assert BAND_END <= 0x1FFFFC - 0x1000, "bands run into the stack"
    n = S_["NOBJ"]
    assert S_["OBJS"] + n * 16 <= S_["LIVE"]
    assert S_["LIVE"] + (n + 1) * 16 <= S_["SHADOW"]
    assert S_["SHADOW"] + (n + 1) * 16 <= S_["HUDBUF"]
    # 3. object indices: band first, HUD and text last, one slot each, NOBJ 20
    names = sorted((v, k) for k, v in S_.items() if k.startswith("O_") and k != "O_" and isinstance(v, int))
    assert [v for v, _ in names] == list(range(n)), names
    assert n == 20 and S_["O_BAND"] == 0 and S_["O_HUD"] == n - 2 and S_["O_TEXT"] == n - 1
    print("   NOBJ %d: %s ... %s | art ends $%X | bands $%X-$%X" % (n, names[0][1], names[-1][1], art_end, BAND_ADDR[0], BAND_END))
    # 4. resident data == Kimi's files, byte for byte (after boot)
    for f in range(5):
        want = struct.pack(">%dH" % (320 * 180), *band_words(f))
        got = bytes(b.s.uc.mem_read(BAND_ADDR[f], len(want)))
        assert got == want, "band F%d in DRAM differs from Kimi's file" % (f + 1)
    # 5. the object: first in the list, opaque, 80 phrases x 180 lines, this floor's data, links onward
    # 6. refreshed through the normal build/copy: SHADOW holds the same, LIVE is copied from it every blank
    for _ in range(3):
        b.frames(1)
        lb = live_band(b.s)
        assert lb["typ"] == 0 and lb["data"] == BAND_ADDR[b.v("FLOOR")] and lb["iw"] == 80 and lb["h"] == 180, lb
        assert lb["trans"] == 0, "band must be opaque"
        assert lb["link"] == S_["LIVE"] + 16, "band must link to object 1"
    sh = struct.unpack(">QQ", bytes(b.s.uc.mem_read(S_["SHADOW"], 16)))
    assert ((sh[0] >> 43) & 0x1FFFFF) << 3 == BAND_ADDR[0] and (sh[1] >> 47) & 1 == 0
    assert b.s.w(S_["OBJS"] + S_["OB_FL"]) == 0, "band record carries no TRANS flag"
    for base in (S_["LIVE"], S_["SHADOW"]):                  # STOP at index NOBJ in both lists
        stop = struct.unpack(">Q", bytes(b.s.uc.mem_read(base + n * 16, 8)))[0]
        assert stop & 7 == 4, hex(base)
    for i in range(n):                                       # every LINK points at the next object / STOP
        p0 = struct.unpack(">Q", bytes(b.s.uc.mem_read(S_["LIVE"] + i * 16, 8)))[0]
        assert (((p0 >> 24) & 0x7FFFF) << 3) == S_["LIVE"] + (i + 1) * 16, i
    print("   band object: data $%X, 80 phrases x 180 lines, y %d, no TRANS, LINK chain of %d objects + STOP intact" % (
        lb["data"], lb["y"], n))


@scenario
def band_floors(b):
    """A real five-floor route: the band switches with the floor and its pixels show through (rows 40-140, x 24-140 and 170-280: clear of ladders)."""
    import struct
    seen = []
    clear = [x for x in range(24, 140)] + [x for x in range(170, 280)]

    def check(tag):
        b.s.run_frames(1, draw_last=True)
        f = b.v("FLOOR")
        lb = live_band(b.s)
        assert lb["data"] == BAND_ADDR[f], (tag, f, hex(lb["data"]))
        words = band_words(f)
        bad = 0
        for y in range(40, 141, 4):
            line = b.s.frame_buf[16 + y]
            for x in clear:
                if line[x] != words[y * 320 + x]:
                    bad += 1
        assert bad == 0, "%s: %d band pixels differ on F%d" % (tag, bad, f + 1)
        seen.append(f)

    orig_climb = Bot.climb

    def climb(self, direction="up", limit=400):
        orig_climb(self, direction, limit)
        if self.v("GSTATE") == 0 and (not seen or self.v("FLOOR") != seen[-1]):
            check("after climb")
    check("start")
    Bot.climb = climb
    try:
        b.run_route("L", "L")
    finally:
        Bot.climb = orig_climb
    assert seen[:5] == [0, 1, 2, 3, 4], seen
    for f in range(5):                                       # nobody ever wrote to the resident bands
        want = struct.pack(">%dH" % (320 * 180), *band_words(f))
        assert bytes(b.s.uc.mem_read(BAND_ADDR[f], len(want))) == want, "band F%d was modified" % (f + 1)
    print("   floors %s: band pointer + pixels correct on each; all five bands unmodified after the run" % [x + 1 for x in seen])


def _baseline_cof(ref=None):
    """The build of git ref `ref` (default: the pre-band BAND_REF) assembled into the temp dir."""
    import subprocess, tempfile
    ref = ref or BAND_REF
    tmp = os.path.join(tempfile.gettempdir(), "g7_base_" + ref)
    cof = os.path.join(tmp, "base.cof")
    if not os.path.exists(cof):
        os.makedirs(tmp, exist_ok=True)
        tar = subprocess.run(["git", "-C", os.path.dirname(ROOT), "archive", ref, "jaguar-toolchain/gate7_castle",
                              "jaguar-toolchain/kimi_sprites"],
                             capture_output=True, check=True).stdout
        import io, tarfile
        tarfile.open(fileobj=io.BytesIO(tar)).extractall(tmp)
        src = os.path.join(tmp, "jaguar-toolchain", "gate7_castle")
        bindir = os.environ.get("JAG_BIN", r"C:/Users/Owner/.bob/playground/jaguar-toolchain/bin")
        subprocess.run([os.path.join(bindir, "rmac.exe"), "-fb", "-m68000", "-o", "base.o", "gate7_castle.s"], cwd=src, check=True, capture_output=True)
        subprocess.run([os.path.join(bindir, "rln.exe"), "-a", "802000", "r", "r", "-e", "-o", cof, os.path.join(src, "base.o")], cwd=src, check=True, capture_output=True)
    return cof


def _same_gameplay(ref):
    """Same input -> the same settled gameplay state every frame as the build of git ref `ref`."""
    from soak_gate7 import find_wait_blank
    old = Bot.__new__(Bot)
    old.s, old.name, old.shots = JagSim(_baseline_cof(ref)), "old", 0
    old.s.boot_wait()
    new = Bot("new")
    lp = [find_wait_blank(x.s) for x in (old, new)]
    hi = SYM["MSG_ID"]
    script = [("right", 25), ("a", 1), (None, 3), ("right", 60), ("up", 160), ("left", 30), ("a", 1), (None, 10),
              ("left", 60), (None, 200), ("right", 120), ("up", 40), (None, 300), ("left", 90), ("up", 120), (None, 600)]
    frame = compared = 0
    for key, cnt in script:
        for _ in range(cnt):
            pad = {key} if key else set()
            st = [_settled_frame(x.s, pad, hi, l) for x, l in zip((old, new), lp)]
            frame += 1
            if st[0] is None or st[1] is None:
                assert st[0] is None and st[1] is None, "frame %d: one build did not finish its logic" % frame
                continue
            compared += 1
            diff = [i for i in range(hi) if st[0][i] != st[1][i]]
            assert not diff, "gameplay state diverged from %s at frame %d (offset %d)" % (ref, frame, diff[0])
    print("   %d frames vs %s, settled gameplay state identical (%d bytes, %d frames compared)" % (frame, ref, hi, compared))


@scenario
def band_no_gameplay_effect(b):
    """Gameplay is untouched by the bands: same input, same settled gameplay state every frame as the pre-band build."""
    _same_gameplay(BAND_REF)


# ---------------------------------------------------------------- hero facing + climb (presentation only)
HERO_REF = "cfbad1b"                                  # the band build: hero art was one frame, facing/climb not drawn


@scenario
def hero_no_gameplay_effect(b):
    """Hero facing and climb frames are presentation only: gameplay state identical to the build before them."""
    _same_gameplay(HERO_REF)


def _hero_probe(b, pad):
    """Run one frame; return what the hero object says once that frame's logic and list build are done."""
    from soak_gate7 import find_wait_blank
    from jagsim import HALFLINES_PER_FRAME
    sim = b.s
    lo, hi = find_wait_blank(sim)
    sim.pad = set(pad)
    vdb, vde = sim.io_w(0x46), sim.io_w(0x48)
    got = None
    for hl in range(HALFLINES_PER_FRAME):
        sim.vc = hl
        if vdb <= hl < vde and hl % 2 == 0 and sim.olp_valid():
            sim._op_line(hl)
        sim._run_halfline()
        if got is None and hl < 507 and lo <= sim.pc < hi:
            got = dict(data=sim.l(SYM["OBJS"] + SYM["O_HERO"] * 16 + SYM["OB_DATA"]), hy=sim.sw(S + SYM["HY"]),
                       climb=sim.sw(S + SYM["CLIMB"]), facing=sim.sw(S + SYM["FACING"]), hx=sim.sw(S + SYM["HX"]))
    sim.frame += 1
    return got


def _hero_frames(b):
    """(right-facing, left-facing) frame addresses as the game uses them, and their pixel words."""
    import struct
    seen = {}
    for pad, key in (({"left"}, "L"), ({"right"}, "R")):
        for _ in range(4):
            r = _hero_probe(b, pad)
        seen[key] = r["data"]
    words = {k: struct.unpack(">%dH" % (16 * 24), bytes(b.s.uc.mem_read(a, 16 * 24 * 2))) for k, a in seen.items()}
    return seen, words


@scenario
def hero_facing(b):
    """The hero faces the way it last walked: Bob's frame for right, its exact mirror for left."""
    seen, words = _hero_frames(b)
    assert seen["L"] != seen["R"], "walking left and right must use different frames"
    for y in range(24):                                  # left frame == mirror of Bob's frame, row for row
        assert words["L"][y * 16:(y + 1) * 16] == tuple(reversed(words["R"][y * 16:(y + 1) * 16])), y
    assert any(words["R"]) and words["L"] != words["R"]
    got = []
    for pad, want in (({"left"}, "L"), (set(), "L"), (set(), "L"), ({"right"}, "R"), (set(), "R"), ({"left"}, "L"),
                      ({"right"}, "R"), ({"left", "right"}, None)):
        _hero_probe(b, pad)                               # (the logic that finishes in a frame read the previous frame's pad)
        r = _hero_probe(b, pad)
        got.append((sorted(pad), r["facing"], "L" if r["data"] == seen["L"] else "R" if r["data"] == seen["R"] else "?"))
        if want:
            assert got[-1][2] == want, got[-1]
        assert got[-1][2] != "?", got[-1]
        assert (r["facing"] < 0) == (got[-1][2] == "L"), got[-1]         # the sprite always follows FACING
    print("   right frame $%X, left frame $%X (exact mirror); follows FACING through %d inputs" % (seen["R"], seen["L"], len(got)))


@scenario
def hero_climb(b):
    """On a ladder the hero alternates the two frames every 16 halflines of travel (hand over hand), and holds still when it stops."""
    seen, _ = _hero_frames(b)
    b.choice_floor(0, "L")                               # through the door to the left ladder foot
    b.wait_safe_climb()
    assert b.v("CLIMB") == 0 and b.v("HX") == LAD["L"]
    flips = trace = 0
    last = None
    for _ in range(14):                                  # climbing up: the frame is a function of HY alone
        r = _hero_probe(b, {"up"})
        if r["climb"]:
            trace += 1
            want = seen["L"] if (r["hy"] >> 4) & 1 else seen["R"]
            assert r["data"] == want, (r, hex(want))
            flips += last is not None and r["data"] != last
            last = r["data"]
    assert trace >= 10 and flips >= 2, (trace, flips)
    held = {_hero_probe(b, set())["data"] for _ in range(20)}               # let go: frozen, no flicker
    assert len(held) == 1, held
    hy0 = b.v("HY")
    for _ in range(14):                                  # climbing back down: still a function of HY
        r = _hero_probe(b, {"down"})
        if r["climb"]:
            assert r["data"] == (seen["L"] if (r["hy"] >> 4) & 1 else seen["R"]), r
    assert b.v("HY") > hy0
    b.climb("up")                                        # off the ladder, onto F2: back to walking facing
    for _ in range(3):
        r = _hero_probe(b, set())
    assert r["climb"] == 0 and r["data"] == (seen["L"] if r["facing"] < 0 else seen["R"]), r
    print("   %d climbing frames, %d hand-over-hand flips, still when still, walking frame restored after the climb" % (trace, flips))


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
