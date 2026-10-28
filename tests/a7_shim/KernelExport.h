// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Host injection API only. Real Haiku headers are checked by the cross-link.
#pragma once
#include "../os_shim/KernelExport.h"
#include <sys/types.h>
enum { B_BUSY=-7,B_BAD_ADDRESS=-8,B_CUR_DRIVER_API_VERSION=2 };
void spin(bigtime_t);
status_t user_memcpy(void*,const void*,size_t);
int k40_a7_mock_log(const char*,...);
#define dprintf k40_a7_mock_log
