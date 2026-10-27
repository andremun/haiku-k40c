# 008. Hardware approval for the sequential S1 programme

Date: 2026-10-27. Status: accepted (direct user instruction).

The user requested continued task-by-task work through S1, one task per commit,
then preparation for S2/S3 if S1 succeeds, with a final review document. The user
then stated: "Hardware access is approved."

This authorizes the planned S1 hardware work on the development card
0000:04:00.0, including necessary reviewed first-write stages when their concrete
implementation and preconditions are ready. Do not request the same general
hardware approval again. Record the exact executed scope and evidence per stage.

The other hardware and evidence rules remain: no root, host binding change,
manual reset, other GPU access, or push. Verify VFIO isolation/access, one guest,
disposable overlays, bounded execution and write-once evidence. Hardware approval
does not supply missing DMA, visibility, readiness or quiescence proof, or waive
required stage review. After a launcher-reported stop, ADR 006 still applies.

S2/S3 preparation is conditional on actual S1 success. Do not label simulation,
linking, mapping observation or source analysis as S1 hardware success.
