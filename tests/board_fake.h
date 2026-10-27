// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Host-only transport recorder. It never opens a device or a VM.
#pragma once
#include "devinit/Board.h"
#include <map>
#include <vector>
using namespace k40::devinit;

struct BoardFake : Backend, BoardTransport {
    struct Event { char kind; unsigned width; uint32_t address, value; };
    std::map<uint32_t, uint32_t> regs;
    std::vector<Event> events;
    std::vector<I2cBus> buses;
    uint64_t clock = 0;
    bool simulation = true;
    int failAt = -1;
    unsigned calls = 0, audits = 0;
    Error lastAudit = Error::None;
    bool hostSimulation() const override { return simulation; }
    uint64_t nowUs() override { return ++clock; }
    bool event(char kind, unsigned width, uint32_t at, uint32_t value) {
        events.push_back({kind, width, at, value});
        return int(calls++) != failAt;
    }
    bool delayUs(uint64_t us) override { clock += us; return event('D', 0, 0, uint32_t(us)); }
    bool read32(uint32_t at, uint32_t& value) override {
        value = regs[at]; return event('R', 4, at, value);
    }
    bool write32(uint32_t at, uint32_t value) override {
        if (!event('W', 4, at, value)) return false;
        regs[at] = value; return true;
    }
    bool read8(uint32_t at, uint8_t& value) override {
        value = uint8_t(regs[at]); return event('R', 1, at, value);
    }
    bool write8(uint32_t at, uint8_t value) override {
        if (!event('W', 1, at, value)) return false;
        regs[at] = value; return true;
    }
    bool i2cWrite(const I2cBus& bus, uint8_t address, uint8_t reg, uint8_t value) override {
        buses.push_back(bus); return event('I', address, reg, value);
    }
    void audit(uint32_t, uint8_t, bool, Error error) override { ++audits; lastAudit = error; }
};

