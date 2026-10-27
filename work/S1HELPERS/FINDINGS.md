# S1HELPERS findings

- BoardCore owns the freestanding view, transport and helper interfaces. Only the
  legacy PolicyBackend retains a vector snapshot in Board.*.
- GPIO entries use a 255-row bounded array (the table count is an unsigned byte).
  The complete table validates before effects. Duplicate reset/first-match logic,
  defaults, exclusion, routing and skipped IO waits retain their prior behavior.
- BoundPost offers explicit DedicatedPins mode. prepareI2c derives one matching
  dedicated descriptor across the approved I2C rows, then separately initializes
  that pin register with value 7. This source-only preinit is not a ROM write.
  Preparation is once per image, including failure. No implicit init during POST.
- Every dedicated transaction read/write passes through BoundPost's current-PC
  register/width/direction policy. Bit delays are restricted to active I2C, 1/5 us.
  Per-transaction limits and the whole-POST deadline both apply. On a sticky bound
  error, cleanup cannot forward more effects. A NACK can attempt bounded STOP.
- TransactionCallback mode remains the default for existing host simulations.
  Its payload checks remain intact, but its transaction callback is trusted.
  Neither mode grants hardware access. Owner/guest-wide integration remains open.
- Initial native cross-link of all seven core units passed against kernel.so,
  with exceptions/RTTI disabled and frames above 4096 bytes treated as errors.
  Undefined imports were memset, memcmp and compiler-emitted sized delete from
  virtual destructors. No allocator/new import or dynamic helper storage exists.
  The link-only library has no stage/driver entry point and was not loaded.

- Full-path wire fault injection found that the initial adapter flattened a
  DedicatedI2c clock rollback into Io. The adapter now preserves Clock, Timeout
  and Budget, while retaining primary/cleanup details. The regression passes.
- Host evidence: board 577 checks, dedicated wire 908 checks. The new bound wire
  exercise has two profiles (one complete, one expected GPIO denial), ten faults,
  zero observed pin-policy bypasses and zero transaction-callback invocations.
  Existing 32 POST scenarios and 34,128 independent policy queries pass unchanged.
- Hardware register/helper facts are KNOWN from the cited pinned source and
  SOURCE_ONLY. Linux's internal I2C algorithm selection remains UNKNOWN.
  Simulated pin timing and payloads provide no physical compatibility evidence.
- Final make check exits 0: repository checks report zero failures, pinned refs
  are clean, source/generator comparisons pass, and all host suites pass.
  Full output is check-final.log. Shared VM files were not changed, so the sibling
  application's existing tool pin needs no update. No VM or card stage ran.
