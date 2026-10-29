// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memstage/Upload.h"
#include <cassert>
#include <cstdio>
#include <vector>
using namespace k40::memstage;
using namespace k40::memory::vram;
struct Bus final:Io {
    std::vector<uint32_t> ram=std::vector<uint32_t>(4*1024*1024);
    std::vector<uint32_t> selectors;
    uint64_t clock=10,step=1,base=0;unsigned writes=0,reads=0,locks=0,stores=0,loads=0;
    unsigned failWrite=0,failRead=0;bool enabled=true,uncached=true,lockFail=false,held=false,alias=false,busy=false,backward=false,clockFail=false,fenceFail=false;
    bool active() const override{return enabled;}
    CacheProfile profile() const override{return uncached?CacheProfile::ExplicitUncached:CacheProfile::Unknown;}
    bool acquire(Lock) override {if(lockFail || held)return false;held=true;++locks;return true;}
    void release(Lock) override{assert(held);held=false;}
    bool now(uint64_t& t) override{if(clockFail)return false;if(backward)--clock;else clock+=step;t=clock;return true;}
    bool storeFence() override{assert(held);++stores;return !fenceFail;}
    bool loadFence() override{assert(held);++loads;return !fenceFail;}
    bool barRead32(uint64_t,uint32_t&) override{return false;}
    uint64_t physical(uint32_t reg) const {auto a=base+reg-0x700000;return alias?(0x200000+(a&4095)):a;}
    bool write32(uint32_t reg,uint32_t value) override {
        assert(held);++writes;if(writes==failWrite)return false;
        if(reg==0x1700){base=uint64_t(value)<<16;selectors.push_back(value);return true;}
        if(reg==0x70000){assert(value==1);return true;}
        assert(reg>=0x700000 && reg<0x800000);ram.at(physical(reg)/4)=value;return true;
    }
    bool read32(uint32_t reg,uint32_t& value) override {
        ++reads;if(reads==failRead)return false;
        if(reg>=0x700000 && reg<0x800000){assert(held);value=ram.at(physical(reg)/4);return true;}
        if(reg==0x70000){assert(held);value=busy?2:0;return true;}
        value=reg==0x22700?3:0;return true;
    }
};
struct Fixture {
    Bus bus;Journal journal;Arena arena;Faults faults{bus,journal,55};Upload upload{bus,faults,journal,arena};Token directory,table,a,b;
    Fixture(){Probe p;p.parts=p.units=6;for(auto& m:p.mib)m=1920;
        assert(arena.configure(p,11520ULL*1048576,7,55));
        assert(faults.capture(Phase::Reset,55) && faults.capture(Phase::Post,55));
        assert(arena.allocate(Role::Directory,65536,262144,directory));
        assert(arena.allocate(Role::SmallTable,262144,4096,table));
        assert(arena.allocate(Role::DataA,4096,4096,a));assert(arena.allocate(Role::DataB,4096,4096,b));}
};
int main()
{
    unsigned cases=0;
    {Fixture f;assert(f.upload.zero(f.table));assert(!f.bus.held);bool lower=false,upper=false;for(auto s:f.bus.selectors){lower|=s==0;upper|=s==16;}assert(lower && upper);
     assert(f.upload.exercise(f.a,f.b));Record r;assert(f.arena.describe(f.a,r) && r.staged && !r.referenced);
     for(auto t:{f.a,f.b}){assert(f.arena.describe(t,r));for(uint64_t offset=0;offset<r.bytes;offset+=4){const auto address=r.physical.value+offset;const uint32_t expected=uint32_t(address/4)^uint32_t(address/4294967296ULL)^2772213361u;assert(f.bus.ram[address/4]==expected);}}
     assert(f.bus.stores==4 && f.bus.loads==4);++cases;}
    for(unsigned n:{1u,2u,9u,1025u,65538u}){Fixture f;f.bus.failWrite=n;assert(!f.upload.zero(f.table));assert(!f.bus.held);assert(!f.arena.healthy());auto count=f.bus.writes;assert(!f.upload.zero(f.table) && f.bus.writes==count);Record r;assert(f.arena.describe(f.table,r) && r.retained && !r.staged);++cases;}
    {Fixture f;f.bus.alias=true;assert(!f.upload.exercise(f.a,f.b) && f.upload.error()==Error::Compare);++cases;}
    {Fixture f;f.bus.uncached=false;assert(!f.upload.zero(f.table) && f.bus.writes==0 && f.upload.error()==Error::Profile);++cases;}
    {Fixture f;f.bus.enabled=false;assert(!f.upload.zero(f.table) && f.bus.writes==0 && f.upload.error()==Error::Authority);++cases;}
    {Fixture f;f.bus.lockFail=true;assert(!f.upload.zero(f.table) && f.bus.writes==0);++cases;}
    {Fixture f;f.bus.failRead=f.bus.reads+1;assert(!f.upload.zero(f.a) && f.upload.error()==Error::Read);++cases;}
    {Fixture f;f.bus.busy=true;assert(!f.upload.zero(f.a) && f.upload.error()==Error::Flush);++cases;}
    {Fixture f;f.bus.busy=true;f.bus.step=0;assert(!f.upload.zero(f.a) && f.upload.error()==Error::Flush);assert(f.bus.reads<100100);++cases;}
    {Fixture f;f.bus.backward=true;assert(!f.upload.zero(f.table) && f.bus.writes==0 && f.upload.error()==Error::Clock);++cases;}
    {Fixture f;f.bus.clockFail=true;assert(!f.upload.zero(f.table) && f.bus.writes==0);++cases;}
    {Fixture f;f.bus.step=3000000;assert(!f.upload.zero(f.a) && f.upload.error()==Error::Budget);++cases;}
    {Fixture f;auto t=f.a;++t.epoch;assert(!f.upload.zero(t) && f.bus.writes==0 && f.upload.error()==Error::Bounds);++cases;}
    {Fixture f;assert(f.upload.zero(f.a));assert(f.arena.reference(f.a));auto count=f.bus.writes;assert(!f.upload.zero(f.a) && count==f.bus.writes);++cases;}
    {Fixture f;f.bus.fenceFail=true;assert(!f.upload.zero(f.a) && f.upload.error()==Error::Profile);++cases;}
    {Fixture f;assert(!f.upload.exercise(f.b,f.a) && f.bus.writes==0);++cases;}
    std::printf("memory upload: %u ordering/window/alias/failure cases pass; HOST_ONLY\n",cases);
}
