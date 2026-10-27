/* Copyright 2026 Mario Andres Munoz.
 * Distributed under the terms of the MIT License.
 * Host API tokens, not native ABI evidence. */
#pragma once
#include "KernelExport.h"
enum { B_MODULE_INIT = 1, B_MODULE_UNINIT = 2, B_KEEP_LOADED = 1 };
#ifdef __cplusplus
extern "C" {
#endif
status_t get_module(const char*, module_info**);
status_t put_module(const char*);
#ifdef __cplusplus
}
#endif
