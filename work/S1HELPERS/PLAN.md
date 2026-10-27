# S1HELPERS plan

1. Extract freestanding board interfaces/helpers; retain the hosted legacy adapter.
   Replace GPIO vector storage with a bounded table and preserve duplicate semantics.
2. Add explicit host dedicated-pin wiring to BoundPost. Keep bus initialization
   separate from script permissions; guard each transaction pin access and delay.
3. Add regression/fault coverage, cross-link the complete bound core without
   allocation, and regenerate independent policy/trace/source reports.
4. Run make check; record limits, update status and handoff, and commit on main.

No VM, physical card, root, PCI/BAR access, binding, reset or push.
