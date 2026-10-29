// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#ifdef _KERNEL_MODE
#include "memnative/NativeOwner.h"
#include <cstring>
#include <new>
namespace k40::memnative {
using namespace memory::vram;
NativeOwner::NativeOwner(const uint8_t key[32],const uint8_t nonce[32],const uint8_t plan[32],const uint8_t challenge[16],uint64_t epoch,uint64_t vram)
    :faults_(io_,journal_,epoch),policy_(arena_,faults_),upload_(io_,faults_,journal_,arena_),mapper_(io_,faults_,journal_,arena_,upload_,epoch)
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
{return experiment_ && experiment_->run();}
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
        passed?"PASS BAR1_SCOPED":"FAIL",unsigned(faults_.error()),unsigned(upload_.error()),unsigned(mapper_.error()),
        unsigned(mapper_.closure()),arena_.count(),journal_.overflow());return passed;
}
}
#endif
