// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "memory/VramArena.h"
namespace k40::memstage::channel {
// One host channel on the CE0 runlist, encoded like the Linux kernel channel 1
// of reference/linux-run-debug/mmiotrace.txt.xz lines 562253-562292.
constexpr uint32_t chid=1; // no source: software choice, the ID of the Linux CE channel (mmiotrace line 562290).
constexpr uint64_t gpfifoVa=0x10000000; // no source: software channel VA, distinct from physical and BAR VA.
constexpr uint64_t pushVa=0x10001000; // no source: next small page in the same SPT.
constexpr uint32_t gpfifoBytes=4096; // no source: one small page of 8-byte entries.
constexpr uint32_t userdSlot=chid*0x200; // fifo/gk104.c:117 USERD stride.
constexpr uint32_t gpGet=userdSlot+0x88,gpPut=userdSlot+0x8c; // nouveau_dma.c:92 GP_PUT 0x8c; GP_GET 0x88 per open-gpu-doc classes/host/cla16f.h line 62.
constexpr uint32_t nopHeader=0x20010002; // no source: in the checked trees; envytools dma-pusher.rst line 417 header, open-gpu-doc cla16f.h line 74 NOP 0x08.
// S2: one copy of one page on the same channel, as nve0_bo_move_copy (nouveau_boa0b5.c:37-71).
constexpr uint64_t sourceVa=0x10002000,destVa=0x10003000; // no source: next small pages in the same SPT.
constexpr uint32_t copyBytes=4096; // no source: one small page; PITCH and LINE_LENGTH as nouveau_boa0b5.c:57-59 PAGE_SIZE.
constexpr uint32_t copySubchannel=4; // include/nvif/push906f.h:19 PUSH906F_SUBC_NVA0B5.
constexpr uint32_t copyClass=0xa0b5; // nouveau_bo.c:937,962-967 class and handle; nouveau_boa0b5.c:85 object method 0x0000.
constexpr uint32_t copyOffsetIn=0x400; // include/nvhw/class/cla0b5.h:94 OFFSET_IN_UPPER, eight methods to LINE_COUNT 0x41c.
constexpr uint32_t copyLaunchMethod=0x300; // include/nvhw/class/cla0b5.h:37 LAUNCH_DMA.
// cla0b5.h:38-73: NON_PIPELINED (2), FLUSH_ENABLE (bit 2), SRC and DST PITCH (bits 7, 8),
// MULTI_LINE_ENABLE (bit 9); semaphore, interrupt and remap off; both types VIRTUAL.
constexpr uint32_t copyLaunch=0x00000386; // nouveau_boa0b5.c:61-71.
constexpr uint32_t copyPushOffset=8,copyPushBytes=48; // no source: after the NOP; 12 words, see image().
// include/nvif/push906f.h:22-44 with include/nvhw/class/cl906f.h:54-70: SEC_OP in bits 31:29
// (INC_METHOD 1, IMMD_DATA_METHOD 4), count or data in 28:16, subchannel in 15:13, method/4 in 11:0.
constexpr uint32_t methodHeader(uint32_t op,uint32_t count,uint32_t subchannel,uint32_t method)
{return (op<<29)|(count<<16)|(subchannel<<13)|(method>>2);}
struct Addresses {uint64_t directory=0,small=0,instance=0,userd=0,gpfifo=0,push=0,runlist=0,source=0,dest=0;bool copy=false;};
// Physical placement of every channel role from the owned ledger: the seven S1
// roles, or those and the two S2 copy pages (copy = true).
bool resolve(const memory::vram::Arena&,Addresses&);
struct Word {uint32_t offset=0;uint64_t value=0;};
// The nonzero 8-byte words of one role's image; every other byte is zero.
unsigned image(memory::vram::Role,const Addresses&,Word out[],unsigned capacity);
// Expected 32-bit value at a 4-byte offset, from the same image.
bool expected(memory::vram::Role,const Addresses&,uint64_t offset,uint32_t& value);
// Writable entry (BAR1 USERD page, S2 destination page): valid, VRAM, kind 0.
bool userdPte(uint64_t physical,uint64_t& out);
}
