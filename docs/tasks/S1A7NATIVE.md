# S1A7NATIVE: native POST integration and A7 review package

Read docs/STATUS.md, the accepted review in work/S1D0RUN/CLAUDE-REVIEW.md,
docs/HAIKU_BUILD_TEST.md, docs/NATIVE-OWNER.md, docs/POST-BINDING.md,
docs/BOARD-OPERATIONS.md and the relevant S1-PLAN A4/A6/A7 sections.
Use only the resident owner, bound POST/board helpers and native backend files
needed for this integration. Do not read unrelated task files.

The user requests continued S1 work. Claude places native POST next after D0.
This task performs host implementation and native link checks only. It never
runs a write-stage guest. ADR 008 supplies no A7 permission.

Write the plan first. Determine the exact native preinit/POST order and resolve
its existing pre-POST flush-page, memory/publication and ownership prerequisites
against the pinned call chain. D0 is structural mapping evidence, not payload or
coherency proof. Do not silently promote it into a verified provider or bypass a
remaining gate. If source evidence contradicts the requested order, document the
specific chain and follow the repository escalation rule.

Connect the bound POST and board helpers to a real register backend behind a
closed A7 stage gate. Keep D0 and its binaries read-only. Keep native context,
transport and callbacks in the permanent owner. Its one-shot latch must cover
preinit and POST across client reload. Deny arbitrary addresses, bytecode,
callbacks or user-supplied permission claims. Preserve failed-state quarantine.
Use the exact ROM and ADR 004 policy, immutable inputs, bounds and deadlines.

Host tests must exercise the actual native binding boundary, one-shot reload,
failures and teardown retention. Cross-link against the matching guest kernel.
Do not merely enable hostSimulation on a physical backend. Record all consulted
Nouveau source in licensing.md and every new constant's pinned source.

End with a concrete reviewed A7 stage package: exact command and driver hashes,
complete possible register-write inventory from devinit_preflight on this ROM,
identity and PCI command before POST, independent timer/memory-size/scratch
readiness checks, ownership and visibility requirements, limits and stop rules.
State unresolved prerequisites clearly. Do not request approval for an incomplete
or misleading package. Present the ready package for an explicit per-run yes.

Write FINDINGS.md and RESULT.md (max 40 lines), update status and the review doc,
run make check, and commit this task separately on main. Never push. Do not build
D1 or more mapping/visibility machinery before A7. S2/S3 remain conditional on S1.
