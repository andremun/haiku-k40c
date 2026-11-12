// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#ifdef _KERNEL_MODE
#include "memnative/NativeOwner.h"
#include <cstring>
#include <new>
namespace k40::memnative {
using namespace memory::vram;
NativeOwner::NativeOwner(const uint8_t key[32],const uint8_t nonce[32],const uint8_t plan[32],const uint8_t challenge[16],uint64_t epoch,uint64_t vram,unsigned stage)
    :faults_(io_,journal_,epoch),policy_(arena_,faults_),upload_(io_,faults_,journal_,arena_),mapper_(io_,faults_,journal_,arena_,upload_,epoch),
     channel_(io_,faults_,journal_,arena_,upload_,mapper_,epoch,stage==1),stage_(stage),guard_(arena_,policy_),
     compute_(io_,faults_,journal_,arena_,upload_,mapper_,epoch,stage==3)
{
    io_.policy_=&policy_;
    std::memcpy(binding_.key,key,32);std::memcpy(binding_.nonce,nonce,32);std::memcpy(binding_.plan,plan,32);std::memcpy(binding_.challenge,challenge,16);
    binding_.epoch=binding_.owner=epoch;binding_.vram=vram;
    binding_.begin=256*1024+4096;binding_.end=vram-1048576; // ramgf100.c:497-498; no source: extra A7 scratch exclusion.
}
status_t NativeOwner::observeLoad()
{
    if(loads_>=16)return B_BUSY; // no source: bounded harmless client-load observation count.
    ++loads_;dprintf("k40_mem: CLIENT_LOAD n=%u state=%u\n",loads_,failed_?4:session_?unsigned(session_->state()):0);
    return B_OK;
}
status_t NativeOwner::prepare(uint64* lease,uint8_t* request)
{
    if(!lease || !request || opened_)return B_BUSY;
    opened_=true;failed_=true;dprintf("k40_mem: PREPARE_CALL n=1\n");
    module_info* info=nullptr;
    if(get_module(K40_A7_OWNER_NAME,&info)!=B_OK)return B_NO_INIT;
    a7_=reinterpret_cast<k40_a7_module*>(info);
    if(!info->name || std::strcmp(info->name,K40_A7_OWNER_NAME) || !(info->flags&B_KEEP_LOADED) || a7_->abi!=2)return B_BAD_DATA;
    const auto initialized=io_.initialize();if(initialized!=B_OK)return initialized;
    binding_.bar0=io_.bar0();binding_.bar0Bytes=io_.bar0Bytes();binding_.bar1=io_.bar1();binding_.bar1Bytes=io_.bar1Bytes();
    experiment_=new(experimentStorage_) memstage::Experiment(io_,faults_,arena_,upload_,mapper_,binding_.owner,binding_.epoch,binding_.vram,binding_.bar1Bytes);
    session_=new(sessionStorage_) memauth::Session(binding_,*this);
    if(!session_->prepare(request))return B_BAD_DATA;
    failed_=false;*lease=binding_.owner;
    dprintf("k40_mem: PREPARED owner=%llu epoch=%llu bar0=%llx bar1=%llx\n",(unsigned long long)*lease,
        (unsigned long long)binding_.epoch,(unsigned long long)binding_.bar0,(unsigned long long)binding_.bar1);
    return B_OK;
}
status_t NativeOwner::submit(uint64 lease,const uint8_t* grant,size_t bytes)
{
    if(!session_ || failed_ || lease!=binding_.owner)return B_NOT_ALLOWED;
    const bool result=session_->submit(grant,bytes);failed_=!result;
    dprintf("k40_mem: SUBMIT result=%u state=%u\n",result?0:1,unsigned(session_->state()));return result?B_OK:B_ERROR;
}
status_t NativeOwner::detach(uint64 lease)
{
    if(!session_ || lease!=binding_.owner || !session_->detach())return B_BAD_VALUE;
    dprintf("k40_mem: RETAINED owner=%llu state=%u\n",(unsigned long long)lease,unsigned(session_->state()));return B_OK;
}
bool NativeOwner::work()
{
    // The unchanged batch-1 memory/BAR1 gates first, then one channel: S1 (host
    // NOP), or S2 (NOP, then one copy) when the package was built for the copy stage.
    // S3 (stages 2 and 3): the compute stage replaces the CE0 channel, and its
    // guard decides the channel-phase accesses (gr/Guard.h).
    if(!experiment_ || !experiment_->run())return false;
    if(stage_<2)return channel_.run();
    if(stage_>3)return false;
    policy_.extend(&guard_);
    return compute_.run();
}
void NativeOwner::drain()
{
    const auto& probe_=experiment_->probe();const auto probeKnown_=experiment_->known();
    const auto step_=unsigned(experiment_->step());
    dprintf("k40_mem: DISCOVERY step=%u known=%llx parts=%u units=%u disabled=%x\n",step_,(unsigned long long)probeKnown_,probe_.parts,probe_.units,probe_.disabled);
    for(unsigned i=0;i<32;++i)if(probeKnown_&(uint64_t(1)<<(i+3)))dprintf("k40_mem: FBPA unit=%u mib=%u\n",i,probe_.mib[i]);
    dprintf("k40_mem: IO_REJECT kind=%u offset=%x value=%x\n",io_.denialKind(),io_.denialOffset(),io_.denialValue());
    for(unsigned i=0;i<journal_.count();++i) {
        const auto* event=journal_.at(i);
        dprintf("k40_mem: EVENT phase=%u error=%u offset=%x value=%llx polls=%u elapsed=%llu operation=%u role=%u detail=%u\n",unsigned(event->phase),unsigned(event->error),
            event->offset,(unsigned long long)event->value,event->polls,(unsigned long long)event->elapsed,unsigned(event->operation),event->role,event->detail);
    }
    for(unsigned i=0;i<arena_.count();++i) {
        Record r;if(!arena_.at(i,r))continue;
        dprintf("k40_mem: ALLOCATION id=%llu role=%u physical=%llx bytes=%llu generation=%llu staged=%u referenced=%u retained=%u\n",
            (unsigned long long)r.token.id,unsigned(r.role),(unsigned long long)r.physical.value,(unsigned long long)r.bytes,
            (unsigned long long)r.writeGeneration,r.staged,r.referenced,r.retained);
    }
    if(stage_>=2) {
        const auto& g=compute_.report();
        dprintf("k40_mem: GR step=%u error=%u bound=%u started=%u golden=%u attached=%u submitted=%u consumed=%u computed=%u closed=%u\n",
            unsigned(g.step),unsigned(g.error),g.bound,g.started,g.golden,g.attached,g.submitted,g.consumed,g.computed,g.closed);
        dprintf("k40_mem: GR_PROGRAM ops=%u reads=%u writes=%u guard=%u/%u total_us=%llu\n",g.ops,g.reads,g.writes,
            guard_.stage(),guard_.index(),(unsigned long long)g.totalUs);
        dprintf("k40_mem: GR_FAILURE runner=%u index=%u addr=%x value=%x expected=%x closing=%u closing_index=%u\n",unsigned(g.runner.error),
            g.runner.index,g.runner.addr,g.runner.value,g.runner.expected,unsigned(g.closing.error),g.closing.index);
        dprintf("k40_mem: GR_GET after=%u/%u polls=%u us=%llu result_polls=%u result_us=%llu wrong=%u first=%u value=%x\n",g.getAfter,g.putAfter,
            g.polls,(unsigned long long)g.progressUs,g.resultPolls,(unsigned long long)g.resultUs,g.wrong,g.firstWrong,g.firstValue);
        dprintf("k40_mem: GR_STATUS mc=%x fifo=%x mmu=%x pbdma=%x hce=%x state=%x gr=%x trap=%x fecs=%x engine=%x\n",g.mc,g.fifoIntr,
            g.mmuPending,g.pbdmaIntr,g.pbdmaHce,g.state,g.grIntr,g.grTrap,g.fecsIntr,g.engineStatus);
        dprintf("k40_mem: GR_IMAGE %x %x %x %x %x %x %x %x\n",g.image[0],g.image[1],g.image[2],g.image[3],g.image[4],g.image[5],g.image[6],g.image[7]);
    }
    const auto& c=channel_.report();
    dprintf("k40_mem: CHANNEL runlist=%u pbdma=%u mask=%x runm=%x bound=%u closed=%u progress=%u error=%u step=%u\n",
        c.runlist,c.pbdma,c.pbdmaMask,c.runm,c.bound,c.closed,unsigned(c.progress),unsigned(channel_.error()),policy_.channelStep());
    dprintf("k40_mem: CHANNEL_GET before=%u/%u after=%u/%u polls=%u us=%llu\n",c.getBefore,c.putBefore,
        c.getAfter,c.putAfter,c.polls,(unsigned long long)c.progressUs);
    dprintf("k40_mem: CHANNEL_STATUS mc=%x fifo=%x mmu=%x pbdma=%x hce=%x state=%x\n",
        c.mc,c.fifoIntr,c.mmuPending,c.pbdmaIntr,c.pbdmaHce,c.state);
    if(channel_.copy()) {
        dprintf("k40_mem: COPY engine=%u submitted=%u get=%u/%u polls=%u us=%llu copied=%u\n",c.engine,c.copySubmitted,
            c.copyGet,c.copyPut,c.copyPolls,(unsigned long long)c.copyUs,c.copied);
        dprintf("k40_mem: COPY_STATUS engine=%x idle_polls=%u idle_us=%llu ce_intr=%x launcherr=%x\n",c.engineStatus,
            c.idlePolls,(unsigned long long)c.idleUs,c.ceIntr,c.ceLaunchErr);
    }
    dprintf("k40_mem: ROUTES count=%u\n",faults_.routeCount());
    for(unsigned i=0;i<faults_.routeCount();++i) {
        memstage::Routing r;if(!faults_.route(i,r))continue;
        dprintf("k40_mem: ROUTE type=%u instance=%u address=%x fault=%u/%u runlist=%u/%u engine=%u/%u\n",
            r.type,r.instance,r.address,r.hasFault,r.fault,r.hasRunlist,r.runlist,r.hasEngine,r.engine);
    }
}
bool NativeOwner::execute()
{
    io_.activate();const bool passed=work();io_.revoke();
    // No MMIO after revocation, including speculative rollback. The owner and
    // CPU mappings stay resident through guest/VFIO end on every path.
    if(!passed)arena_.fail();
    drain();
    dprintf("k40_mem: %s faults=%u upload=%u mapper=%u closure=%u allocations=%u journal_overflow=%u\n",
        !passed?"FAIL":stage_==3?"PASS S3_COMPUTE":stage_==2?"PASS S3_GOLDEN":stage_==1?"PASS S2_COPY":"PASS S1_CHANNEL_NOP",unsigned(faults_.error()),unsigned(upload_.error()),unsigned(mapper_.error()),
        unsigned(mapper_.closure()),arena_.count(),journal_.overflow());return passed;
}
}
#endif
