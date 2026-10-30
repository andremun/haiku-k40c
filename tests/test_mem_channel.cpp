// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Host test of the S1 channel phase through the resident Policy. The simulated
// FIFO advances GP_GET only if the encoded RAMFC, channel page tables, GPFIFO
// entry and push-buffer NOP decode correctly. HOST_ONLY, not card evidence.
#include "memnative/Policy.h"
#include "memstage/Channel.h"
#include "memstage/Experiment.h"
#include "memstage_device.h"
#include <cstdio>
#include <map>
namespace k40::memnative {struct PolicyProbe {static void aperture(Policy& p,uint64_t bytes){p.aperture(bytes);}};}
using namespace k40::memnative;
namespace ch=k40::memstage::channel;
struct Fifo:Device {
    Policy* policy=nullptr;unsigned denials=0;bool stall=false,mmuFault=false;
    std::map<uint32_t,uint32_t> regs{{0x2390,0x1},{0x2394,0x6e},{0x2398,0x10},{0x2a04,0x800003ff}, // trace 230517-230519, 560973.
        {0x4013c,0xffffffff},{0x4213c,0xffffffff},{0x4413c,0xffffffff},{0x204,0x7}};
    uint32_t present=0x7;bool committed=false;uint32_t committedEntries=0,runlistBase=0;
    uint64_t walk(uint64_t instance,uint64_t va) const { // gk104 17/12: PDE va>>27, SPT (va>>12)&32767.
        const auto directory=word64(instance+0x200);assert(directory%4096==0 && word64(instance+0x208)==(uint64_t(1)<<40)-1);
        const auto pde=word64(directory+(va>>27)*8);assert(uint32_t(pde)==0 && ((pde>>32)&15)==1);
        const auto pte=word64((pde>>36)*4096+((va>>12)&32767)*8);assert(pte&1);
        return (pte>>4<<12)+(va&4095);
    }
    uint64_t bar(uint64_t offset,bool write) const {
        assert(context&0x80000000);
        const uint64_t instance=uint64_t(context&0x7fffffff)*4096;
        const auto directory=word64(instance+0x200);const auto pde=word64(directory+(offset>>27)*8);
        const auto pte=word64((pde>>36)*4096+((offset>>12)&32767)*8);
        assert((pte&1) && (!write || !(pte&4)));return (pte>>4<<12)+(offset&4095);
    }
    bool read32(uint32_t reg,uint32_t& value) override {
        if(!policy->read(reg,locks[0])){++denials;return false;}
        if(reg==0x22700){value=2|0x10|0x20|(4u<<21)|(4u<<26)|0x80000000;policy->observed(reg,value);return true;} // top/gk104.c:57-60,72 CE0 runlist 4.
        if(reg==0x22704){value=3|(1u<<2);policy->observed(reg,value);return true;} // top/gk104.c:67-68 type 1.
        if(reg==0x259c && mmuFault && committed){value=1;policy->observed(reg,value);return true;}
        if(regs.count(reg) || (reg>=0x800000 && reg<0x808000) || reg==0x2634 || (reg>=0x2284 && reg<0x2304)){
            value=regs[reg];policy->observed(reg,value);return true;
        }
        const auto ok=Device::read32(reg,value);if(ok)policy->observed(reg,value);return ok;
    }
    bool write32(uint32_t reg,uint32_t value) override {
        if(!policy->write(reg,value,locks[0],locks[1])){++denials;return false;}
        if(reg==0x100cbc && value==0x80000001){assert(locks[1] && pdbSelector);return true;}
        if(reg==0x204){regs[reg]=value==0xffffffff?present:value;return true;}
        if(reg==0x2270){runlistBase=value;return true;}
        if(reg==0x2274){committed=(value&0xfffff)!=0;committedEntries=value&0xfffff;assert((value>>20)==4);return true;}
        if(regs.count(reg) || (reg>=0x800000 && reg<0x808000) || reg==0x2634 || reg==0x2254){
            if(reg==0x800004+ch::chid*8)value&=~0xc00u; // trigger bits read back clear.
            regs[reg]=value;return true;
        }
        return Device::write32(reg,value);
    }
    bool storeFence() override{return true;} // GP_PUT ordering fence; NativeIo needs no lock for it.
    bool barRead32(uint64_t offset,uint32_t& value) override {
        if(!policy->barRead(offset,locks[1])){++denials;return false;}
        if(offset==ch::gpGet || offset==ch::gpPut){value=ram.at(bar(offset,false)/4);return true;}
        return Device::barRead32(offset,value);
    }
    bool barWrite32(uint64_t offset,uint32_t value) override {
        if(!policy->barWrite(offset,value,locks[1])){++denials;return false;}
        const auto slot=bar(offset,true)-0x8c;ram.at((slot+0x8c)/4)=value; // cla16f.h:63 GP_PUT within the slot.
        const auto inst=uint64_t(regs[0x800000+ch::chid*8]&0x7fffffff)*4096;
        if(stall || !committed || committedEntries!=1 || !(regs[0x800000+ch::chid*8]&0x80000000))return true;
        assert(ram.at(uint64_t(runlistBase)*4096/4)==ch::chid && word64(inst+8)==slot); // gk104.c:454; RAMFC USERD slot.
        const auto gp=word64(inst+0x48)&0xffffffffffULL;assert(((word64(inst+0x48)>>48)&31)==9);
        const auto entry=word64(walk(inst,gp));assert(((entry>>42)&0x1fffff)==2); // GP_ENTRY1 bits 30:10: two words.
        // Independent of ChannelImage: dma-pusher.rst:417 format, cla16f.h:74 NOP method 0x08.
        assert(ram.at(walk(inst,entry&0xffffffffffULL)/4)==((1u<<29)|(1u<<16)|(0x08u>>2)));
        assert(ram.at((walk(inst,entry&0xffffffffffULL)+4)/4)==0);
        // Fixed RAMFC words as written by Linux, mmiotrace.txt.xz lines 562273-562285.
        const std::pair<uint32_t,uint32_t> trace[]={{0x10,0xface},{0x30,0xfffff902},{0x84,0x20400000},{0x94,0x30000001},
            {0x9c,0x100},{0xac,0x1f},{0xe4,0x20},{0xb8,0xf8000000},{0xf8,0x10003080},{0xfc,0x10000010}};
        for(const auto& w:trace)assert(ram.at((inst+w.first)/4)==w.second);
        assert(ram.at((inst+0xe8)/4)==1 && ram.at((inst+0x20c)/4)==0xff && ram.at((inst+0x208)/4)==0xffffffff); // trace 562255-562256,562282.
        ram.at((slot+0x88)/4)=value;return true; // GP_GET reaches GP_PUT.
    }
};
static bool scenario(bool stall,bool mmuFault,k40::memstage::ChannelReport& report,unsigned& step,unsigned& denials,bool dump=false)
{
    using namespace k40::memstage;
    Arena arena;Journal journal;Fifo io;io.stall=stall;io.mmuFault=mmuFault;
    Faults faults(io,journal,2);Policy policy(arena,faults);io.policy=&policy;
    PolicyProbe::aperture(policy,256*1048576);Upload upload(io,faults,journal,arena);Mapper mapper(io,faults,journal,arena,upload,2);
    Experiment experiment(io,faults,arena,upload,mapper,2,2,11520ULL*1048576,256*1048576);
    Channel channel(io,faults,journal,arena,upload,mapper,2);
    assert(experiment.run());
    // Forbidden in the channel phase: interrupt enables and clears, other channels, BAR2.
    const bool passed=channel.run();
    for(uint32_t reg:{0x2140u,0x2100u,0x40108u,0x4010cu,0x800000u,0x800010u,0x1714u,0x100c10u})
        assert(!policy.write(reg,0xffffffff,true,true));
    assert(!policy.barWrite(ch::gpPut,1,true) && !policy.barWrite(0,1,true));
    report=channel.report();step=policy.channelStep();denials=io.denials;
    assert(mapper.closure()==Closure::OwnedDisabled);
    if(dump) { // Same line formats as memnative/NativeOwner.cpp.
        const auto& c=report;
        std::puts("k40_mem: IO_REJECT kind=0 offset=0 value=0");
        for(unsigned i=0;i<journal.count();++i){const auto* e=journal.at(i);
            std::printf("k40_mem: EVENT phase=%u error=%u offset=%x value=%llx polls=%u elapsed=%llu operation=%u role=%u detail=%u\n",
                unsigned(e->phase),unsigned(e->error),e->offset,(unsigned long long)e->value,e->polls,(unsigned long long)e->elapsed,unsigned(e->operation),e->role,e->detail);}
        for(unsigned i=0;i<arena.count();++i){Record r;assert(arena.at(i,r));std::printf("k40_mem: ALLOCATION id=%llu role=%u physical=%llx bytes=%llu generation=%llu staged=%u referenced=%u retained=%u\n",
            (unsigned long long)r.token.id,unsigned(r.role),(unsigned long long)r.physical.value,(unsigned long long)r.bytes,(unsigned long long)r.writeGeneration,r.staged,r.referenced,r.retained);}
        std::printf("k40_mem: CHANNEL runlist=%u pbdma=%u mask=%x runm=%x bound=%u closed=%u progress=%u error=%u step=%u\n",
            c.runlist,c.pbdma,c.pbdmaMask,c.runm,c.bound,c.closed,unsigned(c.progress),unsigned(channel.error()),step);
        std::printf("k40_mem: CHANNEL_GET before=%u/%u after=%u/%u polls=%u us=%llu\n",c.getBefore,c.putBefore,c.getAfter,c.putAfter,c.polls,(unsigned long long)c.progressUs);
        std::printf("k40_mem: CHANNEL_STATUS mc=%x fifo=%x mmu=%x pbdma=%x hce=%x state=%x\n",c.mc,c.fifoIntr,c.mmuPending,c.pbdmaIntr,c.pbdmaHce,c.state);
        for(unsigned i=0;i<faults.routeCount();++i){Routing x;assert(faults.route(i,x));
            std::printf("k40_mem: ROUTE type=%u instance=%u address=%x fault=%u/%u runlist=%u/%u engine=%u/%u\n",
                x.type,x.instance,x.address,x.hasFault,x.fault,x.hasRunlist,x.runlist,x.hasEngine,x.engine);}
        std::printf("k40_mem: PASS S1_CHANNEL_NOP faults=0 upload=0 mapper=0 closure=2 allocations=%u journal_overflow=0\n",arena.count());
        std::puts("k40_mem: SUBMIT result=0 state=3\nk40_mem: RETAINED owner=2 state=3\nK40-MEM-END");
    }
    return passed;
}
int main(int argc,char**)
{
    k40::memstage::ChannelReport r;unsigned step=0,denials=0;
    if(argc>1)return scenario(false,false,r,step,denials,true)?0:1;
    assert(scenario(false,false,r,step,denials));
    assert(r.progress==k40::memstage::Progress::Consumed && r.getAfter==1 && r.putAfter==1 && r.closed);
    assert(r.runlist==4 && r.pbdma==2 && r.pbdmaMask==7 && step==23 && denials==0);
    assert(!scenario(true,false,r,step,denials));
    assert(r.progress==k40::memstage::Progress::Stalled && r.getAfter==0 && r.closed && step==23 && denials==0);
    assert(!scenario(false,true,r,step,denials));
    assert(r.progress==k40::memstage::Progress::Consumed && r.mmuPending && r.closed && step==23);
    std::puts("memory channel: S1 NOP path, stall teardown and fault refusal pass through Policy; HOST_ONLY");
}
