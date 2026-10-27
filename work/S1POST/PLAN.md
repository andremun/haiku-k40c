# S1POST plan

1. Separate freestanding board permission identity from the hosted helper adapter.
2. Add an owned, noncopyable exact-ROM snapshot and bounded POST layout parser.
   Derive roots and tables internally; cache one backend strap read, never caller indices.
3. Derive per-instruction read/write/width permissions, including table operands
   and exact approved helper effects. Reject contextual encodings and alternate GPIO.
4. Add a host-only bound POST adapter using the immutable inputs, guarded register,
   byte and I2C operations, aggregate budgets, and no arbitrary start/table arguments.
5. Test malformed layouts, mutation, RAM selection, permissions and alternate paths.
   Cross-compile the freestanding binding/policy. No VM or hardware backend.
6. Generate independent ROM/policy comparison evidence, update documentation,
   licensing/provenance/status, run make check and commit the handoff.
