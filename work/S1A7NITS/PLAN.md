# A7 review nits: host-only follow-up

1. Enforce FIFO read/modify/write pairing and bit-0x100-only changes at the
   actual transport boundary. Add negative tests against that boundary.
2. Derive the preinit I2C pin from the immutable ROM's one dedicated bus and
   deny the other bus registers. Keep POST bit-banging behind its existing policy.
3. Copy the exact Ed25519 checkout into ~/haiku-cross/src/orlp-ed25519. Keep its
   revision, clean-tree and file-hash checks. Preserve the old temporary checkout.
4. Generate and document omissions for hybrid AUX pads, unused bus inits and
   ROM shadow toggles, with pinned sources and reasons. Do not execute them.
5. Build a new package under a new path with a fresh key. Preserve the consumed
   original package, all run evidence and original artifacts. No VM or D1 run.
6. Preserve guest shell output and client module-load status in the next package
   so a future separately approved attempt can diagnose the pre-grant stop.
   Change no register sequence for this diagnostic correction.
7. Regenerate affected reports, run host/native checks and make check, update
   status/review/result, and commit this macro task separately. Never push.
