// Copyright 2026 Mario Andrés Muñoz.
// Distributed under the terms of the MIT License.
#pragma once
#include <cstddef>
#include <cstdint>

namespace k40::memory {
// Distinct address domains: no implicit CPU-pointer/device-address conversion.
struct GuestPhysical { uint64_t value; };
struct DeviceIova { uint64_t value; };
struct VramPhysical { uint64_t value; };
struct GpuVirtual { uint64_t value; };
enum class Placement { Host, Vram };
struct Allocation {
    uint64_t id = 0; // Nonzero backend ownership token, not an address.
    uint64_t bytes = 0;
    Placement placement = Placement::Host;
    DeviceIova device{0};
    bool deviceAddressVerified = false;
    VramPhysical vram{0};
    bool vramAddressVerified = false;
};
class Backend {
public:
    virtual ~Backend() = default;
    // False may still return a partial nonzero ownership token: caller cleans it.
    virtual bool allocate(uint64_t bytes, uint64_t alignment, Placement, Allocation&) = 0;
    virtual bool write(const Allocation&, uint64_t offset, const void*, size_t) = 0;
    virtual bool read(const Allocation&, uint64_t offset, void*, size_t) = 0;
    // Upload/device visibility and all required cache/bus flushes, not merely
    // a compiler fence. False leaves storage dirty and forbids submission.
    virtual bool publish(const Allocation&) = 0;
    virtual bool release(const Allocation&) = 0;
    // Transfer ownership to a recovery list. Must NOT free this storage. The
    // backend outlives Buffer objects and records why recovery is required.
    virtual void quarantine(const Allocation&) = 0;
};
class Buffer {
public:
    explicit Buffer(Backend& backend) : backend_(backend) {}
    ~Buffer();
    Buffer(const Buffer&) = delete;
    Buffer& operator=(const Buffer&) = delete;
    bool allocate(uint64_t bytes, uint64_t alignment, Placement);
    bool write(uint64_t offset, const void*, size_t);
    bool read(uint64_t offset, void*, size_t);
    bool publish();
    bool deviceAddress(DeviceIova&) const;
    bool vramAddress(VramPhysical&) const;
    // A GPU virtual mapping is a separate backend/MMU operation. This class
    // does not invent one from an IOVA, CPU pointer or captured address.
    bool pinForSubmission();
    bool retire(bool quiescenceVerified);
    bool close();
    bool owned() const { return allocation_.id != 0; }
    uint64_t bytes() const { return allocation_.bytes; }
    bool pinned() const { return pinned_; }
    bool visible() const { return owned() && published_ && !releaseFailed_; }
private:
    bool range(uint64_t offset, size_t bytes) const;
    Backend& backend_;
    Allocation allocation_{};
    bool published_ = false;
    bool pinned_ = false;
    // A failed release may already have removed a device mapping.
    // Only another close attempt is allowed until ownership is discharged.
    bool releaseFailed_ = false;
};
} // namespace k40::memory
