// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Cardless native memory probe. No PCI enumeration, BAR mapping, or device IOVA.
#include "os/HaikuMemory.h"
#include <Drivers.h>
#include <cstring>

static k40::os::NativePool pool;
static const char* devices[] = {nullptr};

static bool exercise(k40::os::HaikuMemory& backend)
{
    k40::memory::Buffer buffer(backend);
    if (!buffer.allocate(513, 65536, k40::memory::Placement::Host)) return false;
    k40::os::HaikuMemory::Info info;
    if (!backend.describe(0, info) || !info.physicalKnown || info.physical.value % 65536
        || info.physical.value > UINT32_MAX || info.mappingVerified) return false;
    dprintf("k40_memory: bytes %llu, aligned GPA 0x%llx; IOVA unverified\n",
        (unsigned long long)info.bytes, (unsigned long long)info.physical.value);
    unsigned char input[513], output[513];
    for (unsigned i = 0; i < sizeof(input); ++i) input[i] = (unsigned char)(i * 37 + 11);
    if (!buffer.write(0, input, sizeof(input)) || !buffer.read(0, output, sizeof(output))
        || std::memcmp(input, output, sizeof(input))) return false;
    k40::memory::DeviceIova address{0};
    if (buffer.deviceAddress(address) || buffer.publish() || buffer.pinForSubmission()) return false;
    if (!buffer.close()) return false;
    return backend.ownedCount() == 0 && backend.quarantinedCount() == 0;
}

extern "C" {
int32 api_version = B_CUR_DRIVER_API_VERSION;
status_t init_hardware(void) { return B_OK; }
status_t init_driver(void)
{
    dprintf("k40_stage: CARDLESS_MEMORY_ONLY\n");
    k40::os::HaikuMemory backend(pool);
    if (backend.ownedCount() || !exercise(backend)) {
        dprintf("k40_os: FAIL native memory adapter, owned %lu, quarantined %lu\n",
            (unsigned long)backend.ownedCount(), (unsigned long)backend.quarantinedCount());
        return B_ERROR;
    }
    dprintf("k40_os: PASS native memory adapter only; IOVA unverified\n");
    return B_OK;
}
void uninit_driver(void)
{
    k40::os::HaikuMemory backend(pool);
    if (backend.ownedCount()) dprintf("k40_memory: retained ownership; guest recovery required\n");
}
const char** publish_devices(void) { return devices; }
device_hooks* find_device(const char* name) { (void)name; return nullptr; }
}
