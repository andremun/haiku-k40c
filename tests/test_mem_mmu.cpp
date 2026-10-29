// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memstage/Mapper.h"
#include <cassert>
#include <cstdio>
#include <map>
#include <vector>
using namespace k40::memstage;
using namespace k40::memory::vram;
struct Device final:Io {
    std::vector<uint32_t> ram=std::vector<uint32_t>(4*1024*1024);
    std::vector<std::pair<uint32_t,uint32_t>> writes;
    uint64_t clock=10,step=1,window=0,cached[2]{};
    uint32_t context=0,pdbSelector=0,failReg=0,failReadReg=0;unsigned flushes=0,invalidates=0,disables=0;
    bool backwards=false,slowSlots=false,dirtyAfterInvalidate=false,wrongContextRead=false;
    bool locks[2]{},modeSticks=false,mode16=true,slots=true,queued=true,ignoreInvalidate=false,alias=false,failDisable=false;
    bool active() const override{return true;}
    CacheProfile profile() const override{return CacheProfile::ExplicitUncached;}
    bool acquire(Lock l) override{auto& held=locks[unsigned(l)];if(held)return false;held=true;return true;}
    void release(Lock l) override{assert(locks[unsigned(l)]);locks[unsigned(l)]=false;}
    bool now(uint64_t& t) override{if(backwards)--clock;else clock+=step;t=clock;return true;}
    bool storeFence() override{assert(locks[0]);return true;}
    bool loadFence() override{return true;}
    uint64_t word64(uint64_t address) const{return uint64_t(ram.at(address/4))+uint64_t(ram.at(address/4+1))*4294967296ULL;}
    bool read32(uint32_t reg,uint32_t& value) override{
        if(reg==failReadReg)return false;
        if(reg==0x2100 && dirtyAfterInvalidate && invalidates){value=1;return true;}
        if(reg>=0x700000 && reg<0x800000){assert(locks[0]);value=ram.at((window+reg-0x700000)/4);return true;}
        if(reg==0x1704){value=context+((wrongContextRead && invalidates==3)?1:0);return true;}
        if(reg==0x100c80){if(slowSlots && !slots)clock+=1000000;value=(slots?0x10000:0)+(queued?0x8000:0)+(mode16?1:0);return true;}
        value=reg==0x22700?3:0;return true;
    }
    bool write32(uint32_t reg,uint32_t value) override {
        writes.push_back({reg,value});if(reg==failReg)return false;
        if(reg==0x1700){assert(locks[0]);window=uint64_t(value)*65536;return true;}
        if(reg>=0x700000 && reg<0x800000){assert(locks[0]);ram.at((window+reg-0x700000)/4)=value;return true;}
        if(reg==0x70000){assert(locks[0] && value==1);++flushes;return true;}
        assert(locks[1]);
        if(reg==0x100c80){if(!modeSticks)mode16=value&1;return true;}
        if(reg==0x100cb8){assert(!(value&15));pdbSelector=value;return true;}
        if(reg==0x100cbc){assert(value==0x80000005 && pdbSelector);++invalidates;if(!ignoreInvalidate)cached[0]=cached[1]=0;return true;}
        assert(reg==0x1704);
        if(!(value&0x80000000)){++disables;if(failDisable)return false;}
        else cached[0]=cached[1]=0;
        context=value;return true;
    }
    bool barRead32(uint64_t offset,uint32_t& value) override {
        assert(locks[1] && !locks[0]);if(!(context&0x80000000) || offset>=8192 || (offset%4))return false;
        unsigned page=unsigned(offset/4096);if(alias)page=0;
        if(!cached[page]) {
            const uint64_t instance=uint64_t(context%0x80000000)*4096;
            const auto directory=word64(instance+512);assert(directory%4096==0);
            if(offset>word64(instance+520))return false;
            const auto pde=word64(directory+(offset/134217728)*8);
            assert(uint32_t(pde)==0 && ((pde/4294967296ULL)%16)==1);
            const auto spt=(pde/68719476736ULL)*4096;
            const auto pte=word64(spt+page*8);
            assert(pte%16==5 && pte/68719476736ULL==0);
            cached[page]=(pte/16)*4096;
        }
        value=ram.at((cached[page]+offset%4096)/4);return true;
    }
};
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
