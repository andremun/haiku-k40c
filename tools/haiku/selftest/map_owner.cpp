// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// D0 memory-only client. No PCI, BAR, IOVA publication or device operation.
#include "os/OwnerClient.h"
#include <Drivers.h>
#include <KernelExport.h>
#include <cstring>
#include <new>
using k40::os::OwnerClient;
namespace {
alignas(OwnerClient) unsigned char storage[sizeof(OwnerClient)];
OwnerClient* client=nullptr;
unsigned phase=0;
uint64 token=0;
const char* devices[]={nullptr};
bool prepare()
{
    auto* api=client->api();auto lease=client->lease();
    if(api->allocate(lease,4096,4096,&token)!=K40_OWNER_OK)return false;
    unsigned char input[256],output[256];
    for(unsigned at=0;at<4096;at+=sizeof(input)) {
        for(unsigned i=0;i<sizeof(input);++i)input[i]=uint8((at+i)*37+11);
        if(api->write(lease,token,at,input,sizeof(input))!=K40_OWNER_OK
            || api->read(lease,token,at,output,sizeof(output))!=K40_OWNER_OK
            || std::memcmp(input,output,sizeof(input)))return false;
    }
    if(api->publish(lease,token)!=K40_OWNER_DMA_DENIED
        || api->begin(lease)!=K40_OWNER_OK || api->finish(lease,0)!=K40_OWNER_OK)return false;
    phase=1;return true;
}
bool report(const k40_owner_info& info)
{
    auto* api=client->api();auto lease=client->lease();k40_owner_allocation allocation{};
    if(api->describe(lease,0,&allocation)!=K40_OWNER_OK || !allocation.physical_known
        || allocation.mapping_verified || allocation.releasing || allocation.bytes!=4096
        || allocation.guest_physical%4096 || allocation.guest_physical>uint64(UINT32_MAX)-4095
        || !allocation.token || (phase==1 && allocation.token!=token))return false;
    if(phase==2 && (!allocation.quarantined || info.startup!=3 || info.owned!=1 || info.quarantined!=1
        || api->begin(lease)!=K40_OWNER_RETAINED))return false;
    token=allocation.token;
    dprintf("k40_d0: phase=%u lease=%llu token=%llu gpa=0x%llx bytes=%llu quarantine=%lu visibility=DENIED\n",
        phase,(unsigned long long)lease,(unsigned long long)token,
        (unsigned long long)allocation.guest_physical,(unsigned long long)allocation.bytes,
        (unsigned long)allocation.quarantined);
    return true;
}
void destroy() {if(client){client->~OwnerClient();client=nullptr;}}
}
extern "C" {
int32 api_version=B_CUR_DRIVER_API_VERSION;
status_t init_hardware(void){return B_OK;}
status_t init_driver(void)
{
    dprintf("k40_stage: D0_MEMORY_NO_DEVICE\n");
    if(client){dprintf("k40_os: FAIL D0 duplicate init\n");return B_ERROR;}
    phase=0;token=0;client=new(storage) OwnerClient;
    k40_owner_info info{};
    if(client->open()!=K40_OWNER_OK || client->api()->inspect(&info)!=K40_OWNER_OK)goto fail;
    if(info.startup==0) {
        if(info.owned || info.quarantined || !prepare())goto fail;
    } else phase=2;
    if(!report(info))goto fail;
    return B_OK;
fail:
    dprintf("k40_os: FAIL D0 owner preparation\n");destroy();return B_ERROR;
}
void uninit_driver(void)
{
    if(!client || !phase){dprintf("k40_os: FAIL D0 uninit state\n");return;}
    auto lease=client->lease();auto closed=client->close();
    if(closed!=K40_OWNER_RETAINED)dprintf("k40_os: FAIL D0 detach result=%ld\n",(long)closed);
    else {
        dprintf("k40_d0: phase=%u detached lease=%llu token=%llu retained\n",phase,
            (unsigned long long)lease,(unsigned long long)token);
        if(phase==2)dprintf("k40_d0: PASS retained host extent only; DMA denied\n");
    }
    destroy();phase=0;
}
const char** publish_devices(void){return devices;}
device_hooks* find_device(const char*){return nullptr;}
}
