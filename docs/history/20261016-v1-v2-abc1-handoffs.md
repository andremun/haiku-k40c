# V1, V2 and ABC1 handoffs (history)

Moved from `docs/STATUS.md` on 23 October 2026. Historical record. The current state is in `docs/STATUS.md`.

## V1 handoff (historical; input blockers resolved by V2)

Purpose: revise possible mistakes made by "Local" and approach the
machine-dependent implementation. `docs/S1-VERIFICATION.md` records the
remaining gates. All existing C++ checks and new targeted tests pass on the
host; this is neither native Haiku verification nor GPU evidence. The ROM was subsequently found in `~/mediaflux/vbios/` and verified against
the recorded size/hash; saved decoder output is present. The missing-ROM
blocker is resolved, but fresh decoding/A3 acceptance remains pending. Restore pinned
reference sources and the verification environment before full acceptance.
No hardware, VM, host service or push operations were performed in V1.

### ROM follow-up (2026-10-16)

User provided `~/mediaflux/vbios/`. Offline hash and size match the recorded
capture exactly. Updated the generated input inventory with the explicit ROM
path and documented the saved decoder output hash/warnings in
`reference/vbios/README.md`. No decoder rerun, source validation or card
access occurred. Source/toolchain/dependency blockers from V1 remain.

## V2 current handoff

The missing reference-source and verification-environment blockers are resolved.
Use `tools/restore_verification_refs.py --check` and the isolated PyYAML
environment documented in `work/V2/RESULT.md`. `make check` now passes, including
all positive-input trace/QMD tests. No pytest exit override remains. V1's code
now has repository-wide host-check evidence; its original failed attempt is
retained as history. No native Haiku or GPU result follows from these checks.

The ROM is verified and the independent pinned decoder was rebuilt and run.
Fresh full output equals the saved output, including warnings. A3 inventory
rework is now a feasible next bounded task, but has not started or been accepted.
The native cross-compiler/header/matching-kernel bundle remains absent here.
No GPU, VM, sudo, host driver/service or push operation occurred in V2.

## ABC1 current handoff

See `docs/ABC-CARDLESS-OUTCOME.md` for the actual A/B/C matrix, reproduction
commands and remaining gates; `work/ABC1/RESULT.md` and `evidence.json` retain
checks/hashes and unsuccessful attempts. This work revises possible mistakes
by "Local" and advances toward machine-dependent implementation. It is not
acceptance of the earlier rejected A3 branch or evidence of a working GPU.

The pinned cross compiler and headers are restored under `build/haiku-cross`.
Both native probe configurations and four freestanding core components compile.
B3 host failure tests pass, including cleanup failures. Native linking/loading
is blocked because three disposable TCG guests did not reach their test job;
all watchdogs cleaned up, KVM is absent, and further VM variants stopped under
ESC-001. The matching kernel is not substituted. Existing vm-test.sh is unchanged.

**Update 2026-10-18 (ESC-001 resolved).** The block above is history. With
`/dev/kvm` now available, the native gate passed on a known-working guest:

```sh
python3 tools/haiku/cardless_run.py --base <opencode-haiku>/vm/system.qcow2 --cpus 2 --kvm
HAIKU_CROSS=$HOME/haiku-cross bash tools/haiku/build_backend.sh
python3 tools/haiku/cardless_run.py --base <opencode-haiku>/vm/system.qcow2 --cpus 2 --kvm \
    --driver build/haiku/k40_cardless_probe
```

Runs `build/cardless/20261018-152513` (kernel export) and
`build/cardless/20261018-152628` (`k40_os: PASS`). The opencode-haiku VM must
be shut down before a run; the runner uses a disposable overlay. Evidence
copy: `opencode-haiku/results/t7610-20261018-driver-native/`. This proves
link and load on Haiku without a card, nothing about the K40c.

A3 inventory and raw-ROM structural coverage, source cross-reference and trace
interval join pass generated checks. The host interpreter refuses hardware and
default-denies board helpers. B2 actual GPU mapping/publication and C2/C3 full
FIFO/MMU/channel integration still require design/review and subsequent hardware
evidence. A5 decisions and unknown I2C device remain open; A7/B5/card C3 not run.
The v6.8 comparison supplement is incomplete due HTTP 429, not evidence that
selected sources differ. No push, physical GPU access, sudo or host-service
change occurred. Rebuild local committed-source review artifacts with
`python3 tools/review_bundle.py`; external firmware/caches are not bundled.
