// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "devinit/I2c.h"

namespace k40::devinit {
bool DedicatedI2c::initialize(const I2cBus& bus)
{
    ready_ = false;
    result_ = {};
    if (!executionAllowed()) { result_.primary = I2cError::HardwareDisabled; return false; }
    // Reviewed dedicated NVIO descriptor only; shared pad modes are unsupported.
    if (bus.type != 0x05 || bus.share != 0xff || bus.drive > 15) { // include/nvkm/subdev/bios/i2c.h:8,12.
        result_.primary = I2cError::Input; return false;
    }
    address_ = 0x00d014 + uint32_t(bus.drive) * 0x20; // nvkm/subdev/i2c/busgf119.c:93.
    if (!registers_.write32(address_, 7)) { result_.primary = I2cError::Io; return false; } // nvkm/subdev/i2c/busgf119.c:69.
    bus_ = bus;
    ready_ = true;
    return true;
}

bool DedicatedI2c::retryAddressNack()
{
    // Only BoundPost can reopen the engine, after its exact-ROM sensor policy.
    if(!executionAllowed() || ready_ || result_.primary!=I2cError::Nack
        || result_.cleanup!=I2cError::None || result_.phase!=I2cPhase::Address || result_.bit!=8)return false;
    ready_=true;return true;
}

bool DedicatedI2c::guard()
{
    if (error_ != I2cError::None) return false;
    // no source: software callback budget, independent of clock progress.
    if (++operations_ > 20000) return fail(I2cError::Budget);
    const auto now = registers_.nowUs();
    if (now < last_) return fail(I2cError::Clock);
    last_ = now;
    if (now - started_ >= timeout_) return fail(I2cError::Timeout);
    return true;
}
bool DedicatedI2c::read(uint32_t& value)
{
    if (!guard() || !(registers_.read32(address_, value) || fail(I2cError::Io))) return false;
    lastRead_=value; return true;
}
bool DedicatedI2c::drive(uint32_t mask, bool high)
{
    uint32_t old = 0;
    return read(old) && guard()
        && (registers_.write32(address_, (old & ~mask) | (high ? mask : 0)) || fail(I2cError::Io));
}
bool DedicatedI2c::sense(uint32_t mask, bool& high)
{
    uint32_t value = 0;
    if (!read(value)) return false;
    high = (value & mask) != 0;
    return true;
}
bool DedicatedI2c::delay(uint64_t us)
{
    return guard() && (registers_.delayUs(us) || fail(I2cError::Io)) && guard();
}
bool DedicatedI2c::raise()
{
    if (!drive(1, true)) return false; // nvkm/subdev/i2c/busgf119.c:37.
    // bit.c:27-29,63-74: 2.2 ms stretch bound, sampled every microsecond.
    for (unsigned poll = 0; poll < 2200; ++poll) {
        bool high = false;
        if (!delay(1) || !sense(0x10, high)) return false; // nvkm/subdev/i2c/busgf119.c:53.
        if (high) return true;
    }
    return fail(I2cError::Stretch);
}
bool DedicatedI2c::start()
{
    bool scl = false, sda = false;
    if (!sense(0x10, scl) || !sense(0x20, sda)) return false; // nvkm/subdev/i2c/busgf119.c:53,61.
    // bit.c:78-96: bring a non-idle bus to START, without recovery pulses.
    if ((!scl || !sda) && (!drive(1, false) || !drive(2, true) || !raise())) return false;
    return drive(2, false) && delay(5) && drive(1, false) && delay(5); // nvkm/subdev/i2c/bit.c:91-94.
}
bool DedicatedI2c::stop()
{
    // bit.c:101-111: STOP is bounded; it does not prove clock release or recovery.
    return drive(1, false) && drive(2, false) && delay(1)
        && drive(1, true) && delay(5) && drive(2, true) && delay(5);
}
bool DedicatedI2c::byte(uint8_t value)
{
    for (int bit = 7; bit >= 0; --bit) {
        bit_=unsigned(7-bit);
        // bit.c:115-129: transmit MSB first, with 1 us setup and 5 us holds.
        if (!drive(2, (value >> bit) & 1) || !delay(1) || !raise()
            || !delay(5) || !drive(1, false) || !delay(5)) return false;
    }
    bit_=8;
    bool nack = false;
    // bit.c:133-150,169-173: release SDA, sample ACK, then lower SCL.
    if (!drive(2, true) || !delay(1) || !raise() || !delay(5)
        || !sense(0x20, nack) || !drive(1, false) || !delay(5)) return false; // nvkm/subdev/i2c/busgf119.c:61.
    return !nack || fail(I2cError::Nack);
}
bool DedicatedI2c::i2cWrite(const I2cBus& bus, uint8_t address7, uint8_t reg, uint8_t value)
{
    result_ = {};
    if (!executionAllowed()) { result_.primary = I2cError::HardwareDisabled; return false; }
    if (!ready_) { result_.primary = I2cError::NotInitialized; return false; }
    if (!timeout_ || address7 > 127 || bus.index != bus_.index || bus.type != bus_.type
        || bus.drive != bus_.drive || bus.share != bus_.share || bus.aux != bus_.aux) {
        result_.primary = I2cError::Input; return false;
    }
    operations_ = 0;
    error_ = I2cError::None;
    started_ = last_ = registers_.nowUs();
    // Address byte and two payload bytes: bios/init.c:294-299; i2c/bit.c:177-183.
    phase_=I2cPhase::Start;bit_=0;lastRead_=0;
    auto send=[&](I2cPhase phase,uint8_t data) { phase_=phase;return byte(data); };
    const bool transferred = start() && send(I2cPhase::Address,uint8_t(address7 << 1))
        && send(I2cPhase::Register,reg) && send(I2cPhase::Value,value);
    result_.primary = error_;
    result_.phase=phase_;result_.bit=bit_;result_.levels=lastRead_;
    result_.transferUs=last_>=started_?last_-started_:0;
    const auto cleanupStart=last_;
    // Source always attempts STOP. Preserve the primary error and use the same
    // deadline/budget for cleanup. No retry, extra pulses, or implicit reinit.
    error_ = I2cError::None;
    phase_=I2cPhase::Stop;
    const bool stopped = stop();
    result_.cleanup = error_;
    result_.operations=operations_;
    result_.cleanupUs=last_>=cleanupStart?last_-cleanupStart:0;
    result_.disposition=transferred && stopped?I2cDisposition::Complete:I2cDisposition::Fatal;
    if (!transferred || !stopped) ready_ = false;
    return transferred && stopped;
}
}
