# Result

Added source-backed raw fault snapshots, bounded TOP routing discovery and
resident deferred diagnostics. Reset-only and post-A7 scopes are distinct.
No acknowledgement/clear, interrupt enable or scheduler/PBDMA write exists.

Validation: 25 host baseline/routing/fault/clock cases, native object build,
generated catalog --check, A7 source freeze, full make check and diff check.
The report records source semantics and host tests, not physical observations.
Reset-time applicability of the MC status read remains INFERRED.

The upload/MMU/native-package integration remains. No VM/card was launched.
