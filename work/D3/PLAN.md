# Task D3 Plan

## Steps
1. Write `src/fifo/PushBuffer.h` — enums, structs, constants, function declarations.
2. Write `src/fifo/PushBuffer.cpp` — encode/decode header, PushBuffer, decodeBuffer, GpEntry, GpFifo.
3. Compile acceptance test: `g++ -std=c++17 -Wall -Wextra -Werror -Isrc tests/accept/d3_accept.cpp src/fifo/*.cpp -o build/d3 && build/d3`
4. Write `tests/test_pushbuffer.cpp` (15+ checks) and update `tests/Makefile`.
5. Write `docs/pushbuffer-encoding.md` (50+ lines).
6. Run `make check`, fix failures, write RESULT.md.

## Sources
- `reference/mesa/src/gallium/drivers/nouveau/nvc0/nvc0_winsys.h` lines 65-88: header encoding formulas.
- `reference/nouveau/nouveau_dma.c` lines 72-95: GPFIFO entry layout.
- `reference/nouveau/nouveau_dma.h` line 50: `NV50_DMA_PUSH_MAX_LENGTH`.
- `docs/hardware-model/chan.md`: word 0x4c layout.
