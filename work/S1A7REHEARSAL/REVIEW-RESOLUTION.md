# Claude Code review of ESC-003, supplied by the user, 2026-10-28

Resolution: return to the B5/D0 installation folders and rehearse the exact A7
job without a card before offering a new physical package.

- Three guest installation failures occurred before request/grant. No A7 writes
  is INFERRED from absent grants. Empty filtered R5 deltas are not full-log proof.
- Hard-link publication failed with Operation not allowed. Its cause is UNKNOWN.
  Do not use hard links or try to establish their filesystem cause to proceed.
- Use /boot/system/non-packaged/add-ons/kernel. Download each artifact to a
  same-directory temporary name. Check size and SHA-256 against host metadata.
  Move to final name and require equal pre/post inode numbers. Any error or
  changed inode stops the job. Never provide a copying fallback.
- Complete the generic owner before installing the stage client. Publish the
  device symlink last. Identity uses the B5 method. Keep bounded node wait and
  exactly one open. Do not widen register or DMA permissions.
- Rehearse the identical generator/binaries in cardless KVM with no VFIO,
  signing key or grant. Require checked installations, node appearance, and
  the open callback's expected no-card refusal before PCI reservation.
  Cardless failures may be retried without user approval.
- Bind rehearsal evidence to the exact guest job and binaries. Build --check
  must refuse changed inputs. Record evidence under results/*-a7-rehearsal/.
- Close ESC-003 only after passing rehearsal. Prepare a new package for Claude
  review including unreviewed changes in 24fb578 and 0390b8b. A fourth physical
  run still needs the user's explicit yes under ADR 006/008.

The shell open returns failure because prepare executes inside that callback.
Passing rehearsal means entry into that callback followed by the specific
no-card refusal. It cannot yield a prepared descriptor without an actual card.
