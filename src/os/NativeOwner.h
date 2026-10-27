// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "os/HaikuMemory.h"
#include "runtime/BootState.h"
#include "devinit/PostImage.h"
#include <atomic>

namespace k40::devinit { class BoardTransport; }
namespace k40::os {
enum class OwnerError { None, Busy, Lease, Input, Exhausted, Io, Retained, Startup, DmaDenied };
struct OwnerInfo {
    uint64_t lease = 0;
    size_t owned = 0, quarantined = 0;
    runtime::startup::BootState startup = runtime::startup::BootState::Fresh;
};
struct OwnerPostInfo {
    bool bindingAttempted = false, bound = false, selectionAttempted = false;
    bool executionAttempted = false, ramSelected = false;
    uint8_t ramIndex = 0;
    devinit::Error selection = devinit::Error::Input;
    devinit::Result result{devinit::Error::Input,0,0};
};
// Boot-lifetime object in a separate KEEP_LOADED module, never in driver storage.
// No external provider, object pointer, or driver callback is retained.
class NativeOwner {
public:
    NativeOwner() = default;
    ~NativeOwner() = delete; // Boot lifetime; no destructor may erase quarantine.
    OwnerError acquire(uint64_t& lease);
    OwnerError detach(uint64_t lease);
    OwnerError allocate(uint64_t lease, uint64_t bytes, uint64_t alignment, uint64_t& token);
    OwnerError write(uint64_t lease, uint64_t token, uint64_t offset, const void*, size_t);
    OwnerError read(uint64_t lease, uint64_t token, uint64_t offset, void*, size_t);
    OwnerError release(uint64_t lease, uint64_t token);
    OwnerError publish(uint64_t lease, uint64_t token);
    OwnerError begin(uint64_t lease);
    OwnerError finish(uint64_t lease, bool success);
    OwnerError inspect(OwnerInfo&);
    OwnerError describe(uint64_t lease, size_t index, HaikuMemory::Info&);
    OwnerError bindPost(uint64_t lease, const uint8_t* rom, uint32_t bytes);
    OwnerError inspectPost(uint64_t lease, OwnerPostInfo&);
#ifndef _KERNEL_MODE
    // Host fixture only. No declaration, implementation or C ABI in kernel builds.
    // All callback references live only for this serialized synchronous call.
    OwnerError simulatePost(uint64_t lease, devinit::Backend&, devinit::BoardTransport&,
                            devinit::Limits limits = {});
#endif
private:
    struct Guard {
        std::atomic_flag& flag;
        bool held;
        explicit Guard(std::atomic_flag& flag) : flag(flag), held(!flag.test_and_set(std::memory_order_acquire)) {}
        ~Guard() { if (held) flag.clear(std::memory_order_release); }
    };
    bool valid(uint64_t lease) const { return lease && lease == lease_; }
    bool fresh() const { return startup_.state() == runtime::startup::BootState::Fresh; }
    memory::Allocation* find(uint64_t token);
    // Resident storage, not a kernel-stack object. Construct once after validation.
    alignas(devinit::PostImage) unsigned char postStorage_[sizeof(devinit::PostImage)];
    devinit::PostImage* post_ = nullptr;
    OwnerPostInfo postInfo_;
    NativePool pool_;
    HaikuMemory memory_{pool_}; // Default denied; no DmaProvider installation API.
    runtime::startup::OncePerBoot startup_;
    // no source: software handle capacity, equal to NativePool capacity.
    std::array<memory::Allocation, 16> allocations_{};
    uint64_t lease_ = 0, nextLease_ = 1;
    std::atomic_flag lock_ = ATOMIC_FLAG_INIT;
};
}
