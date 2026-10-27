// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "board_fake.h"
#include <cstdio>
#include <map>
#include <string>
#include <vector>
using namespace k40::devinit;
static unsigned checks = 0, failed = 0;
#define CHECK(c) do { ++checks; if (!(c)) { ++failed; std::printf("FAIL %d: %s\n", __LINE__, #c); } } while (0)


struct Synthetic {
    std::vector<uint8_t> bytes = std::vector<uint8_t>(512, 0);
    Synthetic() {
        put(0x36, 0x80, 2); bytes[0x80] = 0x40; bytes[0x81] = 12;
        put(0x86, 0x4edcbdcb, 4); put(0x84, 0xa0, 2); put(0x8a, 0xc0, 2);
        bytes[0xa0] = 0x40; bytes[0xa1] = 5; bytes[0xa2] = 3; bytes[0xa3] = 4;
        bytes[0xa4] = 0x12; // Primary CCB 2, secondary CCB 1.
        put(0xad, 0x050007a3, 4); put(0xa9, 0x05000001, 4);
        bytes[0xc0] = 0x41; bytes[0xc1] = 4; bytes[0xc2] = 4; bytes[0xc3] = 5;
        gpio(0, 0, 4, true, 0xa1, 2, 0, 1);
        gpio(1, 7, 0x18, true, 0x55, 3, 0, 1);
        gpio(2, 16, 9, false, 0x77, 0, 2, 3);
        gpio(3, 63, 0xff, false, 0, 0, 0, 0);
    }
    void put(unsigned at, uint32_t value, unsigned size) {
        for (unsigned i = 0; i < size; ++i) bytes[at + i] = uint8_t(value >> (8 * i));
    }
    void gpio(unsigned index, uint8_t line, uint8_t function, bool defaults,
              uint8_t route, uint8_t selector, uint8_t lo, uint8_t hi) {
        const auto at = 0xc4 + index * 5;
        put(at, line | (defaults ? 0x80 : 0) | (uint32_t(function) << 8)
            | (uint32_t(route) << 16) | (uint32_t(selector) << 24), 4);
        bytes[at + 4] = uint8_t((lo << 4) | (hi << 6));
    }
    RomView view() const { return {bytes.data(), uint32_t(bytes.size())}; }
};

static std::string hex(const Digest& digest)
{
    std::string out;
    for (auto byte : digest) { char part[3]; std::snprintf(part, sizeof(part), "%02x", byte); out += part; }
    return out;
}

int main()
{
    CHECK(hex(sha256(nullptr, 0)) == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855");
    const uint8_t abc[] = {'a', 'b', 'c'};
    CHECK(hex(sha256(abc, 3)) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
    std::vector<uint8_t> million(1000000, 'a');
    CHECK(hex(sha256(million.data(), uint32_t(million.size()))) ==
          "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0");
    CHECK(boardRules().size() == 6);
    for (const auto& rule : boardRules()) {
        CHECK(boardAllowed(rule.rom, rule.offset, rule.opcode));
        CHECK(!boardAllowed(rule.rom, rule.offset + 1, rule.opcode));
        CHECK(!boardAllowed(rule.rom, rule.offset, uint8_t(rule.opcode ^ 1)));
        auto changed = rule.rom; changed[31] ^= 1;
        CHECK(!boardAllowed(changed, rule.offset, rule.opcode));
    }
    CHECK(!boardAllowed(boardRules()[0].rom, 0x89c2, 0x8e));
    const uint8_t io[] = {0x69,0xc3,3,0x80,1};
    {
        BoardFake f; BoardHelpers helpers(f, f);
        f.regs[0x000200] = 0x40012125; f.regs[0x00e18c] = 0x10000; f.regs[0x6013c3] = 0xff;
        CHECK(helpers.execute({}, io, sizeof(io), true) == Error::None);
        CHECK(f.regs[0x000200] == 0x40012125 && f.regs[0x00e18c] == 0x10000);
        CHECK(f.regs[0x614100] == 0x10000018 && f.regs[0x614900] == 0x10000018);
        CHECK(f.regs[0x6013c3] == 0x81);
        CHECK(f.events.size() == 20 && f.events[8].kind == 'D' && f.events[15].kind == 'D');
        CHECK(f.events[8].value == 10000 && f.events[15].value == 10000);
        CHECK(f.events[18].width == 1 && f.events[19].width == 1);
    }
    {
        BoardFake f; BoardHelpers helpers(f, f);
        CHECK(helpers.execute({}, io, sizeof(io), false) == Error::None);
        CHECK(f.events.size() == 2 && f.events[0].kind == 'D' && f.events[1].kind == 'D');
        CHECK(f.clock == 20000 && f.regs.empty());
    }
    for (int failure = 0; failure < 20; ++failure) {
        BoardFake f; f.failAt = failure; BoardHelpers helpers(f, f);
        CHECK(helpers.execute({}, io, sizeof(io), true) == Error::Io);
        CHECK(f.events.size() == unsigned(failure + 1));
    }
    const uint8_t cr[] = {0x53,0x3f,0x57};
    {
        BoardFake f; BoardHelpers helpers(f, f);
        CHECK(helpers.execute({}, cr, sizeof(cr), true) == Error::None);
        CHECK(f.events.size() == 2 && f.events[0].address == 0x6013d4
              && f.events[0].value == 0x3f && f.events[1].address == 0x6013d5
              && f.events[1].value == 0x57 && f.events[1].width == 1);
        const auto count = f.events.size();
        CHECK(helpers.execute({}, cr, sizeof(cr), false) == Error::None && f.events.size() == count);
    }
    Synthetic rom;
    const uint8_t i2c[] = {0x4d,0x80,0x52,2,0x11,0x22,0x33,0x44};
    {
        BoardFake f; BoardHelpers helpers(f, f);
        CHECK(helpers.execute(rom.view(), i2c, sizeof(i2c), true) == Error::None);
        CHECK(f.buses.size() == 2 && f.buses[0].index == 2 && f.buses[0].drive == 3
              && f.buses[0].share == 3 && f.buses[0].type == 5);
        CHECK(f.events[0].width == 0x29 && f.events[0].address == 0x11 && f.events[1].address == 0x33);
        I2cBus bus;
        CHECK(BoardHelpers::resolveBus(rom.view(), 0x81, bus) && bus.index == 1);
        CHECK(BoardHelpers::resolveBus(rom.view(), 0xff, bus) && bus.index == 2);
        CHECK(!BoardHelpers::resolveBus(rom.view(), 15, bus));
        CHECK(helpers.execute({}, i2c, sizeof(i2c), false) == Error::None);
    }
    {
        Synthetic pmgr; pmgr.bytes[0xa0] = 0x41; pmgr.put(0xad, 4 | (5 << 5), 4);
        I2cBus bus;
        CHECK(BoardHelpers::resolveBus(pmgr.view(), 0x80, bus) && bus.type == 0x80
              && bus.drive == 4 && bus.aux == 5 && bus.share == 5);
        pmgr.put(0xad, 0x1f | (5 << 5), 4);
        CHECK(!BoardHelpers::resolveBus(pmgr.view(), 0x80, bus));
    }
    {
        BoardFake f; f.failAt = 0; BoardHelpers helpers(f, f);
        CHECK(helpers.execute(rom.view(), i2c, sizeof(i2c), true) == Error::Io && f.events.size() == 1);
        CHECK(helpers.execute(rom.view(), i2c, 7, true) == Error::Input);
    }
    const uint8_t gpio[] = {0xa9,1,4};
    {
        BoardFake f; BoardHelpers helpers(f, f); f.regs[0xd62c] = 0xaaaa0000; f.regs[0xd610] = 0x1234;
        CHECK(helpers.execute(rom.view(), gpio, sizeof(gpio), true) == Error::None);
        CHECK(f.regs[0xd610] == 0x1234); // Excluded core-voltage function.
        CHECK(f.regs[0xd62c] == 0xaaaa3055); // Default output high and routing byte.
        CHECK(f.regs[0xd748] == 7 && f.regs[0xd604] == 1);
        CHECK((f.regs[0xd650] & 0x30ff) == 0x77); // Input low, selector zero omitted.
        unsigned writes = 0; for (auto event : f.events) writes += event.kind == 'W';
        CHECK(writes == 7);
    }
    for (unsigned cut = 0; cut < 0xd8; ++cut) {
        BoardFake f; BoardHelpers helpers(f, f);
        CHECK(helpers.execute({rom.bytes.data(), cut}, gpio, sizeof(gpio), true) == Error::Input);
        CHECK(f.events.empty());
    }
    {
        Synthetic invalid; invalid.bytes[0xc4 + 5] = 63;
        BoardFake f; BoardHelpers helpers(f, f);
        CHECK(helpers.execute(invalid.view(), gpio, sizeof(gpio), true) == Error::Input && f.events.empty());
        CHECK(helpers.execute({}, gpio, sizeof(gpio), false) == Error::None && f.events.empty());
    }
    {
        Synthetic duplicate;
        duplicate.gpio(3, 7, 0x18, false, 0x33, 0, 3, 3);
        const uint8_t exclusions[] = {0xa9,2,4,9};
        BoardFake f; BoardHelpers helpers(f, f);
        CHECK(helpers.execute(duplicate.view(), exclusions, sizeof(exclusions), true) == Error::None);
        CHECK((f.regs[0xd62c] & 0x30ff) == 0x2033);
        unsigned writes = 0; for (auto event : f.events) writes += event.kind == 'W';
        CHECK(writes == 14); // GPIO_NE resets the duplicate function twice.
    }
    for (int failure = 0; failure < 14; ++failure) {
        BoardFake f; f.failAt = failure; BoardHelpers helpers(f, f);
        CHECK(helpers.execute(rom.view(), gpio, sizeof(gpio), true) == Error::Io);
        CHECK(f.events.size() == unsigned(failure + 1));
    }
    {
        BoardFake registers, ports; ports.simulation = false;
        BoardHelpers helpers(registers, ports);
        CHECK(helpers.execute({}, io, sizeof(io), true) == Error::HardwareDisabled);
        CHECK(registers.events.empty() && ports.events.empty());
    }
    {
        BoardFake f; f.simulation = false; BoardHelpers helpers(f, f);
        CHECK(helpers.execute({}, io, sizeof(io), false) == Error::HardwareDisabled && f.events.empty());
        PolicyBackend policy(rom.bytes.data(), uint32_t(rom.bytes.size()), f, f);
        CHECK(policy.run(16).error == Error::HardwareDisabled && f.events.empty());
    }
    {
        BoardFake f; PolicyBackend policy(rom.bytes.data(), uint32_t(rom.bytes.size()), f, f);
        CHECK(!policy.approved() && policy.run(16).error == Error::Denied);
        CHECK(!policy.board(0x69, 0x8506, io, sizeof(io), true));
        CHECK(f.events.empty() && f.audits == 1 && f.lastAudit == Error::Denied);
        CHECK(!policy.write32(0, 1) && !policy.delayUs(10000) && f.events.empty());
    }
    std::printf("board helpers: %u checks, %u failures (HOST_ONLY)\n", checks, failed);
    return failed ? 1 : 0;
}
