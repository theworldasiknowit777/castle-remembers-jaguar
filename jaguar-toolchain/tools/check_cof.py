"""check_cof.py - refuse anything that is not a sane Jaguar 68000 COFF.

Guard added after a Gate 7 .cof was written through Windows PowerShell 5.1 `>`
(binary re-encoded as UTF-16 text, header FF FE): Virtual Jaguar ran garbage
and stopped with "Illegal instruction at $E00004".

Checks: COFF magic $0150 (bytes 01 50), entry point $802000, a .text section
at $802000, and every section's file data inside the file.

    python tools/check_cof.py file.cof [more.cof ...]   # exit 1 on any failure
"""
import struct
import sys

MAGIC = 0x0150
ENTRY = 0x802000


def check(path):
    """Return a list of problems (empty = OK)."""
    try:
        d = open(path, "rb").read()
    except OSError as e:
        return ["cannot read: %s" % e]
    if len(d) < 48:
        return ["too short (%d bytes) to be a COFF" % len(d)]
    problems = []
    magic, nsect = struct.unpack(">HH", d[0:4])
    if magic != MAGIC:
        hint = " (UTF-16 text: written by PowerShell '>'?)" if d[:2] in (b"\xff\xfe", b"\xfe\xff") else ""
        return ["bad magic %02X %02X, expected 01 50%s" % (d[0], d[1], hint)]
    optsz = struct.unpack(">H", d[16:18])[0]
    entry = struct.unpack(">I", d[36:40])[0]
    if entry != ENTRY:
        problems.append("entry $%06X, expected $%06X" % (entry, ENTRY))
    text_ok = False
    sh = 20 + optsz
    for i in range(nsect):
        if sh + (i + 1) * 40 > len(d):
            problems.append("section header %d past end of file" % i)
            break
        name, _pa, va, size, ptr = struct.unpack(">8sIIII", d[sh + i * 40: sh + i * 40 + 24])
        name = name.rstrip(b"\0").decode("ascii", "replace")
        if name == ".text":
            text_ok = va == ENTRY and size > 0
        if size and ptr and name != ".bss" and ptr + size > len(d):
            problems.append("%s data (%d bytes at %d) runs past end of file" % (name, size, ptr))
    if not text_ok:
        problems.append(".text missing or not at $%06X" % ENTRY)
    return problems


def main(paths):
    bad = 0
    for p in paths:
        probs = check(p)
        if probs:
            bad += 1
            print("BAD COF  %s: %s" % (p, "; ".join(probs)))
        else:
            print("ok COF   %s" % p)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
