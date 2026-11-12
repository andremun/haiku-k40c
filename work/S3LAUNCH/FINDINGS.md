# S3LAUNCH findings

## Launch images (2026-11-12, SOURCE_ONLY)

`tools/gr/launch.py` builds the layout (12 records, 66,379,776 bytes, of which the
TLS area is 63,438,848), the push buffer (106 words: 100 set-up, 6 launch), the
descriptor and constant buffer 7 from the Mesa sources. The descriptor equals the
one of the reference run in 154 of 155 fields. The one difference is the address
of constant buffer 7, which follows our layout.

- KNOWN: `mp_count` of Mesa is the TPC total (`gf100.c:1160-1169`,
  `nvc0_screen.c:1065`): 15 on this card. TLS bytes per unit 0x408000.
- UNKNOWN: whether the 64 values of method 0x248 and the TIC/TSC addresses are
  needed for a job without textures. They are kept, as in Mesa.

## Slow-window speed (KNOWN, HARDWARE_VERIFIED under Haiku, S1 run of 2026-10-31)

results/20261031-batch1-a7-bar1-d198d424/serial.log: a 262,144-byte record is
zeroed in 21 to 124 ms and read back in about 100 ms; one 8-byte patch with flush
and readback takes about 6 us. Consequence: zeroing the 847,872-byte context
memory and writing about 16,000 page-table entries fit in well under one second
each when the entries are written in bulk with one flush.
