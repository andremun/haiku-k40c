// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "os/HaikuOwnerModule.h"
#include "os/NativeOwner.h"
#include <new>

namespace {
using namespace k40::os;
alignas(NativeOwner) unsigned char storage[sizeof(NativeOwner)];
NativeOwner* owner = nullptr;
int32 code(OwnerError error)
{
    switch (error) {
    case OwnerError::None: return K40_OWNER_OK;
    case OwnerError::Busy: return K40_OWNER_BUSY;
    case OwnerError::Lease: return K40_OWNER_LEASE;
    case OwnerError::Input: return K40_OWNER_INPUT;
    case OwnerError::Exhausted: return K40_OWNER_EXHAUSTED;
    case OwnerError::Io: return K40_OWNER_IO;
    case OwnerError::Retained: return K40_OWNER_RETAINED;
    case OwnerError::Startup: return K40_OWNER_STARTUP;
    case OwnerError::DmaDenied: return K40_OWNER_DMA_DENIED;
    }
    return K40_OWNER_INPUT;
}
status_t standard(int32 op, ...)
{
    // module.cpp:2216-2221 adds a permanent ref only after successful INIT.
    // UNINIT never discards the boot latch, ownership records, or quarantine.
    if (op == B_MODULE_UNINIT) return B_NOT_ALLOWED;
    if (op != B_MODULE_INIT || owner) return B_BAD_VALUE;
    owner = new (storage) NativeOwner;
    return B_OK;
}
int32 acquire(uint64* lease)
{
    if (!lease) return K40_OWNER_INPUT;
    *lease = 0;
    return owner ? code(owner->acquire(*lease)) : K40_OWNER_INPUT;
}
int32 detach(uint64 lease) { return owner ? code(owner->detach(lease)) : K40_OWNER_INPUT; }
int32 allocate(uint64 lease, uint64 bytes, uint64 alignment, uint64* token)
{
    if (!token) return K40_OWNER_INPUT;
    *token = 0;
    return owner ? code(owner->allocate(lease, bytes, alignment, *token)) : K40_OWNER_INPUT;
}
int32 write(uint64 lease, uint64 token, uint64 offset, const void* data, size_t bytes)
{ return owner ? code(owner->write(lease, token, offset, data, bytes)) : K40_OWNER_INPUT; }
int32 read(uint64 lease, uint64 token, uint64 offset, void* data, size_t bytes)
{ return owner ? code(owner->read(lease, token, offset, data, bytes)) : K40_OWNER_INPUT; }
int32 release(uint64 lease, uint64 token) { return owner ? code(owner->release(lease, token)) : K40_OWNER_INPUT; }
int32 publish(uint64 lease, uint64 token) { return owner ? code(owner->publish(lease, token)) : K40_OWNER_INPUT; }
int32 begin(uint64 lease) { return owner ? code(owner->begin(lease)) : K40_OWNER_INPUT; }
int32 finish(uint64 lease, uint32 success)
{ return owner && success <= 1 ? code(owner->finish(lease, success != 0)) : K40_OWNER_INPUT; }
int32 inspect(k40_owner_info* info)
{
    if (!info) return K40_OWNER_INPUT;
    *info = {};
    if (!owner) return K40_OWNER_INPUT;
    OwnerInfo value;
    const auto error = owner->inspect(value);
    if (error == OwnerError::None)
        *info = {value.owned, value.quarantined, value.lease != 0, uint32(value.startup)};
    return code(error);
}
int32 describe(uint64 lease, size_t index, k40_owner_allocation* info)
{
    if (!info) return K40_OWNER_INPUT;
    *info = {};
    if (!owner) return K40_OWNER_INPUT;
    HaikuMemory::Info value;
    const auto error = owner->describe(lease, index, value);
    if (error == OwnerError::None)
        *info = {value.token, value.bytes, value.physical.value, value.physicalKnown,
                 value.mappingVerified, value.releasing, value.quarantined};
    return code(error);
}
k40_owner_module interface = {
    {K40_OWNER_MODULE_NAME, B_KEEP_LOADED, standard}, 1,
    acquire, detach, allocate, write, read, release, publish, begin, finish, inspect, describe
};
}
extern "C" {
module_info* modules[] = {&interface.info, nullptr};
}
