// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "a7/ExecutionPermit.h"
#include "memory/ArmedReference.h"
#include "devinit/BoardCore.h"
#include "runtime/BootState.h"

namespace k40::runtime::startup {
enum class Step { Inputs, Identity, Interrupts, PostDecision, Crtc, PrivateRing,
                  I2c, FlushPage, FifoReset, Rom, FlushReadback, FlushRearm, Readiness, Complete };
enum class Error { None, HardwareDisabled, AlreadyAttempted, Inputs, Io, UnexpectedState, Timeout, Clock };
struct Result { Error error = Error::None; Step step = Step::Inputs; bool referenceRetained = false; uint32_t flushReadback = 0; unsigned armAttempts = 0; };

class Backend {
public:
    virtual ~Backend() = default;
    virtual bool hostSimulation() const = 0;
    virtual const a7::ExecutionPermit* a7Permit() const { return nullptr; }
    bool executionAllowed() const { return a7::permitted(hostSimulation(),a7Permit()); }
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
    virtual bool readFlushPage(uint32_t&) = 0;
    // Must check independent memory/fault evidence, not just the script's marker.
    virtual bool independentReadiness() = 0;
};
class Controller {
public:
    explicit Controller(OncePerBoot& state) : state_(state) {}
    Result run(Backend&, memory::ArmedReference& flushPage, uint64_t timeoutUs);
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
    bool allowed() const { return a7::compatible(registers_.hostSimulation(),registers_.a7Permit(),
        bytes_.hostSimulation(),bytes_.a7Permit()); }
    bool masked(uint32_t reg, uint32_t mask, uint32_t value);
    devinit::Backend& registers_;
    devinit::BoardTransport& bytes_;
};
}
