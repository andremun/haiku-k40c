# S2COPY result (host preparation)

Done by Claude Code on 2026-11-12 in the cloud container. No card run. No native
build, package or cardless rehearsal yet: those are T7610 steps (decision 012).

New and changed code: arena roles CopySource and CopyDest; ChannelImage (two
channel pages, second GPFIFO entry, twelve push words); Upload `fill` and
`matches`; Channel `submitCopy` and `verifyCopy` with the S2 predicate; Policy
(second GP_PUT, three status reads, copy-page data rules); NativeOwner copy flag
and report lines; `mem_config.h` carries `memoryCopy`.
Tools: `tools/memstage/stage.py` (`K40_MEM_STAGE=s1|s2`), build, rehearse and run
follow it; `evidence.memory_final` validates an S2 report on its own encoding.

Checks (HOST_ONLY):
- tests/test_mem_copy: pass, stall of the second entry, launch error, one wrong
  word, busy engine, stall of the NOP, MMU fault. Teardown completes in each.
- Four source mutations (launch flags, read-only destination, line length,
  subchannel) make the test fail.
- tests/test_memstage_tools: the S2 report passes; 14 mutations are refused; an
  S2 report is refused as S1 and the reverse.
- The S1 report of tests/test_mem_channel is byte-identical to the one before
  this task. `make check` passes at CI scope (no VBIOS image).

Native compile (cloud container, cross compiler built from the pinned Haiku
b42b90f and buildtools 8375c2d): the 13 owner sources compile for kernel mode with
the package flags (`-O2 -Werror -Wframe-larger-than=4096`) and `memoryCopy=true`.
No link: `kernel.so` comes from the test image and is not in the container.

Open:
- T7610: `K40_MEM_STAGE=s2 python3 tools/memstage/build.py`, rehearsal, `--check`.
- The diagnostic variant of rung 3 (FINDINGS, "UNKNOWN until rung 3").
- Review by a new session under REVIEW.md before rung 3.

A host result is not K40c evidence. S2 is not done.
