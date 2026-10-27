# Native memory adapter — 2026-10-27

The cardless KVM Haiku memory probe passed in 50.75 seconds (result.json).
It checked a 513-byte view aligned to 64 KiB, byte readback, denied IOVA publication,
and successful cleanup. Both devfs loads passed. No panic or failed probe marker occurred.

Source revision: 54db484. Exact command: command.txt. Configuration: launch.json.
The matching raw kernel and linked memory-probe hashes are in hashes.txt.
The guest kernel matches the cross-link installation byte for byte.

This is native OS evidence only. No GPU was passed through. No DMA, device IOVA,
GPU virtual mapping, production quarantine recovery, or compute support is proved.
