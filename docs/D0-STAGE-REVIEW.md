# D0 mapping observation package for review

Scope: S1D0PACKAGE. No physical run occurred in this task. S1 remains incomplete.
User hardware approval is recorded in ADR 008. ADR 006 still controls retries.

## Exact stage

Run from the repository root, without root:

```sh
python3 tools/haiku/d0_run.py --check
python3 tools/haiku/d0_run.py
```

The first command checks prerequisites and starts no guest. The second starts
one disposable Q35/KVM Haiku guest with only `0000:04:00.0` assigned.
The launcher accepts no QEMU options or artifact paths. Its two VFIO isolation
checks use the existing B5 preflight. It rejects other GPU_BDF values and root.
The independent pidfd watchdog limits the actual QEMU child to 600 seconds.
The shared guest lock rejects another running QEMU guest.

R5 in `docs/REQUESTS.md` must be satisfied first. The user starts the read-only
kernel journal stream. The agent does not run a privileged command. The launcher
requires a live journal reader, a kernel baseline and append-only bounded data.
New IOMMU/VFIO fault indications stop the stage. A stop requires a report and
user authorization before another guest run, including a parser false alarm.

## Native effects

The unchanged B5 identity probe reads PMC_BOOT_0 and PCI command. It writes no
GPU register. The new `D0_MEMORY_NO_DEVICE` probe uses only the owner module API.
It allocates 4096 aligned bytes, checks all logical bytes through CPU writes and
reads, verifies denied DMA publication, and consumes the startup latch as Failed.
The permanent owner retains the whole backing allocation across two detachments.
A reload must show the same GPA, size and token, a later lease and quarantine.
The client exports no device node. Its allowed kernel imports are checked.

The standard VFIO startup reset remains permitted. Firmware and Haiku PCI setup
can affect device state. The package does not claim that the whole boot is free
of writes. Neither POST nor a DMA provider is enabled.

## Source and artifact binding

`tools/haiku/d0_stage.py --check` compares `work/S1D0PACKAGE/stage.json` with the
current source and artifact bytes. That record contains full SHA-256 values for
the identity probe, owner, memory probe, observer, QEMU and stage source files.
The guest exports its kernel before the probes load. Its hash must match B5.
The suite is revalidated immediately before process creation.

The userspace observer derives from exact Ubuntu strace 5.16-0ubuntu3 sources.
`tools/observer/build.py --check` checks the original source and generated patch.
The original decoder adds bounded group status, container attachment, device
identity and map/unmap fields. Every close is captured, including anonymous FDs.
Old S1D0OBSERVER captures remain records of the earlier decoder generation.
The new inert group fixture is `work/S1D0PACKAGE/group-null-trace-02.log`.
All its ioctls failed on `/dev/null`. It is not VFIO success evidence.

## Evidence cutoff and limits

The host requires exact probe roles, successful B5 identity, kernel identity,
retained owner extent and a guest ready handshake. QMP supplies the realized
qtree, global system-memory FlatView and ramblock sizes. The parser requires a
Q35 host, fixed 4 GiB RAM, exactly the approved VFIO device and no virtual IOMMU.
It checks that the full allocation lies in one realized system-RAM range.
The ramblock Offset column is internal ram_addr_t. It is never treated as HVA.

The observer must prove a viable group, successful attachment to a known
container, correct device FD, supported IOMMU setup and complete successful map
coverage. Failed, opaque, ambiguous or unsupported histories fail closed.
Mapping and related FD operations must belong to the owned QEMU process.
Unrelated closes from its other threads have no mapping effect.

The host drains the trace after topology queries, rejects partial records, then
records the exact trace prefix and coverage witness before releasing the guest.
The retained native backing survives that handshake. The final raw trace includes
controlled shutdown, and its remaining records must parse completely.
Tracer death or failure to finish invalidates the run. Evidence files are fresh
and bounded. Kernel logs are preserved on failure when readable.

A pass establishes structural API mapping coverage at the recorded cutoff only.
The candidate IOVA equals GPA under the selected source-backed topology. This
remains INFERRED until live evidence supports the conditional address chain.
No pass installs a provider, publishes an IOVA, proves CPU/GPU visibility or
verifies device payload. Q7 remains open. D1 and later S1 work remain necessary.

## Checks and retained records

Host tests cover native retention, strict binding, topology holes, cutoff races,
partial output, fault streams, HTTP transfer limits and observer death/watchdog.
Positive VFIO-format fixtures in tests are explicitly synthetic.

`results/20261027-d0-owner-readiness/` records a passing cardless owner reload.
`results/20261027-d0-topology-fixture/` records actual cardless QMP formatting.
Neither result is K40c evidence. Native linking and CPU checks do not establish
physical DMA. The final repository check is recorded in
`work/S1D0PACKAGE/check-final.log`. Claude review remains pending in the batch.
