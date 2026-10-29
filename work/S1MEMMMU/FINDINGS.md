# Findings

KNOWN / SOURCE_ONLY: gk104 17/12 uses 15-bit SPT and 13-bit PGD indices.
The small-table pointer occupies the high PDE half; the absent LPT half is zero.
Read-only VRAM data PTEs have valid+RO only, with no kind/VOL/compression flags.
The selected MMU has 40-bit DMA addresses. The 44-bit physical-window mask is
not a PTE-width claim: the encoder rejects >=2^40 before VOL/target fields.
The bounded pure format can be reused by future channel encoding; this is not
channel or PBDMA evidence.

The preflight rejects an enabled BAR1 context before any new VRAM writes.
The complete table/enable/remap/restore/disable experiment holds the MMU lock;
window uploads take their separate lock inside it. Mode-17 RMW preserves other
bits. Invalidations select only the owned PGD and PAGE_ALL|HUB_ONLY, with free-slot
and queued-condition polls. The latter is not generic quiescence. Only BAR1 is
programmed, using 0x1704 and its sourced two-flush wait. BAR2 is absent.

The independent BAR oracle decodes the actual serialized instance/PDE/PTE data
from separate simulated physical storage. A/B -> B/B -> A/B witnesses catch a
stale TLB or aliased BAR view. Context replacement or uncertain disable stops
without guessed rollback. All objects remain retained. Successful owned-context
disable is scoped closure, not a general live-free contract.

4096 independent format cases and 21 lifecycle/fault cases pass, including
partial enable/disable, source poll conditions, stationary/backwards clocks,
changed context ownership and new raw faults. The full five-component core
links against the matching Haiku kernel with no undefined symbols, no load.
No UC mapping, GPU translation or hardware behavior was tested here.
