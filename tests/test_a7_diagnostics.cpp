// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "a7/PostDiagnostics.h"
#include "devinit/Interpreter.h"
#include <cassert>
#include <string>
#include <vector>
using namespace k40;
struct Sink {
    std::vector<std::string> names;std::vector<uint64_t> first,second;
    void log(const char* n,uint64_t a,uint64_t b) {names.emplace_back(n);first.push_back(a);second.push_back(b);}
    unsigned find(const char* n) {for(unsigned i=0;i<names.size();++i)if(names[i]==n)return i;assert(false);return 0;}
};
struct Backend:devinit::Backend {
    a7::PostDiagnostics diagnostic;
    uint64_t clock=0;unsigned reads=0,writes=0;
    bool hostSimulation() const override {return true;}
    uint64_t nowUs() override {return ++clock;}
    bool delayUs(uint64_t us) override {const auto before=clock;clock+=us+3;diagnostic.delay(us,before,clock);return true;}
    bool read32(uint32_t,uint32_t& value) override {value=++reads>1;return true;}
    bool write32(uint32_t,uint32_t) override {++writes;return true;}
    bool diagnosticsHealthy() const override {return diagnostic.healthy();}
    void trace(uint32_t pc,uint8_t op,bool active) override {diagnostic.record(active?"SCRIPT_ACTIVE":"SCRIPT_SKIPPED",pc,op,nowUs());}
    void pollSample(uint32_t pc,uint8_t index,uint32_t value,bool met) override {diagnostic.poll(pc,index,value,met,nowUs());}
};
int main() {
    Backend backend;backend.diagnostic.begin(0);
    std::vector<uint8_t> rom(64,0);rom[16]=0x56;rom[17]=0;rom[18]=2;rom[19]=0x7a;rom[28]=0x71;
    // Condition table: register 0, mask 1, compare 1.
    rom[44]=1;rom[48]=1;
    auto result=devinit::Interpreter(rom.data(),rom.size(),{40,0,0,0},backend).run(16);
    assert(result.error==devinit::Error::None && backend.reads==2 && backend.writes==1);
    backend.diagnostic.finishPost(backend.nowUs());
    backend.diagnostic.record("POST_RESULT",0,0,backend.nowUs());Sink sink;backend.diagnostic.flush(sink);
    assert(sink.first[sink.find("POLL_COUNT")]==16 && sink.second[sink.find("POLL_COUNT")]==2);
    assert(sink.second[sink.find("POLL_LAST")]==1 && sink.second[sink.find("POLL_STATE")]==1);
    assert(sink.first[sink.find("POST_DELAY_US")]==20000 && sink.second[sink.find("POST_DELAY_US")]==20003);
    assert(sink.find("SCRIPT_ACTIVE")<sink.find("TRACE_END"));
    assert(sink.find("POST_RESULT")>sink.find("TRACE_END"));
    Backend full;full.diagnostic.begin(0);
    for(unsigned i=0;i<=a7::PostDiagnostics::capacity;++i)full.diagnostic.record("event",i,0,i);
    auto denied=devinit::Interpreter(rom.data(),rom.size(),{},full).run(19);
    assert(denied.error==devinit::Error::Budget && full.writes==0 && full.reads==0);
    full.diagnostic.finishPost(3000);Sink overflow;full.diagnostic.flush(overflow);assert(overflow.first[overflow.find("TRACE_END")]==1);
    a7::PostDiagnostics polls;polls.begin(0);
    for(unsigned i=0;i<=a7::PostDiagnostics::pollCapacity;++i)polls.poll(i,0,0,false,i);
    assert(!polls.healthy());
    a7::PostDiagnostics clock;clock.begin(10);clock.record("bad",0,0,9);assert(!clock.healthy());
    a7::PostDiagnostics mmio;mmio.begin(0);mmio.mmio(5,12);mmio.mmio(15,18);mmio.finishPost(20);
    Sink measured;mmio.flush(measured);assert(measured.first[measured.find("POST_MMIO_US")]==10);
    assert(measured.second[measured.find("POST_MMIO_US")]==7);
}
