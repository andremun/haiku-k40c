// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "memory/Memory.h"
#include "os/HaikuBackend.h"
#include <array>

namespace k40::os {
struct DmaMapping {
    memory::DeviceIova address{0};
    uint64_t token = 0;
    bool verified = false;
};
class DmaProvider {
public:
    virtual ~DmaProvider() = default;
    // Implementations must supply independent device-address evidence.
    // No identity mapper or hardware visibility implementation is provided here.
    // A failed map must return a nonzero token for any partial owned mapping.
    virtual bool map(memory::GuestPhysical, uint64_t bytes, uint64_t alignment, DmaMapping&) = 0;
    virtual bool publish(const DmaMapping&, const void* cpu, uint64_t bytes) = 0;
    virtual bool unmap(const DmaMapping&) = 0;
};

// Caller-owned state must outlive all allocations, quarantine, and providers.
// Keep it across adapter recreation. Never unload its owner while it is nonempty.
// The caller must serialize pool, backend, and buffer operations.
class NativePool {
    friend class HaikuMemory;
    struct Slot {
        memory::Allocation allocation{};
        k40_host_allocation native{-1,nullptr,0,0};
        uint64_t displacement = 0;
        DmaMapping mapping{};
        DmaProvider* provider = nullptr;
        bool cpuReady = false, mappingOwned = false, releasing = false, quarantined = false;
    };
    // no source: software ownership-record capacity, not a GPU limit.
    static constexpr size_t capacity = 16;
    std::array<Slot, capacity> slots_{};
    uint64_t next_ = 1;
};

class HaikuMemory final : public memory::Backend {
public:
    struct Info {
        uint64_t token = 0, bytes = 0;
        memory::GuestPhysical physical{0};
        bool physicalKnown = false, mappingVerified = false, releasing = false, quarantined = false;
    };
    explicit HaikuMemory(NativePool& pool, DmaProvider* provider = nullptr) : pool_(pool), provider_(provider) {}
    // Host placement only. GPU VA and owned VRAM allocation are separate operations.
    bool allocate(uint64_t bytes, uint64_t alignment, memory::Placement, memory::Allocation&) override;
    bool write(const memory::Allocation&, uint64_t offset, const void*, size_t) override;
    bool read(const memory::Allocation&, uint64_t offset, void*, size_t) override;
    bool publish(const memory::Allocation&) override;
    bool release(const memory::Allocation&) override;
    void quarantine(const memory::Allocation&) override;
    // Diagnostic enumeration exposes GPA, never an invented device IOVA or CPU pointer.
    bool describe(size_t index, Info&) const;
    size_t ownedCount() const;
    size_t quarantinedCount() const;
    // Recovery requires external quiescence evidence and retains state on failure.
    bool recover(uint64_t token, bool quiescenceVerified);
private:
    NativePool::Slot* find(const memory::Allocation&);
    bool cleanup(NativePool::Slot&);
    bool range(const NativePool::Slot&, uint64_t offset, size_t bytes) const;
    NativePool& pool_;
    DmaProvider* provider_;
};
}
