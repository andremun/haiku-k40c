# 008. Hardware approval for the sequential S1 programme

Date: 2026-10-27. Status: accepted (direct user instruction).

The user requested continued task-by-task work through S1, one task per commit,
then preparation for S2/S3 if S1 succeeds, with a final review document. The user
then stated: "Hardware access is approved."

This authorizes the planned S1 read-only stages on the development card
0000:04:00.0 when their concrete implementation and preconditions are ready.
Do not request the same general approval again for a read-only stage.
Record the exact executed scope and evidence per stage.

A write stage needs the user's go-ahead each time, before it runs. This
applies to A7 and to the first write of each C3 stage, as in ADR 007 and
`docs/S1-PLAN.md`. A write stage is any stage whose driver can write a GPU
register, program the card, or start device DMA. Present the reviewed stage
package (command, driver hashes, writes it can make, stop conditions) and
wait for an explicit yes. This approval does not carry over to another stage
or to a second run of the same stage.

The other hardware and evidence rules remain: no root, host binding change,
manual reset, other GPU access, or push. Verify VFIO isolation/access, one guest,
disposable overlays, bounded execution and write-once evidence. Hardware approval
does not supply missing DMA, visibility, readiness or quiescence proof, or waive
required stage review. After a launcher-reported stop, ADR 006 still applies.

S2/S3 preparation is conditional on actual S1 success. Do not label simulation,
linking, mapping observation or source analysis as S1 hardware success.

## Amendment 2026-10-28 (user decision)

The first version said that the approval covered "necessary reviewed
first-write stages" and that the approval was not to be requested again.
That conflicted with ADR 007, ADR 005 and `docs/S1-PLAN.md`. The user
decided: write stages need the user's go-ahead each time. The text above
is corrected. Task records written under the first version keep their
dated wording. No write stage ran under the first version.
