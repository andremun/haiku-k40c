# S1A7REHEARSAL2: stage outside watched paths and verify reloads

Implement Claude's REWORK review of 88678c4, supplied by the user 2026-10-28.
Use /boot/system/non-packaged/.k40-a7-staging outside watched add-on folders.
Keep guest size/hash checks and cross-folder same-inode mv. No hard-link/copy
fallback. A move error stops and is reported. Keep fixed devices and permissions.

Expected cardless behaviour: client init publishes misc/k40_a7_stage without
starting hardware. The one open calls the permanent owner's prepare. PCI
search finds no matching card, before reserve_device or BAR mapping. The owner
enters Failed state (3), and client open returns B_ERROR (-1, 0xffffffff).
A native helper must record the raw Haiku status. No request/grant is produced.
Rehearsal-only reload after that refusal must preserve the same resident owner
and Failed state, without another open or preparation. Count actual driver
initializations and owner loads. Reject any add/load from partial/staging names.
Use the same production job and binaries until its expected open refusal.

Rerun cardless without approval. Preserve old evidence. Rebuild and bind passing
rehearsal to the exact package. ESC-003 direction remains accepted, but its task
state is reopened until passing rework. No fourth physical run is authorized.
Record make check's dependency on the ~/mediaflux network mount. Run make check,
update PLAN/FINDINGS/RESULT and STATUS, prepare Claude review and commit on main.
