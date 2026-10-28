// Copyright 2026 Mario Andrés Muñoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "a7/ExecutionPermit.h"
#include <cstdint>

namespace k40::devinit {
// Opcode facts: nvkm/subdev/bios/init.c:2231-2297.
// Full semantic/provenance record: docs/DEVINIT-EXECUTOR.md.
enum class Error { None, Input, Bounds, Unsupported, Malformed, Io, Denied, Budget, Depth, Timeout, Clock, HardwareDisabled };
struct Tables {
    uint32_t conditions = 0, macros = 0;
    uint8_t ramGroups = 0, ramIndex = 0; // Pre-resolved/cached, not reread per opcode.
};
struct Limits { uint32_t steps = 100000; uint32_t depth = 32; uint64_t timeoutUs = 10000000; };
struct Result { Error error = Error::None; uint32_t offset = 0; uint32_t steps = 0; };
class Backend {
public:
    virtual ~Backend() = default;
    // This executor is not approved for hardware. A production backend must
    // not identify itself as a host simulation to bypass this gate.
    virtual bool hostSimulation() const = 0;
    virtual const a7::ExecutionPermit* a7Permit() const { return nullptr; }
    bool executionAllowed() const { return a7::permitted(hostSimulation(),a7Permit()); }
    virtual uint64_t nowUs() = 0;
    virtual bool delayUs(uint64_t) = 0; // Host-monotonic bounded implementation.
    // The backend must resolve encoded register helpers and enforce policy.
    virtual bool read32(uint32_t encodedRegister, uint32_t&) = 0;
    virtual bool write32(uint32_t encodedRegister, uint32_t value) = 0;
    // Default is deny. GPIO/I2C/VGA/helper effects require a separately reviewed
    // implementation. The pointer is read-only ROM payload, not register data
    // to replay blindly. IO may have MMIO effects even beyond legacy ports.
    virtual bool board(uint8_t, uint32_t, const uint8_t*, uint32_t, bool) { return false; }
    virtual void trace(uint32_t, uint8_t, bool) {}
};
class Interpreter {
public:
    Interpreter(const uint8_t* rom, uint32_t size, Tables tables, Backend& backend)
        : rom_(rom), size_(size), tables_(tables), backend_(backend) {}
    Result run(uint32_t start, Limits limits = {}, uint8_t executeFlags = 1);
private:
    enum class Stop { Done, EndRepeat, Failed };
    bool span(uint64_t offset, uint64_t bytes);
    uint32_t word(uint64_t offset, uint32_t bytes);
    bool active() const { return flags_ == 1 || (flags_ & 5) == 5; }
    void conditionFlag(bool success) { if (!success) flags_ |= 2; }
    bool read(uint32_t reg, uint32_t& value);
    bool write(uint32_t reg, uint32_t value);
    bool masked(uint32_t reg, uint32_t keep, uint32_t value);
    bool condition(uint8_t index, bool& met);
    bool deadline();
    Stop execute(uint32_t& pc, uint32_t depth, bool repeatBody);
    const uint8_t* rom_;
    uint32_t size_;
    Tables tables_;
    Backend& backend_;
    Limits limits_{};
    Result result_{};
    uint8_t flags_ = 1;
    uint64_t started_ = 0, last_ = 0;
};
} // namespace k40::devinit
