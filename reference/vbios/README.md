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

## Decoder

The tables and scripts were decoded with `nvbios` from envytools, commit
`f102b82381f3f11cee113d16374c87091db039d9` (the same pin as
`agent-refs/envytools` in llm-server). The project's full build needs
`pkg-config` and libraries that are not installed, so only `nvbios` was
built, by hand and without root, in
`~/haiku-cross/src/envytools/build-manual/` (the flex and bison sources
generated into `gen/`). Output of `nvbios` on the image:
`~/haiku-cross/vbios/decoded/all.txt`, outside the repository because it
reproduces the firmware's content. It warns that no strap is given and
that it cannot parse BIT table `B`; the tables used so far (scripts, GPIO,
I²C, external devices) decode. The board operations found with it are in
`docs/BOARD-OPERATIONS.md`.

## Available copy verified in V1 follow-up (2026-10-16)

The user supplied the mounted directory `~/mediaflux/vbios/`. Read-only
verification of `/home/unimelb.edu.au/mariom1/mediaflux/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom` found exactly 181,760 bytes and SHA-256
`aecb0b5fa466f64e2651a551a3cad57cccbdedd929e3996f542201af06ff1f54`,
matching the capture above. The ROM is available locally; no recapture,
copy into Git or physical-card access is needed.

Saved decoder output: `/home/unimelb.edu.au/mariom1/mediaflux/vbios/decoded/all.txt`; SHA-256
`dce802b40173ececd2df0217e9e3adbb816614a64d7c0b0f1d00ad26646df0bf`.
Its opening diagnostics include no strap specified and parse warnings for
BIT tables B, C and I, among others. These warnings do not by themselves
establish whether the script listing is complete; review the relevant
sections and reproduce decoding with the pinned tool before accepting A3.
The saved output was hashed, not regenerated in this follow-up.

Reproduce the offline input inventory from the repository root:

```sh
python3 tools/s1_verification_inputs.py --rom "/home/unimelb.edu.au/mariom1/mediaflux/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom"
python3 tools/s1_verification_inputs.py --rom "/home/unimelb.edu.au/mariom1/mediaflux/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom" --check
```

Both commands succeed; the report records ROM match and still marks the
other external verification inputs incomplete. `--check` must use the same
explicit ROM argument to reproduce this report. Mounted content may be
unavailable on another host; retain the expected hash as the identity gate.

## Pinned decoder reproduced in V2 (2026-10-16)

The reference source is now restored and clean at the recorded envytools pin.
`tools/build_nvbios.py` builds a decoder using locally extracted tools, without
system installation or source changes. A fresh full decode matches
`~/mediaflux/vbios/decoded/all.txt` byte for byte, including all diagnostics.
Script-only and board-table decoding also complete. Commands, package hashes
and limitations are in `work/V2/RESULT.md` and `work/V2/evidence.json`.

The BIT-I parser warning does not prevent the separate front-end code from
reading initialization pointers and printing scripts (nvbios.c:1100-1123 and
1282-1318). This explains the output, not its completeness. A3 reachability,
log agreement and helper semantics still require their own verification.
