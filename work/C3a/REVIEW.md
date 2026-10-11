# Review of C3a (2026-10-11): ACCEPT after scaffold corrections

Two sessions. The first (3.5 hours) wrote the tool and the structure and
then lost its descriptions three times at context compaction, because it
wrote them into files that the tool regenerates. The second (1 h 55 min),
with decisions in separate files and reading rules, finished all six
subsystems with 0 check failures.

The descriptions are much better than in B5 and C2: nearly all restate
the quoted source line and are right. The scaffold read all 46 against
their quotes and corrected these:

1. `mc`: register `0x000200` was described as interrupt enable. It holds
   the enable bits of the engines and subdevices (the quoted line has the
   comment "everything enabled"). Fixed in `init`, `device.enable`,
   `device.disable`, `device.enabled` and the summary.
2. `mc.unk260` was marked not needed for compute. The GR microcode
   upload calls it (C2), so it is needed.
3. `bar`: the texts said "BAR0". The code's `bar->bar[0]` is BAR2 and
   `bar->bar[1]` is BAR1. `depends_on` was empty; the code uses instance
   memory and address spaces (`imem`, `mmu`).
4. Four `value` or `table` members were `KNOWN` with no source text
   behind them (`mc.intrs`, `mc.intr_nonstall`, `mc.reset`,
   `mmu.kind_sys`): now `INFERRED`.

Limit: 45 of 46 members are marked `KNOWN`. For functions this means
"the text restates a quoted line", not "the purpose is understood".
