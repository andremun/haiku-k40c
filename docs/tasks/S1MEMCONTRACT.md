# S1MEMCONTRACT: first-batch evidence and operation contract

## Why and inputs

First implementation task after S1-BATCH1-REVIEW.md is accepted. Read STATUS,
that review plan, DMA-CONTRACT visibility/D1 sections, MEMORY-CONTRACT,
S1-INTEGRATION-CHOICES and the selected current memory/owner/permit interfaces.
Follow only the pinned source chains needed for the candidate memory path.
Do not read unrelated tasks, tools/check_repo.py or tests/accept/.

## Outputs

- docs/S1-MEMORY-CONTRACT.md: object/address roles, allowed consumers, ownership,
  operation order, effective CPU aperture/cache assumptions, barriers/flushes,
  evidence scopes, exact stop rules and unresolved facts.
- work/S1MEMCONTRACT/{PLAN,FINDINGS,RESULT}.md and a deterministic generated
  source/evidence matrix with a no-write --check helper under tools/.
- Proposed distinct memory-stage authority/request/grant/phase boundaries. Keep
  A7's consumed package and permit scope unchanged. No client-supplied callbacks,
  register ranges, addresses or claimed proof flags as execution authority.
- Single permanent card/resource owner and one reservation, with a separate
  startup-once latch and memory-stage phase state. Never reset the A7 latch or
  promote its permit after POST. Any phase-specific handoffs must share the
  launch/owner/combined-plan binding and reject skips/replay after failure.

## Work and gates

Separate host arm-only references from physical VRAM, BAR virtual and future
channel GPU-VA objects. Decide the smallest scoped VRAM bootstrap/publication
profile supported by source. Do not set a general host-DMA provider verified.
D1 completion/readback alone cannot close Q7. Resolve what a flush-target readback
can mean before requiring an address echo. Zero after POST does not prove clearing.
Specify relevant faults, phase deadlines/poll counts, CPU ordering, retained
references and reviewed guest-end termination. Resolve the selected FB/MMU debug
allocations and BAR bootstrap dependencies without importing another chip's path.

Every operation/constant needs pinned source and scope. Record live-unknown
facts and exact read-only user commands in REQUESTS only if required. Unknown
mandatory contracts block the runnable branch, while independent host work may
continue. A revised experiment scope must be reviewed before approval is sought.

## Checks and limits

Test stage/token/scope confusion and unsupported-profile rejection if adding
contract code. Validate source matrix and --check. Record consulted Nouveau
files in licensing.md. make check, diff check, RESULT <=40 lines, one main commit.
Host/source work only. No VM/card, PCI/BAR, reset, root, binding or publication
promotion. This task cannot approve or run the proposed combined experiment.
