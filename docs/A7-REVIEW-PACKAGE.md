# A7 sensor response package (2026-10-29)

**Current status:** Claude accepted commit 2818763 and the user approved one
run of `build/a7/package-i2c/`. It launched once and stopped at POST Timeout,
0x85d6, before the sensor operation. The package is consumed. No retry is
approved. See results/20261029-a7-2aadfd99/README.md. S1 remains incomplete.
D1 is unapproved. The preparation/review record below is historical.

Review scope: `git diff 3ac1176..HEAD` after this macro task is committed.
This package adds precise I2C diagnostics and the user's ADR 010 response
policy. No register address, DMA permission, readiness step or R5 rule expands.
ADR 009's single startup enable-line allowance remains unchanged.
The exact new binaries passed cardless rehearsal in 78.34 seconds at
results/20261029-104357-a7-rehearsal/. This is installation/lifetime evidence.

## Diagnosis and approved package scope

KNOWN / TRACE_VERIFIED: Linux attempted both sensor pairs at 0xab8d. Each
register (0x19 and 0x0d, intended value 0x73) has four address frames. Every
frame sends 0x98 and receives NACK. No register/value bytes were sent.
Nouveau bios/init.c:1033-1056 ignores the return and continues the script.
Source-bound decoder: tools/a7/i2c_capture.py, work/S1A7I2C/linux-i2c.json.
Eight captured slave responses replay through the actual DedicatedI2c code as
address NACK with a clean STOP. An ACK-all control sends all three bytes.
This is response replay, not a reproduction of Linux's timing or adapter code.

INFERRED: a similar NACK may explain the Haiku stop. UNKNOWN: run5's actual
I2C error class and which pair failed. The previous log cannot settle that.
The 99.799 ms pre-acquire gap does not establish a required settle wait.
Acquire/release intervals are 6.272 ms and 8.885 ms for two separate transfers.
A pad mode log alone is not proof of a pad register write: dedicated-pad
callbacks have no mode function. No guessed delay or pad write is added.

ADR 010 records the user's explicit response-policy choice. Only the exact
0xab8d pairs, on the immutable ROM/default bus/address 0x4c, get at most four
attempts. An address NACK may retry after a successful bounded STOP. Four such
NACKs may continue POST as ReferenceNack. An ACKed transfer completes normally.
Payload NACK, IO, stretch, timeout, clock, budget and cleanup failures stop.
Every other address/PC/pair remains fatal on error. Repeated or out-of-order
sensor pairs are denied. No recovery pulses or implicit reinitialization occur.
The existing 100 ms/20,000-guard-operation per-attempt, 10 s POST and 15 s startup
bounds remain. STOP success means callbacks completed, not proof of bus recovery.

The write inventory now lists this bounded policy explicitly. The data bytes
remain the vendor ROM's approved values. This does not claim sensor presence or
successful configuration after NACK. Ordinary physical backends stay gated.

## Native I2C diagnostics

Each attempted transaction emits a fixed six-line record:

| Event | a | b |
|---|---|---|
| I2C_REQUEST | ROM PC | address7 << 16, register << 8, value |
| I2C_DISPOSITION | attempt 1..4 | Fatal=0, Complete=1, RetryAddress=2, ReferenceNack=3 |
| I2C_RESULT | primary error | STOP/cleanup error |
| I2C_PHASE | transfer phase | bit 0..7 MSB first, 8=ACK |
| I2C_TIME | transfer guard elapsed us | cleanup guard elapsed us |
| I2C_WORK | guard-operation count | last pre-cleanup register read |

I2cError values: None=0, HardwareDisabled=1, Input=2, NotInitialized=3,
Io=4, Nack=5, Stretch=6, Timeout=7, Clock=8, Budget=9.
Transfer phases: Idle=0, Start=1, Address=2, Register=3, Value=4.
Diagnostics preserve both primary and cleanup failure. They add no MMIO reads.
All records remain bounded by the fixed attempt count and existing deadlines.

## Exact inputs and commands

`work/S1A7I2C/package.json` is the generated artifact/source manifest.
`write-inventory.json` in that folder lists all 544 possible script-write
locations from the exact ROM's structural preflight and independent access
policy decoder. Each row gives the script PC, opcode, register, width and
permission. The immutable private ROM supplies values, masks, tables and runtime
branches; the inventory is conservative, not a prediction of an executed path.
No ROM instruction writes the flush-target register. Driver writes are listed
separately in the same file. Private firmware and signing material stay in build/.

| Artifact | SHA-256 |
|---|---|
| `k40_a7_owner_module` | `a14758b05384bf5669ac49795903709e1dd5a9c70beccc8a7cf46787c1c625c3` |
| `k40_a7_stage` | `d11b0d3773e8f1a206a98b79b85a1c6e7c73948dbe096001d472ef0ee66ee122` |
| Open helper (`tools/a7/open_session.c`) | `58bec7c51730bf95f541c61c8ed9b8379b97f1c2b335702de0f9542698914977` |
| Identity probe | `8c45ec7bf2a2a16f3981431a3d0e5ee3588cfa9df63429ea51b01cc93fdf9d2f` |
| Observer | `75b7aeed34785c8ac729d68cbca83d256434acb036e336d0adf5a4bdc30bc7a2` |
| Guest kernel | `2da9a5b98719b40a61893836fb9c9e393e92e44f470e8af2024e76d50e2d2c62` |
| ROM | `aecb0b5fa466f64e2651a551a3cad57cccbdedd929e3996f542201af06ff1f54` |

From the repository root, read-only package verification is:

```sh
export K40_VBIOS="$HOME/haiku-cross/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom"
python3 tools/a7/build.py --check
python3 tools/a7/rehearse.py --check
python3 tools/a7/host_check.py --check
python3 tools/a7/i2c_capture.py --check
python3 tools/a7/i2c_replay.py --check
python3 tools/a7/run.py --check
```

After review and the user's explicit yes for this package, the runtime checks
and the single run command are:

```sh
python3 tools/a7/run.py --host-check
python3 tools/a7/run.py --run-approved-A7-once
```

The execution option is an operator approval assertion; it does not obtain or
replace human approval. The default and `--check` never start a guest. The new package directory is `build/a7/package-i2c/`. The host
signing key is a fresh per-package Ed25519 key, mode 0600. The launcher atomically
creates a consumed marker before starting QEMU. Even a failed launch consumes
the package. A retry requires reporting the stop, a new reviewed package and
fresh approval. Do not remove the marker to rerun.

Build-only reproduction (no guest) uses `python3 tools/a7/i2c_capture.py`,
`python3 tools/a7/i2c_replay.py`, then `python3 tools/a7/host_check.py`, followed
by `python3 tools/a7/build.py`. Keep the exact verification-only dependency at
`~/haiku-cross/src/orlp-ed25519`, revision recorded in `crypto-sources.json`. Recover it with
a clean clone of https://github.com/orlp/ed25519 and checkout
`b1f19fab4aebe607805620d25a5e42566ce46a0e`. The original zlib notice accompanies
that checkout and the private package. The dependency is external original
code; no signing/key-generation function is linked into the kernel. Rebuilding
changes the reviewable package if any input differs. A consumed package is
preserved rather than reused.

## Native ownership and fresh witness

The separate KEEP_LOADED module owns the platform, image, board transport,
controller, once-per-boot latch and storage. It refuses module teardown.
Haiku's PCI reservation must succeed; a second matching card or another driver's
reservation fails preparation. The regular D0 module has no physical POST entry.
Physical helpers use an owner-controlled execution permit. They report
`hostSimulation=false`; ordinary physical backends remain denied by default.

The native storage owner allocates DMA32 backing, aligns a 4096-byte page,
zeros it and immediately quarantines it. There is no CPU access, release or
submission API after this point. Partial failures retain backing too. The
`ArmedReference` type never sets publication, mapping verification or visibility.
It is separate from a payload Buffer. The card may write the page. Its contents
are never consumed by the CPU or reused during this guest boot.

One client descriptor remains open while the host obtains a fresh same-run D0
observer witness. The fixed request identifies the package nonce, native owner
instance, token, GPA and full extent. The host checks the exact kernel hash,
B5 identity, realized QMP system-RAM topology, device/group/container association,
READ/WRITE map coverage and the trace cutoff. No ended D0 witness is reused.
An Ed25519 grant binds these fields, the candidate IOVA and the captured proof
digest. The guest has the public key only. Signature, scope and exact-size checks
precede the first GPU write. Failed or repeated submissions consume native state.

KNOWN: successful VFIO API mappings and source-selected topology can establish
structural coverage at a cutoff. **INFERRED: the armed IOVA equals the GPA.**
UNKNOWN: hardware flush-target use, DMA payload visibility and effective
coherency. Observation is asynchronous: the cutoff is not an atomic hardware
lease. The launcher continues checking the mapping history and R5 after releasing
the grant, stopping on invalidation or lost observation. This bounds the experiment;
it does not turn the reference into a production DMA provider.

## Execution and independent readiness

1. B5 logs the PCI command and PMC_BOOT_0. Native preparation also reads these;
   native execution checks PMC_BOOT_0 = `0x0f1240a1` and memory decode enabled.
   Bus mastering may already be enabled (D0/B5 observed command `0x0007`).
2. The one-shot latch covers interrupt unarm, cold-POST decision, CRTC unlock,
   private-ring setup, dedicated I2C initialization, flush arming and FIFO reset.
   An already-POSTed card stops; this is a cold-POST experiment.
3. Write `0x100c10 = current witnessed IOVA >> 8` before the script. Execute only
   the immutable ROM and ADR 004 board policy, with bounded instructions,
   transactions and polling. Log instruction PCs and POST result.
4. After successful POST, read and record `0x100c10`, accepting that POST could
   have changed it, then write the same owned address again. Neither write is a
   script write. SOURCE_ONLY: Nouveau `fb/base.c:227,204`, `fb/gf100.c:83`.
   TRACE_VERIFIED: the Linux run made both writes (review record gives lines).
   The new Haiku writes/readback remain unverified until this run.
5. Check PMC_BOOT_0 again; read PTIMER high/low/high with bounded rollover retry,
   wait 1 ms and require advancement. Probe physical FB partition amounts using
   GK104's selected GF108/GF100 chain. Reject mixed or malformed topology and
   require the captured total of 11520 MiB physical VRAM (not usable nvidia-smi
   memory). These checks are source-backed candidates, not prior Haiku results.
6. Reserve the first normal-heap VRAM page at `0x40000`, after the source-derived
   256 KiB VGA head and before the 1 MiB VBIOS tail. The sole PCI owner has no
   other VRAM consumer. Two scratch pattern passes sample offsets 0, 0x100,
   0xffc through PRAMIN selector 0 and window addresses `0x740000`, `0x740100`,
   `0x740ffc`. BAR flush writes `0x70000 = 1` and polls bit 1 clear. Require
   `0x100` MC pending to be zero before and after scratch (a conservative stage
   condition). Do not claim that every pending bit has been classified as a fault.

The scratch page is not restored or reused before guest termination. The BAR
flush might use the armed target: A7 makes no assertion of no DMA or payload
visibility. No command buffer, channel, shader or compute job is submitted.
D1 remains a separate stage after POST; A7 success alone is not S1 success.

## Host containment, stops and end of guest

Only host `0000:04:00.0` is passed through. `vfio-pci`, an exclusive one-device
IOMMU group and writable VFIO node are checked twice. No root command, host
binding change, host BAR access or manual reset is used. Other guests are refused;
the launcher never shuts down an existing VM. The base disk uses a disposable
overlay. Evidence files are write-once and logs grow incrementally.

The existing R5 command must be running when `--host-check` and the run begin:

```sh
{ sudo journalctl -k -b -n 1 --no-pager --output=short-monotonic; sudo journalctl -k -b -n all -f --no-pager --output=short-monotonic | grep --line-buffered -iE 'dmar|amd-vi|iommu|vfio|remapping|0000:04:00|aer|pcie bus error'; } > ~/k40-s1-kernel.log
```

This is a user step from R5 in `docs/REQUESTS.md`; the agent must not run it.
For A7, **any new selected-class line** stops the stage, including informational
VFIO/DMAR and corrected AER messages. The only exception (ADR 009) is one
`vfio-pci 0000:04:00.0: enabling device (...)` line between QEMU start and the
first guest serial output, recorded in `result.json`. A stopped/replaced/truncated reader or
filter, panic, stage failure, bad kernel/identity, changed mapping, unknown
observer record, partial cutoff, missing evidence or oversized log also stops.
The native startup budget is 15 s; the host run budget is 570 s inside an
independent 600 s watchdog on the actual QEMU child. No modified retry is allowed
without reporting the stop and obtaining new permission (ADR 006).

The guest never frees the armed page. After the job, the launcher terminates its
owned QEMU and tracer, parses the final trace, and reads only the development
card's host PCI command register. Bus master bit 2 must be clear within 2 s.
The baseline upstream Linux v6.8 `vfio_pci_core_close_device` calls disable
(`vfio_pci_core.c:687-701`); disable clears bus mastering at line 595 before
cleanup. Type1 release unmaps/unpins DMA (`vfio_iommu_type1.c:2597-2609`).
`teardown-sources.json` records exact retrieval hashes and URLs outside reference/.
These are SOURCE_ONLY baseline sources, **not exact Ubuntu -138 sources**.
There is no claim of a reset at guest end. Retention lasts throughout the boot;
VFIO teardown and observed master disable are the proposed reviewed end boundary.
A missing confirmation is a failed stage, not permission to reset or rerun.

A wrong but mapped IOVA can corrupt other guest RAM without an IOMMU fault.
The fault filter does not guarantee guest memory safety or prove a clean full
kernel log. The retained exact extent and single owner reduce that risk. A wrong
unmapped address should fault, but no negative DMA experiment is authorized.

## Validation and review focus

`work/S1A7I2C/host-check.json` records 32 ROM/strap scenarios (16 complete), 192 altered-frame
rejections, seven correctly signed wrong-scope rejections, a noncanonical
signature rejection and I2C/clock failures. The actual owner/controller execute
against simulated registers; this is not card evidence. Actual NativePlatform
and client source tests cover reservation and duplicate-device failure, no permit
writes, DMA32 alignment/zeroing, partial allocation retention, partial stream
input, copy errors and reload refusal. They pass with host OS mocks
(counts in `work/S1A7I2C/check-final.log`). Native compilation separately uses real Haiku headers and the matching
kernel exports. `work/S1A7I2C/native-build.log` records successful links.

The complete `make check` passes. Its log is in `work/S1A7I2C/check-final.log`.
Review the explicit physical permit, request/grant signer, permanent retention,
write allowlist, scratch reservation and teardown boundary before approving the
next physical run. Native owner loading has both cardless and run5 evidence.
The no-card refusal has cardless evidence. Physical timer/memory/scratch behavior remains UNKNOWN. S2/S3 work remains conditional on actual S1 completion.

## Review nits and deliberate Linux omissions

FIFO preinit now requires a fresh successful read before each write to `0x200`.
It admits exactly two writes: clear bit `0x100`, then set it. Each write must
preserve every other bit from its paired read. It rejects a third write.
I2C preinit derives the dedicated bus from the immutable image. For this ROM,
the only preinit register is `0xd054`, with value 7. Other bus addresses fail.
Host fixtures exercise the actual private transport under its active permit,
including rejected addresses, values, missing reads and replay. Test access is
absent from kernel builds.

`write-inventory.json` now includes `deliberate_linux_preinit_omissions`, generated
by tools/a7/omissions.py from the same ROM and pinned source facts. These are
KNOWN / SOURCE_ONLY descriptions. They are not new captured hardware results.

| Omitted Linux setup | Addresses and operation | Reason in this A7 scope |
|---|---|---|
| Four hybrid AUX pads | `0xe50c`, `0xe55c`, `0xe5ac`, `0xe5fc`: set masked bit 0 | A7 uses the unshared dedicated script bus. It has no display/AUX client. No full Linux-preinit equivalence is claimed. |
| Seven other I2C buses | `0xd014`, `0xd034`, `0xd0b4`, `0xd0d4`, `0xd0f4`, `0xd114`, `0xd134`: write 7 | Both approved ZM_I2C_BYTE instructions select CCB bus 2. A7 initializes only its `0xd054` register. |
| ROM shadow toggles | `0x88050`: clear/restore bit 0 | The immutable ROM comes from a checked file. A7 does not fetch it through the hardware PROM aperture. |

Sources: Nouveau i2c/base.c:177-180, pad.c:77-81,102,
padgf119.c:28-39, padg94.c:33-37, busgf119.c:65-69,93,
bios/i2c.c:107-116, bios/shadowrom.c:41-55, pci/base.c:66-74,
pci/nv40.c:41-44 and pci/gk104.c:208-210. The omissions preserve the earlier
A7 scope. They do not prove that arbitrary display-related setup is harmless to
omit, and they do not authorize new pad, bus or PCI writes.

The new job also uploads bounded, write-once shell output before job.exit and
marks its device-open step. The client logs get_module failure status. These
changes add diagnostics without changing the register sequence. The first
run's exact discovery/open cause remains UNKNOWN. Three approved installation
attempts have stopped before a grant.
The old owner/client/identity/observer artifacts remain in
build/a7/approved-8974695/. The immutable original manifest and captures are in
results/20261028-a7-post/. Fresh review and explicit one-run approval are required.

## Installation and exact cardless rehearsal

The job installs into /boot/system/non-packaged/add-ons/kernel, the folder that
B5 and D0 used. Each file downloads into the staging folder
`/boot/system/non-packaged/.k40-a7-staging/`, which Haiku does not watch for
drivers or modules. Guest `stat` checks the size and `sha256sum` checks the bytes
against the host manifest. `mv` then moves the file to its final name in
`kernel/generic/` or `kernel/drivers/bin/`. Equal inode numbers before and after
are required: this proves a rename on one volume, not a copy. A failed download,
size or hash mismatch, failed move or inode change stops the job. There is no
copy fallback. The owner module is installed before the client. Each device
symlink is created only after its binary is complete and checked.

The client driver now loads the owner module in `init_driver` and calls the
read-only `observe_client_load` hook (module ABI 2). The owner constructor only
sets fields. The card search, PCI reservation and storage preparation happen only
in `prepare`, called by the one open. The job opens the device once, through the
native helper `tools/a7/open_session.c`. The helper prints the raw Haiku status of
`_kern_open` (bash misreports negative Haiku status values) and keeps the
descriptor as fd 3 for the rest of the job. The helper's libroot link input was
exported from the guest (`tools/a7/runtime_export.py`, `work/S1A7REHEARSAL2/runtime.json`).

Expected cardless behaviour, from `docs/tasks/S1A7REHEARSAL2.md`: client init
publishes `misc/k40_a7_stage` without starting hardware. The one open calls
`prepare`. The PCI search finds no card before any reservation or BAR mapping.
The owner enters the Failed state (3) and the open returns `B_ERROR`.

KNOWN / cardless OS evidence, `results/20261029-104357-a7-rehearsal/`:

- Four installations pass size/hash/same-inode checks, then node publication
  and the one open return status 0xffffffff (B_ERROR), as expected without a card.
- All discovered/load names are final names. No partial or staging load appears.
- Identity initializes three times, client twice, resident owner once.
- Only one prepare occurs. The client reload sees the same Failed owner state.
  The reload command is cardless-only and never opens again.
- Identity's no-card failure is expected. No physical request/grant/POST occurs.

This proves native installation, final-name loading, one-open entry and the
one-shot owner state. It does not prove physical bring-up. No request, grant,
arming, POST or readiness ran.

`work/S1A7I2C/rehearsal.json` binds the exact generated job, the
four binary sizes and hashes, the guest kernel and the capture hashes.
`build.py --check` and every physical launcher prerequisite require this
matching passing record. A changed job or binary needs another rehearsal.

The original 8974695, 24fb578 and 0390b8b consumed markers and binary archives
remain. After Claude Code's review of this record, the user may approve one new
physical run.

## Host policy checks and review gate

The actual owner/controller host fixture completes after exactly nine I2C
attempts: one 0x20 transaction and four for each sensor pair. It records six
retries and two ReferenceNack continuations. Independent fatal fixtures verify
register/value NACK, STOP failure, stretch, timeout, IO and other-address NACK,
including their exact primary/cleanup error classes. These are host simulations.
The existing native, authentication and lifetime checks remain in the package.

Review the scope and failure classification against ADR 010 before offering
this package for a physical run. A fresh explicit yes still covers one launch
only. No execution command was run against the card during this task.
The filtered R5 scope, fresh witness and all other containment rules remain.
The ~/mediaflux network mount can affect default verification inputs. This task
uses the existing exact-hash local ROM copy via the K40_VBIOS command above.
