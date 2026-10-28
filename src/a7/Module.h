// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include <module.h>
#define K40_A7_OWNER_NAME "generic/k40c_a7_owner/v1"
enum { K40_A7_OK=0,K40_A7_BUSY,K40_A7_RETAINED,K40_A7_INPUT,K40_A7_AUTH,K40_A7_IO,K40_A7_POST };
typedef struct {
    module_info info;
    uint32 abi;
    int32 (*prepare)(uint64* lease,uint8 request[128]);
    int32 (*submit)(uint64 lease,const uint8 grant[192],size_t);
    int32 (*detach)(uint64 lease);
    int32 (*observe_client_load)(void);
} k40_a7_module;
