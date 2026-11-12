# 012. Resume the driver project for S2 and S3

Date: 2026-11-12. Status: accepted (user instructions of 2026-11-12, quoted below).
This record ends the hold of decision 011.

## Context

S1 passed on 2026-10-31. The user has agent time until about 2026-11-17 and one
card day: Monday 2026-11-16. User instruction: "let's push to get it done. Monday
will be the only day for testing, so all non card depending tasks should be
completed." The plan was presented on 2026-11-12. User answer: "Work here, branch
confirmed, b12020, approve ladder and rung 1".

## Decisions

1. **Scope.** S2 (copy), S3 (compute) and a first runtime interface for
   `haiku-k40c-llm` (Q2 to Q5). All work that needs no card is done before Monday.
2. **Place of work.** A Claude Code cloud container, not the T7610. The container
   has no card, no KVM, no VFIO and no private VBIOS image. Its only account is
   root: the "never run as root" rule of `AGENTS.md` protects the T7610 and its
   cards, and it stays in force there. `make check` runs in the container with the
   CI settings (`.check-skip` A3, `K40_CI_NO_VBIOS=1`). The VBIOS checks, the
   cardless rehearsals and every package build for a card run are T7610 steps.
3. **Git.** Work is committed and pushed to the branch `ccr-5d33feda-7ni61l` of
   each repository. The user merges to `main`. This replaces "use only main, never
   push" for these sessions.
4. **Run ladder for 2026-11-16.** The user approved the ladder below as a
   programme. Each rung is one prebuilt package that passed its cardless rehearsal
   on the T7610. Before each launch the agent or the user states the package hash.
   After a launcher-reported stop of a rung, one run of the prebuilt diagnostic
   variant of the same rung is permitted. A second stop of a rung ends that rung:
   report and ask (decision 006). No package is changed on the card day except to
   select a prebuilt variant. Decision 008 stays in force for every run that is
   not on the ladder.

   | Rung | Guest | Content | Pass |
   |---|---|---|---|
   | 1 | Linux, Nouveau and Mesa | Reference runs: copy, `add_f32`, `mul_mat_vec_q8_0`, one FP32 matrix product; captures | Results equal the CPU; traces saved |
   | 2 | Haiku | S1 again on the re-attached card | As on 2026-10-31 |
   | 3 | Haiku | S2: copy between two VRAM buffers | Destination equals source, no fault, clean teardown |
   | 4 | Haiku | S3a: GR engine, FECS and GPCCS, golden context | Context made, no fault, clean teardown |
   | 5 | Haiku | S3b: `output[i] = input[i] + 1` | Every element checked |
   | 6 | Haiku | One timed FP32 matrix product | Equal to the CPU within the stated bound; time recorded |

5. **Rung 1** (`tools/guest/linux-run.sh --gpu`) is approved for the card day.
6. **llama.cpp base.** `haiku-k40c-llm` moves to base b12020
   (`llm-server` note `docs/history/20261102-haiku-llm-b12020-note.md`, option B).

## User steps before the card day

1. `~/llm-server/llm-mode.sh one`.
2. `sudo scripts/passthrough.sh attach` (`docs/PASSTHROUGH.md`), after the branch
   changes to `scripts/` are merged to `origin/main` if there are any.
3. Start the filtered journal stream (`docs/REQUESTS.md` R5).
4. Merge the work branch, then on the T7610: `make refs`, `make check` without
   `.check-skip`, and the cardless rehearsal of each rung.

## Limits

Unchanged: only 0000:04:00.0, only through the guarded launchers, one guest at a
time, ten-minute deadline, evidence labels, no invented constants. Q7 stays open:
S2 and S3 keep every buffer in VRAM and read results through owned BAR1 or
slow-window paths. A cardless or host result is never K40c evidence.
