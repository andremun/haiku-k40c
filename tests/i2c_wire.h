// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "board_fake.h"
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
