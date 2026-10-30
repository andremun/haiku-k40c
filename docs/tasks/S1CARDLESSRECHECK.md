# S1CARDLESSRECHECK: repeat the available package cardlessly

The user requests a cardless rehearsal. Batch 2 has design tasks only, so it
has no channel/NOP binaries to rehearse. Run the existing combined A7/memory
installer and binaries in the guarded cardless KVM mode. No card, private key,
grant or physical-stage approval is involved.

Read STATUS, tools/memstage/rehearse.py, its shared launcher cardless path and
HAIKU_BUILD_TEST. Do not read unrelated tasks or reviewer tests/checker sources.
Write PLAN before launch. Refuse a running guest. Keep the shared guest lock,
disposable overlay, independent 600-second watchdog and existing stop rules.
Do not change launcher, job, binaries or package. Redirect only the generated
rehearsal summary into this task's work folder, preserving the original summary.
Record hashes of the old package/summary/consumed marker and batch-2 design binding.

Check all installation, exact no-card errors, final-name loads, one prepare and
resident Failed state through reload using the existing evidence validator.
Record raw capture and FINDINGS/RESULT, update STATUS, run make check and commit
on main. No push. This provides installation/lifetime evidence, never channel,
K40c, DMA, VRAM, S1 or batch-2 runtime evidence. No retry after a launcher stop.
