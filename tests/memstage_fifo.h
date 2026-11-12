// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Simulated FIFO and copy engine for the channel host tests. The simulation
// decodes RAMFC, page tables, GPFIFO entries and push-buffer words on its own
// (it does not use ChannelImage). HOST_ONLY, not card evidence.
#pragma once
#include "memnative/Policy.h"
#include "memstage/Channel.h"
#include "memstage_device.h"
#include <cstdio>
#include <map>
using namespace k40::memnative;
namespace ch=k40::memstage::channel;
struct Fifo:Device {
    Policy* policy=nullptr;unsigned denials=0;bool stall=false,mmuFault=false;
    // S2 controls: no fetch of the second entry, launch error, one wrong word, engine stays busy.
    bool copyStall=false,copyError=false,copyWrong=false,copyBusy=false;unsigned copies=0;
    std::map<uint32_t,uint32_t> regs{{0x2390,0x1},{0x2394,0x6e},{0x2398,0x10},{0x2a04,0x800003ff}, // trace 230517-230519, 560973.
        {0x4013c,0xffffffff},{0x4213c,0xffffffff},{0x4413c,0xffffffff},{0x204,0x7},
        {0x200,0xe011212d}, // trace 46125: unit enables left by the start-up script.
        {0x2660,0},{0x104908,0},{0x104f14,0}}; // fifo/gk104.c:206 status of engine 4; ce/gk104.c:52,64 CE0 status.
    uint32_t present=0x7;bool committed=false;uint32_t committedEntries=0,runlistBase=0;
    uint64_t walk(uint64_t instance,uint64_t va) const { // gk104 17/12: PDE va>>27, SPT (va>>12)&32767.
        const auto directory=word64(instance+0x200);assert(directory%4096==0 && word64(instance+0x208)==(uint64_t(1)<<40)-1);
        const auto pde=word64(directory+(va>>27)*8);assert(uint32_t(pde)==0 && ((pde>>32)&15)==1);
        const auto pte=word64((pde>>36)*4096+((va>>12)&32767)*8);assert(pte&1);
        return (pte>>4<<12)+(va&4095);
    }
    bool writable(uint64_t instance,uint64_t va) const { // vmmgf100.c:313-316: bit 2 is read-only.
        const auto pde=word64(word64(instance+0x200)+(va>>27)*8);
        return !(word64((pde>>36)*4096+((va>>12)&32767)*8)&4);
    }
    // The second GPFIFO entry, decoded with cl906f.h:54-70 and cla0b5.h only.
    void copyEngine(uint64_t inst,uint64_t gp) {
        const auto entry=word64(walk(inst,gp+8));const auto words=unsigned((entry>>42)&0x1fffff);
        const auto base=entry&0xffffffffffULL;uint32_t object=0,m[0x800/4]{};
        for(unsigned i=0;i<words;) {
            const auto header=ram.at(walk(inst,base+i*4)/4);++i;
            const auto op=header>>29,count=(header>>16)&0x1fff,subc=(header>>13)&7,method=(header&0xfff)<<2;
            assert(subc==4 && (op==1 || op==4)); // push906f.h:19; INC_METHOD and IMMD_DATA_METHOD only.
            if(op==4){assert(method==0x300 && object==0xa0b5);m[method/4]=count;launch(inst,m);continue;}
            for(unsigned k=0;k<count;++k,++i) {
                const auto value=ram.at(walk(inst,base+i*4)/4);
                if(method+k*4==0)object=value;else{assert(object==0xa0b5 && method+k*4<0x800);m[(method+k*4)/4]=value;}
            }
        }
        assert(copies==1 || copyError);
    }
    void launch(uint64_t inst,const uint32_t* m) {
        const auto flags=m[0x300/4];
        const auto source=(uint64_t(m[0x400/4]&0xff)<<32)|m[0x404/4],dest=(uint64_t(m[0x408/4]&0xff)<<32)|m[0x40c/4];
        // cla0b5.h:38-73: NON_PIPELINED, FLUSH, pitch layouts, multi-line, virtual types, nothing else.
        const bool valid=(flags&3)==2 && (flags&4) && (flags&0x80) && (flags&0x100) && (flags&0x200)
            && !(flags&~0x387u) && m[0x410/4]>=m[0x418/4] && m[0x414/4]>=m[0x418/4] && m[0x418/4] && m[0x41c/4];
        if(copyError || !valid || !writable(inst,dest)){regs[0x104908]|=4;regs[0x104f14]=2;return;} // ce/gk104.c:34,76.
        for(uint32_t line=0;line<m[0x41c/4];++line)for(uint32_t x=0;x<m[0x418/4];x+=4)
            ram.at(walk(inst,dest+uint64_t(line)*m[0x414/4]+x)/4)=ram.at(walk(inst,source+uint64_t(line)*m[0x410/4]+x)/4);
        if(copyWrong)ram.at(walk(inst,dest+64)/4)^=0x100;
        ++copies;
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
        if(value==2) { // S2: second entry after the NOP was consumed.
            assert(ram.at((slot+0x88)/4)==1 && committed);
            if(copyStall)return true;
            copyEngine(inst,word64(inst+0x48)&0xffffffffffULL);
            if(copyBusy)regs[0x2660]=0x80000000; // fifo/gk104.c:208.
            ram.at((slot+0x88)/4)=2;return true;
        }
        // Run 2 on the card: no progress without the post-POST unit enable (mc/nv04.c:120).
        if(stall || regs[0x200]!=0xffffffff || !committed || committedEntries!=1 || !(regs[0x800000+ch::chid*8]&0x80000000))return true;
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
// The report of a passing run, in the line formats of memnative/NativeOwner.cpp.
// Input of the host validator tests (tools/memstage/evidence.py).
inline void dumpReport(const Journal& journal,const Arena& arena,const Faults& faults,const Channel& channel,unsigned step)
{
    const auto& c=channel.report();
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
    if(channel.copy()) {
        std::printf("k40_mem: COPY engine=%u submitted=%u get=%u/%u polls=%u us=%llu copied=%u\n",c.engine,c.copySubmitted,
            c.copyGet,c.copyPut,c.copyPolls,(unsigned long long)c.copyUs,c.copied);
        std::printf("k40_mem: COPY_STATUS engine=%x idle_polls=%u idle_us=%llu ce_intr=%x launcherr=%x\n",c.engineStatus,
            c.idlePolls,(unsigned long long)c.idleUs,c.ceIntr,c.ceLaunchErr);
    }
    for(unsigned i=0;i<faults.routeCount();++i){Routing x;assert(faults.route(i,x));
        std::printf("k40_mem: ROUTE type=%u instance=%u address=%x fault=%u/%u runlist=%u/%u engine=%u/%u\n",
            x.type,x.instance,x.address,x.hasFault,x.fault,x.hasRunlist,x.runlist,x.hasEngine,x.engine);}
    std::printf("k40_mem: %s faults=0 upload=0 mapper=0 closure=2 allocations=%u journal_overflow=0\n",
        channel.copy()?"PASS S2_COPY":"PASS S1_CHANNEL_NOP",arena.count());
    std::puts("k40_mem: SUBMIT result=0 state=3\nk40_mem: RETAINED owner=2 state=3\nK40-MEM-END");
}
