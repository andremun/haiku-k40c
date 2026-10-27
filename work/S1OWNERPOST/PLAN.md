# S1OWNERPOST plan and API contract

1. NativeOwner reserves aligned PostImage storage in its resident object. bindPost
   validates the exclusive lease and fresh state, copies one exact-size image, and
   never permits replacement. Wrong identity consumes that binding attempt.
   Null/wrong-size inputs have no binding effects. No raw image view is returned.
2. inspectPost returns only copied status, selection and execution results under
   the same lease/atomic guard. Image/parser pointers and callbacks never escape.
3. simulatePost is declared only outside _KERNEL_MODE and implemented in a
   host-only unit that rejects kernel compilation. The v1 C ABI remains unchanged.
   It holds the owner guard across the synchronous call and consumes OncePerBoot
   before selection, explicit dedicated I2C preparation or POST effects.
4. BoundPost exists only for that synchronous call. The owner retains the image,
   cached selection, result and latch, never a callback/provider reference. Every
   attempted simulation finishes the latch and quarantines owned memory. Complete
   means host simulation completed, never independent GPU readiness.
5. Test source mutation, stale leases, rejected/replacement ROM, new clients,
   preinit/strap/payload failures, concurrent/reentrant calls and latch conflicts.
   Compile/link resident native units without exposing simulation in their symbols.
6. Regenerate aggregate source-bound evidence, run make check, update handoff and
   commit on main. No VM, physical hardware, root, PCI/BAR, reset, binding or push.
