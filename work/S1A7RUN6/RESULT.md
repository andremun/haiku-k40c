# S1A7RUN6 result

The user authorized one unchanged package-i2c run after Claude's ACCEPT review.
Build/hash, host/R5, VFIO ownership and no-existing-guest checks passed.
One launch ran from commit 2818763. The consumed marker remains.

STOPPED after 144.8 s: native POST_RESULT Error::Timeout (9), PC 0x85d6.
490 active and 38 skipped trace entries. This is not POST or S1 success.
B5 identity 0x0f1240a1/command 0x0007 passed twice. The pre-POST flush arm callback
succeeded for candidate 0x15df000, encoded 0x15df0. The I2C 0x20/dd=03 transfer
reported Complete, primary/cleanup None. These are KNOWN / HARDWARE_VERIFIED
under Haiku for this card only. IOVA=GPA remains INFERRED, with no payload claim.

The sensor operation at 0xab8d was NOT_REACHED. The new NACK policy therefore
has no hardware result. Post-POST readback/re-arm, timer, VRAM, scratch and
pending checks were NOT_REACHED. Failed owner/reference retention is logged.

R5 delta is empty, allowed lines empty, and post-exit command 0x0002 confirms
master disabled. No QEMU remains. No manual reset or retry occurred.
The specific deadline guard/last-write completion and reason for elapsed budget
remain UNKNOWN. Do not label this a hardware hang or an I2C timeout.

Evidence and exact command/hashes: results/20261029-a7-2aadfd99/README.md.
The launcher stopped before job-output/job.exit upload; those captures are absent.
No modified package is prepared. Another card run needs review and explicit yes.
S1 remains incomplete. D1 and other write stages are unapproved.
Validation: full make check passes. Its log is work/S1A7RUN6/check-final.log.
