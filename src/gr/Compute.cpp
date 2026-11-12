// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "gr/Compute.h"
#include "memstage/Tables.h"
namespace k40::gr {
using namespace memory::vram;
using namespace memstage;
using MemError=memstage::Error;
using memstage::channel::gpGet;
using memstage::channel::gpPut;
namespace {
constexpr Role channelRoles[7]={Role::ChanDirectory,Role::ChanSmall,Role::ChanInstance,Role::Userd,Role::Gpfifo,Role::Push,Role::Runlist}; // no source: software role order, as memstage/Channel.cpp.
constexpr uint64_t reserved=0x80000; // engine/gr/ctxgf100.c:1436 CB_RESERVED.
constexpr uint64_t budgetUs=120000000; // no source: software budget of the whole stage, microseconds.
constexpr uint64_t waitUs=2000000; // no source: 2 s progress bounds, as memstage/Channel.cpp.
// One mapped extent of the channel address space.
struct Extent {uint64_t va,physical,bytes;bool writable;};
// The small-page table of the channel from its first entry: 8 bytes for each
// 4096-byte page (mmu/vmmgk104.c:39-43), read-only unless the GPU writes the record.
class TableWords final:public WordSource {
public:
    TableWords(const Extent* extents,unsigned count,uint64_t base):extents_(extents),count_(count),base_(base){}
    uint32_t at(uint32_t index) const override {
        const uint64_t va=base_+uint64_t(index/2)*4096;
        for(unsigned i=0;i<count_;++i)if(va>=extents_[i].va && va-extents_[i].va<extents_[i].bytes) {
            uint64_t entry=0;const uint64_t page=extents_[i].physical+(va-extents_[i].va);
            const bool ok=extents_[i].writable?channel::userdPte(page,entry):tables::pte({page},entry);
            return ok?uint32_t(entry>>((index&1)*32)):0;
        }
        return 0;
    }
private:const Extent* extents_;unsigned count_;uint64_t base_;
};
class ArrayWords final:public WordSource {
public:
    ArrayWords(const uint32_t* words):words_(words){}
    uint32_t at(uint32_t index) const override{return words_[index];}
private:const uint32_t* words_;
};
class PairWords final:public WordSource { // One 8-byte word.
public:
    explicit PairWords(uint64_t value):value_(value){}
    uint32_t at(uint32_t index) const override{return uint32_t(value_>>((index&1)*32));}
private:uint64_t value_;
};
class InputWords final:public WordSource { // tools/gr/launch.py input_word().
public:uint32_t at(uint32_t index) const override{return inputMultiplier*(index+1);}
};
class PatchWords final:public WordSource { // engine/gr/gf100.c:469-479 address and value pairs.
public:
    explicit PatchWords(const Runner& runner):runner_(runner){}
    uint32_t at(uint32_t index) const override{const auto& p=patchList[index/2];return (index&1)?runner_.patchValue(p):p.addr;}
private:const Runner& runner_;
};
}
bool Compute::fail(MemError e)
{
    if(report_.error==MemError::None)report_.error=e;
    journal_.append({phase_,report_.error,uint32_t(report_.step),0,0,last_>=start_?last_-start_:0,Operation::Failure});return false;
}
bool Compute::tick()
{
    if(!io_.active())return fail(MemError::Authority);
    uint64_t t;
    if(!io_.now(t) || t<last_)return fail(MemError::Clock);
    last_=t;
    return t-start_<budgetUs || fail(MemError::Budget);
}
bool Compute::read32(uint32_t addr,uint32_t& value){return io_.read32(addr,value);}
bool Compute::write32(uint32_t addr,uint32_t value){return io_.write32(addr,value);}
bool Compute::now(uint64_t& t){if(!io_.now(t) || t<last_)return false;last_=t;return t-start_<budgetUs;}
bool Compute::delay(uint32_t microseconds)
{
    uint64_t begin,t;
    if(!now(begin))return false;
    for(uint32_t i=0;i<100000000;++i){if(!now(t))return false;if(t-begin>=microseconds)return true;} // no source: software loop bound.
    return false;
}
bool Compute::token(Role role,Token& out) const
{
    Record r;
    for(unsigned i=0;i<arena_.count();++i)if(arena_.at(i,r) && r.role==role){out=r.token;return true;}
    return false;
}
bool Compute::physical(Role role,uint64_t& out) const
{
    Record r;
    for(unsigned i=0;i<arena_.count();++i)if(arena_.at(i,r) && r.role==role){out=r.physical.value;return true;}
    return false;
}
bool Compute::route()
{
    // GR is TOP type 0 (top/gk104.c:78). The program is fixed to the reference run:
    // runlist 0 (mmiotrace line 615175) and engine status 0x002640 (line 616724).
    unsigned matches=0;
    for(unsigned i=0;i<faults_.routeCount();++i) {
        Routing r;if(!faults_.route(i,r))return fail(MemError::Routing);
        if(r.type==0 && r.instance==0) {
            ++matches;
            if(!r.hasRunlist || r.runlist!=0 || !r.hasEngine || r.engine!=0)return fail(MemError::Routing);
        }
    }
    return matches==1 || fail(MemError::Routing);
}
bool Compute::contextPointer()
{
    // fifo/gk104.c:134-170 and engine/gr/ctxgf100.c:1483-1487: channel address of the
    // context image, bit 2 set, in words 0x210 and 0x214 of the instance block.
    Token instance;uint64_t context=0;
    for(unsigned i=0;i<regionCount;++i)if(Role(regions[i].role)==Role::GrContext)context=regions[i].va+reserved;
    if(!context || !token(Role::ChanInstance,instance))return false;
    return upload_.store(instance,0x210,2,PairWords(context|4),true); // fifo/gk104.c:138,161-167.
}
bool Compute::hook(uint32_t number)
{
    if(number==contextPointerHook)return contextPointer();
    if(number!=attachHook)return false;
    // The image now holds the golden context. Its first two words get the count and
    // the address of the register list of this channel (engine/gr/gf100.c:336-338).
    Token context;uint64_t list=0;
    for(unsigned i=0;i<regionCount;++i)if(Role(regions[i].role)==Role::GrMmioList)list=regions[i].va;
    if(!list || !token(Role::GrContext,context))return false;
    return upload_.store(context,reserved,2,PairWords(uint64_t(patchCount)|(uint64_t(uint32_t(list>>8))<<32)),true) // engine/gr/gf100.c:337-338.
        && contextPointer();
}
bool Compute::memory()
{
    phase(Phase::ChannelMemory);
    Token chan[7],region[32];
    if(regionCount>32)return fail(MemError::Bounds);
    for(unsigned i=0;i<7;++i)
        if(!arena_.allocate(channelRoles[i],Arena::requiredBytes(channelRoles[i]),4096,chan[i]))return fail(MemError::Bounds); // mmu/vmmgk104.c:41-42 alignment.
    for(unsigned i=0;i<regionCount;++i) {
        const auto role=Role(regions[i].role);
        if(regions[i].bytes!=Arena::requiredBytes(role) || (regions[i].va&4095)
            || !arena_.allocate(role,regions[i].bytes,4096,region[i]))return fail(MemError::Bounds); // mmu/vmmgk104.c:41-42 alignment.
    }
    if(!channel::resolve(arena_,addresses_) || addresses_.copy)return fail(MemError::Bounds);
    for(unsigned i=0;i<7;++i)if(!upload_.zero(chan[i]))return fail(upload_.error());
    for(unsigned i=0;i<regionCount;++i)if(regions[i].zero && !upload_.zero(region[i]))return fail(upload_.error());
    // Channel address space: GPFIFO and push pages as S1, then every record.
    Extent extents[34];unsigned count=0;uint64_t end=channel::pushVa+4096;
    extents[count++]={channel::gpfifoVa,addresses_.gpfifo,4096,false};
    extents[count++]={channel::pushVa,addresses_.push,4096,false};
    for(unsigned i=0;i<regionCount;++i) {
        Record r;if(!arena_.describe(region[i],r))return fail(MemError::Bounds);
        extents[count++]={regions[i].va,r.physical.value,regions[i].bytes,regions[i].writable};
        if(regions[i].va+regions[i].bytes>end)end=regions[i].va+regions[i].bytes;
        if(regions[i].va<channel::gpfifoVa || (regions[i].va>>27)!=(channel::gpfifoVa>>27))return fail(MemError::Bounds); // mmu/vmmgk104.c:39-43 one table.
    }
    if(((end-1)>>27)!=(channel::gpfifoVa>>27))return fail(MemError::Bounds); // mmu/vmmgk104.c:39-43.
    uint64_t pde=0;
    if(!tables::smallDirectory({addresses_.small},pde))return fail(MemError::Bounds);
    const uint32_t first=uint32_t((channel::gpfifoVa>>12)&32767); // mmu/vmmgk104.c:39-43 table index.
    if(!upload_.store(chan[0],uint32_t(channel::gpfifoVa>>27)*8,2,PairWords(pde)) // mmu/vmmgk104.c:39-43 directory index.
        || !upload_.store(chan[1],first*8,uint32_t((end-channel::gpfifoVa)/4096)*2,TableWords(extents,count,channel::gpfifoVa)))return fail(upload_.error());
    // Instance block: the RAMFC and address-space words of S1 (memstage/ChannelImage.cpp).
    channel::Word words[16];const auto n=channel::image(Role::ChanInstance,addresses_,words,16);
    if(!n || n>16)return fail(MemError::Bounds);
    for(unsigned w=0;w<n;++w)if(!upload_.store(chan[2],words[w].offset,2,PairWords(words[w].value)))return fail(upload_.error());
    // One GPFIFO entry for the whole push buffer (nouveau_dma.c:83-84), and the runlist entry.
    if(!upload_.store(chan[4],0,2,PairWords((channel::pushVa&0xffffffff)|((uint64_t(channel::pushVa>>32)|(uint64_t(pushBytes)<<8))<<32))) // nouveau_dma.c:83-84.
        || !upload_.store(chan[6],0,2,PairWords(chid)))return fail(upload_.error()); // fifo/gk104.c:454-455.
    // The run data of the program, then the constant images and the register list.
    uint64_t write=0,readPage=0;
    if(!physical(Role::DebugWrite,write) || !physical(Role::DebugRead,readPage))return fail(MemError::Bounds);
    Runner* const runners[2]={&runner_,&closer_};
    for(Runner* r:runners) {
        r->input(Instance,addresses_.instance);r->input(Runlist,addresses_.runlist);
        r->input(MmuWrite,write);r->input(MmuRead,readPage); // fb/gf100.c:53-59.
        for(unsigned i=0;i<regionCount;++i) {
            if(Role(regions[i].role)==Role::GrPagePool)r->input(PagePool,regions[i].va);
            if(Role(regions[i].role)==Role::GrBundle)r->input(Bundle,regions[i].va);
            if(Role(regions[i].role)==Role::GrAttrib)r->input(Attrib,regions[i].va);
        }
    }
    for(unsigned b=0;b<blobCount;++b) {
        Token target;
        if(!token(Role(blobs[b].role),target) || !upload_.store(target,blobs[b].offset,blobs[b].count,ArrayWords(blobs[b].words)))
            return fail(upload_.error()==MemError::None?MemError::Bounds:upload_.error());
    }
    Token input,list;
    if(!token(Role::GrInput,input) || !token(Role::GrMmioList,list)
        || !upload_.store(input,0,elements,InputWords()) || !upload_.store(list,0,patchCount*2,PatchWords(runner_)))
        return fail(upload_.error()==MemError::None?MemError::Bounds:upload_.error());
    for(unsigned i=0;i<7;++i)if(!arena_.reference(chan[i]))return fail(MemError::Bounds);
    for(unsigned i=0;i<regionCount;++i)if(regions[i].zero && !arena_.reference(region[i]))return fail(MemError::Bounds);
    return true;
}
bool Compute::invalidate()
{
    // mmu/vmmgf100.c:196-233: the channel page directory, PAGE_ALL (as memstage/Channel.cpp).
    LockGuard lock(io_,Lock::Mmu);
    if(!lock.held())return fail(MemError::Budget);
    const auto begin=last_;uint32_t status;
    for(unsigned i=0;;++i) {
        if(i>=100000 || !tick() || !io_.read32(0x100c80,status))return fail(MemError::Invalidate); // mmu/vmmgf100.c:199.
        if(status&0x00ff0000)break; // mmu/vmmgf100.c:199 free slot.
        if(last_-begin>=waitUs)return fail(MemError::Invalidate);
    }
    if(!io_.write32(0x100cb8,uint32_t((addresses_.directory>>12)<<4)) // mmu/vmmgf100.c:216.
        || !io_.write32(0x100cbc,0x80000001))return fail(MemError::Invalidate); // mmu/vmmgf100.c:221,230.
    for(unsigned i=0;;++i) {
        if(i>=100000 || !tick() || !io_.read32(0x100c80,status))return fail(MemError::Invalidate); // mmu/vmmgf100.c:224.
        if(status&0x00008000)return true; // mmu/vmmgf100.c:224 queued.
        if(last_-begin>=waitUs)return fail(MemError::Invalidate);
    }
}
bool Compute::stage(const Stage& ops,Step step,unsigned number)
{
    report_.step=step;
    if(!tick())return false;
    LockGuard lock(io_,Lock::Mmu);
    if(!lock.held())return fail(MemError::Budget);
    const auto begin=last_;
    const bool ok=runner_.run(ops);
    report_.reads=runner_.reads();report_.writes=runner_.writes();report_.ops=runner_.done();
    if(!tick() && ok)return false;
    if(!journal_.append({phase_,MemError::None,number,runner_.done(),runner_.reads(),last_-begin,Operation::Stage,0,uint8_t(ok?1:0)}))return fail(MemError::Overflow);
    if(!ok){report_.runner=runner_.failure();return fail(MemError::Write);}
    return true;
}
bool Compute::submit()
{
    report_.step=Step::Submit;phase(Phase::ChannelSubmit);
    LockGuard lock(io_,Lock::Mmu);
    if(!lock.held())return fail(MemError::Budget);
    uint32_t get=0,put=0;
    if(!io_.loadFence() || !io_.barRead32(gpGet,get) || !io_.barRead32(gpPut,put) || get || put)return fail(MemError::Dirty);
    if(!io_.storeFence() || !io_.barWrite32(gpPut,1))return fail(MemError::Write); // nouveau_dma.c:88-92.
    report_.submitted=true;
    if(!journal_.append({phase_,MemError::None,gpPut,1,0,last_-start_,Operation::Write,uint8_t(Role::Userd),1}))return fail(MemError::Overflow);
    const auto begin=last_;
    for(unsigned i=0;i<20000000;++i) { // no source: software poll-count bound above the time bound.
        if(!tick() || !io_.loadFence() || !io_.barRead32(gpGet,report_.getAfter))return fail(MemError::Read);
        if(!tick())return false;
        report_.polls=i+1;report_.progressUs=last_-begin;
        if(report_.getAfter==1 || report_.progressUs>=waitUs)break;
    }
    if(!io_.barRead32(gpPut,report_.putAfter))return fail(MemError::Read);
    report_.consumed=report_.getAfter==1 && report_.putAfter==1;
    return journal_.append({phase_,MemError::None,gpGet,report_.getAfter,report_.polls,report_.progressUs,Operation::Poll,uint8_t(Role::Userd),1}) || fail(MemError::Overflow);
}
bool Compute::result()
{
    // The entry is fetched; the job ends later. Read the last output element
    // until it has its value or the bound passes, then compare every element.
    report_.step=Step::Result;
    Token output;
    if(!report_.consumed)return true;
    if(!token(Role::GrOutput,output))return fail(MemError::Bounds);
    const auto begin=last_;uint32_t value=0;
    for(unsigned i=0;i<100000;++i) { // no source: software poll-count bound.
        if(!tick() || !upload_.load(output,(elements-1)*4,1,&value))return fail(upload_.error()==MemError::None?MemError::Read:upload_.error());
        report_.resultPolls=i+1;report_.resultUs=last_-begin;
        if(value==inputMultiplier*elements+1 || report_.resultUs>=waitUs)break;
        if(!delay(1000))return fail(MemError::Clock); // no source: 1 ms between result reads.
    }
    for(uint32_t at=0;at<elements;at+=64) {
        uint32_t block[64];
        if(!upload_.load(output,at*4,64,block))return fail(upload_.error()==MemError::None?MemError::Read:upload_.error());
        for(uint32_t k=0;k<64;++k)if(block[k]!=inputMultiplier*(at+k+1)+1) {
            if(!report_.wrong){report_.firstWrong=at+k;report_.firstValue=block[k];}
            ++report_.wrong;
        }
    }
    report_.computed=report_.wrong==0;
    return true;
}
bool Compute::snapshot()
{
    report_.step=Step::Status;
    LockGuard lock(io_,Lock::Mmu);
    if(!lock.held())return fail(MemError::Budget);
    const uint32_t state=0x800004+chid*8; // fifo/gk104.c:44-77.
    // fb/gf100.c:37; fifo/gk104.c:658; fifo/gf100.c:723,358; fifo/gk104.c:378; PBDMA 0.
    return io_.read32(0x000100,report_.mc) && io_.read32(0x002100,report_.fifoIntr) && io_.read32(0x00259c,report_.mmuPending) // fb/gf100.c:37; fifo/gk104.c:658; fifo/gf100.c:723.
        && io_.read32(0x040108,report_.pbdmaIntr) && io_.read32(0x040148,report_.pbdmaHce) && io_.read32(state,report_.state) // fifo/gf100.c:358; fifo/gk104.c:378.
        && io_.read32(0x400100,report_.grIntr) && io_.read32(0x400108,report_.grTrap) // engine/gr/gf100.c:1414,1690 status only.
        && io_.read32(0x409c18,report_.fecsIntr) && io_.read32(0x002640,report_.engineStatus); // engine/gr/gf100.c:1570; fifo/gk104.c:206.
}
bool Compute::teardown()
{
    report_.step=Step::Teardown;phase(Phase::ChannelClosed);
    bool ok=true;
    if(report_.bound) {
        LockGuard lock(io_,Lock::Mmu);
        if(!lock.held())return fail(MemError::Budget);
        ok=closer_.run(gr::teardown);
        if(!ok){report_.closing=closer_.failure();fail(MemError::Preempt);}
    }
    if(exposed_) {
        if(!mapper_.closeUserd(Phase::ChannelClosed)){fail(mapper_.error()==MemError::None?MemError::Order:mapper_.error());ok=false;}
        else exposed_=false;
    }
    report_.closed=ok;return ok;
}
bool Compute::run()
{
    if(attempted_)return fail(MemError::Order);
    attempted_=true;
    if(!io_.now(start_))return fail(MemError::Clock);
    last_=start_;phase(Phase::ChannelBase);report_.step=Step::Route;
    if(!faults_.capture(Phase::ChannelBase,epoch_))return fail(faults_.error());
    report_.step=Step::Memory;
    if(!route() || !memory())return false;
    report_.step=Step::Tables;
    if(!invalidate())return false;
    report_.step=Step::Expose;phase(Phase::ChannelBar);
    Token userd;
    if(!token(Role::Userd,userd) || !mapper_.exposeUserd(userd,Phase::ChannelBar))return fail(mapper_.error()==MemError::None?MemError::Bounds:mapper_.error());
    exposed_=true;
    phase(Phase::ChannelFifo);
    bool ok=stage(gr::fifo,Step::Fifo,0);
    if(ok){phase(Phase::ChannelBound);report_.bound=true;ok=stage(gr::bind,Step::Bind,1);}
    if(ok)ok=stage(gr::gating,Step::Gating,2);
    if(ok){ok=stage(gr::start,Step::Start,3);report_.started=ok;}
    if(ok){ok=stage(gr::golden,Step::Golden,4);report_.golden=ok;}
    if(ok) {
        Token context;
        ok=token(Role::GrContext,context) && upload_.load(context,reserved,8,report_.image);
        if(!ok)fail(upload_.error()==MemError::None?MemError::Read:upload_.error());
    }
    if(ok){ok=stage(gr::attach,Step::Attach,5);report_.attached=ok;}
    if(ok && launch_)ok=submit() && result();
    const bool sampled=snapshot();
    const bool closed=teardown();
    uint64_t end;
    if(io_.now(end) && end>=start_)report_.totalUs=end-start_;
    if(!ok || !sampled || !closed)return false;
    report_.step=Step::Done;
    // No MMU fault, no PBDMA interrupt, only the runlist and non-stall FIFO events
    // (fifo/gk104.c:654-718), no GR interrupt or trap, no FECS interrupt (engine/gr/gf100.c:1414,1570).
    const bool clean=!report_.mmuPending && !report_.pbdmaIntr && !report_.pbdmaHce && !(report_.fifoIntr&0x3fffffff) // fifo/gk104.c:654-718.
        && !report_.grIntr && !report_.grTrap && !report_.fecsIntr;
    return report_.golden && report_.attached && clean && (!launch_ || (report_.consumed && report_.computed));
}
}
