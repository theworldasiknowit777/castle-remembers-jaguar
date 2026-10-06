#!/bin/sh
# Build gate7_castle: regenerate art, assemble, link (Bob's Gate 6 commands).
set -e
cd "$(dirname "$0")/.."
B="${JAG_BIN:-/c/Users/Owner/.bob/playground/jaguar-toolchain/bin}"
PY="${PY:-/c/Users/Owner/AppData/Local/Programs/Python/Python313/python.exe}"
"$PY" tools/mkart.py > /dev/null
cd gate7_castle
# TEXT=1: the castle-voice text band test build (Bob Checkpoint B review only;
# extra OP object + TEXTBUF). Never the shipped gate7_castle.cof.
OUT=gate7_castle; DEF=
if [ "${TEXT:-0}" = 1 ]; then OUT=gate7_castle_text; DEF=-dTEXT_ENABLE=1; fi
"$B/rmac.exe" -fb -m68000 $DEF -o $OUT.o gate7_castle.s
"$B/rln.exe" -a 802000 r r -e -o $OUT.cof $OUT.o > /dev/null
rm -f gate7_castle.prn
"$PY" ../tools/check_cof.py $OUT.cof > /dev/null || { "$PY" ../tools/check_cof.py $OUT.cof; exit 1; }
echo "built $OUT.cof ($(wc -c < $OUT.cof) bytes)"
