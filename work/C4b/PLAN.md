# Plan: Task C4b — Design documents (MMU, FIFO, GR, firmware)

## Order
Write four documents in order: firmware → MMU → FIFO → GR. Each in 2–3 steps.

## Steps per document
1. Sections 1–2: Goal + What Nouveau does
2. Sections 3–4: Haiku driver design + Haiku interfaces
3. Sections 5–6: Host tests + Not known

## Validation
After each document: `make check 2>&1 | grep NAME`, fix, commit.

## Sources
- Firmware: `firmware/README.md`, `firmware/manifest.yaml`, `docs/hardware-model/gr.md`
- MMU: `docs/hardware-model/mmu.md`, `bar.md`, `imem.md`, `fb.md`, `docs/mmu-encoding.md`, `src/mmu/PageTable.h`
- FIFO: `docs/hardware-model/fifo.md`, `chan.md`, `top.md`, `mc.md`, `docs/pushbuffer-encoding.md`, `src/fifo/PushBuffer.h`
- GR: `docs/hardware-model/gr.md`, `ltc.md`, `privring.md`, `timer.md`, `analysis/min_chain.md`, `analysis/compute_launch.md`
- All: `analysis/linux_deps.md`, `docs/register-io.md`
