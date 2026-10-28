# S1A7NITS: four supplied A7 review nits

The user asks for these fixes after recording the one approved A7 run:

- Enforce that FIFO preinit writes to 0x200 change only bit 0x100.
- Restrict I2C preinit to the bus register selected by the immutable BIOS table.
- Keep the exact pinned Ed25519 dependency in a persistent checkout under
  ~/haiku-cross/src/, with source/notice validation.
- Add the intentionally omitted Linux pre-POST writes and their reasons to
  the inventory and a short review table: four hybrid AUX pad power-offs,
  seven other I2C bus inits, and ROM shadow toggles.

This is host-only work. No further guest, GPU write, reset or D1 is authorized.
Preserve the consumed original package and 600d114's captured evidence. Build
new artifacts and a fresh-key package at a new path. Include exact hashes and
scope in the review doc. The first guest's discovery/open failure remains UNKNOWN
unless read-only host evidence resolves it. Do not claim it was a POST failure.

Write PLAN/FINDINGS/RESULT (RESULT max 40 lines), update STATUS, run make check
and commit separately on main. Never push or change reviewer checks/reference/.
