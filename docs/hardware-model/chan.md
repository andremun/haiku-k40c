# chan: Hardware Model

## Purpose
The channel function table (gk110_chan) describes per-channel resources: an instance block (inst) that holds PBDMA state, a USERD area (userd) containing the command-buffer put/get pointers visible to the GPU driver, and a RAMFC block (ramfc) that the PBDMA reads to fetch commands. The table provides bind/unbind to attach or detach a channel, start/stop to enable or disable it, and preempt to take the channel off the engine. On channel bind the driver writes the instance-block address and runlist ID to channel control registers (0x800000–0x800004), then writes a full set of RAMFC state values (command-buffer base address, size, USERD address, privilege flag, channel ID) into the instance block before calling nvkm_done to commit the changes. The RAMFC block is at the start of the instance block; gk104_chan_ramfc_write (fifo/gk104.c:82) writes 15 words: 0x08 and 0x0c the USERD address, 0x10 the value 0x0000face, 0x30 0xfffff902, 0x48 and 0x4c the address of the command buffer (GPFIFO) with log2 of its entry count in bits 16 and up of 0x4c, 0x84 0x20400000, 0x94 0x30000000 or'ed with the devm mask, 0x9c 0x00000100, 0xac 0x0000001f, 0xe4 the privilege bit 0x20, 0xe8 the channel ID, 0xb8 0xf8000000, 0xf8 0x10003080 and 0xfc 0x10000010. The source does not name most of these words.

## Nouveau files

- Constructor: **gk110_fifo_new** (`nvkm/engine/fifo/gk110.c:128`)
- Function table: **gk110_chan** (`nvkm/engine/fifo/gk110.c:49`)

## Members

| Member | Function | Role | Needed | Registers |
|--------|----------|------|--------|-----------|
| inst | gf100_chan_inst | data | True | 0 |
| size | 0x1000 | data | True | 0 |
| zero | true | data | True | 0 |
| vmm | true | data | True | 0 |
| userd | gk104_chan_userd | data | True | 0 |
| bar | 1 | data | True | 0 |
| size | 0x200 | data | True | 0 |
| clear | gf100_chan_userd_clear | runtime | True | 0 |
| ramfc | gk104_chan_ramfc | data | True | 0 |
| write | gk104_chan_ramfc_write | runtime | True | 0 |
| devm | 0xfff | data | True | 0 |
| priv | true | data | True | 0 |
| bind | gk104_chan_bind | runtime | True | 1 |
| unbind | gk104_chan_unbind | teardown | True | 1 |
| start | gk104_chan_start | runtime | True | 1 |
| stop | gk104_chan_stop | teardown | True | 1 |
| preempt | gk110_chan_preempt | runtime | True | 0 |

## Dependencies
imem, mmu

## KNOWN

- **clear**: Maps the USERD memory and writes zero to ten shadow-register locations (0x040, 0x044, 0x048, 0x04c, 0x050, 0x058, 0x05c, 0x060, 0x088, 0x08c) then unmaps the memory (`nvkm/engine/fifo/gf100.c:118`)
- **write**: Writes 15 words into the instance block: the USERD address (0x08, 0x0c), 0x0000face (0x10), 0xfffff902 (0x30), the command buffer address and log2 of its entry count (0x48, 0x4c), 0x20400000 (0x84), 0x30000000 with the devm mask (0x94), 0x100 (0x9c), 0x1f (0xac), the privilege bit (0xe4), the channel ID (0xe8), 0xf8000000 (0xb8), 0x10003080 (0xf8) and 0x10000010 (0xfc) (`nvkm/engine/fifo/gk104.c:82`)
- **bind**: Sets the runlist ID in the channel control register at 0x800004 then calls gk104_chan_bind_inst to write the instance-block address to 0x800000 (`nvkm/engine/fifo/gk104.c:72`)
- **unbind**: Writes zero to the channel instance-block register at 0x800000 + (chan->id * 8) to detach the channel from the PBDMA (`nvkm/engine/fifo/gk104.c:56`)
- **start**: Sets the channel-enable bit (0x00000400) in the channel control register at 0x800004 + (chan->id * 8) (`nvkm/engine/fifo/gk104.c:48`)
- **stop**: Sets bit 0x00000800 in the channel control register at 0x800004 + (chan->id * 8): a disable request (the mask and the value are both 0x800) (`nvkm/engine/fifo/gk104.c:40`)
- **preempt**: Calls the preempt function of the channel group (cgrp) when the channel is in one, otherwise gf100_chan_preempt, which writes the channel ID to register 0x002634 (`nvkm/engine/fifo/gk110.c:36`)

## INFERRED

- **inst**: Channel instance block descriptor: 4 KB size with zero-fill and virtual-memory mapping flags (`nvkm/engine/fifo/gf100.c:142`)
- **size**: Channel instance block is allocated as a 0x1000-byte (4 KB) region
- **zero**: The instance block must be zero-filled when the channel is created
- **vmm**: The instance block uses virtual memory mapping through the GPU VMM subsystem
- **userd**: USERD (user-visible) area descriptor: BAR 1, 0x200 bytes size, clear function for shadow registers (`nvkm/engine/fifo/gk104.c:115`)
- **bar**: USERD is reached through BAR 1; gk104_fifo_init then writes the USERD base in BAR1 to 0x002254
- **size**: The USERD area size is 0x200 bytes
- **ramfc**: RAMFC descriptor (the block with the channel's PBDMA state; RAMFC is not expanded in the source): the write function, the devm mask 0xfff and the privileged flag (`nvkm/engine/fifo/gk104.c:108`)
- **devm**: The devm mask 0xfff; ramfc.write stores 0x30000000 or'ed with it at offset 0x94
- **priv**: Channels run in privileged mode by default, setting bit 0x20 at instance-block offset 0xe4

## UNKNOWN

(none)
