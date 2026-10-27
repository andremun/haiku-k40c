# S1C findings

KNOWN (TRACE_VERIFIED): VGA port operations use byte-wide card MMIO.
Source: reference/nouveau/nvkm/engine/disp/vga.c:27-30,49-52.
Capture: reference/linux-run-debug/mmiotrace.txt.xz:45595-45598,46468-46469.
Read those capture lines with Python lzma.open and line enumeration.
KNOWN (TRACE_VERIFIED): INIT_IO helper writes occur at capture lines 45579-45594.
Source: reference/nouveau/nvkm/subdev/bios/init.c:1631-1647.
UNKNOWN: whether omission permits bring-up. No board policy decision was made.
S1A/S1B host checks passed in the recorded 2026-10-26 status.
The S1A cardless rerun remains pending. No VM command ran for this task.
