// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "a7/ArmAuthority.h"
#include "devinit/BoundPost.h"
#include "runtime/PreStart.h"
#include "runtime/Bootstrap.h"
#include <atomic>
namespace k40::a7 {
// The native module owns this platform for its entire lifetime. Clients supply
// no platform pointer, callbacks, ROM, execution permit or memory-provider object.
class Platform {
    friend class Owner;
    const ExecutionPermit* permit_=nullptr;
    void bindPermit(const ExecutionPermit& permit) { permit_=&permit; }
protected:
    bool writesAuthorized() const { return permit_ && permit_->active(); }
public:
    virtual ~Platform()=default;
    virtual bool initialize()=0;
    virtual bool pciCommand(uint16_t&)=0;
    virtual uint64_t nowUs()=0;
    virtual bool delayUs(uint64_t)=0;
    virtual bool read32(uint32_t,uint32_t&)=0;
    virtual bool write32(uint32_t,uint32_t)=0;
    virtual bool read8(uint32_t,uint8_t&)=0;
    virtual bool write8(uint32_t,uint8_t)=0;
    virtual void log(const char*,uint64_t,uint64_t=0)=0;
};
enum class Status { Ok, Busy, Retained, Input, Authentication, Io, Post };
struct Outcome {
    runtime::startup::Result startup{};
    uint64_t timerBefore=0,timerAfter=0,vramBytes=0;
    uint16_t pciBefore=0;
    uint32_t pending=0;
    bool scratch=false;
};
class Owner {
#ifndef _KERNEL_MODE
    friend struct OwnerBoundaryProbe; // Host-only negative tests of the actual private boundary.
#endif
public:
    Owner(Platform&,memory::ArmStorage&,const uint8_t key[32],const uint8_t nonce[32],const uint8_t challenge[16],
          const uint8_t* rom,uint32_t bytes,uint64_t expectedVram);
#ifdef _KERNEL_MODE
    ~Owner()=delete;
#else
    ~Owner()=default;
#endif
    Status prepare(uint64_t& lease,uint8_t request[requestBytes]);
    Status submit(uint64_t lease,const uint8_t*,size_t);
    Status detach(uint64_t lease);
    Outcome outcome() const { return outcome_; }
    runtime::startup::BootState state() const { return once_.state(); }
private:
    class Transport final:public devinit::Backend,public devinit::BoardTransport,
                          public runtime::startup::Backend,public runtime::BootstrapPort {
#ifndef _KERNEL_MODE
        friend struct OwnerBoundaryProbe;
#endif
    public:
        explicit Transport(Owner& owner):owner_(owner),helpers_(*this,*this) {}
        bool hostSimulation() const override { return false; }
        const ExecutionPermit* a7Permit() const override { return &owner_.permit_; }
        uint64_t nowUs() override { return owner_.platform_.nowUs(); }
        bool delayUs(uint64_t) override;
        bool read32(uint32_t,uint32_t&) override;
        bool write32(uint32_t,uint32_t) override;
        bool read8(uint32_t,uint8_t&) override;
        bool write8(uint32_t,uint8_t) override;
        bool i2cWrite(const devinit::I2cBus&,uint8_t,uint8_t,uint8_t) override { return false; }
        void trace(uint32_t,uint8_t,bool) override;
        bool romPolicyReady() const override { return owner_.image_.approved(); }
        bool identity() override;
        bool unarmInterrupts() override;
        bool postRequired(bool&) override;
        bool unlockCrtc() override;
        bool privateRing() override;
        bool initializeI2c() override;
        bool programFlushPage(memory::DeviceIova) override;
        bool resetFifoBeforePost() override;
        bool executeRom() override;
        bool readFlushPage(uint32_t&) override;
        bool independentReadiness() override;
        bool lock() override { if(windowLocked_)return false;windowLocked_=true;return true; }
        void unlock() override { windowLocked_=false; }
    private:
        enum class Phase { None, Identity, Interrupts, Decision, Crtc, Ring, I2c,
                           Arm, Fifo, Post, Readback, Readiness };
        bool allowed(uint32_t,unsigned,bool) const;
        bool active() const;
        bool timer(uint64_t&);
        bool memorySize(uint64_t&);
        Owner& owner_;
        runtime::startup::RegisterHelpers helpers_;
        Phase phase_=Phase::None;
        uint32_t pc_=0,selector_=0,i2cPin_=0,fifoReadValue_=0;
        unsigned fifoWrites_=0;
        bool fifoRead_=false;
        unsigned armWrites_=0;
        bool romDone_=false,readback_=false,windowLocked_=false,scratchOwned_=false;
    };
    struct Guard {std::atomic_flag& flag;bool held;explicit Guard(std::atomic_flag& f):flag(f),held(!f.test_and_set()){}
        ~Guard(){if(held)flag.clear();}};
    void failed();
    Platform& platform_;
    memory::ArmedReference arm_;
    ArmAuthority authority_;
    devinit::PostImage image_;
    ExecutionPermit permit_;
    runtime::startup::OncePerBoot once_;
    Transport io_{*this};
    devinit::BoundPost post_{image_,io_,io_,devinit::PostI2c::DedicatedPins};
    runtime::startup::Controller controller_{once_};
    const uint64_t expectedVram_;
    Outcome outcome_;
    std::atomic_flag lock_=ATOMIC_FLAG_INIT;
    bool prepared_=false,attached_=false,submitted_=false;
};
}
