// Copyright 2026 Mario Andrés Muñoz.
// Distributed under the terms of the MIT License.
// Scaffold acceptance test for task S1A (docs/tasks/S1A.md). Do not change.
// Source: reference/nouveau/nvkm/subdev/bios/init.c:1892-1905 (INIT_ZM_REG
// sets bit 0 when the register is 0x000200). Trace: the ROM instruction at
// 0x8638 is ZM_REG R[0x000200] = 0x00002020, and the Linux run wrote 0x2021
// (reference/linux-run-debug/mmiotrace.txt.xz, line 45511).
#include "devinit/Interpreter.h"
#include <cstdio>
#include <map>
#include <vector>
using namespace k40::devinit;
static unsigned checks=0,failed=0;
#define CHECK(c) do { ++checks; if(!(c)) { ++failed; std::printf("FAIL line %d: %s\n",__LINE__,#c); } } while(0)
struct Fake : Backend {
    std::map<uint32_t,uint32_t> regs; unsigned writes=0; uint64_t clock=0;
    bool hostSimulation() const override { return true; }
    uint64_t nowUs() override { return ++clock; }
    bool delayUs(uint64_t us) override { clock+=us; return true; }
    bool read32(uint32_t r,uint32_t& v) override { v=regs[r]; return true; }
    bool write32(uint32_t r,uint32_t v) override { ++writes; regs[r]=v; return true; }
};
struct Program {
    std::vector<uint8_t> bytes=std::vector<uint8_t>(16,0);
    void b(uint8_t n) { bytes.push_back(n); }
    void w(uint32_t n) { for(unsigned i=0;i<4;++i)b(n>>(8*i)); }
    void put(uint32_t at,uint32_t n) { if(bytes.size()<at+4)bytes.resize(at+4); for(unsigned i=0;i<4;++i)bytes[at+i]=n>>(8*i); }
    Result run(Fake& f,Tables t={}) { return Interpreter(bytes.data(),bytes.size(),t,f).run(16); }
};
int main() {
    // ZM_REG to 0x000200 with bit 0 clear: bit 0 is set (ROM value 0x2020 -> trace 0x2021).
    { Program p;p.b(0x7a);p.w(0x000200);p.w(0x00002020);p.b(0x71);Fake f;
      CHECK(p.run(f).error==Error::None && f.regs[0x000200]==0x00002021 && f.writes==1); }
    // ZM_REG to 0x000200 with bit 0 already set: value unchanged (ROM 0x8651).
    { Program p;p.b(0x7a);p.w(0x000200);p.w(0x40012125);p.b(0x71);Fake f;
      CHECK(p.run(f).error==Error::None && f.regs[0x000200]==0x40012125); }
    // ZM_REG to another register: no change of bit 0.
    { Program p;p.b(0x7a);p.w(0x000204);p.w(0x00002020);p.b(0x71);Fake f;
      CHECK(p.run(f).error==Error::None && f.regs[0x000204]==0x00002020); }
    // Skipped ZM_REG to 0x000200: no write at all.
    { Program p;p.b(0x38);p.b(0x7a);p.w(0x000200);p.w(0x00002020);p.b(0x71);Fake f;
      CHECK(p.run(f).error==Error::None && f.writes==0); }
    // Only INIT_ZM_REG has the rule. NV_REG (init.c:1709-1720) can clear bit 0.
    { Program p;p.b(0x6e);p.w(0x000200);p.w(0xfffffffe);p.w(0);p.b(0x71);Fake f;f.regs[0x000200]=0x2021;
      CHECK(p.run(f).error==Error::None && f.regs[0x000200]==0x00002020); }
    // ZM_REG_SEQUENCE (init.c:1281-1300) writes plain values.
    { Program p;p.b(0x58);p.w(0x000200);p.b(1);p.w(0x00002020);p.b(0x71);Fake f;
      CHECK(p.run(f).error==Error::None && f.regs[0x000200]==0x00002020); }
    // ZM_REG_GROUP (init.c:2035-2050) writes plain values.
    { Program p;p.b(0x91);p.w(0x000200);p.b(1);p.w(0x00002020);p.b(0x71);Fake f;
      CHECK(p.run(f).error==Error::None && f.regs[0x000200]==0x00002020); }
    // MACRO (init.c:1727-1745) writes plain values.
    { Program p;p.b(0x6f);p.b(0);p.b(0x71);p.put(256,0x000200);p.put(260,0x00002020);Fake f;
      CHECK(p.run(f,{0,256,0,0}).error==Error::None && f.regs[0x000200]==0x00002020); }
    std::printf("s1a_accept: %u checks, %u failed\n",checks,failed);
    return failed ? 1 : 0;
}
