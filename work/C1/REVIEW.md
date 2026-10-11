# Review of C1, attempt 1 (2026-10-11): ACCEPT

One session of 40 minutes on one K40c (preset `qwen3.6-k40b-t1k`), 54
steps. The check compares every field of the 462 entries with values that
it computes itself, and it passes. `tools/build_regdb.py --check` is
stable. The README has the table and the "Not named" lists.

Notes for the tasks that use the database:

- The task is mechanical by design: the rules and `tools/rnndb.py` came
  from the scaffold. The result says which registers Nouveau touches and
  what envytools calls them, not what they do.
- 209 of 462 entries have no envytools name for this chip, and 52 have
  no fixed address. The unnamed ones include most of the GK104 FIFO and
  the memory-training registers.
- The groups follow B3, which includes generic files (`nv04`, `nv50`
  functions appear in the lists). C3 has to drop the registers that the
  GK110B path never reaches.
