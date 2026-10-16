# ABC1 running findings

- A3 rework now passes full make check and both --check runs. Exact observed
  counts: 598/560/38, 24 names; prescribed presentation inventory 2041 rows,
  1519 distinct listing offsets absent from instruction log. Seven COPY_NV_REG
  starts are split-line display, zero is repeat bookkeeping. This is not a
  complete reachable-opcode proof. No rejected branch/reviewer code read.
- Cross-toolchain rebuild running under session 47057, two jobs, ignored
  build/haiku-cross; source checkout session 95876 was started first.
- B2 freestanding memory ownership/publication boundary implemented, 39 host
  checks pass. Distinct guest-physical/IOVA/VRAM/GPU-VA types, no device addresses
  derived from CPU pointers. GPU mapping and physical backend not yet done.
- Next: executor source/design + bounded safe host subset; load-trace/recipe;
  finish native cross build and cardless backend/tooling.
- A3 commits complete through 41b5f58; B2 interface/host tests committed bbad61d.
- Important new A4 finding: Nouveau init_io(0x69) has chip-specific MMIO
  side effects for port 0x3c3, not just legacy VGA. The board document's
  recommendation that VGA operations can simply be omitted is unproven.
- A4/A6: source cross-reference generated for all 24 observed opcodes; 19 host
  core semantics plus five default-denied board/helper operations. 32 checks
  pass; hard host-simulation gate; not full reachable-program/hardware executor.
- C1: load trace survey generated (six anchors, 1456 domain runs). Initial pass
  was too slow naming PRAMIN data words; optimized the known data-window domain.
  C2 recipe now records unknowns instead of guessing a complete hardware sequence.
- C3: slow-window/flush/runlist simulation primitives pass 46 checks. Critical
  plan fix: 0x2634 is preemption, commit is 0x2270/0x2274. No hardware use.
- Cross compiler built successfully (source b42b90f/buildtools 8375c2d). Native
  backend/probe compile with Werror, both test and identity configurations.
- B4 runner session 49046 started a disposable cardless overlay to retrieve
  matching kernel. Guest shows splash/package initialization; desktop/job not
  reached yet. Host watchdog is 600s. No KVM device exists here.
- Raw ROM preflight now covers all main/extra POST roots conservatively: 530
  potential instruction starts, 25 opcode values, no structural issues and no
  observed nonzero offsets missing. Extra potential opcode 0x91 added to core.
  128 real-ROM/artificial-backend scenarios pass (all 8 RAM selections and two
  fallback register profiles over 8 roots). Board callbacks are dummy in these
  scenarios; zero hardware evidence. Synthetic interpreter tests now 33.
- Bootstrap tests now 78, including write-all/read-all scratch alias detection.
  HaikuBackend.c host fault-injection shim tests 35 pass, explicitly not native
  ABI evidence. Full make check abc-final-code.log passed before doc handoff.
- Cross build done; build_backend.sh --objects-only passes, both C probes and
  four freestanding C++ components compiled against actual native headers.
- Native VM attempts 1 (2 GiB/2 CPU) and 2 (4 GiB/2 CPU) timed out after 600s.
  No matching kernel retrieved. All overlays/logs retained, guests cleaned up.
  KVM absent outside sandbox too. Final single-CPU attempt session 2013 running
  with 600s watchdog; log build/cardless-kernel-run3.log. No more boot variants
  after this if it fails. The queued wait worker 47904 safely refused overlap.
- Version comparison: public v6.8 tag resolution session 54265 pending. If that
  stalls, do not spend task on unbounded network retries; mismatch remains open.
- Native host failure-injection tests expanded to 58: failed area/module
  releases retain ownership and cannot report clean teardown; native probe
  propagates cleanup failures. All native objects recompile after correction.
- GitHub v6.8 requests returned HTTP 429; 21-file version supplement is explicitly
  incomplete (no "different file" conclusions). Standalone --check exits 2 until
  source cache is populated. Stalled git tag query was stopped, no further retry.
- Final single-CPU TCG native attempt session 2013 remains under its 600s watchdog.
- Final single-vCPU native attempt failed at its 600s watchdog too. All three
  guests stopped/cleaned up. ESC-001 written; no more VM variants attempted.
  Native matching-kernel link/load remains blocked; objects compile correctly.
- Added timestamp join: 598 devinit intervals, zero skipped intervals with BAR
  accesses; no causal/helper-completeness claim. Corrected TIME units in board
  document: executed 1 us..1 ms, skipped 10 ms, not old 1 ms..1 s wording.
- Preparing final full check/commit and opaque local source review ZIP/bundle.
