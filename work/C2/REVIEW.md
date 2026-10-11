# Review of C2, attempt 1 (2026-10-11): ACCEPT after scaffold corrections

One session of 1 h 50 min on one K40c (`qwen3.6-k40b-t1k`), 81 steps.
The manifest values (sizes, hashes, lines, load sequence) are checked
against the source and are right. The README had wrong statements, which
the scaffold corrected (small, exactly stated; no new session):

1. It said the built-in arrays are NVIDIA firmware written by NVIDIA
   engineers. They are Nouveau's own code (Red Hat, MIT), written to
   replace NVIDIA's microcode. This matters for licensing: the Haiku
   driver may ship them.
2. It called `gf100_gr_load` (external files) the default path. The
   default is `gf100_gr_nofw` (built-in arrays), because `NvGrUseFW` is
   false unless set. The same section said both things.
3. It guessed that `nvkm_mc_unk260` selects a Falcon. It writes 0 and
   then 1 to register `0x000260` around the uploads
   (`nvkm/subdev/mc/gf100.c:64`); the purpose is not known. The two
   `what` texts in `tools/fw_manifest.py` and the README steps now say this.
4. The `what` of line 1869 said two milliseconds; it is 2000 ms.
5. It said Nouveau marks the external files do-not-distribute. That mark
   is this project's.

Pattern, as in B5: values that the check computes are right; sentences
that the check cannot verify are partly guessed from names.
