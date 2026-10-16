// Copyright 2026 Mario Andrés Muñoz.
// Distributed under the terms of the MIT License.
#include "memory/Memory.h"

namespace k40::memory {
Buffer::~Buffer()
{
    if (owned() && (pinned_ || !backend_.release(allocation_)))
        backend_.quarantine(allocation_);
}
bool Buffer::allocate(uint64_t bytes, uint64_t alignment, Placement placement)
{
    if ((placement!=Placement::Host && placement!=Placement::Vram) || owned() || !bytes || !alignment || (alignment & (alignment - 1))) return false;
    Allocation result;
    bool ok = backend_.allocate(bytes, alignment, placement, result);
    if (result.id) allocation_ = result; // Own partial allocations immediately.
    const bool verified = placement == Placement::Host ? result.deviceAddressVerified : result.vramAddressVerified;
    const uint64_t address = placement == Placement::Host ? result.device.value : result.vram.value;
    if (!ok || !result.id || result.bytes < bytes || result.placement != placement
        || (verified
            && ((address & (alignment - 1)) || result.bytes > UINT64_MAX - address))) {
        if (owned() && !backend_.release(allocation_)) backend_.quarantine(allocation_);
        allocation_ = {};
        return false;
    }
    return true;
}
bool Buffer::range(uint64_t offset, size_t bytes) const
{
    return owned() && offset <= allocation_.bytes && bytes <= allocation_.bytes - offset;
}
bool Buffer::write(uint64_t offset, const void* data, size_t bytes)
{
    if (pinned_ || !range(offset, bytes) || (bytes && !data)) return false;
    published_ = false; // A failed partial write must also invalidate visibility.
    return backend_.write(allocation_, offset, data, bytes);
}
bool Buffer::read(uint64_t offset, void* data, size_t bytes)
{
    if (pinned_ || !range(offset, bytes) || (bytes && !data)) return false;
    return backend_.read(allocation_, offset, data, bytes);
}
bool Buffer::publish()
{
    if (!owned() || pinned_) return false;
    published_ = backend_.publish(allocation_);
    return published_;
}
bool Buffer::deviceAddress(DeviceIova& address) const
{
    if (!owned() || allocation_.placement != Placement::Host || !allocation_.deviceAddressVerified) return false;
    address = allocation_.device;
    return true;
}
bool Buffer::vramAddress(VramPhysical& address) const
{
    if (!owned() || allocation_.placement != Placement::Vram || !allocation_.vramAddressVerified) return false;
    address = allocation_.vram;
    return true;
}
bool Buffer::pinForSubmission()
{
    const bool verified = allocation_.placement == Placement::Host
        ? allocation_.deviceAddressVerified : allocation_.vramAddressVerified;
    if (!visible() || pinned_ || !verified) return false;
    pinned_ = true;
    return true;
}
bool Buffer::retire(bool quiescenceVerified)
{
    if (!pinned_ || !quiescenceVerified) return false;
    pinned_ = false;
    return true;
}
bool Buffer::close()
{
    if (!owned() || pinned_ || !backend_.release(allocation_)) return false;
    allocation_ = {};
    published_ = false;
    return true;
}
} // namespace k40::memory
