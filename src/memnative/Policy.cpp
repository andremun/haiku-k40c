// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memnative/Policy.h"
namespace k40::memnative {
using namespace memory::vram;
using memstage::Phase;
bool Policy::record(Role role,Record& out) const
{for(unsigned i=0;i<arena_.count();++i)if(arena_.at(i,out) && out.role==role)return true;return false;}
bool Policy::physical(uint32_t reg,Record& out,uint64_t& offset) const
{
    if(selected_==UINT64_MAX || reg<0x700000 || reg>=0x800000 || (reg&3))return false; // instmem/nv50.c:62-71 window extent.
    const uint64_t address=selected_+reg-0x700000; // instmem/nv50.c:71.
    for(unsigned i=0;i<arena_.count();++i)if(arena_.at(i,out) && address>=out.physical.value
        && address-out.physical.value<=out.bytes-4){offset=address-out.physical.value;return true;}
    return false;
}
bool Policy::read(uint32_t reg,bool window) const
{
    if(reg&3)return false;
    // fb/gf100.c:37; fifo/gk104.c:658; fifo/gf100.c:723; privring/gk104.c:62-66.
    if(reg==0x100 || reg==0x2100 || reg==0x259c || reg==0x120058 || reg==0x12005c
        || reg==0x120070 || reg==0x120074 || reg==0x120078)return true; // privring/gk104.c:62-66.
    if(reg==0x1704 || reg==0x100c80 || reg==0x70000)return true; // bar/gf100.c:46-58; vmmgf100.c:199-224; bar/g84.c:35.
    if(reg==0x22438 || reg==0x2243c || reg==0x22554)return true; // ramgf108.c:30-41; ramgf100.c:477,502.
    if(reg>=0x11020c && reg<=0x12f20c && (reg-0x11020c)%0x1000==0) { // ramgf100.c:467 FBPA amount, maximum 32 from software profile.
        const auto unit=(reg-0x11020c)/0x1000;return unit<units_ && !(disabled_&(uint32_t(1)<<unit)); // ramgf100.c:467; ramgf108.c:36-39.
    }
    if(reg>=0x22700 && reg<0x22800)return true; // top/gk104.c:37-45 64 words.
    if(reg>=0x2800 && reg<0x2a00)return (pending_&(uint32_t(1)<<((reg-0x2800)/16)))!=0; // fifo/gf100.c:699-726.
    const uint32_t bases[]={0x122120,0x124120,0x128120}; // privring/gk104.c:28-55.
    const unsigned counts[]={hubs_,rops_,gpcs_};
    const unsigned starts[]={8,16,0}; // privring/gk104.c:69-87 status bit groups.
    for(unsigned group=0;group<3;++group) {
        const unsigned maximum=group==0?8:group==1?16:32;
        if(counts[group]>maximum)continue;
        for(unsigned i=0;i<counts[group];++i)if((group==2?priv1_:priv0_)&(uint32_t(1)<<(starts[group]+i))) {
            const auto base=bases[group]+i*0x800; // privring/gk104.c:28-55.
            if(reg>=base && reg<=base+8)return true;
        }
    }
    Record r;uint64_t offset;return window && physical(reg,r,offset);
}
void Policy::observed(uint32_t reg,uint32_t value)
{
    switch(reg) {
    case 0x259c:pending_=value;break; // fifo/gf100.c:723.
    case 0x120058:priv0_=value;break; // privring/gk104.c:62.
    case 0x12005c:priv1_=value;break; // privring/gk104.c:63.
    case 0x120070:hubs_=value;break; // privring/gk104.c:64.
    case 0x120074:rops_=value;break; // privring/gk104.c:65.
    case 0x120078:gpcs_=value;break; // privring/gk104.c:66.
    case 0x2243c:units_=value<=32?value:0;break; // ramgf108.c:31; no source: software count ceiling.
    case 0x22554:disabled_=value;break; // ramgf100.c:477.
    case 0x100c80:status_=value;if(commands_ && (value&0x8000))queued_=true;break; // vmmgf100.c:224 queued observation.
    case 0x1704:context_=value;break; // bar/gf100.c:46-58 ownership readback.
    }
}
unsigned Policy::commandPhase() const
{
    if(faults_.completed(Phase::Tables))return 0;
    if(faults_.completed(Phase::Mapped))return 1;
    if(faults_.completed(Phase::Remapped))return 2;
    return 3;
}
bool Policy::dataValue(const Record& r,uint64_t offset,uint32_t value) const
{
    if(!r.writeGeneration || r.staged)return false;
    const bool physicalPhase=faults_.completed(Phase::Post);
    if(r.role==Role::DebugRead || r.role==Role::DebugWrite)return physicalPhase && !r.referenced && value==0;
    if(r.role==Role::DataA || r.role==Role::DataB) {
        const auto expected=memstage::Upload::pattern(r.physical.value+offset,memstage::Image::Pattern);
        return physicalPhase && !r.referenced && (value==expected || value==~expected);
    }
    const bool update=r.referenced && r.role==Role::SmallTable && offset<8
        && (faults_.completed(Phase::Mapped) || faults_.completed(Phase::Remapped));
    if(r.referenced && !update)return false;
    if(!update && !faults_.completed(Phase::Physical))return false;
    if(value==0 && !update)return true;
    Record directory,small,a,b;uint64_t encoded=0;
    if(!record(Role::Directory,directory) || !record(Role::SmallTable,small)
        || !record(Role::DataA,a) || !record(Role::DataB,b))return false;
    if(r.role==Role::Directory) {
        if(offset>=8 || !memstage::tables::smallDirectory(small.physical,encoded))return false;
    } else if(r.role==Role::SmallTable) {
        if(offset>=16)return false;
        const bool second=offset>=8;
        const auto target=update?(faults_.completed(Phase::Mapped)?b.physical:a.physical):(second?b.physical:a.physical);
        if(!memstage::tables::pte(target,encoded))return false;
    } else if(r.role==Role::Instance) {
        uint64_t base,limit;
        if(!memstage::tables::instance(directory.physical,aperture_,base,limit))return false;
        if(offset>=0x200 && offset<0x208)encoded=base; // vmmgf100.c:358.
        else if(offset>=0x208 && offset<0x210)encoded=limit; // vmmgf100.c:359.
        else return false;
    } else return false;
    return value==uint32_t(encoded>>((offset%8)*8));
}
bool Policy::write(uint32_t reg,uint32_t value,bool window,bool mmu)
{
    if(!arena_.healthy() || !faults_.ready() || faults_.completed(Phase::Disabled) || (reg&3))return false;
    if(reg==0x1700) { // instmem/nv50.c:68 physical-window selector.
        if(!window)return false;
        const uint64_t selected=uint64_t(value)<<16;
        if(selected&0xfffff)return false; // instmem/nv50.c:62-68 selector must identify a 1 MiB window.
        Record r;bool owned=false;
        for(unsigned i=0;i<arena_.count();++i)if(arena_.at(i,r))owned|=selected<=r.physical.value+r.bytes-1 && selected+1048576>r.physical.value;
        if(!owned)return false;
        selected_=selected;return true;
    }
    if(reg==0x70000)return window && value==1; // bar/g84.c:33 flush request, no other bits.
    Record r;uint64_t offset;
    if(reg>=0x700000 && reg<0x800000)return window && physical(reg,r,offset) && dataValue(r,offset,value); // instmem/nv50.c:71.
    if(!mmu)return false;
    const auto phase=commandPhase();
    if(reg==0x100c80) { // fb/gf100.c:66-77 page-mode RMW only.
        if(mode_ || phase!=0 || commands_ || value!=(status_&~uint32_t(1)))return false;
        mode_=true;return true;
    }
    if(reg==0x100cb8) { // vmmgf100.c:185,216-218 this-PDB selector.
        if(!mode_ || pdb_ || phase>=3 || commands_!=phase || !(status_&0x00ff0000) // vmmgf100.c:199 free-slot prerequisite.
            || !record(Role::Directory,r) || !r.referenced || !r.staged
            || (r.physical.value>>8)>UINT32_MAX || value!=uint32_t(r.physical.value>>8))return false; // vmmgf100.c:199,216.
        pdb_=true;return true;
    }
    if(reg==0x100cbc) { // vmmgf100.c:221-233 PAGE_ALL|HUB_ONLY only.
        if(!pdb_ || phase>=3 || commands_!=phase || value!=0x80000005)return false; // vmmgf100.c:221,230-233.
        pdb_=false;queued_=false;++commands_;return true;
    }
    if(reg==0x1704) { // bar/gf100.c:46-58 BAR1 only.
        if(value&0x80000000) { // bar/gf100.c:58 enable field.
            if(expectedContext_ || context_&0x80000000 || phase!=0 || commands_!=1 || !queued_ // bar/gf100.c:46-58 enable field.
                || !record(Role::Instance,r) || !r.referenced || !r.staged || (r.physical.value>>12)>=(uint64_t(1)<<31)
                || value!=(0x80000000|uint32_t(r.physical.value>>12)))return false; // bar/gf100.c:56-58.
            expectedContext_=value;return true;
        }
        return faults_.completed(Phase::Restored) && commands_==3 && queued_ && expectedContext_
            && context_==expectedContext_ && value==(expectedContext_&0x7fffffff); // bar/gf100.c:46-49 clear owned enable only.
    }
    return false;
}
bool Policy::barRead(uint64_t offset,bool mmu) const
{
    return mmu && queued_ && expectedContext_ && commands_>=1 && commands_<=3
        && offset<8192 && !(offset&3) && (faults_.completed(Phase::Tables)
            || faults_.completed(Phase::Mapped) || faults_.completed(Phase::Remapped));
}
}
