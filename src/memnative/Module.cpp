// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#ifdef _KERNEL_MODE
#include "memnative/Module.h"
#include "memnative/NativeOwner.h"
#include "mem_config.h"
#include <new>
extern "C" unsigned int secure_random_value(void); // Random.h:24-31 exported kernel generator.
namespace {
using k40::memnative::NativeOwner;
alignas(NativeOwner) uint8 storage[sizeof(NativeOwner)];NativeOwner* owner=nullptr;
std::atomic_flag gate=ATOMIC_FLAG_INIT;
struct Guard {bool held=!gate.test_and_set();~Guard(){if(held)gate.clear();}};
status_t standard(int32 op,...)
{
    if(op==B_MODULE_UNINIT)return B_NOT_ALLOWED;
    if(op!=B_MODULE_INIT || owner)return B_BAD_VALUE;
    uint8 challenge[16];uint64 epoch=0;
    for(unsigned i=0;i<4;++i){const auto random=secure_random_value();for(unsigned j=0;j<4;++j)challenge[i*4+j]=uint8(random>>(j*8));}
    for(unsigned i=0;i<8;++i)epoch|=uint64(challenge[i])<<(i*8);
    if(!epoch)epoch=1; // no source: nonzero software epoch; PRNG not claimed cryptographic entropy.
    owner=new(storage) NativeOwner(memoryPublicKey,memoryNonce,memoryPlan,challenge,epoch,memoryVram);
    dprintf("k40_mem: OWNER_LOAD epoch=%llu\n",(unsigned long long)epoch);return B_OK;
}
status_t prepare(uint64* lease,uint8 request[256]){Guard g;return g.held&&owner?owner->prepare(lease,request):B_BUSY;}
status_t submit(uint64 lease,const uint8 grant[320],size_t n){Guard g;return g.held&&owner?owner->submit(lease,grant,n):B_BUSY;}
status_t detach(uint64 lease){Guard g;return g.held&&owner?owner->detach(lease):B_BUSY;}
status_t observe(){Guard g;return g.held&&owner?owner->observeLoad():B_BUSY;}
k40_memory_module interface={{K40_MEMORY_OWNER_NAME,B_KEEP_LOADED,standard},1,prepare,submit,detach,observe};
}
extern "C" {module_info* modules[]={&interface.info,nullptr};}
#endif
