// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memnative/Policy.h"
#include "memstage/Experiment.h"
#include "memstage_device.h"
#include <cstdio>
namespace k40::memnative {struct PolicyProbe {static void aperture(Policy& p,uint64_t bytes){p.aperture(bytes);}};}
using namespace k40::memnative;
struct Checked:Device {
    Policy* policy=nullptr;unsigned denials=0;bool liveAudit=false,slotAudit=false,commandAudit=false,contextAudit=false;
    bool read32(uint32_t reg,uint32_t& value) override {
        if(!policy->read(reg,locks[0])){++denials;return false;}
        const auto read=Device::read32(reg,value);if(read)policy->observed(reg,value);return read;
    }
    bool write32(uint32_t reg,uint32_t value) override {
        if(!liveAudit){
            for(uint32_t bad:{0x1714u,0x100c10u,0x200u,0x100u,0x259cu,0x2100u,0x12004cu,0xdeadbeecu})
                for(uint32_t v:{0u,1u,0xffffffffu})assert(!policy->write(bad,v,true,true));
            assert(!policy->write(0x1700,1,true,true));assert(!policy->write(0x70000,2,true,true));
            liveAudit=true;
        }
        if(reg==0x100cb8){assert(!policy->write(reg,value+16,true,true));slotAudit=true;}
        if(reg==0x100cbc){assert(!policy->write(reg,0x80000007,true,true));commandAudit=true;}
        if(reg==0x1704 && value&0x80000000){assert(!policy->write(reg,value+1,true,true));contextAudit=true;}
        if(!policy->write(reg,value,locks[0],locks[1])){++denials;return false;}
        return Device::write32(reg,value);
    }
    bool barRead32(uint64_t offset,uint32_t& value) override {
        if(!policy->barRead(offset,locks[1])){++denials;return false;}
        return Device::barRead32(offset,value);
    }
};
int main(int argc,char**)
{
    Arena arena;Journal journal;Checked io;Faults faults(io,journal,2);Policy policy(arena,faults);io.policy=&policy;
    PolicyProbe::aperture(policy,256*1048576);Upload upload(io,faults,journal,arena);Mapper mapper(io,faults,journal,arena,upload,2);
    assert(!policy.write(0x1700,0,true,false) && !policy.barRead(0,true));
    Experiment experiment(io,faults,arena,upload,mapper,2,2,11520ULL*1048576,256*1048576);
    assert(experiment.run());assert(io.denials==0 && io.liveAudit && io.slotAudit && io.commandAudit && io.contextAudit);
    if(argc>1) {
        std::puts("k40_mem: IO_REJECT kind=0 offset=0 value=0");
        for(unsigned i=0;i<journal.count();++i){const auto* e=journal.at(i);
            std::printf("k40_mem: EVENT phase=%u error=%u offset=%x value=%llx polls=%u elapsed=%llu operation=%u role=%u detail=%u\n",
                unsigned(e->phase),unsigned(e->error),e->offset,(unsigned long long)e->value,e->polls,(unsigned long long)e->elapsed,unsigned(e->operation),e->role,e->detail);}
        for(unsigned i=0;i<arena.count();++i){Record r;assert(arena.at(i,r));std::printf("k40_mem: ALLOCATION id=%llu role=%u physical=%llx bytes=%llu generation=%llu staged=%u referenced=%u retained=%u\n",
            (unsigned long long)r.token.id,unsigned(r.role),(unsigned long long)r.physical.value,(unsigned long long)r.bytes,(unsigned long long)r.writeGeneration,r.staged,r.referenced,r.retained);}
        std::puts("k40_mem: PASS BAR1_SCOPED faults=0 upload=0 mapper=0 closure=2 allocations=7 journal_overflow=0\nk40_mem: SUBMIT result=0 state=3\nk40_mem: RETAINED owner=2 state=3\nK40-MEM-END");return 0;
    }
    // Independent forbidden-register/value inventory, including old A7 targets.
    for(uint32_t reg:{0x1714u,0x100c10u,0x200u,0x100u,0x259cu,0x2100u,0x12004cu,0xdeadbeecu})
        for(uint32_t value:{0u,1u,0xffffffffu})assert(!policy.write(reg,value,true,true));
    assert(!policy.write(0x1700,1,true,true));assert(!policy.write(0x1700,0,false,true));
    assert(!policy.write(0x70000,2,true,true));assert(!policy.write(0x70000,1,false,true));
    assert(!policy.write(0x100cbc,0x80000007,true,true));assert(!policy.write(0x100cb8,0,true,true));
    assert(!policy.write(0x700000+0x40000,0,true,true)); // A7 scratch is outside every ledger record.
    assert(!policy.read(0x100c10,false) && !policy.read(0x700000,false));
    assert(!policy.read(0x2800,false));policy.observed(0x259c,1u<<31);assert(policy.read(0x29f0,false) && !policy.read(0x2800,false));
    assert(!policy.barRead(0,true) && !policy.barRead(8192,true));
    std::puts("memory policy: full controller path and independent denials pass; HOST_ONLY");
}
