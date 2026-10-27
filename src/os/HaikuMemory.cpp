// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "os/HaikuMemory.h"
#include <cstring>

namespace k40::os {
namespace {
bool same(const memory::Allocation& a, const memory::Allocation& b)
{
    return a.id == b.id && a.bytes == b.bytes && a.placement == b.placement
        && a.device.value == b.device.value && a.deviceAddressVerified == b.deviceAddressVerified
        && a.vram.value == b.vram.value && a.vramAddressVerified == b.vramAddressVerified;
}
}

bool HaikuMemory::allocate(uint64_t bytes, uint64_t alignment, memory::Placement placement,
                           memory::Allocation& out)
{
    out = {};
    if (placement != memory::Placement::Host || !bytes || !alignment || (alignment & (alignment - 1))
        || bytes > SIZE_MAX || alignment - 1 > SIZE_MAX - bytes || pool_.next_ == UINT64_MAX)
        return false;
    const uint64_t request = bytes + alignment - 1;
    // OS.h:77 guarantees a contiguous guest physical extent below 4 GiB.
    // This bound says nothing about the device IOVA or the GPU address width.
    if (request > uint64_t(UINT32_MAX) + 1) return false;
    NativePool::Slot* slot = nullptr;
    for (auto& candidate : pool_.slots_) if (!candidate.allocation.id) { slot = &candidate; break; }
    if (!slot) return false;
    *slot = {};
    slot->allocation.id = pool_.next_++;
    slot->allocation.bytes = bytes;
    slot->provider = provider_;
    const auto status = k40_os_allocate_dma32(size_t(request), &slot->native);
    if (slot->native.area < 0) { *slot = {}; return false; }
    out = slot->allocation; // Own partial native allocations before any later check.
    if (status != B_OK || !slot->native.address || slot->native.bytes < request
        || slot->native.guest_physical > UINT32_MAX
        || slot->native.bytes > uint64_t(UINT32_MAX) + 1 - slot->native.guest_physical)
        return false;
    const uint64_t physical = slot->native.guest_physical;
    if (physical > UINT64_MAX - (alignment - 1)) return false;
    const uint64_t aligned = (physical + alignment - 1) & ~(alignment - 1);
    slot->displacement = aligned - physical;
    if (slot->displacement > slot->native.bytes || bytes > slot->native.bytes - slot->displacement)
        return false;
    slot->cpuReady = true;
    if (provider_) {
        const bool mapped = provider_->map({aligned}, bytes, alignment, slot->mapping);
        slot->mappingOwned = slot->mapping.token != 0;
        if (!mapped) return false;
        if (slot->mapping.verified && (!slot->mappingOwned || slot->mapping.address.value & (alignment - 1)
            || bytes > UINT64_MAX - slot->mapping.address.value)) return false;
        slot->allocation.device = slot->mapping.address;
        slot->allocation.deviceAddressVerified = slot->mapping.verified;
        out = slot->allocation;
    }
    return true;
}

NativePool::Slot* HaikuMemory::find(const memory::Allocation& allocation)
{
    if (!allocation.id) return nullptr;
    for (auto& slot : pool_.slots_)
        if (same(slot.allocation, allocation)) return &slot;
    return nullptr;
}
bool HaikuMemory::range(const NativePool::Slot& slot, uint64_t offset, size_t bytes) const
{
    return slot.cpuReady && !slot.releasing && !slot.quarantined && offset <= slot.allocation.bytes
        && bytes <= slot.allocation.bytes - offset;
}
bool HaikuMemory::write(const memory::Allocation& allocation, uint64_t offset, const void* data, size_t bytes)
{
    auto* slot = find(allocation);
    if (!slot || !range(*slot, offset, bytes) || (bytes && !data)) return false;
    if (bytes) std::memcpy(static_cast<uint8_t*>(slot->native.address) + slot->displacement + offset, data, bytes);
    return true;
}
bool HaikuMemory::read(const memory::Allocation& allocation, uint64_t offset, void* data, size_t bytes)
{
    auto* slot = find(allocation);
    if (!slot || !range(*slot, offset, bytes) || (bytes && !data)) return false;
    if (bytes) std::memcpy(data, static_cast<uint8_t*>(slot->native.address) + slot->displacement + offset, bytes);
    return true;
}
bool HaikuMemory::publish(const memory::Allocation& allocation)
{
    auto* slot = find(allocation);
    if (!slot || !slot->cpuReady || slot->releasing || slot->quarantined || !slot->mappingOwned
        || !slot->mapping.verified || !slot->provider) return false;
    return slot->provider->publish(slot->mapping,
        static_cast<uint8_t*>(slot->native.address) + slot->displacement, allocation.bytes);
}
bool HaikuMemory::cleanup(NativePool::Slot& slot)
{
    slot.releasing = true;
    if (slot.mappingOwned) {
        if (!slot.provider || !slot.provider->unmap(slot.mapping)) return false;
        slot.mappingOwned = false;
    }
    if (k40_os_free(&slot.native) != B_OK) return false;
    slot = {};
    return true;
}
bool HaikuMemory::release(const memory::Allocation& allocation)
{
    auto* slot = find(allocation);
    return slot && !slot->quarantined && cleanup(*slot);
}
void HaikuMemory::quarantine(const memory::Allocation& allocation)
{
    if (auto* slot = find(allocation)) slot->quarantined = true;
}
bool HaikuMemory::recover(uint64_t token, bool quiescenceVerified)
{
    if (!token || !quiescenceVerified) return false;
    for (auto& slot : pool_.slots_)
        if (slot.allocation.id == token && slot.quarantined) return cleanup(slot);
    return false;
}
bool HaikuMemory::describe(size_t index, Info& out) const
{
    out = {};
    if (index >= pool_.slots_.size()) return false;
    const auto& slot = pool_.slots_[index];
    if (!slot.allocation.id) return false;
    out.token = slot.allocation.id;
    out.bytes = slot.allocation.bytes;
    out.physicalKnown = slot.cpuReady;
    if (slot.cpuReady) out.physical = {slot.native.guest_physical + slot.displacement};
    out.releasing = slot.releasing;
    out.quarantined = slot.quarantined;
    out.mappingVerified = slot.mapping.verified && slot.mappingOwned && !slot.releasing && !slot.quarantined;
    return true;
}
size_t HaikuMemory::ownedCount() const
{
    size_t count = 0;
    for (const auto& slot : pool_.slots_) count += slot.allocation.id != 0;
    return count;
}
size_t HaikuMemory::quarantinedCount() const
{
    size_t count = 0;
    for (const auto& slot : pool_.slots_) count += slot.quarantined;
    return count;
}
}
