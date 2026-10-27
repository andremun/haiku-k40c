// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include <module.h>
#ifdef __cplusplus
extern "C" {
#endif
#define K40_OWNER_MODULE_NAME "generic/k40c_owner/v1"
// Software ABI results, not Haiku status_t or hardware status values.
enum k40_owner_result { K40_OWNER_OK, K40_OWNER_BUSY, K40_OWNER_LEASE, K40_OWNER_INPUT,
    K40_OWNER_EXHAUSTED, K40_OWNER_IO, K40_OWNER_RETAINED, K40_OWNER_STARTUP, K40_OWNER_DMA_DENIED };
typedef struct {
    uint64 owned, quarantined;
    uint32 attached, startup; // startup values: Fresh=0, Running=1, Complete=2, Failed=3.
} k40_owner_info;
typedef struct {
    uint64 token, bytes, guest_physical;
    uint32 physical_known, mapping_verified, releasing, quarantined;
} k40_owner_allocation;
// Kernel callers only. Every buffer is copied synchronously; no pointer is retained.
// A lease holds exclusive client ownership, while module residency is permanent.
typedef struct {
    module_info info;
    uint32 abi_version;
    int32 (*acquire)(uint64* lease);
    int32 (*detach)(uint64 lease);
    int32 (*allocate)(uint64 lease, uint64 bytes, uint64 alignment, uint64* token);
    int32 (*write)(uint64 lease, uint64 token, uint64 offset, const void*, size_t);
    int32 (*read)(uint64 lease, uint64 token, uint64 offset, void*, size_t);
    int32 (*release)(uint64 lease, uint64 token);
    int32 (*publish)(uint64 lease, uint64 token); // Always denied in this ABI version.
    int32 (*begin)(uint64 lease); // Consume one-shot latch; grants no hardware permission.
    int32 (*finish)(uint64 lease, uint32 success); // Caller-reported state, not readiness proof.
    int32 (*inspect)(k40_owner_info*);
    int32 (*describe)(uint64 lease, size_t index, k40_owner_allocation*);
} k40_owner_module;
#ifdef __cplusplus
}
#endif
