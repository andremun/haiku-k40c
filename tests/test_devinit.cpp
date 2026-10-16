// Copyright 2026 Mario Andrés Muñoz.
// Distributed under the terms of the MIT License.
#include "devinit/Interpreter.h"
#include <cstdio>
#include <map>
#include <vector>
using namespace k40::devinit;
static unsigned checks=0,failed=0;
#define CHECK(c) do { ++checks; if(!(c)) { ++failed; std::printf("FAIL line %d: %s\n",__LINE__,#c); } } while(0)
struct Fake : Backend {
    std::map<uint32_t,uint32_t> regs;
    uint64_t clock=0; unsigned reads=0,writes=0,boards=0; bool simulation=true,allowBoard=false,readOk=true;
    bool changing=false,backwards=false; std::vector<uint64_t> delays;
    bool hostSimulation() const override { return simulation; }
    uint64_t nowUs() override { return backwards && writes ? 0 : ++clock; }
    bool delayUs(uint64_t us) override { delays.push_back(us); clock+=us; return true; }
    bool read32(uint32_t r,uint32_t& v) override { ++reads; v=changing && reads>=2 ? 1 : regs[r]; return readOk; }
    bool write32(uint32_t r,uint32_t v) override { ++writes; regs[r]=v; return true; }
    bool board(uint8_t,uint32_t,const uint8_t*,uint32_t,bool) override { ++boards; return allowBoard; }
};
struct Program {
    std::vector<uint8_t> bytes=std::vector<uint8_t>(16,0);
    void b(uint8_t n) { bytes.push_back(n); }
    void w(uint32_t n) { for(unsigned i=0;i<4;++i)b(n>>(8*i)); }
    void put(uint32_t at,uint32_t n) { if(bytes.size()<at+4)bytes.resize(at+4); for(unsigned i=0;i<4;++i)bytes[at+i]=n>>(8*i); }
    void zm(uint32_t reg,uint32_t value) { b(0x7a);w(reg);w(value); }
    Result run(Fake& f,Tables tables={},Limits limits={},uint8_t flags=1) {
        return Interpreter(bytes.data(),bytes.size(),tables,f).run(16,limits,flags);
    }
};
int main() {
    { Program p; p.zm(4,7);p.b(0x71);Fake f;CHECK(p.run(f).error==Error::None && f.regs[4]==7); }
    { Program p;p.b(0x75);p.b(0);p.zm(4,7);p.b(0x72);p.zm(8,9);p.b(0x71);
      p.put(256,12);p.put(260,1);p.put(264,1);Fake f;CHECK(p.run(f,{256,0,0,0}).error==Error::None && f.writes==1 && f.regs[8]==9); }
    { Program p;p.b(0x38);p.zm(4,7);p.b(0x38);p.zm(8,9);p.b(0x71);Fake f;CHECK(p.run(f).error==Error::None && f.writes==1); }
    { Program p;p.b(0x75);p.b(0);p.zm(4,7);p.b(0x71);Fake f;
      CHECK(p.run(f,{}, {},5).error==Error::None && f.writes==1); }
    { Program p;p.b(0x56);p.b(0);p.b(1);p.zm(4,7);p.b(0x71);p.put(256,12);p.put(260,1);p.put(264,1);
      Fake f;f.changing=true;CHECK(p.run(f,{256,0,0,0}).error==Error::None && f.writes==1 && f.delays.size()==1); }
    { Program p;p.b(0x56);p.b(0);p.b(1);p.zm(4,7);p.b(0x71);p.put(256,12);p.put(260,1);p.put(264,1);
      Fake f;CHECK(p.run(f,{256,0,0,0}).error==Error::None && f.writes==0 && f.delays.size()==50); }
    { Program p;p.b(0x74);p.b(0x10);p.b(0x27);p.b(0x71);Fake f;CHECK(p.run(f).error==Error::None && f.delays[0]==10000); }
    { Program p;p.b(0x33);p.b(3);p.b(0x97);p.w(4);p.w(0);p.w(1);p.b(0x36);p.b(0x71);Fake f;
      CHECK(p.run(f).error==Error::None && f.regs[4]==3); }
    { Program p;p.b(0x33);p.b(0);p.b(0x36);p.b(0x71);Fake f;CHECK(p.run(f).error==Error::Malformed); }
    { Program p;p.b(0x36);Fake f;CHECK(p.run(f).error==Error::Malformed); }
    { Program p;p.b(0x5b);p.b(32);p.b(0);p.b(0x71);p.bytes.resize(32);p.zm(4,9);p.b(0x71);Fake f;
      CHECK(p.run(f).error==Error::None && f.regs[4]==9); }
    { Program p;p.b(0x5b);p.b(16);p.b(0);Fake f;CHECK(p.run(f,{}, {100,4,100000}).error==Error::Depth); }
    { Program p;p.b(0x58);p.w(4);p.b(2);p.w(5);p.w(6);p.b(0x71);Fake f;
      CHECK(p.run(f).error==Error::None && f.regs[4]==5 && f.regs[8]==6); }
    { Program p;p.b(0x91);p.w(4);p.b(2);p.w(5);p.w(6);p.b(0x71);Fake f;
      CHECK(p.run(f).error==Error::None && f.regs[4]==6 && f.writes==2); }
    { Program p;p.b(0x8f);p.w(4);p.b(4);p.b(2);p.w(1);p.w(2);p.w(3);p.w(4);p.b(0x71);Fake f;
      CHECK(p.run(f,{0,0,2,1}).error==Error::None && f.regs[4]==2 && f.regs[8]==4); }
    { Program p;p.b(0x8f);p.w(4);p.b(4);p.b(2);Fake f;CHECK(p.run(f).error==Error::Input && f.writes==0); }
    { Program p;p.b(0x6f);p.b(0);p.b(0x71);p.put(256,4);p.put(260,42);Fake f;
      CHECK(p.run(f,{0,256,0,0}).error==Error::None && f.regs[4]==42); }
    { Program p;p.b(0x6e);p.w(4);p.w(0xf0);p.w(3);p.b(0x71);Fake f;f.regs[4]=0xab;CHECK(p.run(f).error==Error::None && f.regs[4]==0xa3); }
    { Program p;p.b(0x90);p.w(4);p.w(8);p.b(0x71);Fake f;f.regs[4]=17;CHECK(p.run(f).error==Error::None && f.regs[8]==17); }
    { Program p;p.b(0x5f);p.w(4);p.b(0xff);p.w(0xf);p.w(1);p.w(8);p.w(0xf0);p.b(0x71);Fake f;f.regs[4]=3;f.regs[8]=0xa0;
      CHECK(p.run(f).error==Error::None && f.regs[8]==0xa7); }
    { Program p;p.b(0x5f);p.w(4);p.b(32);p.w(0xf);p.w(0);p.w(8);p.w(0xf0);Fake f;CHECK(p.run(f).error==Error::Input && f.writes==0); }
    { Program p;p.b(0x8c);p.b(0x8d);p.b(0x71);Fake f;CHECK(p.run(f).error==Error::None && f.writes==0); }
    { Program p;p.b(0x8e);p.b(0x71);Fake f;CHECK(p.run(f).error==Error::Denied && f.boards==1); }
    { Program p;p.b(0x38);p.b(0x8e);p.b(0x71);Fake f;CHECK(p.run(f).error==Error::None && f.boards==0); }
    { Program p;p.b(0x4d);p.b(0x80);p.b(0x40);p.b(1);p.b(0xdd);p.b(3);p.b(0x71);Fake f;CHECK(p.run(f).error==Error::Denied); }
    { Program p;p.b(0x38);p.b(0x69);p.b(0xc3);p.b(3);p.b(0);p.b(1);p.b(0x71);Fake f;CHECK(p.run(f).error==Error::Denied); }
    { Program p;p.b(0xfe);Fake f;CHECK(p.run(f).error==Error::Unsupported && f.writes==0); }
    { Program p;p.b(0x7a);Fake f;CHECK(p.run(f).error==Error::Bounds && f.writes==0); }
    { Program p;p.zm(4,7);p.b(0x71);Fake f;f.simulation=false;CHECK(p.run(f).error==Error::HardwareDisabled && f.writes==0); }
    { Program p;p.zm(4,7);p.b(0x71);Fake f;f.backwards=true;CHECK(p.run(f).error==Error::Clock); }
    { Program p;p.b(0x8c);p.b(0x8d);p.b(0x71);Fake f;CHECK(p.run(f,{}, {1,4,100}).error==Error::Budget); }
    { Program p;p.b(0x74);p.b(0xe8);p.b(3);p.b(0x71);Fake f;CHECK(p.run(f,{}, {100,4,10}).error==Error::Timeout); }
    { Program p;p.b(0x75);p.b(0);p.b(0x71);Fake f;CHECK(p.run(f,{UINT32_MAX,0,0,0}).error==Error::Bounds); }
    std::printf("devinit interpreter: %u checks, %u failures (HOST_SIMULATION_ONLY)\n",checks,failed);
    return failed ? 1 : 0;
}
