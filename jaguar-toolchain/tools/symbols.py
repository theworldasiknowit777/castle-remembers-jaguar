"""symbols.py - read the `NAME equ EXPR` chain from gate7_castle.s.

The state block is defined as a chain of equates (FLOOR equ CLIMB+2 ...), so
the test tools evaluate it here instead of hard-coding offsets. Expressions use
RMAC's rule: strictly left to right, no operator precedence.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "gate7_castle", "gate7_castle.s")
_EQU = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)[ \t]+equ[ \t]+([^;\n]+)", re.M)
_TOK = re.compile(r"\s*(\$[0-9A-Fa-f]+|%[01]+|\d+|[A-Za-z_][A-Za-z0-9_]*|<<|>>|[-+*/&|()])")


def _eval(expr, sym):
    toks = _TOK.findall(expr.strip())

    def atom(i):
        t = toks[i]
        if t == "(":
            v, i = seq(i + 1)
            return v, i + 1                     # skip ')'
        if t == "-":
            v, i = atom(i + 1)
            return -v, i
        if t.startswith("$"):
            return int(t[1:], 16), i + 1
        if t.startswith("%"):
            return int(t[1:], 2), i + 1
        if t.isdigit():
            return int(t), i + 1
        return sym[t], i + 1

    def seq(i):
        v, i = atom(i)
        while i < len(toks) and toks[i] != ")":
            op = toks[i]
            r, i = atom(i + 1)
            v = {"+": v + r, "-": v - r, "*": v * r, "/": int(v / r), "&": v & r, "|": v | r,
                 "<<": v << r, ">>": v >> r}[op]
        return v, i

    return seq(0)[0]


def load(path=SRC):
    sym = {}
    for name, expr in _EQU.findall(open(path, encoding="utf-8", errors="replace").read()):
        try:
            sym[name] = _eval(expr, sym)
        except (KeyError, IndexError, ValueError):
            pass                                # forward refs (art labels) are not needed
    return sym


if __name__ == "__main__":
    s = load()
    for k in ("R_BASE", "M_BASE", "P_BASE", "RUNS", "T_DOOR", "DOORS", "LEVERS", "FSPIKE", "FENEMY",
              "ENEMY", "AX", "LADS", "CHSTATE", "SHARDS", "FBX", "BLADE_CX", "VOICE_ID", "STATE_SIZE"):
        print("%-11s %4d" % (k, s[k]))
