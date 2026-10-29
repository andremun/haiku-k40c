# Findings

Run5 is immutable and consumed. It reached POST and stopped at 0xab8d with
Error::Io. The native log does not identify which sensor register or I2cError.
The hardware cause therefore remains UNKNOWN. No new physical run is approved.

Pinned Nouveau bios/init.c:1033-1056 invokes init_wri2cr for each pair without
checking its return. The original project treated all I2C failures as fatal.
Linux bus.c:230-245 can select the generic Linux bit algorithm instead of the
CONFIG_NOUVEAU_I2C_INTERNAL implementation. Do not claim identical waveforms.
The first Linux sensor address frame has a high SDA ACK sample. A complete
independent decode and response replay will establish the scope of this fact.

KNOWN / TRACE_VERIFIED: both sensor pairs contain four START/address/ACK/STOP
frames. Each sends only 0x98 and samples SDA high in ACK phase. No register/value
payload is sent. The source handler ignores the failure and proceeds to the
second pair and later script instructions. Eight captured slave responses replay
as I2cError::Nack at Address, bit 8, with a successful STOP in DedicatedI2c.
An independent ACK-all control transfers all three bytes successfully.
This is response replay, not callback-by-callback or timing equivalence.

The user explicitly selected the bounded address-NACK policy. ADR 010 records
that decision. It changes the two exact pairs only, four attempts each, with
clean STOP required and all other errors fatal. No 100 ms settle wait or pad
write is added. Source pad.c:27-33 prints its mode line even without a mode
callback; padgf119.c's dedicated x function has no mode callback. Such a log
line alone is not evidence of a missing mode-switch write.

The first Linux transfer is 6.272 ms within its acquire/release window, followed
by a second transfer of 8.885 ms. The 99.799 ms gap before the first acquire is
observed elapsed time, with no source-backed required settle identified.
The earlier combined 16 ms description was not one transfer duration.

The exact new package passes cardless rehearsal in 78.34 s, with identity/client/
owner load counts 3/2/1, raw B_ERROR and one prepare. Reload retains Failed state.
This does not exercise I2C on a card. Host owner cases separately prove narrow
continuation and fatal primary/cleanup classifications. A final source-bound
rebuild after test/timing-record updates still matches those exact guest binaries.
No physical launch or llm-server branch/file change occurred in this task.

Full make check passes in check-final.log. Earlier failures identified one
uncited software pair-to-bit comparison. An annotation was first added to the
neighbouring scope guard, then to the actual pair-bit line after --missing
identified it. No reviewer checks or executable logic changed in that repair.
All generated source bindings were refreshed. The native owner hash remained
unchanged and the exact rehearsal still validates. The package's non-launching
check and all earlier immutable capture recorders pass. No guest remains.
The ~/mediaflux mount is available in this session. The explicit local ROM
selection remains documented so a later mount outage is not mistaken for a
source or hardware result.
