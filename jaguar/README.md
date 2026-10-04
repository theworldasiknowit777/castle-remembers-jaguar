# jaguar/ — Atari Jaguar Port

This directory will contain the Atari Jaguar port of The Castle Remembers.

**Status: not started — awaiting Gate 2**

## Planned structure (Gate 2+)

```
jaguar/
├── src/
│   ├── main.s          68000 entry point, hardware init
│   ├── engine.s        Game engine (adapted from original/)
│   ├── level.s         Level builder / castle generator
│   ├── player.s        Player physics and input
│   ├── render.s        Object Processor / blitter rendering
│   └── memory.s        Memory layout, save state
├── gpu/
│   ├── sprites.s       GPU sprite rendering code (RISC/GPU)
│   └── fx.s            Visual effects
├── dsp/
│   └── audio.s         DSP audio (Jerry) code
├── data/
│   ├── tiles.bin       Tile graphics
│   └── sprites.bin     Sprite graphics
└── Makefile            Build rules (rmac + rln)
```

## Do not add files here until Gate 2 is authorized.
