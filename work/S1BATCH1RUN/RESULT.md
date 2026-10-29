# Result

PASS: one approved acb2aca combined A7/BAR1 launch, 148.54 seconds.
Capture: results/20261030-batch1-a7-bar1-ec8db47d/.
Review: docs/S1-BATCH1-RUN-REVIEW.md.

KNOWN / HARDWARE_VERIFIED under Haiku on 04:00.0 for this finite scope:
A7 POST/readiness, owned physical transfers, BAR1 A/B initial mapping,
B/B remap, A/B restore, targeted invalidations and owned-context disable pass.
Seven objects remain retained. Selected guest fault snapshots pass.
R5 selected logs are identical; no allowed lines. Host mastering was off at exit.
Public grant signatures and observer replay pass offline.

S1 is incomplete. Q7 and Q11 stay open; no channel/PBDMA/submission proof,
host payload visibility, measured effective UC type or S2/S3 success follows.
Approval is consumed; marker retained. No second launch.

Validation: make check; package --check; offline result generator --check;
four evidence-integrity rejection cases (temporary copies only).
Commit on main; no push.
