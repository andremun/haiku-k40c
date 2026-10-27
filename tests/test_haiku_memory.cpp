// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Native adapter contracts with host allocator/mapping spies. No Haiku ABI claim.
#include "os/HaikuMemory.h"
#include <cstdio>
#include <map>
#include <vector>
using namespace k40;
static unsigned checks = 0, failed = 0, allocs = 0, frees = 0;
static bool allocateOk = true, partial = false, freeOk = true, shortExtent = false;
static uint64_t physical = 0x10001000;
static int nextArea = 1;
static std::map<int, std::vector<uint8_t>> areas;
static std::vector<char> order;
#define CHECK(c) do { ++checks; if (!(c)) { ++failed; std::printf("FAIL %d: %s\n", __LINE__, #c); } } while (0)

extern "C" status_t k40_os_allocate_dma32(size_t size, k40_host_allocation* out)
{
    ++allocs; *out = {-1,nullptr,0,0};
    if (!allocateOk && !partial) return B_ERROR;
    const size_t rounded = (size + B_PAGE_SIZE - 1) & ~(size_t)(B_PAGE_SIZE - 1);
    const int area = nextArea++;
    areas[area].resize(rounded);
    *out = {area, areas[area].data(), shortExtent ? size - 1 : rounded, physical};
    return allocateOk ? B_OK : B_ERROR;
}
extern "C" status_t k40_os_free(k40_host_allocation* allocation)
{
    ++frees; order.push_back('F');
    if (!freeOk) return B_ERROR;
    CHECK(areas.erase(allocation->area) == 1);
    *allocation = {-1,nullptr,0,0};
    return B_OK;
}
struct Mapper : os::DmaProvider {
    bool mapOk = true, verified = true, publishOk = true, unmapOk = true, partialMap = false;
    unsigned maps = 0, publications = 0, unmaps = 0;
    uint64_t device = 0x20000000;
    memory::GuestPhysical observed{0};
    bool map(memory::GuestPhysical at, uint64_t bytes, uint64_t alignment, os::DmaMapping& out) override {
        ++maps; observed = at;
        CHECK(bytes > 0 && !(at.value & (alignment - 1)));
        out = {{device}, mapOk || partialMap ? 99u : 0u, verified};
        return mapOk;
    }
    bool publish(const os::DmaMapping& mapping, const void* pointer, uint64_t bytes) override {
        ++publications; order.push_back('P'); CHECK(mapping.token == 99 && pointer && bytes);
        return publishOk;
    }
    bool unmap(const os::DmaMapping& mapping) override {
        ++unmaps; order.push_back('U'); CHECK(mapping.token == 99);
        return unmapOk;
    }
};
static void reset()
{
    CHECK(areas.empty()); allocs = frees = 0; order.clear();
    allocateOk = freeOk = true; partial = shortExtent = false; physical = 0x10001000;
}
int main()
{
    {
        reset(); os::NativePool pool; os::HaikuMemory backend(pool); memory::Buffer buffer(backend);
        CHECK(buffer.allocate(513, 65536, memory::Placement::Host));
        os::HaikuMemory::Info info;
        CHECK(backend.describe(0, info) && info.physicalKnown && info.physical.value == 0x10010000);
        CHECK(info.bytes == 513 && !info.mappingVerified && backend.ownedCount() == 1);
        const unsigned value = 123456; unsigned got = 0;
        CHECK(buffer.write(509, &value, 4) && buffer.read(509, &got, 4) && got == value);
        CHECK(!buffer.write(510, &value, 4) && !buffer.read(UINT64_MAX, &got, 1));
        CHECK(!buffer.publish() && !buffer.pinForSubmission());
        memory::DeviceIova device{0}; CHECK(!buffer.deviceAddress(device));
        CHECK(buffer.close() && backend.ownedCount() == 0 && frees == 1);
    }
    {
        reset(); os::NativePool pool; Mapper mapper; os::HaikuMemory backend(pool, &mapper);
        memory::Buffer buffer(backend); CHECK(buffer.allocate(64, 4096, memory::Placement::Host));
        CHECK(mapper.observed.value == physical && mapper.observed.value != mapper.device);
        memory::DeviceIova device{0}; CHECK(buffer.deviceAddress(device) && device.value == mapper.device);
        CHECK(buffer.publish() && buffer.pinForSubmission());
        CHECK(!buffer.close() && frees == 0 && mapper.unmaps == 0);
        CHECK(buffer.retire(true) && buffer.close());
        CHECK(order.size() == 3 && order[0] == 'P' && order[1] == 'U' && order[2] == 'F');
    }
    {
        reset(); os::NativePool pool; Mapper mapper; mapper.verified = false;
        os::HaikuMemory backend(pool, &mapper); memory::Buffer buffer(backend);
        CHECK(buffer.allocate(64, 4096, memory::Placement::Host));
        CHECK(!buffer.publish() && mapper.publications == 0 && !buffer.pinForSubmission());
        CHECK(buffer.close() && mapper.unmaps == 1);
    }
    {
        reset(); os::NativePool pool; Mapper mapper; mapper.publishOk = false;
        os::HaikuMemory backend(pool, &mapper); memory::Buffer buffer(backend);
        CHECK(buffer.allocate(64, 4096, memory::Placement::Host));
        CHECK(!buffer.publish() && !buffer.visible() && !buffer.pinForSubmission());
        CHECK(buffer.close());
    }
    {
        reset(); allocateOk = false; partial = true; freeOk = false;
        os::NativePool pool;
        uint64_t retained = 0;
        {
            os::HaikuMemory backend(pool); memory::Buffer buffer(backend);
            CHECK(!buffer.allocate(64, 4096, memory::Placement::Host));
            CHECK(backend.quarantinedCount() == 1 && frees == 1);
            os::HaikuMemory::Info info; CHECK(backend.describe(0, info)); retained = info.token;
            CHECK(!info.physicalKnown && info.quarantined);
        }
        // The caller-owned pool survives destruction of the adapter and buffer.
        os::HaikuMemory recovery(pool); freeOk = true;
        CHECK(!recovery.recover(retained, false) && recovery.quarantinedCount() == 1);
        CHECK(recovery.recover(retained, true) && recovery.ownedCount() == 0);
    }
    {
        reset(); os::NativePool pool; Mapper mapper; mapper.mapOk = false; mapper.partialMap = true;
        mapper.unmapOk = false; os::HaikuMemory backend(pool, &mapper); memory::Buffer buffer(backend);
        CHECK(!buffer.allocate(64, 4096, memory::Placement::Host));
        CHECK(frees == 0 && mapper.unmaps == 1 && backend.quarantinedCount() == 1);
        os::HaikuMemory::Info info; CHECK(backend.describe(0, info)); mapper.unmapOk = true;
        CHECK(backend.recover(info.token, true) && frees == 1);
    }
    {
        reset(); os::NativePool pool; Mapper mapper; os::HaikuMemory backend(pool, &mapper);
        memory::Buffer buffer(backend); CHECK(buffer.allocate(64, 4096, memory::Placement::Host));
        CHECK(buffer.publish()); freeOk = false;
        CHECK(!buffer.close() && buffer.owned() && !buffer.visible());
        CHECK(mapper.unmaps == 1 && frees == 1);
        memory::DeviceIova address{0}; CHECK(!buffer.deviceAddress(address) && !buffer.pinForSubmission());
        CHECK(!buffer.publish() && mapper.publications == 1);
        freeOk = true; CHECK(buffer.close() && mapper.unmaps == 1 && frees == 2);
    }
    {
        reset(); os::NativePool pool; Mapper mapper; os::HaikuMemory backend(pool, &mapper);
        memory::Allocation allocation;
        CHECK(backend.allocate(64, 4096, memory::Placement::Host, allocation));
        auto forged = allocation; ++forged.bytes; unsigned data = 0;
        CHECK(!backend.read(forged, 0, &data, 4) && !backend.release(forged));
        backend.quarantine(allocation);
        CHECK(backend.quarantinedCount() == 1 && !backend.write(allocation, 0, &data, 4));
        CHECK(!backend.release(allocation) && !backend.publish(allocation));
        CHECK(backend.recover(allocation.id, true));
        CHECK(!backend.read(allocation, 0, &data, 4));
        memory::Allocation replacement; CHECK(backend.allocate(64, 4096, memory::Placement::Host, replacement));
        CHECK(replacement.id != allocation.id && !backend.release(allocation)); CHECK(backend.release(replacement));
    }
    {
        reset(); os::NativePool pool; os::HaikuMemory backend(pool); memory::Allocation allocation;
        CHECK(!backend.allocate(64, 3, memory::Placement::Host, allocation));
        CHECK(!backend.allocate(UINT64_MAX, 4096, memory::Placement::Host, allocation));
        CHECK(!backend.allocate(64, 4096, memory::Placement::Vram, allocation));
        CHECK(!backend.allocate(64, uint64_t(1) << 40, memory::Placement::Host, allocation));
        CHECK(allocs == 0);
        shortExtent = true; CHECK(!backend.allocate(64, 4096, memory::Placement::Host, allocation));
        CHECK(allocation.id != 0 && backend.release(allocation));
        shortExtent = false; physical = uint64_t(UINT32_MAX) - 31;
        CHECK(!backend.allocate(64, 4096, memory::Placement::Host, allocation));
        CHECK(allocation.id != 0 && backend.release(allocation));
    }
    {
        reset(); os::NativePool pool; os::HaikuMemory backend(pool);
        std::vector<memory::Allocation> retained;
        memory::Allocation allocation;
        while (backend.allocate(64, 4096, memory::Placement::Host, allocation)) {
            retained.push_back(allocation);
            CHECK(retained.size() <= 16);
        }
        CHECK(retained.size() == 16 && backend.ownedCount() == 16 && allocs == 16);
        for (const auto& owned : retained) CHECK(backend.release(owned));
        CHECK(backend.ownedCount() == 0);
    }
    CHECK(areas.empty());
    std::printf("Haiku memory adapter: %u checks, %u failures (HOST_ONLY)\n", checks, failed);
    return failed ? 1 : 0;
}
