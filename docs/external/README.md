# External reviews and research

Documents written outside this project (an independent automated
review and research, supplied by the user on 2026-10-13). They are kept
as received. They are not verified by `make check`, and their links
point to sources outside the repository.

| File | What it is |
|---|---|
| `2026-10-13-review-outcome-package-b.md` | Review of the first review package: seven defects in the host code (F1 to F7), gaps in the path to S1, safety questions |
| `2026-10-13-review-outcome-package-c.md` | Review of the updated package with `docs/S1-PLAN.md`: why a flat replay of the start-up script is not sound (C1 to C4), stronger stage conditions |
| `2026-10-13-haiku-code-research.md` | Existing Haiku code and interfaces that the driver can build on |
| `2026-10-13-k40c-initialisation-research.md` | Public documentation of the start-up script language and tables, and a route through the memory bootstrap |
| `2026-10-13-gk110b-gr-research.md` | A FIFO-only command for S1 (the host NOP), and where Nouveau has the firmware loading and context generation for S3 |
| `2026-10-13-s1-unknowns-research.md` | Source research on the eleven unknowns of the S1 plan: page size and flushes, the slow memory window, address domains in a guest, reset scope, the kernel version difference |

The scaffold's response to them is in `docs/S1-PLAN.md` when that file
is revised.
