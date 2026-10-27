// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Host ABI spies and owner recreation tests; no native module-load evidence.
#include "os/HaikuOwnerModule.h"
#include "os/NativeOwner.h"
#include "os/OwnerClient.h"
#include <cstdio>
#include <cstring>
#include <map>
#include <new>
#include <vector>
extern "C" module_info* modules[];
using namespace k40::os;
static unsigned checks = 0, failures = 0, frees = 0;
static bool allocationOk = true, partial = false, freeOk = true, reenter = false;
static int area = 1;
static std::map<int,std::vector<uint8_t>> areas;
static k40_owner_module* api;
static unsigned moduleGets = 0, modulePuts = 0;
static bool getOk = true;
static OwnerClient* closingClient = nullptr;
#define CHECK(c) do { ++checks; if (!(c)) { ++failures; std::printf("FAIL %d: %s\n", __LINE__, #c); } } while (0)
extern "C" status_t get_module(const char* name, module_info** info)
{
    ++moduleGets; CHECK(!std::strcmp(name,K40_OWNER_MODULE_NAME));
    if (!getOk) return B_ERROR;
    *info = modules[0]; return B_OK;
}
extern "C" status_t put_module(const char* name)
{
    ++modulePuts; CHECK(!std::strcmp(name,K40_OWNER_MODULE_NAME)); return B_OK;
}
extern "C" status_t k40_os_allocate_dma32(size_t bytes, k40_host_allocation* out)
{
    *out = {-1,nullptr,0,0};
    if (reenter) { k40_owner_info info; CHECK(api->inspect(&info) == K40_OWNER_BUSY); }
    if (closingClient) CHECK(closingClient->close() == K40_OWNER_BUSY);
    if (!allocationOk && !partial) return B_ERROR;
    areas[area].resize(bytes);
    *out = {area, areas[area].data(), bytes, 0x10000000};
    ++area;
    return allocationOk ? B_OK : B_ERROR;
}
extern "C" status_t k40_os_free(k40_host_allocation* allocation)
{
    if (!freeOk) return B_ERROR;
    CHECK(areas.erase(allocation->area) == 1);
    ++frees;
    *allocation = {-1,nullptr,0,0};
    return B_OK;
}
int main()
{
    api = reinterpret_cast<k40_owner_module*>(modules[0]);
    CHECK(modules[1] == nullptr && api->abi_version == 1);
    CHECK(!std::strcmp(api->info.name,K40_OWNER_MODULE_NAME) && api->info.flags == B_KEEP_LOADED);
    uint64 lease = 99, token = 99, other = 99;
    CHECK(api->acquire(&lease) == K40_OWNER_INPUT && lease == 0);
    CHECK(api->info.std_ops(99) == B_BAD_VALUE);
    CHECK(api->info.std_ops(B_MODULE_UNINIT) == B_NOT_ALLOWED);
    CHECK(api->info.std_ops(B_MODULE_INIT) == B_OK);
    CHECK(api->info.std_ops(B_MODULE_INIT) == B_BAD_VALUE);
    CHECK(api->acquire(nullptr) == K40_OWNER_INPUT && api->inspect(nullptr) == K40_OWNER_INPUT);
    {
        OwnerClient first, second;
        getOk = false; CHECK(first.open() == K40_OWNER_IO && !first.api());
        getOk = true;
        const auto oldVersion = api->abi_version; api->abi_version = 2;
        CHECK(first.open() == K40_OWNER_INPUT); api->abi_version = oldVersion;
        CHECK(first.open() == K40_OWNER_OK && first.api() == api && first.lease());
        CHECK(first.open() == K40_OWNER_INPUT);
        CHECK(second.open() == K40_OWNER_BUSY && !second.api());
        CHECK(first.close() == K40_OWNER_OK && !first.api() && !first.lease());
        CHECK(first.close() == K40_OWNER_OK);
        CHECK(second.open() == K40_OWNER_OK);
        closingClient = &second;
        uint64 handle = 0;
        CHECK(second.api()->allocate(second.lease(),64,64,&handle) == K40_OWNER_OK);
        closingClient = nullptr;
        CHECK(second.api() && second.lease());
        CHECK(second.close() == K40_OWNER_OK);
    }
    CHECK(moduleGets == modulePuts + 1); // Failed get held no reference.
    CHECK(api->acquire(&lease) == K40_OWNER_OK && lease);
    CHECK(api->acquire(&other) == K40_OWNER_BUSY && !other);
    CHECK(api->detach(lease + 1) == K40_OWNER_LEASE);
    CHECK(api->finish(lease,1) == K40_OWNER_STARTUP);
    CHECK(api->allocate(lease,64,64,nullptr) == K40_OWNER_INPUT);
    CHECK(api->allocate(lease,0,64,&token) == K40_OWNER_IO && !token);
    allocationOk = false;
    CHECK(api->allocate(lease,64,64,&token) == K40_OWNER_IO && !token);
    allocationOk = true;
    reenter = true;
    CHECK(api->allocate(lease,64,64,&token) == K40_OWNER_OK && token);
    reenter = false;
    unsigned value = 123456, readback = 0;
    CHECK(api->write(lease,token,60,&value,4) == K40_OWNER_OK);
    CHECK(api->read(lease,token,60,&readback,4) == K40_OWNER_OK && value == readback);
    CHECK(api->write(lease,token,61,&value,4) == K40_OWNER_IO);
    CHECK(api->read(lease,token,0,nullptr,1) == K40_OWNER_IO);
    CHECK(api->publish(lease,token) == K40_OWNER_DMA_DENIED);
    k40_owner_allocation allocation;
    CHECK(api->describe(lease,0,&allocation) == K40_OWNER_OK);
    CHECK(allocation.token == token && allocation.physical_known && !allocation.mapping_verified);
    CHECK(api->describe(lease,16,&allocation) == K40_OWNER_INPUT);
    CHECK(api->release(lease,token + 1) == K40_OWNER_INPUT);
    CHECK(api->detach(lease) == K40_OWNER_OK && areas.empty());
    const uint64 oldLease = lease, oldToken = token;
    CHECK(api->acquire(&lease) == K40_OWNER_OK && lease != oldLease);
    CHECK(api->allocate(oldLease,64,64,&token) == K40_OWNER_LEASE && !token);
    CHECK(api->allocate(lease,64,64,&token) == K40_OWNER_OK && token != oldToken);
    CHECK(api->release(lease,oldToken) == K40_OWNER_INPUT);
    CHECK(api->write(oldLease,token,0,&value,4) == K40_OWNER_LEASE);
    CHECK(api->release(lease,token) == K40_OWNER_OK);
    std::vector<uint64> tokens;
    for (unsigned i = 0; i < 16; ++i) {
        CHECK(api->allocate(lease,64,64,&token) == K40_OWNER_OK);
        tokens.push_back(token);
    }
    CHECK(api->allocate(lease,64,64,&token) == K40_OWNER_EXHAUSTED && !token);
    for (auto owned : tokens) CHECK(api->release(lease,owned) == K40_OWNER_OK);
    CHECK(api->allocate(lease,4096,4096,&token) == K40_OWNER_OK);
    CHECK(api->begin(lease) == K40_OWNER_OK);
    CHECK(api->begin(lease) == K40_OWNER_STARTUP);
    CHECK(api->finish(lease,2) == K40_OWNER_INPUT);
    CHECK(api->finish(lease,1) == K40_OWNER_OK);
    CHECK(api->finish(lease,0) == K40_OWNER_STARTUP);
    CHECK(api->write(lease,token,0,&value,4) == K40_OWNER_RETAINED);
    CHECK(api->read(lease,token,0,&readback,4) == K40_OWNER_RETAINED);
    CHECK(api->release(lease,token) == K40_OWNER_RETAINED);
    const auto before = frees;
    CHECK(api->detach(lease) == K40_OWNER_RETAINED && frees == before);
    CHECK(api->acquire(&lease) == K40_OWNER_OK);
    k40_owner_info info;
    CHECK(api->inspect(&info) == K40_OWNER_OK && info.owned == 1 && info.quarantined == 1 && info.startup == 2);
    CHECK(api->begin(lease) == K40_OWNER_RETAINED);
    CHECK(api->allocate(lease,64,64,&token) == K40_OWNER_RETAINED && !token);
    CHECK(api->describe(lease,0,&allocation) == K40_OWNER_OK && allocation.quarantined && !allocation.mapping_verified);
    CHECK(api->info.std_ops(B_MODULE_UNINIT) == B_NOT_ALLOWED);
    CHECK(api->info.std_ops(B_MODULE_INIT) == B_BAD_VALUE);
    CHECK(api->inspect(&info) == K40_OWNER_OK && info.quarantined == 1 && info.startup == 2);
    CHECK(api->detach(lease) == K40_OWNER_RETAINED);
    // Independent simulated boots test partial cleanup and abandoned startup.
    for (unsigned mode = 0; mode < 4; ++mode) {
        alignas(NativeOwner) unsigned char storage[sizeof(NativeOwner)];
        auto* owner = new (storage) NativeOwner;
        uint64_t client = 0, handle = 0;
        CHECK(owner->acquire(client) == OwnerError::None);
        allocationOk = mode != 0; partial = mode == 0; freeOk = mode != 0;
        const auto allocated = owner->allocate(client,64,64,handle);
        if (mode == 0) CHECK(allocated == OwnerError::Io && handle == 0);
        else {
            CHECK(allocated == OwnerError::None);
            if (mode != 3) CHECK(owner->begin(client) == OwnerError::None);
            if (mode == 3) freeOk = false;
            if (mode == 2) CHECK(owner->finish(client,false) == OwnerError::None);
        }
        CHECK(owner->detach(client) == OwnerError::Retained);
        freeOk = allocationOk = true; partial = false;
        CHECK(owner->acquire(client) == OwnerError::None);
        OwnerInfo retained;
        CHECK(owner->inspect(retained) == OwnerError::None && retained.quarantined == 1);
        CHECK(retained.startup == ((mode == 0 || mode == 3) ? k40::runtime::startup::BootState::Fresh : k40::runtime::startup::BootState::Failed));
        CHECK(owner->allocate(client,64,64,handle) == OwnerError::Retained);
        CHECK(owner->detach(client) == OwnerError::Retained);
    }
    {
        // Binding failures also persist without the private approved ROM.
        alignas(NativeOwner) unsigned char storage[sizeof(NativeOwner)];
        auto* owner = new (storage) NativeOwner;
        uint64_t client=0;
        CHECK(owner->acquire(client)==OwnerError::None);
        OwnerPostInfo post;
        CHECK(owner->inspectPost(client+1,post)==OwnerError::Lease);
        CHECK(owner->inspectPost(client,post)==OwnerError::None && !post.bindingAttempted);
        std::vector<uint8_t> wrong(k40::devinit::approvedRomBytes,0);
        CHECK(owner->bindPost(client+1,wrong.data(),wrong.size())==OwnerError::Lease);
        CHECK(owner->bindPost(client,nullptr,wrong.size())==OwnerError::Input);
        CHECK(owner->bindPost(client,wrong.data(),wrong.size()-1)==OwnerError::Input);
        CHECK(owner->inspectPost(client,post)==OwnerError::None && !post.bindingAttempted);
        CHECK(owner->bindPost(client,wrong.data(),wrong.size())==OwnerError::Input);
        CHECK(owner->inspectPost(client,post)==OwnerError::None && post.bindingAttempted && !post.bound);
        CHECK(owner->detach(client)==OwnerError::None);
        CHECK(owner->acquire(client)==OwnerError::None);
        CHECK(owner->bindPost(client,wrong.data(),wrong.size())==OwnerError::Input);
        CHECK(owner->inspectPost(client,post)==OwnerError::None && post.bindingAttempted && !post.executionAttempted);
        CHECK(owner->begin(client)==OwnerError::None);
        CHECK(owner->bindPost(client,wrong.data(),wrong.size())==OwnerError::Startup);
        CHECK(owner->detach(client)==OwnerError::None);
    }
    // Only test-process termination discards these simulated quarantined areas.
    std::printf("native owner host contracts: %u checks, %u failures; NOT native load evidence\n",checks,failures);
    return failures ? 1 : 0;
}
