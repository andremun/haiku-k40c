// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memory/VramArena.h"
namespace k40::memory::vram {
bool normalLayout(const Probe& p,uint64_t expected,Layout& out)
{
    out={};
    if(!expected || !p.parts || p.parts>32 || !p.units || p.units>32 || p.units%p.parts)return false;
    uint64_t total=0,common=0;uint32_t active=0;
    // fb/ramgf108.c:30-44 gives one LTC per FBP; ramgf100.c:505-520 tests mixed RAM.
    for(uint32_t part=0;part<p.parts;++part) {
        uint64_t amount=0;
        for(uint32_t sub=0;sub<p.units/p.parts;++sub) {
            const auto unit=part*(p.units/p.parts)+sub;
            if(!(p.disabled&(uint32_t(1)<<unit))) {
                if(!p.mib[unit])return false;
                amount+=uint64_t(p.mib[unit])<<20; // no source: MiB-to-byte conversion.
            }
        }
        if(amount) {
            if(common && common!=amount)return false;
            common=amount;total+=amount;++active;
        }
    }
    if(!active || total!=expected)return false;
    if(total>(uint64_t(1)<<44))return false; // instmem/nv50.c:62-63 physical window address mask.
    out={total,active};return true;
}
uint64_t Arena::requiredBytes(Role role)
{
    switch(role) {
    case Role::DebugRead:case Role::DebugWrite:return uint64_t(1)<<17; // fb/gf100.c:44-64; fb/gk110.c:64.
    case Role::Directory:return uint64_t(1)<<16; // mmu/vmmgk104.c:41-42, 8192 eight-byte PDEs.
    case Role::SmallTable:return uint64_t(1)<<18; // mmu/vmmgk104.c:40-41, 32768 eight-byte SPTEs.
    case Role::Instance:return 4096; // bar/gf100.c:93.
    case Role::DataA:case Role::DataB:return 4096; // no source: software test-page extent, matching small-page mode.
    case Role::ChanDirectory:return uint64_t(1)<<16; // mmu/vmmgk104.c:41-42, channel VMM PDB.
    case Role::ChanSmall:return uint64_t(1)<<18; // mmu/vmmgk104.c:40-41, channel VMM SPT.
    case Role::ChanInstance:return 4096; // fifo/gf100.c:142-143 gf100_chan_inst, 0x1000 bytes.
    case Role::Userd:return 4096; // fifo/gk104.c:117 0x200 slots; no source: one page for channels 0-7.
    case Role::Gpfifo:case Role::Push:case Role::Runlist:return 4096; // no source: one small page each.
    case Role::CopySource:case Role::CopyDest:return 4096; // no source: one small page each, the S2 copy extent.
    default:return 0;
    }
}
bool Arena::configure(const Probe& p,uint64_t expected,uint64_t owner,uint64_t epoch,unsigned limit)
{
    if(attempted_)return false;
    attempted_=true;
    Layout layout;
    if(!owner || !epoch || !limit || limit>capacity || !normalLayout(p,expected,layout)){failed_=true;return false;}
    const uint64_t head=256*1024,tail=1024*1024; // fb/ramgf100.c:497-498,555-558.
    const uint64_t scratch=4096; // no source: A7 owned scratch page at normal-heap start; src/a7/Owner.cpp:250-253.
    if(layout.bytes<=head+scratch+tail){failed_=true;return false;}
    total_=layout.bytes;begin_=cursor_=head+scratch;end_=total_-tail;
    owner_=owner;epoch_=epoch;limit_=limit;configured_=true;
    Token first,second;
    if(!allocate(Role::DebugRead,requiredBytes(Role::DebugRead),4096,first)
        || !allocate(Role::DebugWrite,requiredBytes(Role::DebugWrite),4096,second))return false; // fb/gf100.c:54-60 alignment.
    return true;
}
const Record* Arena::find(Token token) const
{
    if(token.owner!=owner_ || token.epoch!=epoch_ || !token.id || token.id>count_)return nullptr;
    const auto& r=records_[token.id-1];return r.token.id==token.id?&r:nullptr;
}
Record* Arena::find(Token token){return const_cast<Record*>(static_cast<const Arena*>(this)->find(token));}
bool Arena::allocate(Role role,uint64_t bytes,uint64_t alignment,Token& out)
{
    out={};
    if(!healthy())return false;
    bool duplicate=false;for(unsigned i=0;i<count_;++i)duplicate|=records_[i].role==role;
    const bool aligned=alignment>=4096 && !(alignment&(alignment-1)); // mmu/vmmgk104.c:41-42 minimum alignment.
    if(duplicate || !bytes || bytes!=requiredBytes(role) || !aligned || count_>=limit_
        || cursor_>UINT64_MAX-(alignment-1)){fail();return false;}
    const auto address=(cursor_+alignment-1)&~(alignment-1);
    if(address>end_ || bytes>end_-address){fail();return false;}
    auto& r=records_[count_];r={};r.role=role;r.token={owner_,epoch_,count_+1};
    r.physical={address};r.bytes=bytes;r.alignment=alignment;
    out=r.token;++count_;cursor_=address+bytes;return true;
}
bool Arena::span(Token token,uint64_t offset,uint64_t bytes,VramPhysical& out) const
{
    out={0};const auto* r=find(token);
    if(!healthy() || !r || !bytes || offset>r->bytes || bytes>r->bytes-offset)return false;
    out={r->physical.value+offset};return true;
}
bool Arena::describe(Token token,Record& out) const
{const auto* r=find(token);out={};if(!r)return false;out=*r;return true;}
bool Arena::at(unsigned index,Record& out) const
{out={};if(index>=count_)return false;out=records_[index];return true;}
bool Arena::dirty(Token token)
{
    auto* r=find(token);if(!healthy() || !r || r->referenced)return false;
    if(r->writeGeneration==UINT64_MAX){fail();return false;}
    ++r->writeGeneration;r->staged=false;return true;
}
bool Arena::tableDirty(Token token)
{
    auto* r=find(token);if(!healthy() || !r || r->role!=Role::SmallTable)return false;
    if(r->writeGeneration==UINT64_MAX){fail();return false;}
    ++r->writeGeneration;r->staged=false;return true;
}
bool Arena::staged(Token token)
{auto* r=find(token);if(!healthy() || !r || !r->writeGeneration)return false;r->staged=true;return true;}
bool Arena::reference(Token token)
{auto* r=find(token);if(!healthy() || !r || !r->staged)return false;r->referenced=r->retained=true;return true;}
bool Arena::candidateBar(Token token,BarVirtual address)
{
    auto* r=find(token);if(!healthy() || !r || (address.value&4095))return false; // mmu/vmmgk104.c:41 small-page alignment.
    if(r->role!=Role::DataA && r->role!=Role::DataB)return false;
    r->candidateBar=true;r->bar=address;return true;
}
void Arena::fail()
{failed_=true;for(unsigned i=0;i<count_;++i)records_[i].retained=true;}
}
