/* Copyright 2026 Mario Andrés Muñoz.
 * Distributed under the terms of the MIT License.
 * Host failure-injection shim, NOT Haiku ABI evidence. Real headers are used
 * independently by the cross build. Status values here are test-only. */
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
typedef uint8_t uint8;
typedef uint16_t uint16;
typedef uint32_t uint32;
typedef uint64_t uint64;
typedef int32_t int32;
typedef int64_t bigtime_t;
typedef int status_t;
typedef int area_id;
typedef uint64_t phys_addr_t;
typedef uint64_t phys_size_t;
typedef struct { int unused; } module_info;
typedef struct { phys_addr_t address;phys_size_t size; } physical_entry;
enum { B_OK=0,B_ERROR=-1,B_BAD_VALUE=-2,B_BAD_DATA=-3 };
enum { B_NOT_ALLOWED=-4,B_IO_ERROR=-5,B_ENTRY_NOT_FOUND=-6 };
/* API tokens for host mocks; not used to infer native numeric values. */
enum { B_PAGE_SIZE=4096,B_ANY_KERNEL_ADDRESS=1,B_KERNEL_READ_AREA=16,B_KERNEL_WRITE_AREA=32,B_CONTIGUOUS=3 };
status_t get_module(const char*,module_info**);
status_t put_module(const char*);
area_id map_physical_memory(const char*,phys_addr_t,size_t,uint32,uint32,void**);
status_t delete_area(area_id);
area_id create_area(const char*,void**,uint32,size_t,uint32,uint32);
int32 get_memory_map(const void*,size_t,physical_entry*,int32);
bigtime_t system_time(void);
status_t snooze(bigtime_t);
