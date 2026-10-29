# Findings

KNOWN / SOURCE_ONLY: the nv50 instmem slow path selects a physical 1 MiB window
at 0x1700 and accesses words through 0x700000 plus the low physical offset.
The new transaction owns its window lock across the complete transfer and flush,
reselects on each transaction, and handles crossing that boundary. Every word
requires a valid owned arena span; callers cannot supply a raw GPU address.

The explicit UC profile and private physical gate are prerequisites. CPU store
ordering, sourced BAR flush/write/poll and CPU load ordering are separate steps.
The result is scoped staging/readback only, with no generic Buffer proof flags.
Each bounded loop checks failure and elapsed time; a finite poll cap also covers
a clock that stops advancing. A possibly partial write dirties the token first.
Any failure latches the uploader and retains the ledger, with no cleanup writes.

The two data pages receive complete address-dependent patterns before either
page is verified. Complement and original passes repeat that order. The host
oracle uses independently indexed physical storage and a separate pattern
expression; injected aliasing is detected. Table patches are private to Mapper;
updates to a referenced SPT additionally require Mapper's private ledger access.
Twenty host cases and native object compilation pass. No guest/card was run.
