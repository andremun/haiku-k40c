// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "devinit/I2c.h"
#include "board_fake.h"
#include <cstdio>
#include <vector>
using namespace k40::devinit;
static unsigned checks = 0, failures = 0;
#define CHECK(c) do { ++checks; if (!(c)) { ++failures; std::printf("FAIL %d: %s\n", __LINE__, #c); } } while (0)

#include "i2c_wire.h"
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
