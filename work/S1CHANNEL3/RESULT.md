# S1CHANNEL3 result (second fix)

Fix after the S1CHANNEL2 run (results/20261031-batch1-a7-bar1-c261b19b/:
every channel step and the teardown ran, GP_GET stayed 0, no fault).
1. New Policy step 6, before PBDMA discovery: `0x200 = 0xffffffff`, every
   unit enabled, as Linux after POST (mc/nv04.c:120; trace line 47330, read
   back 0xfc37b1ef). The driver had kept the script's 0xe011212d.
2. The GP_GET wait is now bounded by its 2 s time limit; the poll-count cap
   (100000, reached after 145 ms) is raised to 20000000.
Host test: the simulated FIFO advances GP_GET only after the unit enable; a
build without that write fails the test. Steps are now 24 (0-23).

Package build/memstage/package-s1c/ (manifest work/S1CHANNEL3/package.json,
SHA-256 1c7d71d55a314a90a9907fb6910771a729dc76ca9b620b121f55f8b26b17f0a4);
memory_owner 4454fd0f...; A7 owner b4f73dcf... (frozen sources, new key).
Cardless rehearsal results/20261031-batch1-rehearsal-8aa09b93/ PASS; all
package checks and make check pass. No card run yet. This is the third
package for the S1 channel; a third failure triggers the AGENTS escalation.
