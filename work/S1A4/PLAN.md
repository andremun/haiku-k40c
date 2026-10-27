# S1A4 pre-start plan

1. Follow GK110B's selected device callbacks, not similarly named newer-chip files.
2. Separate constructor work, preinit, POST, and later normal init.
3. Record the early I2C and mapped host flush-page requirements with exact source lines.
4. Define a gated, once-per-boot host startup controller and source-backed helper transport work.
5. Keep physical backends disabled. Model errors and partial-state retention with host tests.
6. Write docs/S1-PRESTART.md with choices, excluded paths, and unresolved hardware proof.
7. Run make check, record a bounded result, and continue to C2 under ADR 007.
