# S1D0PACKAGE self-review

Scope: launcher, stage binding, native client, observer changes and host tests.
Reviewed under REVIEW.md. This is a Codex self-review, not a Claude acceptance.

No remaining Important finding was identified in the prepared package.
The physical gate remains closed while R5 is missing. No physical run occurred.

Corrections made before handoff:
- Drain observer records after topology queries before selecting the cutoff.
  Injected device close and incomplete-record tests block guest release.
- Require complete final trace parsing after controlled shutdown.
  Reject a tracer that does not finish. Preserve failure logs.
- Treat ramblock Offset as internal ram_addr_t, never an HVA.
- Decode device names as bounded NUL-terminated strings. The inert fixture caught
  and corrected a fixed-buffer printing error. Both raw records are retained.

Only the 04:00.0 host device appears in the fixed physical command. B5 and
vm-test.sh remain unchanged. All new GPU claims stay below physical payload or
coherency verification. Publication remains denied. Root is never invoked.

The native memory client has no PCI or MMIO imports. Its backing stays in the
permanent owner through detach/reload. Standard VFIO startup reset and firmware
PCI effects remain outside any claim that the probes themselves make no writes.
