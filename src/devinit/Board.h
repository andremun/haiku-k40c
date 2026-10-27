// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "devinit/BoardCore.h"
#include <vector>

namespace k40::devinit {
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
