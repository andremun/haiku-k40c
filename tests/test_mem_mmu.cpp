// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memstage/Mapper.h"
#include <cassert>
#include <cstdio>
#include <map>
#include <vector>
using namespace k40::memstage;
using namespace k40::memory::vram;
#include "memstage_device.h"
struct Fixture {
    Device device;Journal journal;Arena arena;Faults faults{device,journal,8};Upload upload{device,faults,journal,arena};Mapper mapper{device,faults,journal,arena,upload,8};Token a,b;
    Fixture(){Probe p;p.parts=p.units=6;for(auto& m:p.mib)m=1920;assert(arena.configure(p,11520ULL*1048576,2,8));
        assert(faults.capture(Phase::Reset,8) && faults.capture(Phase::Post,8));
        assert(arena.allocate(Role::DataA,4096,4096,a) && arena.allocate(Role::DataB,4096,4096,b));}
    void prepare(){assert(mapper.preflight());for(unsigned i=0;i<2;++i){Record r;assert(arena.at(i,r));assert(upload.zero(r.token) && arena.reference(r.token));}
        assert(upload.exercise(a,b));assert(faults.capture(Phase::Physical,8));}
};
int main()
{
    uint64_t out,base,limit;uint32_t di,si;unsigned cases=0;
    for(unsigned i=1;i<=4096;++i) {
        const uint64_t physical=uint64_t(i)*4096;assert(tables::pte({physical},out));assert(out==physical/256+5);
        assert(tables::smallDirectory({physical},out));assert(out==(physical/256+1)*4294967296ULL);
        uint8_t bytes[8];tables::littleEndian(out,bytes);uint64_t decoded=0,weight=1;for(auto byte:bytes){decoded+=byte*weight;weight*=256;}assert(decoded==out);
        assert(tables::indices({physical},uint64_t(1)<<40,di,si));assert(di==physical/134217728 && si==(physical/4096)%32768);
    }
    assert(tables::indices({(uint64_t(1)<<40)-4096},uint64_t(1)<<40,di,si) && di==8191 && si==32767);
    assert(!tables::pte({1},out) && !tables::pte({uint64_t(1)<<40},out));
    assert(tables::pte({(uint64_t(1)<<40)-4096},out) && out<4294967296ULL);
    assert(!tables::smallDirectory({uint64_t(1)<<40},out));
    assert(!tables::instance({4096},4096,base,limit) && !tables::instance({1},8192,base,limit));
    assert(!tables::instance({4096},12288,base,limit));assert(!tables::indices({1},8192,di,si));++cases;
    {Fixture f;f.prepare();assert(f.mapper.run(256*1048576,f.a,f.b));assert(f.mapper.closure()==Closure::OwnedDisabled && f.device.invalidates==3 && f.device.disables==1);assert(!f.device.locks[0] && !f.device.locks[1]);auto n=f.device.writes.size();assert(!f.mapper.run(256*1048576,f.a,f.b) && f.device.writes.size()==n);for(unsigned i=0;i<f.arena.count();++i){Record r;assert(f.arena.at(i,r) && r.retained);}++cases;}
    {Fixture f;f.device.context=0x80000001;assert(!f.mapper.preflight() && f.device.writes.empty());++cases;}
    for(uint32_t reg:{0x100c80u,0x100cb8u,0x100cbcu,0x1704u}){Fixture f;f.prepare();f.device.failReg=reg;assert(!f.mapper.run(256*1048576,f.a,f.b));auto n=f.device.writes.size();assert(!f.mapper.run(256*1048576,f.a,f.b) && f.device.writes.size()==n);assert(f.device.disables==0);++cases;}
    {Fixture f;f.prepare();f.device.slots=false;assert(!f.mapper.run(256*1048576,f.a,f.b) && f.mapper.error()==Error::Invalidate);assert(f.device.invalidates==0);++cases;}
    {Fixture f;f.prepare();f.device.queued=false;assert(!f.mapper.run(256*1048576,f.a,f.b) && f.mapper.error()==Error::Invalidate);assert(f.device.invalidates==1 && f.device.context==0);++cases;}
    {Fixture f;f.prepare();f.device.modeSticks=true;assert(!f.mapper.run(256*1048576,f.a,f.b) && f.mapper.error()==Error::Profile);++cases;}
    {Fixture f;f.prepare();f.device.ignoreInvalidate=true;assert(!f.mapper.run(256*1048576,f.a,f.b) && f.mapper.error()==Error::Compare);assert(f.mapper.closure()==Closure::RetainedUnknown && f.device.disables==0);++cases;}
    {Fixture f;f.prepare();f.device.alias=true;assert(!f.mapper.run(256*1048576,f.a,f.b) && f.mapper.error()==Error::Compare);++cases;}
    {Fixture f;f.prepare();f.device.failDisable=true;assert(!f.mapper.run(256*1048576,f.a,f.b) && f.mapper.closure()==Closure::RetainedUnknown);assert(f.device.disables==1 && f.device.context&0x80000000);++cases;}
    {Fixture f;f.prepare();assert(!f.mapper.run(12288,f.a,f.b));assert(f.device.invalidates==0);++cases;}
    {Fixture f;f.prepare();f.device.step=0;f.device.slots=false;assert(!f.mapper.run(256*1048576,f.a,f.b) && f.mapper.error()==Error::Invalidate);++cases;}
    {Fixture f;f.prepare();f.device.backwards=true;assert(!f.mapper.run(256*1048576,f.a,f.b) && f.mapper.error()==Error::Clock);++cases;}
    {Fixture f;f.prepare();f.device.step=20000000;assert(!f.mapper.run(256*1048576,f.a,f.b) && f.mapper.error()==Error::Budget);++cases;}
    {Fixture f;f.prepare();f.device.failReadReg=0x100c80;assert(!f.mapper.run(256*1048576,f.a,f.b) && f.mapper.error()==Error::Read);++cases;}
    {Fixture f;f.prepare();f.device.slots=false;f.device.slowSlots=true;assert(!f.mapper.run(256*1048576,f.a,f.b) && f.mapper.error()==Error::Invalidate);++cases;}
    {Fixture f;f.prepare();f.device.dirtyAfterInvalidate=true;assert(!f.mapper.run(256*1048576,f.a,f.b) && f.mapper.error()==Error::Dirty);assert(f.device.disables==0);++cases;}
    {Fixture f;f.prepare();f.device.wrongContextRead=true;assert(!f.mapper.run(256*1048576,f.a,f.b) && f.mapper.error()==Error::Dirty);assert(f.device.disables==0 && f.mapper.closure()==Closure::RetainedUnknown);++cases;}
    std::printf("memory MMU: 4096 independent encoding cases; %u lifecycle/fault cases pass; HOST_ONLY\n",cases);
}
