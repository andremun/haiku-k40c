# Firmware image (VBIOS) of the development card

Captured 2026-10-14 in the Linux guest with the K40c at host address
`0000:04:00.0` passed through, from Nouveau's copy in debugfs
(`/sys/kernel/debug/dri/0000:00:03.0/vbios.rom`), after Nouveau had
chosen and checked its image ("bios: using image from PROM" in the
earlier debug run). Script: `tools/guest/files/capture_vbios.sh`.
The guest has no PCI ROM file for the card, so the sysfs route is not
available there.

| Item | Value |
|---|---|
| File (outside this repository) | `~/haiku-cross/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom` |
| Size | 181,760 bytes |
| SHA-256 | `aecb0b5fa466f64e2651a551a3cad57cccbdedd929e3996f542201af06ff1f54` |
| Version string | `Version 80.80.65.00.01`, board `GK110B P2081 SKU 0206`, `GK110B Board - 20810206` |
| Agrees with | `nvidia-smi` VBIOS version 80.80.65.00.01 (`reference/pci/`), Nouveau's "bios: version 80.80.65.00.01" |
| BIT table | signature at offset `0x1c2` |
| PCI images | x86 image at `0x0` (59,904 bytes), EFI image at `0xea00` (70,144 bytes, last image flag set); then the NVIDIA data that Nouveau reported as types `e0` and `70` |

The image is NVIDIA's firmware. It is kept outside the repository, which
may become public, and only its hash and description are recorded here.
The card at `0000:03:00.0` has the same VBIOS version but its image was
not read.

Use: offline decoding of the BIT table, the start-up scripts, and the GPIO
and I²C tables (track A of `docs/S1-PLAN.md`). Reading the file never
touches the card.
