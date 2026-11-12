// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include <cstdint>
namespace k40::gr {
// The GR bring-up as data. tools/gr/program.py records the host model
// (tools/gr/model.py) into these ops after the model reproduced the Linux
// reference trace. The op tables are build output (ProgramData.cpp).
enum class Kind:uint8_t {
    Write,     // write a to addr
    WriteSlot, // write ((slot >> shift) & a) | b to addr
    Read,      // slot = read addr
    Expect,    // read addr; stop unless (value & a) == b
    Mask,      // old = read addr; write (old & ~a) | b; slot = old when slot is set
    MaskSlot,  // old = read addr; write (old & ~a) | slot
    Poll,      // read addr until (value & a) == b, bounded
    WaitIdle,  // the engine idle wait of Nouveau
    Delay,     // wait a microseconds
    Hook       // call the driver: a is the hook number
};
struct Op {Kind kind;uint8_t slot,shift;uint32_t addr,a,b;};
struct Stage {const Op* ops;uint32_t count;};
// Run data that the driver supplies before a stage that uses it. Addresses in
// bytes: channel addresses for PagePool, Bundle and Attrib; physical VRAM
// addresses for Instance, the two MMU fault pages and Runlist.
enum Input:uint8_t {Instance,PagePool,Bundle,Attrib,MmuWrite,MmuRead,Runlist,InputCount};
constexpr uint8_t noSlot=0xff; // no source: software marker for "no slot".
constexpr unsigned maxSlots=64; // no source: software bound; program.py refuses more.
constexpr uint32_t contextPointerHook=1; // no source: hook number of program.py; engine/gr/ctxgf100.c:1483-1487.
constexpr uint32_t attachHook=2; // no source: hook number of program.py; fifo/gk104.c:134-170.
// One entry of the per-channel register list (engine/gr/gf100.c:469-479): the value is
// ((slot >> shift) & a) | b, or b alone when slot is noSlot.
struct Patch {uint32_t addr;uint8_t slot,shift;uint32_t a,b;};
// One owned record of the compute stage and its place in the channel address space.
struct Region {uint8_t role;uint32_t bytes;uint64_t va;bool writable,zero;};
// Constant words of one record, written before the channel is bound.
struct Blob {uint8_t role;uint32_t offset;const uint32_t* words;uint32_t count;};
// GR stages (verified against the trace), then the channel sequences on the GR runlist.
extern const Stage gating,start,golden,fifo,bind,attach,teardown;
extern const Patch patchList[];
extern const Region regions[];
extern const Blob blobs[];
extern const unsigned patchCount,slotCount,regionCount,blobCount,chid,pushBytes,elements;
extern const uint32_t inputMultiplier;
}
