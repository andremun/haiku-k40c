# B5 identity stage — 2026-10-27

## First attempt: host-parser false alarm

The launcher ended the guest before probe load. Its result.json says panic,
but the classifier matched a normal boot banner, not a panic message.
The original tool output remains unchanged.

Evidence: serial.log:235 says "Welcome to kernel debugger output!".
The same banner occurs in the passing cardless run at
../20261027-s1a-cardless/serial.log:237.
No PANIC message or B5 probe marker appears in the first-attempt serial log.
The log ended during kernel initialization. No HTTP guest job ran.
This attempt gives no PMC_BOOT_0 result (UNKNOWN).

The parser fix excludes the normal banner and retains actual PANIC detection.
A host regression test covers both cases. The guest and driver configuration
stay unchanged. The next attempt remains an authorized read-only B5 stage.
The no-retry rule for a real hang or panic remains in force.

## Second attempt: identity pass

KNOWN / HARDWARE_VERIFIED: the Haiku identity probe read PMC_BOOT_0 as
0x0f1240a1 on the development K40c. The PCI command register was 0x0007.
Source: attempt-02/serial.log, between K40-B5-BEGIN and K40-B5-END.
The driver read no other GPU register. It did not perform bring-up or DMA.
No PANIC message occurred. The guest exited under launcher cleanup.

The tool's attempt-02/result.json records pass in 128.49 seconds.
attempt-02/launch.json records the exact command, source commit, driver SHA-256,
source hashes, matching guest kernel hash, and the VFIO isolation preflight.
attempt-02/command.txt is the reproduction command.
The kernel SHA-256 matched the cross-link kernel before driver download.

This is identity-only evidence. It proves no memory adapter, IOVA correctness,
clock or board initialization, scheduler state, or compute support.
A7 and first-write C3 stages still need the user's go-ahead.
