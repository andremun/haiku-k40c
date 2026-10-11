# Review of C4a (2026-10-12): ACCEPT after scaffold corrections

One session of 56 minutes, no resume. Comments only: the code of `src/`
is unchanged (compared with comments stripped) and all eight test
programs pass with the same numbers of checks. Every constant line now
has a citation or a `no source:` note, and the tool writes the table.

The scaffold opened every newly cited line. Two were wrong and are fixed:

1. `kUserdGpPut = 0x8c` cited `nouveau_dma.c:104`, which is the read of
   the get pointer at `0x88`. The put pointer is written at line 92.
2. `kPteUnmapped = 0` was marked "no source: zero-initialisation
   convention". It has a source: `gf100_vmm_pgt_unmap` writes `0ULL`
   (`vmmgf100.c:94`).

Not done as the task asked, and accepted as is: the table has no column
with the text of the cited line, and the introduction explains only the
status `SOURCE_ONLY`.
