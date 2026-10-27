# S1B5 macro-task result — 2026-10-27

B5 identity PASS. Ready for Claude Code macro review.

KNOWN / HARDWARE_VERIFIED: PMC_BOOT_0 = 0x0f1240a1 under Haiku.
Evidence: results/20261027-b5-identity/attempt-02/serial.log and result.json.
The PCI command register was 0x0007. No other GPU register was read.
No bring-up, slow-window operation, DMA, or compute job ran.

- Recorded ADR 005, main-only commits, macro reviews, and read-only passthrough.
- Added card_run.py, stage/source/kernel hashes, VFIO isolation checks, and a watchdog.
- Shared guest lock serializes the card, cardless, and application launchers.
- Identity probe fails for a missing card and carries the B5 read-only stage tag.
- Preserved vm-test.sh and transfer_server.Handler(..., budget=None) compatibility.
- Added 32 identity host checks and 12 launcher tests.
- Applied all four S1C/S1D review fixes and restored the old B5 task records.
- Updated guides, gates, status, and the results index.

The S1A cardless KVM run passed: results/20261027-s1a-cardless/.
It is Haiku OS evidence only, not GPU evidence.
The first B5 attempt stopped on a normal boot banner misclassified as panic.
Its original logs/result are preserved. A regression fixes that false alarm.
The second attempt used the same guest options and driver and passed.
There was no real hang or panic. No modified retry of a real failure occurred.

Validation: both native probes link. make check and make vm-tools-test pass.
The shared VM suite has 26 checks, the launcher suite 12 tests, all passing.
Sibling OpenCode runner tests: 21 pass. Application integration fixtures: 5 pass.
Application make check passes. Shared tools re-pinned to owner 5368556,
committed in haiku-k40c-llm as 9bbd144.
Commands, input hashes, source pins, and logs are in the dated results and work/S1B5/.

No root, host BAR access, binding change, manual GPU reset, or push occurred.
Only 0000:04:00.0 passed through. VFIO startup reset is authorized by ADR 005.
Board-operation helpers, B2, A4, C2, and write stages remain open.
Next macro task: host-only board-operation policy and helpers, after review.
