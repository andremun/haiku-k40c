// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "devinit/Interpreter.h"
#include "devinit/BoardPolicy.h"
#include <array>
#include <vector>

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
    // Callbacks must be bounded and return false on an unavailable bus or NACK.
    // No physical I2C adapter is supplied in this host-only macro task.
    virtual bool read8(uint32_t address, uint8_t& value) = 0;
    virtual bool write8(uint32_t address, uint8_t value) = 0;
    virtual bool i2cWrite(const I2cBus&, uint8_t address7, uint8_t reg, uint8_t value) = 0;
    virtual void audit(uint32_t, uint8_t, bool, Error) {}
};

// Semantic helpers alone grant no ROM permission. Both transports must be host simulations.
// PolicyBackend is the permission-bearing interpreter entry point.
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

class PolicyBackend final : public Backend {
public:
    // Copies the ROM before hashing. The caller cannot mutate its verified snapshot.
    PolicyBackend(const uint8_t* rom, uint32_t size, Backend& registers, BoardTransport& ports);
    bool approved() const { return approved_; }
    Result run(uint32_t start, Tables tables = {}, Limits limits = {}, uint8_t flags = 1);
    bool hostSimulation() const override;
    uint64_t nowUs() override;
    bool delayUs(uint64_t us) override;
    bool read32(uint32_t reg, uint32_t& value) override;
    bool write32(uint32_t reg, uint32_t value) override;
    bool board(uint8_t opcode, uint32_t offset, const uint8_t* payload, uint32_t size, bool active) override;
    void trace(uint32_t offset, uint8_t opcode, bool active) override;
    Error boardError() const { return boardError_; }
private:
    const std::vector<uint8_t> rom_;
    const Digest digest_;
    const bool approved_;
    Backend& registers_;
    BoardTransport& ports_;
    BoardHelpers helpers_;
    Error boardError_ = Error::None;
};
}
