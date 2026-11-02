# CI check repair

1. Make `host_check.py --check` build the host probe it needs before comparing
   the deterministic report.
2. Fetch the exact pinned Ed25519 source in Actions and pass its location to
   the checker.
3. Run targeted validation and `make check` where the local source inputs allow
   it; review the final diff and run required security checks.

Outputs: the checker, `.github/workflows/check.yml`, and this plan.
