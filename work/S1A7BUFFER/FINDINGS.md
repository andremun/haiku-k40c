# Findings

User authorizes implementation and cardless validation, then an approval request.
No physical launch. Existing consumed package-i2c and prior captures are retained.
Drain must occur after the full controller returns: draining inside executeRom
would remove cost from the 10 s POST guard but still consume its 15 s parent.
Buffer POST_RESULT and subsequent readiness events too, preserving logical order,
then revoke the permit and drain before PASS/FAIL startup reporting.

First native plain benchmark passed. Observed case stopped before QEMU launch:
observed_child requires an absolute executable; cardless runner supplied a bare
command. Stop reported and ADR 006 permission requested before another guest.
Fix resolves only the executable path; QEMU options stay fixed and cardless.
The trace drain now emits all script/timing details before POST_RESULT, retaining
POST_RESULT-before-readback ordering even though output occurs after controller.
This header correction requires fresh native measurements; old evidence retained.

Host owner/authentication tests pass, including injected buffer overflow. All 32
RAM/profile cases retain the prior reviewed write counts. Native no-extra-MMIO
poll observations and deferred trace-result ordering pass focused tests.

Preliminary plain evidence stores its actual probe and kernel. The header changed
after that measurement to ensure metrics drain before POST_RESULT. Do not bind
this preliminary capture to the final candidate. Fresh plain/observed runs are
required once continuation permission is received. New role rejection tests ensure
the observed cardless path rejects missing/wrong probes before any subprocess.

The native logger benchmark runs in init_driver kernel-thread context, not the
signed A7 write callback; it measures the common dprintf/buffer mechanism only.
Source-bound host reports (board trace, policy, owner lifetime, input closure)
were regenerated after instrumentation. Physical evidence was not regenerated.
Shared cardless_run.py changed: after the owner commit, the consumer's permitted
reference/HAIKU-TOOLS.json re-pin remains a follow-up before consumer checks.
