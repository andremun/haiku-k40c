// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memstage/Faults.h"
#include <cassert>
#include <cstdio>
#include <map>
#include <vector>
using namespace k40::memstage;
struct Fake final:ReadPort {
    std::map<uint32_t,uint32_t> words;
    std::vector<uint32_t> reads;
    uint64_t time=10,step=1;uint32_t missing=UINT32_MAX;bool backwards=false,stalled=false;
    Fake(){words[0x22700]=0x80000001|4|(3<<3);words[0x22704]=0x80000002|0x10|(5<<21);words[0x22708]=3;}
    bool read32(uint32_t o,uint32_t& v) override {reads.push_back(o);if(o==missing)return false;v=words[o];return true;}
    bool now(uint64_t& t) override {if(stalled)return false;if(backwards)--time;else time+=step;t=time;return true;}
};
static void initial(Faults& f){assert(f.capture(Phase::Reset,81));}
int main()
{
    unsigned cases=0;
    {Fake p;Journal j;Faults f(p,j,81);initial(f);assert(f.capture(Phase::Post,81));Routing r;assert(f.routeCount()==1 && f.route(0,r));assert(r.hasFault && r.fault==3 && r.hasRunlist && r.runlist==5);assert(!r.hasEngine);
     for(auto phase:{Phase::Physical,Phase::Tables,Phase::Mapped,Phase::Remapped,Phase::Restored,Phase::Disabled})assert(f.capture(phase,81));
     assert(f.completed(Phase::Disabled));assert(!f.capture(Phase::Disabled,81));++cases;}
    for(uint32_t offset:{0x100u,0x2100u,0x259cu,0x120058u,0x12005cu}) {
        Fake p;Journal j;Faults f(p,j,81);initial(f);p.words[offset]=1;assert(!f.capture(Phase::Post,81));assert(f.error()==Error::Dirty);const auto count=p.reads.size();assert(!f.capture(Phase::Physical,81) && p.reads.size()==count);++cases;
    }
    for(uint32_t offset:{0x100u,0x2100u,0x259cu,0x120058u,0x120070u,0x22700u}) {
        Fake p;Journal j;Faults f(p,j,81);initial(f);p.missing=offset;assert(!f.capture(Phase::Post,81));assert(f.error()==Error::Read);++cases;
    }
    {Fake p;Journal j;Faults f(p,j,81);initial(f);p.words[0x259c]=0x80000001;assert(!f.capture(Phase::Post,81));unsigned n=0;for(auto o:p.reads)if(o>=0x2800 && o<0x2a00)++n;assert(n==8);++cases;}
    {Fake p;Journal j;Faults f(p,j,81);initial(f);p.words[0x120058]=1<<15;p.words[0x120070]=8;assert(!f.capture(Phase::Post,81));assert(p.words.count(0x125920));++cases;}
    {Fake p;Journal j;Faults f(p,j,81);initial(f);p.words[0x120078]=33;assert(!f.capture(Phase::Post,81) && f.error()==Error::Topology);++cases;}
    {Fake p;Journal j;Faults f(p,j,81);assert(!f.capture(Phase::Post,81) && p.reads.empty());++cases;}
    {Fake p;Journal j;Faults f(p,j,81);assert(!f.capture(Phase::Reset,80) && p.reads.empty());++cases;}
    {Fake p;Journal j;Faults f(p,j,81);initial(f);p.backwards=true;assert(!f.capture(Phase::Post,81) && f.error()==Error::Clock);++cases;}
    {Fake p;Journal j;Faults f(p,j,81);initial(f);p.stalled=true;assert(!f.capture(Phase::Post,81) && f.error()==Error::Clock);++cases;}
    {Fake p;Journal j;Faults f(p,j,81);initial(f);p.step=1000001;assert(!f.capture(Phase::Post,81) && f.error()==Error::Budget);++cases;}
    {Fake p;Journal j;for(unsigned i=0;i<Journal::capacity;++i)assert(j.append({}));Faults f(p,j,81);assert(!f.capture(Phase::Reset,81) && j.overflow());++cases;}
    {Fake p;Journal j;Faults f(p,j,81);initial(f);p.words.clear();assert(!f.capture(Phase::Post,81) && f.error()==Error::Topology);++cases;}
    {Fake p;Journal j;Faults f(p,j,81);initial(f);p.words[0x22708]=0x80000003;assert(!f.capture(Phase::Post,81) && f.error()==Error::Topology);++cases;}
    {Fake p;Journal j;Faults f(p,j,81);p.words[0x100]=1;assert(!f.capture(Phase::Reset,81));assert(p.reads.size()==1);++cases;}
    {Fake p;p.step=0;Journal j;Faults f(p,j,81);initial(f);assert(f.capture(Phase::Post,81));assert(p.reads.size()==73);++cases;}
    std::printf("memory faults: %u bounded baseline/routing/clock cases pass; HOST_ONLY\n",cases);
}
