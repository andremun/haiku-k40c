// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "devinit/BoardCore.h"

namespace k40::devinit {
enum class I2cError { None, HardwareDisabled, Input, NotInitialized, Io, Nack, Stretch, Timeout, Clock, Budget };
enum class I2cPhase { Idle, Start, Address, Register, Value, Stop };
enum class I2cDisposition { Fatal, Complete, RetryAddress, ReferenceNack };
struct I2cResult {
    I2cError primary = I2cError::None, cleanup = I2cError::None;
    I2cPhase phase = I2cPhase::Idle;
    I2cDisposition disposition = I2cDisposition::Fatal;
    unsigned attempt = 1;
    uint32_t bit = 0, operations = 0, levels = 0;
    uint64_t transferUs = 0, cleanupUs = 0;
};
// SOURCE_ONLY candidate for CONFIG_NOUVEAU_I2C_INTERNAL, not capture timing proof.
// Caller serializes the complete bus transaction. All callbacks must be bounded.
class DedicatedI2c final : public BoardTransport {
public:
    DedicatedI2c(Backend& registers, BoardTransport& bytes) : registers_(registers), bytes_(bytes) {}
    bool initialize(const I2cBus&);
    bool hostSimulation() const override { return registers_.hostSimulation() && bytes_.hostSimulation(); }
    const a7::ExecutionPermit* a7Permit() const override {
        return !registers_.hostSimulation() && !bytes_.hostSimulation()
            && registers_.a7Permit()==bytes_.a7Permit()?registers_.a7Permit():nullptr;
    }
    bool read8(uint32_t at, uint8_t& value) override { return executionAllowed() && bytes_.read8(at, value); }
    bool write8(uint32_t at, uint8_t value) override { return executionAllowed() && bytes_.write8(at, value); }
    bool i2cWrite(const I2cBus&, uint8_t address7, uint8_t reg, uint8_t value) override;
    void audit(uint32_t at, uint8_t op, bool active, Error error) override { if (executionAllowed()) bytes_.audit(at, op, active, error); }
    I2cResult result() const { return result_; }
    // Software transaction deadline. Poll counts also bound a stalled clock.
    void timeoutUs(uint64_t value) { timeout_ = value; }
private:
    friend class BoundPost;
    bool retryAddressNack();
    bool guard();
    bool read(uint32_t&);
    bool drive(uint32_t mask, bool high);
    bool sense(uint32_t mask, bool& high);
    bool delay(uint64_t us);
    bool raise();
    bool start();
    bool stop();
    bool byte(uint8_t);
    bool fail(I2cError error) { if (error_ == I2cError::None) error_ = error; return false; }
    Backend& registers_;
    BoardTransport& bytes_;
    I2cBus bus_{};
    uint32_t address_ = 0, operations_ = 0;
    uint64_t started_ = 0, last_ = 0, timeout_ = 100000;
    bool ready_ = false;
    I2cPhase phase_ = I2cPhase::Idle;
    uint32_t bit_ = 0, lastRead_ = 0;
    I2cError error_ = I2cError::None;
    I2cResult result_{};
};
}
