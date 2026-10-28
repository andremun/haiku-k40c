// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "runtime/PreStart.h"
#include "board_fake.h"
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <type_traits>
#include <vector>
namespace mem=k40::memory;
namespace start=k40::runtime::startup;
static unsigned checks;
#define CHECK(x) do { ++checks; if(!(x)){std::fprintf(stderr,"line %d: %s\n",__LINE__,#x);std::abort();} }while(0)
struct Storage:mem::ArmStorage {
    unsigned reserves=0,retains=0;
    mem::ArmAllocation next{7,4096,{0x400000}};
    bool success=true;
    unsigned char bytes[4096];
    bool reserveZeroed(mem::ArmAllocation& out) override {
        ++reserves;std::fill_n(bytes,sizeof(bytes),0);out=next;return success;
    }
    void retain(const mem::ArmAllocation&) override { ++retains; }
};
static void prepare(mem::ArmedReference& page,Storage& storage)
{
    CHECK(page.prepare());CHECK(storage.retains==1);
    CHECK(std::all_of(storage.bytes,storage.bytes+4096,[](auto b){return b==0;}));
    auto grant=mem::ArmGrant::hostFixture(storage.next.token,storage.next.physical,{storage.next.physical.value},4096);
    CHECK(page.bind(grant));
}
struct Startup:start::Backend {
    BoardFake raw;
    start::RegisterHelpers helpers{raw,raw};
    bool simulation=true,cold=true,policy=true;
    int failure=-1;
    uint64_t clock=0;unsigned rollback=0,ticks=0,roms=0;
    std::vector<start::Step> calls;
    start::Controller* recursive=nullptr;
    mem::ArmedReference* page=nullptr;
    start::Error nested=start::Error::None;
    bool hostSimulation() const override { return simulation; }
    bool romPolicyReady() const override { return policy; }
    uint64_t nowUs() override { return rollback && ++ticks>=rollback?0:++clock; }
    bool call(start::Step s) {calls.push_back(s);return int(s)!=failure;}
    bool identity() override {
        if(recursive){auto* p=recursive;recursive=nullptr;nested=p->run(*this,*page,1000).error;}
        return call(start::Step::Identity);
    }
    bool unarmInterrupts() override {return call(start::Step::Interrupts)&&helpers.unarmInterrupts();}
    bool postRequired(bool& value) override {value=cold;return call(start::Step::PostDecision);}
    bool unlockCrtc() override {return call(start::Step::Crtc)&&helpers.unlockCrtc();}
    bool privateRing() override {return call(start::Step::PrivateRing)&&helpers.privateRing();}
    bool initializeI2c() override {k40::devinit::I2cBus bus;bus.type=5;bus.drive=2;return call(start::Step::I2c)&&helpers.initializeDedicatedI2c(bus);}
    bool programFlushPage(mem::DeviceIova a) override {
        const auto step=roms?start::Step::FlushRearm:start::Step::FlushPage;
        return call(step)&&helpers.programFlushPage(a);
    }
    bool resetFifoBeforePost() override {return call(start::Step::FifoReset)&&helpers.resetFifoBeforePost();}
    bool executeRom() override {++roms;raw.regs[0x100c10]=0xdeadbeef;return call(start::Step::Rom);}
    bool readFlushPage(uint32_t& value) override {value=raw.regs[0x100c10];return call(start::Step::FlushReadback);}
    bool independentReadiness() override {return call(start::Step::Readiness);}
};
int main()
{
    static_assert(!std::is_copy_constructible<mem::ArmedReference>::value);
    static_assert(!std::is_convertible<mem::ArmedReference*,mem::Buffer*>::value);
    {
        Storage storage;mem::ArmedReference page(storage);prepare(page,storage);
        start::OncePerBoot once;start::Controller first(once),second(once);Startup io;
        io.recursive=&second;io.page=&page;
        auto result=first.run(io,page,1000);
        CHECK(result.error==start::Error::None && result.referenceRetained && result.armAttempts==2);
        CHECK(result.flushReadback==0xdeadbeef && io.raw.regs[0x100c10]==0x4000);
        CHECK(page.armed() && once.state()==start::BootState::Complete);
        CHECK(io.calls.size()==12 && io.roms==1);
        CHECK(io.nested==start::Error::AlreadyAttempted);
        CHECK(second.run(io,page,1000).error==start::Error::AlreadyAttempted);
        CHECK(storage.reserves==1 && storage.retains==1);
        CHECK(!page.prepare());
    }
    for(int fail=int(start::Step::Identity);fail<=int(start::Step::Readiness);++fail) {
        Storage storage;mem::ArmedReference page(storage);prepare(page,storage);
        start::OncePerBoot once;start::Controller controller(once);Startup io;io.failure=fail;
        auto result=controller.run(io,page,1000);
        CHECK(result.error==start::Error::Io && int(result.step)==fail);
        CHECK(page.state()==mem::ArmedReference::State::Failed && once.state()==start::BootState::Failed);
        CHECK(storage.retains==1 && storage.reserves==1);
        CHECK(controller.run(io,page,1000).error==start::Error::AlreadyAttempted);
    }
    for(unsigned bad=0;bad<5;++bad) {
        Storage storage;
        if(bad==0)storage.next.physical.value++;
        if(bad==1)storage.next.bytes=8192;
        if(bad==2)storage.next.physical.value=uint64_t(1)<<32;
        if(bad==3)storage.success=false;
        if(bad==4)storage.next.token=0;
        mem::ArmedReference page(storage);CHECK(!page.prepare());CHECK(!page.prepare());
        CHECK(storage.reserves==1 && storage.retains==(bad==4?0u:1u));
    }
    for(unsigned bad=0;bad<4;++bad) {
        Storage storage;mem::ArmedReference page(storage);CHECK(page.prepare());
        auto grant=mem::ArmGrant::hostFixture(bad==0?8:7,{bad==1?0x800000u:0x400000u},
            {bad==2?0x800000u:0x400000u},bad==3?8192:4096);
        CHECK(!page.bind(grant));CHECK(page.state()==mem::ArmedReference::State::Failed);
    }
    for(unsigned mode=0;mode<5;++mode) {
        Storage storage;mem::ArmedReference page(storage);prepare(page,storage);
        start::OncePerBoot once;start::Controller controller(once);Startup io;
        if(mode==0)io.simulation=false;
        if(mode==1)io.cold=false;
        if(mode==2)io.policy=false;
        if(mode==3)io.rollback=5;
        auto result=controller.run(io,page,mode==4?5:1000);
        CHECK(result.error==(mode==0?start::Error::HardwareDisabled:mode==1?start::Error::UnexpectedState:
            mode==2?start::Error::Inputs:mode==3?start::Error::Clock:start::Error::Timeout));
        CHECK(mode==0?once.state()==start::BootState::Fresh:once.state()==start::BootState::Failed);
    }
    BoardFake denied;denied.simulation=false;start::RegisterHelpers helpers(denied,denied);
    CHECK(!helpers.programFlushPage({0x400000}) && denied.events.empty());
    std::printf("arm-only startup: %u checks pass; no payload publication\n",checks);
}
