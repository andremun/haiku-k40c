// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "devinit/I2c.h"
#include "board_fake.h"
#include <cstdio>
#include <vector>
using namespace k40::devinit;
static unsigned checks = 0, failures = 0;
#define CHECK(c) do { ++checks; if (!(c)) { ++failures; std::printf("FAIL %d: %s\n", __LINE__, #c); } } while (0)

// Decode transitions, rather than replaying the transmitter's register calls.
struct Wire : BoardFake {
    uint32_t output = 7;
    bool active = false, frozen = false, stuck = false, rollback = false;
    unsigned phase = 0, starts = 0, stops = 0, ack = 0, nackAt = 0, stretch = 0, remaining = 0;
    uint8_t value = 0;
    std::vector<uint8_t> decoded;
    uint64_t nowUs() override { return rollback && clock > 40 ? 0 : (frozen ? clock : ++clock); }
    bool delayUs(uint64_t us) override { if (!frozen) clock += us; return event('D',0,0,uint32_t(us)); }
    bool read32(uint32_t at, uint32_t& out) override {
        bool high = output & 1;
        if (high && remaining) { high = false; --remaining; }
        if (stuck) high = false;
        bool data = output & 2;
        if (active && phase == 9) data = nackAt && ack == nackAt;
        out = output | (high ? 0x10 : 0) | (data ? 0x20 : 0);
        return event('R',4,at,out);
    }
    bool write32(uint32_t at, uint32_t out) override {
        if (!event('W',4,at,out)) return false;
        const bool scl = output & 1, sda = output & 2, nextScl = out & 1, nextSda = out & 2;
        if (scl && nextScl && sda != nextSda) {
            if (!nextSda) { active = true; phase = 0; value = 0; ++starts; }
            else if (active) { active = false; ++stops; }
        }
        if (active && !scl && nextScl) {
            ++phase;
            if (phase <= 8) value = uint8_t((value << 1) | nextSda);
            else if (phase == 9) { decoded.push_back(value); ++ack; }
            remaining = stretch;
        }
        if (active && scl && !nextScl && phase == 9) { phase = 0; value = 0; }
        output = out & ~0x30u; // Sense bits are read-only.
        return true;
    }
};
I2cBus bus() { I2cBus b; b.index = 2; b.type = 5; b.drive = 2; return b; }
int main()
{
    unsigned successfulCalls = 0;
    {
        Wire wire; DedicatedI2c i2c(wire, wire); CHECK(i2c.initialize(bus()));
        CHECK(i2c.i2cWrite(bus(), 0x4c, 0x19, 0x73));
        CHECK(wire.decoded == std::vector<uint8_t>({0x98,0x19,0x73}));
        CHECK(wire.starts == 1 && wire.stops == 1 && wire.ack == 3);
        CHECK(i2c.result().primary == I2cError::None && i2c.result().cleanup == I2cError::None);
        successfulCalls = wire.calls;
        for (const auto& event : wire.events) if (event.width == 4) CHECK(event.address == 0xd054);
        CHECK(i2c.i2cWrite(bus(), 0x20, 0xdd, 3));
        CHECK(wire.decoded[3] == 0x40 && wire.decoded[4] == 0xdd && wire.decoded[5] == 3);
    }
    for (unsigned nack = 1; nack <= 3; ++nack) {
        Wire wire; wire.nackAt = nack; DedicatedI2c i2c(wire, wire); CHECK(i2c.initialize(bus()));
        CHECK(!i2c.i2cWrite(bus(), 0x4c, 0x19, 0x73));
        CHECK(i2c.result().primary == I2cError::Nack && i2c.result().cleanup == I2cError::None);
        CHECK(wire.decoded.size() == nack && wire.stops == 1);
        const auto calls = wire.calls;
        CHECK(!i2c.i2cWrite(bus(), 1, 2, 3) && wire.calls == calls);
    }
    {
        Wire baseline; baseline.nackAt = 1; DedicatedI2c first(baseline,baseline);
        CHECK(first.initialize(bus()) && !first.i2cWrite(bus(),1,2,3));
        Wire failing; failing.nackAt = 1; failing.failAt = int(baseline.calls - 1);
        DedicatedI2c second(failing,failing); CHECK(second.initialize(bus()));
        CHECK(!second.i2cWrite(bus(),1,2,3));
        CHECK(second.result().primary == I2cError::Nack && second.result().cleanup == I2cError::Io);
    }
    {
        Wire registers; BoardFake bytes; bytes.simulation = false;
        DedicatedI2c denied(registers,bytes); CHECK(!denied.initialize(bus()));
        denied.audit(1,2,true,Error::Io);
        CHECK(registers.events.empty() && bytes.events.empty() && !bytes.audits);
    }
    // Includes every read, write and delay, and each STOP callback.
    for (unsigned access = 0; access < successfulCalls; ++access) {
        Wire wire; wire.failAt = int(access); DedicatedI2c i2c(wire, wire);
        const bool initialized = i2c.initialize(bus());
        const bool transferred = initialized && i2c.i2cWrite(bus(), 0x4c, 0x19, 0x73);
        CHECK(!transferred);
        const auto r = i2c.result(); CHECK(r.primary == I2cError::Io || r.cleanup == I2cError::Io);
    }
    {
        Wire wire; DedicatedI2c i2c(wire,wire); CHECK(i2c.initialize(bus())); wire.stretch = 3;
        CHECK(i2c.i2cWrite(bus(),1,2,3) && wire.stops == 1);
    }
    for (unsigned kind = 0; kind < 5; ++kind) {
        Wire wire; DedicatedI2c i2c(wire,wire); CHECK(i2c.initialize(bus()));
        if (kind == 0) wire.stuck = true;
        if (kind == 1) { wire.stuck = true; wire.frozen = true; }
        if (kind == 2) i2c.timeoutUs(20);
        if (kind == 3) wire.rollback = true;
        if (kind == 4) { wire.frozen = true; wire.stretch = 2199; }
        CHECK(!i2c.i2cWrite(bus(),1,2,3));
        const I2cError errors[] = {I2cError::Stretch,I2cError::Stretch,I2cError::Timeout,I2cError::Clock,I2cError::Budget};
        CHECK(i2c.result().primary == errors[kind]);
        CHECK(wire.calls < 20000);
    }
    {
        Wire wire; DedicatedI2c i2c(wire,wire); CHECK(!i2c.i2cWrite(bus(),1,2,3) && wire.events.empty());
        auto invalid = bus(); invalid.share = 0;
        CHECK(!i2c.initialize(invalid) && wire.events.empty());
        invalid = bus(); invalid.type = 6; CHECK(!i2c.initialize(invalid));
        invalid = bus(); invalid.drive = 16; CHECK(!i2c.initialize(invalid));
        CHECK(i2c.initialize(bus())); const auto count = wire.calls;
        invalid = bus(); invalid.index = 3; CHECK(!i2c.i2cWrite(invalid,1,2,3) && wire.calls == count);
        CHECK(!i2c.i2cWrite(bus(),128,2,3) && wire.calls == count);
        i2c.timeoutUs(0); CHECK(!i2c.i2cWrite(bus(),1,2,3) && wire.calls == count);
        wire.simulation = false; CHECK(!i2c.initialize(bus()) && wire.calls == count);
        CHECK(!i2c.i2cWrite(bus(),1,2,3) && wire.calls == count);
        uint8_t byte = 0; CHECK(!i2c.read8(1,byte) && !i2c.write8(1,2) && wire.calls == count);
    }
    std::printf("dedicated host I2C: %u checks, %u failures (SOURCE_ONLY)\n",checks,failures);
    return failures ? 1 : 0;
}
