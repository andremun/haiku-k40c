// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Fixed A7 stream client. The resident module owns every hardware callback.
#include "a7/Module.h"
#include <Drivers.h>
#include <KernelExport.h>
#include <atomic>
#include <cstring>
namespace {
const char* devices[]={"misc/k40_a7_stage",nullptr};
struct Cookie {k40_a7_module* api=nullptr;uint64 lease=0;uint8 request[128]{},grant[192]{};size_t received=0;bool queried=false,submitted=false;};
Cookie cookie;
std::atomic_flag attached=ATOMIC_FLAG_INIT,ioLock=ATOMIC_FLAG_INIT;
struct Guard {bool held=!ioLock.test_and_set();~Guard(){if(held)ioLock.clear();}};
status_t openDevice(const char*,uint32,void** out)
{
    if(!out || attached.test_and_set())return B_BUSY;
    cookie={};module_info* info=nullptr;
    const auto loaded=get_module(K40_A7_OWNER_NAME,&info);
    if(loaded!=B_OK) {attached.clear();dprintf("k40_a7: FAIL client get_module status=%ld\n",long(loaded));return B_ERROR;}
    auto* api=reinterpret_cast<k40_a7_module*>(info);
    if(!api || !info->name || std::strcmp(info->name,K40_A7_OWNER_NAME) || !(info->flags&B_KEEP_LOADED)
        || api->abi!=1 || !api->prepare || !api->submit || !api->detach
        || api->prepare(&cookie.lease,cookie.request)!=K40_A7_OK || !cookie.lease) {
        put_module(K40_A7_OWNER_NAME);attached.clear();dprintf("k40_a7: FAIL client prepare\n");return B_ERROR;
    }
    cookie.api=api;*out=&cookie;return B_OK;
}
status_t closeDevice(void* value)
{
    Guard guard;if(!guard.held)return B_BUSY;
    if(value!=&cookie || !cookie.api)return B_BAD_VALUE;
    const auto result=cookie.api->detach(cookie.lease);
    return result==K40_A7_RETAINED?B_OK:B_ERROR;
}
status_t freeCookie(void* value)
{
    Guard guard;if(!guard.held)return B_BUSY;
    if(value!=&cookie)return B_BAD_VALUE;
    if(cookie.api && put_module(K40_A7_OWNER_NAME)!=B_OK) {
        dprintf("k40_a7: FAIL client put_module\n");return B_ERROR;
    }
    cookie={};attached.clear();return B_OK;
}
status_t readDevice(void* value,off_t,void* user,size_t* bytes)
{
    Guard guard;if(!guard.held)return B_BUSY;
    if(value!=&cookie || !cookie.api || !bytes)return B_BAD_VALUE;
    if(cookie.queried){*bytes=0;return B_OK;}
    if(*bytes<sizeof(cookie.request))return B_BAD_VALUE;
    if(user_memcpy(user,cookie.request,sizeof(cookie.request))!=B_OK)return B_BAD_ADDRESS;
    cookie.queried=true;*bytes=sizeof(cookie.request);return B_OK;
}
status_t writeDevice(void* value,off_t,const void* user,size_t* bytes)
{
    Guard guard;if(!guard.held)return B_BUSY;
    if(value!=&cookie || !cookie.api || !bytes || !cookie.queried || cookie.submitted
        || !*bytes || *bytes>sizeof(cookie.grant)-cookie.received)return B_BAD_VALUE;
    if(user_memcpy(cookie.grant+cookie.received,user,*bytes)!=B_OK)return B_BAD_ADDRESS;
    cookie.received+=*bytes;
    if(cookie.received==sizeof(cookie.grant)) {
        cookie.submitted=true;
        if(cookie.api->submit(cookie.lease,cookie.grant,sizeof(cookie.grant))!=K40_A7_OK)return B_ERROR;
    }
    return B_OK;
}
status_t controlDevice(void*,uint32,void*,size_t){return B_NOT_ALLOWED;}
device_hooks hooks={openDevice,closeDevice,freeCookie,controlDevice,readDevice,writeDevice,nullptr,nullptr,nullptr,nullptr};
}
extern "C" {
int32 api_version=B_CUR_DRIVER_API_VERSION;
status_t init_hardware(){return B_OK;}
status_t init_driver(){dprintf("k40_stage: A7_ARM_ONLY_POST_WRITE\n");return B_OK;}
void uninit_driver(){}
const char** publish_devices(){return devices;}
device_hooks* find_device(const char* name){return name && !std::strcmp(name,devices[0])?&hooks:nullptr;}
}
