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
struct Addresses {uint64_t directory=0,small=0,instance=0,userd=0,gpfifo=0,push=0,runlist=0;};
// Physical placement of every channel role from the owned ledger.
bool resolve(const memory::vram::Arena&,Addresses&);
struct Word {uint32_t offset=0;uint64_t value=0;};
// The nonzero 8-byte words of one role's image; every other byte is zero.
unsigned image(memory::vram::Role,const Addresses&,Word out[],unsigned capacity);
// Expected 32-bit value at a 4-byte offset, from the same image.
bool expected(memory::vram::Role,const Addresses&,uint64_t offset,uint32_t& value);
// Writable BAR1 entry for the USERD page: valid, VRAM, kind 0.
bool userdPte(uint64_t physical,uint64_t& out);
}
