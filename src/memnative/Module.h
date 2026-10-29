// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#ifdef _KERNEL_MODE
#include <module.h>
#define K40_MEMORY_OWNER_NAME "generic/k40c_memory_owner/v1"
typedef struct {
    module_info info;
    uint32 abi;
    status_t (*prepare)(uint64* lease,uint8 request[256]);
    status_t (*submit)(uint64 lease,const uint8 grant[320],size_t);
    status_t (*detach)(uint64 lease);
    status_t (*observe_client_load)();
} k40_memory_module;
#endif
