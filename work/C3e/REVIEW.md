# Review of C3e (2026-10-12): ACCEPT after scaffold corrections

Two runs of one session, 4 hours in all (one interruption by the
runner). 70 members, 0 check failures. The 40 function descriptions name
the registers and values that the quoted lines show; a sample of twelve
was compared with the source and is right.

Corrections by the scaffold:

1. Invented expansions: FECS as "Front End Command Scheduler", GPCCS as
   "General Purpose Command Command Scheduler", PPC as "pixel pipeline
   combiner". The task text said these are not expanded in the source.
2. `mmio` was described as function pointers packed into the context
   image. It is the list of register-write tables that `gf100_gr_init`
   applies at start-up.
3. The eight `grctx` pack members were called "function pointers"; they
   are tables of register writes.
4. `depends_on` lacked `mc`, `fb`, `pmu` and `timer`.

Limits:

- Every init hook is marked needed for compute, because `gf100_gr_init`
  calls them all. Whether a compute-only driver may leave out `init_zcull`
  and the two ROP hooks (B5 called them graphics-only, without evidence)
  is still open.
- The descriptions of the `grctx` functions say which registers are
  written, not what the values mean.
