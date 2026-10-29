# Integration decisions

The original A7 phase stays byte-for-byte as in run7. Build a fresh child config
with its own key/nonce using original build.py pure config/inputs helpers and
frozen OWNER/CLIENT source lists, writing to build/memstage/package/a7/ rather
than consumed package-buffer. Reuse the verified original helper and identity.
Do not call the old build/validate entry points: their historical wide manifests
include test/Makefile that necessarily changed in this batch. Do not regenerate
old consumed-package evidence to conceal the difference.

The new outer job installs a read-only preflight driver, runs the unchanged A7
job as a child on its original phase-scoped service, then waits for the outer
host's continuation gate before installing/opening the memory phase. The old
child job.exit cannot end the full guest experiment. Physical continuation
requires current A7 PASS/evidence order, kernel, unchanged witness and R5.
Cardless continuation instead requires the exact existing no-card A7 refusal;
no private signing key is read, no grant is produced. Use identical outer job
bytes/generator/binaries in both modes; only ephemeral HTTP ports differ.
If a physical phase fails, do not authorize a later phase. The unchanged A7
installer uses its own unwatched staging folder; the new installer uses a
separate unwatched folder and the same size/hash/inode-preserving move contract.

Use separate memory request/grant magic/key/nonce. Proposed frame: 256-byte
request/message and 64-byte Ed25519 signature (320-byte grant). Fields:
magic[0:16], nonce[16:48], plan hash[48:80], owner challenge[80:96],
epoch[96:104], owner/lease[104:112], BAR0 base/length[112:128],
BAR1 base/length[128:144], expected VRAM bytes[144:152], arena begin/end[152:168],
read-only BAR1 prefix bytes[168:176], reserved zeros[176:192],
A7 transcript/witness digest[192:224] (zero in request, nonzero signed grant),
reserved zeros[224:256]. Grant magic differs. Compare all fixed/request fields,
require canonical Ed25519 scalar, validate signature over all 256 bytes, no replay.
The plan hash includes protocol/source/profile/write scope, not artifact hashes
that would create a build self-reference. The public manifest and exact rehearsal
bind actual artifact/job/kernel hashes separately.

Native prepare does PCI enumeration and explicit-UC CPU mappings only. No GPU
reads are needed to frame BAR resource bindings; compiled expected VRAM/exclusions
are request fields. After the signed A7 attestation, the controller enables its
private memory gate, discovers/checks actual normal VRAM, configures the arena,
captures its own MC-only then complete post-A7 baselines, preflights the disabled
BAR1 context, zeros/references the debug objects and tests data A/B, captures
Physical, and invokes Mapper. Revoke before deferred diagnostic output on every
return. A separate read-only G0 driver records the actual pre-A7 MC baseline.

Obtain and retain the original A7 API v2 module reference. It holds the sole PCI
reservation; no second reserve_device call. New module KEEP_LOADED, uninit denied,
single prepare/open/run latch survives client unload/reload and all failures.
No-card prepare returns B_ENTRY_NOT_FOUND (Errors.h:104, encoded 0x80006003),
not generic shell errors. Keep the original A7 helper unchanged. New fixed-node helpers use the same
raw-status mechanics for the preflight and memory nodes, with no path options. Cardless job must install all artifacts,
check final-name-only loads and exercise harmless second driver load; no grants.

NativeIo must gate every write privately. Value/range policy derives from arena
records and Faults phase: debug only zero, data only physical-address pattern or
complement; unreferenced tables only zeros and exact derived PDE/PTE/instance
fields; referenced SPT only entry 0 in remap/restore phases. Selector/data stay
under Window lock, complete Mapper experiment under Mmu lock. Mode RMW only
once after Tables; PDB/command ordering and exact target/count; enable only owned
instance after Tables, disable only after Restored with matching raw ownership.
No write to 0x100c10, BAR2, PCI config, interrupts, scheduler or fault clear.
Source-only UC request, resource bounds and map result must be logged. BAR0
needs physical-window 8 MiB; map read/write UC. BAR1 maps exactly 8192 bytes UC,
read-only; full discovered aperture bounds the VMM. All mappings and VRAM retained
until guest/VFIO end after failure or successful scoped disable.

New code can live in src/memauth (freestanding Authority/Session), src/memnative
(physical Io/policy/module; kernel-only bodies guarded), and existing memstage
core. Test real crypto with a public RFC test seed via a separate explicit host
probe, not generic memstage wildcard tests. Test the production write policy
with independent raw-value cases, lifecycle failure injection and prior core
oracles. No physical backend identifies as hostSimulation.

The new closed launcher reuses stable lower-level VFIO/QEMU/observer/R5/pidfd
helpers. It needs its own single-use marker and distinct approval flag; never
reuse old A7 run flag/consumed marker. Fresh task/FD topology coverage before
A7 grant, continuous witness and R5 supervision through memory completion,
write-once incremental evidence and <=600 s watchdog. Final PASS provisional
until exact guest completion, trace closure, owned processes exited and host
bus-master bit clear. After any launcher stop ask before another launch.
No card run is authorized during this preparation.
