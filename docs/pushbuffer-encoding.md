# Push-Buffer Encoding

Phase D3. Bit layouts for GPFIFO push-buffer headers and GPFIFO ring entries.

## Header Word (method dispatch)

A push-buffer header word tells the GPU which subchannel to route the following
data words to, which method base they apply to, and how many data words follow.
The encoding comes from `reference/mesa/src/gallium/drivers/nouveau/nvc0/nvc0_winsys.h`
lines 65–88.

### Bit layout (all four types)

```
Bits 31-30  29      28-16        15-13          12-0
+-----------+--------+-----------+-----------+--------+
| type bits | count/data | subchannel | method>>2 |
+-----------+--------+-----------+-----------+--------+
```

All types share bits 16–28 for `count` (13 bits) or the immediate data value
(for IMMEDIATE type), bits 13–15 for `subc` (3 bits, values 0–7), and bits
0–12 for `method >> 2` (13 bits, method is always a multiple of 4).

### Type 1 — Increasing (`_SQ`, `NVC0_FIFO_PKHDR_SQ`)

```
0x20000000 | (count << 16) | (subc << 13) | (method >> 2)
```

The GPU increments the method address by 4 for each data word.
Example: subc=1, method=0x02b4, count=1 → `0x200120ad`

Source: `nvc0_winsys.h:68`

### Type 2 — Non-increasing (`_NI`, `NVC0_FIFO_PKHDR_NI`)

```
0x60000000 | (count << 16) | (subc << 13) | (method >> 2)
```

All data words target the same method address.
Example: subc=1, method=0x01b4, count=16 → `0x6010206d`

Source: `nvc0_winsys.h:74`

### Type 3 — Immediate (`_IL`, `NVC0_FIFO_PKHDR_IL`)

```
0x80000000 | (data << 16) | (subc << 13) | (method >> 2)
```

The data value is carried in the header itself (13-bit data, max 0x1fff).
Example: subc=1, method=0x1698, data=0x1000 → `0x900025a6`

Source: `nvc0_winsys.h:81`

### Type 4 — Increase-once (`_1I`, `NVC0_FIFO_PKHDR_1I`)

```
0xa0000000 | (count << 16) | (subc << 13) | (method >> 2)
```

The first data word targets `method`; subsequent words target `method + 4`.
Example: subc=1, method=0x01b0, count=5 → `0xa005206c`

Source: `nvc0_winsys.h:87`

### Validation

- `subc` must be 0–7 (3 bits).
- `method` must be a multiple of 4 and ≤ 0x7ffc (fits in 13 bits after >> 2).
- `count` must be 0–0x1fff (13 bits). A count of 0 with non-IMMEDIATE type
  throws `std::invalid_argument`.

## GPFIFO Ring Entry

Each entry in the channel's GPFIFO ring tells the PBDMA where to find a
push-buffer and how long it is. Layout from
`reference/nouveau/nouveau_dma.c` lines 82–84:

```
Word 0: lower 32 bits of push-buffer address
Word 1: upper 8 bits of address | (length << 8) | (noPrefetch ? 1<<31 : 0)
```

Specifically (nouveau_dma.c:83):

```c
nouveau_bo_wr32(pb, ip++,
    upper_32_bits(offset) | length << 8 |
    (no_prefetch ? (1 << 31) : 0));
```

Bits of Word 1:
```
Bit 31: noPrefetch flag
Bits 8-30: length in bytes (23 bits, max 0x7fffff)
Bits 0-7: upper 32 bits of address (8 bits for 40-bit addressing)
```

Constants:
- `NV50_DMA_PUSH_MAX_LENGTH = 0x7fffff` (nouveau_dma.h:50)
- `kUserdGpGet = 0x88` (nouveau_dma.c:104 — read get pointer)
- `kUserdGpPut = 0x8c` (nouveau_dma.c:92 — write put pointer)
- `kGpEntryBytes = 8` (two 32-bit words)

## GPFIFO Ring

The ring is a circular buffer of GPFIFO entries. The driver writes entries at
the put position and advances put with wrap-around modulo the ring size.
One slot is always reserved to distinguish full from empty.

The GPU reads entries, advances its own get pointer, and the driver reads
USERD offset 0x88 to see progress. The driver writes the new put value to
USERD offset 0x8c (nouveau_dma.c:92).

### Channel RAMFC word 0x4c

When the channel is bound, the driver writes word 0x4c of the channel's RAMFC
block. This word holds the log2 of the ring size (bits 16–31) and the upper
32 bits of the ring address (bits 0–15). Formula: `(log2 << 16) | upper32`,
derived from `docs/hardware-model/chan.md` which documents the gk104_chan_ramfc_write
function (`reference/nouveau/.../gk104.c:82`).

## Worked Example

Bind the compute class `0xa1c0` on subchannel 1, then send one method:

| Word | Value | Meaning |
|------|-------|---------|
| 0 | `0x20012000` | Header: increasing, subc=1, method=0, count=1 |
| 1 | `0x0000a1c0` | Data: class ID 0xa1c0 (bindObject) |

The header encodes as `0x20000000 | (1<<16) | (1<<13) | (0>>2) = 0x20012000`
(nvc0_winsys.h:68).

## Not Covered

- How the kernel tells the GPU that the put pointer moved (doorbell/irq).
- What happens on a full ring (GPU stalls, driver waits via USERD get polling).
- Subroutine calls and nested push-buffer entries.
- Fault handling when the GPU cannot access the push-buffer address.
