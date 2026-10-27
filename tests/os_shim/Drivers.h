/* Copyright 2026 Mario Andres Munoz.
 * Distributed under the terms of the MIT License.
 * Probe control-flow mock only. Not Haiku ABI evidence. */
#pragma once
#include <KernelExport.h>
#define B_CUR_DRIVER_API_VERSION 2
typedef struct { int unused; } device_hooks;
void k40_probe_log(const char*, ...);
#define dprintf k40_probe_log
