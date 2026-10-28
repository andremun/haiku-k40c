# A7 package after the cardless rehearsal (2026-10-28)

**Current status:** the exact guest job and candidate binaries passed cardless
KVM rehearsal in 52.34 seconds. ESC-003 is RESOLVED by the user-supplied Claude
review and this rehearsal. No fourth physical launch has occurred or is approved.
S1 remains incomplete. D1 remains unapproved.

Review the complete change since the last reviewed package, commit 8974695.
This includes **24fb578 and 0390b8b**, whose preinit guards and installation
changes had not been reviewed. `git diff 8974695..HEAD` covers the review scope after this task is committed. Earlier consumed markers and all three raw captures
remain unchanged. The hard-link method from 0390b8b has been removed.
The resolution is recorded in work/S1A7REHEARSAL/REVIEW-RESOLUTION.md.

## Exact inputs and commands

`work/S1A7REHEARSAL/package.json` is the generated artifact/source manifest.
`write-inventory.json` in that folder lists all 544 possible script-write
locations from the exact ROM's structural preflight and independent access
policy decoder. Each row gives the script PC, opcode, register, width and
permission. The immutable private ROM supplies values, masks, tables and runtime
branches; the inventory is conservative, not a prediction of an executed path.
No ROM instruction writes the flush-target register. Driver writes are listed
separately in the same file. Private firmware and signing material stay in build/.

| Artifact | SHA-256 |
|---|---|
| `k40_a7_owner_module` | `694ca685f555405158a58b0ac47d758420921f190be19726761c5fd5739f8baf` |
| `k40_a7_stage` | `b99101a130a7b8a391b7f7e6e3ece6ce560e98ba897023dca56ab6cf726af44c` |
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
python3 tools/a7/run.py --check
```

After review and the user's explicit yes for this package, the runtime checks
and the single run command are:

```sh
python3 tools/a7/run.py --host-check
python3 tools/a7/run.py --run-approved-A7-once
```

The execution option is an operator approval assertion; it does not obtain or
replace human approval. The default and `--check` never start a guest. The new package directory is `build/a7/package-rehearsed/`. The host
signing key is a fresh per-package Ed25519 key, mode 0600. The launcher atomically
creates a consumed marker before starting QEMU. Even a failed launch consumes
the package. A retry requires reporting the stop, a new reviewed package and
fresh approval. Do not remove the marker to rerun.

Build-only reproduction (no guest) uses `python3 tools/a7/host_check.py`, followed
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
VFIO/DMAR and corrected AER messages. A stopped/replaced/truncated reader or
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

`work/S1A7REHEARSAL/host-check.json` records 32 ROM/strap scenarios (16 complete), 192 altered-frame
rejections, seven correctly signed wrong-scope rejections, a noncanonical
signature rejection and I2C/clock failures. The actual owner/controller execute
against simulated registers; this is not card evidence. Actual NativePlatform
and client source tests cover reservation and duplicate-device failure, no permit
writes, DMA32 alignment/zeroing, partial allocation retention, partial stream
input, copy errors and reload refusal. They pass 4129 and 24 assertions with host
OS mocks. Native compilation separately uses real Haiku headers and the matching
kernel exports. `work/S1A7REHEARSAL/native-build.log` records successful links.

The complete `make check` passes. Its log is in `work/S1A7REHEARSAL/check-final.log`.
Review the explicit physical permit, request/grant signer, permanent retention,
write allowlist, scratch reservation and teardown boundary before approving the
fourth physical run. Native owner loading and the no-card refusal now have
cardless evidence. Physical timer/memory/scratch behavior remains UNKNOWN. S2/S3 work remains conditional on actual S1 completion.

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

The job uses /boot/system/non-packaged/add-ons/kernel, the proven B5 folder.
Each download uses a same-directory hidden partial file. Guest stat checks its
size, and sha256sum checks its bytes against the host manifest. The executable
file moves to its final name with mv. Equal pre/post inode numbers are required.
A failed download, size/hash mismatch, failed move or inode change stops the job.
There is no explicit copying fallback. Both paths share one parent directory.
No staging directory or hard link remains. The owner finishes before the client.
Each device symlink is published only after its binary is complete and checked.

B5-BEGIN precedes identity publication. A bounded 30-second loop checks for the
A7 character node without opening it. The script then attempts exactly one open.
The native no-card diagnostic adds no GPU permission or register access.

`tools/a7/rehearse.py` starts a fixed cardless KVM guest with a disposable disk
and an independent 600-second watchdog. It shares the production exchange and
job generator. It copies the exact identity, owner and client binaries. It never
reads the host signing key, sets grant readiness, signs a grant or supplies VFIO.
The script has no rehearsal branch. The runtime HTTP port is its only variable.

KNOWN / cardless OS evidence: results/20261028-134127-a7-rehearsal/ records three
successful size/SHA-256 checks and unchanged inodes, A7-DEVICE-PUBLISHED,
A7-OPEN-DEVICE, and the native REFUSED no matching PCI card before reservation.
The client then logs FAIL client prepare. Shell open reports ambiguous redirect
and exits 1, because owner preparation occurs inside the callback. That is the
expected refusal, distinct from the earlier absent-node/devfs error. It does
not yield a prepared descriptor. No request, grant, arming, POST or readiness ran.
The identity probe's no-card failure is also expected in this cardless guest.
This proves native installation and callback entry, not physical bring-up.

`work/S1A7REHEARSAL/rehearsal.json` binds the canonical job rendered with port 0,
the three exact binary sizes/hashes, guest kernel and immutable capture hashes.
Validation also compares the actual saved job using its recorded runtime port.
`build.py --check` and all physical launcher prerequisites require this matching
passing record. A changed job or binary requires another cardless rehearsal.
The public package manifest binds the sources, binaries and host checks as before.
Building a candidate alone does not make it eligible for physical execution.

Four host fixtures cover corrupted/short downloads, chmod/move failure,
copy-instead-of-rename detection, existing destination, bounded node wait,
one-open ordering, and rejection of incomplete/no-card/physical rehearsal logs.
The full native test and source-bound host reports remain separate from this
actual guest evidence. No physical retry command was executed in this task.

The original 8974695, 24fb578 and 0390b8b consumed markers and binary archives
remain. Claude must review this package, including the earlier FIFO and I2C
guards. Only after that review may the user approve one new physical run.
