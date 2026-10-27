// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Cardless legacy client. No PCI, BAR, DMA, or physical card operations.
#include "os/OwnerClient.h"
#include <Drivers.h>
#include <KernelExport.h>
#include <cstring>
#include <new>
using k40::os::OwnerClient;
namespace {
alignas(OwnerClient) unsigned char storage[sizeof(OwnerClient)];
OwnerClient* client = nullptr;
unsigned phase = 0;
uint64 token = 0;
const char* devices[] = {nullptr};
bool first_load()
{
    auto* api = client->api();
    const auto lease = client->lease();
    uint64 scratch = 0;
    if (api->allocate(lease,513,65536,&scratch) != K40_OWNER_OK) return false;
    unsigned char input[513], output[513];
    for (unsigned i = 0; i < sizeof(input); ++i) input[i] = uint8(i * 37 + 11);
    if (api->write(lease,scratch,0,input,sizeof(input)) != K40_OWNER_OK
        || api->read(lease,scratch,0,output,sizeof(output)) != K40_OWNER_OK
        || std::memcmp(input,output,sizeof(input))
        || api->publish(lease,scratch) != K40_OWNER_DMA_DENIED) return false;
    k40_owner_allocation allocation;
    if (api->describe(lease,0,&allocation) != K40_OWNER_OK || !allocation.physical_known
        || allocation.mapping_verified || allocation.guest_physical % 65536
        || api->release(lease,scratch) != K40_OWNER_OK) return false;
    k40_owner_info empty;
    if (api->inspect(&empty) != K40_OWNER_OK || empty.owned || empty.quarantined) return false;
    dprintf("k40_owner_test: host-bytes-cleanup PASS; publication DENIED\n");
    if (api->allocate(lease,4096,4096,&token) != K40_OWNER_OK
        || api->begin(lease) != K40_OWNER_OK || api->finish(lease,0) != K40_OWNER_OK) return false;
    dprintf("k40_owner_test: phase1 init lease=%llu token=%llu\n",
        (unsigned long long)lease,(unsigned long long)token);
    phase = 1;
    return true;
}
bool reloaded(const k40_owner_info& info)
{
    auto* api = client->api();
    const auto lease = client->lease();
    k40_owner_allocation allocation;
    uint64 refused = 99;
    if (info.startup != 3 || info.owned != 1 || info.quarantined != 1
        || api->describe(lease,0,&allocation) != K40_OWNER_OK
        || !allocation.quarantined || !allocation.physical_known || allocation.mapping_verified
        || allocation.bytes != 4096 || !allocation.token
        || api->begin(lease) != K40_OWNER_RETAINED
        || api->allocate(lease,64,64,&refused) != K40_OWNER_RETAINED || refused) return false;
    token = allocation.token;
    dprintf("k40_owner_test: phase2 init lease=%llu token=%llu state=%lu owned=%llu quarantine=%llu\n",
        (unsigned long long)lease,(unsigned long long)token,(unsigned long)info.startup,
        (unsigned long long)info.owned,(unsigned long long)info.quarantined);
    phase = 2;
    return true;
}
void destroy()
{
    if (client) { client->~OwnerClient(); client = nullptr; }
}
}
extern "C" {
int32 api_version = B_CUR_DRIVER_API_VERSION;
status_t init_hardware(void) { return B_OK; }
status_t init_driver(void)
{
    dprintf("k40_stage: CARDLESS_OWNER_ONLY\n");
    if (client) { dprintf("k40_os: FAIL owner client initialized twice without uninit\n"); return B_ERROR; }
    phase = 0; token = 0;
    client = new (storage) OwnerClient;
    k40_owner_info info{};
    const auto opened = client->open();
    if (opened != K40_OWNER_OK || client->api()->inspect(&info) != K40_OWNER_OK
        || !(info.startup == 0 ? first_load() : reloaded(info))) {
        dprintf("k40_os: FAIL owner client init open=%ld state=%lu owned=%llu quarantine=%llu\n",
            (long)opened,(unsigned long)info.startup,(unsigned long long)info.owned,
            (unsigned long long)info.quarantined);
        destroy(); return B_ERROR;
    }
    return B_OK;
}
void uninit_driver(void)
{
    if (!client || !phase) { dprintf("k40_os: FAIL owner uninit state\n"); return; }
    const auto lease = client->lease();
    const auto result = client->close();
    if (result != K40_OWNER_RETAINED) dprintf("k40_os: FAIL owner detach result=%ld\n",(long)result);
    else {
        dprintf("k40_owner_test: phase%u uninit lease=%llu token=%llu retained\n",
            phase,(unsigned long long)lease,(unsigned long long)token);
        if (phase == 2) dprintf("k40_os: PASS native owner reload only; DMA denied\n");
    }
    destroy(); phase = 0;
}
const char** publish_devices(void) { return devices; }
device_hooks* find_device(const char*) { return nullptr; }
}
