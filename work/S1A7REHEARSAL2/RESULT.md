# S1A7REHEARSAL2 result

Rework of 88678c4 after Claude Code's review. Codex implemented it. Codex ran
out of usage before the records were complete; Claude Code verified the
uncommitted work, finished the records and committed them on 2026-10-28.

KNOWN / cardless OS evidence: results/20261028-142613-a7-rehearsal/ passed in
79.31 s (`result.json`: PASS_CARDLESS_NO_CARD).
- Downloads go to /boot/system/non-packaged/.k40-a7-staging/, outside the
  watched add-on folders. Four installs (identity, owner, client, open helper)
  pass size/SHA-256 checks with equal inodes across the move (job-output.txt).
- No `partial` or staging name in serial.log. Drivers load from final names
  only (lines 864, 880).
- Owner loads once, prepare runs once, the PCI search refuses before any
  reservation, the owner is Failed (3) (lines 881-887).
- The one open returns B_ERROR (`A7-OPEN-RESULT status=0xffffffff`), recorded
  by tools/a7/open_session.c from the raw `_kern_open` status.
- Rehearsal-only reload: client reloads (CLIENT_LOAD 2) with Failed state kept
  and no second prepare (lines 888-898).

Code: the client loads the owner in init_driver (module ABI 2,
observe_client_load). The owner constructor touches no hardware. No GPU
register, DMA or permission change. The FIFO and I2C preinit guards of
24fb578/0390b8b are reviewed and accepted.

Binding: work/S1A7REHEARSAL2/rehearsal.json and package.json. build.py,
rehearse.py, host_check.py and run.py --check pass. Full make check passes
(work/S1A7REHEARSAL2/check-final.log). make check reads the ROM from the
~/mediaflux network mount by default; it dropped once on 2026-10-28. Set
K40_VBIOS to the checked copy in ~/haiku-cross/vbios/ when the mount is absent.

ESC-003 is RESOLVED. No physical run occurred. The package
(build/a7/package-rehearsal2/) is unconsumed. A fourth card run needs the
user's explicit yes for one run. S1 remains incomplete. D1 is unapproved.
