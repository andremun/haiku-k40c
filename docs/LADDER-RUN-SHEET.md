# Run sheet for the card day, 2026-11-16

Decision 012, item 4. State of 2026-11-12: every Haiku stage below passes its host
tests in the cloud container. None was linked, packaged or rehearsed yet: that
needs the T7610. This sheet is a draft until the rehearsals pass.

## Preparation on the T7610 (user or a T7610 session, before Monday)

1. Merge or check out the branch `ccr-5d33feda-7ni61l` of `haiku-k40c`.
2. `make refs`, then `make check` without `.check-skip` (full scope, with the VBIOS).
3. For each stage NAME in `s1`, `s2`, `s3a`, `s3b`:

   ```sh
   K40_MEM_STAGE=NAME python3 tools/memstage/build.py            # package
   K40_MEM_STAGE=NAME python3 tools/memstage/rehearse.py --run   # cardless guest, about 80 s
   K40_MEM_STAGE=NAME python3 tools/memstage/build.py --check    # sources, artifacts, rehearsal
   ```

   The build runs `tools/gr/program.py`, which checks the GR program against the
   reference trace again. A failure of any command is a stop: send the output.
4. Card: `~/llm-server/llm-mode.sh one`, `sudo scripts/passthrough.sh attach`,
   then the journal stream of `docs/REQUESTS.md` R5.
5. `K40_MEM_STAGE=NAME python3 tools/memstage/run.py --host-check` for each stage.

Expected first problems (not seen yet, because nothing was linked here): link
errors from the new `src/gr` sources, the size of the owner module (about 100 KB
more data), and cardless expectations of the rehearsal. They are fixed on the
branch before Monday, not on the card day.

## Rungs

Each Haiku run: `K40_MEM_STAGE=NAME python3 tools/memstage/run.py --run-approved-batch1-once`.
State the package SHA-256 (`work/<task>/package.json`) before the launch. One guest
at a time. A new guest for every run: the stages do not reset the GR engine.

| Rung | Stage | Writes beyond the earlier rung | Pass | Stop conditions |
|---|---|---|---|---|
| 1 | Linux guest, `tools/guest/linux-run.sh --gpu` | Nouveau and Mesa, as in the reference run | Reference job results | Guest or host fault line |
| 2 | `s1` | None new (S1 of 2026-10-31) | `PASS S1_CHANNEL_NOP`, validator accepts | Launcher stop, R5 line, validator refusal |
| 3 | `s2` | One more GPFIFO entry: copy class bind, 8 methods, launch | `PASS S2_COPY`: destination equals source | As rung 2; copy-engine launch error |
| 4 | `s3a` | Power gating off, GR engine start, two microcode loads, golden context, context attach: the 6,253 ops of the program | `PASS S3_GOLDEN` | As rung 2; any expect, poll or idle failure of the program |
| 5 | `s3b` | Rung 4 and one GPFIFO entry of 106 words: compute set-up and one launch | `PASS S3_COMPUTE`: 1024 of 1024 elements | As rung 4; GR interrupt or trap, FECS interrupt, wrong element |
| 6 | Timed matrix product | Not prepared yet | Result equal to the CPU, time recorded | - |

After a stop: decision 012 allows one run of the prebuilt diagnostic variant of
that rung. No diagnostic variant exists yet (2026-11-12). Until one exists, a stop
ends the rung: report and ask.

## What each pass would establish

- Rung 3: S2. The copy engine needs no set-up beyond the S1 channel (INFERRED today).
- Rung 4: the GR bring-up of Nouveau works from a Haiku driver on this card, and
  FECS saves a context through our page tables.
- Rung 5: S3, the goal of the design documents.

## Known weak points, in order of risk

1. Rung 5 push buffer: SOURCE_ONLY (Mesa), no trace. Rung 1 does not check it yet.
2. Rung 3 predicate needs the copy engine "not busy" (FINDINGS of S2COPY).
3. Rung 4 and 5 reuse the generation memory as the channel context (S3LAUNCH PLAN).
4. All four packages are unlinked and unrehearsed today.
