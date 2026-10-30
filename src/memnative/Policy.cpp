// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memnative/Policy.h"
#include "memstage/ChannelImage.h"
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
    if((reg&3) || reg>bar0View-4)return false; // Never beyond the mapped BAR0 view.
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
    if(channelRead(reg))return true;
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
    if(!channelActive())return;
    using memstage::channel::chid;
    if(reg==0x100c80 && waitQueued_ && (value&0x8000))chanQueued_=true; // vmmgf100.c:224.
    if(reg==0x000204 && step_==8){mask_=value;probed_=true;} // fifo/gf100.c:927-934 present units.
    if(reg>=0x002390 && reg<0x0023b0)runm_[(reg-0x002390)/4]=value; // fifo/gk104.c:392.
    if(reg==0x002a04 && step_==9){value2a04_=value;read2a04_=true;} // fifo/gk104.c:740.
    if(reg>=0x04013c && reg<0x04013c+8*0x2000 && (reg-0x04013c)%0x2000==0 && step_==10){control_=value;readControl_=true;} // fifo/gf100.c:357.
    if(reg==0x800004+chid*8){state_=value;readState_=true;} // fifo/gk104.c:44-77.
    if(reg==0x800000+chid*8){inst_=value;readInst_=true;} // fifo/gk104.c:60-68.
    if(reg>=0x002284 && reg<0x002284+16*8 && (reg-0x002284)%8==0)runlistClear_=!(value&0x00100000); // fifo/gk104.c:426.
    if(reg==0x002634)preemptClear_=!(value&0x00100000); // fifo/gf100.c:372.
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
    if(channelActive())return const_cast<Policy*>(this)->channelData(r,offset,value);
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
    if(!arena_.healthy() || !faults_.ready() || (reg&3) || reg>bar0View-4)return false; // Mapped BAR0 view only.
    if(channelActive() && reg!=0x1700 && reg!=0x70000 && (reg<0x700000 || reg>=0x800000)) // instmem/nv50.c:62-71 window; bar/g84.c:33.
        return mmu && channelWrite(reg,value);
    if(faults_.completed(Phase::Disabled))return false;
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
    if(channelActive()) // cla16f.h:62-63 GP_GET/GP_PUT of the selected USERD slot only.
        return mmu && step_>=6 && step_<=23 && (offset==memstage::channel::gpGet || offset==memstage::channel::gpPut);
    return mmu && queued_ && expectedContext_ && commands_>=1 && commands_<=3
        && offset<8192 && !(offset&3) && (faults_.completed(Phase::Tables)
            || faults_.completed(Phase::Mapped) || faults_.completed(Phase::Remapped));
}
}

namespace k40::memnative {
using memstage::channel::chid;
bool Policy::channelActive() const{return faults_.completed(Phase::ChannelBase);}
bool Policy::runlist(uint32_t& out) const
{
    // top/gk104.c:79 CE0 is TOP type 1; independent of the Channel's own route.
    unsigned matches=0;out=0;
    for(unsigned i=0;i<faults_.routeCount();++i) {
        memstage::Routing r;if(!faults_.route(i,r))return false;
        if(r.type==1 && r.instance==0 && r.hasRunlist){out=r.runlist;++matches;}
    }
    return matches==1 && out<16; // fifo/gk104.c:77 four-bit field.
}
bool Policy::pbdma(uint32_t& out) const
{
    uint32_t rl;if(!probed_ || !runlist(rl))return false;
    unsigned matches=0;out=0;
    for(unsigned p=0;p<8;++p)if((mask_&(1u<<p)) && (runm_[p]&(1u<<rl))){out=p;++matches;} // fifo/gk104.c:392,770-777.
    return matches==1;
}
bool Policy::channelAddresses(Record out[7]) const
{
    const Role roles[7]={Role::ChanDirectory,Role::ChanSmall,Role::ChanInstance,Role::Userd,Role::Gpfifo,Role::Push,Role::Runlist};
    for(unsigned i=0;i<7;++i)if(!record(roles[i],out[i]))return false;
    return true;
}
bool Policy::channelRead(uint32_t reg) const
{
    if(!channelActive())return false;
    if(reg==0x000200 || reg==0x000204 || reg==0x002a04 || reg==0x002634 || reg==0x800000+chid*8 || reg==0x800004+chid*8)return true; // fifo/gf100.c:927-934; fifo/gk104.c:44-77,740; fifo/gf100.c:372.
    if(reg>=0x002390 && reg<0x0023b0)return true; // fifo/gk104.c:392, eight PBDMAs.
    if(reg>=0x002284 && reg<0x002284+16*8 && (reg-0x002284)%8==0)return true; // fifo/gk104.c:426.
    for(unsigned p=0;p<8;++p) {
        const auto base=p*0x2000; // fifo/gf100.c:357 PBDMA stride.
        if(reg==0x04013c+base || reg==0x040108+base || reg==0x040148+base)return true; // fifo/gf100.c:357-358; fifo/gk104.c:378 status reads.
    }
    return false;
}
bool Policy::channelData(const Record& r,uint64_t offset,uint32_t value)
{
    Record roles[7];
    if(!r.writeGeneration || r.staged)return false;
    if(r.role==Role::SmallTable) { // BAR1 SPT entry 0 -> writable USERD page (Mapper::exposeUserd).
        uint64_t entry;
        if(step_!=2 || !chanQueued_ || !r.referenced || offset>=8 || !channelAddresses(roles)
            || !memstage::channel::userdPte(roles[3].physical.value,entry))return false;
        if(value!=uint32_t(entry>>((offset%8)*8)))return false;
        if(++sptWords_==2)step_=3;
        return true;
    }
    uint32_t expected;
    if(step_!=0 || r.referenced || !channelAddresses(roles)
        || !memstage::channel::expected(r.role,{roles[0].physical.value,roles[1].physical.value,roles[2].physical.value,
            roles[3].physical.value,roles[4].physical.value,roles[5].physical.value,roles[6].physical.value},offset,expected))return false;
    return value==0 || value==expected; // zeroing pass, then the exact image word.
}
bool Policy::channelWrite(uint32_t reg,uint32_t value)
{
    Record roles[7];uint32_t rl,p;
    if(!channelAddresses(roles) || !runlist(rl))return false;
    for(const auto& r:roles)if(!r.staged || (step_>0 && !r.referenced))return false;
    if(step_==0 && !roles[0].referenced)return false;
    const auto chanState=0x800004+chid*8,chanReg=0x800000+chid*8; // fifo/gk104.c:44-77.
    const auto runlistBase=uint32_t(roles[6].physical.value>>12);
    // Teardown jumps: a selected/bound channel must be stopped; an exposed but
    // unselected BAR1 context must be disabled. Nothing else may be skipped.
    // fifo/gk104.c:44 stop; bar/gf100.c:46-49 context disable.
    if(step_>=13 && step_<=17 && reg==chanState && readState_ && value==(state_|0x800))step_=18;
    if(step_>=6 && step_<=12 && reg==0x001704)step_=23; // bar/gf100.c:46-49.
    bool ok=false;
    switch(step_) {
    case 0: ok=reg==0x100cb8 && (status_&0x00ff0000) && value==uint32_t((roles[0].physical.value>>12)<<4); // vmmgf100.c:199,216.
        break;
    case 1: ok=reg==0x100cbc && value==0x80000001; // vmmgf100.c:221,230 PAGE_ALL.
        if(ok){waitQueued_=true;chanQueued_=false;}
        break;
    case 3: {
        Record bar;
        ok=reg==0x100cb8 && (status_&0x00ff0000) && record(Role::Directory,bar) // mmu/vmmgf100.c:199,216 BAR PDB.
            && value==uint32_t((bar.physical.value>>12)<<4); // vmmgf100.c:199,216 BAR PDB.
        break;
    }
    case 4: ok=reg==0x100cbc && value==0x80000005; // vmmgf100.c:221,230-233 PAGE_ALL|HUB_ONLY.
        if(ok){waitQueued_=true;chanQueued_=false;}
        break;
    case 5: ok=reg==0x001704 && chanQueued_ && expectedContext_ && context_==(expectedContext_&0x7fffffff) // bar/gf100.c:46-58.
            && value==expectedContext_; // bar/gf100.c:52-58 owned BAR1 context only.
        break;
    case 6: ok=reg==0x000200 && value==0xffffffff;break; // mc/nv04.c:120 every unit enabled; trace line 47330.
    case 7: ok=reg==0x000204 && value==0xffffffff;break; // fifo/gf100.c:927-934.
    case 8: ok=reg==0x000204 && probed_ && mask_ && mask_<=0xff && value==mask_;break; // fifo/gk104.c:739.
    case 9: ok=reg==0x002a04 && read2a04_ && value==(value2a04_|0xbfffffff);break; // fifo/gk104.c:740.
    case 10: ok=pbdma(p) && reg==0x04013c+p*0x2000 && readControl_ && value==(control_&~0x10000100u);break; // fifo/gf100.c:357.
    case 11: ok=reg==0x002254 && value==0x10000000;break; // fifo/gk104.c:749; trace 560992.
    case 12: ok=reg==chanState && readState_ && readInst_ && !state_ && !inst_
            && value==((state_&~0x000f0000u)|(rl<<16));break; // fifo/gk104.c:77; trace 562288-562289.
    case 13: ok=reg==chanReg && value==(0x80000000|uint32_t(roles[2].physical.value>>12)); // fifo/gk104.c:68.
        if(ok)readState_=false;
        break; // fifo/gk104.c:68.
    case 14: ok=reg==chanState && readState_ && value==(state_|0x400);break; // fifo/gk104.c:52.
    case 15: ok=reg==0x002270 && value==runlistBase;break; // fifo/gk104.c:446 VRAM target 0.
    case 16: ok=reg==0x002274 && value==((rl<<20)|1); // fifo/gk104.c:447.
        if(ok)runlistClear_=false;
        break;
    case 18: ok=reg==chanState && readState_ && value==(state_|0x800);break; // fifo/gk104.c:44.
    case 19: ok=reg==0x002634 && value==chid; // fifo/gf100.c:43.
        if(ok)preemptClear_=false;
        break;
    case 20: ok=reg==0x002270 && preemptClear_ && value==runlistBase;break; // fifo/gk104.c:446.
    case 21: ok=reg==0x002274 && value==(rl<<20); // fifo/gk104.c:447 empty list.
        if(ok)runlistClear_=false;
        break;
    case 22: ok=reg==chanReg && runlistClear_ && value==0;break; // fifo/gk104.c:60.
    case 23: ok=reg==0x001704 && expectedContext_ && context_==expectedContext_ // bar/gf100.c:46-49.
            && value==(expectedContext_&0x7fffffff);break; // bar/gf100.c:46-49.
    default: ok=false;
    }
    if(ok)++step_;
    return ok;
}
bool Policy::barWrite(uint64_t offset,uint32_t value,bool mmu)
{
    // nouveau_dma.c:92 GP_PUT, once, after the runlist commit completed.
    if(!channelActive() || !mmu || step_!=17 || !runlistClear_ || offset!=memstage::channel::gpPut || value!=1)return false;
    ++step_;return true;
}
}
