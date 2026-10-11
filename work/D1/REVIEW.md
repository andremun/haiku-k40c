# Review of D1, attempt 1 (2026-10-11): ACCEPT after scaffold corrections

One session of 49 minutes on one K40c (`qwen3.6-k40a-t1k`), 61 steps,
no rework. The acceptance test (57 checks) and the agent's own tests
(now 49 checks) pass, with `-Wall -Wextra -Werror`.

The scaffold corrected three small defects:

1. **Out-of-bounds write.** `MockMMIO(0x101)` made 64 registers but
   accepted offset `0x100`, the 65th. The agent's own test did exactly
   that and passed by luck (undefined behaviour). The size is now rounded
   down to whole registers and the test expects `std::out_of_range`.
2. `parseTrace` rejected lines with only spaces and comments that do not
   start in column 1; the task text says empty lines are skipped and `#`
   starts a comment.
3. `peek` was not `const`.

Note for later tasks: an agent test that passes is not evidence. The test
of point 1 described the bug in its comment and asserted it.
