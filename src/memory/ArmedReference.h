// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "memory/Memory.h"
namespace k40::a7 { class ArmAuthority; }
namespace k40::memory {
struct ArmAllocation { uint64_t token=0, bytes=0; GuestPhysical physical{0}; };
class ArmStorage {
public:
    virtual ~ArmStorage()=default;
    // Native implementation owns DMA32 backing and zeros it before returning.
    virtual bool reserveZeroed(ArmAllocation&)=0;
    // Boot-lifetime retention only. There is deliberately no release operation.
    virtual void retain(const ArmAllocation&)=0;
};
class ArmGrant {
    friend class k40::a7::ArmAuthority;
    friend class ArmedReference;
    ArmGrant(uint64_t token,GuestPhysical gpa,DeviceIova iova,uint64_t bytes)
        : token_(token),gpa_(gpa),iova_(iova),bytes_(bytes) {}
    uint64_t token_; GuestPhysical gpa_; DeviceIova iova_; uint64_t bytes_;
public:
#ifndef _KERNEL_MODE
    // Synthetic host fixtures only. This constructor is absent from kernel builds.
    static ArmGrant hostFixture(uint64_t token,GuestPhysical gpa,DeviceIova iova,uint64_t bytes)
    { return ArmGrant(token,gpa,iova,bytes); }
#endif
};
// A retained address reference, never a published/pinned payload Buffer.
class ArmedReference {
public:
    enum class State { Empty, Prepared, Bound, Armed, Failed };
    explicit ArmedReference(ArmStorage& storage):storage_(storage) {}
    ~ArmedReference();
    ArmedReference(const ArmedReference&)=delete;
    ArmedReference& operator=(const ArmedReference&)=delete;
    bool prepare();
    bool bind(const ArmGrant&);
    bool beginArm(DeviceIova&);
    void fail();
    State state() const { return state_; }
    ArmAllocation allocation() const { return owned_; }
    bool armed() const { return state_==State::Armed; }
private:
    void retain();
    ArmStorage& storage_;
    ArmAllocation owned_{};
    DeviceIova address_{0};
    State state_=State::Empty;
    bool retained_=false;
};
}
