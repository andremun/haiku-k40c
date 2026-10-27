// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "devinit/BoardCore.h"

namespace k40::devinit {
namespace {
// Current ROM uses DCB 4.0. Older table layouts remain deliberately unsupported.
// nvkm/subdev/bios/dcb.c:28-60, gpio.c:33-64, i2c.c:32-62.
bool table(RomView rom, unsigned pointer, uint32_t& at)
{
    if (!rom.contains(0x36, 2)) return false; // nvkm/subdev/bios/dcb.c:35.
    const auto dcb = rom.little(0x36, 2); // nvkm/subdev/bios/dcb.c:35.
    if (!dcb || !rom.contains(dcb, 12) || rom.data[dcb] < 0x30 || rom.data[dcb] > 0x41 // nvkm/subdev/bios/dcb.c:43,47.
        || rom.data[dcb + 1] < 12 || rom.little(dcb + 6, 4) != 0x4edcbdcb) // nvkm/subdev/bios/dcb.c:48.
        return false;
    at = rom.little(dcb + pointer, 2);
    return at && rom.contains(at, 4);
}

struct Gpio {
    uint8_t function, line;
    std::array<uint8_t, 2> logic;
    bool defaults;
    uint8_t route, selector;
};
// GPIO count is an unsigned byte: bios/gpio.c:44-50. Storage also includes unused rows.
struct GpioEntries { std::array<Gpio,255> rows{}; unsigned count = 0; };
bool gpioEntries(RomView rom, GpioEntries& out)
{
    uint32_t at = 0;
    if (!table(rom, 10, at)) return false;
    const auto version = rom.data[at], header = rom.data[at + 1];
    const auto count = rom.data[at + 2], stride = rom.data[at + 3];
    // Exact GPIO 4.1 record layout: bios/gpio.c:103-110.
    if (version != 0x41 || header < 4 || stride < 5
        || !rom.contains(at, header + uint32_t(count) * stride)) return false;
    for (unsigned i = 0; i < count; ++i) {
        const auto entry = at + header + i * stride;
        const auto raw = rom.little(entry, 4);
        const auto function = uint8_t(raw >> 8);
        if (function == 0xff) continue; // include/nvkm/subdev/bios/gpio.h:14, DCB_GPIO_UNUSED.
        const auto line = uint8_t(raw & 0x3f); // nvkm/subdev/bios/gpio.c:106.
        if (line >= 32) return false; // gpio/gk104.c:64, 32 hardware lines.
        const bool defaults = raw & 0x80; // gpio/gf119.c:38.
        const auto logic = rom.data[entry + 4];
        out.rows[out.count++] = {function, line, {uint8_t((logic >> 4) & 3), uint8_t((logic >> 6) & 3)},
                       defaults, uint8_t(raw >> 16), uint8_t((raw >> 24) & 0x1f)}; // nvkm/subdev/gpio/gf119.c:40-41.
    }
    return true;
}
}

bool RomView::contains(uint32_t at, uint32_t length) const
{
    return data && at <= size && length <= size - at;
}
uint32_t RomView::little(uint32_t at, unsigned bytes) const
{
    uint32_t out = 0;
    for (unsigned i = 0; i < bytes; ++i) out |= uint32_t(data[at + i]) << (8 * i);
    return out;
}

bool BoardHelpers::masked(uint32_t reg, uint32_t mask, uint32_t value)
{
    uint32_t previous = 0;
    return registers_.read32(reg, previous) && registers_.write32(reg, (previous & ~mask) | value);
}

Error BoardHelpers::io(const uint8_t* bytes, bool active)
{
    const uint16_t port = uint16_t(bytes[1]) | (uint16_t(bytes[2]) << 8);
    // NV50+ IO helper: bios/init.c:1636-1655. The two waits are unconditional.
    if (port == 0x03c3 && bytes[4] == 1) {
        struct Step { uint32_t reg, mask, value; bool rmw, wait; };
        constexpr Step steps[] = { // no source: software sequence container; each hardware value has its own citation.
            {0x614100,0xf0800000,0x00800000,true,false}, // nvkm/subdev/bios/init.c:1640.
            {0x00e18c,0x00020000,0x00020000,true,false}, // nvkm/subdev/bios/init.c:1641.
            {0x614900,0xf0800000,0x00800000,true,false}, // nvkm/subdev/bios/init.c:1642.
            {0x000200,0x40000000,0x00000000,true,true}, // nvkm/subdev/bios/init.c:1643.
            {0x00e18c,0x00020000,0x00000000,true,false}, // nvkm/subdev/bios/init.c:1645.
            {0x000200,0x40000000,0x40000000,true,false}, // nvkm/subdev/bios/init.c:1646.
            {0x614100,0,0x00800018,false,false}, // nvkm/subdev/bios/init.c:1647.
            {0x614900,0,0x00800018,false,true}, // nvkm/subdev/bios/init.c:1648.
            {0x614100,0,0x10000018,false,false}, // nvkm/subdev/bios/init.c:1650.
            {0x614900,0,0x10000018,false,false}, // nvkm/subdev/bios/init.c:1651.
        };
        for (const auto& step : steps) {
            if (active && !(step.rmw ? masked(step.reg, step.mask, step.value)
                                    : registers_.write32(step.reg, step.value))) return Error::Io;
            if (step.wait && !registers_.delayUs(10000)) return Error::Io;
        }
    }
    if (active) {
        // disp/vga.c:27-30,49-52: byte MMIO, not host legacy port access.
        uint8_t old = 0;
        const uint32_t address = 0x601000 + port; // nvkm/engine/disp/vga.c:52.
        if (!ports_.read8(address, old) || !ports_.write8(address, (old & bytes[3]) | bytes[4]))
            return Error::Io;
    }
    return Error::None;
}

bool BoardHelpers::resolveBus(RomView rom, uint8_t index, I2cBus& bus)
{
    uint32_t at = 0;
    if (!table(rom, 4, at)) return false;
    const auto version = rom.data[at], header = rom.data[at + 1];
    const auto count = rom.data[at + 2], stride = rom.data[at + 3];
    // Only CCB 4.0/4.1 are needed here. Source: bios/i2c.c:32-143.
    if ((version != 0x40 && version != 0x41) || header < 5 || stride < 4
        || !rom.contains(at, header + uint32_t(count) * stride)) return false;
    // init.c:263-280 (no display-output context); i2c/base.c:53-64.
    if (index == 0x80 || index == 0xff) index = rom.data[at + 4] & 0x0f;
    else if (index == 0x81) index = rom.data[at + 4] >> 4; // nvkm/subdev/i2c/base.c:61; nvkm/subdev/bios/init.c:274.
    if (index >= count) return false;
    const auto entry = at + header + index * stride;
    const auto raw = rom.little(entry, 4);
    bus = {};
    bus.index = index;
    if (version == 0x40) { // nvkm/subdev/bios/i2c.c:79-90.
        bus.type = uint8_t(raw >> 24);
        // NVIO bit bus: bios/i2c.c:107-112, include/nvkm/subdev/bios/i2c.h:8.
        if (bus.type != 0x05) return false;
        bus.drive = raw & 0x0f; // nvkm/subdev/bios/i2c.c:109.
        if (raw & 0x100) bus.share = uint8_t((raw >> 9) & 0x7f); // nvkm/subdev/bios/i2c.c:110-111.
    } else {
        // PMGR ports: bios/i2c.c:79-89,119-129; include/nvkm/subdev/bios/i2c.h:11.
        bus.type = 0x80;
        bus.drive = raw & 0x1f; // nvkm/subdev/bios/i2c.c:119.
        bus.aux = (raw >> 5) & 0x1f; // nvkm/subdev/bios/i2c.c:122.
        if (bus.drive == 0x1f) return false; // No physical I2C port. nvkm/subdev/bios/i2c.c:120-121.
        if (bus.aux == 0x1f) bus.aux = 0xff; // nvkm/subdev/bios/i2c.c:123-124.
        bus.share = bus.aux;
    }
    return true;
}

Error BoardHelpers::gpio(RomView rom, const uint8_t* instruction, uint32_t length)
{
    GpioEntries entries;
    if (!gpioEntries(rom, entries)) return Error::Input;
    // GPIO_NE selects functions; reset then revisits all matching table rows.
    // init.c:2209-2220; gpio/gf119.c:27-53; gpio/base.c:80-92.
    for (unsigned i = 0; i < entries.count; ++i) {
        const auto& selected = entries.rows[i];
        bool excluded = false;
        for (uint32_t j = 2; j < length; ++j) if (instruction[j] == selected.function) excluded = true;
        if (excluded) continue;
        for (unsigned j = 0; j < entries.count; ++j) {
            const auto& pin = entries.rows[j];
            if (pin.function != selected.function) continue;
            // gpio/base.c:85, bios/gpio.c:125-128: use the first matching
            // function/line for its logic levels, even with duplicate records.
            const Gpio* match = &pin;
            for (unsigned k = 0; k < entries.count; ++k) {
                const auto& entry = entries.rows[k];
                if (entry.function == pin.function && entry.line == pin.line) { match = &entry; break; }
            }
            const auto state = match->logic[pin.defaults ? 1 : 0];
            const uint32_t reg = 0x00d610 + uint32_t(pin.line) * 4; // nvkm/subdev/gpio/gf119.c:60.
            const uint32_t direction = ((state >> 1) ^ 1) << 13;
            const uint32_t level = (state & 1) << 12;
            // gpio/gf119.c:57-64: drive, then latch. Reset also restores routing.
            if (!masked(reg, 0x00003000, direction | level)
                || !masked(0x00d604, 1, 1) // nvkm/subdev/gpio/gf119.c:61.
                || !masked(reg, 0xff, pin.route)) return Error::Io; // nvkm/subdev/gpio/gf119.c:49.
            if (pin.selector && !masked(0x00d740 + uint32_t(pin.selector - 1) * 4, 0xff, pin.line)) // nvkm/subdev/gpio/gf119.c:51.
                return Error::Io;
        }
    }
    return Error::None;
}

Error BoardHelpers::execute(RomView rom, const uint8_t* bytes, uint32_t length, bool active)
{
    if (!registers_.hostSimulation() || !ports_.hostSimulation()) return Error::HardwareDisabled;
    if (!bytes || !length) return Error::Input;
    switch (bytes[0]) {
    case 0x69: return length == 5 ? io(bytes, active) : Error::Input; // nvkm/subdev/bios/init.c:2269.
    case 0x53: // nvkm/subdev/bios/init.c:2252.
        if (length != 3) return Error::Input;
        // disp/vga.c:104-108,49-52: indexed CRTC byte writes.
        if (active && (!ports_.write8(0x6013d4, bytes[1]) || !ports_.write8(0x6013d5, bytes[2])))
            return Error::Io;
        return Error::None;
    case 0x4d: { // nvkm/subdev/bios/init.c:2246.
        if (length < 4 || length != 4u + 2u * bytes[3]) return Error::Input;
        if (!active) return Error::None;
        I2cBus bus;
        if (!resolveBus(rom, bytes[1], bus)) return Error::Input;
        // init.c:1037-1050: convert stored address to seven bits, then write pairs.
        for (unsigned i = 0; i < bytes[3]; ++i)
            if (!ports_.i2cWrite(bus, bytes[2] >> 1, bytes[4 + 2 * i], bytes[5 + 2 * i]))
                return Error::Io;
        return Error::None;
    }
    case 0xa9: // nvkm/subdev/bios/init.c:2297.
        if (length < 2 || length != 2u + bytes[1]) return Error::Input;
        return active ? gpio(rom, bytes, length) : Error::None;
    default: return Error::Denied;
    }
}

}
