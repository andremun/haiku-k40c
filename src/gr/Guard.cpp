// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "gr/Guard.h"
#include "memstage/ChannelImage.h"
namespace k40::gr {
using namespace memory::vram;
namespace {
const Stage* const sequence[Guard::stages]={&fifo,&bind,&gating,&start,&golden,&attach,&teardown};
constexpr unsigned attachStage=5,teardownStage=6,bindStage=1; // no source: indexes in sequence.
bool writes(Kind kind){return kind==Kind::Write || kind==Kind::WriteSlot || kind==Kind::Mask || kind==Kind::MaskSlot;}
}
bool Guard::record(Role role,Record& out) const
{for(unsigned i=0;i<arena_.count();++i)if(arena_.at(i,out) && out.role==role)return true;return false;}
bool Guard::inputs()
{
    // The run data, from the owned ledger only (the Runner gets its copy from the stage).
    if(known_)return true;
    Record r;
    if(!record(Role::ChanInstance,r))return false;
    slots_[Instance]=r.physical.value;
    if(!record(Role::Runlist,r))return false;
    slots_[Runlist]=r.physical.value;
    if(!record(Role::DebugWrite,r))return false;
    slots_[MmuWrite]=r.physical.value; // fb/gf100.c:58-59 mmu_wr.
    if(!record(Role::DebugRead,r))return false;
    slots_[MmuRead]=r.physical.value; // fb/gf100.c:53-54 mmu_rd.
    for(unsigned i=0;i<regionCount;++i) {
        const auto role=Role(regions[i].role);
        if(role==Role::GrPagePool)slots_[PagePool]=regions[i].va;
        if(role==Role::GrBundle)slots_[Bundle]=regions[i].va;
        if(role==Role::GrAttrib)slots_[Attrib]=regions[i].va;
    }
    known_=true;return true;
}
bool Guard::next(unsigned& stage,unsigned& index) const
{
    for(;stage<stages;++stage,index=0)
        for(;index<sequence[stage]->count;++index)
            if(writes(sequence[stage]->ops[index].kind))return true;
    return false;
}
bool Guard::matches(const Op& op,uint32_t reg,uint32_t value) const
{
    if(op.addr!=reg)return false;
    switch(op.kind) {
    case Kind::Write:return value==op.a;
    case Kind::WriteSlot:return op.slot<maxSlots && value==((uint32_t(slots_[op.slot]>>op.shift)&op.a)|op.b);
    case Kind::Mask:return pendingReg_==reg && value==((pendingOld_&~op.a)|op.b);
    case Kind::MaskSlot:return op.slot<maxSlots && pendingReg_==reg && value==((pendingOld_&~op.a)|uint32_t(slots_[op.slot]));
    default:return false;
    }
}
void Guard::observed(uint32_t reg,uint32_t value)
{
    pendingReg_=reg;pendingOld_=value;
    if(reg==0x100c80 && (value&0x00008000))vmmQueued_=true; // mmu/vmmgf100.c:224 queued.
    // A Read op between the cursor and the next writing op takes this value.
    unsigned stage=stage_,index=index_;
    for(;stage<stages;++stage,index=0)
        for(;index<sequence[stage]->count;++index) {
            const Op& op=sequence[stage]->ops[index];
            if(writes(op.kind))return;
            if(op.kind==Kind::Read && op.addr==reg && op.slot<maxSlots)slots_[op.slot]=value;
        }
}
bool Guard::special(uint32_t reg,uint32_t value)
{
    // Writes of the stage and of the Mapper that are not ops: the two TLB
    // invalidations and the owned BAR1 context enable and disable (as S1).
    Record r;
    if(reg==0x100cb8) { // mmu/vmmgf100.c:216 page directory to invalidate.
        const Role role=invalidations_==0?Role::ChanDirectory:Role::Directory;
        return invalidations_<2 && (policy_.invalidateStatus()&0x00ff0000) && record(role,r) // mmu/vmmgf100.c:199.
            && value==uint32_t((r.physical.value>>12)<<4);
    }
    if(reg==0x100cbc) { // mmu/vmmgf100.c:221,230-233: PAGE_ALL, and HUB_ONLY for the BAR table.
        if(invalidations_>=2 || value!=(invalidations_==0?0x80000001u:0x80000005u))return false; // mmu/vmmgf100.c:221,230-233.
        ++invalidations_;vmmQueued_=false;return true;
    }
    if(reg==0x001704) { // bar/gf100.c:46-58 owned BAR1 context only.
        const auto context=policy_.barContext();
        if(!context)return false;
        if(value==context && exposeStep_==0 && invalidations_==2 && vmmQueued_){exposeStep_=1;return true;}
        if(value==(context&0x7fffffff) && exposeStep_==1 && closeStep_==0){closeStep_=1;return true;} // bar/gf100.c:46-49.
    }
    return false;
}
bool Guard::write(uint32_t reg,uint32_t value)
{
    if(!inputs())return false;
    if(reg==0x100cb8 || reg==0x100cbc || reg==0x001704)return special(reg,value); // mmu/vmmgf100.c:216,221; bar/gf100.c:46-58.
    if(exposeStep_!=1 || closeStep_)return false; // Program writes only while the owned BAR1 context is enabled.
    unsigned stage=stage_,index=index_;
    if(next(stage,index) && matches(sequence[stage]->ops[index],reg,value)) {
        const Op& op=sequence[stage]->ops[index];
        if(op.kind==Kind::Mask && op.slot<maxSlots)slots_[op.slot]=pendingOld_;
        stage_=stage;index_=index+1;return true;
    }
    // Teardown after a failure: from any point after the first bind write. The
    // attach and teardown stages begin with the same three ops (stop, preempt).
    if(stage_<bindStage || (stage_==bindStage && index_<3))return false;
    unsigned t=teardownStage,at=(stage_==attachStage && index_<=3)?index_:0;
    if(stage_==teardownStage)return false;
    if(next(t,at) && t==teardownStage && matches(sequence[t]->ops[at],reg,value)){stage_=t;index_=at+1;return true;}
    return false;
}
bool Guard::read(uint32_t reg) const
{
    if((reg&3))return false;
    if(reg>=0x400000 && reg<0x528000)return true; // engine/gr/gf100.h:40-45 PGRAPH, 5 GPC units.
    if(reg==0x000200 || reg==0x000204 || reg==0x002a04 || reg==0x002634 || reg==0x002640)return true; // mc/nv04.c:120; fifo/gk104.c:206,739-740; fifo/gf100.c:372.
    if(reg>=0x002390 && reg<0x0023b0)return true; // fifo/gk104.c:392.
    if(reg>=0x002284 && reg<0x002284+16*8 && (reg-0x002284)%8==0)return true; // fifo/gk104.c:426.
    if(reg==0x04013c || reg==0x040108 || reg==0x040148)return true; // fifo/gf100.c:357-358; fifo/gk104.c:378, PBDMA 0.
    if(reg==0x800000+chid*8 || reg==0x800004+chid*8)return true; // fifo/gk104.c:44-77.
    if(reg==0x10a78c || reg==0x0206b4 || (reg>=0x020520 && reg<=0x020530))return true; // pmu/gk110.c:38-80.
    if(reg==0x17e91c || reg==0x17e920 || reg==0x17ea44)return true; // engine/gr/ctxgk104.c:867-868; ltc/gf100.c:59.
    return reg==0x100800 || reg==0x120074; // engine/gr/gf100.c:2285; engine/gr/gk104.c:409.
}
bool Guard::data(const Record& r,uint64_t offset,uint32_t value)
{
    // Owned records only (the Policy resolved the address in the ledger).
    if(r.role==Role::SmallTable) { // BAR1 table entry 0 -> USERD page, by the Mapper, exact value.
        Record userd;uint64_t entry;
        return r.referenced && offset<8 && invalidations_==1 && record(Role::Userd,userd)
            && memstage::channel::userdPte(userd.physical.value,entry) && value==uint32_t(entry>>((offset%8)*8));
    }
    const bool channel=r.role>=Role::ChanDirectory && r.role<=Role::Runlist;
    const bool compute=r.role>=Role::GrText && r.role<=Role::GrMmioList;
    if(!channel && !compute)return false;
    if(!r.referenced)return stage_==0 && index_==0; // Images: before the first program write.
    // Later writes into referenced records: the context pointer words of the instance
    // block (fifo/gk104.c:134-170) and the two list words of the context image (engine/gr/gf100.c:336-338).
    if(r.role==Role::ChanInstance)return offset>=0x210 && offset<0x218; // fifo/gk104.c:138.
    if(r.role==Role::GrContext)return offset>=0x80000 && offset<0x80008; // engine/gr/ctxgf100.c:1436; engine/gr/gf100.c:337-338.
    return false;
}
bool Guard::barRead(uint64_t offset) const
{return exposeStep_==1 && !closeStep_ && (offset==memstage::channel::gpGet || offset==memstage::channel::gpPut);}
bool Guard::barWrite(uint64_t offset,uint32_t value)
{
    // nouveau_dma.c:92 GP_PUT, once, after the context was attached and before teardown.
    if(put_ || exposeStep_!=1 || closeStep_ || offset!=memstage::channel::gpPut || value!=1)return false;
    if(stage_!=attachStage || index_!=attach.count)return false;
    put_=true;return true;
}
}
