// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "a7/Module.h"
#include "a7/NativePlatform.h"
#include "a7_config.h" // Build-only exact ROM, public key and single-use package nonce.
#include <new>
// Exact exported declaration: Haiku private/kernel/util/Random.h:24-31.
// Avoid including unrelated private boot-layout headers.
extern "C" unsigned int secure_random_value(void);
namespace {
using namespace k40::a7;
alignas(NativeStorage) unsigned char storageMemory[sizeof(NativeStorage)];
alignas(NativePlatform) unsigned char platformMemory[sizeof(NativePlatform)];
alignas(Owner) unsigned char ownerMemory[sizeof(Owner)];
Owner* owner=nullptr;
status_t standard(int32 op,...)
{
    if(op==B_MODULE_UNINIT)return B_NOT_ALLOWED;
    if(op!=B_MODULE_INIT || owner)return B_BAD_VALUE;
    auto* storage=new(storageMemory) NativeStorage;
    auto* platform=new(platformMemory) NativePlatform;
    uint8 challenge[16];
    // Exported kernel PRNG, not claimed as cryptographic entropy. Single-use
    // package keys are host-generated; this also distinguishes owner instances.
    for(unsigned i=0;i<4;++i) {
        const uint32 value=secure_random_value();
        for(unsigned j=0;j<4;++j)challenge[4*i+j]=uint8(value>>(8*j));
    }
    owner=new(ownerMemory) Owner(*platform,*storage,a7PublicKey,a7PackageNonce,challenge,a7Rom,sizeof(a7Rom),a7ExpectedVram);
    return B_OK;
}
int32 prepare(uint64* lease,uint8 request[128])
{if(!owner || !lease || !request)return K40_A7_INPUT;return int32(owner->prepare(*lease,request));}
int32 submit(uint64 lease,const uint8 grant[192],size_t size)
{return owner?int32(owner->submit(lease,grant,size)):K40_A7_INPUT;}
int32 detach(uint64 lease){return owner?int32(owner->detach(lease)):K40_A7_INPUT;}
k40_a7_module interface={{K40_A7_OWNER_NAME,B_KEEP_LOADED,standard},1,prepare,submit,detach};
}
extern "C" {module_info* modules[]={&interface.info,nullptr};}
