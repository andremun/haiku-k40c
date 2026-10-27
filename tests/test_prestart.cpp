// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Source-backed preinit and one-shot controller tests. No hardware access.
#include "runtime/PreStart.h"
#include "board_fake.h"
#include <cstdio>
#include <type_traits>
#include <vector>
namespace start = k40::runtime::startup;
namespace mem = k40::memory;
static unsigned checks = 0, failed = 0;
#define CHECK(c) do { ++checks; if (!(c)) { ++failed; std::printf("FAIL %d: %s\n", __LINE__, #c); } } while (0)

struct PageBackend : mem::Backend {
    uint64_t address = 0x300000;
    unsigned frees = 0, retained = 0;
    bool verified = true;
    bool allocate(uint64_t bytes, uint64_t, mem::Placement placement, mem::Allocation& out) override {
        out = {}; out.id = 1; out.bytes = bytes; out.placement = placement;
        out.device = {address}; out.deviceAddressVerified = verified; return true;
    }
    bool write(const mem::Allocation&, uint64_t, const void*, size_t) override { return true; }
    bool read(const mem::Allocation&, uint64_t, void*, size_t) override { return true; }
    bool publish(const mem::Allocation&) override { return true; }
    bool release(const mem::Allocation&) override { ++frees; return true; }
    void quarantine(const mem::Allocation&) override { ++retained; }
};
struct Startup : start::Backend {
    BoardFake raw;
    start::RegisterHelpers helpers{raw, raw};
    std::vector<start::Step> calls;
    bool simulation = true, policyReady = true, cold = true;
    uint64_t clock = 0;
    unsigned clockCalls = 0, rollbackAt = 0;
    int failStep = -1;
    unsigned romRuns = 0;
    start::Controller* reentrant = nullptr;
    mem::Buffer* page = nullptr;
    start::Error inner = start::Error::None;
    bool hostSimulation() const override { return simulation; }
    bool romPolicyReady() const override { return policyReady; }
    uint64_t nowUs() override { return rollbackAt && ++clockCalls >= rollbackAt ? 0 : ++clock; }
    bool call(start::Step step) { calls.push_back(step); return int(step) != failStep; }
    bool identity() override {
        if (reentrant) { auto* other = reentrant; reentrant = nullptr; inner = other->run(*this, *page, 1000).error; }
        return call(start::Step::Identity);
    }
    bool unarmInterrupts() override { return call(start::Step::Interrupts) && helpers.unarmInterrupts(); }
    bool postRequired(bool& value) override {
        raw.regs[0x02240c] = cold ? 0 : 2;
        return call(start::Step::PostDecision) && helpers.postRequired(value);
    }
    bool unlockCrtc() override { return call(start::Step::Crtc) && helpers.unlockCrtc(); }
    bool privateRing() override { return call(start::Step::PrivateRing) && helpers.privateRing(); }
    bool initializeI2c() override {
        k40::devinit::I2cBus bus; bus.index = 2; bus.type = 5; bus.drive = 2;
        return call(start::Step::I2c) && helpers.initializeDedicatedI2c(bus);
    }
    bool programFlushPage(mem::DeviceIova address) override {
        return call(start::Step::FlushPage) && helpers.programFlushPage(address);
    }
    bool resetFifoBeforePost() override { return call(start::Step::FifoReset) && helpers.resetFifoBeforePost(); }
    bool executeRom() override { ++romRuns; return call(start::Step::Rom); }
    bool independentReadiness() override { return call(start::Step::Readiness); }
};

int main()
{
    static_assert(!std::is_copy_constructible<start::OncePerBoot>::value);
    {
        PageBackend storage; mem::Buffer page(storage); CHECK(page.allocate(4096, 4096, mem::Placement::Host));
        CHECK(page.publish()); start::OncePerBoot state; start::Controller controller(state); Startup backend;
        auto result = controller.run(backend, page, 1000);
        CHECK(result.error == start::Error::None && result.step == start::Step::Complete && result.flushPinned);
        CHECK(state.state() == start::BootState::Complete && page.pinned());
        CHECK(backend.calls.size() == 10 && backend.romRuns == 1);
        for (size_t i = 0; i < backend.calls.size(); ++i)
            CHECK(int(backend.calls[i]) == int(start::Step::Identity) + int(i));
        CHECK(backend.raw.regs[0x100c10] == storage.address >> 8);
        CHECK(backend.raw.regs[0xd054] == 7 && backend.raw.regs[0x122358] == 0x2880);
        CHECK(backend.raw.regs[0x144] == 0 && backend.raw.regs[0x6013d5] == 0x57);
        start::Controller recreated(state); Startup another;
        CHECK(recreated.run(another, page, 1000).error == start::Error::AlreadyAttempted && another.calls.empty());
        CHECK(!page.close() && storage.frees == 0); CHECK(page.retire(true) && page.close());
    }
    {
        PageBackend storage; mem::Buffer page(storage); CHECK(page.allocate(4096, 4096, mem::Placement::Host) && page.publish());
        start::OncePerBoot state; start::Controller first(state), second(state); Startup backend;
        backend.reentrant = &second; backend.page = &page;
        CHECK(first.run(backend, page, 1000).error == start::Error::None);
        CHECK(backend.inner == start::Error::AlreadyAttempted && backend.romRuns == 1);
        CHECK(page.retire(true) && page.close());
    }
    for (int step = int(start::Step::Identity); step <= int(start::Step::Readiness); ++step) {
        PageBackend storage;
        {
            mem::Buffer page(storage); CHECK(page.allocate(4096, 4096, mem::Placement::Host) && page.publish());
            start::OncePerBoot state; start::Controller controller(state); Startup backend; backend.failStep = step;
            const auto result = controller.run(backend, page, 1000);
            CHECK(result.error == start::Error::Io && int(result.step) == step && page.pinned());
            CHECK(state.state() == start::BootState::Failed && int(backend.calls.back()) == step);
            Startup next; start::Controller recreated(state);
            CHECK(recreated.run(next, page, 1000).error == start::Error::AlreadyAttempted && next.calls.empty());
        }
        CHECK(storage.frees == 0 && storage.retained == 1);
    }
    // Fail each transport access, including partial private-ring/FIFO updates.
    for (int access = 0; access < 29; ++access) {
        PageBackend storage; mem::Buffer page(storage);
        CHECK(page.allocate(4096, 4096, mem::Placement::Host) && page.publish());
        start::OncePerBoot state; start::Controller controller(state); Startup backend;
        backend.raw.failAt = access;
        auto result = controller.run(backend, page, 1000);
        CHECK(result.error == start::Error::Io && backend.romRuns == 0 && page.pinned());
        CHECK(backend.raw.calls == unsigned(access + 1));
        CHECK(page.retire(true) && page.close());
    }
    for (unsigned invalid = 0; invalid < 5; ++invalid) {
        PageBackend storage; mem::Buffer page(storage);
        storage.verified = invalid != 0;
        if (invalid == 2) storage.address += 1;
        if (invalid == 3) storage.address = uint64_t(1) << 40;
        CHECK(page.allocate(invalid == 4 ? 256 : 4096, 1, mem::Placement::Host));
        if (invalid != 1) CHECK(page.publish());
        start::OncePerBoot state; start::Controller controller(state); Startup backend;
        CHECK(controller.run(backend, page, 1000).error == start::Error::Inputs && backend.calls.empty());
        CHECK(!page.pinned() && page.close());
    }
    {
        PageBackend storage; mem::Buffer page(storage); CHECK(page.allocate(4096, 4096, mem::Placement::Host) && page.publish());
        start::OncePerBoot state; start::Controller controller(state); Startup backend; backend.cold = false;
        CHECK(controller.run(backend, page, 1000).error == start::Error::UnexpectedState && backend.romRuns == 0);
        CHECK(page.retire(true) && page.close());
    }
    for (bool clockRollback : {false, true}) {
        PageBackend storage; mem::Buffer page(storage); CHECK(page.allocate(4096, 4096, mem::Placement::Host) && page.publish());
        start::OncePerBoot state; start::Controller controller(state); Startup backend;
        if (clockRollback) backend.rollbackAt = 5;
        const auto result = controller.run(backend, page, clockRollback ? 1000 : 5);
        CHECK(result.error == (clockRollback ? start::Error::Clock : start::Error::Timeout));
        CHECK(state.state() == start::BootState::Failed && page.pinned());
        CHECK(page.retire(true) && page.close());
    }
    {
        PageBackend storage; mem::Buffer page(storage); start::OncePerBoot state; start::Controller controller(state);
        Startup backend; backend.simulation = false;
        CHECK(controller.run(backend, page, 1000).error == start::Error::HardwareDisabled);
        CHECK(backend.calls.empty() && state.state() == start::BootState::Fresh);
        BoardFake raw; raw.simulation = false; start::RegisterHelpers helpers(raw, raw);
        bool required = false; k40::devinit::I2cBus bus;
        CHECK(!helpers.unarmInterrupts() && !helpers.postRequired(required) && !helpers.unlockCrtc()
              && !helpers.privateRing() && !helpers.initializeDedicatedI2c(bus)
              && !helpers.programFlushPage({0}) && !helpers.resetFifoBeforePost());
        CHECK(raw.events.empty());
    }
    {
        BoardFake raw; start::RegisterHelpers helpers(raw, raw); k40::devinit::I2cBus bus;
        bus.type = 5; bus.drive = 2; bus.share = 1;
        CHECK(!helpers.initializeDedicatedI2c(bus) && raw.events.empty());
        CHECK(!helpers.programFlushPage({uint64_t(1) << 40}) && raw.events.empty());
        CHECK(!helpers.programFlushPage({3}) && raw.events.empty());
    }
    std::printf("pre-start controller/helpers: %u checks, %u failures (HOST_ONLY)\n", checks, failed);
    return failed ? 1 : 0;
}
