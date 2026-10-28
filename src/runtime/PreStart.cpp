// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "runtime/PreStart.h"

namespace k40::runtime::startup {
Result Controller::run(Backend& backend, memory::ArmedReference& page, uint64_t timeoutUs)
{
    Result result;
    if (!backend.executionAllowed()) { result.error = Error::HardwareDisabled; return result; }
    if (!state_.begin()) {
        result.error = Error::AlreadyAttempted; return result;
    }
    auto fail = [&](Error error) {
        page.fail();
        state_.finish(false);
        result.error = error;
        return result;
    };
    memory::DeviceIova address{0};
    if (!timeoutUs || !backend.romPolicyReady() || !page.beginArm(address))return fail(Error::Inputs);
    result.referenceRetained = true;
    const uint64_t started = backend.nowUs();
    uint64_t last = started;
    auto deadline = [&]() {
        const auto now = backend.nowUs();
        if (now < last) return Error::Clock;
        last = now;
        return now - started >= timeoutUs ? Error::Timeout : Error::None;
    };
    auto call = [&](Step step, auto operation) {
        result.step = step;
        auto error = deadline();
        if (error != Error::None) { result.error = error; return false; }
        if (!operation()) { result.error = Error::Io; return false; }
        result.error = deadline();
        return result.error == Error::None;
    };
    // Source-backed preinit order: engine/device/base.c:2908-2916, core/layout.h:7-17,35.
    bool post = false;
    if (!call(Step::Identity, [&] { return backend.identity(); })
        || !call(Step::Interrupts, [&] { return backend.unarmInterrupts(); })
        || !call(Step::PostDecision, [&] { return backend.postRequired(post); })) return fail(result.error);
    // This candidate is deliberately cold-POST-only, not a warm-resume implementation.
    if (!post) return fail(Error::UnexpectedState);
    if (!call(Step::Crtc, [&] { return backend.unlockCrtc(); })
        || !call(Step::PrivateRing, [&] { return backend.privateRing(); })
        || !call(Step::I2c, [&] { return backend.initializeI2c(); })
        || !call(Step::FlushPage, [&] { ++result.armAttempts; return backend.programFlushPage(address); })
        || !call(Step::FifoReset, [&] { return backend.resetFifoBeforePost(); })
        || !call(Step::Rom, [&] { return backend.executeRom(); })
        || !call(Step::FlushReadback, [&] { return backend.readFlushPage(result.flushReadback); })
        || !call(Step::FlushRearm, [&] { ++result.armAttempts; return backend.programFlushPage(address); })
        || !call(Step::Readiness, [&] { return backend.independentReadiness(); })) return fail(result.error);
    result.step = Step::Complete;
    state_.finish(true);
    return result;
}

bool RegisterHelpers::masked(uint32_t reg, uint32_t mask, uint32_t value)
{
    uint32_t old = 0;
    return registers_.read32(reg, old) && registers_.write32(reg, (old & ~mask) | value);
}
bool RegisterHelpers::unarmInterrupts()
{
    if (!allowed()) return false;
    // MC has two leaves: mc/base.c:140-141, mc/gk104.c:56. Unarm: mc/nv04.c:87-90.
    for (unsigned leaf = 0; leaf < 2; ++leaf)
        if (!registers_.write32(0x000140 + leaf * 4, 0)) return false; // nvkm/subdev/mc/nv04.c:88.
    uint32_t drain = 0;
    return registers_.read32(0x000140, drain); // nvkm/subdev/mc/nv04.c:90.
}
bool RegisterHelpers::postRequired(bool& post)
{
    post = false;
    uint32_t state = 0;
    if (!allowed() || !registers_.read32(0x02240c, state)) return false; // nvkm/subdev/devinit/gf100.c:101.
    post = !(state & 2); // nvkm/subdev/devinit/gf100.c:101.
    return true;
}
bool RegisterHelpers::unlockCrtc()
{
    if (!allowed()) return false;
    uint8_t oldLock = 0;
    // nvkm/engine/disp/vga.c:130-135,97-107,49-52: indexed byte MMIO.
    return bytes_.write8(0x6013d4, 0x1f) // nvkm/engine/disp/vga.c:130,99.
        && bytes_.read8(0x6013d5, oldLock) // nvkm/engine/disp/vga.c:100.
        && bytes_.write8(0x6013d4, 0x3f) // nvkm/engine/disp/vga.c:135,106.
        && bytes_.write8(0x6013d5, 0x57); // nvkm/engine/disp/vga.c:131,107.
}
bool RegisterHelpers::privateRing()
{
    if (!allowed()) return false;
    struct Setting { uint32_t reg, value; };
    const Setting settings[] = {
        {0x122318,0x1000}, // nvkm/subdev/privring/gk104.c:103.
        {0x12231c,0x0200}, // nvkm/subdev/privring/gk104.c:104.
        {0x122310,0x0800}, // nvkm/subdev/privring/gk104.c:105.
        {0x122348,0x0100}, // nvkm/subdev/privring/gk104.c:106.
        {0x1223b0,0x0fff}, // nvkm/subdev/privring/gk104.c:107.
        {0x122348,0x0200}, // nvkm/subdev/privring/gk104.c:108.
        {0x122358,0x2880}, // nvkm/subdev/privring/gk104.c:109.
    };
    for (const auto& setting : settings)
        if (!masked(setting.reg, 0x0003ffff, setting.value)) return false; // nvkm/subdev/privring/gk104.c:103-109.
    return true;
}
bool RegisterHelpers::initializeDedicatedI2c(const devinit::I2cBus& bus)
{
    // Dedicated GF119 pads have no mode callback: i2c/padgf119.c:42-45.
    if (!allowed() || bus.type != 0x05 || bus.share != 0xff || bus.drive > 15) return false; // include/nvkm/subdev/bios/i2c.h:8,12.
    return registers_.write32(0x00d014 + uint32_t(bus.drive) * 0x20, 7); // nvkm/subdev/i2c/busgf119.c:69,93.
}
// Both arming writes: fb/base.c:227,204 and fb/gf100.c:83.
bool RegisterHelpers::programFlushPage(memory::DeviceIova address)
{
    if (!allowed() || address.value % 4096 || (address.value >> 8) > UINT32_MAX) return false;
    return registers_.write32(0x100c10, uint32_t(address.value >> 8)); // nvkm/subdev/fb/gf100.c:83.
}
bool RegisterHelpers::resetFifoBeforePost()
{
    if (!allowed()) return false;
    // Cold first POST uses fallback FIFO mask: mc/base.c:57-64, mc/gk104.c:28.
    uint32_t drain = 0;
    return masked(0x000200, 0x00000100, 0) // nvkm/subdev/mc/nv04.c:39; mc/gk104.c:28.
        && masked(0x000200, 0x00000100, 0x00000100) // nvkm/subdev/mc/nv04.c:47; mc/gk104.c:28.
        && registers_.read32(0x000200, drain); // nvkm/subdev/mc/nv04.c:49.
}
}
