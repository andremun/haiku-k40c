# S1MEMFAULTS: scoped baselines, discovery and phase diagnostics

## Why and inputs

Depends on S1MEMCONTRACT. Read STATUS, S1-MEMORY-CONTRACT, first-batch gates,
S1-INTEGRATION-CHOICES routing/release sections, current A7 diagnostics and
launcher/observer/R5 interfaces. Follow selected pinned MC/FB/MMU/BAR/TOP sources
only as required. Read capture-format documentation before interpreting captures.

## Outputs

- A source-backed fault/read catalog: address expression, access semantics,
  reset/POST validity, engine/context scope, observed raw values and stop rules.
- Bounded snapshot/discovery and buffered phase-diagnostic code, plus host tests.
- Generated source/evidence report with --check and work/S1MEMFAULTS/{PLAN,FINDINGS,RESULT}.

## Work and invariants

Separate safe pre-write baseline from post-A7 and per-operation snapshots.
Cover the effects actually in this batch; do not claim whole-chip fault coverage.
Classify read side effects, W1C/clear semantics and incomplete/unknown observations.
Preserve original faults. Do not clear an unexplained baseline to obtain PASS.
A mandatory unknown/destructive read protocol blocks that hardware phase.
Read TOP only with a bounded sourced protocol. Record routing without assuming
runlist zero. PBDMA-count write-all/restore probes are excluded from this batch.
If required coverage depends on such a write, report the scope dependency rather
than silently adding it. Do not enable interrupts or scheduler/channel activity.

Keep source-backed phase IDs, operation/offset, primary/cleanup errors, elapsed
and poll counts. No MMIO solely for pretty output. Fixed-capacity overflow fails
closed; deferred output follows permit revocation. Log progress as deferred data.

## Checks and limits

Inject missing/dirty baselines, unsupported routing, partial reads, overflow,
stalled/backward clocks and mismatched generations. Native build only, no load.
Keep existing observer task/FD proof and R5 allowance unchanged. New probes need
source and explicit future scope, not hostSimulation on a physical backend.
Run report --check, make check and diff check; RESULT <=40 lines and one commit.
No VM/card/root/reset/binding action or permission expansion is authorized here.
