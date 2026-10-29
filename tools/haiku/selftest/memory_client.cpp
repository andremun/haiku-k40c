// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memnative/Module.h"
#include <Drivers.h>
#include <KernelExport.h>
#include <atomic>
#include <cstring>
namespace {
const char* devices[]={"misc/k40_mem_stage",nullptr};
struct Cookie {k40_memory_module* api=nullptr;uint64 lease=0;uint8 request[256]{},grant[320]{};size_t received=0;bool queried=false,submitted=false;};
Cookie cookie;std::atomic_flag attached=ATOMIC_FLAG_INIT,ioLock=ATOMIC_FLAG_INIT;
struct Guard {bool held=!ioLock.test_and_set();~Guard(){if(held)ioLock.clear();}};
status_t openDevice(const char*,uint32,void** out)
{
    if(!out || attached.test_and_set())return B_BUSY;
    module_info* info=nullptr;const auto loaded=get_module(K40_MEMORY_OWNER_NAME,&info);
    if(loaded!=B_OK){attached.clear();return loaded;}
    auto* api=reinterpret_cast<k40_memory_module*>(info);
    if(!info->name || std::strcmp(info->name,K40_MEMORY_OWNER_NAME) || !(info->flags&B_KEEP_LOADED)
        || api->abi!=1 || !api->prepare || !api->submit || !api->detach) {
        put_module(K40_MEMORY_OWNER_NAME);attached.clear();return B_BAD_DATA;
    }
    cookie={};const auto prepared=api->prepare(&cookie.lease,cookie.request);
    if(prepared!=B_OK || !cookie.lease){put_module(K40_MEMORY_OWNER_NAME);attached.clear();return prepared==B_OK?B_BAD_DATA:prepared;}
    cookie.api=api;*out=&cookie;return B_OK;
}
status_t closeDevice(void* value)
{Guard g;if(!g.held)return B_BUSY;if(value!=&cookie || !cookie.api)return B_BAD_VALUE;return cookie.api->detach(cookie.lease);}
status_t freeCookie(void* value)
{
    Guard g;if(!g.held)return B_BUSY;if(value!=&cookie)return B_BAD_VALUE;
    const auto status=cookie.api?put_module(K40_MEMORY_OWNER_NAME):B_OK;
    cookie={};attached.clear();return status;
}
status_t readDevice(void* value,off_t,void* user,size_t* bytes)
{
    Guard g;if(!g.held)return B_BUSY;if(value!=&cookie || !cookie.api || !bytes)return B_BAD_VALUE;
    if(cookie.queried){*bytes=0;return B_OK;}if(*bytes<sizeof(cookie.request))return B_BAD_VALUE;
    if(user_memcpy(user,cookie.request,sizeof(cookie.request))!=B_OK)return B_BAD_ADDRESS;
    cookie.queried=true;*bytes=sizeof(cookie.request);return B_OK;
}
status_t writeDevice(void* value,off_t,const void* user,size_t* bytes)
{
    Guard g;if(!g.held)return B_BUSY;
    if(value!=&cookie || !cookie.api || !bytes || !cookie.queried || cookie.submitted || !*bytes
        || *bytes>sizeof(cookie.grant)-cookie.received)return B_BAD_VALUE;
    if(user_memcpy(cookie.grant+cookie.received,user,*bytes)!=B_OK)return B_BAD_ADDRESS;
    cookie.received+=*bytes;
    if(cookie.received==sizeof(cookie.grant)){cookie.submitted=true;return cookie.api->submit(cookie.lease,cookie.grant,sizeof(cookie.grant));}
    return B_OK;
}
status_t controlDevice(void*,uint32,void*,size_t){return B_NOT_ALLOWED;}
device_hooks hooks={openDevice,closeDevice,freeCookie,controlDevice,readDevice,writeDevice,nullptr,nullptr,nullptr,nullptr};
}
extern "C" {
int32 api_version=B_CUR_DRIVER_API_VERSION;
status_t init_hardware(){return B_OK;}
status_t init_driver()
{
    dprintf("k40_mem_stage: BATCH1_MEMORY\n");module_info* info=nullptr;
    const auto loaded=get_module(K40_MEMORY_OWNER_NAME,&info);if(loaded!=B_OK)return loaded;
    auto* api=reinterpret_cast<k40_memory_module*>(info);
    const auto result=api->abi==1 && api->observe_client_load?api->observe_client_load():B_BAD_DATA;
    const auto released=put_module(K40_MEMORY_OWNER_NAME);return result==B_OK?released:result;
}
void uninit_driver(){dprintf("k40_mem: CLIENT_UNLOAD\n");}
const char** publish_devices(){return devices;}
device_hooks* find_device(const char* name){return name && !std::strcmp(name,devices[0])?&hooks:nullptr;}
}
