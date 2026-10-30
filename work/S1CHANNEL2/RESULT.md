# S1CHANNEL2 result (fixed package)

Fix after run 1 (results/20261031-batch1-a7-bar1-3f33bd37/): the native
memory owner now maps the whole 16 MiB BAR0 (memnative::bar0View; mmiotrace
MAP 0xc1000000 size 0x1000000), so the channel registers at 0x800000 are
reachable. Policy itself refuses any register beyond bar0View, so a view
smaller than a needed register is caught by the host tests. Evidence and the
signed plan record mapped=16777216. No other change.

New single-use package build/memstage/package-s1b/ (manifest
work/S1CHANNEL2/package.json, SHA-256 4be2edd3a012c11c082738b1c29bb026a2a30bac3057bb339a0c52a9f326ae6e).
memory_owner 0e2473d0...; A7 owner 3d460faa... (frozen sources, new key).
Cardless rehearsal results/20261031-batch1-rehearsal-4d87ce09 PASS_CARDLESS_NO_CARD. All package --check commands
and full make check pass (check-final.log). No card run yet.
