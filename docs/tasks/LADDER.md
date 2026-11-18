# LADDER: packages, rehearsals and the run sheet for 2026-11-16

## Why and inputs

Decision 012, item 4. Tools: tools/memstage/{build,rehearse,run}.py, tools/guest/linux-run.sh.

## Outputs

- One package per Haiku rung (2 to 6), each with one prebuilt diagnostic variant.
- The Linux guest jobs of rung 1 and their capture commands.
- docs/LADDER-RUN-SHEET.md: for each rung the command, hashes, writes, stop conditions,
  pass predicate and the action after a stop.
- T7610 step list for the user: build, rehearse, verify hashes.

## Checks and limits

Every package passes its cardless rehearsal on the T7610 before the card day.
No package changes on the card day.
