# Testing status

Main contains manual runtime records in AGENTS.md and jaguar-toolchain/DEVLOG.md: Gates 1–5 recorded PASS; Gate 6 remains pending. No full HTML-to-Jaguar behavioral-equivalence suite exists on main.

The separate `claude/gameplay-refinement` branch contains Gate 7 scripted playtests, a Unicorn-based partial Jaguar hardware model, soak checks and Virtual Jaguar evidence. See [submission reproduction instructions](../docs/submission/DEMO.md) and [evidence boundaries](../docs/submission/EVIDENCE.md).

The original goal of full baseline equivalence remains future work. The original HTML is read-only; gameplay-specific model tests do not establish complete parity, timing accuracy or physical-hardware correctness.
