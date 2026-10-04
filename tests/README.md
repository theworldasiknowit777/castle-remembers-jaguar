# tests/ — Behavioral Equivalence Tests

This directory will contain tests verifying that the Jaguar port's game logic
matches the authoritative original in `original/`.

**Status: not started — awaiting Gate 2+**

## Planned approach

- Extract deterministic game logic from `original/index.html` (level generator,
  trap placement, adaptive difficulty, save-state model)
- Port equivalent logic to 68000 assembly
- Write test harness that feeds identical seed inputs to both and compares outputs
- Targets: level layout, door/lever positions, trap activation, save-state versioning

## Do not add test files here until Gate 2 is authorized.
