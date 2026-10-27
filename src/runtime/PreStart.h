// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "memory/Memory.h"
#include "devinit/Board.h"
#include <atomic>

namespace k40::runtime::startup {
enum class BootState : uint8_t { Fresh, Running, Complete, Failed };
enum class Step { Inputs, Identity, Interrupts, PostDecision, Crtc, PrivateRing,
                  I2c, FlushPage, FifoReset, Rom, Readiness, Complete };
enum class Error { None, HardwareDisabled, AlreadyAttempted, Inputs, Io, UnexpectedState, Timeout, Clock };
struct Result { Error error = Error::None; Step step = Step::Inputs; bool flushPinned = false; };
class OncePerBoot {
    friend class Controller;
    std::atomic<BootState> state_{BootState::Fresh};
public:
    BootState state() const { return state_.load(std::memory_order_acquire); }
};
class Backend {
public:
    virtual ~Backend() = default;
    virtual bool hostSimulation() const = 0;
    virtual uint64_t nowUs() = 0;
    virtual bool romPolicyReady() const = 0;
    // Every callback is bounded. No PCI configuration writes belong here.
    virtual bool identity() = 0;
    virtual bool unarmInterrupts() = 0;
    virtual bool postRequired(bool&) = 0;
    virtual bool unlockCrtc() = 0;
    virtual bool privateRing() = 0;
    virtual bool initializeI2c() = 0;
    virtual bool programFlushPage(memory::DeviceIova) = 0;
    virtual bool resetFifoBeforePost() = 0;
    virtual bool executeRom() = 0;
    // Must check independent memory/fault evidence, not just the script's marker.
    virtual bool independentReadiness() = 0;
};
class Controller {
public:
    explicit Controller(OncePerBoot& state) : state_(state) {}
    Result run(Backend&, memory::Buffer& flushPage, uint64_t timeoutUs);
private:
    OncePerBoot& state_;
};

// SOURCE_ONLY host implementation of selected GK110B preinit register mechanics.
// It does not authorize a hardware stage, select script roots, or prove readiness.
class RegisterHelpers {
public:
    RegisterHelpers(devinit::Backend& registers, devinit::BoardTransport& bytes)
        : registers_(registers), bytes_(bytes) {}
    bool unarmInterrupts();
    bool postRequired(bool&);
    bool unlockCrtc();
    bool privateRing();
    bool initializeDedicatedI2c(const devinit::I2cBus&);
    bool programFlushPage(memory::DeviceIova);
    // Cold first POST uses the selected fallback; TOP has not yet been parsed.
    bool resetFifoBeforePost();
private:
    bool allowed() const { return registers_.hostSimulation() && bytes_.hostSimulation(); }
    bool masked(uint32_t reg, uint32_t mask, uint32_t value);
    devinit::Backend& registers_;
    devinit::BoardTransport& bytes_;
};
}
