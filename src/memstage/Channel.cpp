// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memstage/Channel.h"
namespace k40::memstage {
using namespace memory::vram;
using namespace channel;
namespace {
constexpr uint32_t chanReg=0x800000+chid*8,chanState=0x800004+chid*8; // fifo/gk104.c:44-77.
// no source: software allocation order of the channel roles.
constexpr Role roles[7]={Role::ChanDirectory,Role::ChanSmall,Role::ChanInstance,Role::Userd,Role::Gpfifo,Role::Push,Role::Runlist};
}
bool Channel::fail(Error e,uint32_t offset,uint32_t value)
{
    if(error_==Error::None)error_=e;
    if(report_.progress==Progress::NotRun)report_.progress=Progress::Failed;
    journal_.append({phase_,error_,offset,value,0,last_>=start_?last_-start_:0,Operation::Failure});return false;
}
bool Channel::tick()
{
    // After a bind, teardown must still run when an earlier step failed.
    if((error_!=Error::None && !closing_) || !faults_.healthy() || !arena_.healthy() || journal_.overflow())return fail(Error::Dirty);
    if(!io_.active())return fail(Error::Authority);
    uint64_t now;
    if(!io_.now(now) || now<last_)return fail(Error::Clock);
    last_=now;
    if(now-start_>=10000000)return fail(Error::Budget); // no source: channel-stage software budget, microseconds.
    return true;
}
bool Channel::read(uint32_t offset,uint32_t& value)
{
    value=0;
    if(!tick())return false;
    if(!io_.read32(offset,value))return fail(Error::Read,offset);
    if(!journal_.append({phase_,Error::None,offset,value,0,last_-start_,Operation::Read}))return fail(Error::Overflow);
    return tick();
}
bool Channel::write(uint32_t offset,uint32_t value)
{
    if(!tick())return false;
    if(!io_.write32(offset,value))return fail(Error::Write,offset,value);
    if(!journal_.append({phase_,Error::None,offset,value,0,last_-start_,Operation::Write}))return fail(Error::Overflow);
    return tick();
}
bool Channel::waitClear(uint32_t reg,uint32_t mask,Error error)
{
    const auto start=last_;
    for(unsigned i=0;i<100000;++i) { // no source: software poll-count bound.
        uint32_t value;
        if(!tick() || !io_.read32(reg,value))return fail(Error::Read,reg);
        if(!tick())return false;
        if(!(value&mask))
            return journal_.append({phase_,Error::None,reg,value,i+1,last_-start,Operation::Poll}) || fail(Error::Overflow);
        if(last_-start>=2000000)return fail(error,reg,value); // fifo/gk104.c:426, fifo/gf100.c:372 polls; no source: 2 s bound.
    }
    return fail(error,reg);
}
bool Channel::route()
{
    // CE0 is TOP type 1 (top/gk104.c:79). A CE channel needs no engine context
    // (fifo/gk104.c:281-287). Batch-1 TOP capture: CE0 on runlist 4.
    unsigned matches=0;
    for(unsigned i=0;i<faults_.routeCount();++i) {
        Routing r;if(!faults_.route(i,r))return fail(Error::Routing);
        if(r.type==1 && r.instance==0 && r.hasRunlist){report_.runlist=r.runlist;++matches;}
    }
    if(matches!=1 || report_.runlist>15)return fail(Error::Routing); // fifo/gk104.c:77 four-bit field.
    return true;
}
bool Channel::memory()
{
    phase(Phase::ChannelMemory);
    for(unsigned i=0;i<7;++i)
        if(!arena_.allocate(roles[i],Arena::requiredBytes(roles[i]),4096,tokens_[i]))return fail(Error::Bounds); // vmmgk104.c:41-42 alignment.
    if(!resolve(arena_,addresses_))return fail(Error::Bounds);
    for(auto token:tokens_)if(!upload_.zero(token))return fail(upload_.error());
    for(unsigned i=0;i<7;++i) {
        Word words[16];const auto n=image(roles[i],addresses_,words,16);
        if(n>16 || (!n && roles[i]!=Role::Userd))return fail(Error::Bounds);
        for(unsigned w=0;w<n;++w)if(!upload_.patch(tokens_[i],words[w].offset,words[w].value))return fail(upload_.error());
    }
    for(auto token:tokens_)if(!arena_.reference(token))return fail(Error::Bounds);
    return true;
}
bool Channel::invalidate()
{
    // vmmgf100.c:196-233: this PDB, PAGE_ALL; HUB_ONLY only for BAR-referenced VMMs.
    LockGuard lock(io_,Lock::Mmu);
    if(!lock.held())return fail(Error::Budget);
    const auto start=last_;
    for(unsigned i=0;;++i) {
        uint32_t status;
        if(i>=100000 || !read(0x100c80,status))return fail(Error::Invalidate); // vmmgf100.c:199.
        if(status&0x00ff0000)break; // mmu/vmmgf100.c:199 free slot.
        if(last_-start>=2000000)return fail(Error::Invalidate); // vmmgf100.c:198 2000 ms.
    }
    if(!write(0x100cb8,uint32_t((addresses_.directory>>12)<<4))  // vmmgf100.c:216 VRAM target 0.
        || !write(0x100cbc,0x80000001))return false; // vmmgf100.c:221,230 PAGE_ALL.
    for(unsigned i=0;;++i) {
        uint32_t status;
        if(i>=100000 || !read(0x100c80,status))return fail(Error::Invalidate); // vmmgf100.c:224.
        if(status&0x00008000)return true; // mmu/vmmgf100.c:224 queued.
        if(last_-start>=2000000)return fail(Error::Invalidate); // vmmgf100.c:221 2000 ms.
    }
}
bool Channel::fifo()
{
    phase(Phase::ChannelFifo);
    LockGuard lock(io_,Lock::Mmu);
    if(!lock.held())return fail(Error::Budget);
    uint32_t value,mask;
    // fifo/gf100.c:927-934 PBDMA discovery, then fifo/gk104.c:739-740 enable mask.
    if(!read(0x000204,value) || !write(0x000204,0xffffffff) || !read(0x000204,mask))return false;
    if(!mask || mask>0xff)return fail(Error::Routing,0x000204,mask); // no source: software unit bound.
    if(!write(0x000204,mask))return false; // fifo/gk104.c:739.
    report_.pbdmaMask=mask;unsigned matches=0;
    for(unsigned p=0;p<8;++p)if(mask&(1u<<p)) {
        uint32_t runm;
        if(!read(0x002390+p*4,runm))return false; // fifo/gk104.c:392 runlists served by this PBDMA.
        if(runm&(1u<<report_.runlist)){report_.pbdma=p;report_.runm=runm;++matches;}
    }
    if(matches!=1)return fail(Error::Routing,0x002390,matches); // fifo/gk104.c:770-777 runlist queue association.
    if(!read(0x002a04,value) || !write(0x002a04,value|0xbfffffff))return false; // fifo/gk104.c:740.
    const auto control=0x04013c+report_.pbdma*0x2000; // fifo/gf100.c:357.
    if(!read(control,value) || !write(control,value&~0x10000100u))return false; // fifo/gf100.c:357.
    return write(0x002254,0x10000000); // fifo/gk104.c:749 USERD at BAR1 VA 0, as trace line 560992.
}
bool Channel::bind()
{
    phase(Phase::ChannelBound);
    LockGuard lock(io_,Lock::Mmu);
    if(!lock.held())return fail(Error::Budget);
    uint32_t inst,state;
    if(!read(chanReg,inst) || !read(chanState,state))return false;
    if(inst || state)return fail(Error::Dirty,chanState,state); // trace 562288: inactive baseline read 0.
    report_.bound=true; // From here on, teardown is mandatory.
    if(!write(chanState,(state&~0x000f0000u)|(report_.runlist<<16)) // fifo/gk104.c:77.
        || !write(chanReg,0x80000000|uint32_t(addresses_.instance>>12)) // fifo/gk104.c:68.
        || !read(chanState,state) || !write(chanState,state|0x400) // fifo/gk104.c:52 start.
        || !write(0x002270,uint32_t(addresses_.runlist>>12)) // fifo/gk104.c:446 VRAM target 0.
        || !write(0x002274,(report_.runlist<<20)|1))return false; // fifo/gk104.c:447 one entry.
    return waitClear(0x002284+report_.runlist*8,0x00100000,Error::Runlist); // fifo/gk104.c:426.
}
bool Channel::submit()
{
    phase(Phase::ChannelSubmit);
    LockGuard lock(io_,Lock::Mmu);
    if(!lock.held())return fail(Error::Budget);
    if(!io_.loadFence() || !io_.barRead32(gpGet,report_.getBefore) || !io_.barRead32(gpPut,report_.putBefore))return fail(Error::Read,gpGet);
    if(report_.getBefore || report_.putBefore)return fail(Error::Dirty,gpGet,report_.getBefore); // empty baseline.
    if(!io_.storeFence() || !io_.barWrite32(gpPut,1))return fail(Error::Write,gpPut,1); // nouveau_dma.c:88-92 ordered GP_PUT.
    if(!journal_.append({phase_,Error::None,gpPut,1,0,last_-start_,Operation::Write,uint8_t(Role::Userd),1}))return fail(Error::Overflow);
    const auto start=last_;
    report_.progress=Progress::Stalled;
    for(unsigned i=0;i<100000;++i) { // no source: software poll-count bound.
        if(!tick() || !io_.loadFence() || !io_.barRead32(gpGet,report_.getAfter))return fail(Error::Read,gpGet);
        if(!tick())return false;
        report_.polls=i+1;report_.progressUs=last_-start;
        if(report_.getAfter==1)break;
        if(report_.progressUs>=2000000)break; // no source: 2 s progress bound; a stall still tears down.
    }
    if(!io_.barRead32(gpPut,report_.putAfter))return fail(Error::Read,gpPut);
    if(!journal_.append({phase_,Error::None,gpGet,report_.getAfter,report_.polls,report_.progressUs,Operation::Poll,uint8_t(Role::Userd),1}))return fail(Error::Overflow);
    if(report_.getAfter==1 && report_.putAfter==1)report_.progress=Progress::Consumed;
    return true;
}
bool Channel::snapshot()
{
    const auto pb=report_.pbdma*0x2000; // fifo/gf100.c:357 PBDMA stride.
    return read(0x000100,report_.mc) && read(0x002100,report_.fifoIntr) && read(0x00259c,report_.mmuPending) // fb/gf100.c:37; fifo/gk104.c:658; fifo/gf100.c:723.
        && read(0x040108+pb,report_.pbdmaIntr) && read(0x040148+pb,report_.pbdmaHce) // fifo/gf100.c:358; fifo/gk104.c:378 status only.
        && read(chanState,report_.state);
}
bool Channel::teardown()
{
    phase(Phase::ChannelClosed);
    {
        LockGuard lock(io_,Lock::Mmu);
        if(!lock.held())return fail(Error::Budget);
        uint32_t state;
        if(!read(chanState,state) || !write(chanState,state|0x800) // fifo/gk104.c:44 stop.
            || !write(0x002634,chid) || !waitClear(0x002634,0x00100000,Error::Preempt) // fifo/gf100.c:43,372.
            || !write(0x002270,uint32_t(addresses_.runlist>>12)) || !write(0x002274,report_.runlist<<20) // fifo/gk104.c:446-447 empty list.
            || !waitClear(0x002284+report_.runlist*8,0x00100000,Error::Runlist) // fifo/gk104.c:426.
            || !write(chanReg,0))return false; // fifo/gk104.c:60 unbind.
    }
    if(!mapper_.closeUserd(Phase::ChannelClosed))return fail(mapper_.error()==Error::None?Error::Order:mapper_.error());
    exposed_=false;report_.closed=true;return true;
}
bool Channel::run()
{
    if(attempted_)return fail(Error::Order);
    attempted_=true;
    if(!io_.now(start_))return fail(Error::Clock);
    last_=start_;phase(Phase::ChannelBase);
    if(!faults_.capture(Phase::ChannelBase,epoch_))return fail(faults_.error());
    if(!route() || !memory() || !invalidate())return false;
    phase(Phase::ChannelBar);
    if(!mapper_.exposeUserd(tokens_[3],Phase::ChannelBar))return fail(mapper_.error());
    exposed_=true;
    bool ok=fifo() && bind() && submit();
    closing_=true;
    const bool sampled=snapshot();
    if(report_.bound)ok=teardown() && ok; // Teardown after any bind, also after a stall.
    else if(exposed_)ok=mapper_.closeUserd(Phase::ChannelClosed) && ok;
    if(!sampled || !ok)return false;
    // S1 predicate: entry consumed, no MMU fault or PBDMA interrupt, only the
    // runlist (bit 30) and non-stall (bit 31) FIFO events (fifo/gk104.c:654-718).
    return report_.progress==Progress::Consumed && report_.closed && !report_.mmuPending
        && !report_.pbdmaIntr && !report_.pbdmaHce && !(report_.fifoIntr&0x3fffffff); // fifo/gk104.c:654-718.
}
}
