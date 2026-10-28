# S1A7RUN5 preparation result

Done by Claude Code on 2026-10-29 (Codex out of usage).

- tools/a7/run.py: StrictLog allows one exact device-enable line for
  0000:04:00.0 between QEMU start and the first guest serial output (ADR 009).
  The allowed line is recorded in result.json (allowed_kernel_lines).
- tests/test_a7_run.py: new test for the allowed line and six rejected cases
  (window closed, second line, allowance used, other card, other message,
  another filtered line). The old code fails it. The fake kernel log gained
  close_start_window. All nine tests pass.
- Tool paths now point to work/S1A7RUN5/ and build/a7/package-run5/. The
  consumed package-rehearsal2 and the S1A7REHEARSAL2 records are unchanged.
  runtime.json is copied unchanged (runtime_export.py --check passes).
- New package: owner e031b8a3... (new key and nonce); client d11b0d37...,
  helper 58bec7c5..., identity 8c45ec7b..., observer 75b7aeed... unchanged.
- Cardless rehearsal PASS in 79.64 s: results/20261029-100317-a7-rehearsal/.
  Same results as S1A7REHEARSAL2: final-name loads, one prepare, open B_ERROR,
  owner state kept on reload, no partial names.
- build.py, rehearse.py, host_check.py, runtime_export.py and run.py --check
  pass. make check passes (check-final.log).

No card run. Package build/a7/package-run5/ is unconsumed. A card run needs the
user's explicit yes for one run. S1 remains incomplete. D1 is unapproved.
