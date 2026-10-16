# Linux load phase: named evidence

This is a source-anchored survey, not an executable recipe or proof that GR can be omitted.

Load ends before trace line 573390 at time 32.810737.

| Register | First line | Last line | Reads | Writes | Source |
|---|---|---|---|---|---|
| 0x100c10 | 45505 | 114450 | 0 | 2 | reference/nouveau/nvkm/subdev/fb/gf100.c:81-84 |
| 0x001700 | 47374 | 196669 | 0 | 6 | reference/nouveau/nvkm/subdev/instmem/nv50.c:57-92 |
| 0x070000 | 80143 | 571868 | 50 | 50 | reference/nouveau/nvkm/subdev/bar/g84.c:29-40 |
| 0x000204 | 230513 | 560971 | 2 | 3 | reference/nouveau/nvkm/engine/fifo/gf100.c:927 |
| 0x002270 | 561633 | 562369 | 0 | 2 | reference/nouveau/nvkm/engine/fifo/gk104.c:430-447 |
| 0x002274 | 561634 | 562370 | 0 | 2 | reference/nouveau/nvkm/engine/fifo/gk104.c:430-447 |

## Domain totals

| Domain | Reads | Writes | First line | Last line |
|---|---|---|---|---|
| BAR1_memory | 2 | 0 | 561650 | 562386 |
| BAR3_memory | 0 | 365300 | 196681 | 571866 |
| PBFB | 16 | 28 | 46200 | 47373 |
| PBFB_BROADCAST | 6 | 5 | 46175 | 112944 |
| PBUS | 0 | 11 | 47249 | 204929 |
| PCLOCK | 32 | 27 | 45611 | 214044 |
| PDAEMON | 8 | 1684 | 46099 | 206630 |
| PDISPLAY | 47 | 25 | 22 | 563540 |
| PFFB | 44 | 45 | 45505 | 563673 |
| PFIFO | 30 | 10 | 230517 | 562382 |
| PFIFO_CHAN | 4 | 6 | 561553 | 562293 |
| PFIFO_FLUSH | 50 | 50 | 80143 | 571868 |
| PFUSE | 126 | 0 | 206636 | 573381 |
| PGPIO | 4727 | 3462 | 45497 | 573320 |
| PGRAPH | 4 | 4 | 46085 | 46092 |
| PIBUS | 14 | 15 | 45475 | 47312 |
| PMC | 227 | 215 | 11 | 573389 |
| PMFB_BROADCAST | 2 | 4 | 46129 | 114595 |
| PMPLL | 2 | 0 | 214014 | 214015 |
| PNVIO | 13 | 14 | 45581 | 563609 |
| PPCI | 8 | 45 | 23 | 573328 |
| PPCI_2 | 4 | 0 | 47287 | 47294 |
| PPCI_HDA | 1 | 2 | 46485 | 46507 |
| PRAMIN_WINDOW | 0 | 147590 | 47375 | 196673 |
| PRMIO | 2 | 8 | 45471 | 46469 |
| PROM | 45440 | 0 | 25 | 45464 |
| PSTRAPS | 10 | 2 | 14 | 112945 |
| PSUBFIFO | 3 | 15 | 560974 | 560991 |
| PTHERM | 186 | 40 | 45613 | 573384 |
| PTIMER | 496 | 120 | 47250 | 573387 |
| PUNITS | 180 | 270 | 21 | 573383 |
| unknown_bar0 | 386 | 2293 | 45489 | 573382 |

Detailed chronological domain runs and first anchor samples are in load_trace.json. BAR1/BAR3 writes are memory accesses, not independently identified objects. Unknown register names remain unknown.

0x002634 is channel preemption; runlist publication uses 0x002270/0x002274. Capture addresses are examples, never allocation addresses for Haiku.
