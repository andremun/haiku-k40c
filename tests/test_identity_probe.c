/* Copyright 2026 Mario Andres Munoz.
 * Distributed under the terms of the MIT License.
 * Run the identity probe against host spies. No hardware or native ABI claim. */
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include "HaikuBackend.h"

extern status_t init_driver(void);
static unsigned checks, failures, maps, reads, commands;
static bool present = true;
static uint16 command = PCI_command_memory;
static uint32 identity = 0x0f1240a1;
static uint32 scratch[B_PAGE_SIZE / 4];
static char log_text[4096];
#define CHECK(c) do { ++checks; if (!(c)) { ++failures; \
    printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

void k40_probe_log(const char* format, ...)
{
    va_list args;
    va_start(args, format);
    size_t used = strlen(log_text);
    vsnprintf(log_text + used, sizeof(log_text) - used, format, args);
    va_end(args);
}
static status_t next(int32 index, pci_info* info)
{
    if (!present || index) return B_ENTRY_NOT_FOUND;
    memset(info, 0, sizeof(*info));
    info->vendor_id = 0x10de;
    info->device_id = 0x1024;
    return B_OK;
}
static uint32 config(uint8 bus, uint8 device, uint8 function, uint8 offset, uint8 size)
{
    (void)bus; (void)device; (void)function;
    ++commands;
    CHECK(offset == PCI_command && size == 2);
    return command;
}
static pci_module_info pci = { next, config };
status_t k40_os_init(k40_os* os)
{
    memset(os, 0, sizeof(*os)); os->mapping = -1; os->pci = &pci;
    return B_OK;
}
status_t k40_os_allocate(size_t size, k40_host_allocation* out)
{
    CHECK(size == B_PAGE_SIZE);
    memset(out, 0, sizeof(*out)); out->area = 1;
    out->address = scratch; out->bytes = size;
    return B_OK;
}
status_t k40_os_free(k40_host_allocation* out)
{
    memset(out, 0, sizeof(*out)); out->area = -1;
    return B_OK;
}
status_t k40_os_map_readonly(k40_os* os, const pci_info* info, unsigned bar, size_t size)
{
    (void)os; (void)info; ++maps;
    CHECK(command & PCI_command_memory);
    CHECK(bar == 0 && size == B_PAGE_SIZE);
    return B_OK;
}
status_t k40_os_read32(k40_os* os, size_t offset, uint32* value)
{
    (void)os; ++reads; CHECK(offset == 0); *value = identity;
    return B_OK;
}
status_t k40_os_close(k40_os* os) { os->pci = NULL; return B_OK; }
bigtime_t system_time(void) { static bigtime_t time; return ++time; }
status_t snooze(bigtime_t usecs) { (void)usecs; return B_OK; }

static void reset(void)
{
    maps = reads = commands = 0; log_text[0] = 0;
    present = true; command = PCI_command_memory; identity = 0x0f1240a1;
}
int main(void)
{
    reset(); CHECK(init_driver() == B_OK);
    CHECK(maps == 1 && reads == 1 && commands == 1);
    CHECK(strstr(log_text, "B5_IDENTITY_READ_ONLY") != NULL);
    CHECK(strstr(log_text, "PASS B5 identity reads only") != NULL);
    reset(); command = 0; CHECK(init_driver() == B_NOT_ALLOWED);
    CHECK(maps == 0 && reads == 0 && commands == 1);
    CHECK(strstr(log_text, "PASS") == NULL);
    reset(); present = false; CHECK(init_driver() == B_ENTRY_NOT_FOUND);
    CHECK(maps == 0 && reads == 0 && commands == 0);
    CHECK(strstr(log_text, "PASS") == NULL);
    reset(); identity = 0xffffffff; CHECK(init_driver() == B_IO_ERROR);
    CHECK(strstr(log_text, "PASS") == NULL);
    reset(); identity = 0; CHECK(init_driver() == B_BAD_DATA);
    CHECK(strstr(log_text, "PASS") == NULL);
    printf("Identity probe host spies: %u checks, %u failures; NOT hardware evidence\n", checks, failures);
    return failures ? 1 : 0;
}
