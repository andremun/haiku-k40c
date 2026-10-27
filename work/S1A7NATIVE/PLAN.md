# Native A7 preparation plan

1. Resolve preinit/POST ordering and the existing flush-page requirement from the
   pinned Nouveau chain. D0 supplies no payload/coherency or provider permission.
2. Audit the permanent-owner and native register boundaries before adding any
   physical execution entry point. Keep D0 and its artifacts unchanged.
3. If prerequisites permit integration, add a closed A7-only native path with
   immutable ROM/policy, permanent context and one-shot/quarantine semantics.
   Test the actual binding and cross-link. Never masquerade as host simulation.
4. Produce the complete write inventory and independent readiness/ownership
   checks. End with an exact reviewed package and unresolved gates stated.
5. Do not run a write stage. Present a ready package for one explicit yes.
   Follow escalation rules if source contradicts the requested order.
6. Run make check, write findings/result and commit this task separately.
