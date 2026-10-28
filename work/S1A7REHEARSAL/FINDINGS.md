# Findings

The user supplied Claude's ESC-003 resolution on 2026-10-28. Implementation and
cardless retries are authorized. A physical fourth launch remains unapproved.
The hard-link failure is KNOWN. Its filesystem cause remains UNKNOWN.
The cardless expected refusal occurs inside openDevice during owner prepare.
Thus shell open returns failure after entering the callback, rather than yielding
an open descriptor. The rehearsal must distinguish that from devfs open failure.

The first corrected cardless rehearsal passed in 52.34 seconds. All three
artifacts passed size/hash checks and retained their inodes across mv. The node
appeared and open entered the native callback. KNOWN: no matching PCI card was
found before reservation. The shell's ambiguous redirect accompanies the
callback failure. No request/grant/physical event was reached. The identity
probe's no-card failure is expected and is not a hardware identity result.

The initial host fixture run lacked its inert host variable. It was corrected
before any guest. The default mediaflux ROM path was absent in this session.
The existing byte-identical private ROM in ~/haiku-cross/vbios/ was selected
through K40_VBIOS. Build checks enforce the approved ROM hash.
The existing formatter stalled inside the process sandbox. Its two owned
processes were stopped, and formatting completed outside that sandbox.
No VM was stopped by that correction.

Validation finished: make check passes in check-final.log. Its first run found
only stale generated provenance after the diagnostic shifted C++ line numbers.
Regeneration fixed that report without changing reviewer checks. Negative
runtime fixtures show build validation rejects changed job bytes, an altered
owner hash and missing rehearsal evidence, then accepts the unchanged package.
All three original run recorders still pass. No QEMU guest remains.
