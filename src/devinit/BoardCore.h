// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "a7/ExecutionPermit.h"
#include "devinit/Interpreter.h"
#include "devinit/BoardPolicy.h"
#include <array>

namespace k40::devinit {
struct RomView {
    const uint8_t* data;
    uint32_t size;
    bool contains(uint32_t at, uint32_t length) const;
    uint32_t little(uint32_t at, unsigned bytes) const; // Call contains first.
};
struct I2cBus {
    uint8_t index = 0, type = 0, drive = 0xff, share = 0xff, aux = 0xff; // include/nvkm/subdev/bios/i2c.h:12, unavailable bus-field sentinel.
};
class BoardTransport {
public:
    virtual ~BoardTransport() = default;
    virtual bool hostSimulation() const = 0;
    virtual const a7::ExecutionPermit* a7Permit() const { return nullptr; }
    bool executionAllowed() const { return a7::permitted(hostSimulation(),a7Permit()); }
    // Callbacks must be bounded and return false on an unavailable bus or NACK.
    // Physical transports remain gated. DedicatedI2c supplies a host pin candidate.
    virtual bool read8(uint32_t address, uint8_t& value) = 0;
    virtual bool write8(uint32_t address, uint8_t value) = 0;
    virtual bool i2cWrite(const I2cBus&, uint8_t address7, uint8_t reg, uint8_t value) = 0;
    virtual void audit(uint32_t, uint8_t, bool, Error) {}
};

// Semantic helpers alone grant no ROM permission. Both transports must be host simulations.
// BoundPost supplies per-instruction permissions; helpers alone grant none.
class BoardHelpers {
public:
    BoardHelpers(Backend& registers, BoardTransport& ports) : registers_(registers), ports_(ports) {}
    Error execute(RomView rom, const uint8_t* instruction, uint32_t length, bool active);
    static bool resolveBus(RomView rom, uint8_t index, I2cBus& bus);
private:
    bool masked(uint32_t reg, uint32_t mask, uint32_t value);
    Error io(const uint8_t*, bool active);
    Error gpio(RomView, const uint8_t*, uint32_t length);
    Backend& registers_;
    BoardTransport& ports_;
};

}
