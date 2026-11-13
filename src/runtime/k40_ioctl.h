/* Copyright 2026 Mario Andres Munoz.
 * Distributed under the terms of the MIT License.
 *
 * First user interface of the K40c compute driver: a private ioctl set on the
 * device node. PROPOSED (docs/RUNTIME-INTERFACE.md). No device node implements
 * it yet. Shared with haiku-k40c-llm (runtime contract v0.3). Plain C, fixed
 * width, no pointers inside structures except the user buffers of each call.
 */
#ifndef K40_IOCTL_H
#define K40_IOCTL_H
#include <stdint.h>

#define K40_IOCTL_VERSION 1u
#define K40_DEVICE_PATH "/dev/misc/k40c"
/* Haiku private ioctl numbers start at B_DEVICE_OP_CODES_END (Drivers.h). */
#define K40_IOCTL_BASE 0x4b343000u // no source: software choice, 'K40' << 8

enum k40_op {
	K40_QUERY = K40_IOCTL_BASE + 0, /* k40_query */
	K40_ALLOCATE,                   /* k40_allocate */
	K40_WRITE,                      /* k40_transfer */
	K40_READ,                       /* k40_transfer */
	K40_LOAD_MODULE,                /* k40_module */
	K40_DISPATCH,                   /* k40_dispatch */
	K40_WAIT,                       /* k40_wait */
	K40_RELEASE,                    /* k40_release */
};

enum k40_status {
	K40_OK = 0,
	K40_BUSY = 1,       /* buffer or context in flight */
	K40_TIMEOUT = 2,    /* deadline passed; resources stay pinned */
	K40_FAULT = 3,      /* GR, FECS, FIFO or MMU fault; context poisoned */
	K40_POISONED = 4,   /* call on a poisoned context */
	K40_BAD_HANDLE = 5,
	K40_BAD_RANGE = 6,
	K40_NO_MEMORY = 7,
	K40_UNSUPPORTED = 8,
};

struct k40_query {
	uint32_t version;        /* out: K40_IOCTL_VERSION */
	uint32_t chipset;        // out; no source: software field, this card reads 0xf1 (hardware/record.md)
	uint64_t vram_bytes;     /* out: usable by this context */
	uint32_t units;          /* out: 15 shader units on this card */
	uint32_t max_buffers;    /* out */
};

/* All buffers live in VRAM. The GPU address is fixed at allocation (Q4). */
struct k40_allocate {
	uint64_t bytes;          /* in */
	uint32_t alignment;      /* in: power of two, at least 256 */
	uint32_t flags;          /* in: K40_BUFFER_* */
	uint32_t handle;         /* out */
	uint32_t status;         /* out */
};
#define K40_BUFFER_GPU_WRITE 1u /* a kernel may write it */

struct k40_transfer {
	uint32_t handle;         /* in */
	uint32_t status;         /* out */
	uint64_t offset;         /* in: bytes, multiple of 4 */
	uint64_t bytes;          /* in: multiple of 4 */
	void*    user;           /* in: source (WRITE) or destination (READ) */
};

/* One argument of a kernel: where it sits in constant buffer 0. */
struct k40_argument {
	uint32_t offset;         /* bytes in constant buffer 0 */
	uint32_t kind;           /* K40_ARG_POINTER (8 bytes) or K40_ARG_VALUE */
	uint32_t bytes;          /* 4 or 8 for values */
	uint32_t access;         /* pointers: K40_BUFFER_GPU_WRITE or 0 */
};
#define K40_ARG_POINTER 1u
#define K40_ARG_VALUE 2u
#define K40_MAX_ARGUMENTS 16u

/* A compiled kernel (GK110B machine code from the host compiler). */
struct k40_module {
	const void* code;        /* in */
	uint32_t code_bytes;     /* in */
	uint32_t register_count; /* in: launch register count */
	uint32_t local_bytes;    /* in */
	uint32_t shared_bytes;   /* in */
	uint32_t barriers;       /* in */
	uint32_t argument_count; /* in */
	struct k40_argument arguments[K40_MAX_ARGUMENTS]; /* in */
	uint32_t relocations;    /* in: must be 0 in version 1 (no built-in library) */
	uint32_t handle;         /* out */
	uint32_t status;         /* out */
};

struct k40_binding {
	uint32_t argument;       /* index in the module's argument table */
	uint32_t handle;         /* pointers: buffer handle */
	uint64_t value;          /* pointers: byte offset in the buffer; values: the value */
};

struct k40_dispatch {
	uint32_t module;         /* in */
	uint32_t binding_count;  /* in */
	const struct k40_binding* bindings; /* in */
	uint32_t grid[3];        /* in: blocks */
	uint32_t block[3];       /* in: threads in one block */
	uint32_t fence;          /* out */
	uint32_t status;         /* out */
};

struct k40_wait {
	uint32_t fence;          /* in */
	uint32_t status;         /* out */
	uint64_t timeout_us;     /* in */
};

struct k40_release {
	uint32_t handle;         /* in: buffer or module */
	uint32_t status;         /* out: K40_BUSY keeps it */
};
#endif
