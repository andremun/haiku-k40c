# S1CHANNEL result (preparation)

Done by Claude Code on 2026-10-31. No card run yet.

New code: src/memstage/ChannelImage.{h,cpp}, src/memstage/Channel.{h,cpp};
Mapper exposeUserd/closeUserd; Policy channel script (24 steps), reads,
barWrite; NativeIo writable 8 KiB BAR1 view and barWrite32; NativeOwner runs
the channel after the batch-1 experiment; seven arena roles; Upload patch roles.
Host side: evidence.memory_final validates the channel phase independently;
run.py records S1_complete only on pass. Tools moved to work/S1CHANNEL/ and
build/memstage/package-s1/; the consumed batch-1 package is unchanged.

Checks: tests/test_mem_channel (pass, stall, MMU fault, mutations detected),
test_memstage_tools (nine channel mutations refused), cardless rehearsal
results/20261031-batch1-rehearsal-8779e475/ PASS_CARDLESS_NO_CARD, all package
--check commands, full make check (check-final.log). Source-bound reports of
S1MEMARENA/UPLOAD/MMU/FAULTS and S1OWNERPOST regenerated for changed hashes.

Review and hashes: docs/S1-CHANNEL-REVIEW.md. HOST/cardless evidence only.
