// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "os/NativeOwner.h"
namespace k40::os {
OwnerError NativeOwner::acquire(uint64_t& lease)
{
    lease = 0;
    Guard guard(lock_);
    if (!guard.held || lease_) return OwnerError::Busy;
    if (nextLease_ == UINT64_MAX) return OwnerError::Exhausted;
    lease = lease_ = nextLease_++;
    return OwnerError::None;
}
memory::Allocation* NativeOwner::find(uint64_t token)
{
    if (!token) return nullptr;
    for (auto& allocation : allocations_) if (allocation.id == token) return &allocation;
    return nullptr;
}
OwnerError NativeOwner::detach(uint64_t lease)
{
    Guard guard(lock_);
    if (!guard.held) return OwnerError::Busy;
    if (!valid(lease)) return OwnerError::Lease;
    if (startup_.state() == runtime::startup::BootState::Running) startup_.finish(false);
    // Once startup was attempted, storage may have references outside the driver.
    // This owner exposes no guessed quiescence/recovery override.
    for (auto& allocation : allocations_) if (allocation.id) {
        if (!fresh() || !memory_.release(allocation)) memory_.quarantine(allocation);
        allocation = {};
    }
    lease_ = 0;
    return memory_.ownedCount() ? OwnerError::Retained : OwnerError::None;
}
OwnerError NativeOwner::allocate(uint64_t lease, uint64_t bytes, uint64_t alignment, uint64_t& token)
{
    token = 0;
    Guard guard(lock_);
    if (!guard.held) return OwnerError::Busy;
    if (!valid(lease)) return OwnerError::Lease;
    if (!fresh() || memory_.quarantinedCount()) return OwnerError::Retained;
    memory::Allocation* record = nullptr;
    for (auto& candidate : allocations_) if (!candidate.id) { record = &candidate; break; }
    if (!record) return OwnerError::Exhausted;
    if (!memory_.allocate(bytes, alignment, memory::Placement::Host, *record)) {
        if (record->id && !memory_.release(*record)) memory_.quarantine(*record);
        *record = {};
        return OwnerError::Io;
    }
    token = record->id;
    return OwnerError::None;
}
OwnerError NativeOwner::write(uint64_t lease, uint64_t token, uint64_t offset, const void* data, size_t bytes)
{
    Guard guard(lock_);
    if (!guard.held) return OwnerError::Busy;
    if (!valid(lease)) return OwnerError::Lease;
    if (!fresh()) return OwnerError::Retained;
    auto* allocation = find(token);
    return allocation && memory_.write(*allocation, offset, data, bytes) ? OwnerError::None : OwnerError::Io;
}
OwnerError NativeOwner::read(uint64_t lease, uint64_t token, uint64_t offset, void* data, size_t bytes)
{
    Guard guard(lock_);
    if (!guard.held) return OwnerError::Busy;
    if (!valid(lease)) return OwnerError::Lease;
    if (!fresh()) return OwnerError::Retained;
    auto* allocation = find(token);
    return allocation && memory_.read(*allocation, offset, data, bytes) ? OwnerError::None : OwnerError::Io;
}
OwnerError NativeOwner::release(uint64_t lease, uint64_t token)
{
    Guard guard(lock_);
    if (!guard.held) return OwnerError::Busy;
    if (!valid(lease)) return OwnerError::Lease;
    if (!fresh()) return OwnerError::Retained;
    auto* allocation = find(token);
    if (!allocation) return OwnerError::Input;
    if (!memory_.release(*allocation)) return OwnerError::Io;
    *allocation = {};
    return OwnerError::None;
}
OwnerError NativeOwner::publish(uint64_t lease, uint64_t token)
{
    Guard guard(lock_);
    if (!guard.held) return OwnerError::Busy;
    if (!valid(lease)) return OwnerError::Lease;
    if (!find(token)) return OwnerError::Input;
    // Allocation, GPA, and module residency provide no DMA/visibility proof.
    return OwnerError::DmaDenied;
}
OwnerError NativeOwner::begin(uint64_t lease)
{
    Guard guard(lock_);
    if (!guard.held) return OwnerError::Busy;
    if (!valid(lease)) return OwnerError::Lease;
    if (memory_.quarantinedCount()) return OwnerError::Retained;
    return startup_.begin() ? OwnerError::None : OwnerError::Startup;
}
OwnerError NativeOwner::finish(uint64_t lease, bool success)
{
    Guard guard(lock_);
    if (!guard.held) return OwnerError::Busy;
    if (!valid(lease)) return OwnerError::Lease;
    return startup_.finish(success) ? OwnerError::None : OwnerError::Startup;
}
OwnerError NativeOwner::inspect(OwnerInfo& info)
{
    info = {};
    Guard guard(lock_);
    if (!guard.held) return OwnerError::Busy;
    info = {lease_, memory_.ownedCount(), memory_.quarantinedCount(), startup_.state()};
    return OwnerError::None;
}
OwnerError NativeOwner::describe(uint64_t lease, size_t index, HaikuMemory::Info& info)
{
    info = {};
    Guard guard(lock_);
    if (!guard.held) return OwnerError::Busy;
    if (!valid(lease)) return OwnerError::Lease;
    return memory_.describe(index, info) ? OwnerError::None : OwnerError::Input;
}
}
