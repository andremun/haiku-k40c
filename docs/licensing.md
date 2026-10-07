# Licensing record

This project is under the MIT License (`LICENSE`). New source files carry:

    Copyright 2026 <author>. Distributed under the terms of the MIT License.

Why MIT: Haiku is MIT-licensed and asks for MIT for code that may be
merged, and the Nouveau code that this project studies is MIT-licensed.

| Source | License | Consequence |
|---|---|---|
| Haiku (`reference/haiku`) | MIT | Headers and interfaces may be used. Same license as this project. |
| Nouveau (`reference/nouveau`, Linux v6.12) | MIT in 403 file headers; one file `GPL-2.0 OR MIT`; one file `GPL-2.0-only` (`Kconfig`, not code); 54 files with neither an SPDX line nor the MIT text | Study and reimplement. Check the header of each consulted file and record it below. Take nothing from a file without a license notice. |
| Mesa (`reference/mesa`, nouveau driver and codegen) | MIT (check each file header) | Study and reimplement, as for Nouveau. A shader binary that Mesa generates for our own source is our output, not Mesa code. |
| envytools `rnndb` | MIT | Register names and bit fields may be used with the source cited. |
| NVIDIA open-gpu-doc | MIT (check each file) | As for envytools. |
| NVIDIA firmware and the proprietary driver | Proprietary | Never copy into this repository. Firmware is loaded from the user's system at run time (see phase C2). |

Reimplement, do not copy. A short constant table or register offset is a
fact and needs a source citation, not a license. A copied function or
block keeps its original notice and is listed in the last column below.

| Source file consulted | License (from header) | Used for | Copied material |
|---|---|---|---|
