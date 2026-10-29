# S1MEMUPLOAD: bounded physical-VRAM upload and test path

## Why and inputs

Depends on S1MEMCONTRACT, S1MEMARENA and S1MEMFAULTS. Read their contract/interfaces,
STATUS, Bootstrap.*, native BAR mapping code, and the selected slow-window/BAR
flush sources cited in S1-INTEGRATION-CHOICES. Do not use trace addresses as storage.

## Outputs

- Native bounded physical-VRAM read/write/bootstrap operations with scoped ordering.
- Pattern/complement, alias and transfer-boundary tests with independent read oracle.
- Generated evidence/operation report with --check; work/S1MEMUPLOAD/{PLAN,FINDINGS,RESULT}.

## Work and invariants

Use owned arena tokens, validated physical extents and an explicit aperture/cache
profile. Serialize selector plus data access for the complete bounded transaction.
Handle crossing windows and chunk boundaries; reject overflow and partial coverage.
Use the source-supported CPU ordering and BAR flush protocol with count/time
limits. A CPU fence, flush completion or CPU echo alone is not generic DMA proof.
Return an explicitly scoped staged/readback/protocol result, not a forged general
Buffer publication flag. Keep experimental references owned and retained until
their consumer and safe-removal contracts are satisfied.

Specify the finite live test extents and distinct address-dependent patterns.
All writes precede verification reads within a pass so aliases cannot pass by
immediate write/read reuse. Use complements and explicit untouched controls if
source supports them. No unmapped/foreign address probe or live free as a test.
Preserve the A7 scratch reservation; a larger arena test needs its own reviewed
ownership and write inventory. Do not claim GPU-VA translation from slow-window IO.

## Checks and limits

Test every chunk/window boundary, aliases, stale tokens, wrong profile, timeouts,
failed write/read/flush and partial effects. Unknown publication protocol denies
consumers instead of selecting a fence-only fallback. Native link without a load.
Run report --check, make check and diff check; RESULT <=40 lines, one main commit.
No card, VM, root/reset/binding change, executable package or run authorization.
