# Findings

KNOWN / SOURCE_ONLY: gf108 RAM groups enabled subunits by FBP and returns one
LTC per FBP. The selected normal heap requires equal nonzero FBP amounts.
Mixed layouts and inconsistent totals are rejected. No captured physical
allocation address is used. Head 256 KiB, tail 1 MiB and A7's scratch page
are excluded before append-only allocation.

The ledger reserves two debug objects first. Owner/epoch/id tokens, distinct
physical/BAR/channel address roles and per-record dirty/staged/reference state
keep allocation metadata separate from translation or DMA payload evidence.
There is no free/reuse operation. Failure retains all partial allocations;
referenced storage cannot be dirtied through the ordinary upload interface.
Only the private future Mapper can update the retained small table.
The ledger must itself live in the permanent native memory owner; its value
object alone cannot establish kernel module lifetime.

The independent interval oracle exercises 48 uniform layouts. Boundary, wrong
alignment/role, capacity, partial acquisition, stale generation, repeated
configuration and dirty-before-failure cases pass. A separate Haiku kernel
object builds with warnings and frame-size checks treated as errors.
No guest, card, reset, live allocation or DMA publication test was performed.
