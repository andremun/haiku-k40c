# User-supplied Claude review nits

The user supplied these four nonblocking nits after the approved run began:

1. Owner.cpp Fifo phase accepts arbitrary values at 0x200. Enforce the actual
   bit-0x100-only read/modify/write sequence at the allowlist boundary.
2. Owner.cpp I2C phase admits sixteen bus registers. Restrict it to the one bus
   selected by this ROM's BIOS table.
3. /tmp/k40-a7-ed25519 disappears after reboot. Keep the exact pinned checkout
   under ~/haiku-cross/src/ so the package can be rebuilt.
4. Include intentionally omitted Linux setup in write-inventory.json: four
   hybrid AUX pad power-offs, seven other bus initializations and ROM shadow
   toggles at 0x88050. State the reasons in a short table.

The user requests a new package after the run record. No second launch or D1
is approved. Diagnostic capture for the pre-grant failure is included as a
bounded host/client correction, not as a new hardware sequence.
