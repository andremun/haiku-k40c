# Review of D5 (2026-10-12): ACCEPT after scaffold fixes

Three sessions, about 6.5 hours of card time. Acceptance test 101
checks, own tests 56 checks, both also clean under the address and
undefined-behaviour sanitizers.

What the agent did: the header, the implementation (23 descriptor fields,
all with the right bits), the tests, the document, and a source citation
for every constant. The scaffold checked all 23 field rows mechanically:
each cited header line gives exactly the bits of the row, and each cited
line of `nve4_compute.c` assigns that field.

What the scaffold did:

1. Two code defects that the second session could not find in two hours:
   the constant-buffer size was stored in the wrong bits (967 to 975, not
   975 to 991), and `encodeLaunch` sent an extra bind method.
2. Two citations corrected (`SUBC_CP` is defined in `nvc0_winsys.h:45`;
   the alignment `0x100` is in `nve4_compute.c:600`).
3. One sentence of the document corrected: it said the `UPLOAD_*` methods
   "use the upload engine, not the compute subchannel". They are compute
   methods.

Limit: the descriptor is checked against Mesa's code, not against a
descriptor that ran on the card. The comparison with a real trace waits
for task C5.
