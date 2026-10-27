# Plan

1. Keep the stopped D0 capture unchanged. Record the user's retry go-ahead.
2. Emit original bounded TGID/KCMP_FILES proof from the pinned tracer at the
   syscall stop. Decode proof separately from mapping semantics.
3. Require the owned process and zero table comparison before accepting a TID.
   Capture/reject file-table split/replacement operations and ambiguous records.
4. Test actual owned threads and independent processes without a guest or VFIO.
   Never normalize raw numeric FDs without a valid syscall-time proof.
5. Rebuild observer, regenerate source/artifact pins, amend the package review,
   run make check and commit. Then attempt the one approved physical retry.
