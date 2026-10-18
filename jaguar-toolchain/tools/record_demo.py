"""record_demo.py - replay a pad log in real Virtual Jaguar and record the window to an mp4.

  python record_demo.py ROUTE.json OUT.mp4 [--cof gate7_castle.cof] [--lead 1.5] [--tail 3]

ROUTE.json is a list with one entry per 60 Hz frame: the pad names held that frame
(left, right, up, down, a), as logged from the jagsim playtest bot. Keys sent are the
documented Virtual Jaguar ones: Z C S X L. Needs an ffmpeg (FFMPEG env var, or imageio-ffmpeg).
Run it with the Virtual Jaguar window visible and nothing else on top of it."""
import ctypes, json, os, subprocess, sys, time
from ctypes import wintypes

KEYS = {"left": "Z", "right": "C", "up": "S", "down": "X", "a": "L"}
VJ = os.environ.get("VJ", r"C:\Users\Owner\.bob\playground\jaguar-toolchain\emulator\vjaguar\virtualjaguar.exe")
u = ctypes.windll.user32


def vk(ch):
    return ord(ch)


def key(ch, down):
    u.keybd_event(vk(ch), u.MapVirtualKeyW(vk(ch), 0), 0 if down else 2, 0)


def find_window(pid):
    found = []
    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cb(h, _):
        p = wintypes.DWORD()
        u.GetWindowThreadProcessId(h, ctypes.byref(p))
        if p.value == pid and u.IsWindowVisible(h) and u.GetWindowTextLengthW(h) > 0:
            found.append(h)
        return True
    u.EnumWindows(cb, 0)
    return found[0] if found else None


def main():
    args = sys.argv[1:]
    route, out = json.load(open(args[0])), args[1]
    opt = {args[i]: args[i + 1] for i in range(2, len(args) - 1, 2)}
    cof = os.path.abspath(opt.get("--cof", os.path.join(os.path.dirname(__file__), "..", "gate7_castle", "gate7_castle.cof")))
    lead, tail = float(opt.get("--lead", 1.5)), float(opt.get("--tail", 3))
    ffmpeg = os.environ.get("FFMPEG")
    if not ffmpeg:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    hdr = open(cof, "rb").read(48)
    assert hdr[:2] == b"\x01\x50" and int.from_bytes(hdr[36:40], "big") == 0x802000, "not a Jaguar COFF"
    p = subprocess.Popen([VJ, cof], cwd=os.path.dirname(VJ))
    h = None
    for _ in range(100):
        time.sleep(0.2)
        h = find_window(p.pid)
        if h:
            break
    assert h, "no Virtual Jaguar window"
    u.ShowWindow(h, 9)
    u.SetWindowPos(h, -1, 0, 0, 0, 0, 0x0001 | 0x0002)       # topmost: nothing may cover the capture or take the keys
    u.SetForegroundWindow(h)
    time.sleep(0.5)
    r = wintypes.RECT()
    u.GetWindowRect(h, ctypes.byref(r))
    w, hh = (r.right - r.left) & ~1, (r.bottom - r.top) & ~1
    rec = subprocess.Popen([ffmpeg, "-y", "-f", "gdigrab", "-framerate", "30", "-offset_x", str(r.left), "-offset_y", str(r.top),
                            "-video_size", "%dx%d" % (w, hh), "-i", "desktop", "-draw_mouse", "0",
                            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "12", "-pix_fmt", "yuv420p", out],
                           stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(lead)
    held = set()
    t0 = time.perf_counter()
    for i, pad in enumerate(route):
        want = {KEYS[x] for x in pad}
        for k in held - want:
            key(k, False)
        for k in want - held:
            key(k, True)
        held = want
        if i % 30 == 0 and u.GetForegroundWindow() != h:      # keys go to the foreground window: never to another app
            for k in held:
                key(k, False)
            held = set()
            u.SetForegroundWindow(h)
        dt = t0 + (i + 1) / 60.0 - time.perf_counter()
        if dt > 0:
            time.sleep(dt)
    for k in held:
        key(k, False)
    time.sleep(tail)
    rec.stdin.write(b"q"); rec.stdin.flush(); rec.wait(timeout=30)
    p.kill()
    print("recorded", out, "%dx%d window" % (w, hh))


main()
