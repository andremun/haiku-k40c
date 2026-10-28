# S1A7NITS: new host-only package

Fixed all four supplied review nits. FIFO preinit enforces fresh paired reads,
bit-0x100-only changes and exactly two writes. I2C preinit admits only the bus
selected from the immutable BIOS table. Actual-boundary negative fixtures pass.

The exact Ed25519 checkout is persistent at ~/haiku-cross/src/orlp-ed25519.
Commit, clean-tree, source and notice checks remain. The generated inventory now
lists four omitted AUX pad power-offs, seven other bus inits and ROM shadow
toggles, with source citations and scoped reasons. No omitted write was added.

The new package also captures bounded guest shell output and logs module-load
failure status. The old pre-grant discovery/open failure remains UNKNOWN.
No native loading or physical readiness claim follows from host tests.

Both native links and host fixtures pass. Actual native boundary/client tests
pass 4129/24 assertions. Eight launcher and two omission fixtures pass. Full
make check passes, recorded in check-final.log. Package/source hashes and the full
write inventory are in this folder. docs/A7-REVIEW-PACKAGE.md is updated.

New package: build/a7/package-review-nits/, with a fresh key and no consumed marker.
Original build/a7/package/consumed.json and all approved-run captures remain.
The failed first run is committed as 600d114, results/20261028-a7-post/.
No retry, other guest, D1, root command, manual reset or push occurred.
Fresh review and an explicit one-run yes are required before another launch.
S1 remains incomplete. D1/Q7 and conditional S2/S3 preparation stay open.
